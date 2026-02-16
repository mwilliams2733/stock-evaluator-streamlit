"""Portfolio Hub — 5-tab portfolio management with analysis, ETF breakdown, and forecasting."""
import datetime as dt
import time

import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import pandas as pd

from config.settings import APP_TITLE, last_market_day, SCANNER_API_DELAY
from config.portfolios import PREDEFINED_PORTFOLIOS
from config.etf_holdings import get_etf_exposure, ETF_HOLDINGS
from config.watchlists import SECTOR_ETF_MAP, SECTOR_NAMES
from data.persistence import (
    load_portfolios, save_portfolios, add_stock_to_portfolio,
    remove_stock_from_portfolio, create_custom_portfolio,
    export_portfolio_json, import_portfolio_json,
)
from data.polygon_client import PolygonData
from core.technicals import calculate_all_technicals
from core.scoring import calculate_institutional_flow, calculate_breakout_score, calculate_overall_score
from core.recommendations import generate_recommendation, calculate_win_probability, get_action_color
from utils.formatting import format_price, format_pct, format_large_number
from utils.export import export_portfolio_csv, export_portfolio_report_text

st.set_page_config(page_title=f"{APP_TITLE} - Portfolio", layout="wide", page_icon="💼")
st.title("Portfolio Hub")
st.caption("Manage portfolios, analyze holdings, and forecast returns.")

# --- Initialize ---
if "polygon_api_key" not in st.session_state:
    from config.settings import POLYGON_API_KEY
    st.session_state["polygon_api_key"] = POLYGON_API_KEY

api_key = st.session_state.get("polygon_api_key", "")
if not api_key:
    st.warning("Please set your Polygon API key in the **Settings** page.")
    st.stop()

# --- Sidebar: Portfolio Management ---
portfolios = load_portfolios()

with st.sidebar:
    st.header("Portfolio Manager")

    portfolio_options = {pid: p["name"] for pid, p in portfolios.items()}
    selected_id = st.selectbox(
        "Select Portfolio",
        options=list(portfolio_options.keys()),
        format_func=lambda x: portfolio_options[x],
        key="portfolio_select",
    )

    selected_portfolio = portfolios.get(selected_id, {})

    st.divider()

    # Add stock
    st.subheader("Add Stock")
    new_ticker = st.text_input("Ticker", key="add_ticker").upper().strip()
    new_shares = st.number_input("Shares", value=0.0, min_value=0.0, step=1.0, key="add_shares")
    new_cost = st.number_input("Cost Basis ($)", value=0.0, min_value=0.0, step=0.01, key="add_cost")
    if st.button("Add to Portfolio", type="primary"):
        if new_ticker:
            add_stock_to_portfolio(selected_id, new_ticker, new_shares, new_cost)
            st.success(f"Added {new_ticker}")
            portfolios = load_portfolios()
            st.rerun()

    st.divider()

    # Create custom portfolio
    st.subheader("Create Portfolio")
    new_name = st.text_input("Portfolio Name", key="new_portfolio_name")
    new_desc = st.text_input("Description", key="new_portfolio_desc")
    if st.button("Create"):
        if new_name:
            pid = new_name.lower().replace(" ", "-")
            create_custom_portfolio(pid, new_name, new_desc)
            st.success(f"Created '{new_name}'")
            st.rerun()

# --- Main Content ---
symbols = selected_portfolio.get("symbols", [])
holdings = selected_portfolio.get("holdings", {})

if not symbols:
    st.info("This portfolio is empty. Add stocks using the sidebar.")
    st.stop()

st.markdown(f"**{selected_portfolio.get('name', '')}** — {selected_portfolio.get('description', '')} ({len(symbols)} stocks)")

# Analyze portfolio stocks
analyze = st.button("Analyze Portfolio", type="primary", use_container_width=True)

if analyze or st.session_state.get("portfolio_data"):
    if analyze:
        polygon = PolygonData(api_key)
        today = dt.date.today()
        market_day = last_market_day()
        from_date = (today - dt.timedelta(days=250)).isoformat()

        progress_bar = st.progress(0)
        status = st.empty()
        results = []

        for idx, ticker in enumerate(symbols):
            progress_bar.progress((idx + 1) / len(symbols))
            status.text(f"Analyzing {ticker}... ({idx + 1}/{len(symbols)})")

            try:
                df = polygon.get_aggregates(ticker, from_date, market_day)
                if df.empty or len(df) < 30:
                    results.append({"ticker": ticker, "price": None, "error": "No data"})
                    continue

                technicals = calculate_all_technicals(df)
                inst_flow = calculate_institutional_flow(df)
                breakout = calculate_breakout_score(df, technicals)
                overall = calculate_overall_score(technicals, inst_flow, breakout)

                stock_data = {
                    "score": overall.get("score", 0),
                    "ema_score": technicals.get("ema_score", 0),
                    "rsi": technicals.get("rsi", 50),
                    "institutional_score": inst_flow.get("score", 50),
                    "breakout_score": breakout.get("score", 0),
                    "momentum_5d": technicals.get("momentum_5d", 0),
                    "momentum_20d": technicals.get("momentum_20d", 0),
                    "bollinger_squeeze": technicals.get("bollinger_squeeze", False),
                }
                rec = generate_recommendation(stock_data)
                win_prob = calculate_win_probability(rec["action"], stock_data)

                price = technicals.get("price", 0)
                h = holdings.get(ticker, {})
                shares = h.get("shares", 0)
                cost_basis = h.get("cost_basis", 0)
                current_value = price * shares if shares else 0
                pnl = (price - cost_basis) * shares if shares and cost_basis else 0
                pnl_pct = ((price / cost_basis) - 1) * 100 if cost_basis > 0 else 0

                results.append({
                    "ticker": ticker,
                    "price": price,
                    "shares": shares,
                    "cost_basis": cost_basis,
                    "current_value": current_value,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "score": overall.get("score", 0),
                    "ema_score": technicals.get("ema_score", 0),
                    "rsi": technicals.get("rsi"),
                    "recommendation": rec["action"],
                    "confidence": rec["confidence"],
                    "win_probability": win_prob["win_probability"],
                    "expected_return": win_prob["expected_return"],
                })

                time.sleep(SCANNER_API_DELAY)
            except Exception:
                results.append({"ticker": ticker, "price": None, "error": "Failed"})

        progress_bar.empty()
        status.empty()
        st.session_state["portfolio_data"] = results

    results = st.session_state.get("portfolio_data", [])
    if not results:
        st.stop()

    valid = [r for r in results if r.get("price")]

    # ===== TABS =====
    tab_overview, tab_holdings, tab_etf, tab_forecast, tab_export = st.tabs(
        ["Overview", "Holdings", "ETF Breakdown", "Forecast", "Export"]
    )

    # --- Tab 1: Overview ---
    with tab_overview:
        total_value = sum(r.get("current_value", 0) for r in valid)
        total_pnl = sum(r.get("pnl", 0) for r in valid)
        total_cost = sum(r.get("cost_basis", 0) * r.get("shares", 0) for r in valid if r.get("cost_basis"))
        total_pnl_pct = ((total_value / total_cost) - 1) * 100 if total_cost > 0 else 0
        avg_score = sum(r.get("score", 0) for r in valid) / len(valid) if valid else 0

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Value", format_price(total_value) if total_value > 0 else "N/A")
        m2.metric("Total P&L", format_price(total_pnl), f"{total_pnl_pct:+.1f}%")
        m3.metric("Holdings", len(symbols))
        m4.metric("Avg Score", f"{avg_score:.0f}")
        m5.metric("With Data", f"{len(valid)}/{len(symbols)}")

        if total_value > 0:
            # Allocation pie chart
            alloc_data = [{"ticker": r["ticker"], "value": r.get("current_value", 0)}
                          for r in valid if r.get("current_value", 0) > 0]
            if alloc_data:
                fig = px.pie(
                    pd.DataFrame(alloc_data), values="value", names="ticker",
                    title="Portfolio Allocation",
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#c9d1d9",
                )
                st.plotly_chart(fig, use_container_width=True)

    # --- Tab 2: Holdings ---
    with tab_holdings:
        if valid:
            display_data = []
            for r in valid:
                display_data.append({
                    "Ticker": r["ticker"],
                    "Price": f"${r['price']:,.2f}" if r.get("price") else "N/A",
                    "Shares": r.get("shares", 0),
                    "P&L": f"${r.get('pnl', 0):,.2f}" if r.get("shares") else "N/A",
                    "P&L%": f"{r.get('pnl_pct', 0):+.1f}%" if r.get("cost_basis") else "N/A",
                    "Score": r.get("score", 0),
                    "EMA": r.get("ema_score", 0),
                    "Action": r.get("recommendation", ""),
                    "Win%": f"{r.get('win_probability', 0) * 100:.0f}%",
                })

            st.dataframe(pd.DataFrame(display_data), use_container_width=True, height=500)

            # Remove stock
            st.subheader("Remove Stock")
            rm_ticker = st.selectbox("Select stock to remove", options=symbols, key="rm_ticker")
            if st.button("Remove", type="secondary"):
                remove_stock_from_portfolio(selected_id, rm_ticker)
                st.success(f"Removed {rm_ticker}")
                st.session_state.pop("portfolio_data", None)
                st.rerun()

    # --- Tab 3: ETF Breakdown ---
    with tab_etf:
        st.subheader("ETF Exposure Analysis")
        etf_exposure = {}
        for r in valid:
            ticker = r["ticker"]
            exposures = get_etf_exposure(ticker)
            for exp in exposures:
                etf = exp["etf"]
                if etf not in etf_exposure:
                    etf_exposure[etf] = {"etf": etf, "name": exp["etf_name"], "stocks": [], "total_weight": 0}
                etf_exposure[etf]["stocks"].append({"ticker": ticker, "weight": exp["weight"]})
                etf_exposure[etf]["total_weight"] += exp["weight"]

        if etf_exposure:
            for etf, data in sorted(etf_exposure.items(), key=lambda x: -x[1]["total_weight"]):
                with st.expander(f"**{etf}** — {data['name']} ({len(data['stocks'])} stocks)"):
                    for s in data["stocks"]:
                        st.write(f"  {s['ticker']}: {s['weight']:.1f}% weight")

            # Sector breakdown
            sector_counts = {}
            for r in valid:
                sector_etf = SECTOR_ETF_MAP.get(r["ticker"], "Unknown")
                sector = SECTOR_NAMES.get(sector_etf, "Other")
                sector_counts[sector] = sector_counts.get(sector, 0) + 1

            if sector_counts:
                fig = px.pie(
                    pd.DataFrame([{"sector": k, "count": v} for k, v in sector_counts.items()]),
                    values="count", names="sector", title="Sector Distribution",
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#c9d1d9",
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No ETF exposure data found for portfolio stocks.")

    # --- Tab 4: Forecast ---
    with tab_forecast:
        st.subheader("Expected Returns Forecast")
        if valid:
            forecast_data = []
            for r in valid:
                forecast_data.append({
                    "ticker": r["ticker"],
                    "action": r.get("recommendation", "HOLD"),
                    "win_probability": r.get("win_probability", 0),
                    "expected_return": r.get("expected_return", 0),
                    "confidence": r.get("confidence", "MEDIUM"),
                })

            for f in sorted(forecast_data, key=lambda x: -x["win_probability"]):
                action_color = get_action_color(f["action"])
                col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
                col1.write(f"**{f['ticker']}**")
                col2.markdown(f"<span style='color:{action_color}'>{f['action']}</span>", unsafe_allow_html=True)
                col3.write(f"Win: {f['win_probability'] * 100:.0f}%")
                col4.write(f"Exp: {f['expected_return'] * 100:+.1f}%")

            # Portfolio-level forecast
            st.divider()
            avg_win = sum(f["win_probability"] for f in forecast_data) / len(forecast_data) if forecast_data else 0
            avg_exp = sum(f["expected_return"] for f in forecast_data) / len(forecast_data) if forecast_data else 0
            st.metric("Portfolio Avg Win Probability", f"{avg_win * 100:.0f}%")
            st.metric("Portfolio Avg Expected Return", f"{avg_exp * 100:+.1f}%")

    # --- Tab 5: Export ---
    with tab_export:
        st.subheader("Export Portfolio")

        # CSV
        csv_data = export_portfolio_csv(results)
        if csv_data:
            st.download_button(
                "Download CSV", data=csv_data,
                file_name=f"portfolio_{selected_id}.csv", mime="text/csv",
            )

        # Text report
        summary = {
            "total_value": total_value,
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
            "num_stocks": len(valid),
            "avg_score": avg_score,
        }
        report = export_portfolio_report_text(selected_portfolio.get("name", ""), results, summary)
        st.download_button(
            "Download Report (TXT)", data=report,
            file_name=f"portfolio_report_{selected_id}.txt", mime="text/plain",
        )

        # JSON export
        st.divider()
        st.subheader("Portfolio JSON")
        json_str = export_portfolio_json(selected_id)
        st.download_button(
            "Export JSON", data=json_str,
            file_name=f"portfolio_{selected_id}.json", mime="application/json",
        )

        # JSON import
        st.divider()
        st.subheader("Import Portfolio")
        uploaded = st.text_area("Paste portfolio JSON here", key="import_json")
        if st.button("Import"):
            if uploaded:
                result = import_portfolio_json(uploaded)
                if result:
                    st.success(f"Imported '{result.get('name', 'portfolio')}'")
                    st.rerun()
                else:
                    st.error("Invalid JSON format. Must contain 'symbols' list.")
