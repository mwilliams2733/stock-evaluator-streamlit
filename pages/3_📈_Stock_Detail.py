"""Stock Detail — Quick single-stock lookup with chart and scores."""
import datetime as dt

import plotly.graph_objects as go
import streamlit as st

from config.settings import APP_TITLE
from core.technicals import calculate_all_technicals
from core.scoring import calculate_institutional_flow, calculate_breakout_score, calculate_overall_score
from data.polygon_client import PolygonData
from utils.formatting import format_price, format_pct, score_color

st.set_page_config(page_title=f"{APP_TITLE} - Stock Detail", layout="wide", page_icon="📈")
st.title("Stock Detail")
st.caption("Quick single-stock lookup with chart, technicals, and score summary.")

# --- Initialize session state ---
if "polygon_api_key" not in st.session_state:
    from config.settings import POLYGON_API_KEY
    st.session_state["polygon_api_key"] = POLYGON_API_KEY

api_key = st.session_state.get("polygon_api_key", "")
if not api_key:
    st.warning("Please set your Polygon API key in the **Settings** page.")
    st.stop()

# --- Ticker Input ---
col1, col2 = st.columns([3, 1])
with col1:
    ticker = st.text_input("Ticker Symbol", value="AAPL", key="detail_ticker").upper().strip()
with col2:
    st.write("")
    analyze = st.button("Analyze", type="primary", use_container_width=True)

if not ticker:
    st.stop()

if analyze or ticker:
    polygon = PolygonData(api_key)

    today = dt.date.today()
    from_date = (today - dt.timedelta(days=200)).isoformat()
    to_date = today.isoformat()

    with st.spinner(f"Loading {ticker}..."):
        df = polygon.get_aggregates(ticker, from_date, to_date)

    if df.empty or len(df) < 30:
        st.error(f"No data available for {ticker}. Check the symbol and try again.")
        st.stop()

    # Calculate everything
    technicals = calculate_all_technicals(df)
    inst_flow = calculate_institutional_flow(df)
    breakout = calculate_breakout_score(df, technicals)
    overall = calculate_overall_score(technicals, inst_flow, breakout)

    price = technicals["price"]

    # --- Metrics Row ---
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Price", format_price(price))
    m2.metric("Score", overall["score"])
    m3.metric("EMA Score", technicals["ema_score"])
    m4.metric("Breakout", breakout["score"])
    m5.metric("Inst. Flow", inst_flow["score"])
    m6.metric("RSI", f"{technicals.get('rsi', 0):.0f}" if technicals.get("rsi") else "N/A")

    st.divider()

    # --- Chart ---
    st.subheader("Price Chart")
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="Price",
    ))

    # Add EMAs
    ema_colors = {8: "#ff6b6b", 21: "#ffd93d", 50: "#6bcb77", 200: "#4d96ff"}
    for period in [8, 21, 50]:
        ema = df["close"].ewm(span=period, adjust=False).mean()
        fig.add_trace(go.Scatter(
            x=df["date"], y=ema,
            name=f"EMA {period}",
            line=dict(width=1.5, color=ema_colors[period]),
        ))

    fig.update_layout(
        height=450,
        xaxis_rangeslider_visible=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#c9d1d9",
        xaxis=dict(gridcolor="#1a1d24"),
        yaxis=dict(gridcolor="#1a1d24"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Volume
    colors = ["#00c853" if c >= o else "#f44336"
              for c, o in zip(df["close"], df["open"])]
    fig_vol = go.Figure(go.Bar(
        x=df["date"], y=df["volume"],
        marker_color=colors, name="Volume",
    ))
    fig_vol.update_layout(
        height=150,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#c9d1d9",
        xaxis=dict(gridcolor="#1a1d24"),
        yaxis=dict(gridcolor="#1a1d24"),
        margin=dict(t=10),
    )
    st.plotly_chart(fig_vol, use_container_width=True)

    st.divider()

    # --- Technical Summary ---
    st.subheader("Technical Indicators")
    t_cols = st.columns(4)
    t_cols[0].metric("MACD Histogram", f"{technicals.get('macd_histogram', 0):.3f}" if technicals.get("macd_histogram") else "N/A")
    t_cols[1].metric("ADX", f"{technicals.get('adx', 0):.0f}" if technicals.get("adx") else "N/A")
    t_cols[2].metric("ATR", f"{technicals.get('atr', 0):.2f}" if technicals.get("atr") else "N/A")
    t_cols[3].metric("Volume Ratio", f"{technicals.get('volume_ratio', 1.0):.1f}x")

    t_cols2 = st.columns(4)
    t_cols2[0].metric("5-Day Momentum", format_pct(technicals.get("momentum_5d")))
    t_cols2[1].metric("20-Day Momentum", format_pct(technicals.get("momentum_20d")))
    t_cols2[2].metric("Bollinger Squeeze", "Yes" if technicals.get("bollinger_squeeze") else "No")
    t_cols2[3].metric("Flow Signal", inst_flow.get("signal", "Neutral"))

    # S/R Levels
    if technicals.get("supports") or technicals.get("resistances"):
        st.divider()
        st.subheader("Support / Resistance")
        sr_cols = st.columns(2)
        with sr_cols[0]:
            st.markdown("**Support Levels**")
            for s in technicals.get("supports", []):
                st.write(f"${s:,.2f}")
        with sr_cols[1]:
            st.markdown("**Resistance Levels**")
            for r in technicals.get("resistances", []):
                st.write(f"${r:,.2f}")

    # Signals
    if overall.get("reasons") or inst_flow.get("signals") or breakout.get("signals"):
        st.divider()
        st.subheader("Active Signals")
        all_signals = overall.get("reasons", []) + inst_flow.get("signals", []) + breakout.get("signals", [])
        for sig in all_signals:
            st.markdown(f"- {sig}")

    # Link to full research
    st.divider()
    if st.button("Open Full Research Panel", type="primary"):
        st.session_state["research_ticker"] = ticker
        st.switch_page("pages/2_📊_Research.py")
