"""Risk utilities: position sizing, price lookup, and simple daily loss guard."""
import os
import time
import json
import math
import logging
from typing import Optional

import yfinance as yf

logger = logging.getLogger(__name__)

STATE_FILE = os.path.join(os.path.dirname(__file__), "trading_state.json")


def get_cash_balance() -> float:
    # Attempt to read from environment (for demo) or fallback to 10000
    try:
        return float(os.getenv("TRADING212_ACCOUNT_CASH", "10000"))
    except Exception:
        return 10000.0


def get_price(ticker: str) -> float:
    """Get the latest market price for a ticker using yfinance."""
    t = yf.Ticker(ticker.replace("_DEMO", ""))
    df = t.history(period="1d", interval="1d")
    if df.empty:
        raise RuntimeError(f"Price lookup failed for {ticker}")
    return float(df.iloc[-1]["Close"])


def compute_position_size_by_risk(price: float, cash: Optional[float] = None, risk_per_trade: float = 0.01, stop_loss_pct: float = 0.02) -> float:
    """Compute quantity so that risk per trade is risk_per_trade * cash, given stop loss percent.

    quantity = (cash * risk_per_trade) / (price * stop_loss_pct)
    Allows fractional quantities; returns rounded down to 4 decimals for safety.
    """
    if cash is None:
        cash = get_cash_balance()
    if price <= 0 or stop_loss_pct <= 0:
        raise ValueError("Invalid price or stop_loss_pct")
    qty = (cash * float(risk_per_trade)) / (price * float(stop_loss_pct))
    # Round down to 4 decimal places
    qty = math.floor(qty * 10000) / 10000.0
    return float(qty)


def _load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"daily_loss": 0.0, "last_reset": time.time()}


def _save_state(st):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(st, f)
    except Exception as e:
        logger.warning("Failed to save trading state: %s", e)


def add_realized_loss(amt: float):
    st = _load_state()
    st.setdefault("daily_loss", 0.0)
    st["daily_loss"] += float(amt)
    _save_state(st)


def get_daily_loss() -> float:
    st = _load_state()
    return float(st.get("daily_loss", 0.0))


def reset_daily_loss():
    st = _load_state()
    st["daily_loss"] = 0.0
    st["last_reset"] = time.time()
    _save_state(st)


def check_daily_loss_allowed(max_daily_loss: Optional[float]) -> bool:
    """Return True if new orders are allowed (daily loss below threshold)."""
    if max_daily_loss is None:
        return True
    try:
        max_daily_loss = float(max_daily_loss)
    except Exception:
        return True
    return get_daily_loss() < max_daily_loss
