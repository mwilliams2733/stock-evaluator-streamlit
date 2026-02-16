"""File-based JSON persistence for user data — replaces localStorage from the HTML app."""
import json
import os
import datetime as dt
from pathlib import Path
from copy import deepcopy

from config.portfolios import PREDEFINED_PORTFOLIOS, DEFAULT_CUSTOM_PORTFOLIOS

# Persistence directory — relative to project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
PERSISTENCE_DIR = _PROJECT_ROOT / "data" / "user"


def _ensure_dir():
    """Create persistence directory if it doesn't exist."""
    PERSISTENCE_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(filename: str) -> dict | list:
    """Read a JSON file from the persistence directory."""
    filepath = PERSISTENCE_DIR / filename
    if not filepath.exists():
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _write_json(filename: str, data):
    """Write data to a JSON file in the persistence directory."""
    _ensure_dir()
    filepath = PERSISTENCE_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


# ─── Portfolios ───────────────────────────────────────────────────────────────

def load_portfolios() -> dict:
    """Load all portfolios (predefined + custom).

    Returns a dict keyed by portfolio ID.
    Predefined portfolios are always included with latest symbol lists.
    Custom portfolios are loaded from persistence.
    """
    saved = _read_json("portfolios.json")

    # Always include latest predefined portfolios
    portfolios = deepcopy(PREDEFINED_PORTFOLIOS)

    # Merge saved holdings data into predefined portfolios
    for pid, pdata in portfolios.items():
        if pid in saved and "holdings" in saved[pid]:
            pdata["holdings"] = saved[pid]["holdings"]

    # Add custom portfolios from saved data
    for pid, pdata in saved.items():
        if pid not in portfolios:
            portfolios[pid] = pdata

    # Add default custom portfolios if they don't exist
    for pid, pdata in DEFAULT_CUSTOM_PORTFOLIOS.items():
        if pid not in portfolios:
            portfolios[pid] = deepcopy(pdata)

    return portfolios


def save_portfolios(portfolios: dict):
    """Save all portfolios to disk."""
    _write_json("portfolios.json", portfolios)


def add_stock_to_portfolio(portfolio_id: str, ticker: str,
                           shares: float = 0, cost_basis: float = 0):
    """Add a stock to a portfolio."""
    portfolios = load_portfolios()
    if portfolio_id not in portfolios:
        return False

    portfolio = portfolios[portfolio_id]

    # Add to symbols list if not already there
    if ticker not in portfolio.get("symbols", []):
        portfolio.setdefault("symbols", []).append(ticker)

    # Add holdings info
    portfolio.setdefault("holdings", {})[ticker] = {
        "shares": shares,
        "cost_basis": cost_basis,
        "date_added": dt.date.today().isoformat(),
    }

    save_portfolios(portfolios)
    return True


def remove_stock_from_portfolio(portfolio_id: str, ticker: str):
    """Remove a stock from a portfolio."""
    portfolios = load_portfolios()
    if portfolio_id not in portfolios:
        return False

    portfolio = portfolios[portfolio_id]

    if ticker in portfolio.get("symbols", []):
        portfolio["symbols"].remove(ticker)
    if ticker in portfolio.get("holdings", {}):
        del portfolio["holdings"][ticker]

    save_portfolios(portfolios)
    return True


def create_custom_portfolio(portfolio_id: str, name: str, description: str = ""):
    """Create a new custom portfolio."""
    portfolios = load_portfolios()
    if portfolio_id in portfolios:
        return False  # Already exists

    portfolios[portfolio_id] = {
        "id": portfolio_id,
        "name": name,
        "description": description,
        "symbols": [],
        "holdings": {},
        "created": dt.datetime.now().isoformat(),
    }
    save_portfolios(portfolios)
    return True


def delete_custom_portfolio(portfolio_id: str):
    """Delete a custom portfolio (cannot delete predefined ones)."""
    if portfolio_id in PREDEFINED_PORTFOLIOS:
        return False
    portfolios = load_portfolios()
    if portfolio_id in portfolios:
        del portfolios[portfolio_id]
        save_portfolios(portfolios)
        return True
    return False


# ─── Alerts ───────────────────────────────────────────────────────────────────

def load_alerts() -> list:
    """Load price/fair-value alerts."""
    data = _read_json("alerts.json")
    return data.get("alerts", []) if isinstance(data, dict) else data if isinstance(data, list) else []


def save_alerts(alerts: list):
    """Save alerts to disk."""
    _write_json("alerts.json", {"alerts": alerts})


def add_alert(ticker: str, target_price: float, direction: str = "below",
              alert_type: str = "price") -> dict:
    """Add a new alert and save.

    Args:
        ticker: Stock symbol.
        target_price: Target price for alert.
        direction: 'below' or 'above'.
        alert_type: 'price' or 'fair_value'.
    """
    alerts = load_alerts()
    alert = {
        "id": f"{ticker}-{target_price}-{len(alerts)}",
        "ticker": ticker,
        "target_price": target_price,
        "direction": direction,
        "alert_type": alert_type,
        "active": True,
        "triggered": False,
        "created": dt.datetime.now().isoformat(),
        "triggered_at": None,
    }
    alerts.append(alert)
    save_alerts(alerts)
    return alert


def remove_alert(alert_id: str):
    """Remove an alert by ID."""
    alerts = load_alerts()
    alerts = [a for a in alerts if a.get("id") != alert_id]
    save_alerts(alerts)


def trigger_alert(alert_id: str):
    """Mark an alert as triggered."""
    alerts = load_alerts()
    for alert in alerts:
        if alert.get("id") == alert_id:
            alert["triggered"] = True
            alert["active"] = False
            alert["triggered_at"] = dt.datetime.now().isoformat()
            break
    save_alerts(alerts)


# ─── Trade History (for Learning Engine) ──────────────────────────────────────

def load_trade_history() -> list:
    """Load trade history for learning engine."""
    data = _read_json("trade_history.json")
    return data.get("trades", []) if isinstance(data, dict) else data if isinstance(data, list) else []


def save_trade_history(trades: list):
    """Save trade history to disk."""
    _write_json("trade_history.json", {"trades": trades})


# ─── User Settings ────────────────────────────────────────────────────────────

def load_user_settings() -> dict:
    """Load persisted user settings."""
    return _read_json("user_settings.json") or {}


def save_user_settings(settings: dict):
    """Save user settings to disk."""
    _write_json("user_settings.json", settings)


# ─── Import / Export ──────────────────────────────────────────────────────────

def export_portfolio_json(portfolio_id: str) -> str:
    """Export a single portfolio as a JSON string."""
    portfolios = load_portfolios()
    if portfolio_id not in portfolios:
        return "{}"
    return json.dumps(portfolios[portfolio_id], indent=2, default=str)


def import_portfolio_json(json_str: str) -> dict | None:
    """Import a portfolio from a JSON string.

    Returns the portfolio dict if valid, None otherwise.
    """
    try:
        data = json.loads(json_str)
        if not isinstance(data, dict):
            return None
        # Validate required fields
        if "symbols" not in data or not isinstance(data["symbols"], list):
            return None
        # Ensure ID exists
        if "id" not in data:
            data["id"] = f"imported-{dt.datetime.now().strftime('%Y%m%d%H%M%S')}"
        if "name" not in data:
            data["name"] = f"Imported Portfolio"

        # Save it
        portfolios = load_portfolios()
        portfolios[data["id"]] = data
        save_portfolios(portfolios)
        return data
    except (json.JSONDecodeError, TypeError):
        return None
