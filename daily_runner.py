#!/usr/bin/env python3
"""Daily demo runner for Trading212 demo strategy.

- Reads tickers from env var TRADING212_DAILY_TICKERS (comma-separated) or default list
- Runs demo_pipeline.run_demo_strategy for each ticker
- Writes a timestamped JSON and CSV report under `reports/` directory
- Optionally posts summary to Slack if SLACK_WEBHOOK is set
"""
import os
import json
import csv
from datetime import datetime
import logging
from typing import List

from demo_pipeline import run_demo_strategy

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

REPORT_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORT_DIR, exist_ok=True)

DEFAULT_TICKERS = os.getenv("TRADING212_DAILY_TICKERS", "AAPL,MSFT,GOOG").split(",")


def _run_for_ticker(ticker: str):
    try:
        logger.info("Running demo strategy for %s", ticker)
        r = run_demo_strategy(ticker.strip(), short=int(os.getenv("SMA_SHORT", 10)), long=int(os.getenv("SMA_LONG", 30)))
        return {"ticker": ticker, "error": None, "result": r}
    except Exception as e:
        logger.exception("Error running demo for %s", ticker)
        return {"ticker": ticker, "error": str(e), "result": None}


def _write_reports(results: List[dict]):
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    json_path = os.path.join(REPORT_DIR, f"report_{ts}.json")
    csv_path = os.path.join(REPORT_DIR, f"summary_{ts}.csv")

    with open(json_path, "w") as f:
        json.dump(results, f, default=str, indent=2)

    # write CSV summary with enhanced metrics
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ticker", "pnl", "return_%", "num_trades", "win_rate_%", "max_drawdown_%", "sharpe_ratio", "error"])
        for r in results:
            if r["result"]:
                pnl = r["result"].get("pnl", "")
                analytics = r["result"].get("analytics", {})
                num_trades = analytics.get("total_trades", 0)
                win_rate = analytics.get("win_rate", 0)
                max_dd = analytics.get("max_drawdown", 0)
                sharpe = analytics.get("sharpe_ratio", 0)
                ret_pct = analytics.get("return_pct", 0)
            else:
                pnl = ""
                num_trades = ""
                win_rate = ""
                max_dd = ""
                sharpe = ""
                ret_pct = ""
            writer.writerow([r["ticker"], pnl, ret_pct, num_trades, win_rate, max_dd, sharpe, r["error"]])

    return json_path, csv_path


def _post_to_slack(summary: str):
    webhook = os.getenv("SLACK_WEBHOOK")
    if not webhook:
        logger.debug("No SLACK_WEBHOOK configured, skipping post")
        return
    try:
        import requests
        payload = {"text": summary}
        requests.post(webhook, json=payload, timeout=10)
    except Exception:
        logger.exception("Failed to post to Slack")


def run(tickers: List[str] = None):
    tickers = tickers or DEFAULT_TICKERS
    
    # Check daily profit target
    profit_target = float(os.getenv("TRADING212_DAILY_PROFIT_TARGET", "250"))
    tracker_file = os.path.join(os.path.dirname(__file__), "daily_tracker.json")
    
    # Load or initialize daily tracker
    today = datetime.utcnow().date().isoformat()
    try:
        with open(tracker_file, "r") as f:
            tracker = json.load(f)
            # Reset if new day
            if tracker.get("date") != today:
                tracker = {"date": today, "daily_pnl_gbp": 0.0, "trades_today": 0, "target_hit": False}
    except:
        tracker = {"date": today, "daily_pnl_gbp": 0.0, "trades_today": 0, "target_hit": False}
    
    # Check if target already hit today
    if tracker.get("target_hit", False):
        print(f"\n🎯 £{profit_target:.2f} TARGET ALREADY HIT TODAY! Taking a break until tomorrow.\n")
        logger.info(f"Daily target of £{profit_target:.2f} already achieved. Skipping run.")
        return []
    
    results = []
    for t in tickers:
        results.append(_run_for_ticker(t))

    json_path, csv_path = _write_reports(results)

    # Enhanced summary with analytics
    summary_lines = [
        "\n" + "="*70,
        f"📊 TRADING BOT PERFORMANCE REPORT - {datetime.utcnow().isoformat()} UTC",
        "="*70,
        f"📁 Reports: JSON: {json_path} | CSV: {csv_path}\n"
    ]
    
    total_pnl = 0
    total_trades = 0
    
    for r in results:
        if r["result"]:
            ticker = r["ticker"]
            pnl = r["result"].get("pnl", 0)
            analytics = r["result"].get("analytics", {})
            trades = analytics.get("total_trades", 0)
            wins = analytics.get("wins", 0)
            win_rate = analytics.get("win_rate", 0)
            max_dd = analytics.get("max_drawdown", 0)
            sharpe = analytics.get("sharpe_ratio", 0)
            ret_pct = analytics.get("return_pct", 0)
            
            total_pnl += pnl
            total_trades += trades
            
            status = "✅ PROFIT" if pnl >= 0 else "❌ LOSS"
            summary_lines.append(
                f"{status} {ticker:6} | PnL: ${pnl:8.2f} ({ret_pct:+6.2f}%) | "
                f"Trades: {trades:2} | Win%: {win_rate:5.1f}% | DD: {max_dd:5.1f}% | Sharpe: {sharpe:6.2f}"
            )
        else:
            summary_lines.append(f"❌ {r['ticker']:6} | ERROR: {r['error']}")
    
    # Convert USD to GBP (approximate rate)
    gbp_rate = 0.79
    total_pnl_gbp = total_pnl * gbp_rate
    
    # Update daily tracker
    tracker["daily_pnl_gbp"] += total_pnl_gbp
    tracker["trades_today"] += total_trades
    
    # Check if target hit
    if tracker["daily_pnl_gbp"] >= profit_target:
        tracker["target_hit"] = True
        target_status = f"🎯🎉 TARGET HIT! £{tracker['daily_pnl_gbp']:.2f} / £{profit_target:.2f} - STOPPING FOR THE DAY!"
    else:
        remaining = profit_target - tracker["daily_pnl_gbp"]
        target_status = f"📈 Progress: £{tracker['daily_pnl_gbp']:.2f} / £{profit_target:.2f} (£{remaining:.2f} to go)"
    
    # Save tracker
    with open(tracker_file, "w") as f:
        json.dump(tracker, f, indent=2)
    
    summary_lines.extend([
        "-"*70,
        f"🎯 SESSION | PnL: ${total_pnl:8.2f} (£{total_pnl_gbp:.2f}) | Trades: {total_trades}",
        f"📊 TODAY TOTAL | £{tracker['daily_pnl_gbp']:.2f} | {tracker['trades_today']} trades",
        f"💰 {target_status}",
        "="*70 + "\n"
    ])

    summary = "\n".join(summary_lines)
    print(summary)
    logger.info(summary)
    _post_to_slack(summary)
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Daily demo runner")
    parser.add_argument("--tickers", help="Comma separated tickers to run", default=None)
    args = parser.parse_args()
    if args.tickers:
        tickers = args.tickers.split(",")
    else:
        tickers = None
    run(tickers)
