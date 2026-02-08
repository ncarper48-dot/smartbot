#!/usr/bin/env python3
"""
Kraken crypto trading integration (DISABLED) - Stocks-only mode
"""
raise SystemExit("Crypto trading disabled: stocks-only mode")
import requests
import time
import hmac
import hashlib
import base64
import urllib.parse
import os
from dotenv import load_dotenv

load_dotenv()

# Kraken API credentials (to be added later)
KRAKEN_API_KEY = os.getenv('KRAKEN_API_KEY', '')
KRAKEN_PRIVATE_KEY = os.getenv('KRAKEN_PRIVATE_KEY', '')
KRAKEN_BASE_URL = 'https://api.kraken.com'

# Crypto pairs to trade
CRYPTO_PAIRS = ['XXBTZUSD', 'XETHZUSD', 'SOLUSD']  # BTC, ETH, SOL

def generate_kraken_signature(urlpath, data, secret):
    """Generate Kraken API signature"""
    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()
    
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()

def kraken_request(uri_path, data=None, api_key=None, api_secret=None):
    """Make authenticated request to Kraken API"""
    headers = {}
    
    if api_key and api_secret:
        data['nonce'] = str(int(1000 * time.time()))
        headers['API-Key'] = api_key
        headers['API-Sign'] = generate_kraken_signature(uri_path, data, api_secret)
    
    url = KRAKEN_BASE_URL + uri_path
    response = requests.post(url, headers=headers, data=data)
    return response.json()

def get_balance():
    """Get account balance"""
    if not KRAKEN_API_KEY or not KRAKEN_PRIVATE_KEY:
        print("❌ Kraken API credentials not set")
        return None
    
    data = {'nonce': str(int(1000 * time.time()))}
    result = kraken_request('/0/private/Balance', data, KRAKEN_API_KEY, KRAKEN_PRIVATE_KEY)
    
    if result.get('error'):
        print(f"❌ Error: {result['error']}")
        return None
    
    return result.get('result', {})

def get_ticker(pair):
    """Get current price for a crypto pair"""
    url = f"{KRAKEN_BASE_URL}/0/public/Ticker?pair={pair}"
    response = requests.get(url)
    data = response.json()
    
    if data.get('error'):
        return None
    
    result = data.get('result', {})
    if pair in result:
        return float(result[pair]['c'][0])  # Last trade price
    
    # Try alternate pair name
    for key in result.keys():
        return float(result[key]['c'][0])
    
    return None

def place_market_order(pair, side, volume):
    """
    Place market order on Kraken
    
    Args:
        pair: Trading pair (e.g., 'XXBTZUSD')
        side: 'buy' or 'sell'
        volume: Amount to trade
    """
    if not KRAKEN_API_KEY or not KRAKEN_PRIVATE_KEY:
        print("❌ Kraken API credentials not set")
        return None
    
    data = {
        'nonce': str(int(1000 * time.time())),
        'ordertype': 'market',
        'type': side,
        'volume': str(volume),
        'pair': pair
    }
    
    result = kraken_request('/0/private/AddOrder', data, KRAKEN_API_KEY, KRAKEN_PRIVATE_KEY)
    
    if result.get('error'):
        print(f"❌ Order error: {result['error']}")
        return None
    
    return result.get('result')

def test_connection():
    """Test Kraken API connection"""
    print("🔍 Testing Kraken API Connection")
    print("=" * 60)
    print()
    
    if not KRAKEN_API_KEY or not KRAKEN_PRIVATE_KEY:
        print("⚠️  Kraken API credentials not configured yet")
        print()
        print("📝 TO ENABLE KRAKEN TRADING:")
        print("   1. Go to: https://www.kraken.com/sign-up")
        print("   2. Complete KYC verification")
        print("   3. Go to Settings → API")
        print("   4. Create API Key with permissions:")
        print("      - Query Funds")
        print("      - Create & Modify Orders")
        print("   5. Copy API Key and Private Key")
        print("   6. Add to .env file:")
        print("      KRAKEN_API_KEY=your_api_key")
        print("      KRAKEN_PRIVATE_KEY=your_private_key")
        print()
        print("💰 FUNDING:")
        print("   • Minimum: £20 recommended")
        print("   • Deposit: Bank transfer (UK faster payments)")
        print("   • Buy: BTC, ETH, or SOL")
        print()
        print("🤖 Once set up, SmartBot will:")
        print("   • Trade crypto 24/7 (weekends too)")
        print("   • Same aggressive strategies")
        print("   • Email alerts for all trades")
        print("   • More opportunities to hit £250 target")
        print()
        return False
    
    # Test public endpoint
    print("Testing public API...")
    btc_price = get_ticker('XXBTZUSD')
    if btc_price:
        print(f"✅ Public API works - BTC: ${btc_price:,.2f}")
    else:
        print("❌ Public API failed")
        return False
    
    # Test private endpoint
    print("\nTesting account access...")
    balance = get_balance()
    if balance:
        print("✅ Account access works")
        print("\n💰 BALANCES:")
        for currency, amount in balance.items():
            if float(amount) > 0:
                print(f"   {currency}: {float(amount):.8f}")
    else:
        print("❌ Account access failed")
        return False
    
    print("\n✅ Kraken integration ready!")
    return True

if __name__ == "__main__":
    test_connection()
