import os
import importlib
import pytest

# Importing functions from bot.py
import bot

def test_get_headers_with_env(monkeypatch):
    monkeypatch.setenv("TRADING212_SKIP_DOTENV", "1")
    monkeypatch.setenv("TRADING212_API_KEY", "k")
    monkeypatch.setenv("TRADING212_API_SECRET", "s")
    # Reload module to pick up monkeypatched env vars
    importlib.reload(bot)

    headers = bot.get_headers()
    assert "Authorization" in headers
    assert headers["Content-Type"] == "application/json"


def test_get_headers_missing_env(monkeypatch):
    # Ensure env vars absent and prevent loading .env
    monkeypatch.setenv("TRADING212_SKIP_DOTENV", "1")
    monkeypatch.delenv("TRADING212_API_KEY", raising=False)
    monkeypatch.delenv("TRADING212_API_SECRET", raising=False)
    importlib.reload(bot)

    with pytest.raises(RuntimeError):
        bot.get_headers()
