import importlib
import os

import pytest

import bot


def test_order_limit():
    # Quantity above MAX_ORDER_QUANTITY should raise
    too_big = bot.MAX_ORDER_QUANTITY + 1
    with pytest.raises(ValueError):
        bot.place_market_order("AAPL_US_EQ", too_big, mode="mock")


def test_live_requires_confirm(monkeypatch):
    monkeypatch.delenv("TRADING212_USE_MOCK", raising=False)
    # Ensure we're not in auto-confirm
    monkeypatch.delenv("TRADING212_AUTO_CONFIRM", raising=False)

    with pytest.raises(RuntimeError):
        bot.place_market_order("AAPL_US_EQ", 1.0, mode="live", confirm=False)


def test_demo_order_not_placed():
    res = bot.place_market_order("AAPL_US_EQ", 1.0, mode="demo", confirm=False)
    assert res.get("status") == "demo"


def test_mock_order(monkeypatch):
    monkeypatch.setenv("TRADING212_USE_MOCK", "1")
    importlib.reload(bot)
    res = bot.place_market_order("AAPL_US_EQ", 1.0)
    assert res.get("status") == "ok"