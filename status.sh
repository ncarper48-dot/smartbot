#!/bin/bash
# Quick status dashboard for tradebot

echo "════════════════════════════════════════════════════════════"
echo "🤖 TRADEBOT STATUS - $(date '+%Y-%m-%d %H:%M:%S')"
echo "════════════════════════════════════════════════════════════"

# Bot status
if ps aux | grep -q "[a]uto_trader.py"; then
    PID=$(ps aux | grep "[a]uto_trader.py" | awk '{print $2}')
    UPTIME=$(ps -p $PID -o etime= | tr -d ' ')
    echo "✅ Bot Running (PID: $PID, Uptime: $UPTIME)"
else
    echo "❌ Bot NOT Running"
fi

# Account status
echo ""
echo "💰 ACCOUNT STATUS:"
python3 /home/tradebot/bot.py --cash 2>/dev/null | grep -E "free|total|invested" | head -1

# Today's tracker
echo ""
echo "📊 TODAY'S PROGRESS:"
if [ -f /home/tradebot/daily_tracker.json ]; then
    python3 -c "
import json
with open('/home/tradebot/daily_tracker.json') as f:
    d = json.load(f)
    print(f\"P&L: £{d.get('daily_pnl_gbp', 0):.2f} | Trades: {d.get('trades_today', 0)} | Target Hit: {d.get('target_hit', False)}\")
"
fi

# Performance stats
echo ""
python3 /home/tradebot/performance_tracker.py --stats 2>/dev/null | head -8

# Recent activity
echo ""
echo "📝 RECENT ACTIVITY (last 5 lines):"
tail -5 /home/tradebot/auto_trader.log 2>/dev/null | sed 's/^/   /'

echo "════════════════════════════════════════════════════════════"
echo "Commands: tail -f auto_trader.log | python3 performance_tracker.py --stats"
echo "════════════════════════════════════════════════════════════"
