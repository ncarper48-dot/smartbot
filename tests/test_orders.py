import importlib
import time
import pytest

import bot


def test_get_order_mock(monkeypatch):
    monkeypatch.setenv("TRADING212_USE_MOCK", "1")
    importlib.reload(bot)

    order = bot.get_order("MOCK-1")
    assert order["id"] == "MOCK-1"
    assert order["status"] == "filled"


def test_list_orders_mock(monkeypatch):
    monkeypatch.setenv("TRADING212_USE_MOCK", "1")
    importlib.reload(bot)

    res = bot.list_orders()
    assert isinstance(res, list)
    assert res[0]["id"] == "MOCK-1"


def test_wait_for_order_status_simulated(monkeypatch):
    # Simulate get_order changing status from pending -> filled
    states = [{"id": "ORD-1", "status": "pending"}, {"id": "ORD-1", "status": "filled"}]

    def fake_get_order(order_id):
        return states.pop(0)

    monkeypatch.setattr(bot, "get_order", fake_get_order)

    res = bot.wait_for_order_status("ORD-1", target_statuses=("filled",), timeout=5, poll_interval=0.01)
    assert res["status"] == "filled"


def test_place_market_order_demo_wait(monkeypatch):
    # Simulate wait_for_order_status being called and raising (fallback to returning demo order)
    monkeypatch.setattr(bot, "wait_for_order_status", lambda *a, **k: (_ for _ in ()).throw(TimeoutError()))

    res = bot.place_market_order("AAPL_US_EQ", 0.01, mode="demo", wait_for_fill=True, wait_timeout=1)
    assert res["status"] == "demo"