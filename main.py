#!/usr/bin/env python3
"""Fetch a user post (or posts) from X (Twitter).

Usage:
  # Fetch a single tweet by ID
  python main.py tweet 1234567890123456789

  # Fetch recent posts from a user (by handle or numeric ID)
  python main.py user elonmusk
  python main.py user elonmusk --max 5

  # Load .env automatically (optional; copy .env.example to .env)
  pip install python-dotenv && python main.py user elonmusk
"""

import argparse
import json
import os
import sys

# Optional: load .env if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from x_fetcher import XClient


def _print_tweet(t: dict) -> None:
    text = t.get("text", "")
    created = t.get("created_at", "")
    tid = t.get("id", "")
    metrics = t.get("public_metrics", {})
    print(f"[{created}] @{tid}")
    print(text)
    if metrics:
        print(f"  likes={metrics.get('like_count', 0)} retweets={metrics.get('retweet_count', 0)} replies={metrics.get('reply_count', 0)}")
    print()


def cmd_tweet(client: XClient, tweet_id: str, raw: bool) -> None:
    data = client.get_tweet(tweet_id)
    if raw:
        print(json.dumps(data, indent=2))
        return
    if "data" not in data:
        print("No tweet data in response.", file=sys.stderr)
        sys.exit(1)
    _print_tweet(data["data"])


def cmd_user(
    client: XClient,
    username: str,
    max_results: int,
    raw: bool,
    reply_text: str | None = None,
) -> None:
    data = client.get_user_posts(username, max_results=max_results)
    if raw:
        print(json.dumps(data, indent=2))
        return
    if "data" not in data or not data["data"]:
        print("No tweets in response.", file=sys.stderr)
        sys.exit(1)
    tweets = data["data"]
    for t in tweets:
        _print_tweet(t)
    if reply_text:
        latest = tweets[0]
        tid = latest["id"]
        print(f"Replying to latest tweet {tid}...", file=sys.stderr)
        result = client.reply_to(tid, reply_text)
        if result.get("data"):
            print(f"Posted reply: {result['data'].get('id', '')} — {result['data'].get('text', '')}")
        else:
            print(json.dumps(result, indent=2))


def cmd_reply(client: XClient, tweet_id: str, text: str, raw: bool) -> None:
    result = client.reply_to(tweet_id, text)
    if raw:
        print(json.dumps(result, indent=2))
        return
    if result.get("data"):
        print(f"Posted reply: {result['data'].get('id')} — {result['data'].get('text')}")
    else:
        print(json.dumps(result, indent=2))


def cmd_reply_latest(client: XClient, username: str, text: str, raw: bool) -> None:
    latest = client.get_latest_post(username)
    if not latest:
        print(f"No recent post found for {username}.", file=sys.stderr)
        sys.exit(1)
    tid = latest["id"]
    print(f"Latest post: [{latest.get('created_at')}] {latest.get('text', '')[:60]}...", file=sys.stderr)
    cmd_reply(client, tid, text, raw)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch user posts from X (Twitter)")
    sub = parser.add_subparsers(dest="command", required=True)

    t = sub.add_parser("tweet", help="Fetch a single tweet by ID")
    t.add_argument("tweet_id", help="Numeric tweet ID")
    t.add_argument("--raw", action="store_true", help="Print raw JSON")

    u = sub.add_parser("user", help="Fetch recent posts from a user")
    u.add_argument("username", help="Username (handle) or numeric user ID")
    u.add_argument("--max", type=int, default=10, metavar="N", help="Max tweets (default 10)")
    u.add_argument("--reply", metavar="TEXT", help="Reply to the user's latest post with this text")
    u.add_argument("--raw", action="store_true", help="Print raw JSON")

    r = sub.add_parser("reply", help="Reply to a tweet (needs OAuth 1.0a keys in .env)")
    r.add_argument("--user", metavar="USER", help="Reply to this user's latest post")
    r.add_argument("--tweet-id", metavar="ID", dest="tweet_id", help="Tweet ID to reply to")
    r.add_argument("--text", "-t", required=True, metavar="TEXT", help="Reply text")
    r.add_argument("--raw", action="store_true", help="Print raw JSON")

    args = parser.parse_args()
    client = XClient()

    try:
        if args.command == "tweet":
            cmd_tweet(client, args.tweet_id, getattr(args, "raw", False))
        elif args.command == "user":
            cmd_user(
                client,
                args.username,
                args.max,
                getattr(args, "raw", False),
                reply_text=getattr(args, "reply", None),
            )
        elif args.command == "reply":
            raw = getattr(args, "raw", False)
            text = args.text
            if getattr(args, "user", None):
                cmd_reply_latest(client, args.user, text, raw)
            elif getattr(args, "tweet_id", None):
                cmd_reply(client, args.tweet_id, text, raw)
            else:
                print("Use either --user USER or --tweet-id ID.", file=sys.stderr)
                sys.exit(1)
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
