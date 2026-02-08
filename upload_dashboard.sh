#!/bin/bash
# Simple script to open dashboard in Chrome for remote access

echo "Opening SmartBot Trading Dashboard in Chrome..."
echo "You can now:"
echo "  1. View it on this Chromebook"
echo "  2. Use Chrome Remote Desktop on your phone to access this screen"
echo ""
echo "Or copy /home/tradebot/status_dashboard.html to Dropbox/Google Drive"
echo "and open it on your phone directly"

# Try to open in browser
xdg-open file:///home/tradebot/status_dashboard.html 2>/dev/null || \
  echo "file:///home/tradebot/status_dashboard.html"
