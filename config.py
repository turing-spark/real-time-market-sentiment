"""
Real-Time Market Sentiment Dashboard — Configuration

Central configuration for model, database, fetcher intervals,
data sources, and known ticker symbols.
"""

import os

# ─── Model & Database ─────────────────────────────────────────

MODEL = os.getenv("MODEL", "gemini-3.1-flash-lite-preview")
DB_PATH = os.getenv("MEMORY_DB", "sentiment.db")

# ─── Fetcher Intervals (seconds) ──────────────────────────────

REDDIT_INTERVAL = int(os.getenv("REDDIT_INTERVAL", "120"))      # 2 minutes
RSS_INTERVAL = int(os.getenv("RSS_INTERVAL", "180"))             # 3 minutes
SEC_INTERVAL = int(os.getenv("SEC_INTERVAL", "300"))             # 5 minutes
TWITTER_MOCK_INTERVAL = int(os.getenv("TWITTER_INTERVAL", "60")) # 1 minute

# ─── Reddit Configuration ─────────────────────────────────────

SUBREDDITS = ["wallstreetbets", "stocks", "investing"]
REDDIT_POST_LIMIT = 25  # posts per subreddit per fetch

# ─── RSS Feed URLs ─────────────────────────────────────────────

RSS_FEEDS = [
    # Yahoo Finance
    "https://finance.yahoo.com/news/rssindex",
    # MarketWatch
    "https://feeds.marketwatch.com/marketwatch/topstories/",
    "https://feeds.marketwatch.com/marketwatch/marketpulse/",
]

# ─── SEC EDGAR Configuration ──────────────────────────────────

SEC_EDGAR_BASE = "https://efts.sec.gov/LATEST/search-index"
SEC_FULL_TEXT_SEARCH = "https://efts.sec.gov/LATEST/search-index?q=%22Form+4%22&dateRange=custom&startdt={start}&enddt={end}&forms=4,13F-HR"
SEC_RECENT_FILINGS = "https://efts.sec.gov/LATEST/search-index?forms=4,13F-HR&dateRange=custom&startdt={start}&enddt={end}"
# Use the public EDGAR full-text search API
SEC_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
SEC_USER_AGENT = os.getenv("SEC_USER_AGENT", "MarketSentimentBot/1.0 (research@example.com)")
SEC_FILING_TYPES = ["4", "13F-HR"]

# ─── Known Tickers ─────────────────────────────────────────────
# Top ~150 most-discussed tickers. Used to filter false positives from regex.

STOCK_TICKERS = {
    # Mega-cap tech
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSLA",
    "AMD", "INTC", "CRM", "ORCL", "ADBE", "NFLX", "PYPL", "SQ",
    "SHOP", "SNOW", "PLTR", "UBER", "COIN", "ROKU", "SNAP", "PINS",
    "TWLO", "ZM", "DDOG", "NET", "CRWD", "ZS", "MDB", "OKTA",
    # Semiconductors
    "AVGO", "QCOM", "TXN", "MU", "MRVL", "LRCX", "AMAT", "KLAC",
    "ARM", "SMCI", "TSM", "ASML",
    # Finance
    "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW",
    "V", "MA", "AXP", "COF",
    # Healthcare / Biotech
    "JNJ", "UNH", "PFE", "MRNA", "LLY", "ABBV", "BMY", "GILD",
    "AMGN", "BIIB", "REGN", "VRTX", "ISRG",
    # Consumer
    "WMT", "COST", "TGT", "HD", "LOW", "NKE", "SBUX", "MCD",
    "KO", "PEP", "PG", "DIS", "CMCSA",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "OXY", "DVN",
    # Industrial / Auto
    "BA", "CAT", "DE", "GE", "HON", "UPS", "FDX",
    "F", "GM", "RIVN", "LCID",
    # Meme / High-volatility
    "GME", "AMC", "BB", "BBBY", "WISH", "CLOV", "SOFI",
    "MARA", "RIOT", "HUT",
    # Crypto-related / Fintech
    "MSTR", "HOOD",
    # ETFs (commonly discussed)
    "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO", "ARKK", "XLF",
    "XLE", "XLK", "GLD", "SLV", "TLT", "HYG",
    # Indices (treated as tickers in discussion)
    "VIX",
}

# ─── Company Name → Ticker Mapping ────────────────────────────
# Common company names that appear in text without $ prefix.

COMPANY_TO_TICKER = {
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "meta": "META",
    "facebook": "META",
    "nvidia": "NVDA",
    "tesla": "TSLA",
    "amd": "AMD",
    "intel": "INTC",
    "netflix": "NFLX",
    "paypal": "PYPL",
    "shopify": "SHOP",
    "snowflake": "SNOW",
    "palantir": "PLTR",
    "coinbase": "COIN",
    "salesforce": "CRM",
    "oracle": "ORCL",
    "adobe": "ADBE",
    "uber": "UBER",
    "gamestop": "GME",
    "robinhood": "HOOD",
    "microstrategy": "MSTR",
    "broadcom": "AVGO",
    "qualcomm": "QCOM",
    "walmart": "WMT",
    "costco": "COST",
    "target": "TGT",
    "boeing": "BA",
    "disney": "DIS",
    "starbucks": "SBUX",
    "pfizer": "PFE",
    "moderna": "MRNA",
    "jpmorgan": "JPM",
    "goldman sachs": "GS",
    "goldman": "GS",
    "exxon": "XOM",
    "chevron": "CVX",
}

# ─── Sentiment Reversal Detection ─────────────────────────────

REVERSAL_THRESHOLD = 0.3  # minimum delta between 24h avg and 7d avg to trigger alert
