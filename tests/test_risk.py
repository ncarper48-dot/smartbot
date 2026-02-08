import importlib
import os
import pytest

import risk


def test_compute_position_size():
    # Known inputs
    price = 100.0
    cash = 10000.0
    qty = risk.compute_position_size_by_risk(price, cash, risk_per_trade=0.01, stop_loss_pct=0.02)
    # Expected: (10000*0.01)/(100*0.02) = (100)/(2) = 50
    assert qty >= 49.9999 and qty <= 50.0


def test_daily_loss_guard(tmp_path, monkeypatch):
    # Set a small max daily loss and write state to tmp path
    monkeypatch.setenv("TRADING212_SKIP_DOTENV", "1")
    monkeypatch.setenv("TRADING212_MAX_DAILY_LOSS", "10")
    monkeypatch.setattr(risk, "STATE_FILE", str(tmp_path / "state.json"))

    # Initially allowed
    assert risk.check_daily_loss_allowed(10)
    # Add loss exceeding the cap
    risk.add_realized_loss(15)
    assert not risk.check_daily_loss_allowed(10)
    # Reset
    risk.reset_daily_loss()
    assert risk.check_daily_loss_allowed(10)
