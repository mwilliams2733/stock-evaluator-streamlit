"""Application configuration, default weights, and constants."""
import os
from dotenv import load_dotenv

load_dotenv()

# --- API Configuration ---
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")

# --- Scanner Defaults ---
SCANNER_LOOKBACK_DAYS = 200  # Days of price history for technical analysis
MIN_PRICE = 5.0
MIN_VOLUME = 500_000
MIN_SCORE = 55
MIN_EMA_SCORE = 70
TOP_N_RESULTS = 100

# --- Scoring Weights ---
# Overall score composition
SCORE_WEIGHTS = {
    "ema_alignment": 0.35,
    "institutional_flow": 0.20,
    "pre_breakout": 0.15,
    "momentum_5d": 0.05,
    "momentum_20d": 0.10,
    "volume_ratio": 0.10,
    "rsi_quality": 0.05,
}

# Moat score factor weights (max points per factor, total = 100)
MOAT_FACTOR_WEIGHTS = {
    "grossMargin": 20,
    "roe": 15,
    "revenueGrowth": 12,
    "lowDebt": 13,
    "marketPosition": 12,
    "fcf": 8,
    "ccr": 10,
    "roic": 10,
}

# Fair value sector multiples
SECTOR_MULTIPLES = {
    "Technology": {"pe": 28, "pb": 7.0, "ps": 6.0, "evEbitda": 18},
    "Healthcare": {"pe": 22, "pb": 4.0, "ps": 4.0, "evEbitda": 14},
    "Financial Services": {"pe": 14, "pb": 1.5, "ps": 3.0, "evEbitda": 10},
    "Consumer Cyclical": {"pe": 20, "pb": 4.0, "ps": 1.5, "evEbitda": 12},
    "Consumer Defensive": {"pe": 22, "pb": 4.0, "ps": 2.0, "evEbitda": 14},
    "Industrials": {"pe": 20, "pb": 3.5, "ps": 2.0, "evEbitda": 12},
    "Energy": {"pe": 12, "pb": 1.8, "ps": 1.2, "evEbitda": 6},
    "Utilities": {"pe": 18, "pb": 1.8, "ps": 2.2, "evEbitda": 10},
    "Real Estate": {"pe": 35, "pb": 2.2, "ps": 6.0, "evEbitda": 16},
    "Basic Materials": {"pe": 15, "pb": 2.0, "ps": 1.5, "evEbitda": 8},
    "Communication Services": {"pe": 18, "pb": 3.5, "ps": 3.0, "evEbitda": 10},
    "default": {"pe": 20, "pb": 3.0, "ps": 2.5, "evEbitda": 12},
}

# SIC code to sector mapping
SIC_SECTOR_MAP = {
    (3570, 3579): "Technology",
    (7370, 7379): "Technology",
    (3825, 3829): "Technology",
    (2833, 2836): "Healthcare",
    (3841, 3851): "Healthcare",
    (6000, 6799): "Financial Services",
    (5200, 5999): "Consumer Cyclical",
    (2000, 2111): "Consumer Defensive",
    (3500, 3569): "Industrials",
    (1300, 1389): "Energy",
    (4900, 4999): "Utilities",
    (6500, 6553): "Real Estate",
    (1000, 1499): "Basic Materials",
    (4800, 4899): "Communication Services",
}

# --- Cache TTL (seconds) ---
CACHE_TTL_TICKERS = 86400      # 24 hours
CACHE_TTL_PRICES = 3600        # 1 hour
CACHE_TTL_FINANCIALS = 86400   # 24 hours
CACHE_TTL_NEWS = 3600          # 1 hour
CACHE_TTL_DETAILS = 86400      # 24 hours
CACHE_TTL_METRICS = 86400      # 24 hours
CACHE_TTL_SCANNER = 86400      # 24 hours

# --- Sector ETF Mapping ---
SECTOR_ETFS = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financials": "XLF",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Materials": "XLB",
    "Real Estate": "XLRE",
    "Utilities": "XLU",
    "Communication Services": "XLC",
}

# --- Persistence ---
PERSISTENCE_DIR = "data/user"

# --- Government Data Cache ---
GOV_API_CACHE_TTL = 3600  # 1 hour

# --- Display ---
APP_TITLE = "Dynamic Momentum Screener"
APP_ICON = "📈"

# --- Scanner Rate Limiting ---
SCANNER_API_DELAY = 0.15  # seconds between API calls during scan
SCANNER_BATCH_SIZE = 50   # stocks processed per batch


def last_market_day() -> str:
    """Return the most recent completed US market trading day as YYYY-MM-DD.

    Walks back from today, skipping weekends and major US holidays.
    Always returns at least yesterday to avoid requesting intraday data
    that the free Polygon tier cannot access.
    """
    import datetime as _dt

    today = _dt.date.today()

    # Major US market holidays (month, day) — fixed-date ones
    _FIXED_HOLIDAYS = {
        (1, 1),   # New Year's Day
        (6, 19),  # Juneteenth
        (7, 4),   # Independence Day
        (12, 25), # Christmas Day
    }

    for days_back in range(1, 10):
        candidate = today - _dt.timedelta(days=days_back)
        # Skip weekends
        if candidate.weekday() >= 5:  # 5=Saturday, 6=Sunday
            continue
        # Skip known fixed holidays
        if (candidate.month, candidate.day) in _FIXED_HOLIDAYS:
            continue
        return candidate.isoformat()

    # Fallback: 5 days ago
    return (today - _dt.timedelta(days=5)).isoformat()


def get_sector_from_sic(sic_code: str | None) -> str:
    """Map SIC code to sector name for fair value calculations."""
    if not sic_code:
        return "default"
    try:
        sic = int(sic_code)
    except (ValueError, TypeError):
        return "default"
    for (lo, hi), sector in SIC_SECTOR_MAP.items():
        if lo <= sic <= hi:
            return sector
    return "default"
