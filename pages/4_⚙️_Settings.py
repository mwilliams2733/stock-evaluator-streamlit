"""Settings — API key configuration, scoring weights, cache management."""
import streamlit as st
from config.settings import APP_TITLE

st.set_page_config(page_title=f"{APP_TITLE} - Settings", layout="wide", page_icon="⚙️")
st.title("Settings")
st.caption("Configure API keys, scoring parameters, and manage cache.")

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

# ===== Cache Management =====
st.subheader("Cache Management")

from data.cache import cache_stats, clear_cache

stats = cache_stats()
cache_col1, cache_col2, cache_col3 = st.columns(3)
with cache_col1:
    st.metric("Cached Files", stats["file_count"])
with cache_col2:
    st.metric("Cache Size", f"{stats['total_size_mb']} MB")
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

**Data Sources:**
- [Polygon.io](https://polygon.io) — Price data, financials, company details, options
- [Finnhub](https://finnhub.io) — P/E, ROE, beta, news sentiment, earnings calendar

**Scoring System:**
- Overall Score: EMA alignment + Institutional flow + Pre-breakout + Momentum + Volume
- Moat Score: 8-factor economic moat analysis (Gross Margin, ROE, Revenue Growth, Debt, Market Position, FCF, CCR, ROIC)
- Fair Value: 5-model weighted valuation (P/E, P/B, P/S, DCF, EV/EBITDA)
"""
)
