"""9-level recommendation engine with win probability and expected return."""

from config.signals import SIGNAL_WIN_RATES, TECHNICAL_ADJUSTMENTS


# ─── Action Colors ────────────────────────────────────────────────────────────

ACTION_COLORS = {
    "STRONG BUY":      "#00c853",
    "ACCUMULATE":      "#4caf50",
    "BUY DIP":         "#8bc34a",
    "SPECULATIVE BUY": "#cddc39",
    "WATCH":           "#ffeb3b",
    "HOLD":            "#ff9800",
    "REDUCE":          "#ff5722",
    "TAKE PROFITS":    "#f44336",
    "SELL":            "#d50000",
}

ACTION_PRIORITY = {
    "STRONG BUY": 1,
    "ACCUMULATE": 2,
    "BUY DIP": 3,
    "SPECULATIVE BUY": 4,
    "WATCH": 5,
    "HOLD": 6,
    "REDUCE": 7,
    "TAKE PROFITS": 8,
    "SELL": 9,
}


def get_action_color(action: str) -> str:
    """Return a hex color for the given action level."""
    return ACTION_COLORS.get(action, "#8b949e")


def get_action_priority(action: str) -> int:
    """Return sort priority for the action (lower = more bullish)."""
    return ACTION_PRIORITY.get(action, 6)


# ─── Recommendation Generator ────────────────────────────────────────────────

def generate_recommendation(stock_data: dict) -> dict:
    """Generate a 9-level recommendation for a stock.

    Args:
        stock_data: Dict with keys like 'score', 'ema_score', 'rsi',
                    'institutional_score' or 'institutional_flow',
                    'breakout' or 'breakout_score',
                    'momentum_5d', 'momentum_20d',
                    'bollinger_squeeze'.

    Returns:
        Dict with 'action', 'confidence', 'reasoning', 'option_strategy', 'metrics'.
    """
    # Extract values with fallbacks
    score = stock_data.get("score", 0) or 0
    rsi = stock_data.get("rsi", 50) or 50
    ema_score = stock_data.get("ema_score", 0) or 0

    # Handle institutional score from different data shapes
    inst_score = stock_data.get("institutional_score", 50)
    if inst_score is None:
        inst_flow = stock_data.get("institutional_flow", {})
        inst_score = inst_flow.get("score", 50) if isinstance(inst_flow, dict) else 50

    squeeze = stock_data.get("bollinger_squeeze", False)
    week_change = stock_data.get("momentum_5d", 0) or 0
    month_change = stock_data.get("momentum_20d", 0) or 0

    action = "HOLD"
    confidence = "MEDIUM"
    reasoning = []
    option_strategy = None

    # ─── BACKTEST-OPTIMIZED THRESHOLDS ────────────────────────────────────
    # Based on 71-stock backtest with +20% target, -15% stop, 14/45 day holds

    # CRITICAL: Never buy overbought — 0% win rate in backtest
    if rsi > 70:
        action = "TAKE PROFITS"
        confidence = "HIGH"
        reasoning.append("RSI overbought (>70) — backtest shows 0% win rate for buys")
        option_strategy = {"type": "SELL CALLS", "strike": "ATM covered call", "expiry": "30 DTE"}
        return _build_result(action, confidence, reasoning, option_strategy, stock_data)

    # STRONG BUY — 40% win rate at 45 days (best performer)
    if score >= 75 and ema_score >= 70 and inst_score >= 65 and 40 <= rsi <= 70:
        action = "STRONG BUY"
        confidence = "HIGH"
        reasoning.append("Score 75+ with strong institutional flow (40% backtest win rate)")
        reasoning.append(f"RSI {rsi:.0f} in optimal 40-70 range")
        option_strategy = {"type": "BUY CALLS", "strike": "ATM or 5% OTM", "expiry": "45-60 DTE"}

    # BUY DIP — 19% win rate at 45 days (second best)
    elif rsi < 30 and inst_score >= 60 and ema_score >= 40:
        action = "BUY DIP"
        confidence = "MEDIUM"
        reasoning.append("Oversold RSI <30 with institutional support (19% backtest win rate)")
        reasoning.append("Best as 45-day hold for mean reversion")
        option_strategy = {"type": "SELL PUTS", "strike": "10-15% OTM", "expiry": "45-60 DTE"}

    # ACCUMULATE — 33% win rate with healthy RSI
    elif score >= 70 and ema_score >= 60 and 35 <= rsi <= 65:
        action = "ACCUMULATE"
        confidence = "MEDIUM"
        reasoning.append("Score 70+ in RSI sweet spot (33% backtest win rate)")
        if squeeze:
            reasoning.append("Bollinger squeeze adds breakout potential")
        option_strategy = {"type": "BUY CALLS", "strike": "5-10% OTM", "expiry": "45-60 DTE"}

    # SPECULATIVE BUY — 12% win rate (consistent across timeframes)
    elif rsi < 25 and month_change < -30:
        action = "SPECULATIVE BUY"
        confidence = "LOW"
        reasoning.append("Capitulation level — deeply oversold")
        reasoning.append("High risk/reward mean reversion play")
        option_strategy = {"type": "BUY CALLS", "strike": "15-20% OTM", "expiry": "60-90 DTE"}

    # SELL — Strong sell signals
    elif score < 25 and ema_score < 30 and inst_score < 40:
        action = "SELL"
        confidence = "HIGH"
        reasoning.append("Weak technicals with distribution")
        if month_change < -20:
            reasoning.append("Significant downtrend accelerating")
            option_strategy = {"type": "BUY PUTS", "strike": "ATM", "expiry": "45-60 DTE"}

    # REDUCE — Deteriorating but not critical
    elif score < 40 and month_change < -15 and inst_score < 45:
        action = "REDUCE"
        confidence = "MEDIUM"
        reasoning.append("Deteriorating momentum with weak institutional flow")

    # WATCH — Potential setup forming
    elif 55 <= score < 70 and 35 <= rsi <= 55:
        action = "WATCH"
        confidence = "LOW"
        reasoning.append("Neutral setup — wait for score 70+ or RSI dip for entry")
        if squeeze:
            reasoning.append("Squeeze forming — watch for breakout trigger")

    # HOLD — Default
    else:
        action = "HOLD"
        confidence = "MEDIUM"
        if score >= 50:
            reasoning.append("Decent score but missing confirmation signals")
        else:
            reasoning.append("Insufficient momentum for new positions")

    return _build_result(action, confidence, reasoning, option_strategy, stock_data)


def _build_result(action, confidence, reasoning, option_strategy, stock_data):
    """Build the standard result dict."""
    return {
        "action": action,
        "confidence": confidence,
        "reasoning": reasoning,
        "option_strategy": option_strategy,
        "metrics": {
            "score": stock_data.get("score", 0),
            "rsi": stock_data.get("rsi", 50),
            "ema_score": stock_data.get("ema_score", 0),
            "institutional_score": stock_data.get("institutional_score",
                                                   stock_data.get("institutional_flow", {}).get("score", 50)
                                                   if isinstance(stock_data.get("institutional_flow"), dict) else 50),
            "momentum_5d": stock_data.get("momentum_5d", 0),
            "momentum_20d": stock_data.get("momentum_20d", 0),
        },
    }


# ─── Win Probability ──────────────────────────────────────────────────────────

def calculate_win_probability(action: str, stock_data: dict) -> dict:
    """Calculate win probability using base signal rates + technical adjustments.

    Args:
        action: The recommendation action string.
        stock_data: Dict with technical indicators.

    Returns:
        Dict with 'win_probability', 'expected_return', 'confidence', 'adjustments'.
    """
    base = SIGNAL_WIN_RATES.get(action, SIGNAL_WIN_RATES["HOLD"])
    base_win_rate = base["win_rate"]
    base_avg_return = base["avg_return"]
    base_confidence = base["confidence"]

    # Extract values
    ema_score = stock_data.get("ema_score", 0) or 0
    rsi = stock_data.get("rsi", 50) or 50
    score = stock_data.get("score", 0) or 0
    squeeze = stock_data.get("bollinger_squeeze", False)

    inst_score = stock_data.get("institutional_score", 50)
    if inst_score is None:
        inst_flow = stock_data.get("institutional_flow", {})
        inst_score = inst_flow.get("score", 50) if isinstance(inst_flow, dict) else 50

    # Apply technical adjustments
    total_adjustment = 0.0
    adjustments = []

    # EMA high
    if ema_score >= 70:
        adj = TECHNICAL_ADJUSTMENTS["ema_high"]["adjustment"]
        total_adjustment += adj
        adjustments.append({"label": "EMA Score 70+", "value": adj})

    # RSI overbought
    if rsi > 70:
        adj = TECHNICAL_ADJUSTMENTS["rsi_overbought"]["adjustment"]
        total_adjustment += adj
        adjustments.append({"label": "RSI Overbought", "value": adj})

    # RSI optimal
    if 40 <= rsi <= 65:
        adj = TECHNICAL_ADJUSTMENTS["rsi_optimal"]["adjustment"]
        total_adjustment += adj
        adjustments.append({"label": "RSI Optimal Zone", "value": adj})

    # Institutional strong
    if inst_score >= 65:
        adj = TECHNICAL_ADJUSTMENTS["inst_strong"]["adjustment"]
        total_adjustment += adj
        adjustments.append({"label": "Strong Inst. Flow", "value": adj})

    # Score high
    if score >= 55:
        adj = TECHNICAL_ADJUSTMENTS["score_high"]["adjustment"]
        total_adjustment += adj
        adjustments.append({"label": "Overall Score 55+", "value": adj})

    # Trend bullish
    if ema_score >= 60:
        adj = TECHNICAL_ADJUSTMENTS["trend_bullish"]["adjustment"]
        total_adjustment += adj
        adjustments.append({"label": "Bullish Trend", "value": adj})

    # Trend bearish
    if ema_score < 30:
        adj = TECHNICAL_ADJUSTMENTS["trend_bearish"]["adjustment"]
        total_adjustment += adj
        adjustments.append({"label": "Bearish Trend", "value": adj})

    # Squeeze potential
    if squeeze:
        adj = TECHNICAL_ADJUSTMENTS["squeeze_potential"]["adjustment"]
        total_adjustment += adj
        adjustments.append({"label": "Squeeze Setup", "value": adj})

    # Calculate final probability (clamped 0-1)
    win_probability = max(0.0, min(1.0, base_win_rate + total_adjustment))
    expected_return = base_avg_return * (1 + total_adjustment)

    return {
        "win_probability": win_probability,
        "expected_return": expected_return,
        "confidence": base_confidence,
        "hold_period": base["hold_period"],
        "adjustments": adjustments,
        "total_adjustment": total_adjustment,
    }
