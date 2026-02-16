"""Alerts — Fair value and price alerts with monitoring."""
import datetime as dt
import time

import streamlit as st
import pandas as pd

from config.settings import APP_TITLE, last_market_day, SCANNER_API_DELAY
from data.persistence import load_alerts, add_alert, remove_alert, trigger_alert
from data.polygon_client import PolygonData

st.set_page_config(page_title=f"{APP_TITLE} - Alerts", layout="wide", page_icon="🔔")
st.title("Price Alerts")
st.caption("Set price targets and monitor stocks for entry/exit opportunities.")

# --- Initialize ---
if "polygon_api_key" not in st.session_state:
    from config.settings import POLYGON_API_KEY
    st.session_state["polygon_api_key"] = POLYGON_API_KEY

api_key = st.session_state.get("polygon_api_key", "")
if not api_key:
    st.warning("Please set your Polygon API key in the **Settings** page.")
    st.stop()

# --- Sidebar: Create Alert ---
with st.sidebar:
    st.header("Create Alert")

    alert_ticker = st.text_input("Ticker", key="alert_ticker").upper().strip()
    alert_price = st.number_input("Target Price ($)", value=0.0, min_value=0.0, step=0.01, key="alert_price")
    alert_direction = st.selectbox("Direction", ["below", "above"], key="alert_direction")
    alert_type = st.selectbox("Alert Type", ["price", "fair_value"], key="alert_type",
                              format_func=lambda x: "Price Alert" if x == "price" else "Fair Value Alert")

    if st.button("Create Alert", type="primary"):
        if alert_ticker and alert_price > 0:
            new_alert = add_alert(alert_ticker, alert_price, alert_direction, alert_type)
            st.success(f"Alert created for {alert_ticker} @ ${alert_price:,.2f}")
            st.rerun()
        else:
            st.error("Please enter a valid ticker and target price.")

    st.divider()
    st.caption(
        "**Price Alert**: Triggers when current price crosses the target.\n\n"
        "**Fair Value Alert**: Monitors premium/discount to your estimated fair value."
    )

# --- Load Alerts ---
alerts = load_alerts()
active_alerts = [a for a in alerts if a.get("active", False) and not a.get("triggered", False)]
triggered_alerts = [a for a in alerts if a.get("triggered", False)]

# --- Check Alerts Against Current Prices ---
check_btn = st.button("Check Alerts", type="primary", use_container_width=True)

if check_btn and active_alerts:
    polygon = PolygonData(api_key)
    today = dt.date.today()
    market_day = last_market_day()
    from_date = (today - dt.timedelta(days=10)).isoformat()

    progress = st.progress(0)
    status = st.empty()
    checked_results = []

    for idx, alert in enumerate(active_alerts):
        ticker = alert.get("ticker", "")
        progress.progress((idx + 1) / len(active_alerts))
        status.text(f"Checking {ticker}... ({idx + 1}/{len(active_alerts)})")

        try:
            df = polygon.get_aggregates(ticker, from_date, market_day)
            if not df.empty:
                current_price = float(df.iloc[-1]["close"])
                target = alert.get("target_price", 0)
                direction = alert.get("direction", "below")

                # Check if alert should trigger
                triggered = False
                if direction == "below" and current_price <= target:
                    triggered = True
                elif direction == "above" and current_price >= target:
                    triggered = True

                if triggered:
                    trigger_alert(alert.get("id", ""))

                distance = current_price - target
                distance_pct = (distance / target * 100) if target > 0 else 0

                checked_results.append({
                    "id": alert.get("id", ""),
                    "ticker": ticker,
                    "target_price": target,
                    "direction": direction,
                    "current_price": current_price,
                    "distance": distance,
                    "distance_pct": distance_pct,
                    "triggered": triggered,
                    "alert_type": alert.get("alert_type", "price"),
                })
            time.sleep(SCANNER_API_DELAY)
        except Exception:
            checked_results.append({
                "id": alert.get("id", ""),
                "ticker": ticker,
                "target_price": alert.get("target_price", 0),
                "direction": alert.get("direction", ""),
                "current_price": None,
                "error": "Failed to fetch",
            })

    progress.empty()
    status.empty()
    st.session_state["alert_check_results"] = checked_results

    # Reload alerts after triggering
    alerts = load_alerts()
    active_alerts = [a for a in alerts if a.get("active", False) and not a.get("triggered", False)]
    triggered_alerts = [a for a in alerts if a.get("triggered", False)]

# --- Active Alerts ---
st.subheader(f"Active Alerts ({len(active_alerts)})")

if active_alerts:
    check_results = st.session_state.get("alert_check_results", [])
    result_map = {r.get("id"): r for r in check_results}

    alert_display = []
    for alert in active_alerts:
        aid = alert.get("id", "")
        result = result_map.get(aid, {})
        current = result.get("current_price")

        row = {
            "Ticker": alert.get("ticker", ""),
            "Target": f"${alert.get('target_price', 0):,.2f}",
            "Direction": alert.get("direction", "").title(),
            "Type": "Fair Value" if alert.get("alert_type") == "fair_value" else "Price",
            "Current": f"${current:,.2f}" if current else "—",
            "Distance": f"${result.get('distance', 0):,.2f}" if current else "—",
            "Distance%": f"{result.get('distance_pct', 0):+.1f}%" if current else "—",
            "Created": alert.get("created", "")[:10],
        }
        alert_display.append(row)

    st.dataframe(pd.DataFrame(alert_display), use_container_width=True, hide_index=True)

    # Remove alert
    st.subheader("Remove Alert")
    alert_options = {a.get("id", ""): f"{a.get('ticker', '')} — ${a.get('target_price', 0):,.2f} ({a.get('direction', '')})"
                     for a in active_alerts}
    rm_id = st.selectbox("Select alert to remove", options=list(alert_options.keys()),
                         format_func=lambda x: alert_options.get(x, x), key="rm_alert")
    if st.button("Remove Alert", type="secondary"):
        remove_alert(rm_id)
        st.success("Alert removed!")
        st.session_state.pop("alert_check_results", None)
        st.rerun()

    # Recently triggered
    recently_triggered = [r for r in check_results if r.get("triggered")]
    if recently_triggered:
        st.divider()
        st.subheader("Just Triggered!")
        for r in recently_triggered:
            st.success(
                f"**{r['ticker']}** hit target ${r['target_price']:,.2f} "
                f"(current: ${r['current_price']:,.2f})"
            )
else:
    st.info("No active alerts. Create one using the sidebar.")

# --- Triggered History ---
st.divider()
st.subheader(f"Triggered Alert History ({len(triggered_alerts)})")

if triggered_alerts:
    history_data = []
    for alert in triggered_alerts:
        history_data.append({
            "Ticker": alert.get("ticker", ""),
            "Target": f"${alert.get('target_price', 0):,.2f}",
            "Direction": alert.get("direction", "").title(),
            "Type": "Fair Value" if alert.get("alert_type") == "fair_value" else "Price",
            "Created": alert.get("created", "")[:10],
            "Triggered": alert.get("triggered_at", "")[:10] if alert.get("triggered_at") else "—",
        })

    st.dataframe(pd.DataFrame(history_data), use_container_width=True, hide_index=True)

    if st.button("Clear Triggered History"):
        # Remove all triggered alerts
        current_alerts = load_alerts()
        active_only = [a for a in current_alerts if not a.get("triggered", False)]
        from data.persistence import save_alerts
        save_alerts(active_only)
        st.success("Triggered alerts cleared!")
        st.rerun()
else:
    st.caption("No triggered alerts yet.")

# --- Quick Monitor ---
st.divider()
st.subheader("Quick Price Monitor")
st.caption("Enter tickers to quickly check current prices without creating alerts.")

monitor_tickers = st.text_input(
    "Tickers (comma-separated)",
    placeholder="AAPL, NVDA, TSLA",
    key="monitor_tickers",
)

if st.button("Check Prices") and monitor_tickers:
    tickers = [t.strip().upper() for t in monitor_tickers.split(",") if t.strip()]
    polygon = PolygonData(api_key)
    today = dt.date.today()
    market_day = last_market_day()
    from_date = (today - dt.timedelta(days=10)).isoformat()

    monitor_results = []
    for ticker in tickers:
        try:
            df = polygon.get_aggregates(ticker, from_date, market_day)
            if not df.empty:
                close = float(df.iloc[-1]["close"])
                prev_close = float(df.iloc[-2]["close"]) if len(df) >= 2 else close
                change = close - prev_close
                change_pct = (change / prev_close * 100) if prev_close > 0 else 0
                monitor_results.append({
                    "Ticker": ticker,
                    "Price": f"${close:,.2f}",
                    "Change": f"${change:+,.2f}",
                    "Change%": f"{change_pct:+.2f}%",
                })
            time.sleep(SCANNER_API_DELAY)
        except Exception:
            monitor_results.append({"Ticker": ticker, "Price": "Error", "Change": "—", "Change%": "—"})

    if monitor_results:
        st.dataframe(pd.DataFrame(monitor_results), use_container_width=True, hide_index=True)
