"""Technical analysis calculations — EMA, RSI, MACD, Bollinger, ATR, ADX, volume."""
import numpy as np
import pandas as pd


# ------------------------------------------------------------------
# Exponential Moving Averages
# ------------------------------------------------------------------

def calculate_emas(df: pd.DataFrame, periods: list[int] | None = None) -> dict:
    """Calculate EMAs for given periods.

    Args:
        df: DataFrame with 'close' column.
        periods: EMA periods (default [8, 21, 50, 200]).

    Returns:
        Dict mapping period -> Series of EMA values.
    """
    if periods is None:
        periods = [8, 21, 50, 200]
    close = df["close"]
    return {p: close.ewm(span=p, adjust=False).mean() for p in periods}


def calculate_ema_score(emas: dict, current_price: float) -> int:
    """Score EMA alignment from 0-100.

    Higher score = better bullish alignment (price > EMA8 > EMA21 > EMA50 > EMA200).
    """
    score = 0
    periods = sorted(emas.keys())

    # Get the latest EMA values
    latest = {}
    for p in periods:
        s = emas[p]
        if len(s) > 0 and pd.notna(s.iloc[-1]):
            latest[p] = float(s.iloc[-1])

    if not latest:
        return 0

    # Price above EMAs (up to 40 points)
    for p in periods:
        if p in latest and current_price > latest[p]:
            weight = {8: 10, 21: 10, 50: 10, 200: 10}.get(p, 5)
            score += weight

    # EMA stacking order (up to 30 points)
    sorted_periods = sorted(latest.keys())
    for i in range(len(sorted_periods) - 1):
        p_short = sorted_periods[i]
        p_long = sorted_periods[i + 1]
        if latest[p_short] > latest[p_long]:
            score += 10

    # Price proximity to short-term EMA (up to 15 points)
    if 8 in latest:
        dist_pct = abs(current_price - latest[8]) / latest[8] * 100
        if dist_pct < 1:
            score += 15
        elif dist_pct < 2:
            score += 10
        elif dist_pct < 3:
            score += 5

    # Trend direction - short EMAs rising (up to 15 points)
    for p in [8, 21]:
        if p in emas and len(emas[p]) >= 5:
            recent = float(emas[p].iloc[-1])
            prior = float(emas[p].iloc[-5])
            if pd.notna(recent) and pd.notna(prior) and recent > prior:
                score += 7 if p == 8 else 8

    return min(score, 100)


# ------------------------------------------------------------------
# RSI (Relative Strength Index)
# ------------------------------------------------------------------

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate RSI for a DataFrame."""
    close = df["close"]
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))


# ------------------------------------------------------------------
# MACD (Moving Average Convergence Divergence)
# ------------------------------------------------------------------

def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26,
                   signal: int = 9) -> dict:
    """Calculate MACD line, signal line, and histogram."""
    close = df["close"]
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return {
        "macd_line": macd_line,
        "signal_line": signal_line,
        "histogram": histogram,
    }


# ------------------------------------------------------------------
# Bollinger Bands
# ------------------------------------------------------------------

def calculate_bollinger(df: pd.DataFrame, period: int = 20,
                        std_dev: float = 2.0) -> dict:
    """Calculate Bollinger Bands and squeeze detection."""
    close = df["close"]
    mid = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = mid + std_dev * std
    lower = mid - std_dev * std

    # Bandwidth as % of mid
    bandwidth = ((upper - lower) / mid * 100).fillna(0)

    # Squeeze detection: bandwidth in lowest 20% of recent 120 bars
    squeeze = False
    if len(bandwidth) >= 120:
        recent_bw = bandwidth.iloc[-120:]
        current_bw = bandwidth.iloc[-1]
        threshold = recent_bw.quantile(0.20)
        squeeze = current_bw <= threshold

    return {
        "upper": upper,
        "mid": mid,
        "lower": lower,
        "bandwidth": bandwidth,
        "squeeze": squeeze,
    }


# ------------------------------------------------------------------
# ATR (Average True Range)
# ------------------------------------------------------------------

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


# ------------------------------------------------------------------
# ADX (Average Directional Index)
# ------------------------------------------------------------------

def calculate_adx(df: pd.DataFrame, period: int = 14) -> dict:
    """Calculate ADX with +DI and -DI."""
    high = df["high"]
    low = df["low"]
    close = df["close"]

    # Directional movement
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = pd.Series(
        np.where((up_move > down_move) & (up_move > 0), up_move, 0),
        index=df.index,
    )
    minus_dm = pd.Series(
        np.where((down_move > up_move) & (down_move > 0), down_move, 0),
        index=df.index,
    )

    # True range
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)

    # Smoothed values
    atr = tr.ewm(alpha=1 / period, min_periods=period).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1 / period, min_periods=period).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1 / period, min_periods=period).mean() / atr)

    # DX and ADX
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1e-10)
    adx = dx.ewm(alpha=1 / period, min_periods=period).mean()

    return {
        "adx": adx,
        "plus_di": plus_di,
        "minus_di": minus_di,
    }


# ------------------------------------------------------------------
# Volume Analysis
# ------------------------------------------------------------------

def calculate_obv(df: pd.DataFrame) -> pd.Series:
    """Calculate On-Balance Volume."""
    close = df["close"]
    volume = df["volume"]
    obv = pd.Series(0.0, index=df.index)
    for i in range(1, len(df)):
        if close.iloc[i] > close.iloc[i - 1]:
            obv.iloc[i] = obv.iloc[i - 1] + volume.iloc[i]
        elif close.iloc[i] < close.iloc[i - 1]:
            obv.iloc[i] = obv.iloc[i - 1] - volume.iloc[i]
        else:
            obv.iloc[i] = obv.iloc[i - 1]
    return obv


def calculate_volume_ratio(df: pd.DataFrame, period: int = 20) -> float:
    """Calculate current volume vs average volume ratio."""
    if len(df) < period + 1:
        return 1.0
    avg_vol = df["volume"].iloc[-(period + 1):-1].mean()
    if avg_vol == 0:
        return 1.0
    return float(df["volume"].iloc[-1] / avg_vol)


def calculate_accumulation_distribution(df: pd.DataFrame) -> pd.Series:
    """Calculate Accumulation/Distribution line."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    volume = df["volume"]

    mfm = ((close - low) - (high - close)) / (high - low).replace(0, 1e-10)
    mfv = mfm * volume
    return mfv.cumsum()


# ------------------------------------------------------------------
# Support / Resistance
# ------------------------------------------------------------------

def calculate_support_resistance(df: pd.DataFrame, window: int = 5,
                                  num_levels: int = 3) -> dict:
    """Calculate support and resistance levels from swing points."""
    high = df["high"]
    low = df["low"]

    supports = []
    resistances = []

    for i in range(window, len(df) - window):
        # Swing high
        if all(high.iloc[i] >= high.iloc[i - j] for j in range(1, window + 1)) and \
           all(high.iloc[i] >= high.iloc[i + j] for j in range(1, window + 1)):
            resistances.append(float(high.iloc[i]))

        # Swing low
        if all(low.iloc[i] <= low.iloc[i - j] for j in range(1, window + 1)) and \
           all(low.iloc[i] <= low.iloc[i + j] for j in range(1, window + 1)):
            supports.append(float(low.iloc[i]))

    # Deduplicate by clustering close levels (within 1%)
    supports = _cluster_levels(supports)[:num_levels]
    resistances = _cluster_levels(resistances)[:num_levels]

    return {
        "supports": sorted(supports),
        "resistances": sorted(resistances, reverse=True),
    }


def _cluster_levels(levels: list[float], threshold: float = 0.01) -> list[float]:
    """Cluster price levels that are within threshold% of each other."""
    if not levels:
        return []
    levels = sorted(levels)
    clusters = [[levels[0]]]
    for level in levels[1:]:
        if (level - clusters[-1][-1]) / clusters[-1][-1] < threshold:
            clusters[-1].append(level)
        else:
            clusters.append([level])
    # Return the average of each cluster, sorted by frequency (most touches first)
    result = [(sum(c) / len(c), len(c)) for c in clusters]
    result.sort(key=lambda x: -x[1])
    return [r[0] for r in result]


# ------------------------------------------------------------------
# Combined technicals
# ------------------------------------------------------------------

def calculate_all_technicals(df: pd.DataFrame) -> dict:
    """Calculate all technical indicators for a DataFrame.

    Returns:
        Dict with all computed indicators and their latest values.
    """
    if df.empty or len(df) < 30:
        return {}

    close = df["close"]
    current_price = float(close.iloc[-1])

    # EMAs
    emas = calculate_emas(df)
    ema_score = calculate_ema_score(emas, current_price)

    # RSI
    rsi = calculate_rsi(df)
    rsi_value = float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else None

    # MACD
    macd = calculate_macd(df)
    macd_value = float(macd["histogram"].iloc[-1]) if pd.notna(macd["histogram"].iloc[-1]) else None

    # Bollinger
    bb = calculate_bollinger(df)

    # ATR
    atr = calculate_atr(df)
    atr_value = float(atr.iloc[-1]) if pd.notna(atr.iloc[-1]) else None

    # ADX
    adx_data = calculate_adx(df)
    adx_value = float(adx_data["adx"].iloc[-1]) if pd.notna(adx_data["adx"].iloc[-1]) else None

    # Volume
    vol_ratio = calculate_volume_ratio(df)

    # S/R
    sr = calculate_support_resistance(df)

    # Momentum
    momentum_5d = ((current_price - float(close.iloc[-6])) / float(close.iloc[-6]) * 100) if len(close) >= 6 else 0
    momentum_20d = ((current_price - float(close.iloc[-21])) / float(close.iloc[-21]) * 100) if len(close) >= 21 else 0

    return {
        "price": current_price,
        "emas": {p: float(s.iloc[-1]) for p, s in emas.items() if pd.notna(s.iloc[-1])},
        "ema_score": ema_score,
        "rsi": rsi_value,
        "macd_histogram": macd_value,
        "macd_line": float(macd["macd_line"].iloc[-1]) if pd.notna(macd["macd_line"].iloc[-1]) else None,
        "macd_signal": float(macd["signal_line"].iloc[-1]) if pd.notna(macd["signal_line"].iloc[-1]) else None,
        "bollinger_squeeze": bb["squeeze"],
        "bollinger_bandwidth": float(bb["bandwidth"].iloc[-1]) if pd.notna(bb["bandwidth"].iloc[-1]) else None,
        "atr": atr_value,
        "atr_pct": (atr_value / current_price * 100) if atr_value else None,
        "adx": adx_value,
        "plus_di": float(adx_data["plus_di"].iloc[-1]) if pd.notna(adx_data["plus_di"].iloc[-1]) else None,
        "minus_di": float(adx_data["minus_di"].iloc[-1]) if pd.notna(adx_data["minus_di"].iloc[-1]) else None,
        "volume_ratio": vol_ratio,
        "supports": sr["supports"],
        "resistances": sr["resistances"],
        "momentum_5d": momentum_5d,
        "momentum_20d": momentum_20d,
        # Full series for charting
        "_ema_series": emas,
        "_rsi_series": rsi,
        "_macd": macd,
        "_bollinger": bb,
        "_atr_series": atr,
    }
