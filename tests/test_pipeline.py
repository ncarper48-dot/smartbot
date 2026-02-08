import pandas as pd
import numpy as np
import importlib
import bot
import demo_pipeline


def make_price_series(n=50, base=100.0):
    rng = pd.date_range(end=pd.Timestamp.today(), periods=n, freq='D')
    prices = base + np.cumsum(np.random.randn(n))
    return pd.DataFrame({"Close": prices}, index=rng)


def test_sma_signal_and_backtest(monkeypatch):
    # Replace fetch_history to return deterministic data
    df = make_price_series(100)
    monkeypatch.setattr(demo_pipeline, "fetch_history", lambda ticker, period='6mo', interval='1d': df)

    sig = demo_pipeline.sma_signals(df, short=5, long=20)
    pnl, trades = demo_pipeline.backtest_signals(sig)
    assert isinstance(pnl, float)
    assert isinstance(trades, list)


def test_run_demo_strategy(monkeypatch):
    # Use mock for place_market_order to avoid external calls
    monkeypatch.setattr(bot, "place_market_order", lambda ticker, qty, **k: {"status": "demo", "order": {"ticker": ticker, "quantity": qty}})

    monkeypatch.setattr(demo_pipeline, "fetch_history", lambda ticker, period='6mo', interval='1d': make_price_series(60))

    report = demo_pipeline.run_demo_strategy("AAPL", short=5, long=20)
    assert "pnl" in report
    assert "demo_results" in report
