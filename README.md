# x-fetcher

Fetch user posts from **X (Twitter)** using the official API v2.

## Setup

1. **Create a developer account and app**
   - Go to [developer.x.com](https://developer.x.com/), sign in, and create a project/app.
   - In the app, open "Keys and tokens" and generate a **Bearer Token**.

2. **Create a virtual environment and install dependencies** (recommended on macOS/Homebrew)
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # on Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
   Then run the script with the same environment active: `python main.py ...`

3. **Set credentials in `.env`** (copy from `.env.example`)
   - **Read (fetch):** `X_BEARER_TOKEN` — from your app’s “Keys and tokens”.
   - **Write (reply):** `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` — same app: API Key/Secret, then create Access Token and Secret for your user.

## Usage

**Fetch a single tweet by ID**
```bash
python main.py tweet 1234567890123456789
```

**Fetch recent posts from a user**
```bash
python main.py user elonmusk
python main.py user elonmusk --max 5
```

**Reply to a user’s latest post** (needs OAuth 1.0a keys in `.env`)
```bash
python main.py user georgistst --reply "Your comment here"
# or explicitly reply to a tweet:
python main.py reply --user georgistst --text "Your comment here"
python main.py reply --tweet-id 1234567890 --text "Your comment here"
```

**Print raw JSON**
```bash
python main.py tweet 1234567890123456789 --raw
python main.py user elonmusk --raw
```

## Using the client in code

```python
from x_fetcher import XClient

client = XClient()  # reads .env for tokens

# Read
tweet = client.get_tweet("1234567890123456789")
posts = client.get_user_posts("elonmusk", max_results=10)
latest = client.get_latest_post("georgistst")

# Write (reply) — requires OAuth 1.0a keys in .env
if latest:
    client.reply_to(latest["id"], "My reply text")
```

## API notes

- **Read:** Bearer Token only. Free tier has rate limits (e.g. 300 tweet lookups per 15 min).
- **Write (replies):** OAuth 1.0a (API Key, API Secret, Access Token, Access Token Secret) from the same developer app.
- Do not commit `.env` or any file containing your tokens.
# beezio-x
