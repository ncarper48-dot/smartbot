#!/bin/bash
# Watchdog to restart bot if it crashes

while true; do
  if ! pgrep -f "auto_trader.py" > /dev/null; then
    echo "$(date): Bot crashed, restarting..." >> /home/tradebot/watchdog.log
    cd /home/tradebot
    nohup /home/tradebot/.venv/bin/python auto_trader.py > /dev/null 2>&1 &
  fi
  sleep 60
done
