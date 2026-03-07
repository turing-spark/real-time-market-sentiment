"""
Real-Time Market Sentiment — Ticker Extraction & Sentiment Scoring

Provides:
- extract_tickers(text) -> list[str]  — regex + company name matching
- score_sentiment(text) -> float      — finance-specific lexicon, returns -1.0 to 1.0
"""

import re
from config import STOCK_TICKERS, COMPANY_TO_TICKER

# ─── Ticker Extraction ────────────────────────────────────────


def extract_tickers(text: str) -> list[str]:
    """Extract stock ticker symbols from text.

    Matches:
    1. $TICKER patterns (e.g. $NVDA, $AAPL)
    2. Bare uppercase words filtered against known tickers
    3. Company name mentions mapped to tickers

    Returns:
        Deduplicated list of ticker symbols.
    """
    found = set()

    # 1. $TICKER pattern — high confidence
    for match in re.finditer(r'\$([A-Z]{1,5})\b', text):
        ticker = match.group(1)
        if ticker in STOCK_TICKERS:
            found.add(ticker)

    # 2. Bare uppercase words — filter against known tickers
    # Exclude common English words that happen to be 1-5 uppercase letters
    UPPERCASE_EXCLUDE = {
        "I", "A", "AM", "AN", "AS", "AT", "BE", "BY", "DO", "GO", "HE",
        "IF", "IN", "IS", "IT", "ME", "MY", "NO", "OF", "OH", "OK", "ON",
        "OR", "OUR", "SO", "TO", "UP", "US", "WE", "CEO", "CFO", "CTO",
        "COO", "IPO", "ETF", "SEC", "FDA", "GDP", "EPS", "PE", "DD",
        "IMO", "FYI", "LMAO", "OMG", "WTF", "TBH", "YOLO", "FOMO",
        "ALL", "ARE", "BUT", "CAN", "DAY", "FOR", "GET", "GOT", "HAS",
        "HAD", "HIS", "HOW", "ITS", "LET", "MAY", "NEW", "NOT", "NOW",
        "OLD", "ONE", "OUR", "OUT", "OWN", "PUT", "RAN", "RUN", "SAY",
        "SHE", "THE", "TOO", "TOP", "TRY", "TWO", "USE", "WAR", "WAS",
        "WAY", "WHO", "WHY", "WIN", "WON", "YET", "YOU",
        "AFTER", "ALSO", "BACK", "BEEN", "CALL", "COME", "DOES", "DOWN",
        "EACH", "EVEN", "FIND", "FIRST", "FROM", "GOOD", "HAND", "HAVE",
        "HERE", "HIGH", "HOLD", "HOME", "INTO", "JUST", "KEEP", "KNOW",
        "LAST", "LEFT", "LIKE", "LINE", "LIST", "LONG", "LOOK", "LOSS",
        "MADE", "MAKE", "MANY", "MIND", "MORE", "MOST", "MUCH", "MUST",
        "NAME", "NEED", "NEXT", "ONLY", "OPEN", "OVER", "PART", "PLAN",
        "POST", "REAL", "REST", "RISE", "SAID", "SAME", "SELL", "SHOW",
        "SIDE", "SOME", "SURE", "TAKE", "TELL", "THAN", "THAT", "THEM",
        "THEN", "THEY", "THIS", "TIME", "VERY", "WANT", "WEEK", "WELL",
        "WENT", "WERE", "WHAT", "WHEN", "WILL", "WITH", "WORK", "YEAR",
        "YOUR", "ZERO", "BEST", "BOTH", "BULL", "BEAR", "BOND", "CASH",
        "DARK", "DATA", "DEAL", "DROP", "DUMP", "EDIT", "EVER", "FACT",
        "FALL", "FAST", "FEAR", "FEEL", "FILL", "FLAT", "FLIP", "FLOW",
        "FREE", "FULL", "GAIN", "GAME", "GAVE", "GIVE", "GOES", "GONE",
        "GRAB", "GROW", "HALF", "HARD", "HATE", "HELP", "HOPE", "HUGE",
        "IDEA", "INFO", "JUMP", "LATE", "LEAD", "LESS", "LIVE", "LOAD",
        "LOSE", "LOST", "LOVE", "LUCK", "MAIN", "MEAN", "MEGA", "MISS",
        "MOON", "MOVE", "NEWS", "NICE", "NONE", "NOTE", "ONCE", "PAID",
        "PASS", "PAST", "PAYS", "PEAK", "PICK", "PLAY", "PLUS", "POLL",
        "POOR", "PULL", "PUMP", "PURE", "PUSH", "QUIT", "RACE", "RATE",
        "READ", "RICH", "RISK", "ROAD", "ROLE", "RULE", "RUNS", "RUSH",
        "SAFE", "SALE", "SAVE", "SEEN", "SEND", "SHOT", "SIGN", "SIZE",
        "SLOW", "SOLD", "SORT", "SPOT", "STAY", "STEP", "STOP", "TALK",
        "TANK", "TERM", "TEST", "THIN", "TIER", "TINY", "TIPS", "TOLD",
        "TOOK", "TOPS", "TRAP", "TREE", "TRIM", "TRUE", "TURN", "TYPE",
        "UNIT", "USED", "VAST", "VIEW", "VOTE", "WAIT", "WAKE", "WALK",
        "WALL", "WARN", "WAVE", "WEAK", "WILD", "WISE", "WORD", "WRAP",
        "YEAH",
    }

    for match in re.finditer(r'\b([A-Z]{1,5})\b', text):
        word = match.group(1)
        if word in STOCK_TICKERS and word not in UPPERCASE_EXCLUDE:
            found.add(word)

    # 3. Company name mentions
    text_lower = text.lower()
    for name, ticker in COMPANY_TO_TICKER.items():
        if name in text_lower:
            found.add(ticker)

    return sorted(found)


# ─── Sentiment Lexicon ─────────────────────────────────────────

# Finance-specific sentiment words with scores (-1.0 to 1.0)
# Positive scores = bullish, negative scores = bearish

SENTIMENT_LEXICON = {
    # Strong bullish (+0.7 to +1.0)
    "moon": 0.9, "mooning": 0.9, "moonshot": 0.9, "rocket": 0.8,
    "skyrocket": 0.9, "skyrocketing": 0.9, "surge": 0.8, "surging": 0.8,
    "soar": 0.8, "soaring": 0.8, "explode": 0.8, "explosive": 0.7,
    "breakout": 0.7, "parabolic": 0.8, "squeeze": 0.7,
    "tendies": 0.7, "lambo": 0.8, "diamond hands": 0.7,
    "undervalued": 0.7, "massive upside": 0.9, "gamma squeeze": 0.8,
    "short squeeze": 0.8, "to the moon": 0.9,

    # Moderate bullish (+0.3 to +0.6)
    "bullish": 0.6, "bull": 0.5, "calls": 0.4, "buy": 0.4,
    "buying": 0.4, "bought": 0.3, "long": 0.3, "rally": 0.5,
    "rallying": 0.5, "recovery": 0.4, "recovering": 0.4,
    "uptrend": 0.5, "breakeven": 0.2, "accumulate": 0.4,
    "accumulating": 0.4, "upgrade": 0.5, "upgraded": 0.5,
    "outperform": 0.5, "beat": 0.4, "beats": 0.4, "strong": 0.3,
    "strength": 0.3, "growth": 0.4, "growing": 0.4, "profit": 0.4,
    "profitable": 0.4, "gains": 0.4, "gain": 0.4, "positive": 0.3,
    "optimistic": 0.5, "confidence": 0.4, "innovation": 0.3,
    "opportunity": 0.3, "promising": 0.4, "momentum": 0.4,
    "winner": 0.5, "winning": 0.5, "green": 0.3, "rip": 0.4,
    "ripping": 0.5, "pump": 0.4, "pumping": 0.5, "load up": 0.4,
    "loaded": 0.3, "hold": 0.2, "holding": 0.2, "hodl": 0.3,

    # Mild positive (+0.1 to +0.2)
    "support": 0.2, "stable": 0.1, "steady": 0.1, "fair value": 0.1,
    "dividend": 0.2, "earnings": 0.1, "revenue": 0.1,

    # Mild negative (-0.1 to -0.2)
    "concern": -0.2, "concerned": -0.2, "uncertainty": -0.2,
    "volatile": -0.1, "volatility": -0.1, "risk": -0.1,
    "risky": -0.2, "overvalued": -0.2, "overbought": -0.2,
    "resistance": -0.1, "flat": -0.1, "stagnant": -0.2,

    # Moderate bearish (-0.3 to -0.6)
    "bearish": -0.6, "bear": -0.5, "puts": -0.4, "sell": -0.4,
    "selling": -0.4, "sold": -0.3, "short": -0.3, "shorting": -0.4,
    "downtrend": -0.5, "decline": -0.4, "declining": -0.4,
    "downgrade": -0.5, "downgraded": -0.5, "underperform": -0.5,
    "miss": -0.4, "missed": -0.4, "misses": -0.4, "weak": -0.3,
    "weakness": -0.3, "loss": -0.4, "losses": -0.4, "negative": -0.3,
    "pessimistic": -0.5, "red": -0.3, "dump": -0.4, "dumping": -0.5,
    "bag holder": -0.5, "bagholder": -0.5, "bagholding": -0.5,
    "paper hands": -0.4, "exit": -0.3, "cut losses": -0.4,
    "overextended": -0.3, "correction": -0.3, "pullback": -0.3,
    "dip": -0.2, "dipping": -0.3, "bleeding": -0.5, "bleed": -0.4,

    # Strong bearish (-0.7 to -1.0)
    "crash": -0.8, "crashing": -0.9, "tank": -0.7, "tanking": -0.8,
    "plunge": -0.8, "plunging": -0.8, "collapse": -0.9,
    "collapsing": -0.9, "freefall": -0.9, "free fall": -0.9,
    "bankrupt": -0.9, "bankruptcy": -0.9, "fraud": -0.8,
    "scam": -0.8, "ponzi": -0.9, "bubble": -0.6, "rug pull": -0.9,
    "rugpull": -0.9, "dead": -0.7, "worthless": -0.9,
    "disaster": -0.8, "catastrophe": -0.9, "panic": -0.7,
    "capitulation": -0.8, "margin call": -0.8, "liquidation": -0.7,
    "liquidated": -0.7, "wipeout": -0.9, "wiped out": -0.9,
    "rekt": -0.8, "destroyed": -0.7,
}


def score_sentiment(text: str) -> float:
    """Score the sentiment of financial text using a lexicon approach.

    Scans text for known sentiment words/phrases and computes
    a weighted average score.

    Args:
        text: The text to analyze.

    Returns:
        Float from -1.0 (extremely bearish) to 1.0 (extremely bullish).
        Returns 0.0 if no sentiment words found.
    """
    text_lower = text.lower()
    total_score = 0.0
    match_count = 0

    # Check multi-word phrases first (longer matches take priority)
    phrases_checked = set()
    for phrase, score in sorted(SENTIMENT_LEXICON.items(), key=lambda x: -len(x[0])):
        if " " in phrase and phrase in text_lower:
            total_score += score
            match_count += 1
            # Mark individual words in this phrase so they aren't double-counted
            for word in phrase.split():
                phrases_checked.add(word)

    # Check single words
    words = re.findall(r'[a-z]+', text_lower)
    for word in words:
        if word in phrases_checked:
            continue
        if word in SENTIMENT_LEXICON:
            total_score += SENTIMENT_LEXICON[word]
            match_count += 1

    if match_count == 0:
        return 0.0

    # Average, clamped to [-1, 1]
    avg = total_score / match_count
    return max(-1.0, min(1.0, avg))
