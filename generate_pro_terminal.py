#!/usr/bin/env python3
"""
SmartBot V4 — Professional Trading Terminal
============================================
Bloomberg-grade dashboard with Brain Intelligence, P&L tracking,
trade history, and real-time position monitoring.
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
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('TRADING212_API_KEY')
        api_secret = os.getenv('TRADING212_API_SECRET')
        base_url = os.getenv('TRADING212_BASE_URL')
        auth_str = f"{api_key}:{api_secret}"
        encoded = base64.b64encode(auth_str.encode()).decode()
        headers = {'Authorization': f'Basic {encoded}', 'Content-Type': 'application/json'}

        cash_resp = requests.get(f"{base_url}/equity/account/cash", headers=headers, timeout=5)
        cash_data = cash_resp.json() if cash_resp.status_code == 200 else {}

        port_resp = requests.get(f"{base_url}/equity/portfolio", headers=headers, timeout=5)
        positions = port_resp.json() if port_resp.status_code == 200 else []

        orders_resp = requests.get(f"{base_url}/equity/orders", headers=headers, timeout=5)
        orders = orders_resp.json() if orders_resp.status_code == 200 else []

        return cash_data, positions, orders
    except Exception as e:
        print(f"Error getting live data: {e}")
        return {}, [], []


def get_bot_status():
    """Check if bot and watchdog are running."""
    try:
        r1 = subprocess.run(['pgrep', '-f', 'auto_trader.py'], capture_output=True, text=True)
        r2 = subprocess.run(['pgrep', '-f', 'watchdog.sh'], capture_output=True, text=True)
        bot_running = r1.returncode == 0
        wd_running = r2.returncode == 0
        pid = r1.stdout.strip().split('\n')[0] if bot_running else None
        return bot_running, wd_running, pid
    except:
        return False, False, None


def get_brain_data():
    """Load brain intelligence data."""
    try:
        with open('/home/tradebot/smartbot_brain.json') as f:
            return json.load(f)
    except:
        return {}


def get_performance_data():
    """Load performance history."""
    try:
        with open('/home/tradebot/performance_history.json') as f:
            return json.load(f)
    except:
        return {"trades": [], "total_pnl": 0, "total_trades": 0}


def get_overnight_data():
    """Load overnight intelligence."""
    try:
        with open('/home/tradebot/overnight_watchlist.json') as f:
            return json.load(f)
    except:
        return {}


def get_uk_time():
    """Get current UK time string."""
    try:
        import pytz
        uk = pytz.timezone('Europe/London')
        return datetime.now(uk).strftime('%H:%M:%S')
    except:
        return datetime.now().strftime('%H:%M:%S')


def get_et_time():
    """Get current ET time string."""
    try:
        import pytz
        et = pytz.timezone('America/New_York')
        return datetime.now(et).strftime('%H:%M ET')
    except:
        return ""


def generate_html():
    """Generate professional V4 dashboard."""
    cash_data, positions, pending_orders = get_trading212_live_data()
    bot_running, wd_running, pid = get_bot_status()
    brain = get_brain_data()
    perf = get_performance_data()
    overnight = get_overnight_data()

    # ── Account metrics ──
    total = cash_data.get('total', 0)
    free = cash_data.get('free', 0)
    invested = cash_data.get('invested', 0)
    blocked = cash_data.get('blocked', 0)
    realized = cash_data.get('result', 0)
    open_pnl = cash_data.get('ppl', 0)
    net_pnl = realized + open_pnl

    # ── Position analysis ──
    pos_data = []
    winners_count = 0
    losers_count = 0
    total_unrealized = 0

    for p in positions:
        ticker = p.get('ticker', '').replace('_US_EQ', '')
        qty = p.get('quantity', 0)
        entry = p.get('averagePrice', 0)
        current = p.get('currentPrice', 0)
        ppl = p.get('ppl', 0)
        pct = ((current - entry) / entry * 100) if entry > 0 else 0
        total_unrealized += ppl
        if ppl >= 0:
            winners_count += 1
        else:
            losers_count += 1

        # Brain data for each position
        tm = brain.get('ticker_memory', {}).get(ticker, {})
        brain_wr = tm.get('wins', 0) / max(tm.get('total_trades', 1), 1) * 100 if tm.get('total_trades', 0) > 0 else 0
        brain_trades = tm.get('total_trades', 0)

        pos_data.append({
            'ticker': ticker, 'qty': qty, 'entry': entry, 'current': current,
            'ppl': ppl, 'pct': pct, 'value': current * qty,
            'brain_wr': brain_wr, 'brain_trades': brain_trades,
        })

    pos_data.sort(key=lambda x: x['ppl'], reverse=True)

    # ── Brain intelligence ──
    brain_trades_learned = brain.get('total_trades_learned', 0)
    brain_tickers = len(brain.get('ticker_memory', {}))
    brain_factors = len(brain.get('factor_memory', {}))
    ap = brain.get('adaptive_params', {})
    brain_boost = ap.get('confidence_boost_tickers', {})
    brain_penalty = ap.get('confidence_penalty_tickers', {})
    best_factors = ap.get('best_factors', [])[:6]
    worst_factors = ap.get('worst_factors', [])[:6]
    optimal_score = ap.get('optimal_score_min', 50)

    if brain_trades_learned >= 500:
        brain_level, brain_color = "EXPERT", "#3fb950"
    elif brain_trades_learned >= 100:
        brain_level, brain_color = "HIGH", "#58a6ff"
    elif brain_trades_learned >= 30:
        brain_level, brain_color = "MEDIUM", "#e3b341"
    else:
        brain_level, brain_color = "LOW", "#f85149"

    # ── Brain ticker rankings ──
    tm_all = brain.get('ticker_memory', {})
    ticker_rankings = []
    for t, stats in tm_all.items():
        if stats.get('total_trades', 0) >= 3:
            wr = stats['wins'] / max(stats['total_trades'], 1) * 100
            ticker_rankings.append({
                'ticker': t, 'wr': wr, 'trades': stats['total_trades'],
                'avg_pnl': stats.get('avg_pnl', 0), 'best': stats.get('best_trade', 0),
            })
    ticker_rankings.sort(key=lambda x: x['avg_pnl'], reverse=True)

    # ── Trade history ──
    trades = perf.get('trades', [])
    sell_trades = [t for t in trades if t.get('action') in ('sell', 'sell_partial')]
    recent_sells = sell_trades[-15:][::-1]
    total_realized_pnl = perf.get('total_pnl', 0)

    # ── Overnight intelligence ──
    overnight_ts = overnight.get('timestamp', '')
    overnight_age = ''
    if overnight_ts:
        try:
            age_sec = (datetime.now() - datetime.fromisoformat(overnight_ts)).total_seconds()
            if age_sec < 3600:
                overnight_age = f'{int(age_sec / 60)}m ago'
            elif age_sec < 86400:
                overnight_age = f'{int(age_sec / 3600)}h ago'
            else:
                overnight_age = 'stale'
        except:
            overnight_age = ''

    # ── Time / Market status ──
    uk_time = get_uk_time()
    et_time = get_et_time()
    date_str = datetime.now().strftime('%a %d %b %Y')

    try:
        import pytz
        now_et = datetime.now(pytz.timezone('America/New_York'))
        is_weekday = now_et.weekday() < 5
        is_market_open = is_weekday and 9 * 60 + 30 <= now_et.hour * 60 + now_et.minute <= 16 * 60
        market_status = "OPEN" if is_market_open else "CLOSED"
        market_color = "#3fb950" if is_market_open else "#f85149"
    except:
        market_status = "UNKNOWN"
        market_color = "#8b949e"

    # ─────────────────── BUILD HTML ───────────────────
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="10">
<title>SmartBot V4 Terminal</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{
  font-family:'Inter',-apple-system,system-ui,sans-serif;
  background:#080b10;color:#c5cdd9;line-height:1.5;min-height:100vh;
}}
.terminal{{max-width:1600px;margin:0 auto;padding:16px;}}

/* ─── HEADER ─── */
.header{{
  background:linear-gradient(135deg,#0f1520 0%,#141d2b 100%);
  border:1px solid #1c2636;border-radius:10px;
  padding:16px 24px;margin-bottom:12px;
  display:flex;justify-content:space-between;align-items:center;
}}
.h-left{{display:flex;align-items:center;gap:16px;}}
.logo{{
  width:44px;height:44px;border-radius:12px;
  background:linear-gradient(135deg,#0969da 0%,#2ea043 100%);
  display:grid;place-items:center;font-size:22px;
  box-shadow:0 0 24px rgba(9,105,218,0.35);
}}
.brand-name{{font-size:1.15rem;font-weight:800;color:#f0f4f8;letter-spacing:2px;}}
.brand-ver{{font-size:0.68rem;color:#4a5f78;font-family:'JetBrains Mono',monospace;letter-spacing:0.5px;}}
.h-status{{display:flex;gap:12px;align-items:center;flex-wrap:wrap;}}
.pill{{
  display:flex;align-items:center;gap:6px;
  padding:4px 12px;border-radius:20px;
  font-size:0.7rem;font-weight:600;
  font-family:'JetBrains Mono',monospace;
  text-transform:uppercase;letter-spacing:0.5px;
}}
.pill-live{{
  background:{"rgba(46,160,67,0.12)" if bot_running else "rgba(248,81,73,0.12)"};
  color:{"#3fb950" if bot_running else "#f85149"};
  border:1px solid {"rgba(46,160,67,0.3)" if bot_running else "rgba(248,81,73,0.3)"};
}}
.pill-dot{{
  width:7px;height:7px;border-radius:50%;
  background:{"#3fb950" if bot_running else "#f85149"};
  {"animation:pulse 2s infinite;" if bot_running else ""}
}}
.pill-market{{
  background:rgba({"46,160,67" if market_status=="OPEN" else "248,81,73"},0.08);
  color:{market_color};
  border:1px solid rgba({"46,160,67" if market_status=="OPEN" else "248,81,73"},0.2);
}}
.pill-brain{{
  background:rgba(88,166,255,0.1);color:{brain_color};
  border:1px solid rgba(88,166,255,0.25);
}}
.pill-wd{{
  background:{"rgba(46,160,67,0.08)" if wd_running else "rgba(248,81,73,0.08)"};
  color:{"#3fb950" if wd_running else "#f85149"};
  border:1px solid {"rgba(46,160,67,0.2)" if wd_running else "rgba(248,81,73,0.2)"};
}}
.h-right{{
  display:flex;gap:14px;align-items:center;
  font-family:'JetBrains Mono',monospace;font-size:0.76rem;color:#4a5f78;
}}
.time-uk{{color:#f0f4f8;font-weight:600;}}
@keyframes pulse{{0%,100%{{opacity:1;}}50%{{opacity:0.3;}}}}

/* ─── METRIC CARDS ─── */
.metrics{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:12px;}}
.card{{
  background:#0f1520;border:1px solid #1c2636;border-radius:8px;
  padding:14px 16px;position:relative;overflow:hidden;
  transition:border-color 0.2s;
}}
.card:hover{{border-color:#2a3a50;}}
.card::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;}}
.acc-green::before{{background:linear-gradient(90deg,#2ea043,#3fb950);}}
.acc-blue::before{{background:linear-gradient(90deg,#0969da,#58a6ff);}}
.acc-orange::before{{background:linear-gradient(90deg,#d29922,#e3b341);}}
.acc-red::before{{background:linear-gradient(90deg,#da3633,#f85149);}}
.acc-purple::before{{background:linear-gradient(90deg,#8957e5,#a371f7);}}
.card-label{{
  font-size:0.66rem;text-transform:uppercase;letter-spacing:0.8px;
  color:#4a5f78;font-weight:600;margin-bottom:6px;
}}
.card-value{{
  font-size:1.55rem;font-weight:700;
  font-family:'JetBrains Mono',monospace;
  line-height:1.2;margin-bottom:3px;color:#f0f4f8;
}}
.card-sub{{font-size:0.7rem;color:#4a5f78;font-family:'JetBrains Mono',monospace;}}
.green{{color:#3fb950!important;}}
.red{{color:#f85149!important;}}
.blue{{color:#58a6ff!important;}}
.yellow{{color:#e3b341!important;}}

/* ─── LAYOUT ─── */
.two-col{{display:grid;grid-template-columns:5fr 3fr;gap:12px;margin-bottom:12px;}}
.three-col{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:12px;}}

/* ─── PANELS ─── */
.panel{{background:#0f1520;border:1px solid #1c2636;border-radius:8px;overflow:hidden;}}
.panel-head{{
  padding:12px 16px;border-bottom:1px solid #182130;
  display:flex;justify-content:space-between;align-items:center;
}}
.panel-title{{
  font-size:0.82rem;font-weight:700;color:#f0f4f8;
  display:flex;align-items:center;gap:8px;
}}
.panel-badge{{
  font-size:0.66rem;padding:3px 10px;
  background:#141d2b;border-radius:12px;
  font-family:'JetBrains Mono',monospace;color:#4a5f78;font-weight:500;
}}

/* ─── TABLE ─── */
table{{width:100%;border-collapse:collapse;}}
thead{{background:#0b1018;}}
th{{
  padding:9px 14px;text-align:left;
  font-size:0.66rem;font-weight:600;color:#4a5f78;
  text-transform:uppercase;letter-spacing:0.6px;
  border-bottom:1px solid #182130;
}}
td{{
  padding:10px 14px;font-size:0.78rem;
  border-bottom:1px solid #131c28;
  font-family:'JetBrains Mono',monospace;
}}
tbody tr{{transition:background 0.15s;}}
tbody tr:hover{{background:#0b1018;}}
tbody tr:last-child td{{border-bottom:none;}}
.tk{{font-weight:700;color:#f0f4f8;}}
.up{{color:#3fb950;font-weight:600;}}
.dn{{color:#f85149;font-weight:600;}}

/* ─── BRAIN STYLES ─── */
.brain-row{{
  display:flex;justify-content:space-between;align-items:center;
  padding:5px 0;font-size:0.76rem;
  font-family:'JetBrains Mono',monospace;
  border-bottom:1px solid #131c28;
}}
.brain-row:last-child{{border-bottom:none;}}
.tag{{
  display:inline-block;padding:2px 8px;border-radius:4px;
  font-size:0.68rem;font-family:'JetBrains Mono',monospace;
  font-weight:500;margin:2px 3px 2px 0;
}}
.tag-g{{background:rgba(46,160,67,0.12);color:#3fb950;border:1px solid rgba(46,160,67,0.25);}}
.tag-r{{background:rgba(248,81,73,0.1);color:#f85149;border:1px solid rgba(248,81,73,0.2);}}

/* ─── OVERNIGHT ─── */
.ov-row{{
  display:flex;justify-content:space-between;
  padding:4px 0;font-size:0.74rem;
  font-family:'JetBrains Mono',monospace;
  border-bottom:1px solid #131c28;
}}
.ov-row:last-child{{border-bottom:none;}}
.edge-bar{{display:flex;align-items:center;gap:6px;margin-bottom:3px;font-size:0.74rem;font-family:'JetBrains Mono',monospace;}}
.edge-track{{height:5px;border-radius:3px;flex:1;background:#182130;overflow:hidden;}}
.edge-fill{{height:100%;border-radius:3px;}}

/* ─── FOOTER ─── */
.footer{{
  margin-top:12px;padding:12px;text-align:center;
  font-size:0.68rem;color:#2e3d50;
  font-family:'JetBrains Mono',monospace;
  border-top:1px solid #1c2636;
}}

/* ─── SCROLLBAR ─── */
::-webkit-scrollbar{{width:7px;}}
::-webkit-scrollbar-track{{background:#080b10;}}
::-webkit-scrollbar-thumb{{background:#1c2636;border-radius:4px;}}
::-webkit-scrollbar-thumb:hover{{background:#2a3a50;}}

/* ─── RESPONSIVE ─── */
@media(max-width:1400px){{
  .metrics{{grid-template-columns:repeat(3,1fr);}}
  .two-col,.three-col{{grid-template-columns:1fr;}}
}}
@media(max-width:768px){{
  .metrics{{grid-template-columns:1fr 1fr;}}
  .header{{flex-direction:column;gap:12px;align-items:flex-start;}}
  .h-status{{flex-wrap:wrap;}}
}}
</style>
</head>
<body>
<div class="terminal">

<!-- ════════ HEADER ════════ -->
<div class="header">
  <div class="h-left">
    <div class="logo">🤖</div>
    <div>
      <div class="brand-name">SMARTBOT</div>
      <div class="brand-ver">V4 ARMED · Brain Intelligence · Live Trading</div>
    </div>
  </div>
  <div class="h-status">
    <div class="pill pill-live"><span class="pill-dot"></span>{"LIVE" if bot_running else "OFFLINE"}{f" · PID {pid}" if pid else ""}</div>
    <div class="pill pill-market">MKT {market_status}</div>
    <div class="pill pill-brain">🧠 {brain_level} · {brain_trades_learned}T</div>
    <div class="pill pill-wd">🛡️ {"WD ON" if wd_running else "WD OFF"}</div>
  </div>
  <div class="h-right">
    <span>{date_str}</span>
    <span class="time-uk">🇬🇧 {uk_time}</span>
    <span>{et_time}</span>
  </div>
</div>

<!-- ════════ TOP METRICS ════════ -->
<div class="metrics">
  <div class="card acc-blue">
    <div class="card-label">Total Balance</div>
    <div class="card-value">${total:,.2f}</div>
    <div class="card-sub">Free ${free:,.2f} · Inv ${invested:,.2f}</div>
  </div>
  <div class="card acc-{"green" if realized >= 0 else "red"}">
    <div class="card-label">Realized P&amp;L</div>
    <div class="card-value {"green" if realized >= 0 else "red"}">${realized:+,.2f}</div>
    <div class="card-sub">Closed trade profits</div>
  </div>
  <div class="card acc-{"green" if open_pnl >= 0 else "red"}">
    <div class="card-label">Open P&amp;L</div>
    <div class="card-value {"green" if open_pnl >= 0 else "red"}">${open_pnl:+,.2f}</div>
    <div class="card-sub">{len(positions)} pos · {winners_count}W {losers_count}L</div>
  </div>
  <div class="card acc-{"green" if net_pnl >= 0 else "red"}">
    <div class="card-label">Net P&amp;L</div>
    <div class="card-value {"green" if net_pnl >= 0 else "red"}">${net_pnl:+,.2f}</div>
    <div class="card-sub">ROI {(net_pnl / max(total - net_pnl, 1) * 100):+.1f}%</div>
  </div>
  <div class="card acc-{"orange" if blocked > 1 else "purple"}">
    <div class="card-label">Capital Status</div>
    <div class="card-value {"yellow" if blocked > 1 else ""}">${blocked:,.2f}</div>
    <div class="card-sub">{len(pending_orders)} pending order{"s" if len(pending_orders) != 1 else ""}</div>
  </div>
</div>

<!-- ════════ POSITIONS + BRAIN ════════ -->
<div class="two-col">

<!-- POSITIONS TABLE -->
<div class="panel">
  <div class="panel-head">
    <div class="panel-title">📊 Live Positions</div>
    <div class="panel-badge">{len(positions)} open · ${total_unrealized:+,.2f}</div>
  </div>
  <table>
    <thead><tr>
      <th>Symbol</th><th>Qty</th><th>Entry</th><th>Current</th><th>Value</th><th>P&amp;L</th><th>%</th><th>Brain WR</th>
    </tr></thead>
    <tbody>'''

    if pos_data:
        for p in pos_data:
            pc = "up" if p['ppl'] >= 0 else "dn"
            bwr_c = "green" if p['brain_wr'] >= 55 else ("red" if p['brain_wr'] < 40 else "")
            html += f'''
      <tr>
        <td class="tk">{p['ticker']}</td>
        <td>{p['qty']:.2f}</td>
        <td>${p['entry']:.2f}</td>
        <td>${p['current']:.2f}</td>
        <td>${p['value']:.2f}</td>
        <td class="{pc}">${p['ppl']:+.2f}</td>
        <td class="{pc}">{p['pct']:+.1f}%</td>
        <td class="{bwr_c}">{p['brain_wr']:.0f}% <span style="color:#4a5f78">({p['brain_trades']}T)</span></td>
      </tr>'''
    else:
        html += '''
      <tr><td colspan="8" style="text-align:center;padding:28px;color:#2e3d50">No active positions</td></tr>'''

    html += '''
    </tbody>
  </table>
</div>

<!-- BRAIN INTELLIGENCE PANEL -->
<div class="panel">
  <div class="panel-head">
    <div class="panel-title">🧠 Brain Intelligence</div>'''

    html += f'''
    <div class="panel-badge" style="color:{brain_color}">{brain_level} · {brain_trades_learned} trades</div>
  </div>
  <div style="padding:14px 16px;">

    <!-- Optimal entry score -->
    <div style="margin-bottom:14px;">
      <div class="card-label" style="margin-bottom:6px;">Optimal Entry Score</div>
      <div style="display:flex;align-items:center;gap:10px;">
        <div style="flex:1;height:7px;background:#182130;border-radius:4px;overflow:hidden;">
          <div style="height:100%;width:{min(optimal_score, 100)}%;background:linear-gradient(90deg,#f85149,#e3b341,#3fb950);border-radius:4px;"></div>
        </div>
        <span style="font-family:'JetBrains Mono',monospace;font-size:0.85rem;font-weight:700;color:#f0f4f8;">≥{optimal_score}</span>
      </div>
    </div>

    <!-- Core stats -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:14px;">
      <div style="background:#0b1018;border-radius:6px;padding:10px;text-align:center;">
        <div style="font-size:1.1rem;font-weight:700;font-family:'JetBrains Mono',monospace;color:#58a6ff;">{brain_tickers}</div>
        <div style="font-size:0.64rem;color:#4a5f78;text-transform:uppercase;">Tickers</div>
      </div>
      <div style="background:#0b1018;border-radius:6px;padding:10px;text-align:center;">
        <div style="font-size:1.1rem;font-weight:700;font-family:'JetBrains Mono',monospace;color:#a371f7;">{brain_factors}</div>
        <div style="font-size:0.64rem;color:#4a5f78;text-transform:uppercase;">Factors</div>
      </div>
    </div>

    <!-- Boosted tickers -->
    <div class="card-label" style="margin-bottom:6px;">🚀 Boosted</div>'''

    if brain_boost:
        for t, mult in sorted(brain_boost.items(), key=lambda x: x[1], reverse=True):
            html += f'\n    <div class="brain-row"><span class="green">{t}</span><span class="green">x{mult:.2f}</span></div>'
    else:
        html += '\n    <div class="brain-row"><span style="color:#2e3d50">None yet</span><span></span></div>'

    html += '\n\n    <!-- Penalized tickers -->\n    <div class="card-label" style="margin-top:12px;margin-bottom:6px;">⛔ Blocked</div>'

    if brain_penalty:
        for t, mult in sorted(brain_penalty.items(), key=lambda x: x[1]):
            html += f'\n    <div class="brain-row"><span class="red">{t}</span><span class="red">x{mult:.2f}</span></div>'
    else:
        html += '\n    <div class="brain-row"><span style="color:#2e3d50">None yet</span><span></span></div>'

    # Best and worst factors
    html += '\n\n    <!-- Factors -->\n    <div class="card-label" style="margin-top:12px;margin-bottom:6px;">✅ Best Factors</div>\n    <div style="margin-bottom:8px;">'
    if best_factors:
        for f in best_factors:
            html += f'<span class="tag tag-g">{f}</span>'
    else:
        html += '<span style="color:#2e3d50;font-size:0.72rem;">Training needed</span>'

    html += '</div>\n    <div class="card-label" style="margin-bottom:6px;">❌ Worst Factors</div>\n    <div>'
    if worst_factors:
        for f in worst_factors:
            html += f'<span class="tag tag-r">{f}</span>'
    else:
        html += '<span style="color:#2e3d50;font-size:0.72rem;">Training needed</span>'

    html += '''</div>

  </div>
</div>

</div>

<!-- ════════ TICKER RANKINGS + TRADE HISTORY ════════ -->
<div class="two-col">

<!-- BRAIN TICKER RANKINGS -->
<div class="panel">
  <div class="panel-head">
    <div class="panel-title">🏆 Brain Ticker Rankings</div>'''

    html += f'''
    <div class="panel-badge">{brain_tickers} profiled · sorted by avg P&amp;L</div>
  </div>
  <table>
    <thead><tr>
      <th>#</th><th>Ticker</th><th>Win Rate</th><th>Trades</th><th>Avg P&amp;L</th><th>Best</th><th>Status</th>
    </tr></thead>
    <tbody>'''

    for i, tr in enumerate(ticker_rankings[:14]):
        wr_cls = "up" if tr['wr'] >= 50 else "dn"
        pnl_cls = "up" if tr['avg_pnl'] >= 0 else "dn"
        if tr['ticker'] in brain_boost:
            status = '<span class="green">🟢 BOOST</span>'
        elif tr['ticker'] in brain_penalty:
            status = '<span class="red">🔴 BLOCK</span>'
        else:
            status = '<span style="color:#4a5f78">⚪ NEUTRAL</span>'
        html += f'''
      <tr>
        <td style="color:#4a5f78">{i + 1}</td>
        <td class="tk">{tr['ticker']}</td>
        <td class="{wr_cls}">{tr['wr']:.0f}%</td>
        <td>{tr['trades']}</td>
        <td class="{pnl_cls}">${tr['avg_pnl']:+.3f}</td>
        <td class="up">${tr['best']:+.2f}</td>
        <td>{status}</td>
      </tr>'''

    if not ticker_rankings:
        html += '<tr><td colspan="7" style="text-align:center;padding:28px;color:#2e3d50">Needs more training data</td></tr>'

    html += '''
    </tbody>
  </table>
</div>

<!-- RECENT TRADE HISTORY -->
<div class="panel">
  <div class="panel-head">
    <div class="panel-title">📜 Trade History</div>'''

    html += f'''
    <div class="panel-badge">{len(sell_trades)} closed · ${total_realized_pnl:+,.2f}</div>
  </div>
  <table>
    <thead><tr>
      <th>Time</th><th>Ticker</th><th>Action</th><th>Qty</th><th>Price</th><th>P&amp;L</th>
    </tr></thead>
    <tbody>'''

    for t in recent_sells:
        ts = t.get('timestamp', '')[:16].replace('T', ' ')
        tkr = t.get('ticker', '').replace('_US_EQ', '')
        act = t.get('action', '').upper()
        qty = t.get('quantity', 0)
        price = t.get('price', 0)
        pnl = t.get('pnl', 0)
        if pnl == 0:
            meta_pnl = t.get('meta', {}).get('pnl')
            if meta_pnl:
                try:
                    pnl = float(meta_pnl)
                except:
                    pass
        pc = "up" if pnl > 0 else ("dn" if pnl < 0 else "")
        html += f'''
      <tr>
        <td style="color:#4a5f78;font-size:0.7rem;">{ts}</td>
        <td class="tk">{tkr}</td>
        <td>{act}</td>
        <td>{qty}</td>
        <td>${price:.2f}</td>
        <td class="{pc}">${pnl:+.2f}</td>
      </tr>'''

    if not recent_sells:
        html += '<tr><td colspan="6" style="text-align:center;padding:28px;color:#2e3d50">No closed trades yet</td></tr>'

    html += '''
    </tbody>
  </table>
</div>

</div>'''

    # ═══════ OVERNIGHT INTELLIGENCE ═══════
    global_mkts = overnight.get('global_markets', {})
    sector_rot = overnight.get('sector_rotation', {})
    watchlist = overnight.get('watchlist', [])

    html += f'''

<!-- ════════ OVERNIGHT INTELLIGENCE ════════ -->
<div class="panel" style="margin-bottom:10px;">
  <div class="panel-head">
    <div class="panel-title">🌙 Overnight Intelligence</div>
    <div class="panel-badge">{overnight_age if overnight_age else "no data"}</div>
  </div>
</div>
<div class="three-col">'''

    # Global Markets
    html += '\n<div class="panel">\n  <div style="padding:14px 16px;">\n    <div class="card-label" style="margin-bottom:8px;">🌍 Global Markets</div>'
    key_indices = ['ES=F', 'NQ=F', '^FTSE', '^GDAXI', '^N225', '^HSI', '^VIX', 'GC=F', 'CL=F', 'BTC-USD']
    for sym in key_indices:
        gd = global_mkts.get(sym, {})
        if not gd:
            continue
        chg = gd.get('chg_1d', 0)
        color = '#3fb950' if chg >= 0 else '#f85149'
        name = gd.get('name', sym)[:22]
        html += f'\n    <div class="ov-row"><span>{name}</span><span style="color:{color};font-weight:600">{chg:+.2f}%</span></div>'
    if not global_mkts:
        html += '\n    <div class="ov-row" style="color:#2e3d50">Run overnight analysis</div>'
    html += '\n  </div>\n</div>'

    # Sector Rotation
    html += '\n<div class="panel">\n  <div style="padding:14px 16px;">\n    <div class="card-label" style="margin-bottom:8px;">📊 Sector Rotation</div>'
    sectors_sorted = sorted(sector_rot.items(), key=lambda x: x[1].get('chg_1d', 0), reverse=True)
    for etf, sd in sectors_sorted:
        chg = sd.get('chg_1d', 0)
        color = '#3fb950' if chg >= 0 else '#f85149'
        name = sd.get('name', etf)[:22]
        html += f'\n    <div class="ov-row"><span>{name}</span><span style="color:{color};font-weight:600">{chg:+.2f}%</span></div>'
    if not sector_rot:
        html += '\n    <div class="ov-row" style="color:#2e3d50">Run overnight analysis</div>'
    html += '\n  </div>\n</div>'

    # Edge Watchlist
    html += '\n<div class="panel">\n  <div style="padding:14px 16px;">\n    <div class="card-label" style="margin-bottom:8px;">🎯 Edge Watchlist</div>'
    for w in watchlist[:8]:
        edge = w.get('edge_score', 0)
        sym = w.get('symbol', '?')
        rec = w.get('recommendation', '')
        if edge >= 25:
            color = '#3fb950'
        elif edge >= 10:
            color = '#e3b341'
        elif edge >= 0:
            color = '#8b949e'
        else:
            color = '#f85149'
        bar_w = max(0, min(100, edge))
        badge = '🟢' if rec == 'PRIORITY BUY' else ('🟡' if rec == 'WATCH' else '⚪')
        html += f'''
    <div class="edge-bar">
      <span style="min-width:18px">{badge}</span>
      <span style="min-width:50px;text-align:right;color:#4a5f78">{sym}</span>
      <div class="edge-track"><div class="edge-fill" style="width:{bar_w}%;background:{color}"></div></div>
      <span style="min-width:38px;font-weight:700;color:{color}">{edge:+.0f}</span>
    </div>'''
    if not watchlist:
        html += '\n    <div class="ov-row" style="color:#2e3d50">Run overnight analysis</div>'
    html += '\n  </div>\n</div>'

    html += '\n</div>'

    # ═══════ V4 SYSTEM STATUS ═══════
    v4_features = [
        ("Brain Filter", f"Blocks {len(brain_penalty)} losers", True),
        ("Trailing Stop", "1.5 ATR from peak", True),
        ("EOD Profit Lock", "3:45 PM ET", True),
        ("Deep Loss Cut", "Auto at -8%", True),
        ("Partial Take", "+5% half / +15% all", True),
        ("Stale Order Cleanup", "Auto-cancel", True),
        ("Overnight Intel", "Global + sectors", True),
        ("Watchdog", "Auto-restart" if wd_running else "OFFLINE", wd_running),
    ]

    html += '''

<!-- ════════ V4 SYSTEM STATUS ════════ -->
<div class="panel">
  <div class="panel-head">
    <div class="panel-title">⚡ V4 Armed Systems</div>
    <div class="panel-badge">''' + f'{sum(1 for _, _, ok in v4_features if ok)}/{len(v4_features)} active' + '''</div>
  </div>
  <div style="padding:14px 18px;display:grid;grid-template-columns:repeat(4,1fr);gap:10px 16px;">'''

    for name, desc, active in v4_features:
        dot_c = "green" if active else "red"
        html += f'''
    <div style="font-size:0.74rem;font-family:'JetBrains Mono',monospace;">
      <span class="{dot_c}">●</span> {name}<br>
      <span style="color:#4a5f78;font-size:0.66rem;">{desc}</span>
    </div>'''

    html += '''
  </div>
</div>

<!-- ════════ FOOTER ════════ -->
<div class="footer">'''

    html += f'''
    SmartBot V4 Armed · Brain {brain_level} ({brain_trades_learned} trades · {brain_tickers} tickers · {brain_factors} factors) · Balance ${total:,.2f} · Generated {datetime.now().strftime("%H:%M:%S")}
</div>

</div>
</body>
</html>'''

    return html


if __name__ == '__main__':
    html = generate_html()
    with open('/home/tradebot/status_dashboard.html', 'w') as f:
        f.write(html)
    print("✅ SmartBot V4 Pro Terminal Dashboard Generated")
