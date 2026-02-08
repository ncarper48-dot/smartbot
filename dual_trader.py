#!/usr/bin/env python3
"""
Dual-Mode Trading Bot: Runs DEMO + LIVE accounts simultaneously
Demo: Aggressive testing ($5,028)
Live: Conservative proof (£3.81 real money)
"""
import os
import time
import subprocess
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Check both accounts are running
RUN_INTERVAL = 180  # 3 minutes

def log(msg, account="SYSTEM"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = "🎯" if account == "DEMO" else "💰" if account == "LIVE" else "⚙️"
    print(f"{prefix} [{timestamp}] [{account}] {msg}")
    sys.stdout.flush()

def run_demo_scan():
    """Run demo account scan (aggressive 40% confidence)"""
    try:
        log("Running demo scan...", "DEMO")
        # Run existing auto_trader which uses demo credentials
        result = subprocess.run(
            ['python3', '/home/tradebot/live_trader.py'],
            env={**os.environ, 'TRADING_MODE': 'DEMO'},
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            log(f"Demo scan complete", "DEMO")
        else:
            log(f"Demo scan error: {result.stderr[:200]}", "DEMO")
            
    except Exception as e:
        log(f"Demo exception: {e}", "DEMO")

def run_live_scan():
    """Run live account scan (conservative 50% confidence)"""
    try:
        log("Running LIVE scan (real money)...", "LIVE")
        
        # Run live_trader with LIVE credentials
        result = subprocess.run(
            ['python3', '/home/tradebot/live_trader.py'],
            env={
                **os.environ,
                'TRADING_MODE': 'LIVE',
                'TRADING212_API_KEY': os.getenv('TRADING212_LIVE_API_KEY'),
                'TRADING212_API_SECRET': os.getenv('TRADING212_LIVE_API_SECRET'),
                'TRADING212_BASE_URL': os.getenv('TRADING212_LIVE_BASE_URL'),
                'TRADING212_RISK_PER_TRADE': str(os.getenv('TRADING212_LIVE_RISK_PER_TRADE', '0.20')),
                'TRADING212_MAX_POSITIONS': str(os.getenv('TRADING212_LIVE_MAX_POSITIONS', '3')),
                'TRADING212_MAX_DAILY_LOSS_PCT': str(os.getenv('TRADING212_LIVE_MAX_DAILY_LOSS_PCT', '0.10')),
            },
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            log(f"LIVE scan complete", "LIVE")
        else:
            log(f"LIVE scan error: {result.stderr[:200]}", "LIVE")
            
    except Exception as e:
        log(f"LIVE exception: {e}", "LIVE")

def main():
    log("=" * 70)
    log("DUAL-MODE TRADING BOT STARTED")
    log("=" * 70)
    log(f"Demo: $5,028 | Aggressive (40% confidence)")
    log(f"Live: £3.81 | Conservative (50% confidence)")
    log(f"Scan interval: {RUN_INTERVAL}s (3 min)")
    log("=" * 70)
    
    cycle = 0
    
    while True:
        try:
            cycle += 1
            log(f"Cycle #{cycle} starting...")
            
            # Run demo first
            run_demo_scan()
            time.sleep(10)  # 10 second gap between accounts
            
            # Run live
            run_live_scan()
            
            log(f"Cycle #{cycle} complete. Next scan in {RUN_INTERVAL}s")
            log("-" * 70)
            
            # Wait for next interval
            time.sleep(RUN_INTERVAL)
            
        except KeyboardInterrupt:
            log("Shutdown requested")
            break
        except Exception as e:
            log(f"Error in main loop: {e}")
            time.sleep(60)  # Wait 1 min on error

if __name__ == '__main__':
    main()
