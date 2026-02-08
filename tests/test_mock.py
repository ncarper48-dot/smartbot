import importlib


def test_mock_get_account_cash(monkeypatch):
    monkeypatch.setenv("TRADING212_USE_MOCK", "1")
    import bot
    importlib.reload(bot)

    res = bot.get_account_cash()
    assert isinstance(res, dict)
    assert res.get("cash", {}).get("available") == 10000.0


def test_mock_place_order(monkeypatch):
    monkeypatch.setenv("TRADING212_USE_MOCK", "true")
    import bot
    importlib.reload(bot)

    res = bot.place_market_order("AAPL_US_EQ", 1.0)
    assert res.get("status") == "ok"
    assert res.get("order", {}).get("ticker") == "AAPL_US_EQ"
