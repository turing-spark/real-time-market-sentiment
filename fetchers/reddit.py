"""
Reddit fetcher — pulls posts from r/wallstreetbets, r/stocks, r/investing.

Uses Reddit's public JSON API (no authentication required).
Appends .json to subreddit hot listing URLs.
"""

import logging

import requests

from config import SUBREDDITS, REDDIT_POST_LIMIT, REDDIT_INTERVAL
from fetchers.base import BaseFetcher

log = logging.getLogger("fetcher.reddit")


class RedditFetcher(BaseFetcher):
    source_type = "reddit"

    def __init__(self, agent_url: str = "http://localhost:8888", interval: int = REDDIT_INTERVAL,
                 subreddits: list[str] | None = None):
        super().__init__(agent_url=agent_url, interval=interval)
        self.subreddits = subreddits or SUBREDDITS
        self.headers = {
            "User-Agent": "MarketSentimentBot/1.0 (research)",
        }

    def fetch(self) -> list[dict]:
        items = []
        for sub in self.subreddits:
            try:
                url = f"https://www.reddit.com/r/{sub}/hot.json?limit={REDDIT_POST_LIMIT}"
                resp = requests.get(url, headers=self.headers, timeout=15)
                if resp.status_code != 200:
                    log.warning(f"Reddit r/{sub} returned {resp.status_code}")
                    continue

                data = resp.json()
                posts = data.get("data", {}).get("children", [])

                for post in posts:
                    pd = post.get("data", {})
                    title = pd.get("title", "")
                    selftext = pd.get("selftext", "")
                    author = pd.get("author", "unknown")
                    score = pd.get("score", 0)
                    permalink = pd.get("permalink", "")

                    # Skip stickied/pinned posts (usually mod posts)
                    if pd.get("stickied", False):
                        continue

                    # Combine title + selftext for analysis
                    text = title
                    if selftext:
                        # Truncate long posts
                        text += "\n\n" + selftext[:2000]

                    items.append({
                        "text": text,
                        "source": f"r/{sub} | u/{author} | score:{score}",
                        "url": f"https://reddit.com{permalink}" if permalink else "",
                    })

            except Exception as e:
                log.error(f"Reddit r/{sub} fetch error: {e}")

        return items
