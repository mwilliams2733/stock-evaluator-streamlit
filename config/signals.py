"""Signal win rates, technical adjustments, and backtest configuration."""

# Win rates by recommendation action — calibrated from backtest results
SIGNAL_WIN_RATES = {
    "STRONG BUY":      {"win_rate": 0.40, "avg_return": 0.20, "hold_period": 45, "confidence": 0.80},
    "ACCUMULATE":      {"win_rate": 0.33, "avg_return": 0.15, "hold_period": 45, "confidence": 0.65},
    "BUY DIP":         {"win_rate": 0.19, "avg_return": 0.12, "hold_period": 45, "confidence": 0.55},
    "SPECULATIVE BUY": {"win_rate": 0.12, "avg_return": 0.25, "hold_period": 60, "confidence": 0.35},
    "WATCH":           {"win_rate": 0.10, "avg_return": 0.08, "hold_period": 30, "confidence": 0.30},
    "HOLD":            {"win_rate": 0.08, "avg_return": 0.05, "hold_period": 30, "confidence": 0.25},
    "REDUCE":          {"win_rate": 0.05, "avg_return": -0.05, "hold_period": 14, "confidence": 0.60},
    "TAKE PROFITS":    {"win_rate": 0.03, "avg_return": -0.10, "hold_period": 14, "confidence": 0.70},
    "SELL":            {"win_rate": 0.02, "avg_return": -0.15, "hold_period": 7,  "confidence": 0.75},
}

# Technical adjustments applied to base win rate
# Each key has a description of the condition, the adjustment value, and a display label
TECHNICAL_ADJUSTMENTS = {
    "ema_high": {
        "description": "EMA Score >= 70",
        "adjustment": 0.085,
        "label": "EMA Score 70+",
    },
    "rsi_overbought": {
        "description": "RSI > 70",
        "adjustment": -0.15,
        "label": "RSI Overbought",
    },
    "rsi_optimal": {
        "description": "RSI between 40 and 65",
        "adjustment": 0.05,
        "label": "RSI Optimal Zone",
    },
    "inst_strong": {
        "description": "Institutional Flow Score >= 65",
        "adjustment": 0.04,
        "label": "Strong Inst. Flow",
    },
    "score_high": {
        "description": "Overall Score >= 55",
        "adjustment": 0.04,
        "label": "Overall Score 55+",
    },
    "trend_bullish": {
        "description": "EMA Score >= 60",
        "adjustment": 0.03,
        "label": "Bullish Trend",
    },
    "trend_bearish": {
        "description": "EMA Score < 30",
        "adjustment": -0.08,
        "label": "Bearish Trend",
    },
    "squeeze_potential": {
        "description": "Bollinger Squeeze active",
        "adjustment": 0.03,
        "label": "Squeeze Setup",
    },
}

# 110-stock universe for backtesting — diverse sectors, sufficient volume
BACKTEST_UNIVERSE = [
    # Tech (20)
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "AMD", "INTC", "CRM", "ORCL",
    "ADBE", "NOW", "SNOW", "PLTR", "NET", "DDOG", "ZS", "CRWD", "PANW", "FTNT",
    # Finance (12)
    "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW", "AXP", "V", "MA", "PYPL",
    # Healthcare (10)
    "JNJ", "UNH", "PFE", "ABBV", "MRK", "LLY", "TMO", "ABT", "DHR", "BMY",
    # Energy (10)
    "XOM", "CVX", "COP", "SLB", "EOG", "OXY", "PSX", "VLO", "MPC", "HAL",
    # Defense / Industrial (10)
    "LMT", "RTX", "NOC", "GD", "BA", "CAT", "DE", "HON", "GE", "MMM",
    # Consumer (10)
    "WMT", "COST", "HD", "TGT", "LOW", "MCD", "SBUX", "NKE", "DIS", "NFLX",
    # Small / Mid Cap Growth (10)
    "ROKU", "SHOP", "SQ", "COIN", "HOOD", "SOFI", "AFRM", "UPST", "RBLX", "UNITY",
    # Biotech (10)
    "MRNA", "BNTX", "REGN", "VRTX", "GILD", "BIIB", "ILMN", "EXAS", "DXCM", "ISRG",
    # Infrastructure / Materials (10)
    "FCX", "NEM", "VALE", "RIO", "BHP", "CLF", "X", "NUE", "STLD", "AA",
    # Recent IPOs / High Volatility (10)
    "RIVN", "LCID", "TSLA", "NIO", "XPEV", "LI", "FSR", "ARVL", "GOEV", "WKHS",
]

# Backtest configuration defaults
BACKTEST_CONFIG = {
    "holding_period_days": 60,
    "target_percent": 10,     # +10% target
    "stop_percent": 15,       # -15% stop loss
    "min_overall_score": 15,
    "min_pre_breakout_score": 10,
    "min_bars_required": 50,  # Minimum historical bars needed
}
