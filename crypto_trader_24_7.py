#!/usr/bin/env python3
"""
24/7 CRYPTO TRADER (DISABLED) - Stocks-only mode
"""
raise SystemExit("Crypto trading disabled: stocks-only mode")
import os
import time
import json
import subprocess
from datetime import datetime
import pytz
from coinbase_bot import get_accounts, get_crypto_price, place_market_order
from dotenv import load_dotenv

load_dotenv()

# Configuration - SCALPING MODE
CRYPTO_PAIRS = ['BTC-USD', 'ETH-USD', 'SOL-USD']
SCAN_INTERVAL = 60  # 1 minute - RAPID FIRE SCALPING
RISK_PER_TRADE = 0.25  # 25% of crypto portfolio per trade - AGGRESSIVE
MIN_CONFIDENCE = 0.20  # 20% confidence - MORE TRADES
QUICK_PROFIT_TARGET = 0.012  # Take 1.2% profit and exit - SCALPING
TRAILING_STOP = 0.006  # 0.6% trailing stop

def is_stock_market_open():
    """Check if US stock market is currently open."""
    try:
        et = pytz.timezone('America/New_York')
        now_et = datetime.now(et)
        
        # Weekend check
        if now_et.weekday() >= 5:
            return False
        
        # Market hours: 9:30 AM - 4:00 PM ET
        market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now_et <= market_close
    except:
        return False

def analyze_crypto_signal(symbol, price_history):
    """
    Simple momentum strategy for crypto.
    Returns: action ('buy'/'sell'/'hold'), confidence (0-1)
    """
    try:
        # Get current price
        current = get_crypto_price(symbol)
        if not current:
            return 'hold', 0
        
        # Simple momentum: if price moving up fast, buy
        # This is placeholder - you'd add real TA here
        
        # For now, just return hold (we'll enhance this)
        return 'hold', 0.5
        
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return 'hold', 0

def execute_crypto_strategy():
    """Execute trading strategy for crypto."""
    try:
        print(f"\n{'='*60}")
        print(f"🪙 CRYPTO SCAN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        # Get account balance
        accounts = get_accounts()
        if not accounts:
            print("❌ Could not fetch Coinbase accounts")
            return
        
        total_value = accounts.get('total_value_usd', 0)
        print(f"💰 Crypto Portfolio: ${total_value:.2f}")
        
        # Scan each crypto pair
        for pair in CRYPTO_PAIRS:
            print(f"\n🔍 Analyzing {pair}...")
            
            price = get_crypto_price(pair)
            if price:
                print(f"   Current Price: ${price:.2f}")
            
            # Analyze (placeholder for now)
            action, confidence = analyze_crypto_signal(pair, [])
            
            if action == 'buy' and confidence >= MIN_CONFIDENCE:
                print(f"   🟢 BUY Signal: {confidence*100:.0f}% confidence")
                # Would place order here
            elif action == 'sell':
                print(f"   🔴 SELL Signal")
            else:
                print(f"   ⏸️  HOLD")
        
        print(f"\n{'='*60}")
        
    except Exception as e:
        print(f"❌ Error in crypto strategy: {e}")

def main():
    """Main 24/7 crypto trading loop."""
    print("🚀 24/7 CRYPTO TRADER STARTING")
    print("="*60)
    print(f"Trading: {', '.join(CRYPTO_PAIRS)}")
    print(f"Scan Interval: {SCAN_INTERVAL} seconds")
    print(f"Risk per Trade: {RISK_PER_TRADE*100:.0f}%")
    print(f"Min Confidence: {MIN_CONFIDENCE*100:.0f}%")
    print("="*60)
    
    cycle = 0
    
    while True:
        try:
            cycle += 1
            now = datetime.now()
            
            # Check if stock market is open
            stock_market_open = is_stock_market_open()
            
            if stock_market_open:
                print(f"\n💤 Stock market is OPEN - Crypto bot on standby")
                print(f"   (Stock bot is handling trades)")
            else:
                print(f"\n🌙 Stock market CLOSED - Crypto bot ACTIVE!")
                execute_crypto_strategy()
            
            # Wait for next scan
            print(f"\n⏰ Next scan in {SCAN_INTERVAL} seconds...")
            print(f"   Cycle #{cycle} completed at {now.strftime('%H:%M:%S')}")
            
            time.sleep(SCAN_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Crypto bot stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Error in main loop: {e}")
            print("   Continuing in 60 seconds...")
            time.sleep(60)

if __name__ == '__main__':
    main()
