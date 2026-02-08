#!/usr/bin/env python3
"""FORCE BUY FIRST VALID SIGNAL"""
import sys
sys.path.insert(0, '/home/tradebot')
from live_trader import get_current_signal
import requests
import base64
import os

api_key = "44068546ZxTtBvdXzLjZbxOVLmbmQntQgVWBL"
api_secret = "klhXpdv0QPwxhDP4th2Yf0hjDyhJrtrapoT8E-gPAO0"

auth_str = f"{api_key}:{api_secret}"
encoded = base64.b64encode(auth_str.encode()).decode()
headers = {'Authorization': f'Basic {encoded}', 'Content-Type': 'application/json'}

base_url = "https://demo.trading212.com/api/v0"

print("\n🔥 SCANNING FOR ANY BUY SIGNAL")
print("="*70)

tickers = ['COIN', 'MSTR', 'RIOT', 'MARA', 'GME', 'AMC', 'TSLA', 'NVDA', 
           'PLTR', 'SHOP', 'UPST', 'ZM', 'SNAP', 'SOFI', 'HOOD']

for ticker in tickers:
    try:
        signal = get_current_signal(ticker)
        action = signal.get('action')
        confidence = signal.get('confidence', 0)
        
        if action == 'buy' and confidence >= 0.35:
            reason = signal.get('reason')
            price = signal.get('price', 0)
            
            print(f"\n✅ FOUND: {ticker}")
            print(f"   Confidence: {confidence*100:.0f}%")
            print(f"   Reason: {reason}")
            print(f"   Price: ${price:.2f}")
            
            # BUY IT NOW
            ticker_212 = f"{ticker}_US_EQ"
            qty = 10  # Buy 10 shares
            
            print(f"\n🔥 BUYING {qty} shares of {ticker_212}...")
            
            order_data = {"ticker": ticker_212, "quantity": qty}
            response = requests.post(f"{base_url}/equity/orders/market",
                                   json=order_data, headers=headers)
            
            print(f"   Response: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print(f"   ✅ ORDER PLACED!")
                print(f"   {response.json()}")
                print("\n🎉 SMARTBOT MADE ITS FIRST TRADE!")
                break
            else:
                print(f"   ❌ Failed: {response.text[:200]}")
        
    except Exception as e:
        continue

print("\n" + "="*70)
