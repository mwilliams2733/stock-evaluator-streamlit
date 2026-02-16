"""Scanner — Full market scan with technical scoring, institutional flow, and pre-breakout detection."""
import streamlit as st
import pandas as pd

from config.settings import APP_TITLE, MIN_PRICE, MIN_VOLUME, MIN_SCORE, MIN_EMA_SCORE
from config.themes import INVESTMENT_THEMES
from config.watchlists import SECTOR_WATCHLISTS, FILTER_PRESETS
from core.scanner import run_full_scan
from core.recommendations import generate_recommendation, get_action_color
from data.polygon_client import PolygonData
from utils.formatting import format_price, format_pct, format_large_number, format_score, score_color

st.set_page_config(page_title=f"{APP_TITLE} - Scanner", layout="wide", page_icon="🔍")
st.title("Market Scanner")
st.caption("Discover high-scoring momentum stocks with pre-breakout patterns and institutional accumulation.")

# --- Initialize session state ---
if "polygon_api_key" not in st.session_state:
    from config.settings import POLYGON_API_KEY
    st.session_state["polygon_api_key"] = POLYGON_API_KEY

api_key = st.session_state.get("polygon_api_key", "")
if not api_key:
    st.warning("Please set your Polygon API key in the **Settings** page.")
    st.stop()

# --- Sidebar filters ---
with st.sidebar:
    st.header("Scanner Filters")

    # Filter Presets
    st.subheader("Quick Presets")
    preset_names = {"none": "Custom"} | {k: v["name"] for k, v in FILTER_PRESETS.items()}
    selected_preset = st.selectbox(
        "Filter Preset",
        options=list(preset_names.keys()),
        format_func=lambda x: preset_names[x],
        key="scanner_preset",
    )

    # Apply preset values or use defaults
    if selected_preset != "none":
        preset = FILTER_PRESETS[selected_preset]
        preset_min_price = preset.get("min_price", MIN_PRICE)
        preset_min_vol = preset.get("min_volume", MIN_VOLUME)
        preset_min_score = preset.get("min_score", MIN_SCORE)
        preset_min_ema = preset.get("min_ema_score", MIN_EMA_SCORE)
        st.caption(f"_{preset.get('description', '')}_")
    else:
        preset_min_price = st.session_state.get("default_min_price", MIN_PRICE)
        preset_min_vol = int(st.session_state.get("default_min_volume", MIN_VOLUME))
        preset_min_score = int(st.session_state.get("default_min_score", MIN_SCORE))
        preset_min_ema = int(st.session_state.get("default_min_ema", MIN_EMA_SCORE))

    st.divider()

    lookback = st.slider("Lookback (days)", 100, 400, 200, step=25)
    min_price = st.number_input(
        "Min Price ($)",
        value=float(preset_min_price),
        min_value=0.5, step=0.5,
    )
    min_vol = st.number_input(
        "Min Avg Volume",
        value=int(preset_min_vol),
        min_value=10_000, step=50_000,
    )
    min_score = st.number_input(
        "Min Overall Score",
        value=int(preset_min_score),
        min_value=0, max_value=100, step=5,
    )
    min_ema = st.number_input(
        "Min EMA Score",
        value=int(preset_min_ema),
        min_value=0, max_value=100, step=5,
    )

    st.divider()
    st.subheader("Theme / Watchlist")

    # Combined themes + sector watchlists
    theme_options = {"all": "All Stocks"}
    for k, v in INVESTMENT_THEMES.items():
        theme_options[f"theme_{k}"] = f"Theme: {k}"
    for k, v in SECTOR_WATCHLISTS.items():
        theme_options[f"watch_{k}"] = f"Watchlist: {v['name']}"

    theme_choice = st.selectbox(
        "Stock Universe",
        options=list(theme_options.keys()),
        format_func=lambda x: theme_options[x],
    )

# --- Run Scanner ---
if st.button("Run Scanner", type="primary", use_container_width=True):
    st.session_state["scanner_ran"] = True

if st.session_state.get("scanner_ran"):
    # Build filters
    filters = {
        "lookback_days": lookback,
        "min_price": min_price,
        "min_volume": min_vol,
        "min_score": min_score,
        "min_ema_score": min_ema,
    }

    if theme_choice.startswith("theme_"):
        theme_key = theme_choice[6:]
        filters["theme_symbols"] = INVESTMENT_THEMES[theme_key]
    elif theme_choice.startswith("watch_"):
        watch_key = theme_choice[6:]
        filters["theme_symbols"] = SECTOR_WATCHLISTS[watch_key]["symbols"]

    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()

    def update_progress(current, total, message):
        if total > 0:
            progress_bar.progress(current / total)
        status_text.text(message)

    try:
        polygon = PolygonData(api_key)
        df = run_full_scan(polygon, filters, progress_callback=update_progress)
        progress_bar.empty()
        status_text.empty()

        # Add recommendation column to scan results
        if not df.empty:
            recs = []
            for _, row in df.iterrows():
                stock_data = {
                    "score": row.get("score", 0),
                    "ema_score": row.get("ema_score", 0),
                    "rsi": row.get("rsi", 50),
                    "institutional_score": row.get("institutional_score", 50),
                    "breakout_score": row.get("breakout_score", 0),
                    "momentum_5d": row.get("momentum_5d", 0),
                    "momentum_20d": row.get("momentum_20d", 0),
                    "bollinger_squeeze": row.get("bollinger_squeeze", False),
                }
                rec = generate_recommendation(stock_data)
                recs.append(rec["action"])
            df["recommendation"] = recs

        st.session_state["scan_results"] = df
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Scanner failed: {e}")
        st.stop()

# --- Display Results ---
df = st.session_state.get("scan_results")
if df is not None and not df.empty:
    st.success(f"Found {len(df)} stocks passing filters")

    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Stocks", len(df))
    col2.metric("Avg Score", f"{df['score'].mean():.0f}")
    col3.metric("Best Score", f"{df['score'].max():.0f}")
    col4.metric("Avg EMA Score", f"{df['ema_score'].mean():.0f}")

    # Count buy recommendations
    if "recommendation" in df.columns:
        buy_signals = df["recommendation"].isin(["STRONG BUY", "ACCUMULATE", "BUY DIP"]).sum()
        col5.metric("Buy Signals", int(buy_signals))

    # Sort options
    sort_col1, sort_col2 = st.columns(2)
    with sort_col1:
        sort_by = st.selectbox(
            "Sort by",
            ["score", "ema_score", "breakout_score", "institutional_score",
             "rsi", "momentum_5d", "momentum_20d", "volume_ratio"],
            key="scanner_sort",
        )
    with sort_col2:
        sort_dir = st.selectbox("Direction", ["Descending", "Ascending"], key="scanner_sort_dir")

    sorted_df = df.sort_values(sort_by, ascending=(sort_dir == "Ascending")).reset_index(drop=True)

    # Results table
    st.subheader("Scan Results")

    # Build display columns
    display_cols = ["ticker", "name", "price", "score", "ema_score",
                    "breakout_score", "institutional_score", "rsi",
                    "momentum_5d", "momentum_20d", "volume_ratio",
                    "flow_signal", "breakout_pattern"]
    if "recommendation" in sorted_df.columns:
        display_cols.insert(3, "recommendation")

    display_df = sorted_df[[c for c in display_cols if c in sorted_df.columns]].copy()

    display_df["price"] = display_df["price"].apply(lambda x: f"${x:,.2f}" if x else "N/A")
    display_df["momentum_5d"] = display_df["momentum_5d"].apply(lambda x: f"{x:+.1f}%" if x else "N/A")
    display_df["momentum_20d"] = display_df["momentum_20d"].apply(lambda x: f"{x:+.1f}%" if x else "N/A")
    display_df["rsi"] = display_df["rsi"].apply(lambda x: f"{x:.0f}" if x else "N/A")
    display_df["volume_ratio"] = display_df["volume_ratio"].apply(lambda x: f"{x:.1f}x")

    col_config = {
        "ticker": st.column_config.TextColumn("Ticker", width="small"),
        "name": st.column_config.TextColumn("Name", width="medium"),
        "price": st.column_config.TextColumn("Price", width="small"),
        "score": st.column_config.NumberColumn("Score", format="%d", width="small"),
        "ema_score": st.column_config.NumberColumn("EMA", format="%d", width="small"),
        "breakout_score": st.column_config.NumberColumn("Breakout", format="%d", width="small"),
        "institutional_score": st.column_config.NumberColumn("Inst. Flow", format="%d", width="small"),
        "rsi": st.column_config.TextColumn("RSI", width="small"),
        "momentum_5d": st.column_config.TextColumn("5D Mom", width="small"),
        "momentum_20d": st.column_config.TextColumn("20D Mom", width="small"),
        "volume_ratio": st.column_config.TextColumn("Vol Ratio", width="small"),
        "flow_signal": st.column_config.TextColumn("Flow Signal", width="small"),
        "breakout_pattern": st.column_config.TextColumn("Pattern", width="medium"),
    }
    if "recommendation" in display_df.columns:
        col_config["recommendation"] = st.column_config.TextColumn("Action", width="small")

    st.dataframe(
        display_df,
        use_container_width=True,
        height=600,
        column_config=col_config,
    )

    # Quick research link
    st.subheader("Research a Stock")
    research_col1, research_col2 = st.columns([3, 1])
    with research_col1:
        selected_ticker = st.selectbox(
            "Select from scan results",
            options=sorted_df["ticker"].tolist(),
            key="scanner_select_ticker",
        )
    with research_col2:
        if st.button("Open Research", type="primary"):
            st.session_state["research_ticker"] = selected_ticker
            st.switch_page("pages/2_📊_Research.py")

    # Export
    st.subheader("Export")
    csv_data = sorted_df.to_csv(index=False)
    st.download_button(
        "Download CSV",
        data=csv_data,
        file_name="scan_results.csv",
        mime="text/csv",
    )

elif df is not None and df.empty:
    st.warning("No stocks found matching your filters. Try relaxing the criteria.")
