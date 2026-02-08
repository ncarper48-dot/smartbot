#!/bin/bash
# Continuously update professional terminal dashboard
while true; do
    /home/tradebot/.venv/bin/python /home/tradebot/generate_pro_terminal.py
    sleep 10  # Update every 10 seconds
done
