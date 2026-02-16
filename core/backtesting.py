"""Historical backtesting engine — validates scoring strategy on past data."""

import datetime as dt
import time

import pandas as pd

from config.signals import BACKTEST_UNIVERSE, BACKTEST_CONFIG
from config.settings import last_market_day, SCANNER_API_DELAY
from core.technicals import calculate_all_technicals
from core.scoring import (
    calculate_institutional_flow,
    calculate_breakout_score,
    calculate_overall_score,
)
from core.recommendations import generate_recommendation


def run_backtest(
    polygon,
    config: dict | None = None,
    progress_callback=None,
) -> dict:
    """Run a full backtest across the BACKTEST_UNIVERSE.

    For each stock, walks through historical data looking for signal points
    where the scoring system triggers a buy signal, then checks forward
    performance to see if the trade would have been profitable.

    Args:
        polygon: PolygonData instance.
        config: Optional override for BACKTEST_CONFIG.
        progress_callback: Callable(current, total, message).

    Returns:
        Dict with 'trades', 'summary', 'factor_analysis', 'action_breakdown'.
    """
    cfg = {**BACKTEST_CONFIG, **(config or {})}
    universe = BACKTEST_UNIVERSE
    total = len(universe)

    holding_days = cfg["holding_period_days"]
    target_pct = cfg["target_percent"]
    stop_pct = cfg["stop_percent"]
    min_score = cfg["min_overall_score"]
    min_bars = cfg.get("min_bars_required", 50)

    today = dt.date.today()
    market_day = last_market_day()
    from_date = (today - dt.timedelta(days=500)).isoformat()
    to_date = market_day

    trades = []

    for idx, ticker in enumerate(universe):
        if progress_callback and idx % 5 == 0:
            progress_callback(
                idx, total,
                f"Backtesting {ticker}... ({len(trades)} trades found)"
            )

        try:
            df = polygon.get_aggregates(ticker, from_date, to_date)
            if df.empty or len(df) < min_bars + holding_days:
                continue

            # Walk through the data, checking for signals
            # Use a step of 5 (weekly) to avoid too many correlated signals
            for i in range(min_bars, len(df) - holding_days, 5):
                # Calculate technicals up to this point
                window = df.iloc[:i + 1].copy()
                if len(window) < 30:
                    continue

                technicals = calculate_all_technicals(window)
                if not technicals:
                    continue

                score = technicals.get("ema_score", 0)

                # Quick filter: only evaluate if EMA score suggests potential
                if score < min_score:
                    continue

                inst_flow = calculate_institutional_flow(window)
                breakout = calculate_breakout_score(window, technicals)
                overall = calculate_overall_score(technicals, inst_flow, breakout)

                overall_score = overall.get("score", 0)
                if overall_score < min_score:
                    continue

                # Generate recommendation for this point
                stock_data = {
                    "score": overall_score,
                    "ema_score": technicals.get("ema_score", 0),
                    "rsi": technicals.get("rsi", 50),
                    "institutional_score": inst_flow.get("score", 50),
                    "breakout_score": breakout.get("score", 0),
                    "momentum_5d": technicals.get("momentum_5d", 0),
                    "momentum_20d": technicals.get("momentum_20d", 0),
                    "bollinger_squeeze": technicals.get("bollinger_squeeze", False),
                }
                rec = generate_recommendation(stock_data)
                action = rec["action"]

                # Only test buy-side signals
                if action not in ("STRONG BUY", "ACCUMULATE", "BUY DIP", "SPECULATIVE BUY"):
                    continue

                # Check forward performance
                entry_price = float(df.iloc[i]["close"])
                forward = check_forward_performance(
                    df, i, entry_price, target_pct, stop_pct, holding_days
                )

                trade = {
                    "ticker": ticker,
                    "entry_date": str(df.iloc[i]["date"]),
                    "entry_price": entry_price,
                    "action": action,
                    "confidence": rec["confidence"],
                    "overall_score": overall_score,
                    "ema_score": technicals.get("ema_score", 0),
                    "rsi": technicals.get("rsi", 50),
                    "institutional_score": inst_flow.get("score", 50),
                    "breakout_score": breakout.get("score", 0),
                    "bollinger_squeeze": technicals.get("bollinger_squeeze", False),
                    **forward,
                }
                trades.append(trade)

            # Rate limiting
            time.sleep(SCANNER_API_DELAY)

        except Exception:
            continue

    if progress_callback:
        progress_callback(total, total, f"Backtest complete! {len(trades)} trades evaluated.")

    # Analyze results
    summary = _calculate_summary(trades)
    factor_analysis = _analyze_factors(trades)
    action_breakdown = _breakdown_by_action(trades)

    return {
        "trades": trades,
        "summary": summary,
        "factor_analysis": factor_analysis,
        "action_breakdown": action_breakdown,
    }


def check_forward_performance(
    df: pd.DataFrame,
    signal_idx: int,
    entry_price: float,
    target_pct: float,
    stop_pct: float,
    max_days: int,
) -> dict:
    """Simulate forward from a signal point.

    Args:
        df: Full OHLCV DataFrame.
        signal_idx: Index of the signal bar.
        entry_price: Entry price.
        target_pct: Target return percentage (e.g., 10 for +10%).
        stop_pct: Stop loss percentage (e.g., 15 for -15%).
        max_days: Maximum holding period in bars.

    Returns:
        Dict with outcome, exit_price, return_pct, days_held, max_favorable, max_adverse.
    """
    target_price = entry_price * (1 + target_pct / 100)
    stop_price = entry_price * (1 - stop_pct / 100)

    max_favorable = 0.0
    max_adverse = 0.0
    exit_price = entry_price
    days_held = 0
    outcome = "TIMEOUT"

    end_idx = min(signal_idx + max_days + 1, len(df))

    for j in range(signal_idx + 1, end_idx):
        high = float(df.iloc[j]["high"])
        low = float(df.iloc[j]["low"])
        close = float(df.iloc[j]["close"])
        days_held = j - signal_idx

        # Track max favorable / adverse excursion
        favorable = ((high - entry_price) / entry_price) * 100
        adverse = ((entry_price - low) / entry_price) * 100
        max_favorable = max(max_favorable, favorable)
        max_adverse = max(max_adverse, adverse)

        # Check stop hit first (worst case)
        if low <= stop_price:
            outcome = "LOSS"
            exit_price = stop_price
            break

        # Check target hit
        if high >= target_price:
            outcome = "WIN"
            exit_price = target_price
            break

        exit_price = close

    return_pct = ((exit_price - entry_price) / entry_price) * 100

    return {
        "outcome": outcome,
        "exit_price": round(exit_price, 2),
        "return_pct": round(return_pct, 2),
        "days_held": days_held,
        "max_favorable": round(max_favorable, 2),
        "max_adverse": round(max_adverse, 2),
    }


def _calculate_summary(trades: list) -> dict:
    """Calculate aggregate statistics from trades."""
    if not trades:
        return {
            "total_trades": 0, "wins": 0, "losses": 0, "timeouts": 0,
            "win_rate": 0, "avg_return": 0, "profit_factor": 0,
            "avg_days_held": 0, "best_trade": 0, "worst_trade": 0,
        }

    wins = [t for t in trades if t["outcome"] == "WIN"]
    losses = [t for t in trades if t["outcome"] == "LOSS"]
    timeouts = [t for t in trades if t["outcome"] == "TIMEOUT"]

    returns = [t["return_pct"] for t in trades]
    win_returns = [t["return_pct"] for t in wins]
    loss_returns = [abs(t["return_pct"]) for t in losses]

    profit_factor = (
        sum(win_returns) / sum(loss_returns) if loss_returns else float("inf")
    )

    return {
        "total_trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "timeouts": len(timeouts),
        "win_rate": len(wins) / len(trades) * 100 if trades else 0,
        "avg_return": sum(returns) / len(returns) if returns else 0,
        "profit_factor": round(profit_factor, 2),
        "avg_days_held": sum(t["days_held"] for t in trades) / len(trades),
        "best_trade": max(returns) if returns else 0,
        "worst_trade": min(returns) if returns else 0,
    }


def _analyze_factors(trades: list) -> dict:
    """Analyze which factors correlate with wins vs losses."""
    if not trades:
        return {}

    factors = ["overall_score", "ema_score", "rsi", "institutional_score", "breakout_score"]
    result = {}

    for factor in factors:
        wins = [t[factor] for t in trades if t["outcome"] == "WIN" and factor in t]
        losses = [t[factor] for t in trades if t["outcome"] == "LOSS" and factor in t]

        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 0

        result[factor] = {
            "avg_in_wins": round(avg_win, 1),
            "avg_in_losses": round(avg_loss, 1),
            "differential": round(avg_win - avg_loss, 1),
        }

    return result


def _breakdown_by_action(trades: list) -> dict:
    """Breakdown win rates by action level."""
    if not trades:
        return {}

    actions = {}
    for trade in trades:
        action = trade.get("action", "UNKNOWN")
        if action not in actions:
            actions[action] = {"trades": [], "wins": 0, "total": 0}
        actions[action]["trades"].append(trade)
        actions[action]["total"] += 1
        if trade["outcome"] == "WIN":
            actions[action]["wins"] += 1

    result = {}
    for action, data in actions.items():
        returns = [t["return_pct"] for t in data["trades"]]
        result[action] = {
            "total": data["total"],
            "wins": data["wins"],
            "win_rate": data["wins"] / data["total"] * 100 if data["total"] else 0,
            "avg_return": sum(returns) / len(returns) if returns else 0,
        }

    return result
