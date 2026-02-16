"""Relative Strength vs SPY — computes RS Rank at multiple timeframes."""

import pandas as pd


def calculate_rs_vs_spy(stock_df: pd.DataFrame, spy_df: pd.DataFrame) -> dict:
    """Calculate relative strength of a stock vs SPY.

    Args:
        stock_df: Stock OHLCV DataFrame with 'date' and 'close' columns.
        spy_df: SPY OHLCV DataFrame with 'date' and 'close' columns.

    Returns:
        Dict with rs_rank (0-99), rs_1w, rs_1m, rs_3m, rs_6m, rs_rating.
    """
    if stock_df.empty or spy_df.empty:
        return _default_rs()

    try:
        stock_close = stock_df["close"].values
        spy_close = spy_df["close"].values

        if len(stock_close) < 5 or len(spy_close) < 5:
            return _default_rs()

        current_stock = stock_close[-1]
        current_spy = spy_close[-1]

        # Calculate returns at different timeframes
        def _pct_return(arr, periods):
            if len(arr) > periods:
                return (arr[-1] / arr[-periods - 1] - 1) * 100
            return 0.0

        rs_1w = _pct_return(stock_close, 5) - _pct_return(spy_close, 5)
        rs_1m = _pct_return(stock_close, 21) - _pct_return(spy_close, 21)
        rs_3m = _pct_return(stock_close, 63) - _pct_return(spy_close, 63)
        rs_6m = _pct_return(stock_close, 126) - _pct_return(spy_close, 126)

        # Weighted composite: 1m=50%, 3m=35%, 6m=15%
        composite = rs_1m * 0.50 + rs_3m * 0.35 + rs_6m * 0.15

        # Map to 0-99 RS Rank scale
        # Composite range is roughly -50 to +50 for most stocks
        # 50 = market-matching
        rs_rank = int(max(0, min(99, 50 + composite * 1.0)))

        # Letter rating
        rs_rating = _rank_to_rating(rs_rank)

        return {
            "rs_rank": rs_rank,
            "rs_1w": round(rs_1w, 2),
            "rs_1m": round(rs_1m, 2),
            "rs_3m": round(rs_3m, 2),
            "rs_6m": round(rs_6m, 2),
            "rs_composite": round(composite, 2),
            "rs_rating": rs_rating,
        }

    except Exception:
        return _default_rs()


def _rank_to_rating(rank: int) -> str:
    """Convert RS Rank (0-99) to letter rating."""
    if rank >= 90:
        return "A+"
    elif rank >= 80:
        return "A"
    elif rank >= 70:
        return "B+"
    elif rank >= 60:
        return "B"
    elif rank >= 50:
        return "C+"
    elif rank >= 40:
        return "C"
    elif rank >= 30:
        return "D+"
    elif rank >= 20:
        return "D"
    else:
        return "F"


def _default_rs() -> dict:
    """Return default RS values when calculation is not possible."""
    return {
        "rs_rank": 50,
        "rs_1w": 0.0,
        "rs_1m": 0.0,
        "rs_3m": 0.0,
        "rs_6m": 0.0,
        "rs_composite": 0.0,
        "rs_rating": "C+",
    }


def format_rs_rank(rank: int) -> str:
    """Format RS Rank for display."""
    rating = _rank_to_rating(rank)
    return f"{rank} ({rating})"


def rs_rank_color(rank: int) -> str:
    """Return color based on RS Rank."""
    if rank >= 80:
        return "#00c853"  # Green
    elif rank >= 60:
        return "#4caf50"  # Light green
    elif rank >= 40:
        return "#ff9800"  # Orange
    elif rank >= 20:
        return "#ff5722"  # Red-orange
    else:
        return "#f44336"  # Red
