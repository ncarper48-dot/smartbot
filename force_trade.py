#!/usr/bin/env python3
"""Force a trade RIGHT NOW to prove bot can execute"""
import sys
sys.path.insert(0, '/home/tradebot')
from live_trader import get_current_signal
import requests
import os

api_key = os.popen('grep "^TRADING212_API_KEY=" /home/tradebot/.env | cut -d= -f2').read().strip()
base_url = "https://demo.trading212.com/api/v0"

print("\n🔥 FORCING TRADE EXECUTION")
print("="*70)

# Find a signal
ticker = 'RIOT'
signal = get_current_signal(ticker)

print(f"\n1️⃣ Signal for {ticker}:")
print(f"   Action: {signal.get('action')}")
print(f"   Confidence: {signal.get('confidence', 0)*100:.0f}%")
print(f"   Reason: {signal.get('reason')}")

if signal.get('action') == 'buy' and signal.get('confidence', 0) >= 0.35:
    # Force buy 10 shares
    ticker_212 = f"{ticker}_US_EQ"
    qty = 10
    
    print(f"\n2️⃣ Attempting to buy {qty} shares of {ticker_212}...")
    
    order_data = {
        "ticker": ticker_212,
        "quantity": qty
    }
    
    response = requests.post(
        f"{base_url}/equity/orders/market",
        json=order_data,
        headers={'Authorization': api_key}
    )
    
    print(f"\n3️⃣ Response: {response.status_code}")
    print(f"   {response.text[:300]}")
    
    if response.status_code in [200, 201]:
        print("\n✅ ORDER PLACED!")
    else:
        print("\n❌ ORDER FAILED")
        print("\nThis confirms: Trading212 demo API is not working")
        print("401 errors = authentication issue or expired account")
else:
    print("\n❌ No valid buy signal right now")

print("="*70)
