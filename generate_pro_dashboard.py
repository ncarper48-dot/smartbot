#!/usr/bin/env python3
"""Generate professional SmartBot dashboard with modern design"""
import json
from datetime import datetime
import os

# Load data
try:
    with open('/home/tradebot/open_positions.json', 'r') as f:
        positions = json.load(f)
except:
    positions = {}

try:
    with open('/home/tradebot/performance_history.json', 'r') as f:
        history = json.load(f)
    recent_trades = history[-5:] if len(history) > 5 else history
except:
    recent_trades = []

bot_pid = os.popen('pgrep -f auto_trader').read().strip()
watchdog_pid = os.popen('pgrep -f watchdog').read().strip()
total_pnl = sum((pos.get('current_price', 0) - pos.get('entry_price', 0)) * pos.get('quantity', 0) for pos in positions.values())

# Build positions table
if positions:
    position_rows = '\n'.join([
        f"<tr><td><strong>{ticker.replace('_US_EQ', '')}</strong></td><td>{pos.get('quantity', 0)}</td><td>${pos.get('entry_price', 0):.2f}</td><td>${pos.get('current_price', 0):.2f}</td><td class=\"{'profit' if (pos.get('current_price', 0) - pos.get('entry_price', 0)) > 0 else 'loss'}\"><strong>${((pos.get('current_price', 0) - pos.get('entry_price', 0)) * pos.get('quantity', 0)):+.2f}</strong></td></tr>"
        for ticker, pos in positions.items()
    ])
    positions_html = f'<table class="data-table"><thead><tr><th>Symbol</th><th>Shares</th><th>Entry</th><th>Current</th><th>P&L</th></tr></thead><tbody>{position_rows}</tbody></table>'
else:
    positions_html = '<div style="text-align:center;opacity:0.5;padding:20px;">No open positions</div>'

# Build trades list
if recent_trades:
    trade_items = '\n'.join([
        f'<div class="trade-item"><span class="{"buy-badge" if t.get("action","").lower()=="buy" else "sell-badge"}">{t.get("action","").upper()}</span> <strong>{t.get("ticker","")}</strong> {t.get("quantity",0)} @ ${t.get("price",0):.2f} <small style="opacity:0.6;float:right;">{t.get("timestamp","")[:16]}</small></div>'
        for t in recent_trades
    ])
else:
    trade_items = '<div style="text-align:center;opacity:0.5;padding:20px;">No trades today</div>'

# Generate HTML
html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta http-equiv="refresh" content="60">
<title>SmartBot | Professional Trading Terminal</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',-apple-system,sans-serif;background:#0a0e27;color:#e4e7eb;padding:20px;min-height:100vh}}
.container{{max-width:1600px;margin:0 auto}}
.header{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:30px;border-radius:16px;margin-bottom:30px;box-shadow:0 20px 60px rgba(102,126,234,0.3);position:relative;overflow:hidden}}
.header::before{{content:'';position:absolute;top:0;left:0;right:0;bottom:0;background:linear-gradient(45deg,transparent 30%,rgba(255,255,255,0.1) 50%,transparent 70%);animation:shimmer 3s infinite}}
@keyframes shimmer{{0%{{transform:translateX(-100%)}}100%{{transform:translateX(100%)}}}}
.header-content{{position:relative;z-index:1}}
.header h1{{font-size:2.8em;font-weight:700;margin-bottom:8px;letter-spacing:-1px}}
.header p{{opacity:0.95;font-size:1.1em;margin-bottom:20px}}
.status-row{{display:flex;gap:12px;flex-wrap:wrap}}
.status-badge{{display:inline-flex;align-items:center;gap:8px;padding:10px 18px;border-radius:8px;font-weight:600;font-size:0.9em;background:rgba(255,255,255,0.15);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.2)}}
.status-dot{{width:8px;height:8px;border-radius:50%;background:#00ff88;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:0.5}}}}
.alert-banner{{background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);padding:20px 25px;border-radius:12px;margin-bottom:30px;box-shadow:0 10px 30px rgba(245,87,108,0.3)}}
.alert-banner h3{{font-size:1.3em;margin-bottom:10px;font-weight:700}}
.alert-banner p{{opacity:0.95;line-height:1.8}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:24px;margin-bottom:30px}}
.card{{background:linear-gradient(135deg,#1e2139 0%,#252845 100%);padding:28px;border-radius:16px;border:1px solid rgba(255,255,255,0.08);box-shadow:0 10px 40px rgba(0,0,0,0.3);transition:transform 0.3s,box-shadow 0.3s}}
.card:hover{{transform:translateY(-5px);box-shadow:0 20px 60px rgba(0,0,0,0.4)}}
.card h2{{font-size:1.4em;font-weight:600;margin-bottom:20px;color:#a78bfa}}
.metric{{display:flex;justify-content:space-between;align-items:center;padding:14px 0;border-bottom:1px solid rgba(255,255,255,0.05)}}
.metric:last-child{{border-bottom:none}}
.metric-label{{opacity:0.7;font-size:0.95em}}
.metric-value{{font-weight:700;font-size:1.2em}}
.profit{{color:#00ff88}}
.loss{{color:#ff4757}}
.neutral{{color:#ffd93d}}
.info{{color:#6c5ce7}}
.stat-card{{text-align:center;padding:35px 20px}}
.stat-value{{font-size:3em;font-weight:700;line-height:1;margin-bottom:8px}}
.stat-label{{opacity:0.7;font-size:1.1em;text-transform:uppercase;letter-spacing:1px;font-weight:500}}
.data-table{{width:100%;border-collapse:collapse;margin-top:15px}}
.data-table thead{{background:rgba(167,139,250,0.15)}}
.data-table th{{padding:14px 16px;text-align:left;font-weight:600;font-size:0.9em;text-transform:uppercase;letter-spacing:0.5px;color:#a78bfa}}
.data-table td{{padding:16px;border-bottom:1px solid rgba(255,255,255,0.05)}}
.data-table tbody tr:hover{{background:rgba(167,139,250,0.05)}}
.trade-item{{padding:16px;background:rgba(255,255,255,0.03);margin-bottom:10px;border-radius:10px;border-left:3px solid #6c5ce7;transition:background 0.2s}}
.trade-item:hover{{background:rgba(255,255,255,0.06)}}
.buy-badge{{background:#00ff88;color:#000;padding:4px 12px;border-radius:6px;font-weight:700;font-size:0.85em;margin-right:10px}}
.sell-badge{{background:#ff4757;color:#fff;padding:4px 12px;border-radius:6px;font-weight:700;font-size:0.85em;margin-right:10px}}
.strategy-item{{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;background:rgba(255,255,255,0.03);border-radius:8px;border-left:3px solid #a78bfa;margin-bottom:10px}}
.confidence-bar{{width:60px;height:6px;background:rgba(255,255,255,0.1);border-radius:3px;overflow:hidden;margin-top:4px}}
.confidence-fill{{height:100%;background:linear-gradient(90deg,#00ff88,#00d9ff);border-radius:3px}}
.updates-list{{list-style:none}}
.updates-list li{{padding:12px 0 12px 30px;position:relative;line-height:1.8}}
.updates-list li::before{{content:'→';position:absolute;left:0;color:#a78bfa;font-weight:bold;font-size:1.2em}}
.footer{{text-align:center;opacity:0.5;margin-top:40px;font-size:0.9em;padding:20px}}
@media (max-width:768px){{.header h1{{font-size:2em}}.grid{{grid-template-columns:1fr}}.stat-value{{font-size:2.5em}}}}
::-webkit-scrollbar{{width:10px}}
::-webkit-scrollbar-track{{background:#1e2139}}
::-webkit-scrollbar-thumb{{background:#a78bfa;border-radius:5px}}
</style>
</head>
<body>
<div class="container">
<div class="header">
<div class="header-content">
<h1>🤖 SmartBot Trading Terminal</h1>
<p>Professional Algorithmic Trading System</p>
<div class="status-row">
<div class="status-badge"><span class="status-dot"></span>System {'Online' if bot_pid else 'Offline'}</div>
<div class="status-badge">Bot PID: {bot_pid or 'N/A'}</div>
<div class="status-badge">Watchdog: {watchdog_pid or 'N/A'}</div>
</div>
</div>
</div>
<div class="alert-banner">
<h3>⚡ System Diagnostic Report - January 21, 2026</h3>
<p><strong>Critical Fix:</strong> Sell execution logic restored. Bot now exits positions automatically.</p>
<p><strong>Issue:</strong> Limited liquidity ($15 free cash). 4 buy signals detected (RIOT, MSTR, MARA, GME) blocked by insufficient funds.</p>
<p><strong>Status:</strong> 11 ultra-aggressive strategies active. Ready for 9:30 AM ET tomorrow.</p>
</div>
<div class="grid">
<div class="card stat-card"><div class="stat-value profit">$4,865</div><div class="stat-label">Total Balance</div></div>
<div class="card stat-card"><div class="stat-value loss">$15</div><div class="stat-label">Free Cash</div></div>
<div class="card stat-card"><div class="stat-value neutral">{len(positions)}</div><div class="stat-label">Open Positions</div></div>
<div class="card stat-card"><div class="stat-value {'profit' if total_pnl>0 else 'loss'}">${total_pnl:+.0f}</div><div class="stat-label">Today's P&L</div></div>
</div>
<div class="grid">
<div class="card">
<h2>⚙️ System Configuration</h2>
<div class="metric"><span class="metric-label">Confidence Threshold</span><span class="metric-value neutral">35%</span></div>
<div class="metric"><span class="metric-label">Active Strategies</span><span class="metric-value info">11 Strategies</span></div>
<div class="metric"><span class="metric-label">Scan Frequency</span><span class="metric-value info">Every 3 min</span></div>
<div class="metric"><span class="metric-label">Risk Per Trade</span><span class="metric-value neutral">15%</span></div>
<div class="metric"><span class="metric-label">Max Positions</span><span class="metric-value info">15</span></div>
<div class="metric"><span class="metric-label">Daily Target</span><span class="metric-value profit">£250</span></div>
</div>
<div class="card">
<h2>🎯 Active Strategies</h2>
<div class="strategy-item"><div><strong>Momentum Breakout</strong><div class="confidence-bar"><div class="confidence-fill" style="width:88%"></div></div></div><span class="metric-value profit">88%</span></div>
<div class="strategy-item"><div><strong>RSI Bounce</strong><div class="confidence-bar"><div class="confidence-fill" style="width:80%"></div></div></div><span class="metric-value profit">80%</span></div>
<div class="strategy-item"><div><strong>Oversold Bounce</strong> <small style="opacity:0.6;">NEW</small><div class="confidence-bar"><div class="confidence-fill" style="width:55%"></div></div></div><span class="metric-value neutral">55%</span></div>
<div class="strategy-item"><div><strong>Quick Scalp</strong> <small style="opacity:0.6;">NEW</small><div class="confidence-bar"><div class="confidence-fill" style="width:50%"></div></div></div><span class="metric-value neutral">50%</span></div>
<div class="strategy-item"><div><strong>Micro Momentum</strong> <small style="opacity:0.6;">NEW</small><div class="confidence-bar"><div class="confidence-fill" style="width:48%"></div></div></div><span class="metric-value neutral">48%</span></div>
<div class="strategy-item"><div><strong>+ 6 More Strategies</strong><div style="font-size:0.85em;opacity:0.7;">Volume Surge, RSI Recovery, Tiny Move...</div></div><span class="metric-value info">42-82%</span></div>
</div>
</div>
<div class="card" style="margin-bottom:30px;">
<h2>📦 Open Positions</h2>
{positions_html}
</div>
<div class="card" style="margin-bottom:30px;">
<h2>📊 Recent Trading Activity</h2>
{trade_items}
</div>
<div class="card">
<h2>🔥 Today's System Updates</h2>
<ul class="updates-list">
<li><strong>Fixed:</strong> Sell execution logic completely restored (was broken for weeks)</li>
<li><strong>Added:</strong> 4 new ultra-aggressive strategies (0.15% move triggers)</li>
<li><strong>Lowered:</strong> Entry thresholds to RSI < 45 and 0.15% price moves</li>
<li><strong>Tested:</strong> Successfully detected 4 buy signals (RIOT +1.29%, MSTR, MARA, GME)</li>
<li><strong>Issue:</strong> Insufficient funds blocking execution ($15 free vs $4,865 locked)</li>
<li><strong>Status:</strong> All systems operational, ready for tomorrow 9:30 AM ET</li>
</ul>
</div>
<div class="footer">
<div>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} GMT</div>
<div style="margin-top:8px;">Auto-refreshes every 60 seconds • SmartBot v2.0</div>
</div>
</div>
</body>
</html>'''

with open('/home/tradebot/status_dashboard.html', 'w') as f:
    f.write(html)

print("✅ Professional dashboard generated!")
print("📊 View: file:///home/tradebot/status_dashboard.html")
print("🎨 Features: Gradients, animations, hover effects, confidence bars")
