#!/usr/bin/env python3
"""
Professional SmartBot Dashboard Generator
"""
import json
import subprocess
import os
from datetime import datetime
import requests
import base64

def get_bot_status():
    """Check if auto_trader is running."""
    try:
        result = subprocess.run(['pgrep', '-f', 'auto_trader.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            return True, pids[0], len(pids)
        return False, None, 0
    except:
        return False, None, 0

def get_trading212_data():
    """Get real-time Trading212 account data."""
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
        try:
            cash_resp = requests.get(f"{base_url}/equity/account/cash", headers=headers, timeout=5)
            if cash_resp.status_code == 200:
                cash_data = cash_resp.json()
            else:
                cash_data = {'free': 0, 'total': 5000, 'ppl': 0}
        except:
            cash_data = {'free': 0, 'total': 5000, 'ppl': 0}
        
        # Get portfolio
        try:
            port_resp = requests.get(f"{base_url}/equity/portfolio", headers=headers, timeout=5)
            if port_resp.status_code == 200:
                positions = port_resp.json()
            else:
                positions = []
        except:
            positions = []
        
        return cash_data, positions
    except:
        return {'free': 0, 'total': 5000, 'ppl': 0}, []

def get_performance_history():
    """Get performance history."""
    try:
        with open('/home/tradebot/performance_history.json', 'r') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except:
        return []

def get_open_positions_file():
    """Get open positions from file."""
    try:
        with open('/home/tradebot/open_positions.json', 'r') as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except:
        return {}

def generate_html():
    """Generate professional dashboard HTML."""
    
    bot_running, pid, process_count = get_bot_status()
    cash_data, positions = get_trading212_data()
    perf_history = get_performance_history()
    
    total_balance = cash_data.get('total', 0)
    free_cash = cash_data.get('free', 0)
    ppl = cash_data.get('ppl', 0)
    position_count = len(positions)
    
    # Calculate position values
    position_value = sum(p.get('quantity', 0) * p.get('currentPrice', 0) for p in positions)
    deployed_pct = (position_value / total_balance * 100) if total_balance > 0 else 0
    
    # Stats
    total_trades = len(perf_history)
    winning_trades = sum(1 for t in perf_history if t.get('exit_profit', 0) > 0)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    # Recent trades
    recent_trades = perf_history[-10:] if perf_history else []
    recent_trades.reverse()
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta http-equiv="refresh" content="30">
<title>SmartBot Pro Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&family=Inter:wght@300;400;600;700;900&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',sans-serif;background:#050810;color:#e8eaed;overflow-x:hidden}}
.main-container{{max-width:2000px;margin:0 auto;padding:24px}}

/* Hero Header */
.hero{{background:linear-gradient(135deg,#667eea 0%,#764ba2 50%,#f093fb 100%);padding:48px;border-radius:20px;margin-bottom:32px;position:relative;overflow:hidden;box-shadow:0 20px 80px rgba(102,126,234,0.4)}}
.hero::before{{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(circle,rgba(255,255,255,0.1) 1px,transparent 1px);background-size:50px 50px;animation:gridMove 20s linear infinite}}
@keyframes gridMove{{to{{transform:translate(50px,50px)}}}}
.hero-content{{position:relative;z-index:1}}
.hero h1{{font-size:3.5em;font-weight:900;margin-bottom:12px;text-shadow:0 4px 20px rgba(0,0,0,0.3)}}
.hero-subtitle{{font-size:1.3em;opacity:0.95;margin-bottom:24px;font-weight:300}}
.status-pills{{display:flex;gap:16px;flex-wrap:wrap}}
.status-pill{{display:inline-flex;align-items:center;gap:10px;padding:12px 24px;border-radius:12px;font-weight:600;background:rgba(255,255,255,0.2);backdrop-filter:blur(20px);border:2px solid rgba(255,255,255,0.3);font-size:1em}}
.status-dot{{width:10px;height:10px;border-radius:50%;background:#00ff88;box-shadow:0 0 20px #00ff88;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:0.7;transform:scale(1.2)}}}}

/* Stats Grid */
.stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;margin-bottom:32px}}
.stat-card{{background:linear-gradient(135deg,#1a1d2e 0%,#16213e 100%);padding:36px;border-radius:16px;border:1px solid rgba(102,126,234,0.2);box-shadow:0 10px 40px rgba(0,0,0,0.4);position:relative;overflow:hidden;transition:all 0.3s}}
.stat-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,#667eea,#764ba2,#f093fb)}}
.stat-card:hover{{transform:translateY(-8px);box-shadow:0 20px 60px rgba(102,126,234,0.3)}}
.stat-label{{font-size:0.85em;text-transform:uppercase;letter-spacing:1.5px;color:#9ca3af;margin-bottom:12px;font-weight:600}}
.stat-value{{font-size:3.2em;font-weight:900;font-family:'Roboto Mono',monospace;line-height:1;margin-bottom:8px}}
.stat-change{{font-size:0.95em;opacity:0.8}}
.positive{{color:#00ff88}}
.negative{{color:#ff4757}}
.neutral{{color:#ffd93d}}
.info{{color:#6c5ce7}}

/* Data Grid */
.data-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(500px,1fr));gap:24px;margin-bottom:32px}}
.panel{{background:linear-gradient(135deg,#1a1d2e 0%,#16213e 100%);padding:32px;border-radius:16px;border:1px solid rgba(102,126,234,0.2);box-shadow:0 10px 40px rgba(0,0,0,0.4)}}
.panel-title{{font-size:1.5em;font-weight:700;margin-bottom:24px;color:#a78bfa;display:flex;align-items:center;gap:12px}}
.panel-title::before{{content:'';width:4px;height:28px;background:linear-gradient(180deg,#667eea,#764ba2);border-radius:2px}}

/* Table */
.data-table{{width:100%;border-collapse:separate;border-spacing:0 8px}}
.data-table thead th{{padding:12px 16px;text-align:left;font-size:0.8em;text-transform:uppercase;letter-spacing:1px;color:#9ca3af;font-weight:600;background:rgba(102,126,234,0.1);border-top:2px solid rgba(102,126,234,0.3)}}
.data-table thead th:first-child{{border-left:2px solid rgba(102,126,234,0.3);border-radius:8px 0 0 8px}}
.data-table thead th:last-child{{border-right:2px solid rgba(102,126,234,0.3);border-radius:0 8px 8px 0}}
.data-table tbody tr{{background:rgba(255,255,255,0.02);transition:all 0.2s}}
.data-table tbody tr:hover{{background:rgba(102,126,234,0.1);transform:scale(1.01)}}
.data-table td{{padding:16px;font-size:1.05em}}
.data-table td:first-child{{border-left:2px solid transparent;border-radius:8px 0 0 8px}}
.data-table td:last-child{{border-right:2px solid transparent;border-radius:0 8px 8px 0}}
.data-table tbody tr:hover td:first-child{{border-left-color:rgba(102,126,234,0.5)}}
.data-table tbody tr:hover td:last-child{{border-right-color:rgba(102,126,234,0.5)}}
.ticker-badge{{background:linear-gradient(135deg,#667eea,#764ba2);padding:6px 14px;border-radius:8px;font-weight:700;font-family:'Roboto Mono',monospace;font-size:1em}}

/* Trade Feed */
.trade-feed{{max-height:600px;overflow-y:auto;padding-right:8px}}
.trade-item{{background:rgba(255,255,255,0.02);padding:20px;margin-bottom:12px;border-radius:12px;border-left:4px solid #6c5ce7;transition:all 0.2s}}
.trade-item:hover{{background:rgba(102,126,234,0.08);transform:translateX(4px)}}
.trade-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}}
.trade-ticker{{font-size:1.3em;font-weight:700;font-family:'Roboto Mono',monospace}}
.trade-time{{font-size:0.85em;opacity:0.6}}
.trade-details{{font-size:0.95em;opacity:0.8;line-height:1.6}}
.buy-badge{{background:#00ff88;color:#000;padding:4px 12px;border-radius:6px;font-weight:700;font-size:0.85em;margin-right:8px}}
.sell-badge{{background:#ff4757;color:#fff;padding:4px 12px;border-radius:6px;font-weight:700;font-size:0.85em;margin-right:8px}}

/* Config Panel */
.config-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.config-item{{display:flex;justify-content:space-between;align-items:center;padding:16px;background:rgba(102,126,234,0.05);border-radius:10px;border:1px solid rgba(102,126,234,0.1)}}
.config-label{{font-size:0.95em;opacity:0.8}}
.config-value{{font-weight:700;font-size:1.1em;font-family:'Roboto Mono',monospace}}

/* Footer */
.footer{{text-align:center;padding:32px;opacity:0.5;font-size:0.9em}}

/* Scrollbar */
::-webkit-scrollbar{{width:8px}}
::-webkit-scrollbar-track{{background:#1a1d2e}}
::-webkit-scrollbar-thumb{{background:linear-gradient(180deg,#667eea,#764ba2);border-radius:4px}}

/* Responsive */
@media (max-width:768px){{
.hero h1{{font-size:2.5em}}
.stats-grid{{grid-template-columns:1fr}}
.data-grid{{grid-template-columns:1fr}}
.config-grid{{grid-template-columns:1fr}}
}}
</style>
</head>
<body>
<div class="main-container">

<!-- Hero Header -->
<div class="hero">
<div class="hero-content">
<h1>🤖 SmartBot Professional Terminal</h1>
<p class="hero-subtitle">Real-Time Algorithmic Trading System</p>
<div class="status-pills">
<div class="status-pill"><span class="status-dot"></span>{"LIVE TRADING" if bot_running else "OFFLINE"}</div>
<div class="status-pill">⚡ PID: {pid or "N/A"}</div>
<div class="status-pill">🔥 {process_count} Processes</div>
<div class="status-pill">⏱️ Updated: {datetime.now().strftime("%H:%M:%S")}</div>
</div>
</div>
</div>

<!-- Stats Grid -->
<div class="stats-grid">
<div class="stat-card">
<div class="stat-label">Total Balance</div>
<div class="stat-value positive">${total_balance:,.2f}</div>
<div class="stat-change">Trading212 Demo</div>
</div>
<div class="stat-card">
<div class="stat-label">Free Cash</div>
<div class="stat-value {"positive" if free_cash > 1000 else "negative"}">${free_cash:,.2f}</div>
<div class="stat-change">{deployed_pct:.1f}% Deployed</div>
</div>
<div class="stat-card">
<div class="stat-label">Open Positions</div>
<div class="stat-value info">{position_count}</div>
<div class="stat-change">Active Trades</div>
</div>
<div class="stat-card">
<div class="stat-label">Unrealized P&L</div>
<div class="stat-value {"positive" if ppl >= 0 else "negative"}">${ppl:,.2f}</div>
<div class="stat-change">{"Profit" if ppl >= 0 else "Loss"}</div>
</div>
</div>

<!-- Data Panels -->
<div class="data-grid">
<!-- Positions -->
<div class="panel">
<h2 class="panel-title">📦 Open Positions</h2>
{"<table class='data-table'><thead><tr><th>Ticker</th><th>Shares</th><th>Entry</th><th>Current</th><th>P&L</th></tr></thead><tbody>" + "".join([
    f"<tr><td><span class='ticker-badge'>{p['ticker'].replace('_US_EQ','')}</span></td><td>{p['quantity']:.0f}</td><td>${p.get('averagePrice', 0):.2f}</td><td>${p['currentPrice']:.2f}</td><td class='{'positive' if (p['currentPrice'] - p.get('averagePrice',0)) * p['quantity'] >= 0 else 'negative'}'><strong>${(p['currentPrice'] - p.get('averagePrice',0)) * p['quantity']:.2f}</strong></td></tr>"
    for p in positions
]) + "</tbody></table>" if positions else "<div style='text-align:center;opacity:0.5;padding:40px;'>No open positions</div>"}
</div>

<!-- Config -->
<div class="panel">
<h2 class="panel-title">⚙️ System Configuration</h2>
<div class="config-grid">
<div class="config-item"><span class="config-label">Confidence Threshold</span><span class="config-value neutral">35%</span></div>
<div class="config-item"><span class="config-label">Active Strategies</span><span class="config-value info">11</span></div>
<div class="config-item"><span class="config-label">Scan Frequency</span><span class="config-value info">3 min</span></div>
<div class="config-item"><span class="config-label">Risk Per Trade</span><span class="config-value neutral">15%</span></div>
<div class="config-item"><span class="config-label">Max Positions</span><span class="config-value info">15</span></div>
<div class="config-item"><span class="config-label">Total Trades</span><span class="config-value positive">{total_trades}</span></div>
<div class="config-item"><span class="config-label">Win Rate</span><span class="config-value {"positive" if win_rate >= 50 else "neutral"}">{win_rate:.1f}%</span></div>
<div class="config-item"><span class="config-label">Bot Status</span><span class="config-value {"positive" if bot_running else "negative"}">{"ACTIVE ✓" if bot_running else "OFFLINE"}</span></div>
</div>
</div>
</div>

<!-- Recent Activity -->
<div class="panel" style="margin-bottom:32px;">
<h2 class="panel-title">📊 Recent Trading Activity</h2>
<div class="trade-feed">
{"".join([
    f"<div class='trade-item'><div class='trade-header'><div class='trade-ticker'>{'🟢 BUY' if t.get('action','').upper() == 'BUY' else '🔴 SELL'} {t.get('ticker','N/A').replace('_US_EQ','')}</div><div class='trade-time'>{t.get('entry_time', 'N/A')[:16]}</div></div><div class='trade-details'>{t.get('quantity',0):.0f} shares @ ${t.get('entry_price',0):.2f} • Confidence: {t.get('confidence',0)*100:.0f}% • Strategy: {t.get('strategy','N/A')}</div></div>"
    for t in recent_trades
]) if recent_trades else "<div style='text-align:center;opacity:0.5;padding:40px;'>No recent trades</div>"}
</div>
</div>

<div class="footer">
<div>SmartBot v2.0 Professional • Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} GMT</div>
<div style="margin-top:8px;">Auto-refreshes every 30 seconds</div>
</div>

</div>
</body>
</html>'''
    
    return html

if __name__ == '__main__':
    html = generate_html()
    with open('/home/tradebot/status_dashboard.html', 'w') as f:
        f.write(html)
    print("✅ Professional dashboard generated!")
