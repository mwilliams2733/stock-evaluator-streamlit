"""Backtest — Historical strategy validation with factor analysis."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from config.settings import APP_TITLE
from config.signals import BACKTEST_CONFIG, SIGNAL_WIN_RATES
from core.backtesting import run_backtest
from data.polygon_client import PolygonData
from utils.export import export_backtest_report_text

st.set_page_config(page_title=f"{APP_TITLE} - Backtest", layout="wide", page_icon="🔬")
st.title("Strategy Backtester")
st.caption("Validate the scoring strategy against historical data across 110 stocks.")

# --- Initialize ---
if "polygon_api_key" not in st.session_state:
    from config.settings import POLYGON_API_KEY
    st.session_state["polygon_api_key"] = POLYGON_API_KEY

api_key = st.session_state.get("polygon_api_key", "")
if not api_key:
    st.warning("Please set your Polygon API key in the **Settings** page.")
    st.stop()

# --- Sidebar: Backtest Config ---
with st.sidebar:
    st.header("Backtest Configuration")

    holding_period = st.slider(
        "Holding Period (days)", 10, 120,
        value=BACKTEST_CONFIG["holding_period_days"], step=5,
    )
    target_pct = st.slider(
        "Target Return (%)", 3, 30,
        value=BACKTEST_CONFIG["target_percent"], step=1,
    )
    stop_pct = st.slider(
        "Stop Loss (%)", 3, 30,
        value=BACKTEST_CONFIG["stop_percent"], step=1,
    )
    min_score = st.slider(
        "Min Overall Score", 0, 50,
        value=BACKTEST_CONFIG["min_overall_score"], step=5,
    )

    st.divider()
    st.caption(
        f"Universe: 110 stocks across 10 sectors\n\n"
        f"Target: +{target_pct}% | Stop: -{stop_pct}% | Hold: {holding_period}d"
    )

# --- Run Backtest ---
run_btn = st.button("Run Backtest", type="primary", use_container_width=True)

if run_btn:
    config = {
        "holding_period_days": holding_period,
        "target_percent": target_pct,
        "stop_percent": stop_pct,
        "min_overall_score": min_score,
    }

    progress_bar = st.progress(0)
    status = st.empty()

    def update_progress(current, total, message):
        if total > 0:
            progress_bar.progress(current / total)
        status.text(message)

    try:
        polygon = PolygonData(api_key)
        results = run_backtest(polygon, config=config, progress_callback=update_progress)
        progress_bar.empty()
        status.empty()
        st.session_state["backtest_results"] = results
    except Exception as e:
        progress_bar.empty()
        status.empty()
        st.error(f"Backtest failed: {e}")
        st.stop()

# --- Display Results ---
results = st.session_state.get("backtest_results")
if not results:
    st.info(
        "Configure parameters in the sidebar and click **Run Backtest** to validate "
        "the scoring strategy against historical data. This will analyze 110 stocks "
        "across 10 sectors using your configured thresholds."
    )

    # Show expected win rates
    with st.expander("Expected Win Rates by Signal"):
        for action, rates in SIGNAL_WIN_RATES.items():
            cols = st.columns([3, 2, 2, 2])
            cols[0].write(f"**{action}**")
            cols[1].write(f"Win: {rates['win_rate'] * 100:.0f}%")
            cols[2].write(f"Avg Ret: {rates['avg_return'] * 100:+.0f}%")
            cols[3].write(f"Hold: {rates['hold_period']}d")
    st.stop()

summary = results.get("summary", {})
trades = results.get("trades", [])
factor_analysis = results.get("factor_analysis", {})
action_breakdown = results.get("action_breakdown", {})

if not trades:
    st.warning("No trades found matching the backtest criteria. Try lowering the minimum score threshold.")
    st.stop()

# --- Summary Metrics ---
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Total Trades", summary.get("total_trades", 0))
m2.metric("Win Rate", f"{summary.get('win_rate', 0):.1f}%")
m3.metric("Avg Return", f"{summary.get('avg_return', 0):+.1f}%")
m4.metric("Profit Factor", f"{summary.get('profit_factor', 0):.2f}")
m5.metric("Best Trade", f"{summary.get('best_trade', 0):+.1f}%")
m6.metric("Worst Trade", f"{summary.get('worst_trade', 0):+.1f}%")

st.divider()

# ===== TABS =====
tab_breakdown, tab_factors, tab_trades, tab_export = st.tabs(
    ["Signal Breakdown", "Factor Analysis", "Trade Log", "Export"]
)

# --- Tab 1: Signal Breakdown ---
with tab_breakdown:
    st.subheader("Win Rate by Recommendation Level")

    if action_breakdown:
        breakdown_data = []
        for action, data in sorted(
            action_breakdown.items(),
            key=lambda x: -x[1].get("win_rate", 0),
        ):
            expected = SIGNAL_WIN_RATES.get(action, {})
            breakdown_data.append({
                "Action": action,
                "Trades": data.get("total", 0),
                "Wins": data.get("wins", 0),
                "Win Rate": f"{data.get('win_rate', 0):.1f}%",
                "Avg Return": f"{data.get('avg_return', 0):+.1f}%",
                "Expected Win": f"{expected.get('win_rate', 0) * 100:.0f}%",
                "vs Expected": f"{data.get('win_rate', 0) - expected.get('win_rate', 0) * 100:+.1f}%",
            })

        st.dataframe(pd.DataFrame(breakdown_data), use_container_width=True, hide_index=True)

        # Bar chart: actual vs expected win rates
        chart_data = []
        for action, data in action_breakdown.items():
            expected = SIGNAL_WIN_RATES.get(action, {})
            chart_data.append({"Action": action, "Type": "Actual", "Win Rate": data.get("win_rate", 0)})
            chart_data.append({"Action": action, "Type": "Expected", "Win Rate": expected.get("win_rate", 0) * 100})

        fig = px.bar(
            pd.DataFrame(chart_data),
            x="Action", y="Win Rate", color="Type",
            barmode="group", title="Actual vs Expected Win Rates",
            color_discrete_map={"Actual": "#6bcb77", "Expected": "#4d96ff"},
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#c9d1d9",
            xaxis=dict(gridcolor="#1a1d24"),
            yaxis=dict(gridcolor="#1a1d24", title="Win Rate %"),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Outcome distribution pie
    outcomes = {
        "WIN": summary.get("wins", 0),
        "LOSS": summary.get("losses", 0),
        "TIMEOUT": summary.get("timeouts", 0),
    }
    fig_pie = px.pie(
        pd.DataFrame([{"outcome": k, "count": v} for k, v in outcomes.items() if v > 0]),
        values="count", names="outcome", title="Trade Outcomes",
        color_discrete_map={"WIN": "#00c853", "LOSS": "#f44336", "TIMEOUT": "#ff9800"},
    )
    fig_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#c9d1d9",
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# --- Tab 2: Factor Analysis ---
with tab_factors:
    st.subheader("Factor Correlation with Outcomes")

    if factor_analysis:
        factor_data = []
        for factor, data in factor_analysis.items():
            factor_data.append({
                "Factor": factor.replace("_", " ").title(),
                "Avg in Wins": f"{data.get('avg_in_wins', 0):.1f}",
                "Avg in Losses": f"{data.get('avg_in_losses', 0):.1f}",
                "Differential": f"{data.get('differential', 0):+.1f}",
            })

        st.dataframe(pd.DataFrame(factor_data), use_container_width=True, hide_index=True)

        # Differential bar chart
        diff_data = []
        for factor, data in factor_analysis.items():
            diff_data.append({
                "Factor": factor.replace("_", " ").title(),
                "Differential": data.get("differential", 0),
            })

        fig = px.bar(
            pd.DataFrame(diff_data),
            x="Factor", y="Differential",
            title="Factor Differential (Wins - Losses)",
            color="Differential",
            color_continuous_scale=["#f44336", "#ff9800", "#00c853"],
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#c9d1d9",
            xaxis=dict(gridcolor="#1a1d24"),
            yaxis=dict(gridcolor="#1a1d24"),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Insights
        st.subheader("Key Insights")
        for factor, data in factor_analysis.items():
            diff = data.get("differential", 0)
            if abs(diff) >= 5:
                direction = "higher" if diff > 0 else "lower"
                factor_name = factor.replace("_", " ").title()
                st.markdown(
                    f"- **{factor_name}**: Winning trades have a {abs(diff):.1f}pt "
                    f"{direction} average than losing trades"
                )
    else:
        st.info("No factor analysis data available.")

# --- Tab 3: Trade Log ---
with tab_trades:
    st.subheader(f"Trade Log ({len(trades)} trades)")

    # Filters
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        outcome_filter = st.multiselect(
            "Filter by Outcome",
            ["WIN", "LOSS", "TIMEOUT"],
            default=["WIN", "LOSS", "TIMEOUT"],
        )
    with filter_col2:
        action_filter = st.multiselect(
            "Filter by Action",
            list(set(t.get("action", "") for t in trades)),
            default=list(set(t.get("action", "") for t in trades)),
        )

    filtered = [
        t for t in trades
        if t.get("outcome") in outcome_filter and t.get("action") in action_filter
    ]

    if filtered:
        display_trades = []
        for t in filtered:
            display_trades.append({
                "Ticker": t.get("ticker", ""),
                "Date": t.get("entry_date", ""),
                "Entry": f"${t.get('entry_price', 0):,.2f}",
                "Exit": f"${t.get('exit_price', 0):,.2f}",
                "Return": f"{t.get('return_pct', 0):+.1f}%",
                "Outcome": t.get("outcome", ""),
                "Days": t.get("days_held", 0),
                "Action": t.get("action", ""),
                "Score": t.get("overall_score", 0),
                "EMA": t.get("ema_score", 0),
                "Max Fav": f"{t.get('max_favorable', 0):+.1f}%",
                "Max Adv": f"-{t.get('max_adverse', 0):.1f}%",
            })

        st.dataframe(
            pd.DataFrame(display_trades),
            use_container_width=True,
            height=600,
            hide_index=True,
        )
    else:
        st.info("No trades match the selected filters.")

# --- Tab 4: Export ---
with tab_export:
    st.subheader("Export Backtest Results")

    # CSV
    if trades:
        trade_df = pd.DataFrame(trades)
        csv_data = trade_df.to_csv(index=False)
        st.download_button(
            "Download Trade Log (CSV)",
            data=csv_data,
            file_name="backtest_trades.csv",
            mime="text/csv",
        )

    # Text report
    report = export_backtest_report_text(summary, factor_analysis, action_breakdown)
    st.download_button(
        "Download Report (TXT)",
        data=report,
        file_name="backtest_report.txt",
        mime="text/plain",
    )

    # Config summary
    st.divider()
    st.subheader("Backtest Configuration Used")
    st.json({
        "holding_period_days": holding_period,
        "target_percent": target_pct,
        "stop_percent": stop_pct,
        "min_overall_score": min_score,
        "universe_size": 110,
    })
