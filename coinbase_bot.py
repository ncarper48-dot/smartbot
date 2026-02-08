#!/usr/bin/env python3
"""
Coinbase Advanced Trade API Integration (DISABLED)
Crypto trading removed. Stocks-only mode.
"""
raise SystemExit("Crypto trading disabled: stocks-only mode")
import os
import time
import json
import hmac
import hashlib
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY_NAME = os.getenv('COINBASE_API_KEY_NAME')
PRIVATE_KEY = os.getenv('COINBASE_PRIVATE_KEY').replace('\\n', '\n')
BASE_URL = 'https://api.coinbase.com/api/v3/brokerage'


def generate_jwt_token(method, path):
    """Generate JWT token for Coinbase authentication."""
    try:
        import jwt
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        
        # Load private key
        private_key = serialization.load_pem_private_key(
            PRIVATE_KEY.encode('utf-8'),
            password=None,
            backend=default_backend()
        )
        
        # Create JWT payload  
        uri = f"{method} api.coinbase.com{path}"
        payload = {
            'sub': API_KEY_NAME,
            'iss': 'coinbase-cloud',
            'nbf': int(time.time()),
            'exp': int(time.time()) + 120,
            'uri': uri
        }
        
        # Generate token with correct kid header
        token = jwt.encode(
            payload, 
            private_key, 
            algorithm='ES256', 
            headers={'kid': API_KEY_NAME, 'nonce': str(int(time.time() * 1000))}
        )
        return token
        
    except Exception as e:
        print(f"Error generating JWT: {e}")
        raise


def get_auth_headers(method, path):
    """Generate authentication headers for API requests."""
    token = generate_jwt_token(method, path)
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }


def get_accounts():
    """Get all Coinbase accounts and balances."""
    try:
        headers = get_auth_headers('GET', '/api/v3/brokerage/accounts')
        response = requests.get(f'{BASE_URL}/accounts', headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            accounts = data.get('accounts', [])
            
            # Exclude SYLO tokens which are worthless (£0.00 despite large quantity)
            excluded_tokens = ['SYLO']
            
            total_value = 0
            for a in accounts:
                currency = a.get('currency', '')
                if currency not in excluded_tokens:
                    total_value += float(a.get('available_balance', {}).get('value', 0))
            
            return {
                'accounts': accounts,
                'total_value_usd': total_value
            }
        else:
            print(f"Error getting accounts: {response.status_code}")
            print(response.text)
            return {'accounts': [], 'total_value_usd': 0}
    except Exception as e:
        print(f"Exception in get_accounts: {e}")
        return {'accounts': [], 'total_value_usd': 0}


def get_crypto_price(symbol):
    """Get current price for a crypto pair (e.g., BTC-USD)."""
    try:
        headers = get_auth_headers('GET', f'/api/v3/brokerage/products/{symbol}')
        response = requests.get(f'{BASE_URL}/products/{symbol}', headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return float(data.get('price', 0))
        return None
    except Exception as e:
        print(f"Error getting price for {symbol}: {e}")
        return None


def place_market_order(symbol, side, quantity=None, amount_usd=None):
    """
    Place a market order.
    
    Args:
        symbol: Trading pair (e.g., 'BTC-USD')
        side: 'BUY' or 'SELL'
        quantity: Amount of crypto to buy/sell (optional)
        amount_usd: USD amount to spend (optional, for buys only)
    """
    try:
        headers = get_auth_headers('POST', '/api/v3/brokerage/orders')
        
        order_config = {
            'market_market_ioc': {
                'quote_size' if amount_usd else 'base_size': str(amount_usd if amount_usd else quantity)
            }
        }
        
        payload = {
            'client_order_id': f'tradebot_{int(time.time() * 1000)}',
            'product_id': symbol,
            'side': side,
            'order_configuration': order_config
        }
        
        response = requests.post(f'{BASE_URL}/orders', 
                                headers=headers, 
                                json=payload, 
                                timeout=10)
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✅ Order placed: {side} {symbol}")
            return data
        else:
            print(f"Error placing order: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Exception in place_market_order: {e}")
        return None


def get_open_orders():
    """Get all open orders."""
    try:
        headers = get_auth_headers('GET', '/api/v3/brokerage/orders/historical/batch')
        response = requests.get(
            f'{BASE_URL}/orders/historical/batch',
            headers=headers,
            params={'order_status': 'OPEN'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('orders', [])
        return []
    except Exception as e:
        print(f"Error getting open orders: {e}")
        return []


def cancel_order(order_id):
    """Cancel a specific order."""
    try:
        headers = get_auth_headers('POST', f'/api/v3/brokerage/orders/batch_cancel')
        payload = {'order_ids': [order_id]}
        
        response = requests.post(
            f'{BASE_URL}/orders/batch_cancel',
            headers=headers,
            json=payload,
            timeout=10
        )
        
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Error canceling order: {e}")
        return False


def test_connection():
    """Test Coinbase API connection."""
    print("🔍 Testing Coinbase API Connection...")
    print()
    
    try:
        accounts = get_accounts()
        
        if accounts['total_value_usd'] > 0:
            print(f"✅ Connected to Coinbase!")
            print(f"💰 Total Balance: ${accounts['total_value_usd']:.2f}")
            print()
            print("📊 Account Breakdown:")
            for acc in accounts['accounts']:
                currency = acc.get('currency', 'Unknown')
                balance = float(acc.get('available_balance', {}).get('value', 0))
                if balance > 0:
                    print(f"   {currency}: {balance:.8f}")
            return True
        else:
            print("⚠️  Connected but no balance found")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == '__main__':
    test_connection()
