import os
import importlib
import json

import bot


def test_idempotency_generation(tmp_path, monkeypatch):
    # Use a temporary idempotency store path
    monkeypatch.setenv("TRADING212_SKIP_DOTENV", "1")
    monkeypatch.setenv("TRADING212_USE_MOCK", "1")
    idfile = tmp_path / ".idempotency.json"
    monkeypatch.setattr(bot, "IDEMPOTENCY_STORE", str(idfile))

    # generate a key and persist
    key = bot._ensure_client_order_id("AAPL_US_EQ", 0.01, persist=True)
    assert key
    store = json.loads(idfile.read_text())
    assert any(v["idempotency_key"] == key for v in store.values())


def test_idempotency_reuse(tmp_path, monkeypatch):
    monkeypatch.setenv("TRADING212_USE_MOCK", "1")
    idfile = tmp_path / ".idempotency.json"
    monkeypatch.setattr(bot, "IDEMPOTENCY_STORE", str(idfile))

    key1 = bot._ensure_client_order_id("AAPL_US_EQ", 0.01, persist=True)
    key2 = bot._ensure_client_order_id("AAPL_US_EQ", 0.01, persist=False)
    assert key1 == key2
