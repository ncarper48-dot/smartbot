#!/usr/bin/env python3
"""
LIVE ISA TRADER - Real Money Trading (Conservative Mode)
Runs alongside demo account with safer settings
"""
import os
import time
import sys
from dotenv import load_dotenv

load_dotenv()

# Override with LIVE account settings BEFORE importing auto_trader
os.environ['TRADING212_API_KEY'] = os.getenv('TRADING212_LIVE_API_KEY')
os.environ['TRADING212_API_SECRET'] = os.getenv('TRADING212_LIVE_API_SECRET')
os.environ['TRADING212_BASE_URL'] = os.getenv('TRADING212_LIVE_BASE_URL')
os.environ['TRADING212_RISK_PER_TRADE'] = os.getenv('TRADING212_LIVE_RISK_PER_TRADE', '0.20')
os.environ['TRADING212_MAX_POSITIONS'] = os.getenv('TRADING212_LIVE_MAX_POSITIONS', '3')
os.environ['CONFIDENCE_THRESHOLD'] = os.getenv('TRADING212_LIVE_CONFIDENCE_THRESHOLD', '0.50')
os.environ['TRADING212_MODE'] = 'live_isa'
os.environ['LIVE_ACCOUNT'] = 'true'

# Import the main trading logic AFTER setting env vars
from auto_trader import main as run_trading_cycle

print("=" * 60)
print("🔴 LIVE ISA TRADER - REAL MONEY MODE")
print("=" * 60)
print(f"⚠️  CONSERVATIVE SETTINGS:")
print(f"   Risk per trade: {os.getenv('TRADING212_LIVE_RISK_PER_TRADE', '0.20')}%")
print(f"   Max positions: {os.getenv('TRADING212_LIVE_MAX_POSITIONS', '3')}")
print(f"   Min confidence: {os.getenv('TRADING212_LIVE_CONFIDENCE_THRESHOLD', '0.50')}%")
print(f"   Daily loss limit: {os.getenv('TRADING212_LIVE_MAX_DAILY_LOSS_PCT', '0.10')}%")
print("=" * 60)
print()

if __name__ == '__main__':
    while True:
        try:
            run_trading_cycle()
            time.sleep(120)  # 2 minute intervals (same as demo)
        except KeyboardInterrupt:
            print("\n🛑 Live ISA trader stopped by user")
            break
        except Exception as e:
            print(f"❌ Error in live ISA trader: {e}")
            time.sleep(60)
            continue
