"""Scoring systems — overall score, EMA, breakout, institutional flow."""
import numpy as np
import pandas as pd


# ------------------------------------------------------------------
# EMA Score (0-100) — delegates to technicals
# ------------------------------------------------------------------

def calculate_ema_score(emas: dict, current_price: float) -> int:
    """Score EMA alignment. See technicals.calculate_ema_score for details."""
    from core.technicals import calculate_ema_score as _ema_score
    return _ema_score(emas, current_price)


# ------------------------------------------------------------------
# Institutional Flow Score (0-100)
# ------------------------------------------------------------------

def calculate_institutional_flow(df: pd.DataFrame) -> dict:
    """Analyze institutional accumulation/distribution patterns.

    Returns:
        Dict with score (0-100), signal label, signals list, and confidence.
    """
    if df.empty or len(df) < 20:
        return {"score": 50, "signal": "Neutral", "signals": [], "confidence": "Low"}

    score = 50
    signals = []

    close = df["close"]
    volume = df["volume"]
    recent = df.tail(20)

    # 1. Volume-Price Trend (up-day vs down-day volume)
    up_vol = 0.0
    down_vol = 0.0
    for i in range(1, len(recent)):
        if recent["close"].iloc[i] > recent["close"].iloc[i - 1]:
            up_vol += recent["volume"].iloc[i]
        else:
            down_vol += recent["volume"].iloc[i]

    vol_ratio = up_vol / max(down_vol, 1)
    if vol_ratio > 1.5:
        score += 15
        signals.append(f"Heavy buying pressure ({vol_ratio:.1f}x vol ratio)")
    elif vol_ratio < 0.7:
        score -= 15
        signals.append(f"Distribution detected ({vol_ratio:.1f}x vol ratio)")

    # 2. OBV Trend
    obv = [0.0]
    for i in range(1, min(30, len(df))):
        idx = len(df) - 30 + i if len(df) >= 30 else i
        if idx < len(df) and idx > 0:
            if close.iloc[idx] > close.iloc[idx - 1]:
                obv.append(obv[-1] + float(volume.iloc[idx]))
            elif close.iloc[idx] < close.iloc[idx - 1]:
                obv.append(obv[-1] - float(volume.iloc[idx]))
            else:
                obv.append(obv[-1])

    if len(obv) >= 15:
        obv_recent = np.mean(obv[-5:])
        obv_prior = np.mean(obv[10:15]) if len(obv) >= 15 else np.mean(obv[:5])
        if obv_recent > obv_prior * 1.1:
            score += 10
            signals.append("OBV trending up (accumulation)")
        elif obv_recent < obv_prior * 0.9:
            score -= 10
            signals.append("OBV trending down (distribution)")

    # 3. A/D Line
    ad_values = []
    ad = 0.0
    tail = df.tail(30)
    for i in range(len(tail)):
        h = float(tail["high"].iloc[i])
        l = float(tail["low"].iloc[i])
        c = float(tail["close"].iloc[i])
        v = float(tail["volume"].iloc[i])
        mfm = ((c - l) - (h - c)) / max(h - l, 1e-10)
        ad += mfm * v
        ad_values.append(ad)

    if len(ad_values) >= 15:
        if ad_values[-1] > ad_values[-11]:
            score += 10
            signals.append("A/D Line rising (smart money buying)")
        elif ad_values[-1] < ad_values[-11]:
            score -= 10
            signals.append("A/D Line falling (smart money selling)")

    # 4. Unusual Volume
    if len(df) >= 25:
        avg_vol = float(volume.iloc[-21:-1].mean())
        recent_avg = float(volume.iloc[-5:].mean())
        if avg_vol > 0:
            vol_spike = recent_avg / avg_vol
            if vol_spike > 2:
                price_change = (float(close.iloc[-1]) - float(close.iloc[-5])) / float(close.iloc[-5])
                if price_change > 0:
                    score += 15
                    signals.append(f"Institutional accumulation ({vol_spike:.1f}x volume + price up)")
                else:
                    score -= 10
                    signals.append(f"High volume selling ({vol_spike:.1f}x volume)")

    # 5. Consecutive up days on volume
    consecutive_up = 0
    avg_vol_20 = float(volume.iloc[-20:].mean()) if len(df) >= 20 else float(volume.mean())
    for i in range(len(df) - 1, max(len(df) - 11, 0), -1):
        if i > 0 and close.iloc[i] > close.iloc[i - 1] and volume.iloc[i] > avg_vol_20:
            consecutive_up += 1
        else:
            break

    if consecutive_up >= 4:
        score += 10
        signals.append(f"{consecutive_up} consecutive up days on volume")

    score = max(0, min(100, score))

    signal = "Neutral"
    confidence = "Medium"
    if score >= 75:
        signal = "Strong Accumulation"
        confidence = "High"
    elif score >= 60:
        signal = "Accumulating"
        confidence = "Medium"
    elif score <= 25:
        signal = "Strong Distribution"
        confidence = "High"
    elif score <= 40:
        signal = "Distributing"
        confidence = "Medium"

    return {
        "score": round(score),
        "signal": signal,
        "signals": signals,
        "confidence": confidence,
        "volume_ratio": round(vol_ratio, 2),
    }


# ------------------------------------------------------------------
# Pre-Breakout Score (0-100)
# ------------------------------------------------------------------

def calculate_breakout_score(df: pd.DataFrame, technicals: dict) -> dict:
    """Detect pre-breakout patterns combining volume, consolidation, and technical signals.

    Returns:
        Dict with score (0-100), signals list, confidence, and pattern label.
    """
    if df.empty or len(df) < 30:
        return {"score": 0, "signals": [], "confidence": "Low", "pattern": "Insufficient Data"}

    score = 0
    signals = []

    close = df["close"]
    volume = df["volume"]
    high = df["high"]
    low = df["low"]

    # 1. Volume accumulation without price move
    if len(df) >= 30:
        recent_vol = float(volume.iloc[-10:].mean())
        prior_vol = float(volume.iloc[-30:-10].mean())
        recent_price_change = (float(close.iloc[-1]) - float(close.iloc[-10])) / float(close.iloc[-10]) * 100

        if prior_vol > 0:
            vol_increase = recent_vol / prior_vol
            if vol_increase > 1.5 and abs(recent_price_change) < 5:
                score += 20
                signals.append(f"Stealth accumulation: {vol_increase:.1f}x volume, flat price")
            elif vol_increase > 1.3 and abs(recent_price_change) < 8:
                score += 12
                signals.append("Quiet accumulation detected")

    # 2. Tight trading range
    if len(df) >= 15:
        range_high = float(high.iloc[-15:].max())
        range_low = float(low.iloc[-15:].min())
        range_pct = (range_high - range_low) / range_low * 100

        if range_pct < 10:
            score += 15
            signals.append(f"Tight consolidation: {range_pct:.1f}% range")
        elif range_pct < 15:
            score += 8
            signals.append("Narrow trading range")

    # 3. Higher lows pattern
    if len(df) >= 15:
        higher_lows = 0
        for i in range(0, min(10, len(df) - 5), 5):
            period_low1 = float(low.iloc[-(i + 5):-(i + 0) if i > 0 else len(df)].min())
            period_low2 = float(low.iloc[-(i + 10):-(i + 5)].min()) if len(df) >= i + 10 else period_low1
            if period_low1 > period_low2:
                higher_lows += 1

        if higher_lows >= 2:
            score += 10
            signals.append("Higher lows pattern forming")

    # 4. Volume dry-up then spike
    if len(df) >= 20:
        avg_vol = float(volume.iloc[-20:].mean())
        if avg_vol > 0:
            recent_spike = float(volume.iloc[-1]) > avg_vol * 1.5
            prior_quiet = float(volume.iloc[-6:-1].mean()) < avg_vol * 0.8
            if recent_spike and prior_quiet:
                score += 15
                signals.append("Volume spike after quiet period")

    # 5. Decreasing volatility
    atr = technicals.get("atr")
    atr_pct = technicals.get("atr_pct")
    if atr_pct is not None and atr_pct < 2:
        score += 12
        signals.append("Volatility compression")

    # 6. Bollinger squeeze
    if technicals.get("bollinger_squeeze"):
        score += 15
        signals.append("Bollinger Band squeeze detected")

    # 7. RSI in healthy zone
    rsi = technicals.get("rsi")
    if rsi is not None and 50 <= rsi <= 70:
        score += 8

    # Normalize to 0-100
    normalized = min(round(score * 0.70), 100)

    confidence = "Low"
    pattern = "No Clear Pattern"
    if normalized >= 75:
        confidence = "Very High"
        pattern = "EXTREME BREAKOUT PROBABILITY"
    elif normalized >= 65:
        confidence = "High"
        pattern = "HIGH PROBABILITY BREAKOUT"
    elif normalized >= 50:
        confidence = "Medium"
        pattern = "Pre-Breakout Building"
    elif normalized >= 30:
        confidence = "Low"
        pattern = "Early Accumulation"

    return {
        "score": normalized,
        "signals": signals,
        "confidence": confidence,
        "pattern": pattern,
    }


# ------------------------------------------------------------------
# Overall Score (0-100)
# ------------------------------------------------------------------

def calculate_overall_score(technicals: dict, institutional_flow: dict,
                            breakout: dict) -> dict:
    """Calculate the composite overall score combining all factors.

    Matches the weight distribution from the HTML app:
    - EMA Score: 35%
    - Institutional Flow: ~20%
    - Pre-breakout: ~15%
    - Momentum (5d): ~5%
    - Momentum (20d): ~10%
    - Volume ratio: ~10%
    - RSI quality: ~5%

    Returns:
        Dict with score (0-100) and reasons list.
    """
    score = 0.0
    reasons = []

    # EMA alignment (up to ~35 points)
    ema_score = technicals.get("ema_score", 0)
    score += ema_score * 0.35
    if ema_score >= 70:
        reasons.append(f"Strong EMA alignment ({ema_score})")
    elif ema_score >= 50:
        reasons.append(f"Moderate EMA alignment ({ema_score})")

    # EMA signal bonus
    ema_values = technicals.get("emas", {})
    price = technicals.get("price", 0)
    bullish_emas = sum(1 for v in ema_values.values() if price > v)
    if bullish_emas >= 3:
        score += 8
        reasons.append("Price above multiple EMAs")

    # Institutional flow (up to ~18 points)
    inst_score = institutional_flow.get("score", 50)
    if inst_score >= 70:
        score += 18
        reasons.append(f"Strong institutional accumulation ({inst_score})")
    elif inst_score >= 55:
        score += 10
        reasons.append(f"Moderate accumulation ({inst_score})")
    elif inst_score <= 30:
        score -= 10
        reasons.append("Distribution detected")

    # Pre-breakout (up to ~8 points)
    breakout_score = breakout.get("score", 0)
    if breakout_score >= 50:
        score += 8
        reasons.append(f"Pre-breakout setup ({breakout_score})")
    elif breakout_score >= 35:
        score += 5
    elif breakout_score >= 20:
        score += 3

    # 5-day momentum (up to ~4 points)
    mom_5d = technicals.get("momentum_5d", 0)
    if mom_5d > 10:
        score += 4
    elif mom_5d > 5:
        score += 2
    elif mom_5d > 0:
        score += 1

    # 20-day momentum (up to ~8 points)
    mom_20d = technicals.get("momentum_20d", 0)
    if mom_20d > 15:
        score += 8
        reasons.append(f"Strong 20d momentum (+{mom_20d:.1f}%)")
    elif mom_20d > 10:
        score += 5

    # Volume ratio (up to ~12 points)
    vol_ratio = technicals.get("volume_ratio", 1.0)
    if vol_ratio > 2:
        score += 12
        reasons.append(f"High volume ({vol_ratio:.1f}x avg)")
    elif vol_ratio > 1.5:
        score += 8

    # RSI quality (up to ~8 points)
    rsi = technicals.get("rsi")
    if rsi is not None:
        if 50 <= rsi <= 70:
            score += 8
        elif 70 < rsi < 80:
            score += 4
        elif rsi < 30:
            reasons.append(f"RSI oversold ({rsi:.0f})")

    score = max(0, min(round(score), 100))

    return {
        "score": score,
        "reasons": reasons,
        "ema_score": ema_score,
        "institutional_score": inst_score,
        "breakout_score": breakout_score,
    }


# ------------------------------------------------------------------
# Filter check for scanner
# ------------------------------------------------------------------

def passes_scan_filters(stock_data: dict, filters: dict) -> bool:
    """Check if a stock passes the scanner filter criteria.

    Args:
        stock_data: Dict with price, volume, score, ema_score.
        filters: Dict with min_price, min_volume, min_score, min_ema_score.
    """
    price = stock_data.get("price", 0)
    volume = stock_data.get("volume", 0)
    score = stock_data.get("score", 0)
    ema_score = stock_data.get("ema_score", 0)

    if price < filters.get("min_price", 0):
        return False
    if volume < filters.get("min_volume", 0):
        return False
    if score < filters.get("min_score", 0):
        return False
    if ema_score < filters.get("min_ema_score", 0):
        return False

    return True
