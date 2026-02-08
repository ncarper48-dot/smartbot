#!/usr/bin/env python3
"""
Generate status.json for the dashboard - PROFESSIONAL GRADE
"""
import json
import subprocess
import os
import sys
import yfinance as yf

def get_bot_status():
    """Check if auto_trader is running."""
    try:
        result = subprocess.run(['pgrep', '-f', 'auto_trader.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pid = result.stdout.strip().split('\n')[0]
            # Get uptime
            uptime_result = subprocess.run(['ps', '-p', pid, '-o', 'etime='],
                                         capture_output=True, text=True)
            uptime = uptime_result.stdout.strip() if uptime_result.returncode == 0 else 'Unknown'
            return True, pid, uptime
        return False, None, None
    except:
        return False, None, None

def get_account_balance():
    """Get Trading212 account balance."""
    try:
        import requests
        import base64
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('TRADING212_API_KEY')
        api_secret = os.getenv('TRADING212_API_SECRET')
        base_url = os.getenv('TRADING212_BASE_URL')
        
        auth = base64.b64encode(f'{api_key}:{api_secret}'.encode()).decode()
        headers = {'Authorization': f'Basic {auth}'}
        
        resp = requests.get(f'{base_url}/equity/account/cash', headers=headers, timeout=5)
        if resp.status_code == 200:
            account = resp.json()
            return account.get('total', 0), account.get('free', 0)
        return 0, 0
    except:
        return 0, 0

def get_daily_tracker():
    """Get today's P&L and trades."""
    tracker_file = '/home/tradebot/daily_tracker.json'
    try:
        with open(tracker_file, 'r') as f:
            return json.load(f)
    except:
        return {
            'daily_pnl_gbp': 0,
            'trades_today': 0,
            'target_hit': False
        }

def get_risk_state():
    """Get advanced risk management state."""
    risk_file = '/home/tradebot/risk_state.json'
    try:
        with open(risk_file, 'r') as f:
            return json.load(f)
    except:
        return {
            'consecutive_wins': 0,
            'consecutive_losses': 0,
            'daily_pnl': 0.0,
            'last_update': ''
        }

def get_open_positions():
    """Get open trading positions."""
    positions_file = '/home/tradebot/open_positions.json'
    try:
        with open(positions_file, 'r') as f:
            positions = json.load(f)
            return [p for p in positions.values() if p.get('status') == 'OPEN']
    except:
        return []

def get_market_regime():
    """Get current market regime."""
    try:
        vix = yf.Ticker("^VIX")
        vix_data = vix.history(period='1d', interval='1m')
        if not vix_data.empty:
            current_vix = float(vix_data['Close'].iloc[-1])
            if current_vix > 30:
                return 'VOLATILE', current_vix, 0.5
            elif current_vix > 20:
                return 'CHOPPY', current_vix, 0.75
            else:
                return 'NORMAL', current_vix, 1.0
        return 'UNKNOWN', 0, 1.0
    except:
        return 'UNKNOWN', 0, 1.0

def get_performance_stats():
    """Get overall performance statistics."""
    perf_file = '/home/tradebot/performance_history.json'
    try:
        with open(perf_file, 'r') as f:
            data = json.load(f)
            trades = data.get('trades', [])
            if trades:
                total_trades = len(trades)
                # Calculate win rate (approximate based on confidence)
                high_conf_trades = sum(1 for t in trades if t.get('confidence', 0) > 0.7)
                win_rate = (high_conf_trades / total_trades * 100) if total_trades > 0 else 0
                return total_trades, win_rate
            return 0, 0
    except:
        return 0, 0

def generate_status_json():
    """Generate comprehensive status.json file for professional dashboard."""
    bot_running, pid, uptime = get_bot_status()
    balance, free_cash = get_account_balance()
    tracker = get_daily_tracker()
    risk_state = get_risk_state()
    open_positions = get_open_positions()
    regime, vix, regime_mult = get_market_regime()
    total_trades, win_rate = get_performance_stats()
    
    # Load performance history for recent trades
    try:
        with open('/home/tradebot/performance_history.json', 'r') as f:
            perf_history = json.load(f)
    except:
        perf_history = {'trades': []}
    
    # Calculate dynamic risk
    from dotenv import load_dotenv
    load_dotenv()
    base_risk = float(os.getenv('TRADING212_RISK_PER_TRADE', 0.12))
    
    dynamic_risk = base_risk
    if risk_state['consecutive_losses'] >= 3:
        dynamic_risk *= 0.6
    elif risk_state['consecutive_losses'] >= 2:
        dynamic_risk *= 0.75
    if risk_state['consecutive_wins'] >= 3:
        dynamic_risk *= 1.2
        dynamic_risk = min(dynamic_risk, 0.15)
    
    adjusted_risk = dynamic_risk * regime_mult
    adjusted_risk = max(0.01, min(0.15, adjusted_risk))
    
    # Circuit breaker check
    max_loss = float(os.getenv('TRADING212_MAX_DAILY_LOSS_PCT', 0.05))
    circuit_breaker = risk_state['daily_pnl'] <= -max_loss
    
    # Position analysis
    position_count = len(open_positions)
    max_positions = int(os.getenv('TRADING212_MAX_POSITIONS', 7))
    
    total_position_value = sum(p.get('quantity', 0) * p.get('current_price', p.get('entry_price', 0)) 
                               for p in open_positions)
    
    # Calculate unrealized P&L
    unrealized_pnl = sum(
        (p.get('current_price', p.get('entry_price', 0)) - p.get('entry_price', 0)) * p.get('quantity', 0)
        for p in open_positions
    )
    
    status = {
        'bot_running': bot_running,
        'pid': pid or 'N/A',
        'uptime': uptime or 'N/A',
        'balance': balance,
        'free_cash': free_cash,
        'deployed_pct': ((balance - free_cash) / balance * 100) if balance > 0 else 0,
        'pnl_today': tracker.get('daily_pnl_gbp', 0),
        'trades_today': tracker.get('trades_today', 0),
        'target_hit': tracker.get('target_hit', False),
        
        # Advanced risk management
        'base_risk_pct': base_risk * 100,
        'dynamic_risk_pct': dynamic_risk * 100,
        'adjusted_risk_pct': adjusted_risk * 100,
        'consecutive_wins': risk_state.get('consecutive_wins', 0),
        'consecutive_losses': risk_state.get('consecutive_losses', 0),
        'circuit_breaker': circuit_breaker,
        
        # Market regime
        'market_regime': regime,
        'vix': vix,
        'regime_multiplier': regime_mult,
        
        # Position management
        'open_positions': position_count,
        'max_positions': max_positions,
        'position_capacity': f"{position_count}/{max_positions}",
        'total_position_value': total_position_value,
        'unrealized_pnl': unrealized_pnl,
        
        # Performance
        'total_trades_all_time': total_trades,
        'win_rate': win_rate,
        
    # Positions detail
        'positions': open_positions,
        
        # Recent trades for activity feed
        'recent_trades': perf_history.get('trades', [])[-20:] if 'trades' in perf_history else [],
        
        'timestamp': subprocess.run(['date', '+%Y-%m-%d %H:%M:%S'],
                                   capture_output=True, text=True).stdout.strip()
    }
    
    status_file = '/home/tradebot/status.json'
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=2)
    
    return status

if __name__ == '__main__':
    status = generate_status_json()
    if '--print' in sys.argv:
        print(json.dumps(status, indent=2))
