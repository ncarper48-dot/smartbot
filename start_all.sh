#!/bin/bash
# Master startup script - launches bot + watchdog + dashboard updater

echo "🚀 Starting Complete Trading System..."

# Kill any existing processes
pkill -f auto_trader.py 2>/dev/null
pkill -f watchdog.sh 2>/dev/null
pkill -f update_dashboard.sh 2>/dev/null
sleep 2

# Start the trading bot (venv for AI)
echo "Starting trading bot..."
nohup /home/tradebot/.venv/bin/python /home/tradebot/auto_trader.py >> /home/tradebot/auto_trader.log 2>&1 &
BOT_PID=$!
echo "✅ Bot started (PID: $BOT_PID)"

# Start the watchdog
echo "Starting watchdog monitor..."
nohup bash /home/tradebot/watchdog.sh >> /home/tradebot/watchdog.log 2>&1 &
WATCH_PID=$!
echo "✅ Watchdog started (PID: $WATCH_PID)"

# Start dashboard updater if it exists
if [ -f /home/tradebot/update_dashboard.sh ]; then
    echo "Starting dashboard updater..."
    nohup bash /home/tradebot/update_dashboard.sh >> /dev/null 2>&1 &
    echo "✅ Dashboard updater started"
fi

# Run daily report once at startup
if [ -f /home/tradebot/daily_report.py ]; then
    echo "Running daily report..."
    nohup /home/tradebot/.venv/bin/python /home/tradebot/daily_report.py >> /home/tradebot/notifications.log 2>&1 &
    echo "✅ Daily report queued"
fi

echo ""
echo "================================================"
echo "✅ ALL SYSTEMS OPERATIONAL"
echo "================================================"
echo "Bot PID: $BOT_PID"
echo "Watchdog PID: $WATCH_PID"
echo ""
echo "Your bot is now protected by automatic restart!"
echo "Check status: ps -ef | grep -E 'auto_trader|watchdog'"
echo "View watchdog log: tail -f /home/tradebot/watchdog.log"
echo "================================================"
