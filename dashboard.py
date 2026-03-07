"""
Real-Time Market Sentiment — Dashboard

Streamlit UI with 6 tabs: Ingest, Query, Sentiment, Tickers, Alerts, Memory Bank.
Includes Plotly-powered interactive charts for sentiment analysis.

Usage:
    # First start the agent:
    python agent.py

    # Then start the dashboard:
    streamlit run dashboard.py
"""

import json
import time
from pathlib import Path

import requests
import streamlit as st

try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

AGENT_URL = "http://localhost:8888"
INBOX_DIR = Path("./inbox")

UPLOAD_EXTENSIONS = [
    "txt", "md", "json", "csv", "log", "xml", "yaml", "yml",
    "png", "jpg", "jpeg", "gif", "webp", "bmp", "svg",
    "mp3", "wav", "ogg", "flac", "m4a", "aac",
    "mp4", "webm", "mov", "avi", "mkv",
    "pdf",
]

SAMPLE_TEXTS = [
    {
        "title": "NVDA Bullish Post",
        "text": (
            "$NVDA is absolutely crushing it! Q4 earnings blew past estimates. "
            "Data center revenue up 400% YoY. AI demand is insatiable. "
            "Jensen Huang is a visionary. Buying more calls. To the moon!"
        ),
    },
    {
        "title": "TSLA Bear Case",
        "text": (
            "Tesla margins are declining rapidly. Competition from BYD and other "
            "Chinese EVs is crushing their market share. $TSLA is massively "
            "overvalued at these levels. Cybertruck demand disappointing. Shorting."
        ),
    },
    {
        "title": "Market Crash Warning",
        "text": (
            "The yield curve inversion is screaming recession. VIX is spiking. "
            "$SPY forming a massive head and shoulders pattern. Smart money is "
            "dumping stocks. Panic selling could accelerate. Get to cash now."
        ),
    },
    {
        "title": "Reddit WSB Sentiment",
        "text": (
            "The apes are back! $GME short interest is building again. "
            "Diamond hands holding strong. Meanwhile $PLTR just got a massive "
            "government contract. Both looking bullish for a squeeze play."
        ),
    },
]


def api_get(path: str) -> dict | None:
    try:
        r = requests.get(f"{AGENT_URL}{path}", timeout=30)
        return r.json()
    except Exception as e:
        st.error(f"Agent not reachable: {e}")
        return None


def api_post(path: str, data: dict) -> dict | None:
    try:
        r = requests.post(f"{AGENT_URL}{path}", json=data, timeout=60)
        return r.json()
    except Exception as e:
        st.error(f"Agent not reachable: {e}")
        return None


def sentiment_badge(score: float | None) -> str:
    """Return an HTML badge for a sentiment score."""
    if score is None:
        return ""
    if score >= 0.3:
        color, bg, label = "#4ade80", "rgba(74,222,128,0.15)", f"+{score:.2f}"
    elif score <= -0.3:
        color, bg, label = "#ef4444", "rgba(239,68,68,0.15)", f"{score:.2f}"
    else:
        color, bg, label = "#fbbf24", "rgba(251,191,36,0.15)", f"{score:.2f}"
    return f'<span style="background:{bg}; color:{color}; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:600;">{label}</span>'


def ticker_badges(tickers: list) -> str:
    """Return HTML badges for ticker symbols."""
    return "".join(
        f'<span style="background:rgba(59,130,246,0.2); color:#60a5fa; padding:2px 8px; '
        f'border-radius:12px; font-size:11px; font-weight:600;">${t}</span> '
        for t in tickers
    )


def source_badge(source_type: str) -> str:
    """Return an HTML badge for source type."""
    colors = {
        "reddit": ("#ff4500", "rgba(255,69,0,0.15)"),
        "rss": ("#fbbf24", "rgba(251,191,36,0.15)"),
        "sec_edgar": ("#818cf8", "rgba(129,140,248,0.15)"),
        "twitter": ("#1da1f2", "rgba(29,161,242,0.15)"),
        "file": ("#a78bfa", "rgba(167,139,250,0.15)"),
    }
    color, bg = colors.get(source_type, ("#666", "rgba(102,102,102,0.15)"))
    if not source_type:
        return ""
    return f'<span style="background:{bg}; color:{color}; padding:2px 8px; border-radius:12px; font-size:10px;">{source_type}</span>'


def render_memory_card(m: dict):
    entities = m.get("entities", [])
    topics = m.get("topics", [])
    connections = m.get("connections", [])
    importance = m.get("importance", 0.5)
    sentiment = m.get("sentiment")
    tickers = m.get("tickers", [])
    src_type = m.get("source_type", "")

    border_color = "#4ade80" if importance >= 0.7 else "#fbbf24" if importance >= 0.4 else "#555"

    badges_html = ""
    if sentiment is not None:
        badges_html += sentiment_badge(sentiment) + " "
    if tickers:
        badges_html += ticker_badges(tickers)
    if src_type:
        badges_html += source_badge(src_type)

    st.markdown(
        f"""<div style="border-left: 3px solid {border_color}; padding: 8px 16px;
        margin: 8px 0; background: rgba(255,255,255,0.02); border-radius: 0 8px 8px 0;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="color: #ddd;">Memory #{m['id']}</strong>
            <span style="font-size: 11px; color: #666;">{m.get('created_at', '')[:16]}
            {' | ' + m.get('source', '') if m.get('source') else ''}</span>
        </div>
        <p style="color: #bbb; margin: 8px 0; font-size: 14px;">{m['summary']}</p>
        <div style="display: flex; gap: 6px; flex-wrap: wrap; align-items: center;">
            {badges_html}
            {''.join(f'<span style="background: rgba(139,92,246,0.15); color: #c4b5fd; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{t}</span>' for t in topics)}
            {''.join(f'<span style="background: rgba(59,130,246,0.08); color: #93c5fd; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{e}</span>' for e in entities[:5])}
        </div>
        {'<div style="margin-top: 6px; font-size: 11px; color: #666;">connections: ' + str(len(connections)) + '</div>' if connections else ''}
        </div>""",
        unsafe_allow_html=True,
    )


def render_alert_card(alert: dict):
    """Render a sentiment reversal alert card."""
    old = alert.get("old_sentiment", 0)
    new = alert.get("new_sentiment", 0)
    delta = abs(new - old)

    # Severity coloring
    if delta >= 0.5:
        border, severity = "#ef4444", "HIGH"
    elif delta >= 0.3:
        border, severity = "#fbbf24", "MEDIUM"
    else:
        border, severity = "#818cf8", "LOW"

    direction = "BULLISH" if new > old else "BEARISH"
    direction_color = "#4ade80" if new > old else "#ef4444"

    st.markdown(
        f"""<div style="border-left: 4px solid {border}; padding: 12px 16px;
        margin: 8px 0; background: rgba(255,255,255,0.02); border-radius: 0 8px 8px 0;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span style="font-size:18px; font-weight:700; color:#ddd;">${alert['ticker']}</span>
                <span style="background:{border}22; color:{border}; padding:2px 8px; border-radius:4px;
                    font-size:10px; font-weight:700; margin-left:8px;">{severity}</span>
                <span style="background:{direction_color}22; color:{direction_color}; padding:2px 8px;
                    border-radius:4px; font-size:10px; font-weight:700; margin-left:4px;">{direction}</span>
            </div>
            <span style="font-size: 11px; color: #666;">{alert.get('created_at', '')[:16]}</span>
        </div>
        <p style="color: #999; margin: 8px 0 4px; font-size: 13px;">{alert['message']}</p>
        <div style="display:flex; gap:16px; font-size:12px; color:#888;">
            <span>7d avg: <strong style="color:#ddd;">{old:+.2f}</strong></span>
            <span>24h avg: <strong style="color:{direction_color};">{new:+.2f}</strong></span>
            <span>Delta: <strong style="color:{border};">{delta:.2f}</strong></span>
        </div>
        </div>""",
        unsafe_allow_html=True,
    )


def main():
    st.set_page_config(page_title="Market Sentiment Dashboard", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

    st.markdown(
        """<style>
        .stApp { background-color: #0a0a0f; }
        .stMarkdown { color: #e8e8e8; }
        .stTextInput > div > div > input { background: #12121a; color: #e8e8e8; border-color: #222; }
        .stTextArea > div > div > textarea { background: #12121a; color: #e8e8e8; border-color: #222; }
        section[data-testid="stSidebar"] { background: #08080d; }
        .stat-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
            border-radius: 12px; padding: 16px; text-align: center; }
        .stat-number { font-size: 28px; font-weight: 700; color: #c4b5fd; }
        .stat-label { font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.1em; }
        </style>""",
        unsafe_allow_html=True,
    )

    # Sidebar
    with st.sidebar:
        st.markdown("### Agent Status")
        stats = api_get("/status")
        if stats:
            st.markdown(f'<div class="stat-card" style="margin-bottom:8px;"><div class="stat-number" style="color:#4ade80;">Online</div><div class="stat-label">Agent Status</div></div>', unsafe_allow_html=True)
            st.markdown("### Memory Stats")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f'<div class="stat-card"><div class="stat-number">{stats.get("total_memories", 0)}</div><div class="stat-label">Memories</div></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="stat-card"><div class="stat-number">{stats.get("unconsolidated", 0)}</div><div class="stat-label">Pending</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="stat-card" style="margin-top:8px;"><div class="stat-number">{stats.get("consolidations", 0)}</div><div class="stat-label">Consolidations</div></div>', unsafe_allow_html=True)

            st.markdown("### Sentiment Stats")
            col3, col4 = st.columns(2)
            with col3:
                st.markdown(f'<div class="stat-card"><div class="stat-number" style="color:#60a5fa;">{stats.get("tracked_tickers", 0)}</div><div class="stat-label">Tickers</div></div>', unsafe_allow_html=True)
            with col4:
                st.markdown(f'<div class="stat-card"><div class="stat-number" style="color:#fbbf24;">{stats.get("active_alerts", 0)}</div><div class="stat-label">Alerts</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="stat-card" style="margin-bottom:8px;"><div class="stat-number" style="color:#ef4444;">Offline</div><div class="stat-label">Agent Status</div></div>', unsafe_allow_html=True)
            st.info("Start the agent:\n```\npython agent.py\n```")

        st.markdown("---")
        st.markdown("<p style='text-align: center; color: #555; font-size: 11px; text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 12px;'>Powered by</p>", unsafe_allow_html=True)
        logo_col1, logo_col2 = st.columns(2)
        with logo_col1:
            if Path("docs/Gemini_logo.png").exists():
                st.image("docs/Gemini_logo.png", use_container_width=True)
        with logo_col2:
            if Path("docs/adk_logo.png").exists():
                st.image("docs/adk_logo.png", width=90)
        st.caption(f"Endpoint: `{AGENT_URL}`")

    # Main header
    st.markdown(
        """<div style="text-align: center; padding: 20px 0 10px;">
        <span style="font-size: 48px;">📈</span>
        <h1 style="background: linear-gradient(to right, #4ade80, #60a5fa);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            font-size: 36px; margin: 8px 0 4px;">Real-Time Market Sentiment</h1>
        <p style="color: #666; font-size: 14px; max-width: 700px; margin: 0 auto;">
            Continuously monitors Reddit, financial news, and SEC filings for market sentiment.<br>
            Powered by <strong style="color: #60a5fa;">Google ADK</strong> + <strong style="color: #4ade80;">Gemini</strong>.
            Detects sentiment reversals in real time.
        </p>
        </div>""",
        unsafe_allow_html=True,
    )

    tab_ingest, tab_query, tab_sentiment, tab_tickers, tab_alerts, tab_memories = st.tabs(
        ["Ingest", "Query", "Sentiment", "Tickers", "Alerts", "Memory Bank"]
    )

    # ─── Tab 1: Ingest ────────────────────────────────────────
    with tab_ingest:
        st.markdown("#### Feed information into memory")
        st.markdown("<p style='color: #666; font-size: 13px;'>Paste financial text or drop files. Sentiment and tickers are extracted automatically.</p>", unsafe_allow_html=True)

        input_text = st.text_area("Input", height=150, placeholder="Paste financial news, Reddit posts, or market commentary...", label_visibility="collapsed")

        col_ingest, col_samples = st.columns([1, 1])
        with col_ingest:
            source_type = st.selectbox("Source type", ["", "reddit", "rss", "sec_edgar", "twitter", "manual"], index=0)
            if st.button("Process into Memory", type="primary", use_container_width=True):
                if input_text.strip():
                    with st.spinner("IngestAgent processing..."):
                        t0 = time.time()
                        result = api_post("/ingest", {"text": input_text, "source": "dashboard", "source_type": source_type})
                        elapsed = time.time() - t0
                    if result:
                        st.success(f"Processed in {elapsed:.1f}s")
                        st.markdown(result.get("response", ""))

        with col_samples:
            st.markdown("<p style='color: #555; font-size: 12px;'>Or try a sample:</p>", unsafe_allow_html=True)
            for s in SAMPLE_TEXTS:
                if st.button(s["title"], use_container_width=True):
                    with st.spinner("IngestAgent processing..."):
                        t0 = time.time()
                        result = api_post("/ingest", {"text": s["text"], "source": s["title"], "source_type": "manual"})
                        elapsed = time.time() - t0
                    if result:
                        st.success(f"**{s['title']}** processed in {elapsed:.1f}s")
                        st.markdown(result.get("response", ""))

        st.markdown("---")
        st.markdown("#### Upload Files")
        st.markdown("<p style='color: #666; font-size: 13px;'>Upload files to <code>./inbox</code> for automatic processing.</p>", unsafe_allow_html=True)

        uploaded_files = st.file_uploader("Drop files here", type=UPLOAD_EXTENSIONS, accept_multiple_files=True, label_visibility="collapsed")

        if uploaded_files:
            INBOX_DIR.mkdir(parents=True, exist_ok=True)
            for uf in uploaded_files:
                dest = INBOX_DIR / uf.name
                if dest.exists():
                    st.warning(f"**{uf.name}** already exists in inbox, skipping.")
                    continue
                dest.write_bytes(uf.getvalue())
                st.success(f"**{uf.name}** saved to inbox - agent will process it shortly.")

        st.markdown("---")
        st.markdown("#### Consolidate Memories")
        if st.button("Run Consolidation", use_container_width=True):
            with st.spinner("ConsolidateAgent processing..."):
                t0 = time.time()
                result = api_post("/consolidate", {})
                elapsed = time.time() - t0
            if result:
                st.success(f"Consolidated in {elapsed:.1f}s")
                st.markdown(result.get("response", ""))
                if result.get("new_alerts", 0):
                    st.warning(f"Created {result['new_alerts']} new sentiment reversal alert(s)!")

    # ─── Tab 2: Query ─────────────────────────────────────────
    with tab_query:
        st.markdown("#### Ask your memory anything")
        st.markdown("<p style='color: #666; font-size: 13px;'>The <strong>QueryAgent</strong> searches all memories and synthesizes answers.</p>", unsafe_allow_html=True)

        question = st.text_input("Question", placeholder="What's the sentiment on NVDA?", label_visibility="collapsed")

        sample_qs = [
            "What are the most discussed tickers?",
            "What's the overall market sentiment?",
            "Are there any bearish signals?",
            "Summarize the latest financial news.",
        ]
        cols = st.columns(2)
        for i, sq in enumerate(sample_qs):
            with cols[i % 2]:
                if st.button(f"{sq}", key=f"sq_{i}", use_container_width=True):
                    question = sq

        if question:
            with st.spinner("QueryAgent searching memory..."):
                t0 = time.time()
                result = api_get(f"/query?q={question}")
                elapsed = time.time() - t0
            if result:
                st.markdown(
                    f"""<div style="background: rgba(96,165,250,0.05); border: 1px solid rgba(96,165,250,0.15);
                    border-radius: 12px; padding: 20px; margin: 16px 0;">
                    <span style="font-size: 12px; color: #60a5fa;">{elapsed:.1f}s</span>
                    <div style="color: #ddd; line-height: 1.7; margin-top: 8px;">{result.get('answer', '')}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

    # ─── Tab 3: Sentiment ─────────────────────────────────────
    with tab_sentiment:
        st.markdown("#### Ticker Sentiment Analysis")

        col_ticker, col_days = st.columns([2, 1])
        with col_ticker:
            ticker_input = st.text_input("Ticker Symbol", value="NVDA", placeholder="e.g. NVDA, TSLA, SPY").strip().upper()
        with col_days:
            days_input = st.slider("Lookback (days)", min_value=1, max_value=30, value=7)

        if ticker_input:
            data = api_get(f"/sentiment?ticker={ticker_input}&days={days_input}")
            if data:
                # Metric cards
                col_avg, col_count, col_trend = st.columns(3)
                avg_sent = data.get("avg_sentiment", 0)
                mention_count = data.get("mention_count", 0)

                avg_color = "#4ade80" if avg_sent > 0.1 else "#ef4444" if avg_sent < -0.1 else "#fbbf24"
                with col_avg:
                    st.markdown(f'<div class="stat-card"><div class="stat-number" style="color:{avg_color};">{avg_sent:+.3f}</div><div class="stat-label">Avg Sentiment</div></div>', unsafe_allow_html=True)
                with col_count:
                    st.markdown(f'<div class="stat-card"><div class="stat-number">{mention_count}</div><div class="stat-label">Mentions</div></div>', unsafe_allow_html=True)
                with col_trend:
                    trend = "Bullish" if avg_sent > 0.1 else "Bearish" if avg_sent < -0.1 else "Neutral"
                    trend_color = avg_color
                    st.markdown(f'<div class="stat-card"><div class="stat-number" style="color:{trend_color}; font-size:20px;">{trend}</div><div class="stat-label">Trend</div></div>', unsafe_allow_html=True)

                data_points = data.get("data_points", [])
                if data_points and HAS_PLOTLY and HAS_PANDAS:
                    df = pd.DataFrame(data_points)
                    df["created_at"] = pd.to_datetime(df["created_at"])

                    # Scatter chart colored by source_type
                    fig = px.scatter(
                        df, x="created_at", y="sentiment",
                        color="source_type",
                        title=f"${ticker_input} Sentiment Over Time",
                        labels={"created_at": "Time", "sentiment": "Sentiment Score", "source_type": "Source"},
                        color_discrete_map={
                            "reddit": "#ff4500", "rss": "#fbbf24",
                            "sec_edgar": "#818cf8", "twitter": "#1da1f2",
                            "file": "#a78bfa", "manual": "#888",
                        },
                    )
                    fig.update_layout(
                        plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
                        font_color="#ddd",
                        xaxis=dict(gridcolor="#222"), yaxis=dict(gridcolor="#222", range=[-1.1, 1.1]),
                    )
                    fig.add_hline(y=0, line_dash="dash", line_color="#444")
                    st.plotly_chart(fig, use_container_width=True)

                    # Source breakdown pie chart
                    source_breakdown = data.get("source_breakdown", {})
                    if source_breakdown:
                        fig_pie = px.pie(
                            values=list(source_breakdown.values()),
                            names=list(source_breakdown.keys()),
                            title="Source Breakdown",
                            color=list(source_breakdown.keys()),
                            color_discrete_map={
                                "reddit": "#ff4500", "rss": "#fbbf24",
                                "sec_edgar": "#818cf8", "twitter": "#1da1f2",
                                "file": "#a78bfa", "manual": "#888",
                            },
                        )
                        fig_pie.update_layout(
                            plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
                            font_color="#ddd",
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)
                elif data_points:
                    # Fallback without plotly
                    st.line_chart([d["sentiment"] for d in data_points])
                else:
                    st.info(f"No sentiment data for ${ticker_input} in the last {days_input} days.")

    # ─── Tab 4: Tickers ───────────────────────────────────────
    with tab_tickers:
        st.markdown("#### Ticker Leaderboard (Last 7 Days)")

        data = api_get("/tickers")
        if data:
            col_mentioned, col_bullish, col_bearish = st.columns(3)

            with col_mentioned:
                st.markdown("##### Most Mentioned")
                for item in data.get("most_mentioned", []):
                    avg = item["avg_sentiment"]
                    color = "#4ade80" if avg > 0.1 else "#ef4444" if avg < -0.1 else "#fbbf24"
                    st.markdown(
                        f'<div style="display:flex; justify-content:space-between; padding:6px 0; '
                        f'border-bottom:1px solid #1a1a2e;">'
                        f'<span style="color:#ddd; font-weight:600;">${item["ticker"]}</span>'
                        f'<span style="color:#888;">{item["mentions"]} mentions</span>'
                        f'<span style="color:{color};">{avg:+.2f}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            with col_bullish:
                st.markdown("##### Most Bullish")
                for item in data.get("most_bullish", []):
                    st.markdown(
                        f'<div style="display:flex; justify-content:space-between; padding:6px 0; '
                        f'border-bottom:1px solid #1a1a2e;">'
                        f'<span style="color:#ddd; font-weight:600;">${item["ticker"]}</span>'
                        f'<span style="color:#4ade80; font-weight:700;">{item["avg_sentiment"]:+.3f}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            with col_bearish:
                st.markdown("##### Most Bearish")
                for item in data.get("most_bearish", []):
                    st.markdown(
                        f'<div style="display:flex; justify-content:space-between; padding:6px 0; '
                        f'border-bottom:1px solid #1a1a2e;">'
                        f'<span style="color:#ddd; font-weight:600;">${item["ticker"]}</span>'
                        f'<span style="color:#ef4444; font-weight:700;">{item["avg_sentiment"]:+.3f}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            # Full dataframe
            if HAS_PANDAS:
                st.markdown("---")
                st.markdown("##### All Tracked Tickers")
                all_items = data.get("most_mentioned", [])
                if all_items:
                    df = pd.DataFrame(all_items)
                    df = df.rename(columns={"ticker": "Ticker", "mentions": "Mentions", "avg_sentiment": "Avg Sentiment"})
                    st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown(f"<p style='color:#666; font-size:12px; margin-top:8px;'>Total tracked tickers: {data.get('total_tickers', 0)}</p>", unsafe_allow_html=True)
        else:
            st.info("No ticker data available yet. Ingest some financial content first.")

    # ─── Tab 5: Alerts ────────────────────────────────────────
    with tab_alerts:
        st.markdown("#### Sentiment Reversal Alerts")
        st.markdown("<p style='color: #666; font-size: 13px;'>Alerts are triggered when a ticker's 24h average sentiment diverges significantly from its 7-day average.</p>", unsafe_allow_html=True)

        data = api_get("/alerts")
        if data and data.get("alerts"):
            for alert in data["alerts"]:
                render_alert_card(alert)
        else:
            st.info("No active alerts. Alerts are generated during consolidation when sentiment reversals are detected.")

        st.markdown("---")
        if st.button("Check for Reversals Now", use_container_width=True):
            with st.spinner("Checking sentiment reversals..."):
                result = api_post("/consolidate", {})
            if result:
                new_alerts = result.get("new_alerts", 0)
                if new_alerts:
                    st.success(f"Found {new_alerts} new reversal alert(s)!")
                    st.rerun()
                else:
                    st.info("No new reversals detected.")

    # ─── Tab 6: Memory Bank ───────────────────────────────────
    with tab_memories:
        st.markdown("#### Stored Memories")
        data = api_get("/memories")
        if data and data.get("memories"):
            for m in data["memories"]:
                col_card, col_del = st.columns([10, 1])
                with col_card:
                    render_memory_card(m)
                with col_del:
                    if st.button("X", key=f"del_{m['id']}", help=f"Delete memory #{m['id']}"):
                        result = api_post("/delete", {"memory_id": m["id"]})
                        if result and result.get("status") == "deleted":
                            st.toast(f"Deleted memory #{m['id']}")
                            st.rerun()

            st.markdown("---")
            with st.expander("Danger Zone"):
                st.markdown("<p style='color: #ef4444; font-size: 13px;'>This will permanently delete all memories, consolidations, alerts, and inbox files.</p>", unsafe_allow_html=True)
                if st.button("Clear All Memories", type="primary", use_container_width=True):
                    result = api_post("/clear", {})
                    if result:
                        st.toast(f"Cleared {result.get('memories_deleted', 0)} memories")
                        st.rerun()
        else:
            st.info("No memories yet. Ingest some information or start the fetchers.")


if __name__ == "__main__":
    main()
