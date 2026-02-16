"""Polygon.io API wrapper — all API calls go through this module."""
import datetime as dt
from typing import Optional

import pandas as pd
import streamlit as st
from polygon import RESTClient

from config.settings import POLYGON_API_KEY
from config import settings
from data.cache import get_cached, set_cached


def _client(api_key: str | None = None) -> RESTClient:
    key = api_key or st.session_state.get("polygon_api_key") or POLYGON_API_KEY
    if not key or key == "your_api_key_here":
        st.error("Please set your Polygon API key in the Settings page.")
        st.stop()
    return RESTClient(key)


class PolygonData:
    """High-level wrapper around polygon-api-client with caching."""

    def __init__(self, api_key: str | None = None):
        self.client = _client(api_key)

    # ------------------------------------------------------------------
    # All active tickers (paginated)
    # ------------------------------------------------------------------
    def get_all_active_tickers(self) -> pd.DataFrame:
        """Fetch all active US stock tickers, paginating through all results."""
        cache_key = "all_active_tickers"
        cached = get_cached(cache_key, ttl=settings.CACHE_TTL_TICKERS)
        if cached is not None:
            return pd.DataFrame(cached)

        tickers = []
        for t in self.client.list_tickers(
            market="stocks", active=True, limit=1000, order="asc", sort="ticker"
        ):
            tickers.append({
                "ticker": t.ticker,
                "name": t.name,
                "market": t.market,
                "type": getattr(t, "type", ""),
                "currency_name": getattr(t, "currency_name", "usd"),
            })
        df = pd.DataFrame(tickers)
        set_cached(cache_key, df.to_dict(orient="records"))
        return df

    # ------------------------------------------------------------------
    # Aggregates (bars)
    # ------------------------------------------------------------------
    def get_aggregates(self, ticker: str, from_date: str, to_date: str,
                       timespan: str = "day", multiplier: int = 1) -> pd.DataFrame:
        """Fetch historical OHLCV bars for a single ticker."""
        cache_key = f"aggs_{ticker}_{from_date}_{to_date}_{timespan}_{multiplier}"
        cached = get_cached(cache_key, ttl=settings.CACHE_TTL_PRICES)
        if cached is not None:
            return pd.DataFrame(cached)

        aggs = []
        for a in self.client.get_aggs(
            ticker=ticker, multiplier=multiplier, timespan=timespan,
            from_=from_date, to=to_date, limit=50000
        ):
            aggs.append({
                "timestamp": a.timestamp,
                "open": a.open,
                "high": a.high,
                "low": a.low,
                "close": a.close,
                "volume": a.volume,
                "vwap": getattr(a, "vwap", None),
                "transactions": getattr(a, "transactions", None),
            })
        if aggs:
            df = pd.DataFrame(aggs)
            df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
            df = df.sort_values("date").reset_index(drop=True)
            set_cached(cache_key, df.to_dict(orient="records"))
            return df
        return pd.DataFrame()

    # ------------------------------------------------------------------
    # Grouped daily (all tickers, one day)
    # ------------------------------------------------------------------
    def get_grouped_daily(self, date: str) -> pd.DataFrame:
        """Fetch all tickers' OHLCV for a single day (efficient bulk fetch)."""
        cache_key = f"grouped_{date}"
        cached = get_cached(cache_key, ttl=settings.CACHE_TTL_SCANNER)
        if cached is not None:
            return pd.DataFrame(cached)

        resp = self.client.get_grouped_daily_aggs(date=date)
        rows = []
        for r in resp:
            rows.append({
                "ticker": r.ticker,
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
                "vwap": getattr(r, "vwap", None),
            })
        df = pd.DataFrame(rows)
        set_cached(cache_key, df.to_dict(orient="records"))
        return df

    # ------------------------------------------------------------------
    # Snapshot (current quote)
    # ------------------------------------------------------------------
    def get_snapshot(self, ticker: str) -> dict:
        """Get current snapshot for a ticker."""
        try:
            snap = self.client.get_snapshot_ticker("stocks", ticker)
            return {
                "ticker": snap.ticker,
                "day_open": getattr(snap.day, "open", None) if snap.day else None,
                "day_close": getattr(snap.day, "close", None) if snap.day else None,
                "day_high": getattr(snap.day, "high", None) if snap.day else None,
                "day_low": getattr(snap.day, "low", None) if snap.day else None,
                "day_volume": getattr(snap.day, "volume", None) if snap.day else None,
                "prev_close": getattr(snap.prev_day, "close", None) if snap.prev_day else None,
                "change_pct": getattr(snap, "todays_change_perc", None),
            }
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # Ticker details
    # ------------------------------------------------------------------
    def get_ticker_details(self, ticker: str) -> dict:
        """Fetch company info for a ticker."""
        cache_key = f"details_{ticker}"
        cached = get_cached(cache_key, ttl=settings.CACHE_TTL_DETAILS)
        if cached is not None:
            return cached

        try:
            d = self.client.get_ticker_details(ticker)
            details = {
                "ticker": d.ticker,
                "name": d.name,
                "market_cap": getattr(d, "market_cap", None),
                "sic_code": getattr(d, "sic_code", None),
                "sic_description": getattr(d, "sic_description", ""),
                "description": getattr(d, "description", ""),
                "homepage_url": getattr(d, "homepage_url", ""),
                "total_employees": getattr(d, "total_employees", None),
                "list_date": str(getattr(d, "list_date", "")),
                "type": getattr(d, "type", ""),
            }
            set_cached(cache_key, details)
            return details
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # Financials (extended beyond Karen's version)
    # ------------------------------------------------------------------
    def get_financials(self, ticker: str, limit: int = 4) -> list[dict]:
        """Fetch recent financial statements with extended fields.

        Extracts income statement, balance sheet, and cash flow data
        including fields needed for CCR, ROIC, Interest Coverage, EBITDA.
        """
        cache_key = f"financials_{ticker}"
        cached = get_cached(cache_key, ttl=settings.CACHE_TTL_FINANCIALS)
        if cached is not None:
            return cached

        results = []
        try:
            for i, f in enumerate(self.client.vx.list_stock_financials(
                ticker=ticker, limit=limit, sort="period_of_report_date",
                order="desc"
            )):
                fin = {
                    "period": getattr(f, "fiscal_period", ""),
                    "fiscal_year": getattr(f, "fiscal_year", ""),
                    "filing_date": str(getattr(f, "filing_date", "")),
                    # Income statement
                    "revenues": None,
                    "cost_of_revenue": None,
                    "operating_income": None,
                    "net_income": None,
                    "interest_expense": None,
                    "eps_basic": None,
                    "eps_diluted": None,
                    # Balance sheet
                    "total_assets": None,
                    "total_liabilities": None,
                    "equity": None,
                    "long_term_debt": None,
                    "debt_current": None,
                    "current_assets": None,
                    "current_liabilities": None,
                    "cash_and_equivalents": None,
                    # Cash flow
                    "operating_cash_flow": None,
                    "investing_cash_flow": None,
                    "depreciation": None,
                }

                inc = getattr(f, "financials", {})

                # --- Income Statement ---
                if hasattr(inc, "income_statement"):
                    stmt = inc.income_statement
                    if hasattr(stmt, "revenues"):
                        fin["revenues"] = getattr(stmt.revenues, "value", None)
                    if hasattr(stmt, "cost_of_revenue"):
                        fin["cost_of_revenue"] = getattr(stmt.cost_of_revenue, "value", None)
                    if hasattr(stmt, "operating_income_loss"):
                        fin["operating_income"] = getattr(stmt.operating_income_loss, "value", None)
                    if hasattr(stmt, "net_income_loss"):
                        fin["net_income"] = getattr(stmt.net_income_loss, "value", None)
                    if hasattr(stmt, "interest_expense_operating"):
                        fin["interest_expense"] = getattr(stmt.interest_expense_operating, "value", None)
                    elif hasattr(stmt, "interest_expense"):
                        fin["interest_expense"] = getattr(stmt.interest_expense, "value", None)
                    if hasattr(stmt, "basic_earnings_per_share"):
                        fin["eps_basic"] = getattr(stmt.basic_earnings_per_share, "value", None)
                    if hasattr(stmt, "diluted_earnings_per_share"):
                        fin["eps_diluted"] = getattr(stmt.diluted_earnings_per_share, "value", None)

                # --- Balance Sheet ---
                if hasattr(inc, "balance_sheet"):
                    bs = inc.balance_sheet
                    if hasattr(bs, "assets"):
                        fin["total_assets"] = getattr(bs.assets, "value", None)
                    if hasattr(bs, "liabilities"):
                        fin["total_liabilities"] = getattr(bs.liabilities, "value", None)
                    if hasattr(bs, "equity"):
                        fin["equity"] = getattr(bs.equity, "value", None)
                    if hasattr(bs, "long_term_debt"):
                        fin["long_term_debt"] = getattr(bs.long_term_debt, "value", None)
                    if hasattr(bs, "debt_current"):
                        fin["debt_current"] = getattr(bs.debt_current, "value", None)
                    if hasattr(bs, "current_assets"):
                        fin["current_assets"] = getattr(bs.current_assets, "value", None)
                    if hasattr(bs, "current_liabilities"):
                        fin["current_liabilities"] = getattr(bs.current_liabilities, "value", None)
                    # Cash
                    if hasattr(bs, "cash_and_cash_equivalents"):
                        fin["cash_and_equivalents"] = getattr(bs.cash_and_cash_equivalents, "value", None)
                    elif hasattr(bs, "cash"):
                        fin["cash_and_equivalents"] = getattr(bs.cash, "value", None)

                # --- Cash Flow Statement ---
                if hasattr(inc, "cash_flow_statement"):
                    cfs = inc.cash_flow_statement
                    if hasattr(cfs, "net_cash_flow_from_operating_activities"):
                        fin["operating_cash_flow"] = getattr(
                            cfs.net_cash_flow_from_operating_activities, "value", None
                        )
                    if hasattr(cfs, "net_cash_flow_from_investing_activities"):
                        fin["investing_cash_flow"] = getattr(
                            cfs.net_cash_flow_from_investing_activities, "value", None
                        )
                    if hasattr(cfs, "depreciation_and_amortization"):
                        fin["depreciation"] = getattr(
                            cfs.depreciation_and_amortization, "value", None
                        )

                results.append(fin)
                if i >= limit - 1:
                    break
        except Exception:
            pass
        set_cached(cache_key, results)
        return results

    # ------------------------------------------------------------------
    # News
    # ------------------------------------------------------------------
    def get_news(self, ticker: str, limit: int = 20) -> list[dict]:
        """Fetch recent news articles for a ticker."""
        cache_key = f"news_{ticker}_{limit}"
        cached = get_cached(cache_key, ttl=settings.CACHE_TTL_NEWS)
        if cached is not None:
            return cached

        articles = []
        try:
            for i, n in enumerate(self.client.list_ticker_news(
                ticker=ticker, limit=limit, order="desc", sort="published_utc"
            )):
                sentiments = getattr(n, "insights", []) or []
                ticker_sentiment = None
                for s in sentiments:
                    if getattr(s, "ticker", "") == ticker:
                        ticker_sentiment = getattr(s, "sentiment", None)
                        break
                articles.append({
                    "title": n.title,
                    "published": str(n.published_utc),
                    "url": getattr(n, "article_url", ""),
                    "source": (
                        getattr(n, "publisher", {}).get("name", "")
                        if isinstance(getattr(n, "publisher", None), dict)
                        else str(getattr(getattr(n, "publisher", None), "name", ""))
                    ),
                    "sentiment": ticker_sentiment,
                    "keywords": getattr(n, "keywords", []) or [],
                })
                if i >= limit - 1:
                    break
        except Exception:
            pass
        set_cached(cache_key, articles)
        return articles

    # ------------------------------------------------------------------
    # Options contracts (for put/call ratio)
    # ------------------------------------------------------------------
    def get_options_contracts(self, ticker: str) -> dict:
        """Fetch options contracts summary for put/call ratio."""
        cache_key = f"options_contracts_{ticker}"
        cached = get_cached(cache_key, ttl=3600)
        if cached is not None:
            return cached

        result = {"put_count": 0, "call_count": 0, "total": 0, "put_call_ratio": 1.0}
        try:
            for i, c in enumerate(self.client.list_options_contracts(
                underlying_ticker=ticker, expired=False, limit=100,
                order="asc", sort="expiration_date"
            )):
                if c.contract_type == "put":
                    result["put_count"] += 1
                elif c.contract_type == "call":
                    result["call_count"] += 1
                if i >= 99:
                    break

            result["total"] = result["put_count"] + result["call_count"]
            if result["call_count"] > 0:
                result["put_call_ratio"] = round(
                    result["put_count"] / result["call_count"], 2
                )
        except Exception:
            pass

        set_cached(cache_key, result)
        return result
