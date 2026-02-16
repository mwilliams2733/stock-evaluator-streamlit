"""Settings — API key configuration, scoring weights, cache management, learning engine."""
import streamlit as st
from config.settings import APP_TITLE

st.set_page_config(page_title=f"{APP_TITLE} - Settings", layout="wide", page_icon="⚙️")
st.title("Settings")
st.caption("Configure API keys, scoring parameters, manage cache, and view learning engine stats.")

# --- Initialize session state ---
if "polygon_api_key" not in st.session_state:
    from config.settings import POLYGON_API_KEY
    st.session_state["polygon_api_key"] = POLYGON_API_KEY

if "finnhub_api_key" not in st.session_state:
    from config.settings import FINNHUB_API_KEY
    st.session_state["finnhub_api_key"] = FINNHUB_API_KEY

# ===== API Keys =====
st.subheader("API Keys")

col1, col2 = st.columns(2)

with col1:
    polygon_key = st.text_input(
        "Polygon.io API Key",
        value=st.session_state.get("polygon_api_key", ""),
        type="password",
        help="Sign up at https://polygon.io — free tier available",
    )
    if polygon_key != st.session_state.get("polygon_api_key"):
        st.session_state["polygon_api_key"] = polygon_key
        st.success("Polygon API key updated!")

with col2:
    finnhub_key = st.text_input(
        "Finnhub API Key",
        value=st.session_state.get("finnhub_api_key", ""),
        type="password",
        help="Sign up at https://finnhub.io — free tier: 60 calls/min",
    )
    if finnhub_key != st.session_state.get("finnhub_api_key"):
        st.session_state["finnhub_api_key"] = finnhub_key
        st.success("Finnhub API key updated!")

# Status indicators
api_col1, api_col2 = st.columns(2)
with api_col1:
    if st.session_state.get("polygon_api_key"):
        st.success("Polygon API key configured")
    else:
        st.warning("Polygon API key not set — Scanner and Research require this")

with api_col2:
    if st.session_state.get("finnhub_api_key"):
        st.success("Finnhub API key configured")
    else:
        st.info("Finnhub API key not set — News/sentiment features will be limited")

st.divider()

# ===== Scanner Defaults =====
st.subheader("Scanner Defaults")

scan_col1, scan_col2, scan_col3, scan_col4 = st.columns(4)
with scan_col1:
    min_price = st.number_input(
        "Min Price ($)", value=5.0, min_value=0.5, step=0.5,
        key="settings_min_price",
    )
with scan_col2:
    min_volume = st.number_input(
        "Min Avg Volume", value=500_000, min_value=10_000, step=50_000,
        key="settings_min_volume",
    )
with scan_col3:
    min_score = st.number_input(
        "Min Overall Score", value=55, min_value=0, max_value=100, step=5,
        key="settings_min_score",
    )
with scan_col4:
    min_ema = st.number_input(
        "Min EMA Score", value=70, min_value=0, max_value=100, step=5,
        key="settings_min_ema",
    )

# Store defaults in session state
st.session_state["default_min_price"] = min_price
st.session_state["default_min_volume"] = min_volume
st.session_state["default_min_score"] = min_score
st.session_state["default_min_ema"] = min_ema

st.divider()

# ===== Learning Engine Stats =====
st.subheader("Learning Engine")
st.caption("Track trade outcomes and get adaptive threshold suggestions.")

try:
    from core.learning_engine import get_stats, analyze_outcomes, suggest_adjustments

    stats = get_stats()
    le_cols = st.columns(5)
    le_cols[0].metric("Total Trades", stats.get("total_trades", 0))
    le_cols[1].metric("Open", stats.get("open_trades", 0))
    le_cols[2].metric("Closed", stats.get("closed_trades", 0))
    le_cols[3].metric("Wins", stats.get("wins", 0))
    le_cols[4].metric("Losses", stats.get("losses", 0))

    if stats.get("closed_trades", 0) > 0:
        outcomes = analyze_outcomes()
        st.metric("Overall Win Rate", f"{outcomes.get('overall_win_rate', 0):.1f}%")
        st.metric("Avg Return", f"{outcomes.get('overall_avg_return', 0):+.1f}%")

        # Win rate by action
        by_action = outcomes.get("by_action", {})
        if by_action:
            with st.expander("Performance by Action"):
                for action, data in sorted(by_action.items()):
                    st.write(
                        f"**{action}**: {data.get('total', 0)} trades, "
                        f"{data.get('win_rate', 0):.0f}% win rate, "
                        f"{data.get('avg_return', 0):+.1f}% avg return"
                    )
                    expected_wr = data.get("expected_win_rate", 0)
                    if data.get("outperforming"):
                        st.caption(f"Outperforming expected {expected_wr:.0f}%")
                    elif expected_wr > 0:
                        st.caption(f"Below expected {expected_wr:.0f}%")

    # Threshold suggestions
    if stats.get("has_enough_data"):
        adjustments = suggest_adjustments()
        if adjustments.get("suggestions"):
            st.subheader("Suggested Adjustments")
            for sug in adjustments["suggestions"]:
                st.info(
                    f"**{sug['parameter']}**: "
                    f"Current={sug['current']} → Suggested={sug['suggested']} — "
                    f"{sug['reason']}"
                )
    elif stats.get("total_trades", 0) > 0:
        remaining = 10 - stats.get("closed_trades", 0)
        st.caption(f"Need {remaining} more closed trades for adaptive suggestions.")
    else:
        st.caption("Record trades in the Portfolio page to enable adaptive learning.")

except Exception as e:
    st.info(f"Learning engine not yet initialized. Start tracking trades to see stats.")

st.divider()

# ===== Portfolio Import/Export =====
st.subheader("Portfolio Import / Export")

try:
    from data.persistence import load_portfolios, export_portfolio_json, import_portfolio_json

    portfolios = load_portfolios()
    port_options = {pid: p["name"] for pid, p in portfolios.items()}

    export_col1, export_col2 = st.columns(2)

    with export_col1:
        st.markdown("#### Export Portfolio")
        export_port = st.selectbox(
            "Portfolio to Export",
            options=list(port_options.keys()),
            format_func=lambda x: port_options[x],
            key="settings_export_port",
        )
        json_str = export_portfolio_json(export_port)
        st.download_button(
            "Export JSON",
            data=json_str,
            file_name=f"portfolio_{export_port}.json",
            mime="application/json",
        )

    with export_col2:
        st.markdown("#### Import Portfolio")
        uploaded_json = st.text_area("Paste portfolio JSON", key="settings_import_json", height=150)
        if st.button("Import Portfolio"):
            if uploaded_json:
                result = import_portfolio_json(uploaded_json)
                if result:
                    st.success(f"Imported '{result.get('name', 'portfolio')}'")
                    st.rerun()
                else:
                    st.error("Invalid JSON format. Must contain 'symbols' list.")

except Exception:
    st.info("Portfolio system not initialized yet.")

st.divider()

# ===== Backtest Defaults =====
st.subheader("Backtest Defaults")

from config.signals import BACKTEST_CONFIG
bt_cols = st.columns(4)
bt_cols[0].metric("Holding Period", f"{BACKTEST_CONFIG['holding_period_days']}d")
bt_cols[1].metric("Target Return", f"+{BACKTEST_CONFIG['target_percent']}%")
bt_cols[2].metric("Stop Loss", f"-{BACKTEST_CONFIG['stop_percent']}%")
bt_cols[3].metric("Universe Size", "110 stocks")

st.caption("Backtest parameters can be customized on the Backtest page.")

st.divider()

# ===== Cache Management =====
st.subheader("Cache Management")

from data.cache import cache_stats, clear_cache

cache = cache_stats()
cache_col1, cache_col2, cache_col3 = st.columns(3)
with cache_col1:
    st.metric("Cached Files", cache["file_count"])
with cache_col2:
    st.metric("Cache Size", f"{cache['total_size_mb']} MB")
with cache_col3:
    if st.button("Clear Cache", type="secondary"):
        clear_cache()
        st.success("Cache cleared!")
        st.rerun()

st.divider()

# ===== About =====
st.subheader("About")
st.markdown(
    """
**Dynamic Momentum Screener** is a Streamlit port of the single-file React stock evaluator app.

**Pages:**
- **Scanner** — Full market scan with filter presets and sector watchlists
- **Research** — 9-tab deep-dive: Overview, Fair Value, Chart, News, Fundamentals, Gov Opportunities, Growth, ETF, Options
- **Stock Detail** — Quick single-stock lookup with chart and scores
- **Portfolio Hub** — 5-tab portfolio management with analysis, ETF breakdown, and forecasting
- **Backtest** — Historical strategy validation across 110 stocks
- **Alerts** — Price monitoring and alert system

**Data Sources:**
- [Polygon.io](https://polygon.io) — Price data, financials, company details, options
- [Finnhub](https://finnhub.io) — P/E, ROE, beta, news sentiment, earnings calendar
- [USAspending.gov](https://usaspending.gov) — Government contract data
- [Federal Register](https://federalregister.gov) — Government policy documents

**Scoring System:**
- Overall Score: EMA alignment + Institutional flow + Pre-breakout + Momentum + Volume
- 9-Level Recommendations: STRONG BUY through SELL with win probability
- Options Analysis: Rating, IV estimation, strategy suggestions
- Moat Score: 8-factor economic moat analysis
- Fair Value: 5-model weighted valuation
"""
)
