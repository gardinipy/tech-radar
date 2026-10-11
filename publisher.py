"""Publica no X (ou simula, se DRY_RUN=true)."""
import config


def post(text):
    if config.DRY_RUN:
        print(f"[DRY_RUN] Postaria no X:\n{text}\n")
        return "dry-run"
    import tweepy

    client = tweepy.Client(
        consumer_key=config.X_API_KEY,
        consumer_secret=config.X_API_SECRET,
        access_token=config.X_ACCESS_TOKEN,
        access_token_secret=config.X_ACCESS_TOKEN_SECRET,
    )
    resp = client.create_tweet(text=text)
    return str(resp.data["id"])
