"""Research — 8-tab deep-dive analysis panel."""
import datetime as dt

import plotly.graph_objects as go
import streamlit as st

from config.settings import APP_TITLE
from config.themes import GOVERNMENT_THEMES, INVESTMENT_THEMES
from core.scanner import analyze_single_stock
from data.polygon_client import PolygonData
from data.finnhub_client import FinnhubData
from utils.formatting import (
    format_price, format_pct, format_large_number, format_ratio,
    score_color, moat_color, confidence_color,
)

st.set_page_config(page_title=f"{APP_TITLE} - Research", layout="wide", page_icon="📊")
st.title("Research Panel")

# --- Initialize session state ---
if "polygon_api_key" not in st.session_state:
    from config.settings import POLYGON_API_KEY
    st.session_state["polygon_api_key"] = POLYGON_API_KEY
if "finnhub_api_key" not in st.session_state:
    from config.settings import FINNHUB_API_KEY
    st.session_state["finnhub_api_key"] = FINNHUB_API_KEY

api_key = st.session_state.get("polygon_api_key", "")
if not api_key:
    st.warning("Please set your Polygon API key in the **Settings** page.")
    st.stop()

# --- Ticker Input ---
col_input, col_btn = st.columns([3, 1])
with col_input:
    default_ticker = st.session_state.get("research_ticker", "AAPL")
    ticker = st.text_input("Enter Ticker Symbol", value=default_ticker, key="research_input").upper().strip()
with col_btn:
    st.write("")  # spacing
    run_research = st.button("Analyze", type="primary", use_container_width=True)

if run_research or (ticker and ticker != st.session_state.get("_last_research_ticker")):
    st.session_state["research_ticker"] = ticker
    st.session_state["_last_research_ticker"] = ticker

    with st.spinner(f"Analyzing {ticker}..."):
        polygon = PolygonData(api_key)
        finnhub_key = st.session_state.get("finnhub_api_key", "")
        finnhub = FinnhubData(finnhub_key) if finnhub_key else None
        data = analyze_single_stock(ticker, polygon, finnhub)
        st.session_state["research_data"] = data

data = st.session_state.get("research_data")
if not data or not data.get("price"):
    st.info("Enter a ticker symbol and click Analyze to begin.")
    st.stop()

# ===== TABS =====
tab_overview, tab_fair_value, tab_chart, tab_news, tab_fundamentals, tab_gov, tab_growth, tab_etf = st.tabs([
    "Overview", "Fair Value", "Chart", "News", "Fundamentals", "Gov Opportunities", "Growth", "ETF Breakdown"
])

# ===== TAB 1: OVERVIEW =====
with tab_overview:
    company = data.get("company_details", {})
    overall = data.get("overall_score", {})
    technicals = data.get("technicals", {})
    moat = data.get("moat", {})
    inst = data.get("institutional_flow", {})
    breakout = data.get("breakout", {})

    # Header metrics row
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Price", format_price(data["price"]))
    m2.metric("Overall Score", f"{overall.get('score', 'N/A')}", help="0-100 composite score")
    m3.metric("EMA Score", f"{technicals.get('ema_score', 'N/A')}", help="EMA alignment 0-100")
    m4.metric("Moat", f"{moat.get('moat_score', 'N/A')}", help=moat.get("moat_rating", ""))
    m5.metric("RSI", f"{technicals.get('rsi', 0):.0f}" if technicals.get("rsi") else "N/A")

    st.divider()

    # Company info
    if company.get("name"):
        st.subheader(f"{company['name']} ({data['ticker']})")
        if company.get("sic_description"):
            st.caption(company["sic_description"])
        info_cols = st.columns(4)
        info_cols[0].metric("Market Cap", format_large_number(company.get("market_cap")))
        info_cols[1].metric("Employees", f"{company.get('total_employees', 'N/A'):,}" if company.get("total_employees") else "N/A")
        info_cols[2].metric("Inst. Flow", inst.get("signal", "N/A"))
        info_cols[3].metric("Breakout", breakout.get("pattern", "N/A"))

    # Score breakdown
    st.subheader("Score Breakdown")
    score_cols = st.columns(5)
    score_cols[0].metric("Overall", overall.get("score", "N/A"))
    score_cols[1].metric("EMA Alignment", technicals.get("ema_score", "N/A"))
    score_cols[2].metric("Inst. Flow", inst.get("score", "N/A"))
    score_cols[3].metric("Breakout", breakout.get("score", "N/A"))
    score_cols[4].metric("ADX", f"{technicals.get('adx', 0):.0f}" if technicals.get("adx") else "N/A")

    # Moat Score Breakdown
    if moat.get("factors"):
        st.subheader(f"Moat Score: {moat.get('moat_score', 'N/A')} ({moat.get('moat_rating', '')})")
        max_scores = moat.get("max_scores", {})
        factors = moat.get("factors", {})
        factor_labels = {
            "grossMargin": "Gross Margin",
            "roe": "ROE",
            "revenueGrowth": "Revenue Growth",
            "lowDebt": "Low Debt",
            "marketPosition": "Market Position",
            "fcf": "Free Cash Flow",
            "ccr": "Cash Conversion",
            "roic": "ROIC",
        }
        for key, label in factor_labels.items():
            val = factors.get(key)
            max_val = max_scores.get(key, 10)
            if val is not None:
                pct = val / max_val
                st.progress(pct, text=f"{label}: {val}/{max_val}")
            else:
                st.progress(0.0, text=f"{label}: N/A")

    # Signals
    if overall.get("reasons"):
        st.subheader("Signals")
        for reason in overall["reasons"]:
            st.markdown(f"- {reason}")

    # Available data badges
    fins = data.get("financials", {})
    badge_items = []
    if fins.get("cash_conversion_ratio") is not None:
        badge_items.append(f"CCR: {fins['cash_conversion_ratio']:.2f}x")
    if fins.get("roic") is not None:
        badge_items.append(f"ROIC: {fins['roic']:.1f}%")
    if technicals.get("adx") is not None:
        badge_items.append(f"ADX: {technicals['adx']:.0f}")
    if badge_items:
        st.caption(" | ".join(badge_items))


# ===== TAB 2: FAIR VALUE =====
with tab_fair_value:
    fv = data.get("fair_value")
    if fv:
        st.subheader("Fair Value Analysis")

        fv_col1, fv_col2 = st.columns(2)
        with fv_col1:
            st.metric("Current Price", format_price(data["price"]))
            st.metric("Weighted Fair Value", format_price(fv["weighted_fair_value"]))
        with fv_col2:
            prem = fv["premium_discount_pct"]
            label = "Premium" if prem > 0 else "Discount"
            color = "red" if prem > 10 else ("green" if prem < -10 else "orange")
            st.metric(f"{label} to Fair Value", f"{prem:+.1f}%")

        st.divider()
        st.subheader("Valuation Models")
        for model in fv["models"]:
            cols = st.columns([2, 1, 1])
            cols[0].write(f"**{model['model']}**")
            cols[1].write(format_price(model["value"]))
            cols[2].write(f"Weight: {model['weight']}%")
            st.caption(model["details"])

        # Premium/Discount gauge
        import plotly.graph_objects as go
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=prem,
            title={"text": "Premium/Discount %"},
            gauge={
                "axis": {"range": [-50, 50]},
                "bar": {"color": "white"},
                "steps": [
                    {"range": [-50, -10], "color": "#00c853"},
                    {"range": [-10, 10], "color": "#ff9800"},
                    {"range": [10, 50], "color": "#f44336"},
                ],
            },
        ))
        fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", font_color="#c9d1d9")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Fair value data not available — may need more financial data.")


# ===== TAB 3: CHART =====
with tab_chart:
    st.subheader(f"{data['ticker']} Price Chart")

    # Get price data from aggregates
    polygon = PolygonData(api_key)
    today = dt.date.today()
    from_date = (today - dt.timedelta(days=200)).isoformat()
    df_price = polygon.get_aggregates(data["ticker"], from_date, today.isoformat())

    if not df_price.empty:
        # Chart options
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            show_emas = st.multiselect("EMA Overlays", [8, 21, 50, 200], default=[8, 21, 50])
        with chart_col2:
            show_volume = st.checkbox("Show Volume", value=True)

        # Build candlestick chart
        fig = go.Figure()

        fig.add_trace(go.Candlestick(
            x=df_price["date"],
            open=df_price["open"],
            high=df_price["high"],
            low=df_price["low"],
            close=df_price["close"],
            name="Price",
        ))

        # Add EMAs
        ema_colors = {8: "#ff6b6b", 21: "#ffd93d", 50: "#6bcb77", 200: "#4d96ff"}
        for period in show_emas:
            ema = df_price["close"].ewm(span=period, adjust=False).mean()
            fig.add_trace(go.Scatter(
                x=df_price["date"], y=ema,
                name=f"EMA {period}",
                line=dict(width=1.5, color=ema_colors.get(period, "white")),
            ))

        fig.update_layout(
            height=500,
            xaxis_rangeslider_visible=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#c9d1d9",
            xaxis=dict(gridcolor="#1a1d24"),
            yaxis=dict(gridcolor="#1a1d24"),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Volume subplot
        if show_volume:
            colors = ["#00c853" if c >= o else "#f44336"
                      for c, o in zip(df_price["close"], df_price["open"])]
            fig_vol = go.Figure(go.Bar(
                x=df_price["date"], y=df_price["volume"],
                marker_color=colors, name="Volume",
            ))
            fig_vol.update_layout(
                height=200,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#c9d1d9",
                xaxis=dict(gridcolor="#1a1d24"),
                yaxis=dict(gridcolor="#1a1d24"),
                margin=dict(t=10),
            )
            st.plotly_chart(fig_vol, use_container_width=True)
    else:
        st.warning("No price data available.")


# ===== TAB 4: NEWS =====
with tab_news:
    st.subheader("News & Sentiment")
    news = data.get("news", [])
    if news:
        for article in news[:15]:
            sentiment = article.get("sentiment", {})
            label = sentiment.get("label", "Neutral") if isinstance(sentiment, dict) else str(sentiment or "Neutral")
            color_map = {"Positive": "🟢", "Negative": "🔴", "Neutral": "⚪"}
            emoji = color_map.get(label, "⚪")

            category = article.get("category", "General")
            headline = article.get("headline") or article.get("title", "")
            source = article.get("source", "")
            url = article.get("url", "")

            with st.container(border=True):
                cols = st.columns([1, 8])
                cols[0].markdown(f"### {emoji}")
                with cols[1]:
                    if url:
                        st.markdown(f"**[{headline}]({url})**")
                    else:
                        st.markdown(f"**{headline}**")
                    st.caption(f"{source} | {category} | {label}")
    else:
        st.info("No news available. Ensure Finnhub API key is configured.")


# ===== TAB 5: FUNDAMENTALS =====
with tab_fundamentals:
    st.subheader("Fundamental Metrics")
    fins = data.get("financials", {})
    fh = data.get("finnhub_metrics", {})

    if fins or fh:
        # Section 1: Fundamental Analysis
        st.markdown("#### Fundamental Analysis")
        f_cols = st.columns(3)
        f_cols[0].metric("P/E Ratio", format_ratio(fh.get("pe_ratio")))
        f_cols[0].metric("EPS", format_price(fins.get("eps")))
        f_cols[0].metric("EPS Growth", format_pct(fins.get("eps_growth")))

        f_cols[1].metric("Revenue", format_large_number(fins.get("revenue")))
        f_cols[1].metric("Revenue Growth", format_pct(fins.get("revenue_growth")))
        f_cols[1].metric("Gross Margin", format_pct(fins.get("gross_margin")))

        f_cols[2].metric("ROE", format_pct(fins.get("roe")))
        f_cols[2].metric("Debt/Equity", format_ratio(fins.get("debt_to_equity")))
        f_cols[2].metric("Current Ratio", format_ratio(fins.get("current_ratio")))

        st.divider()

        # Section 2: Cash Flow & Profitability
        st.markdown("#### Cash Flow & Profitability")
        cf_cols = st.columns(3)
        cf_cols[0].metric("Operating Margin", format_pct(fins.get("operating_margin")))
        cf_cols[0].metric("FCF", format_large_number(fins.get("free_cash_flow")))
        cf_cols[0].metric("FCF Margin", format_pct(fins.get("fcf_margin")))

        cf_cols[1].metric("Cash Conversion Ratio", format_ratio(fins.get("cash_conversion_ratio")), help="Operating CF / Net Income. Above 1.0 is strong.")
        cf_cols[1].metric("ROIC", format_pct(fins.get("roic")), help="Return on Invested Capital")
        cf_cols[1].metric("ROA", format_pct(fins.get("roa")))

        cf_cols[2].metric("Interest Coverage", format_ratio(fins.get("interest_coverage")), help="Operating Income / Interest Expense")
        cf_cols[2].metric("EBITDA", format_large_number(fins.get("ebitda")))
        cf_cols[2].metric("Dividend Yield", format_pct(fins.get("dividend_yield")))

        st.divider()

        # Section 3: Valuation Metrics
        st.markdown("#### Valuation Metrics")
        derived = data.get("derived_metrics", {})
        v_cols = st.columns(4)
        v_cols[0].metric("FCF Yield", format_pct(derived.get("fcf_yield")), help="FCF per share / Price")
        v_cols[1].metric("PEG Ratio", format_ratio(derived.get("peg_ratio")), help="P/E / EPS Growth Rate")
        v_cols[2].metric("Price/FCF", format_ratio(derived.get("price_to_fcf")))
        v_cols[3].metric("EV/EBITDA", format_ratio(derived.get("ev_ebitda")))

        # Additional Finnhub metrics
        if fh:
            st.divider()
            st.markdown("#### Market Data")
            mk_cols = st.columns(4)
            mk_cols[0].metric("Beta", format_ratio(fh.get("beta")))
            mk_cols[1].metric("52W High", format_price(fh.get("week52_high")))
            mk_cols[2].metric("52W Low", format_price(fh.get("week52_low")))
            mk_cols[3].metric("Market Cap", format_large_number(fh.get("market_cap")))
    else:
        st.info("No fundamental data available.")


# ===== TAB 6: GOV OPPORTUNITIES =====
with tab_gov:
    st.subheader("Government Theme Matching")

    ticker_upper = data["ticker"].upper()
    matched_themes = []
    for key, theme in GOVERNMENT_THEMES.items():
        if ticker_upper in theme["symbols"]:
            matched_themes.append((key, theme))

    if matched_themes:
        for key, theme in matched_themes:
            with st.container(border=True):
                st.markdown(f"### {theme['name']}")
                st.caption(f"Search terms: {', '.join(theme.get('searchTerms', []))}")
                st.caption(f"NAICS codes: {', '.join(theme.get('naicsCodes', []))}")

                # Show peer stocks in this theme
                peers = [s for s in theme["symbols"] if s != ticker_upper]
                if peers:
                    st.markdown(f"**Peer stocks:** {', '.join(peers)}")
    else:
        st.info(f"{data['ticker']} is not currently mapped to any government spending theme. "
                "This stock may still benefit from government spending — check sector exposure.")

    # Show all themes for reference
    with st.expander("All Government Themes"):
        for key, theme in GOVERNMENT_THEMES.items():
            st.markdown(f"**{theme['name']}**: {', '.join(theme['symbols'][:8])}...")


# ===== TAB 7: GROWTH =====
with tab_growth:
    st.subheader("Growth Analysis")

    growth_score = data.get("growth_score")
    if growth_score is not None:
        st.metric("Growth Score", f"{growth_score}/100")
        st.progress(growth_score / 100, text=f"Growth Quality: {growth_score}")

    st.divider()

    # Momentum indicators
    st.markdown("#### Momentum Indicators")
    tech = data.get("technicals", {})
    mom_cols = st.columns(4)
    mom_cols[0].metric("5-Day Momentum", format_pct(tech.get("momentum_5d")))
    mom_cols[1].metric("20-Day Momentum", format_pct(tech.get("momentum_20d")))
    mom_cols[2].metric("RSI (14)", f"{tech.get('rsi', 0):.0f}" if tech.get("rsi") else "N/A")
    mom_cols[3].metric("ADX", f"{tech.get('adx', 0):.0f}" if tech.get("adx") else "N/A")

    st.divider()

    # Volume analysis
    st.markdown("#### Volume Analysis")
    vol_cols = st.columns(3)
    vol_cols[0].metric("Volume Ratio", f"{tech.get('volume_ratio', 1.0):.1f}x")
    vol_cols[1].metric("Bollinger Squeeze", "Yes" if tech.get("bollinger_squeeze") else "No")
    vol_cols[2].metric("MACD Histogram", f"{tech.get('macd_histogram', 0):.3f}" if tech.get("macd_histogram") else "N/A")

    # Institutional flow details
    inst = data.get("institutional_flow", {})
    if inst.get("signals"):
        st.divider()
        st.markdown("#### Institutional Flow Signals")
        for sig in inst["signals"]:
            st.markdown(f"- {sig}")

    # Insider activity
    insider = data.get("insider_activity", {})
    if insider and insider.get("recent_transactions"):
        st.divider()
        st.markdown("#### Recent Insider Activity")
        insider_cols = st.columns(3)
        insider_cols[0].metric("Buy Count (30d)", insider.get("buy_count", 0))
        insider_cols[1].metric("Sell Count (30d)", insider.get("sell_count", 0))
        insider_cols[2].metric("Net Shares", f"{insider.get('net_shares', 0):,}")

        for tx in insider["recent_transactions"][:5]:
            st.caption(f"{tx.get('date', '')} — {tx.get('name', '')} — {tx.get('type', '')} — "
                      f"{tx.get('shares', 0):,} shares @ {format_price(tx.get('price'))}")


# ===== TAB 8: ETF BREAKDOWN =====
with tab_etf:
    st.subheader("ETF & Theme Exposure")

    ticker_upper = data["ticker"].upper()

    # Check which investment themes include this stock
    theme_memberships = []
    for theme_name, symbols in INVESTMENT_THEMES.items():
        if ticker_upper in symbols:
            theme_memberships.append(theme_name)

    if theme_memberships:
        st.markdown("#### Theme Memberships")
        for theme in theme_memberships:
            with st.container(border=True):
                st.markdown(f"**{theme}**")
                theme_stocks = INVESTMENT_THEMES[theme]
                st.caption(f"Stocks: {', '.join(theme_stocks)}")
    else:
        st.info(f"{data['ticker']} is not currently in any tracked investment theme.")

    # Sector ETF mapping
    from config.settings import SECTOR_ETFS
    company = data.get("company_details", {})
    sic_desc = company.get("sic_description", "")
    st.divider()
    st.markdown("#### Sector ETF Mapping")

    if sic_desc:
        st.caption(f"Company sector: {sic_desc}")

    for sector, etf in SECTOR_ETFS.items():
        st.markdown(f"- **{sector}**: {etf}")

    # Options summary
    options = data.get("options_summary", {})
    if options and options.get("total", 0) > 0:
        st.divider()
        st.markdown("#### Options Activity")
        opt_cols = st.columns(4)
        opt_cols[0].metric("Put/Call Ratio", format_ratio(options.get("put_call_ratio")))
        opt_cols[1].metric("Call Contracts", options.get("call_count", 0))
        opt_cols[2].metric("Put Contracts", options.get("put_count", 0))
        opt_cols[3].metric("Total Contracts", options.get("total", 0))
