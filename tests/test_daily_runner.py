import tempfile
import os
import importlib
import json
from pathlib import Path

import demo_pipeline
import bot
import daily_runner


def test_daily_runner_creates_reports(monkeypatch, tmp_path):
    # Mock run_demo_strategy to return deterministic data
    monkeypatch.setattr(demo_pipeline, "run_demo_strategy", lambda ticker, short=10, long=30, period='6mo': {"pnl": 1.23, "trades": []})

    # Make sure reports dir points to tmp
    monkeypatch.setattr(daily_runner, "REPORT_DIR", str(tmp_path))

    results = daily_runner.run(["AAPL"])
    assert results

    reports = list(Path(tmp_path).glob("*.json"))
    assert reports
    with open(reports[0], 'r') as f:
        data = json.load(f)
        assert data[0]['ticker'] == 'AAPL'


def test_slack_post_skipped(monkeypatch, tmp_path):
    monkeypatch.setenv('SLACK_WEBHOOK', '')
    monkeypatch.setattr(daily_runner, "REPORT_DIR", str(tmp_path))
    monkeypatch.setattr(demo_pipeline, "run_demo_strategy", lambda ticker, short=10, long=30, period='6mo': {"pnl": 0.0, "trades": []})

    results = daily_runner.run(["MSFT"])
    assert results[0]['ticker'] == 'MSFT'
