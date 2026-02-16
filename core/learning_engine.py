"""Adaptive learning engine — tracks trade outcomes and suggests parameter adjustments."""

import datetime as dt

from data.persistence import load_trade_history, save_trade_history
from config.signals import SIGNAL_WIN_RATES


def record_trade_entry(
    ticker: str,
    action: str,
    entry_price: float,
    scores: dict,
) -> dict:
    """Record a new trade entry.

    Args:
        ticker: Stock symbol.
        action: Recommendation action (e.g., 'STRONG BUY').
        entry_price: Entry price.
        scores: Dict with score, ema_score, rsi, institutional_score, etc.

    Returns:
        The created trade record.
    """
    trades = load_trade_history()
    trade = {
        "id": f"{ticker}-{dt.datetime.now().strftime('%Y%m%d%H%M%S')}",
        "ticker": ticker,
        "action": action,
        "entry_price": entry_price,
        "entry_date": dt.date.today().isoformat(),
        "score_at_entry": scores.get("score", 0),
        "ema_score_at_entry": scores.get("ema_score", 0),
        "rsi_at_entry": scores.get("rsi", 50),
        "inst_score_at_entry": scores.get("institutional_score", 50),
        "breakout_at_entry": scores.get("breakout_score", 0),
        "exit_price": None,
        "exit_date": None,
        "return_pct": None,
        "outcome": None,  # WIN, LOSS, TIMEOUT
        "status": "OPEN",
    }
    trades.append(trade)
    save_trade_history(trades)
    return trade


def record_trade_exit(trade_id: str, exit_price: float) -> dict | None:
    """Record a trade exit.

    Args:
        trade_id: The trade ID.
        exit_price: Exit price.

    Returns:
        The updated trade record, or None if not found.
    """
    trades = load_trade_history()
    for trade in trades:
        if trade.get("id") == trade_id and trade.get("status") == "OPEN":
            trade["exit_price"] = exit_price
            trade["exit_date"] = dt.date.today().isoformat()

            entry = trade.get("entry_price", 0)
            if entry > 0:
                ret = ((exit_price - entry) / entry) * 100
                trade["return_pct"] = round(ret, 2)

                # Determine outcome
                if ret >= 10:
                    trade["outcome"] = "WIN"
                elif ret <= -15:
                    trade["outcome"] = "LOSS"
                else:
                    trade["outcome"] = "TIMEOUT"
            else:
                trade["return_pct"] = 0
                trade["outcome"] = "TIMEOUT"

            trade["status"] = "CLOSED"
            save_trade_history(trades)
            return trade

    return None


def check_pending_trades(polygon) -> list:
    """Check current prices for open trades.

    Args:
        polygon: PolygonData instance.

    Returns:
        List of open trades with current price and unrealized P&L.
    """
    from config.settings import last_market_day

    trades = load_trade_history()
    open_trades = [t for t in trades if t.get("status") == "OPEN"]

    results = []
    market_day = last_market_day()

    for trade in open_trades:
        ticker = trade.get("ticker")
        try:
            df = polygon.get_aggregates(
                ticker,
                (dt.date.today() - dt.timedelta(days=10)).isoformat(),
                market_day,
            )
            if not df.empty:
                current_price = float(df.iloc[-1]["close"])
                entry = trade.get("entry_price", 0)
                pnl_pct = ((current_price - entry) / entry * 100) if entry > 0 else 0

                results.append({
                    **trade,
                    "current_price": current_price,
                    "unrealized_pnl_pct": round(pnl_pct, 2),
                    "days_held": (dt.date.today() - dt.date.fromisoformat(trade["entry_date"])).days
                    if trade.get("entry_date")
                    else 0,
                })
        except Exception:
            results.append({**trade, "current_price": None, "unrealized_pnl_pct": None})

    return results


def analyze_outcomes() -> dict:
    """Analyze all closed trades to calculate performance metrics.

    Returns:
        Dict with win rates by action, factor correlations, and overall stats.
    """
    trades = load_trade_history()
    closed = [t for t in trades if t.get("status") == "CLOSED"]

    if not closed:
        return {
            "total_closed": 0,
            "total_open": len([t for t in trades if t.get("status") == "OPEN"]),
            "by_action": {},
            "overall_win_rate": 0,
            "overall_avg_return": 0,
            "factor_insights": {},
        }

    # By action
    by_action = {}
    for trade in closed:
        action = trade.get("action", "UNKNOWN")
        if action not in by_action:
            by_action[action] = {"wins": 0, "losses": 0, "total": 0, "returns": []}
        by_action[action]["total"] += 1
        if trade.get("outcome") == "WIN":
            by_action[action]["wins"] += 1
        elif trade.get("outcome") == "LOSS":
            by_action[action]["losses"] += 1
        by_action[action]["returns"].append(trade.get("return_pct", 0))

    for action, data in by_action.items():
        data["win_rate"] = data["wins"] / data["total"] * 100 if data["total"] else 0
        data["avg_return"] = sum(data["returns"]) / len(data["returns"]) if data["returns"] else 0
        # Compare to expected
        expected = SIGNAL_WIN_RATES.get(action, {})
        data["expected_win_rate"] = expected.get("win_rate", 0) * 100
        data["outperforming"] = data["win_rate"] > data["expected_win_rate"]
        del data["returns"]  # Don't need the raw list in output

    # Factor insights
    wins = [t for t in closed if t.get("outcome") == "WIN"]
    losses = [t for t in closed if t.get("outcome") == "LOSS"]

    factor_insights = {}
    for factor in ["score_at_entry", "ema_score_at_entry", "rsi_at_entry", "inst_score_at_entry"]:
        win_vals = [t.get(factor, 0) for t in wins if t.get(factor) is not None]
        loss_vals = [t.get(factor, 0) for t in losses if t.get(factor) is not None]
        avg_win = sum(win_vals) / len(win_vals) if win_vals else 0
        avg_loss = sum(loss_vals) / len(loss_vals) if loss_vals else 0
        factor_insights[factor] = {
            "avg_in_wins": round(avg_win, 1),
            "avg_in_losses": round(avg_loss, 1),
            "differential": round(avg_win - avg_loss, 1),
        }

    all_returns = [t.get("return_pct", 0) for t in closed]

    return {
        "total_closed": len(closed),
        "total_open": len([t for t in trades if t.get("status") == "OPEN"]),
        "by_action": by_action,
        "overall_win_rate": len(wins) / len(closed) * 100 if closed else 0,
        "overall_avg_return": sum(all_returns) / len(all_returns) if all_returns else 0,
        "factor_insights": factor_insights,
    }


def suggest_adjustments() -> dict:
    """Suggest threshold adjustments based on trade outcomes.

    Returns:
        Dict with suggested changes to scoring thresholds.
    """
    outcomes = analyze_outcomes()
    if outcomes["total_closed"] < 10:
        return {
            "sufficient_data": False,
            "message": f"Need at least 10 closed trades (have {outcomes['total_closed']})",
            "suggestions": [],
        }

    suggestions = []
    insights = outcomes.get("factor_insights", {})

    # Score threshold suggestion
    score_diff = insights.get("score_at_entry", {}).get("differential", 0)
    if score_diff > 10:
        suggestions.append({
            "parameter": "min_score",
            "current": 55,
            "suggested": int(insights["score_at_entry"]["avg_in_wins"]) - 5,
            "reason": f"Winning trades have {score_diff:.0f}pt higher scores on average",
        })

    # EMA score suggestion
    ema_diff = insights.get("ema_score_at_entry", {}).get("differential", 0)
    if ema_diff > 10:
        suggestions.append({
            "parameter": "min_ema_score",
            "current": 70,
            "suggested": int(insights["ema_score_at_entry"]["avg_in_wins"]) - 5,
            "reason": f"Winning trades have {ema_diff:.0f}pt higher EMA scores",
        })

    # RSI suggestion
    rsi_win = insights.get("rsi_at_entry", {}).get("avg_in_wins", 50)
    if 40 <= rsi_win <= 65:
        suggestions.append({
            "parameter": "rsi_range",
            "current": "30-70",
            "suggested": f"{int(rsi_win) - 15}-{int(rsi_win) + 15}",
            "reason": f"Winning trades have avg RSI of {rsi_win:.0f}",
        })

    return {
        "sufficient_data": True,
        "total_trades_analyzed": outcomes["total_closed"],
        "overall_win_rate": round(outcomes["overall_win_rate"], 1),
        "suggestions": suggestions,
    }


def get_stats() -> dict:
    """Get a quick summary of the learning engine state."""
    trades = load_trade_history()
    open_trades = [t for t in trades if t.get("status") == "OPEN"]
    closed_trades = [t for t in trades if t.get("status") == "CLOSED"]

    return {
        "total_trades": len(trades),
        "open_trades": len(open_trades),
        "closed_trades": len(closed_trades),
        "wins": len([t for t in closed_trades if t.get("outcome") == "WIN"]),
        "losses": len([t for t in closed_trades if t.get("outcome") == "LOSS"]),
        "has_enough_data": len(closed_trades) >= 10,
    }
