"""Full market scan orchestration — fetches data, scores, and filters stocks."""
import datetime as dt
import time

import pandas as pd
import streamlit as st

from config import settings
from core.technicals import calculate_all_technicals
from core.scoring import (
    calculate_institutional_flow,
    calculate_breakout_score,
    calculate_overall_score,
    passes_scan_filters,
)
from core.fundamentals import calculate_lightweight_moat


def run_full_scan(
    polygon,
    filters: dict,
    progress_callback=None,
) -> pd.DataFrame:
    """Run a full market scan: fetch tickers, compute technicals, score, filter.

    Args:
        polygon: PolygonData instance.
        filters: Dict with min_price, min_volume, min_score, min_ema_score,
                 lookback_days, theme_symbols (optional list).
        progress_callback: Callable(current, total, message) for UI updates.

    Returns:
        DataFrame of passing stocks sorted by score descending.
    """
    lookback = filters.get("lookback_days", settings.SCANNER_LOOKBACK_DAYS)
    theme_symbols = filters.get("theme_symbols")

    # 1. Get ticker universe
    if theme_symbols:
        # Scan only specific theme stocks
        all_tickers = theme_symbols
    else:
        # Get all active tickers and filter to common stocks
        ticker_df = polygon.get_all_active_tickers()
        if ticker_df.empty:
            return pd.DataFrame()
        # Filter to CS (common stock) type and exclude OTC-like tickers
        mask = ticker_df["type"].isin(["CS", ""])
        mask &= ~ticker_df["ticker"].str.contains(r"\.", na=False)  # Exclude warrants etc
        mask &= ticker_df["ticker"].str.len() <= 5
        all_tickers = ticker_df.loc[mask, "ticker"].tolist()

    total = len(all_tickers)
    if progress_callback:
        progress_callback(0, total, f"Scanning {total} tickers...")

    # 2. Get recent grouped daily for quick volume/price filter
    today = dt.date.today()
    # Find most recent trading day
    for days_back in range(0, 5):
        check_date = (today - dt.timedelta(days=days_back)).isoformat()
        grouped = polygon.get_grouped_daily(check_date)
        if not grouped.empty:
            break
    else:
        grouped = pd.DataFrame()

    # Pre-filter by price and volume from grouped daily
    if not grouped.empty:
        min_price = filters.get("min_price", settings.MIN_PRICE)
        min_volume = filters.get("min_volume", settings.MIN_VOLUME)
        grouped_filtered = grouped[
            (grouped["close"] >= min_price) &
            (grouped["volume"] >= min_volume) &
            (grouped["ticker"].isin(all_tickers))
        ]
        candidate_tickers = grouped_filtered["ticker"].tolist()
    else:
        candidate_tickers = all_tickers[:500]  # Fallback limit

    total_candidates = len(candidate_tickers)
    if progress_callback:
        progress_callback(0, total_candidates, f"Analyzing {total_candidates} candidates...")

    # 3. Analyze each candidate
    results = []
    to_date = today.isoformat()
    from_date = (today - dt.timedelta(days=lookback + 50)).isoformat()

    for idx, ticker in enumerate(candidate_tickers):
        if progress_callback and idx % 10 == 0:
            progress_callback(idx, total_candidates, f"Analyzing {ticker}... ({len(results)} found)")

        try:
            # Fetch price data
            df = polygon.get_aggregates(ticker, from_date, to_date)
            if df.empty or len(df) < 30:
                continue

            # Calculate technicals
            technicals = calculate_all_technicals(df)
            if not technicals:
                continue

            price = technicals["price"]
            avg_volume = float(df["volume"].tail(20).mean())

            # Quick filter check
            if price < filters.get("min_price", settings.MIN_PRICE):
                continue
            if avg_volume < filters.get("min_volume", settings.MIN_VOLUME):
                continue

            # Calculate scores
            inst_flow = calculate_institutional_flow(df)
            breakout = calculate_breakout_score(df, technicals)
            overall = calculate_overall_score(technicals, inst_flow, breakout)

            stock_data = {
                "ticker": ticker,
                "price": price,
                "volume": avg_volume,
                "score": overall["score"],
                "ema_score": technicals["ema_score"],
                "breakout_score": breakout["score"],
                "institutional_score": inst_flow["score"],
                "rsi": technicals.get("rsi"),
                "adx": technicals.get("adx"),
                "momentum_5d": technicals.get("momentum_5d", 0),
                "momentum_20d": technicals.get("momentum_20d", 0),
                "volume_ratio": technicals.get("volume_ratio", 1.0),
                "bollinger_squeeze": technicals.get("bollinger_squeeze", False),
                "breakout_pattern": breakout.get("pattern", ""),
                "flow_signal": inst_flow.get("signal", "Neutral"),
                "reasons": overall.get("reasons", []),
            }

            # Apply filter
            if passes_scan_filters(stock_data, filters):
                # Try to get company details for name/market cap
                try:
                    details = polygon.get_ticker_details(ticker)
                    stock_data["name"] = details.get("name", ticker)
                    stock_data["market_cap"] = details.get("market_cap")
                    stock_data["sector"] = details.get("sic_description", "")

                    moat = calculate_lightweight_moat(details)
                    stock_data["moat_score"] = moat.get("moat_score")
                    stock_data["moat_rating"] = moat.get("moat_rating")
                except Exception:
                    stock_data["name"] = ticker
                    stock_data["market_cap"] = None
                    stock_data["sector"] = ""
                    stock_data["moat_score"] = None
                    stock_data["moat_rating"] = None

                results.append(stock_data)

            # Rate limiting
            time.sleep(settings.SCANNER_API_DELAY)

        except Exception:
            continue

    if progress_callback:
        progress_callback(total_candidates, total_candidates, f"Scan complete! {len(results)} stocks found.")

    if not results:
        return pd.DataFrame()

    result_df = pd.DataFrame(results)
    result_df = result_df.sort_values("score", ascending=False).reset_index(drop=True)
    return result_df


def analyze_single_stock(ticker: str, polygon, finnhub=None) -> dict:
    """Full analysis for a single stock (used by Research page).

    Args:
        ticker: Stock symbol.
        polygon: PolygonData instance.
        finnhub: FinnhubData instance (optional).

    Returns:
        Dict with all analysis data.
    """
    from core.fundamentals import (
        process_financials,
        calculate_moat_score,
        calculate_fair_value,
        calculate_growth_score,
        calculate_derived_metrics,
    )

    today = dt.date.today()
    from_date = (today - dt.timedelta(days=250)).isoformat()
    to_date = today.isoformat()

    result = {
        "ticker": ticker,
        "price": None,
        "technicals": {},
        "institutional_flow": {},
        "breakout": {},
        "overall_score": {},
        "financials": {},
        "moat": {},
        "fair_value": None,
        "growth_score": None,
        "derived_metrics": {},
        "company_details": {},
        "news": [],
        "finnhub_metrics": {},
        "options_summary": {},
        "earnings": [],
        "insider_activity": {},
    }

    # Price data + technicals
    try:
        df = polygon.get_aggregates(ticker, from_date, to_date)
        if not df.empty and len(df) >= 30:
            technicals = calculate_all_technicals(df)
            result["technicals"] = technicals
            result["price"] = technicals.get("price")

            inst_flow = calculate_institutional_flow(df)
            result["institutional_flow"] = inst_flow

            breakout = calculate_breakout_score(df, technicals)
            result["breakout"] = breakout

            overall = calculate_overall_score(technicals, inst_flow, breakout)
            result["overall_score"] = overall
    except Exception:
        pass

    # Company details
    try:
        details = polygon.get_ticker_details(ticker)
        result["company_details"] = details
    except Exception:
        pass

    # Financials
    try:
        raw_fins = polygon.get_financials(ticker)
        finnhub_metrics = {}
        if finnhub:
            finnhub_metrics = finnhub.get_basic_metrics(ticker)
        result["finnhub_metrics"] = finnhub_metrics

        processed = process_financials(raw_fins, finnhub_metrics)
        result["financials"] = processed

        moat = calculate_moat_score(processed, result["company_details"])
        result["moat"] = moat

        if result["price"]:
            fv = calculate_fair_value(processed, result["price"], result["company_details"])
            result["fair_value"] = fv

        growth = calculate_growth_score(processed)
        result["growth_score"] = growth

        if result["price"]:
            derived = calculate_derived_metrics(
                processed, result["price"],
                result["company_details"].get("market_cap"),
            )
            result["derived_metrics"] = derived
    except Exception:
        pass

    # News
    try:
        if finnhub:
            result["news"] = finnhub.get_news_sentiment(ticker, days=30)
        else:
            result["news"] = polygon.get_news(ticker)
    except Exception:
        pass

    # Options put/call ratio
    try:
        result["options_summary"] = polygon.get_options_contracts(ticker)
    except Exception:
        pass

    # Earnings calendar
    try:
        if finnhub:
            result["earnings"] = finnhub.get_earnings_calendar(ticker)
    except Exception:
        pass

    # Insider activity
    try:
        if finnhub:
            result["insider_activity"] = finnhub.get_insider_transactions(ticker)
    except Exception:
        pass

    return result
