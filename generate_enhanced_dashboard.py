"""
Generate Enhanced Status Dashboard with AI/ML Features
"""

import json
from datetime import datetime

def generate_enhanced_dashboard():
    """Generate HTML dashboard with AI features"""
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="10">
<title>SmartBot Pro Terminal</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: 'IBM Plex Sans', -apple-system, system-ui, sans-serif;
    background: #0d1117;
    color: #c9d1d9;
    line-height: 1.5;
}
.terminal { max-width: 1920px; margin: 0 auto; padding: 20px; }
.header-bar {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 16px 24px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.terminal-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #f0f6fc;
    letter-spacing: -0.02em;
}
.main-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 16px;
}
.metric-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 20px;
}
.metric-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #8b949e;
    margin-bottom: 8px;
    font-weight: 500;
}
.metric-value {
    font-size: 2rem;
    font-weight: 600;
    font-family: 'IBM Plex Mono', monospace;
    line-height: 1.2;
    margin-bottom: 4px;
}
.metric-subtitle {
    font-size: 0.8rem;
    color: #8b949e;
    font-family: 'IBM Plex Mono', monospace;
}
.positive { color: #3fb950; }
.negative { color: #f85149; }
.neutral { color: #8b949e; }
.ai-card {
    background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
    border: 1px solid #388bfd;
}
.footer {
    margin-top: 20px;
    text-align: center;
    color: #8b949e;
    font-size: 0.85rem;
    padding: 16px;
}
</style>
</head>
<body>
<div class="terminal">

<div class="header-bar">
    <div class="terminal-title">🚀 SmartBot Pro Terminal - Enhanced AI Edition</div>
    <div style="color: #3fb950; font-family: monospace;">⬤ LIVE</div>
</div>

<div class="main-grid">
    <div class="metric-card ai-card" id="market-mood">
        <div class="metric-label">🌐 Market Mood</div>
        <div class="metric-value" id="mood-value">Loading...</div>
        <div class="metric-subtitle" id="mood-desc">Analyzing...</div>
    </div>
    
    <div class="metric-card ai-card" id="sentiment">
        <div class="metric-label">📰 News Sentiment</div>
        <div class="metric-value" id="sentiment-value">--</div>
        <div class="metric-subtitle" id="sentiment-desc">Real-time analysis</div>
    </div>
    
    <div class="metric-card ai-card" id="ensemble-ai">
        <div class="metric-label">🤖 Ensemble AI</div>
        <div class="metric-value" id="ensemble-signal">--</div>
        <div class="metric-subtitle">LSTM + RandomForest</div>
    </div>
    
    <div class="metric-card ai-card" id="backtest">
        <div class="metric-label">📊 Strategy Score</div>
        <div class="metric-value" id="backtest-score">--</div>
        <div class="metric-subtitle">Backtest performance</div>
    </div>
</div>

<div class="main-grid">
    <div class="metric-card">
        <div class="metric-label">ML Confidence</div>
        <div class="metric-value" id="ml-conf">--</div>
        <div class="metric-subtitle" id="ml-signal">Signal: --</div>
    </div>
    
    <div class="metric-card">
        <div class="metric-label">Win Rate</div>
        <div class="metric-value" id="win-rate">--</div>
        <div class="metric-subtitle">Active trades</div>
    </div>
    
    <div class="metric-card">
        <div class="metric-label">Total P&L</div>
        <div class="metric-value" id="total-pnl">--</div>
        <div class="metric-subtitle">All time</div>
    </div>
    
    <div class="metric-card">
        <div class="metric-label">Risk Level</div>
        <div class="metric-value" id="risk-level">ULTRA-AGGRESSIVE</div>
        <div class="metric-subtitle">Confidence: 0.20</div>
    </div>
</div>

<div class="footer">
    SmartBot Pro 24/7 | Enhanced with Deep Learning + Sentiment Analysis + Auto-Backtesting<br>
    <span id="update-time">Last updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</span>
</div>

<script>
// Fetch AI/ML status
async function fetchAIStatus() {
    try {
        const response = await fetch('ml/ml_status.json');
        const data = await response.json();
        
        document.getElementById('ml-conf').textContent = data.confidence || '--';
        document.getElementById('ml-signal').textContent = 'Signal: ' + (data.ml_signal || '--');
    } catch (e) {
        console.log('ML status not available');
    }
}

// Fetch sentiment data
async function fetchSentiment() {
    try {
        const response = await fetch('ml/sentiment_cache.json');
        const data = await response.json();
        
        // Display first symbol's sentiment
        const symbols = Object.keys(data);
        if (symbols.length > 0) {
            const sentiment = data[symbols[0]];
            document.getElementById('sentiment-value').textContent = 
                sentiment.sentiment_score > 0 ? '📈 Bullish' : '📉 Bearish';
            document.getElementById('sentiment-desc').textContent = 
                symbols[0] + ': ' + (sentiment.sentiment_score * 100).toFixed(1) + '%';
        }
    } catch (e) {
        console.log('Sentiment data not available');
    }
}

// Fetch backtest results
async function fetchBacktest() {
    try {
        const response = await fetch('ml/backtest_results.json');
        const data = await response.json();
        
        const results = Object.values(data);
        if (results.length > 0) {
            const avgReturn = results.reduce((sum, r) => sum + r.total_return, 0) / results.length;
            document.getElementById('backtest-score').textContent = 
                (avgReturn > 0 ? '+' : '') + avgReturn.toFixed(1) + '%';
            document.getElementById('backtest-score').className = 
                'metric-value ' + (avgReturn > 0 ? 'positive' : 'negative');
        }
    } catch (e) {
        console.log('Backtest data not available');
    }
}

// Update all AI data
function updateAIData() {
    fetchAIStatus();
    fetchSentiment();
    fetchBacktest();
}

// Initial load and refresh every 10 seconds
updateAIData();
setInterval(updateAIData, 10000);
</script>

</div>
</body>
</html>"""
    
    # Write to file
    with open("status_dashboard_pro.html", "w") as f:
        f.write(html)
    
    print("✅ Enhanced dashboard generated: status_dashboard_pro.html")

if __name__ == "__main__":
    generate_enhanced_dashboard()
