# Real-Time Market Sentiment Dashboard

An open-source market sentiment tool that continuously monitors Reddit, financial news RSS feeds, and SEC filings, stores sentiment-enriched memories, detects sentiment reversals, and provides an interactive Plotly-powered dashboard.

Built on top of the [Always-On Memory Agent](https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/ai_agent_tutorials/always_on_memory_agent) with **Google ADK** and **Gemini**.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Data Sources                          │
│  Reddit (WSB, stocks, investing)  │  RSS (Yahoo, MW)    │
│  SEC EDGAR (Form 4, 13F-HR)      │  Twitter (mock)     │
└──────────────────┬──────────────────────────────────────┘
                   │ fetcher_runner.py
                   ▼
┌─────────────────────────────────────────────────────────┐
│              Agent (agent.py)                           │
│  ┌──────────┐ ┌──────────────┐ ┌──────────┐           │
│  │  Ingest  │ │ Consolidate  │ │  Query   │           │
│  │  Agent   │ │    Agent     │ │  Agent   │           │
│  └──────────┘ └──────────────┘ └──────────┘           │
│  ┌──────────────┐ ┌────────────────────────┐          │
│  │  Sentiment   │ │  Reversal Detection    │          │
│  │    Agent     │ │  (check_sentiment_     │          │
│  │              │ │   reversals)           │          │
│  └──────────────┘ └────────────────────────┘          │
│  ┌──────────────────────────────────────────┐          │
│  │  SQLite: memories + alerts               │          │
│  │  sentiment.py: lexicon scoring           │          │
│  └──────────────────────────────────────────┘          │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP API (:8888)
                   ▼
┌─────────────────────────────────────────────────────────┐
│           Dashboard (dashboard.py)                      │
│  Ingest │ Query │ Sentiment │ Tickers │ Alerts │ Memory │
│         Plotly charts, leaderboards, reversal cards      │
└─────────────────────────────────────────────────────────┘
```

## Features

- **Multi-source ingestion**: Reddit (r/wallstreetbets, r/stocks, r/investing), RSS feeds (Yahoo Finance, MarketWatch), SEC EDGAR filings, mock Twitter data
- **Automatic sentiment scoring**: Finance-specific lexicon with ~200 bullish/bearish terms, zero API cost
- **Ticker extraction**: Regex + `$TICKER` patterns + company name mapping against ~150 known tickers
- **Sentiment reversal detection**: Compares 24h vs 7d average sentiment per ticker, alerts on significant shifts
- **Interactive dashboard**: 6-tab Streamlit UI with Plotly scatter charts, pie charts, leaderboards, and alert cards
- **Always-on agent**: Runs 24/7, auto-consolidates memories, detects patterns across sources

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your API key

```bash
export GOOGLE_API_KEY="your-gemini-api-key"
```

### 3. Start the agent

```bash
python agent.py
```

The agent starts on `http://localhost:8888` with endpoints:
- `GET /status` — Memory and sentiment stats
- `GET /memories` — All stored memories
- `GET /sentiment?ticker=NVDA&days=7` — Ticker sentiment data
- `GET /tickers` — Ticker leaderboard
- `GET /alerts` — Sentiment reversal alerts
- `POST /ingest` — Ingest text with `source_type`
- `POST /consolidate` — Trigger consolidation + reversal check

### 4. Start the fetchers

```bash
python fetcher_runner.py
```

Options:
```bash
python fetcher_runner.py --no-reddit        # skip Reddit
python fetcher_runner.py --no-rss           # skip RSS
python fetcher_runner.py --no-sec           # skip SEC EDGAR
python fetcher_runner.py --no-twitter       # skip mock Twitter
python fetcher_runner.py --reddit-only      # only Reddit
python fetcher_runner.py --agent-url http://localhost:9000
```

### 5. Start the dashboard

```bash
streamlit run dashboard.py
```

## Fetcher Documentation

### Reddit Fetcher
Hits Reddit's public JSON API (`reddit.com/r/{sub}/hot.json`) for r/wallstreetbets, r/stocks, and r/investing. No authentication required. Extracts post titles and self-text. Runs every 2 minutes by default.

### RSS Fetcher
Parses RSS 2.0 and Atom feeds using `xml.etree.ElementTree` (no feedparser dependency). Monitors Yahoo Finance and MarketWatch. Strips HTML from descriptions. Runs every 3 minutes.

### SEC EDGAR Fetcher
Queries the free public EDGAR full-text search API for Form 4 (insider transactions) and 13F-HR (institutional holdings) filings. Includes fallback to EDGAR's Atom feed. Runs every 5 minutes.

### Twitter Mock Fetcher
Generates 2-3 synthetic financial tweets per cycle from templates with randomized tickers, sentiment, and engagement metrics. For testing and demonstration only. Runs every 1 minute.

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/status` | GET | Memory stats + tracked tickers + active alerts |
| `/memories` | GET | All memories (limit 50) with sentiment + tickers |
| `/sentiment?ticker=X&days=N` | GET | Sentiment data for a specific ticker |
| `/tickers` | GET | Leaderboard: most mentioned, bullish, bearish |
| `/alerts` | GET | Active sentiment reversal alerts |
| `/ingest` | POST | Ingest text `{text, source, source_type}` |
| `/query?q=...` | GET | Query memories with natural language |
| `/consolidate` | POST | Trigger consolidation + reversal detection |
| `/delete` | POST | Delete memory `{memory_id}` |
| `/clear` | POST | Full reset (memories + alerts + inbox files) |

## Configuration

All configuration is in `config.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL` | `gemini-3.1-flash-lite-preview` | LLM model (env: `MODEL`) |
| `DB_PATH` | `sentiment.db` | SQLite database path (env: `MEMORY_DB`) |
| `REDDIT_INTERVAL` | 120s | Reddit fetch interval |
| `RSS_INTERVAL` | 180s | RSS fetch interval |
| `SEC_INTERVAL` | 300s | SEC EDGAR fetch interval |
| `TWITTER_MOCK_INTERVAL` | 60s | Mock Twitter interval |
| `REVERSAL_THRESHOLD` | 0.3 | Min delta for reversal alerts |

### Customizing Tickers

The `STOCK_TICKERS` set in `config.py` contains ~150 commonly discussed stock symbols used for ticker extraction. The `COMPANY_TO_TICKER` dictionary maps company names (e.g. "nvidia" -> "NVDA") so they're recognized in natural language text. You can freely add or remove entries from both to match the tickers you care about.

## Design Decisions

- **Lexicon-based sentiment** (not LLM): Deterministic, zero API cost, finance-specific vocabulary. The LLM handles summarization and entity extraction.
- **`source_type` via module-level variable**: More reliable than asking the LLM to forward metadata. Safe because ingests are serialized through the agent runner.
- **In-memory dedup in fetchers**: Simple and sufficient for long-running processes. The agent handles duplicate ingests gracefully.
- **Reversal detection in Python**: SQL averages + threshold comparison, runs every consolidation cycle without API cost.
- **Plotly for charts**: Interactive hover data ideal for financial time series; falls back to `st.line_chart` if not installed.

## Project Structure

```
real-time-market-sentiment/
├── agent.py              # Main ADK agent with sentiment extensions
├── dashboard.py          # Streamlit UI (6 tabs, Plotly charts)
├── config.py             # Central configuration
├── sentiment.py          # Ticker extraction + lexicon scoring
├── fetchers/
│   ├── __init__.py
│   ├── base.py           # Abstract BaseFetcher (dedup + post-to-agent)
│   ├── reddit.py         # Reddit public JSON API
│   ├── rss.py            # RSS 2.0 + Atom parser
│   ├── sec_edgar.py      # SEC EDGAR full-text search
│   └── twitter_mock.py   # Synthetic tweet generator
├── fetcher_runner.py     # Async fetcher orchestrator
├── requirements.txt      # Python dependencies
├── .gitignore
├── LICENSE               # MIT
├── docs/                 # Logo assets
└── inbox/                # File drop folder
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run the agent and dashboard to verify
5. Commit your changes (`git commit -am 'Add my feature'`)
6. Push to the branch (`git push origin feature/my-feature`)
7. Open a Pull Request

### Ideas for contributions:
- Add more RSS feeds (Bloomberg, Reuters, CNBC)
- Implement real Twitter/X API integration (requires API key)
- Add email alerts for sentiment reversals
- Build a backtesting module for sentiment signals
- Add support for crypto tickers
- Implement a more sophisticated NLP sentiment model
- Add options flow analysis

## License

MIT License - see [LICENSE](LICENSE) for details.
