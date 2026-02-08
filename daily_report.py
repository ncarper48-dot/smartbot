#!/usr/bin/env python3
"""
Daily P&L Report + Alerts
Prints daily summary and sends notifications.
"""
from datetime import datetime
from performance_tracker import get_daily_summary
from notify import notify_bot_status

def main():
    today = datetime.now().strftime('%Y-%m-%d')
    summary = get_daily_summary(today)

    if "message" in summary:
        msg = f"📊 Daily Report ({today}): {summary['message']}"
        print(msg)
        notify_bot_status("INFO", msg)
        return

    pnl = summary.get("pnl", 0.0)
    trades = summary.get("trades", 0)
    buys = summary.get("buys", 0)
    sells = summary.get("sells", 0)

    msg = (
        f"📊 Daily Report ({today}) | Trades: {trades} | Buys: {buys} | Sells: {sells} "
        f"| P&L: ${pnl:+.2f}"
    )
    print(msg)

    # Alert level
    if pnl > 0:
        notify_bot_status("SUCCESS", msg)
    elif pnl < 0:
        notify_bot_status("WARNING", msg)
    else:
        notify_bot_status("INFO", msg)

if __name__ == "__main__":
    main()