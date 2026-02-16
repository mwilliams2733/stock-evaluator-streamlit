"""Finnhub API wrapper — news sentiment, basic metrics, earnings calendar."""
import datetime as dt

import requests
import streamlit as st

from config.settings import FINNHUB_API_KEY
from config import settings
from data.cache import get_cached, set_cached

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


def _api_key() -> str:
    return st.session_state.get("finnhub_api_key") or FINNHUB_API_KEY


class FinnhubData:
    """High-level wrapper around Finnhub REST API with caching."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or _api_key()

    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        """Make a GET request to Finnhub."""
        params = params or {}
        params["token"] = self.api_key
        url = f"{FINNHUB_BASE_URL}/{endpoint}"
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Basic financial metrics
    # ------------------------------------------------------------------
    def get_basic_metrics(self, symbol: str) -> dict:
        """Fetch key financial metrics (P/E, EPS, ROE, beta, etc.)."""
        cache_key = f"finnhub_metrics_{symbol}"
        cached = get_cached(cache_key, ttl=settings.CACHE_TTL_METRICS)
        if cached is not None:
            return cached

        try:
            data = self._get("stock/metric", {"symbol": symbol, "metric": "all"})
            metric = data.get("metric", {})

            result = {
                "pe_ratio": metric.get("peNormalizedAnnual"),
                "eps": metric.get("epsBasicExclExtraItemsTTM"),
                "revenue_growth_yoy": metric.get("revenueGrowthQuarterlyYoy"),
                "profit_margin": metric.get("netProfitMarginTTM"),
                "roe": metric.get("roeTTM"),
                "roa": metric.get("roaTTM"),
                "current_ratio": metric.get("currentRatioQuarterly"),
                "dividend_yield": metric.get("dividendYieldIndicatedAnnual"),
                "beta": metric.get("beta"),
                "week52_high": metric.get("52WeekHigh"),
                "week52_low": metric.get("52WeekLow"),
                "shares_outstanding": metric.get("sharesOutstanding"),
                "market_cap": metric.get("marketCapitalization"),
            }
            set_cached(cache_key, result)
            return result
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # News with sentiment
    # ------------------------------------------------------------------
    def get_news_sentiment(self, symbol: str, days: int = 7) -> list[dict]:
        """Fetch recent company news with keyword-based sentiment."""
        cache_key = f"finnhub_news_{symbol}_{days}"
        cached = get_cached(cache_key, ttl=settings.CACHE_TTL_NEWS)
        if cached is not None:
            return cached

        try:
            today = dt.date.today()
            from_date = (today - dt.timedelta(days=days)).isoformat()
            to_date = today.isoformat()

            data = self._get("company-news", {
                "symbol": symbol,
                "from": from_date,
                "to": to_date,
            })

            articles = []
            for item in (data or [])[:20]:
                sentiment = _analyze_sentiment(
                    item.get("headline", ""),
                    item.get("summary", ""),
                )
                articles.append({
                    "headline": item.get("headline", ""),
                    "summary": item.get("summary", ""),
                    "url": item.get("url", ""),
                    "source": item.get("source", ""),
                    "datetime": item.get("datetime", 0),
                    "category": _categorize_article(
                        item.get("headline", ""),
                        item.get("summary", ""),
                    ),
                    "sentiment": sentiment,
                })
            set_cached(cache_key, articles)
            return articles
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Earnings calendar
    # ------------------------------------------------------------------
    def get_earnings_calendar(self, symbol: str) -> list[dict]:
        """Fetch upcoming earnings dates."""
        cache_key = f"finnhub_earnings_{symbol}"
        cached = get_cached(cache_key, ttl=settings.CACHE_TTL_NEWS)
        if cached is not None:
            return cached

        try:
            today = dt.date.today()
            from_date = today.isoformat()
            to_date = (today + dt.timedelta(days=90)).isoformat()

            data = self._get("calendar/earnings", {
                "symbol": symbol,
                "from": from_date,
                "to": to_date,
            })

            earnings = []
            for item in data.get("earningsCalendar", []):
                earnings.append({
                    "date": item.get("date", ""),
                    "eps_estimate": item.get("epsEstimate"),
                    "eps_actual": item.get("epsActual"),
                    "revenue_estimate": item.get("revenueEstimate"),
                    "revenue_actual": item.get("revenueActual"),
                    "quarter": item.get("quarter"),
                    "year": item.get("year"),
                })
            set_cached(cache_key, earnings)
            return earnings
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Insider transactions
    # ------------------------------------------------------------------
    def get_insider_transactions(self, symbol: str) -> dict:
        """Fetch insider transaction summary."""
        cache_key = f"finnhub_insider_{symbol}"
        cached = get_cached(cache_key, ttl=settings.CACHE_TTL_NEWS)
        if cached is not None:
            return cached

        try:
            data = self._get("stock/insider-transactions", {"symbol": symbol})

            result = {
                "buy_count": 0,
                "sell_count": 0,
                "net_shares": 0,
                "buy_value": 0,
                "sell_value": 0,
                "recent_transactions": [],
            }

            thirty_days_ago = dt.date.today() - dt.timedelta(days=30)
            for t in (data.get("data", []) or []):
                tx_date = t.get("transactionDate", "")
                if tx_date and dt.date.fromisoformat(tx_date) >= thirty_days_ago:
                    shares = t.get("share", 0) or 0
                    price = t.get("price", 0) or 0
                    value = shares * price

                    if t.get("transactionCode") == "P":
                        result["buy_count"] += 1
                        result["net_shares"] += shares
                        result["buy_value"] += value
                    elif t.get("transactionCode") == "S":
                        result["sell_count"] += 1
                        result["net_shares"] -= shares
                        result["sell_value"] += value

                    if len(result["recent_transactions"]) < 10:
                        result["recent_transactions"].append({
                            "name": t.get("name", ""),
                            "date": tx_date,
                            "type": "Buy" if t.get("transactionCode") == "P" else "Sell",
                            "shares": shares,
                            "value": value,
                            "price": price,
                        })

            set_cached(cache_key, result)
            return result
        except Exception:
            return {
                "buy_count": 0, "sell_count": 0, "net_shares": 0,
                "buy_value": 0, "sell_value": 0, "recent_transactions": [],
            }


# --- Sentiment helpers ---

_POSITIVE_WORDS = [
    "surge", "rally", "gain", "beat", "upgrade", "acquire", "partnership",
    "growth", "profit", "exceed", "strong", "record", "breakthrough", "success",
]

_NEGATIVE_WORDS = [
    "plunge", "drop", "loss", "miss", "downgrade", "decline", "weak",
    "concern", "fail", "warning", "lawsuit", "investigation",
]


def _analyze_sentiment(headline: str, summary: str) -> dict:
    """Simple keyword-based sentiment analysis."""
    text = f"{headline} {summary}".lower()
    score = 0
    for word in _POSITIVE_WORDS:
        if word in text:
            score += 1
    for word in _NEGATIVE_WORDS:
        if word in text:
            score -= 1

    if score > 0:
        return {"label": "Positive", "color": "green", "score": score}
    if score < 0:
        return {"label": "Negative", "color": "red", "score": score}
    return {"label": "Neutral", "color": "gray", "score": 0}


def _categorize_article(headline: str, summary: str) -> str:
    """Categorize a news article by keywords."""
    text = f"{headline} {summary}".lower()

    ma_keywords = ["acquisition", "merger", "buyout", "takeover", "deal", "acquired", "acquires"]
    earnings_keywords = ["earnings", "revenue", "profit", "quarterly", "results", "eps", "guidance"]
    analyst_keywords = ["upgrade", "downgrade", "rating", "price target", "analyst", "recommendation"]

    if any(kw in text for kw in ma_keywords):
        return "M&A"
    if any(kw in text for kw in earnings_keywords):
        return "Earnings"
    if any(kw in text for kw in analyst_keywords):
        return "Analyst"
    return "General"
