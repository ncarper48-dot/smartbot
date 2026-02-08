#!/usr/bin/env python3
"""24/7 LIVE CRYPTO TRADER (DISABLED) - Stocks-only mode"""
raise SystemExit("Crypto trading disabled: stocks-only mode")
import yfinance as yf
import time
import json
from datetime import datetime
import os
import sys

# Import Coinbase trading functions
sys.path.insert(0, '/home/tradebot')
from coinbase_bot import get_accounts, place_market_order, get_crypto_price

CRYPTOS = ['BTC-USD', 'ETH-USD', 'SOL-USD']
SCAN_INTERVAL = 300  # 5 minutes
TRADE_SIZE_USD = 5.0  # $5 per trade
MIN_CONFIDENCE = 0.65  # Only trade high-confidence signals
POSITIONS_FILE = '/home/tradebot/crypto_positions.json'
TRADE_LOG = '/home/tradebot/crypto_trades.log'

def load_positions():
    """Load current crypto positions."""
    try:
        if os.path.exists(POSITIONS_FILE):
            with open(POSITIONS_FILE, 'r') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_positions(positions):
    """Save current positions."""
    try:
        with open(POSITIONS_FILE, 'w') as f:
            json.dump(positions, f, indent=2)
    except Exception as e:
        print(f"Error saving positions: {e}")

def log_trade(symbol, action, price, amount, pnl=0):
    """Log trade to file."""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"{timestamp} | {symbol} | {action} | ${price:.2f} | ${amount:.2f} | P&L: ${pnl:.2f}\n"
        with open(TRADE_LOG, 'a') as f:
            f.write(log_line)
    except Exception as e:
        print(f"Error logging trade: {e}")

def analyze_crypto(ticker):
    """Simple momentum analysis"""
    try:
        df = yf.download(ticker, period='1d', interval='5m', progress=False)
        if df.empty or len(df) < 20:
            return 'hold', 0
        
        close = df['Close'].values
        current = close[-1]
        ma_short = sum(close[-5:]) / 5
        ma_long = sum(close[-20:]) / 20
        
        # Simple crossover
        if ma_short > ma_long * 1.002:  # 0.2% above
            return 'buy', 0.7
        elif ma_short < ma_long * 0.998:  # 0.2% below
            return 'sell', 0.7
        
        return 'hold', 0
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return 'hold', 0

def execute_trade(symbol, action, confidence):
    """Execute live trade on Coinbase."""
    try:
        positions = load_positions()
        current_price = get_crypto_price(symbol)
        
        if not current_price:
            print(f"❌ Could not get price for {symbol}")
            return False
        
        # BUY logic
        if action == 'buy' and symbol not in positions:
            accounts = get_accounts()
            if accounts['total_value_usd'] < TRADE_SIZE_USD:
                print(f"⚠️  Insufficient balance: ${accounts['total_value_usd']:.2f} < ${TRADE_SIZE_USD}")
                return False
            
            result = place_market_order(symbol, 'BUY', amount_usd=TRADE_SIZE_USD)
            if result:
                positions[symbol] = {
                    'entry_price': current_price,
                    'amount_usd': TRADE_SIZE_USD,
                    'timestamp': datetime.now().isoformat()
                }
                save_positions(positions)
                log_trade(symbol, 'BUY', current_price, TRADE_SIZE_USD)
                print(f"✅ BOUGHT {symbol} @ ${current_price:.2f}")
                return True
        
        # SELL logic
        elif action == 'sell' and symbol in positions:
            entry_price = positions[symbol]['entry_price']
            amount_usd = positions[symbol]['amount_usd']
            
            # Calculate quantity to sell (estimate)
            quantity = amount_usd / entry_price
            
            result = place_market_order(symbol, 'SELL', quantity=quantity)
            if result:
                pnl = (current_price - entry_price) / entry_price * amount_usd
                print(f"✅ SOLD {symbol} @ ${current_price:.2f} | P&L: ${pnl:+.2f}")
                log_trade(symbol, 'SELL', current_price, amount_usd, pnl)
                del positions[symbol]
                save_positions(positions)
                return True
        
        return False
    except Exception as e:
        print(f"❌ Trade execution error: {e}")
        return False

def main():
    print("🚀 24/7 LIVE CRYPTO TRADER STARTED")
    print(f"💰 Trade Size: ${TRADE_SIZE_USD} per position")
    print(f"🎯 Min Confidence: {MIN_CONFIDENCE:.0%}")
    print(f"📊 Tracking: {', '.join(CRYPTOS)}")
    print(f"⏱️  Scan every {SCAN_INTERVAL//60} minutes\n")
    
    # Check balance
    accounts = get_accounts()
    print(f"💵 Starting Balance: ${accounts['total_value_usd']:.2f}\n")
    
    while True:
        try:
            print(f"\n{'='*60}")
            print(f"🔍 CRYPTO SCAN - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}")
            
            positions = load_positions()
            
            for crypto in CRYPTOS:
                action, confidence = analyze_crypto(crypto)
                in_position = crypto in positions
                
                if action == 'buy' and confidence >= MIN_CONFIDENCE and not in_position:
                    print(f"🟢 {crypto}: BUY signal (confidence: {confidence:.0%})")
                    execute_trade(crypto, 'buy', confidence)
                    
                elif action == 'sell' and confidence >= MIN_CONFIDENCE and in_position:
                    print(f"🔴 {crypto}: SELL signal (confidence: {confidence:.0%})")
                    execute_trade(crypto, 'sell', confidence)
                    
                elif in_position:
                    entry = positions[crypto]['entry_price']
                    current = get_crypto_price(crypto)
                    if current:
                        pnl_pct = ((current - entry) / entry) * 100
                        print(f"📍 {crypto}: HOLDING @ ${entry:.2f} | Now ${current:.2f} ({pnl_pct:+.2f}%)")
                    else:
                        print(f"📍 {crypto}: HOLDING @ ${entry:.2f}")
                else:
                    print(f"⚪ {crypto}: HOLD (no position)")
            
            time.sleep(SCAN_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Crypto trader stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    main()
