#!/bin/bash
# Quick status check for phone - generates simple text file

STATUS_FILE="/home/tradebot/smartbot_status.txt"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" > "$STATUS_FILE"
echo "   SMARTBOT TRADING - QUICK STATUS" >> "$STATUS_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$STATUS_FILE"
echo "" >> "$STATUS_FILE"
echo "📅 $(date '+%A, %B %d, %Y at %I:%M %p')" >> "$STATUS_FILE"
echo "" >> "$STATUS_FILE"

# Bot status
if pgrep -f "auto_trader.py" > /dev/null; then
    echo "✅ BOT: RUNNING" >> "$STATUS_FILE"
else
    echo "❌ BOT: STOPPED" >> "$STATUS_FILE"
fi

if pgrep -f "watchdog.sh" > /dev/null; then
    echo "✅ WATCHDOG: ACTIVE" >> "$STATUS_FILE"
else
    echo "⚠️  WATCHDOG: INACTIVE" >> "$STATUS_FILE"
fi

echo "" >> "$STATUS_FILE"

# Account info
if [ -f "/home/tradebot/open_positions.json" ]; then
    POSITIONS=$(python3 -c "import json; f=open('/home/tradebot/open_positions.json'); print(len(json.load(f)))" 2>/dev/null || echo "?")
    echo "📊 OPEN POSITIONS: $POSITIONS" >> "$STATUS_FILE"
else
    echo "📊 OPEN POSITIONS: ?" >> "$STATUS_FILE"
fi

# Daily P&L
if [ -f "/home/tradebot/risk_state.json" ]; then
    DAILY_PNL=$(python3 -c "import json; f=open('/home/tradebot/risk_state.json'); data=json.load(f); print(f\"{data.get('daily_pnl', 0):.2f}\")" 2>/dev/null || echo "0.00")
    echo "💰 DAILY P&L: \$$DAILY_PNL" >> "$STATUS_FILE"
else
    echo "💰 DAILY P&L: \$0.00" >> "$STATUS_FILE"
fi

echo "" >> "$STATUS_FILE"
echo "⚙️  CONFIGURATION:" >> "$STATUS_FILE"
echo "   • Confidence: 40%" >> "$STATUS_FILE"
echo "   • Active Stocks: 15" >> "$STATUS_FILE"
echo "   • Strategies: 4 Aggressive" >> "$STATUS_FILE"
echo "   • Daily Target: £250" >> "$STATUS_FILE"
echo "" >> "$STATUS_FILE"

# Recent activity check
if [ -f "/home/tradebot/auto_trader.log" ]; then
    LAST_RUN=$(tail -5 /home/tradebot/auto_trader.log | grep "INFO" | tail -1 || echo "No recent activity")
    echo "🕐 LAST ACTIVITY:" >> "$STATUS_FILE"
    echo "   $LAST_RUN" >> "$STATUS_FILE"
else
    echo "🕐 LAST ACTIVITY: No log found" >> "$STATUS_FILE"
fi

echo "" >> "$STATUS_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$STATUS_FILE"
echo "Next market open: Tuesday Jan 21, 9:30 AM ET" >> "$STATUS_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$STATUS_FILE"

echo "✅ Status saved to: $STATUS_FILE"
echo "📱 Copy this file to Google Drive to view on phone"
