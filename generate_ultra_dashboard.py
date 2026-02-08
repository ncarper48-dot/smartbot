#!/usr/bin/env python3
"""
Ultra Professional SmartBot Dashboard - CASH POT Edition
Modern, responsive, real-time trading dashboard
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
        print(f"API Error: {e}")
        return {'free': 0, 'total': 5000, 'ppl': 0}, []

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
    """Generate ultra professional dashboard HTML."""
    cash_data, positions = get_trading212_live_data()
    bot_running, pid = get_bot_status()
    
    # Calculate stats
    total = cash_data.get('total', 0)
    free = cash_data.get('free', 0)
    pnl_today = cash_data.get('ppl', 0)
    deployed = total - free
    deployed_pct = (deployed / total * 100) if total > 0 else 0
    
    # Separate winners/losers
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
            'pnl_pct': pnl_pct
        }
        
        if pnl >= 0:
            winners.append(pos_data)
        else:
            losers.append(pos_data)
    
    winners.sort(key=lambda x: x['pnl'], reverse=True)
    losers.sort(key=lambda x: x['pnl'])
    
    # Calculate targets
    target_daily = 500
    progress_pct = (pnl_today / target_daily * 100) if target_daily > 0 else 0
    remaining = max(0, target_daily - pnl_today)
    
    # Win rate
    win_rate = (len(winners) / len(positions) * 100) if positions else 0
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="10">
<title>SmartBot Cash Pot Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Inter:wght@300;400;600;700;900&display=swap" rel="stylesheet">
<style>
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: 'Inter', sans-serif;
    background: #0a0e27;
    color: #fff;
    overflow-x: hidden;
}}

.container {{
    max-width: 1800px;
    margin: 0 auto;
    padding: 24px;
}}

/* Animated Background */
.bg-animation {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: -1;
    background: radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(255, 121, 63, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 40% 80%, rgba(0, 255, 136, 0.05) 0%, transparent 50%);
    animation: float 15s ease-in-out infinite;
}}

@keyframes float {{
    0%, 100% {{ opacity: 0.3; }}
    50% {{ opacity: 0.6; }}
}}

/* Header */
.header {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 48px;
    border-radius: 24px;
    margin-bottom: 32px;
    box-shadow: 0 20px 80px rgba(102, 126, 234, 0.4);
    position: relative;
    overflow: hidden;
}}

.header::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url('data:image/svg+xml,<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg"><rect fill="rgba(255,255,255,0.03)" width="50" height="50"/></svg>');
    animation: slide 20s linear infinite;
}}

@keyframes slide {{
    0% {{ transform: translate(0, 0); }}
    100% {{ transform: translate(50px, 50px); }}
}}

.header-content {{
    position: relative;
    z-index: 1;
}}

.header h1 {{
    font-size: 3.5rem;
    font-weight: 900;
    margin-bottom: 12px;
    text-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}}

.header-subtitle {{
    font-size: 1.4rem;
    opacity: 0.95;
    font-weight: 300;
    margin-bottom: 24px;
}}

.status-bar {{
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
}}

.status-badge {{
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 12px 24px;
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(20px);
    border-radius: 12px;
    border: 2px solid rgba(255, 255, 255, 0.25);
    font-weight: 600;
    font-size: 1.05rem;
}}

.status-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: {"#00ff88" if bot_running else "#ff4757"};
    box-shadow: 0 0 20px {"#00ff88" if bot_running else "#ff4757"};
    animation: {"pulse 2s infinite" if bot_running else "none"};
}}

@keyframes pulse {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.6; transform: scale(1.3); }}
}}

/* Main Stats Grid */
.stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 24px;
    margin-bottom: 32px;
}}

.stat-card {{
    background: linear-gradient(135deg, #1e2139 0%, #1a1d2e 100%);
    padding: 32px;
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}

.stat-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
}}

.stat-card:hover {{
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4);
}}

.stat-label {{
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #9ca3af;
    margin-bottom: 12px;
    font-weight: 600;
}}

.stat-value {{
    font-size: 3.5rem;
    font-weight: 900;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1;
    margin-bottom: 8px;
}}

.stat-change {{
    font-size: 1rem;
    font-weight: 600;
}}

.positive {{ color: #00ff88; }}
.negative {{ color: #ff4757; }}
.neutral {{ color: #ffd93d; }}

/* Progress Bar */
.progress-container {{
    margin-top: 16px;
}}

.progress-bar {{
    height: 12px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    overflow: hidden;
    position: relative;
}}

.progress-fill {{
    height: 100%;
    background: linear-gradient(90deg, #00ff88, #00d9ff);
    border-radius: 6px;
    transition: width 0.5s ease;
    box-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
}}

.progress-text {{
    margin-top: 8px;
    font-size: 0.85rem;
    color: #9ca3af;
}}

/* Positions Grid */
.positions-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
    gap: 24px;
    margin-bottom: 32px;
}}

.panel {{
    background: linear-gradient(135deg, #1e2139 0%, #1a1d2e 100%);
    padding: 32px;
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}}

.panel-header {{
    font-size: 1.6rem;
    font-weight: 700;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 12px;
}}

.panel-header::before {{
    content: '';
    width: 4px;
    height: 32px;
    background: linear-gradient(180deg, #667eea, #764ba2);
    border-radius: 2px;
}}

/* Position List */
.position-list {{
    display: flex;
    flex-direction: column;
    gap: 12px;
}}

.position-item {{
    background: rgba(255, 255, 255, 0.02);
    padding: 20px;
    border-radius: 12px;
    border-left: 4px solid transparent;
    transition: all 0.2s;
}}

.position-item:hover {{
    background: rgba(255, 255, 255, 0.05);
    transform: translateX(4px);
}}

.position-item.winner {{
    border-left-color: #00ff88;
}}

.position-item.loser {{
    border-left-color: #ff4757;
}}

.position-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}}

.ticker {{
    font-size: 1.5rem;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
}}

.pnl {{
    font-size: 1.5rem;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
}}

.position-details {{
    display: flex;
    justify-content: space-between;
    font-size: 0.95rem;
    color: #9ca3af;
}}

.detail-item {{
    display: flex;
    flex-direction: column;
}}

.detail-label {{
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 4px;
}}

.detail-value {{
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    color: #fff;
}}

/* Empty State */
.empty-state {{
    text-align: center;
    padding: 48px 24px;
    color: #6b7280;
}}

.empty-icon {{
    font-size: 4rem;
    margin-bottom: 16px;
    opacity: 0.3;
}}

/* Footer */
.footer {{
    text-align: center;
    padding: 32px;
    color: #6b7280;
    font-size: 0.9rem;
}}

.footer-time {{
    font-family: 'JetBrains Mono', monospace;
    color: #9ca3af;
}}

/* Responsive */
@media (max-width: 768px) {{
    .header h1 {{ font-size: 2.5rem; }}
    .stats-grid {{ grid-template-columns: 1fr; }}
    .positions-grid {{ grid-template-columns: 1fr; }}
}}

/* Scrollbar */
::-webkit-scrollbar {{
    width: 10px;
}}

::-webkit-scrollbar-track {{
    background: #0a0e27;
}}

::-webkit-scrollbar-thumb {{
    background: linear-gradient(180deg, #667eea, #764ba2);
    border-radius: 5px;
}}

::-webkit-scrollbar-thumb:hover {{
    background: linear-gradient(180deg, #764ba2, #667eea);
}}
</style>
</head>
<body>
<div class="bg-animation"></div>
<div class="container">

<!-- Header -->
<div class="header">
    <div class="header-content">
        <h1>💰 SmartBot CASH POT Dashboard</h1>
        <p class="header-subtitle">Autonomous Trading System - Real-Time Performance</p>
        <div class="status-bar">
            <div class="status-badge">
                <span class="status-dot"></span>
                <span>{"🟢 LIVE TRADING" if bot_running else "🔴 OFFLINE"}</span>
            </div>
            <div class="status-badge">
                <span>🤖 PID: {pid or "N/A"}</span>
            </div>
            <div class="status-badge">
                <span>📊 {len(positions)} Positions</span>
            </div>
            <div class="status-badge">
                <span>🎯 Win Rate: {win_rate:.1f}%</span>
            </div>
        </div>
    </div>
</div>

<!-- Main Stats -->
<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-label">💵 Total Balance</div>
        <div class="stat-value">${total:,.2f}</div>
        <div class="stat-change neutral">Free: ${free:,.2f}</div>
    </div>
    
    <div class="stat-card">
        <div class="stat-label">📈 Today's P&L</div>
        <div class="stat-value {"positive" if pnl_today >= 0 else "negative"}">${pnl_today:+.2f}</div>
        <div class="stat-change neutral">Unrealized: ${total_unrealized:+.2f}</div>
    </div>
    
    <div class="stat-card">
        <div class="stat-label">🎯 Daily Target Progress</div>
        <div class="stat-value">{progress_pct:.1f}%</div>
        <div class="stat-change neutral">Target: $500 | Need: ${remaining:.2f}</div>
        <div class="progress-container">
            <div class="progress-bar">
                <div class="progress-fill" style="width: {min(progress_pct, 100):.1f}%"></div>
            </div>
            <div class="progress-text">${pnl_today:.2f} / $500.00</div>
        </div>
    </div>
    
    <div class="stat-card">
        <div class="stat-label">💎 Capital Deployed</div>
        <div class="stat-value">{deployed_pct:.1f}%</div>
        <div class="stat-change neutral">${deployed:,.2f} / ${total:,.2f}</div>
        <div class="progress-container">
            <div class="progress-bar">
                <div class="progress-fill" style="width: {deployed_pct:.1f}%"></div>
            </div>
        </div>
    </div>
</div>

<!-- Positions Grid -->
<div class="positions-grid">
    <!-- Winners -->
    <div class="panel">
        <div class="panel-header">🟢 Winning Positions ({len(winners)})</div>
        <div class="position-list">
'''
    
    if winners:
        for p in winners:
            html += f'''            <div class="position-item winner">
                <div class="position-header">
                    <span class="ticker">{p['ticker']}</span>
                    <span class="pnl positive">${p['pnl']:+.2f}</span>
                </div>
                <div class="position-details">
                    <div class="detail-item">
                        <span class="detail-label">Quantity</span>
                        <span class="detail-value">{p['qty']}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Entry</span>
                        <span class="detail-value">${p['entry']:.2f}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Current</span>
                        <span class="detail-value">${p['current']:.2f}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Gain</span>
                        <span class="detail-value positive">{p['pnl_pct']:+.2f}%</span>
                    </div>
                </div>
            </div>
'''
    else:
        html += '''            <div class="empty-state">
                <div class="empty-icon">📊</div>
                <p>No winning positions yet. Bot is hunting...</p>
            </div>
'''
    
    html += '''        </div>
    </div>
    
    <!-- Losers -->
    <div class="panel">
        <div class="panel-header">🔴 Losing Positions (''' + str(len(losers)) + ''')</div>
        <div class="position-list">
'''
    
    if losers:
        for p in losers:
            html += f'''            <div class="position-item loser">
                <div class="position-header">
                    <span class="ticker">{p['ticker']}</span>
                    <span class="pnl negative">${p['pnl']:.2f}</span>
                </div>
                <div class="position-details">
                    <div class="detail-item">
                        <span class="detail-label">Quantity</span>
                        <span class="detail-value">{p['qty']}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Entry</span>
                        <span class="detail-value">${p['entry']:.2f}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Current</span>
                        <span class="detail-value">${p['current']:.2f}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Loss</span>
                        <span class="detail-value negative">{p['pnl_pct']:.2f}%</span>
                    </div>
                </div>
            </div>
'''
    else:
        html += '''            <div class="empty-state">
                <div class="empty-icon">✨</div>
                <p>No losing positions! Perfect execution!</p>
            </div>
'''
    
    html += f'''        </div>
    </div>
</div>

<!-- Footer -->
<div class="footer">
    <p>🤖 SmartBot Autonomous Trading System</p>
    <p class="footer-time">Last Updated: {now} | Auto-refresh every 10 seconds</p>
    <p style="margin-top: 8px; font-size: 0.8rem;">CASH POT MODE: 22-25% positions | 1:1 profit targets | Auto-compound | Ultra aggressive</p>
</div>

</div>
</body>
</html>'''
    
    return html

if __name__ == '__main__':
    html = generate_html()
    with open('/home/tradebot/status_dashboard.html', 'w') as f:
        f.write(html)
    print("✅ Ultra Professional Dashboard Generated!")
    print("📊 View: file:///home/tradebot/status_dashboard.html")
