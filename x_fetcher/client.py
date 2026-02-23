"""X (Twitter) API v2 client for fetching tweets and user posts."""

import os
from pathlib import Path

import requests
from requests_oauthlib import OAuth1

def _load_dotenv() -> None:
    """Load .env from project root or cwd into os.environ (only if not already set)."""
    for d in (Path.cwd(), Path(__file__).resolve().parents[1]):
        env_file = d / ".env"
        if not env_file.is_file():
            continue
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key and value and key not in os.environ:
                os.environ[key] = value
        break


_load_dotenv()

BASE_URL = "https://api.twitter.com/2"
TWEET_FIELDS = "created_at,author_id,public_metrics,text,lang"
USER_FIELDS = "username,name,description,public_metrics"
EXPANSIONS = "author_id"


def _bearer_auth(request: requests.PreparedRequest) -> requests.PreparedRequest:
    token = os.environ.get("X_BEARER_TOKEN") or os.environ.get("BEARER_TOKEN")
    if not token:
        raise ValueError(
            "Set X_BEARER_TOKEN or BEARER_TOKEN in the environment. "
            "See .env.example and https://developer.x.com/"
        )
    request.headers["Authorization"] = f"Bearer {token}"
    request.headers["User-Agent"] = "x-fetcher"
    return request


def _oauth1() -> OAuth1:
    """OAuth 1.0a for posting (reply). Requires user context keys in .env."""
    key = os.environ.get("X_API_KEY") or os.environ.get("TWITTER_API_KEY")
    secret = os.environ.get("X_API_SECRET") or os.environ.get("TWITTER_API_SECRET")
    token = os.environ.get("X_ACCESS_TOKEN") or os.environ.get("TWITTER_ACCESS_TOKEN")
    token_secret = os.environ.get("X_ACCESS_TOKEN_SECRET") or os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
    if not all((key, secret, token, token_secret)):
        raise ValueError(
            "To post replies, set X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET "
            "(or TWITTER_* equivalents) in .env. See .env.example and https://developer.x.com/"
        )
    return OAuth1(key, secret, token, token_secret)


class XClient:
    """Client for X API v2: read tweets and post replies."""

    def __init__(self, bearer_token: str | None = None):
        if bearer_token:
            os.environ["X_BEARER_TOKEN"] = bearer_token

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{BASE_URL}{path}"
        resp = requests.get(url, params=params, auth=_bearer_auth, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(
                f"X API error {resp.status_code}: {resp.text}"
            )
        return resp.json()

    def _post(self, path: str, json: dict) -> dict:
        url = f"{BASE_URL}{path}"
        resp = requests.post(url, json=json, auth=_oauth1(), timeout=30)
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"X API error {resp.status_code}: {resp.text}"
            )
        return resp.json() if resp.content else {}

    def get_tweet(self, tweet_id: str) -> dict:
        """Fetch a single tweet by ID.

        Returns the API response with 'data' containing the tweet and
        optional 'includes' (e.g. users) when using expansions.
        """
        path = "/tweets/" + tweet_id
        params = {
            "tweet.fields": TWEET_FIELDS,
            "expansions": EXPANSIONS,
            "user.fields": USER_FIELDS,
        }
        return self._get(path, params)

    def get_user_id(self, username: str) -> str:
        """Resolve a username (handle) to a numeric user ID."""
        username = username.lstrip("@")
        data = self._get(f"/users/by/username/{username}")
        if "data" not in data:
            raise ValueError(f"User not found: {username}")
        return data["data"]["id"]

    def get_user_posts(
        self,
        username_or_id: str,
        max_results: int = 10,
        exclude_replies: bool = False,
        exclude_retweets: bool = False,
    ) -> dict:
        """Fetch recent posts (tweets) for a user by username or user ID.

        Returns the API response with 'data' (list of tweets) and optional
        'includes' (e.g. users).
        """
        user_id = username_or_id if username_or_id.isdigit() else self.get_user_id(username_or_id)
        path = f"/users/{user_id}/tweets"
        params: dict = {
            "max_results": min(max(1, max_results), 100),
            "tweet.fields": TWEET_FIELDS,
            "expansions": EXPANSIONS,
            "user.fields": USER_FIELDS,
        }
        exclude = [x for x in ("replies", "retweets") if (exclude_replies and x == "replies") or (exclude_retweets and x == "retweets")]
        if exclude:
            params["exclude"] = ",".join(exclude)
        return self._get(path, params)

    def get_latest_post(
        self,
        username_or_id: str,
        exclude_replies: bool = True,
        exclude_retweets: bool = True,
    ) -> dict | None:
        """Return the most recent post from a user, or None if they have no posts."""
        data = self.get_user_posts(
            username_or_id,
            max_results=1,
            exclude_replies=exclude_replies,
            exclude_retweets=exclude_retweets,
        )
        if not data.get("data"):
            return None
        return data["data"][0]

    def reply_to(self, tweet_id: str, text: str) -> dict:
        """Post a reply to a tweet. Requires OAuth 1.0a (write) credentials in .env."""
        if len(text) > 280:
            raise ValueError("Reply text must be 280 characters or less")
        payload: dict = {"text": text, "reply": {"in_reply_to_tweet_id": tweet_id}}
        return self._post("/tweets", payload)
