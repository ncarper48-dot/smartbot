#!/usr/bin/env python3
"""
SmartBot Professional Trading Terminal - Bloomberg-Style Dashboard
Clean, sophisticated, data-focused design
"""
import json
import subprocess
import os
from datetime import datetime
import requests
import base64

def get_trading212_live_data():
    """Get real-time data from Trading212 API."""
    try:
        api_key = "44068546ZxTtBvdXzLjZbxOVLmbmQntQgVWBL"
        api_secret = "klhXpdv0QPwxhDP4th2Yf0hjDyhJrtrapoT8E-gPAO0"
        base_url = "https://demo.trading212.com/api/v0"
        
        auth_str = f"{api_key}:{api_secret}"
        encoded = base64.b64encode(auth_str.encode()).decode()
        headers = {
            'Authorization': f'Basic {encoded}',
            'Content-Type': 'application/json'
        }
        
        # Get cash
        cash_resp = requests.get(f"{base_url}/equity/account/cash", headers=headers, timeout=5)
        cash_data = cash_resp.json() if cash_resp.status_code == 200 else {'free': 0, 'total': 5000, 'ppl': 0}
        
        # Get portfolio
        port_resp = requests.get(f"{base_url}/equity/portfolio", headers=headers, timeout=5)
        positions = port_resp.json() if port_resp.status_code == 200 else []
        
        return cash_data, positions
    except Exception as e:
        return {'free': 0, 'total': 5000, 'ppl': 0}, []

def get_crypto_data():
    """Get Coinbase crypto account data."""
    try:
        from coinbase_bot import get_accounts, get_crypto_price
        accounts = get_accounts()
        crypto_balance = accounts.get('total_value_usd', 0)
        
        # Get current prices for BTC, ETH, SOL
        btc_price = get_crypto_price('BTC-USD') or 0
        eth_price = get_crypto_price('ETH-USD') or 0
        sol_price = get_crypto_price('SOL-USD') or 0
        
        # Check crypto bot status
        result = subprocess.run(['pgrep', '-f', 'crypto_trader_24_7.py'], 
                              capture_output=True, text=True)
        crypto_bot_running = result.returncode == 0
        crypto_pid = result.stdout.strip().split('\n')[0] if crypto_bot_running else None
        
        return {
            'balance': crypto_balance,
            'btc_price': btc_price,
            'eth_price': eth_price,
            'sol_price': sol_price,
            'running': crypto_bot_running,
            'pid': crypto_pid
        }
    except Exception as e:
        return {
            'balance': 0,
            'btc_price': 0,
            'eth_price': 0,
            'sol_price': 0,
            'running': False,
            'pid': None
        }

def get_bot_status():
    """Check if bot is running."""
    try:
        result = subprocess.run(['pgrep', '-f', 'auto_trader.py'], 
                              capture_output=True, text=True)
        running = result.returncode == 0
        pid = result.stdout.strip().split('\n')[0] if running else None
        return running, pid
    except:
        return False, None

def generate_html():
    """Generate professional terminal-style dashboard."""
    cash_data, positions = get_trading212_live_data()
    bot_running, pid = get_bot_status()
    crypto_data = get_crypto_data()
    
    # Calculate stats
    total = cash_data.get('total', 0)
    free = cash_data.get('free', 0)
    pnl_today = cash_data.get('ppl', 0)
    deployed = total - free
    deployed_pct = (deployed / total * 100) if total > 0 else 0
    
    # Crypto stats
    crypto_balance = crypto_data['balance']
    combined_total = total + crypto_balance
    
    # Analyze positions
    winners = []
    losers = []
    total_unrealized = 0
    
    for p in positions:
        ticker = p['ticker'].replace('_US_EQ', '')
        qty = p['quantity']
        entry = p.get('averagePrice', 0)
        current = p['currentPrice']
        pnl = (current - entry) * qty
        pnl_pct = ((current - entry) / entry * 100) if entry > 0 else 0
        total_unrealized += pnl
        
        pos_data = {
            'ticker': ticker,
            'qty': qty,
            'entry': entry,
            'current': current,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'value': current * qty
        }
        
        if pnl >= 0:
            winners.append(pos_data)
        else:
            losers.append(pos_data)
    
    winners.sort(key=lambda x: x['pnl'], reverse=True)
    losers.sort(key=lambda x: x['pnl'])
    all_positions = winners + losers
    
    # Calculate metrics
    target_daily = 500
    progress_pct = (pnl_today / target_daily * 100) if target_daily > 0 else 0
    remaining = max(0, target_daily - pnl_today)
    win_rate = (len(winners) / len(positions) * 100) if positions else 0
    total_pnl = pnl_today + total_unrealized
    
    now = datetime.now().strftime('%H:%M:%S')
    date = datetime.now().strftime('%Y-%m-%d')
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="10">
<title>SmartBot Terminal</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: 'IBM Plex Sans', -apple-system, system-ui, sans-serif;
    background: #0d1117;
    color: #c9d1d9;
    line-height: 1.5;
}}

.terminal {{
    max-width: 1920px;
    margin: 0 auto;
    padding: 20px;
}}

/* Header Bar */
.header-bar {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 16px 24px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.header-left {{
    display: flex;
    align-items: center;
    gap: 24px;
}}

.terminal-title {{
    font-size: 1.1rem;
    font-weight: 600;
    color: #f0f6fc;
    letter-spacing: -0.02em;
}}

.status-indicator {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    font-family: 'IBM Plex Mono', monospace;
}}

.status-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: {"#3fb950" if bot_running else "#f85149"};
}}

.header-right {{
    display: flex;
    gap: 20px;
    align-items: center;
    font-size: 0.85rem;
    font-family: 'IBM Plex Mono', monospace;
    color: #8b949e;
}}

/* Main Grid */
.main-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 16px;
}}

.metric-card {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 20px;
}}

.metric-label {{
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #8b949e;
    margin-bottom: 8px;
    font-weight: 500;
}}

.metric-value {{
    font-size: 2rem;
    font-weight: 600;
    font-family: 'IBM Plex Mono', monospace;
    line-height: 1.2;
    margin-bottom: 4px;
}}

.metric-subtitle {{
    font-size: 0.8rem;
    color: #8b949e;
    font-family: 'IBM Plex Mono', monospace;
}}

.positive {{ color: #3fb950; }}
.negative {{ color: #f85149; }}
.neutral {{ color: #8b949e; }}

/* Progress Bar */
.progress-wrapper {{
    margin-top: 12px;
}}

.progress-track {{
    height: 4px;
    background: #21262d;
    border-radius: 2px;
    overflow: hidden;
}}

.progress-bar {{
    height: 100%;
    background: #3fb950;
    border-radius: 2px;
    transition: width 0.3s ease;
}}

.progress-label {{
    display: flex;
    justify-content: space-between;
    margin-top: 6px;
    font-size: 0.75rem;
    color: #8b949e;
    font-family: 'IBM Plex Mono', monospace;
}}

/* Data Table */
.data-section {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    overflow: hidden;
}}

.section-header {{
    padding: 16px 20px;
    border-bottom: 1px solid #21262d;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.section-title {{
    font-size: 0.95rem;
    font-weight: 600;
    color: #f0f6fc;
}}

.section-badge {{
    font-size: 0.75rem;
    padding: 3px 8px;
    background: #21262d;
    border-radius: 12px;
    font-family: 'IBM Plex Mono', monospace;
    color: #8b949e;
}}

.data-table {{
    width: 100%;
    border-collapse: collapse;
}}

.data-table thead {{
    background: #0d1117;
}}

.data-table th {{
    padding: 12px 20px;
    text-align: left;
    font-size: 0.75rem;
    font-weight: 500;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid #21262d;
}}

.data-table td {{
    padding: 14px 20px;
    font-size: 0.85rem;
    border-bottom: 1px solid #21262d;
    font-family: 'IBM Plex Mono', monospace;
}}

.data-table tbody tr {{
    transition: background 0.15s ease;
}}

.data-table tbody tr:hover {{
    background: #0d1117;
}}

.data-table tbody tr:last-child td {{
    border-bottom: none;
}}

.ticker-cell {{
    font-weight: 600;
    color: #f0f6fc;
}}

.pnl-positive {{
    color: #3fb950;
    font-weight: 500;
}}

.pnl-negative {{
    color: #f85149;
    font-weight: 500;
}}

/* Footer */
.footer {{
    margin-top: 16px;
    padding: 16px;
    text-align: center;
    font-size: 0.75rem;
    color: #6e7681;
    font-family: 'IBM Plex Mono', monospace;
}}

/* Responsive */
@media (max-width: 1400px) {{
    .main-grid {{ grid-template-columns: repeat(2, 1fr); }}
}}

@media (max-width: 768px) {{
    .main-grid {{ grid-template-columns: 1fr; }}
    .header-bar {{ flex-direction: column; align-items: flex-start; gap: 12px; }}
}}

/* Scrollbar */
::-webkit-scrollbar {{
    width: 10px;
    height: 10px;
}}

::-webkit-scrollbar-track {{
    background: #0d1117;
}}

::-webkit-scrollbar-thumb {{
    background: #30363d;
    border-radius: 5px;
}}

::-webkit-scrollbar-thumb:hover {{
    background: #484f58;
}}
</style>
</head>
<body>
<div class="terminal">

<!-- Header Bar -->
<div class="header-bar">
    <div class="header-left">
        <div class="terminal-title">SmartBot Trading Terminal</div>
        <div class="status-indicator">
            <span class="status-dot"></span>
            <span>STOCKS {"LIVE" if bot_running else "OFF"}</span>
        </div>
        <div class="status-indicator">
            <span class="status-dot" style="background: {"#3fb950" if crypto_data['running'] else "#f85149"}"></span>
            <span>CRYPTO {"LIVE" if crypto_data['running'] else "OFF"}</span>
        </div>
        {"<div class='status-indicator'><span>Stock PID: " + pid + "</span></div>" if pid else ""}
        {"<div class='status-indicator'><span>Crypto PID: " + crypto_data['pid'] + "</span></div>" if crypto_data['pid'] else ""}
    </div>
    <div class="header-right">
        <span>{date}</span>
        <span>{now}</span>
        <span>Auto-refresh: 10s</span>
    </div>
</div>Total Portfolio</div>
        <div class="metric-value">${combined_total:,.2f}</div>
        <div class="metric-subtitle">Stocks: ${total:,.2f} | Crypto: ${crypto_balanc
<div class="main-grid">
    <div class="metric-card">
        <div class="metric-label">Account Value</div>
        <div class="metric-value">${total:,.2f}</div>
        <div class="metric-subtitle">Free Cash: ${free:,.2f}</div>
    </div>
    
    <div class="metric-card">
        <div class="metric-label">Today's P&L</div>
        <div class="metric-value {"positive" if pnl_today >= 0 else "negative"}">${pnl_today:+,.2f}</div>
        <div class="metric-subtitle">Unrealized: ${total_unrealized:+,.2f}</div>
    </div>
    
    <div class="metric-card">
        <div class="metric-label">Total P&L</div>
        <div class="metric-value {"positive" if total_pnl >= 0 else "negative"}">${total_pnl:+,.2f}</div>
        <div class="metric-subtitle">ROI: {(total_pnl / (total - total_pnl) * 100) if total > 0 else 0:.2f}%</div>
    </div>
    
    <div class="metric-card">
        <div class="metric-label">Daily Target</div>
        <div class="metric-value">{progress_pct:.1f}%</div>
        <div class="progress-wrapper">
            <div class="progress-track">
                <div class="progress-bar" style="width: {min(progress_pct, 100):.1f}%"></div>
            </div>
            <div class="progress-label">
                <span>${pnl_today:.2f}</span>
                <span>${target_daily:.2f}</span>
            </div>
        </div>
    </div>
</div>

<!-- Secondary Metrics -->
<div class="main-grid">
    <div class="metric-card">
        <div class="metric-label">Open Positions</div>
        <div class="metric-value">{len(positions)}</div>
        <div class="metric-subtitle">Max: 20</div>
    </div>
    
    <div class="metric-card">
        <div class="metric-label">Win Rate</div>
        <div class="metric-value">{win_rate:.1f}%</div>
        <div class="metric-subtitle">{len(winners)}W / {len(losers)}L</div>
    </div>
    
    <div class="metric-card">
        <div class="metric-label">Capital Deployed</div>
        <div class="metric-value">{deployed_pct:.1f}%</div>
        <div class="metric-subtitle">${deployed:,.2f}</div>
    </div>
    
    <div class="metric-card">
        <div class="metric-label">Largest Position</div>
        <div class="metric-value">{"$" + f"{max(p['value'] for p in all_positions):,.2f}" if all_positions else "$0.00"}</div>
        <div class="metric-subtitle">{all_positions[0]['ticker'] if all_positions else "N/A"}</div>
    </div>
</div>

<!-- Crypto Prices -->
<div class="main-grid" style="margin-top: 16px;">
    <div class="metric-card">
        <div class="metric-label">Bitcoin</div>
        <div class="metric-value" style="font-size: 1.5rem;">${crypto_data['btc_price']:,.2f}</div>
        <div class="metric-subtitle">BTC-USD</div>
    </div>
    
    <div class="metric-card">
        <div class="metric-label">Ethereum</div>
        <div class="metric-value" style="font-size: 1.5rem;">${crypto_data['eth_price']:,.2f}</div>
        <div class="metric-subtitle">ETH-USD</div>
    </div>
    
    <div class="metric-card">
        <div class="metric-label">Solana</div>
        <div class="metric-value" style="font-size: 1.5rem;">${crypto_data['sol_price']:,.2f}</div>
        <div class="metric-subtitle">SOL-USD</div>
    </div>
    
    <div class="metric-card">
        <div class="metric-label">Crypto Bot Status</div>
        <div class="metric-value" style="font-size: 1.5rem; color: {"#3fb950" if crypto_data['running'] else "#f85149"};">{"ACTIVE" if crypto_data['running'] else "OFFLINE"}</div>
        <div class="metric-subtitle">24/7 Trading</div>
    </div>
</div>

<!-- Positions Table -->
<div class="data-section" style="margin-top: 16px;">
    <div class="section-header">
        <div class="section-title">Stock Positions</div>
        <div class="section-badge">{len(positions)} open</div>
    </div>
    <table class="data-table">
        <thead>
            <tr>
                <th>Symbol</th>
                <th>Quantity</th>
                <th>Entry Price</th>
                <th>Current Price</th>
                <th>Value</th>
                <th>P&L</th>
                <th>P&L %</th>
            </tr>
        </thead>
        <tbody>
'''
    
    if all_positions:
        for p in all_positions:
            pnl_class = "pnl-positive" if p['pnl'] >= 0 else "pnl-negative"
            html += f'''            <tr>
                <td class="ticker-cell">{p['ticker']}</td>
                <td>{p['qty']}</td>
                <td>${p['entry']:.2f}</td>
                <td>${p['current']:.2f}</td>
                <td>${p['value']:.2f}</td>
                <td class="{pnl_class}">${p['pnl']:+.2f}</td>
                <td class="{pnl_class}">{p['pnl_pct']:+.2f}%</td>
            </tr>
'''
    else:
        html += '''            <tr>
                <td colspan="7" style="text-align: center; padding: 40px; color: #6e7681;">
                    No active positions
                </td>
            </tr>
'''
    
    html += f'''        </tbody>
    </table>
</div>

<!-- Footer -->
<div class="footer">
    SmartBot 24/7 Trading System | Stocks: Cash Pot Mode 22-25% | Crypto: 15% positions | Combined Portfolio: ${combined_total:,.2f}
</div>

</div>
</body>
</html>'''
    
    return html

if __name__ == '__main__':
    html = generate_html()
    with open('/home/tradebot/status_dashboard.html', 'w') as f:
        f.write(html)
    print("✅ Professional Terminal Dashboard Generated")
