"""
Twitter/X mock fetcher — generates synthetic financial tweets for testing.

Since Twitter/X API requires paid access, this generates realistic mock data
from templates with randomized tickers, sentiment, and engagement metrics.
"""

import logging
import random
from datetime import datetime, timezone

from config import TWITTER_MOCK_INTERVAL, STOCK_TICKERS
from fetchers.base import BaseFetcher

log = logging.getLogger("fetcher.twitter_mock")

# Popular tickers for mock generation (subset of known tickers)
POPULAR_TICKERS = [
    "NVDA", "TSLA", "AAPL", "AMD", "MSFT", "META", "AMZN", "GOOGL",
    "GME", "AMC", "PLTR", "COIN", "SOFI", "SPY", "QQQ", "MSTR",
]

# Tweet templates with {ticker} placeholder
BULLISH_TEMPLATES = [
    "${ticker} is going to the moon! Bought more calls today. Bullish AF!",
    "Just loaded up on ${ticker}. This breakout is real. Target price way higher.",
    "${ticker} earnings beat expectations! Revenue growth is insane. Long and strong.",
    "Everyone sleeping on ${ticker}. Undervalued at these levels. Accumulating heavily.",
    "${ticker} short squeeze incoming. Short interest is through the roof!",
    "Technical analysis: ${ticker} just broke through resistance. Next stop: ATH.",
    "${ticker} institutional buying is massive this week. Smart money loading up.",
    "Diamond hands on ${ticker}. Not selling until we see $500+. Rally just starting.",
    "${ticker} partnership announcement is huge. This changes the growth trajectory.",
    "Why ${ticker} is my top pick: strong earnings, growing market, innovative products.",
]

BEARISH_TEMPLATES = [
    "${ticker} is overvalued. P/E ratio is absurd. Shorting here.",
    "Sold all my ${ticker}. The bubble is about to pop. Get out while you can.",
    "${ticker} missed earnings badly. Revenue declining. This stock is crashing.",
    "Insider selling at ${ticker} - CFO just dumped shares. Red flag!",
    "${ticker} facing SEC investigation. This could tank hard.",
    "${ticker} competition is eating their lunch. Market share declining fast.",
    "Technical breakdown on ${ticker}. Head and shoulders pattern confirmed. Bearish.",
    "${ticker} guidance was terrible. Lowered estimates across the board.",
    "Puts on ${ticker}. This thing is going to zero. Fraud written all over it.",
    "${ticker} debt levels are unsustainable. Bankruptcy risk is real.",
]

NEUTRAL_TEMPLATES = [
    "${ticker} trading sideways. Waiting for the earnings catalyst.",
    "What's everyone's take on ${ticker}? The chart looks interesting but uncertain.",
    "${ticker} CEO interview was vague. No clear direction. Hold for now.",
    "Analyzing ${ticker} options flow. Mixed signals from the market makers.",
    "${ticker} at a crossroads. Could go either way from this support level.",
]

MOCK_USERS = [
    "WallStTrader99", "StockPickGuru", "BullishBrian", "BearishBrenda",
    "TechStockFan", "DayTraderDave", "OptionsQueen", "CryptoMike",
    "ValueInvestor42", "MemeStockKing", "QuantTrader", "RetailRevolt",
]


class TwitterMockFetcher(BaseFetcher):
    source_type = "twitter"

    def __init__(self, agent_url: str = "http://localhost:8888", interval: int = TWITTER_MOCK_INTERVAL):
        super().__init__(agent_url=agent_url, interval=interval)

    def fetch(self) -> list[dict]:
        items = []
        # Generate 2-3 tweets per cycle
        num_tweets = random.randint(2, 3)

        for _ in range(num_tweets):
            ticker = random.choice(POPULAR_TICKERS)
            user = random.choice(MOCK_USERS)

            # Weighted sentiment: 40% bullish, 30% bearish, 30% neutral
            roll = random.random()
            if roll < 0.4:
                template = random.choice(BULLISH_TEMPLATES)
            elif roll < 0.7:
                template = random.choice(BEARISH_TEMPLATES)
            else:
                template = random.choice(NEUTRAL_TEMPLATES)

            text = template.replace("{ticker}", ticker)
            likes = random.randint(5, 5000)
            retweets = random.randint(1, int(likes * 0.3) + 1)
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

            items.append({
                "text": text,
                "source": f"@{user} | {likes} likes | {retweets} RT | {now}",
            })

        return items
