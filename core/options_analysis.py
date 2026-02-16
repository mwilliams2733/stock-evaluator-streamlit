"""Options analysis — rating, IV estimation, and strategy suggestions."""

import math


def calculate_options_rating(stock_data: dict) -> dict:
    """Calculate an options rating for a stock.

    Scoring factors (max 110 points):
    - Avg daily move range (25pt)
    - Volume > 1M (20pt)
    - Price range $20-$200 (15pt)
    - Momentum alignment (20pt)
    - Institutional flow (15pt)
    - Breakout score (15pt)

    Args:
        stock_data: Dict with 'price', 'volume', 'avg_daily_move', 'momentum_5d',
                    'momentum_20d', 'institutional_score', 'breakout_score', 'score'.

    Returns:
        Dict with 'options_score', 'options_rating', 'factors'.
    """
    price = stock_data.get("price", 0) or 0
    volume = stock_data.get("volume", 0) or 0
    avg_daily_move = stock_data.get("avg_daily_move", 0) or stock_data.get("atr", 0) or 0
    momentum_5d = stock_data.get("momentum_5d", 0) or 0
    momentum_20d = stock_data.get("momentum_20d", 0) or 0
    inst_score = stock_data.get("institutional_score", 50)
    if inst_score is None:
        inst_flow = stock_data.get("institutional_flow", {})
        inst_score = inst_flow.get("score", 50) if isinstance(inst_flow, dict) else 50
    breakout_score = stock_data.get("breakout_score", 0)
    if breakout_score is None:
        breakout = stock_data.get("breakout", {})
        breakout_score = breakout.get("score", 0) if isinstance(breakout, dict) else 0

    total = 0
    factors = []

    # 1. Average daily move range (0-25 points)
    if price > 0:
        move_pct = (avg_daily_move / price) * 100 if avg_daily_move else 0
    else:
        move_pct = 0
    move_pts = min(25, move_pct * 10)
    total += move_pts
    factors.append({"name": "Daily Move Range", "score": round(move_pts, 1), "max": 25})

    # 2. Volume (0-20 points)
    if volume >= 5_000_000:
        vol_pts = 20
    elif volume >= 2_000_000:
        vol_pts = 16
    elif volume >= 1_000_000:
        vol_pts = 12
    elif volume >= 500_000:
        vol_pts = 8
    else:
        vol_pts = max(0, (volume / 500_000) * 8)
    total += vol_pts
    factors.append({"name": "Volume", "score": round(vol_pts, 1), "max": 20})

    # 3. Price range (0-15 points) — optimal between $20-$200
    if 20 <= price <= 200:
        price_pts = 15
    elif 10 <= price < 20 or 200 < price <= 500:
        price_pts = 10
    elif 5 <= price < 10 or 500 < price <= 1000:
        price_pts = 5
    else:
        price_pts = 0
    total += price_pts
    factors.append({"name": "Price Range", "score": round(price_pts, 1), "max": 15})

    # 4. Momentum alignment (0-20 points)
    mom_pts = 0
    if momentum_5d > 0 and momentum_20d > 0:
        mom_pts = min(20, abs(momentum_5d) + abs(momentum_20d))
    elif momentum_5d > 0 or momentum_20d > 0:
        mom_pts = min(10, abs(momentum_5d) + abs(momentum_20d)) * 0.5
    total += mom_pts
    factors.append({"name": "Momentum", "score": round(mom_pts, 1), "max": 20})

    # 5. Institutional flow (0-15 points)
    inst_pts = min(15, max(0, (inst_score - 40) * 0.6))
    total += inst_pts
    factors.append({"name": "Institutional Flow", "score": round(inst_pts, 1), "max": 15})

    # 6. Breakout score (0-15 points)
    break_pts = min(15, breakout_score * 0.3)
    total += break_pts
    factors.append({"name": "Breakout Score", "score": round(break_pts, 1), "max": 15})

    # Determine rating
    if total >= 80:
        rating = "Excellent"
    elif total >= 60:
        rating = "Good"
    elif total >= 40:
        rating = "Fair"
    else:
        rating = "Poor"

    return {
        "options_score": round(total, 1),
        "options_rating": rating,
        "factors": factors,
    }


def estimate_iv(avg_daily_move: float, price: float = 0) -> dict:
    """Estimate implied volatility from average daily move.

    IV ≈ avg_daily_move_pct × sqrt(252)

    Args:
        avg_daily_move: ATR or average daily price change.
        price: Current stock price (for percentage calculation).

    Returns:
        Dict with 'estimated_iv', 'iv_percentile', 'iv_label'.
    """
    if price <= 0 or avg_daily_move <= 0:
        return {"estimated_iv": 0, "iv_percentile": "unknown", "iv_label": "N/A"}

    daily_pct = (avg_daily_move / price) * 100
    estimated_iv = daily_pct * math.sqrt(252)

    if estimated_iv < 20:
        percentile = "low"
        label = "Low IV"
    elif estimated_iv < 35:
        percentile = "moderate"
        label = "Moderate IV"
    elif estimated_iv < 50:
        percentile = "high"
        label = "High IV"
    else:
        percentile = "extreme"
        label = "Extreme IV"

    return {
        "estimated_iv": round(estimated_iv, 1),
        "iv_percentile": percentile,
        "iv_label": label,
    }


def suggest_options_strategy(stock_data: dict) -> dict:
    """Suggest an options strategy based on stock characteristics.

    Args:
        stock_data: Dict with score, flow, breakout, momentum, price, etc.

    Returns:
        Dict with 'name', 'description', 'dte_range', 'conviction',
        'max_risk', 'target_return', 'rationale', 'strikes'.
    """
    score = stock_data.get("score", 0) or 0
    ema_score = stock_data.get("ema_score", 0) or 0
    rsi = stock_data.get("rsi", 50) or 50
    price = stock_data.get("price", 0) or 0

    inst_score = stock_data.get("institutional_score", 50)
    if inst_score is None:
        inst_flow = stock_data.get("institutional_flow", {})
        inst_score = inst_flow.get("score", 50) if isinstance(inst_flow, dict) else 50

    breakout_score = stock_data.get("breakout_score", 0)
    if breakout_score is None:
        breakout = stock_data.get("breakout", {})
        breakout_score = breakout.get("score", 0) if isinstance(breakout, dict) else 0

    squeeze = stock_data.get("bollinger_squeeze", False)
    avg_daily_move = stock_data.get("avg_daily_move", 0) or stock_data.get("atr", 0) or 0

    # Estimate IV
    iv_data = estimate_iv(avg_daily_move, price)
    iv_level = iv_data["iv_percentile"]

    # Strategy selection logic (ported from HTML lines 5985-6084)
    if breakout_score >= 50 and iv_level in ("low", "moderate"):
        # Breakout + low/moderate IV → Long Calls
        return {
            "name": "Long Calls",
            "description": "Buy calls to capture breakout move with favorable IV",
            "dte_range": "30-45 DTE",
            "conviction": "High" if score >= 70 else "Medium",
            "max_risk": "Premium paid",
            "target_return": "50-100%",
            "rationale": f"Pre-breakout setup (score {breakout_score}) with {iv_level} IV — favorable for buying options",
            "strikes": {
                "entry": f"${price * 1.05:,.2f} (5% OTM)" if price else "5% OTM",
            },
        }

    elif breakout_score >= 40 and iv_level in ("high",):
        # Breakout + high IV → Bull Call Spread
        return {
            "name": "Bull Call Spread",
            "description": "Debit spread to limit cost in high IV environment",
            "dte_range": "45 DTE",
            "conviction": "Medium",
            "max_risk": "Net debit",
            "target_return": "50-150%",
            "rationale": f"Breakout potential but high IV — spread reduces cost basis",
            "strikes": {
                "long": f"${price * 1.02:,.2f} (2% OTM)" if price else "2% OTM",
                "short": f"${price * 1.10:,.2f} (10% OTM)" if price else "10% OTM",
            },
        }

    elif inst_score >= 65:
        # Strong institutional accumulation → Cash-Secured Puts
        return {
            "name": "Cash-Secured Puts",
            "description": "Sell puts to collect premium at institutional support levels",
            "dte_range": "30-45 DTE",
            "conviction": "Medium-High",
            "max_risk": "Assignment at strike",
            "target_return": "Premium collected (2-4%)",
            "rationale": f"Strong institutional flow (score {inst_score}) provides support — sell puts to collect premium or buy at discount",
            "strikes": {
                "put_strike": f"${price * 0.95:,.2f} (5% OTM)" if price else "5% OTM",
            },
        }

    elif score >= 70 and ema_score >= 60:
        # High score → LEAPS
        return {
            "name": "LEAPS Calls",
            "description": "Long-dated calls for sustained uptrend",
            "dte_range": "90-180 DTE",
            "conviction": "Medium",
            "max_risk": "Premium paid",
            "target_return": "100-200%",
            "rationale": f"Strong score ({score}) and trend (EMA {ema_score}) support longer hold",
            "strikes": {
                "entry": f"${price * 1.05:,.2f} (5% OTM)" if price else "5% OTM",
            },
        }

    elif score >= 55:
        # Moderate score → Bull Call Spread
        return {
            "name": "Bull Call Spread",
            "description": "Defined-risk bullish play",
            "dte_range": "45 DTE",
            "conviction": "Medium",
            "max_risk": "Net debit",
            "target_return": "50-100%",
            "rationale": f"Moderate setup (score {score}) — spread limits risk while capturing upside",
            "strikes": {
                "long": f"${price * 1.02:,.2f} (2% OTM)" if price else "2% OTM",
                "short": f"${price * 1.10:,.2f} (10% OTM)" if price else "10% OTM",
            },
        }

    elif squeeze and rsi < 40:
        # Squeeze + oversold → Bull Put Spread
        return {
            "name": "Bull Put Spread",
            "description": "Credit spread to profit from support hold during squeeze",
            "dte_range": "30-45 DTE",
            "conviction": "Medium",
            "max_risk": "Spread width minus credit",
            "target_return": "Credit collected (30-50% of width)",
            "rationale": "Bollinger squeeze with oversold RSI — premium selling opportunity at support",
            "strikes": {
                "short_put": f"${price * 0.95:,.2f} (5% OTM)" if price else "5% OTM",
                "long_put": f"${price * 0.90:,.2f} (10% OTM)" if price else "10% OTM",
            },
        }

    else:
        # No strong conviction → Watch Only
        return {
            "name": "Watch Only",
            "description": "No clear options setup — wait for better entry",
            "dte_range": "N/A",
            "conviction": "Low",
            "max_risk": "N/A",
            "target_return": "N/A",
            "rationale": "Insufficient technical alignment for options entry",
            "strikes": {},
        }


def options_rating_color(rating: str) -> str:
    """Return color for options rating badge."""
    colors = {
        "Excellent": "#00c853",
        "Good": "#4caf50",
        "Fair": "#ff9800",
        "Poor": "#f44336",
    }
    return colors.get(rating, "#8b949e")
