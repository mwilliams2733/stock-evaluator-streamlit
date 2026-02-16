"""Display helpers, color coding, and formatting utilities."""


def score_color(score: float) -> str:
    """Return a hex color for a given score (0-100)."""
    if score >= 75:
        return "#00c853"   # Strong green
    elif score >= 55:
        return "#4caf50"   # Green
    elif score >= 35:
        return "#ff9800"   # Orange
    else:
        return "#f44336"   # Red


def signal_color(signal: str) -> str:
    """Return a color for a signal string."""
    colors = {
        "Strong Accumulation": "#00c853",
        "Accumulating": "#4caf50",
        "Neutral": "#ff9800",
        "Distributing": "#f44336",
        "Strong Distribution": "#d32f2f",
    }
    return colors.get(signal, "#9e9e9e")


def confidence_color(confidence: str) -> str:
    """Return a color for a confidence level."""
    colors = {
        "Very High": "#00c853",
        "High": "#4caf50",
        "Medium": "#ff9800",
        "Low": "#f44336",
    }
    return colors.get(confidence, "#9e9e9e")


def moat_color(rating: str) -> str:
    """Return a color for a moat rating."""
    colors = {
        "Wide Moat": "#00c853",
        "Narrow Moat": "#ff9800",
        "No Moat": "#f44336",
    }
    return colors.get(rating, "#9e9e9e")


def format_large_number(n) -> str:
    """Format large numbers with K/M/B suffixes."""
    if n is None:
        return "N/A"
    try:
        n = float(n)
    except (ValueError, TypeError):
        return "N/A"
    if abs(n) >= 1e12:
        return f"${n / 1e12:.1f}T"
    if abs(n) >= 1e9:
        return f"${n / 1e9:.1f}B"
    if abs(n) >= 1e6:
        return f"${n / 1e6:.1f}M"
    if abs(n) >= 1e3:
        return f"${n / 1e3:.1f}K"
    return f"${n:,.0f}"


def format_pct(val, decimals: int = 2) -> str:
    """Format a percentage value."""
    if val is None:
        return "N/A"
    try:
        return f"{float(val):+.{decimals}f}%"
    except (ValueError, TypeError):
        return "N/A"


def format_price(val) -> str:
    """Format a dollar price."""
    if val is None:
        return "N/A"
    try:
        return f"${float(val):,.2f}"
    except (ValueError, TypeError):
        return "N/A"


def format_score(val) -> str:
    """Format a score value."""
    if val is None:
        return "N/A"
    try:
        return f"{int(round(float(val)))}"
    except (ValueError, TypeError):
        return "N/A"


def format_ratio(val, decimals: int = 2) -> str:
    """Format a ratio value (e.g. P/E, D/E)."""
    if val is None:
        return "N/A"
    try:
        return f"{float(val):.{decimals}f}"
    except (ValueError, TypeError):
        return "N/A"


def recommendation_color(action: str) -> str:
    """Return a hex color for a recommendation action."""
    from core.recommendations import ACTION_COLORS
    return ACTION_COLORS.get(action, "#8b949e")


def format_rs_rank(rank) -> str:
    """Format RS Rank for display with letter grade."""
    if rank is None:
        return "N/A"
    try:
        rank = int(rank)
    except (ValueError, TypeError):
        return "N/A"
    if rank >= 90:
        grade = "A+"
    elif rank >= 80:
        grade = "A"
    elif rank >= 70:
        grade = "B+"
    elif rank >= 60:
        grade = "B"
    elif rank >= 50:
        grade = "C+"
    elif rank >= 40:
        grade = "C"
    elif rank >= 30:
        grade = "D+"
    elif rank >= 20:
        grade = "D"
    else:
        grade = "F"
    return f"{rank} ({grade})"


def options_rating_color(rating: str) -> str:
    """Return color for options rating badge."""
    colors = {
        "Excellent": "#00c853",
        "Good": "#4caf50",
        "Fair": "#ff9800",
        "Poor": "#f44336",
    }
    return colors.get(rating, "#8b949e")


def format_win_probability(prob) -> str:
    """Format win probability for display."""
    if prob is None:
        return "N/A"
    try:
        return f"{float(prob) * 100:.0f}%"
    except (ValueError, TypeError):
        return "N/A"


def format_expected_return(ret) -> str:
    """Format expected return for display."""
    if ret is None:
        return "N/A"
    try:
        return f"{float(ret) * 100:+.1f}%"
    except (ValueError, TypeError):
        return "N/A"


def colored_metric(label: str, value: str, color: str) -> str:
    """Return HTML for a colored metric display."""
    return (
        f'<div style="text-align:center">'
        f'<span style="font-size:0.85em;color:#888">{label}</span><br>'
        f'<span style="font-size:1.4em;font-weight:bold;color:{color}">{value}</span>'
        f'</div>'
    )
