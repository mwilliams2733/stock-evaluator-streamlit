"""Dynamic Momentum Screener — Stock Evaluation & Pre-Breakout Detection."""
import streamlit as st
from config.settings import APP_TITLE, APP_ICON

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Dynamic Momentum Screener")
st.markdown("Pre-breakout detection, institutional flow analysis, and technical scoring")

# --- Quick Start ---
st.subheader("Quick Start")
col1, col2, col3 = st.columns(3)
with col1:
    st.page_link("pages/1_🔍_Scanner.py", label="Run Scanner", icon="🔍", use_container_width=True)
with col2:
    st.page_link("pages/2_📊_Research.py", label="Research Panel", icon="📊", use_container_width=True)
with col3:
    st.page_link("pages/4_⚙️_Settings.py", label="Settings", icon="⚙️", use_container_width=True)

st.divider()

# --- How to Use ---
with st.expander("How to Use This App"):
    st.markdown(
        """
### Getting Started
1. Go to **Settings** in the sidebar and enter your **Polygon.io** and **Finnhub** API keys
2. Run the **Scanner** to discover high-scoring momentum stocks
3. Click any stock to open the full **Research Panel** with 8 analysis tabs

### Pages
- **Scanner** — Full market scan with EMA alignment, institutional flow, and pre-breakout detection
- **Research** — 8-tab deep-dive: Overview, Fair Value, Chart, News, Fundamentals, Gov Opportunities, Growth, ETF
- **Stock Detail** — Quick single-stock lookup with chart and scores
- **Settings** — API keys, scoring weights, cache management

### Understanding the Scores

**Overall Score (0-100)** — Weighted composite of:
- **EMA Alignment** (35%) — Price vs 8/21/50/200 EMAs + stacking order
- **Institutional Flow** (20%) — Volume-price trends, OBV, A/D line
- **Pre-Breakout** (15%) — Consolidation, volume patterns, Bollinger squeeze
- **20-Day Momentum** (10%) — Medium-term price trend
- **Volume Ratio** (10%) — Current vs average volume
- **5-Day Momentum** (5%) — Short-term price trend
- **RSI Quality** (5%) — RSI in healthy bullish zone

**Moat Score (0-100)** — 8-factor economic moat:
- Gross Margin (20%), ROE (15%), Revenue Growth (12%), Low Debt (13%)
- Market Position (12%), FCF Quality (8%), Cash Conversion (10%), ROIC (10%)

**Fair Value** — 5-model weighted average:
- P/E Multiple, P/B Multiple, P/S Multiple, Simple DCF, EV/EBITDA
"""
    )

# --- Initialize session state ---
if "polygon_api_key" not in st.session_state:
    from config.settings import POLYGON_API_KEY
    st.session_state["polygon_api_key"] = POLYGON_API_KEY

if "finnhub_api_key" not in st.session_state:
    from config.settings import FINNHUB_API_KEY
    st.session_state["finnhub_api_key"] = FINNHUB_API_KEY

if "scan_results" not in st.session_state:
    st.session_state["scan_results"] = None

if "research_ticker" not in st.session_state:
    st.session_state["research_ticker"] = ""
