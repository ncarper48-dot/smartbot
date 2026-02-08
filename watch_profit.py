#!/usr/bin/env python3
"""
Watch SmartBot positions and report profit opportunities
"""
import yfinance as yf
import json
import time
from datetime import datetime

def check_position():
    """Check AMC position for profit"""
    try:
        with open('open_positions.json') as f:
            positions = json.load(f)
        
        if not positions:
            print("📭 No open positions")
            return
        
        for ticker, pos in positions.items():
            # Get current price
            data = yf.Ticker(ticker)
            hist = data.history(period='1d')
            if hist.empty:
                continue
                
            current = hist['Close'].iloc[-1]
            entry = pos['entry_price']
            target = pos['profit_target']
            stop = pos['stop_loss']
            
            pnl = current - entry
            pnl_pct = (pnl / entry) * 100
            to_target = ((target - current) / current) * 100
            to_quick = 0.3 - pnl_pct  # 0.3% quick target
            
            status = "🟢 PROFIT" if pnl > 0 else "🔴 LOSS"
            urgency = ""
            
            if pnl_pct >= 0.3:
                urgency = "💰 READY TO SELL! (Quick profit hit)"
            elif pnl_pct >= 0:
                urgency = f"📈 Close: need +{to_quick:.2f}% more"
            else:
                urgency = f"📉 Need +{abs(pnl_pct):.2f}% to break even"
            
            print(f"\n{'='*60}")
            print(f"🎯 {ticker} Position Update - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}")
            print(f"Entry:   ${entry:.3f}")
            print(f"Current: ${current:.3f}")
            print(f"Target:  ${target:.3f} (normal)")
            print(f"Stop:    ${stop:.3f}")
            print(f"\nP&L: ${pnl:+.4f} ({pnl_pct:+.2f}%)")
            print(f"Status: {status}")
            print(f"{urgency}")
            print(f"{'='*60}\n")
            
    except FileNotFoundError:
        print("📭 No positions file found")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("👀 SmartBot Position Watcher")
    print("Monitoring for profit opportunities...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            check_position()
            time.sleep(30)  # Check every 30 seconds
    except KeyboardInterrupt:
        print("\n\n✅ Monitoring stopped")
