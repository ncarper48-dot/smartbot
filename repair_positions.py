#!/usr/bin/env python3
"""
Repair position tracking by syncing with Trading212 actual positions
"""
import json
from bot import get_account_cash
import yfinance as yf
import pandas as pd
from demo_pipeline import compute_indicators

def get_trading212_positions():
    """Get actual positions from Trading212 API"""
    try:
        # The account endpoint returns positions data
        account = get_account_cash()
        print(f"Account data: {json.dumps(account, indent=2)}")
        
        # Check if there's a positions endpoint or field
        # Note: You may need to import additional API functions from bot.py
        return {}
    except Exception as e:
        print(f"Error fetching positions: {e}")
        return {}

def estimate_atr(ticker):
    """Estimate ATR for a ticker"""
    try:
        df = yf.download(ticker, period='5d', interval='1h', progress=False)
        if df.empty:
            return 2.0  # Default fallback
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df = compute_indicators(df)
        return float(df.iloc[-1]['atr'])
    except:
        return 2.0

def reconstruct_positions_from_history():
    """Reconstruct open positions from trade history"""
    print("=" * 70)
    print("🔧 POSITION TRACKING REPAIR TOOL")
    print("=" * 70)
    
    # Load trade history
    with open('performance_history.json', 'r') as f:
        data = json.load(f)
    
    trades = data.get('trades', [])
    
    # Build position map (track all buys without sells)
    positions_map = {}
    
    for trade in trades:
        ticker_212 = trade.get('ticker', '')
        ticker = ticker_212.replace('_US_EQ', '')
        action = trade.get('action', '')
        qty = trade.get('quantity', 0)
        price = trade.get('price', 0)
        reason = trade.get('reason', 'Unknown')
        confidence = trade.get('confidence', 0.7)
        
        if action == 'buy':
            if ticker not in positions_map:
                positions_map[ticker] = {
                    'ticker': ticker,
                    'quantity': 0,
                    'total_cost': 0,
                    'buys': []
                }
            positions_map[ticker]['quantity'] += qty
            positions_map[ticker]['total_cost'] += (price * qty)
            positions_map[ticker]['buys'].append({
                'price': price,
                'qty': qty,
                'reason': reason,
                'confidence': confidence
            })
        
        elif action == 'sell':
            if ticker in positions_map:
                positions_map[ticker]['quantity'] -= qty
                # Remove if fully closed
                if positions_map[ticker]['quantity'] <= 0:
                    del positions_map[ticker]
    
    # Convert to open_positions.json format
    open_positions = {}
    
    print(f"\n📊 Found {len(positions_map)} open positions to track:\n")
    
    for ticker, pos_data in positions_map.items():
        if pos_data['quantity'] > 0:
            avg_price = pos_data['total_cost'] / pos_data['quantity']
            
            # Estimate current ATR
            atr = estimate_atr(ticker)
            
            # Use most recent buy's reason
            last_reason = pos_data['buys'][-1]['reason'] if pos_data['buys'] else 'Historical'
            
            open_positions[ticker] = {
                'ticker': ticker,
                'quantity': pos_data['quantity'],
                'entry_price': avg_price,
                'current_price': avg_price,  # Will be updated on next scan
                'atr': atr,
                'strategy': last_reason,
                'entry_time': '2026-01-07T00:00:00',  # Approximate
                'stop_loss': avg_price - (atr * 2),
                'profit_target': avg_price + (atr * 4),
                'status': 'OPEN',
                'partial_taken': False
            }
            
            print(f"   {ticker:8s}: {pos_data['quantity']:3.0f} shares @ ${avg_price:.2f}")
            print(f"               Stop: ${avg_price - (atr * 2):.2f} | Target: ${avg_price + (atr * 4):.2f}")
    
    # Save repaired positions
    with open('open_positions.json', 'w') as f:
        json.dump(open_positions, f, indent=2)
    
    print(f"\n✅ Repaired! Saved {len(open_positions)} positions to open_positions.json")
    print("=" * 70)
    
    return open_positions

if __name__ == '__main__':
    reconstruct_positions_from_history()
