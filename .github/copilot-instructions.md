# SmartBot Trading System - AI Agent Guide

## Architecture Overview
This is a 24/7 autonomous trading bot for UK markets (Trading212 platform) that combines technical analysis, machine learning, and advanced risk management. The system operates continuously, executing live trades during market hours (9:30-16:00 ET) and analyzing patterns off-hours.

**Core Components:**
- `auto_trader.py` - Main orchestrator running in 2-minute intervals
- `live_trader.py` - Real-time signal generator with multi-strategy logic (761 lines of complex decision trees)
- `bot.py` - Trading212 API wrapper with idempotency handling
- `demo_pipeline.py` - Indicator computation (SMA, RSI, MACD, Bollinger Bands, ATR) and backtesting
- `advanced_risk.py` - Dynamic risk adjustment based on consecutive wins/losses, sector diversification, circuit breakers
- `ml/` - Machine learning subsystem with RandomForest, LSTM ensemble, sentiment analysis

**Data Flow:**
1. `auto_trader.py` triggers → 2. `live_trader.py` fetches 15-min bars → 3. `demo_pipeline.compute_indicators()` → 4. Multi-strategy signal logic → 5. `advanced_risk.py` validates position limits → 6. `bot.place_market_order()` → 7. `performance_tracker.log_trade()`

## Critical Workflows

### Starting/Stopping the Bot
```bash
# Start with FULL AI (MUST use venv Python for TensorFlow/TextBlob)
cd /home/tradebot && nohup /home/tradebot/.venv/bin/python auto_trader.py >> auto_trader.log 2>&1 &

# Status check
/home/tradebot/status.sh

# Monitor live (watch for AI boost messages: MTF, Pattern, Sentiment)
tail -f /home/tradebot/auto_trader.log | grep -E "(MTF|Pattern|Sentiment|POWER|Analyzing)"

# Stop (also stops watchdog if running)
pkill -f auto_trader.py
pkill -f watchdog.sh

# Protection systems
/home/tradebot/watchdog.sh &  # Auto-restarts bot if crashes
python3 /home/tradebot/cleanup_positions.py  # Removes phantom positions
```

### Manual Trading (Testing)
```bash
# Dry run (no orders)
python3 /home/tradebot/live_trader.py --dry-run --tickers AAPL_US_EQ

# Live single trade
python3 /home/tradebot/live_trader.py --tickers AAPL_US_EQ

# Account info
python3 /home/tradebot/bot.py --cash
python3 /home/tradebot/bot.py --orders
```

### Performance Analysis
```bash
python3 /home/tradebot/performance_tracker.py --stats
# Outputs: total P&L, win rate, Sharpe ratio, best/worst tickers
```

## Project-Specific Conventions

### Ticker Format
- **Trading212 API format:** `AAPL_US_EQ` (underscore-separated with country code)
- **yfinance format:** `AAPL` (plain ticker)
- Convert between them contextually - live_trader.py handles this automatically

### Risk Management Rules (CRITICAL)
- **Never hardcode risk percentages** - always read from `AdvancedRiskManager.get_dynamic_risk()`
- Risk scales 0.6x after 3 losses, 1.3x after 3 wins (capped at 28%)
- Daily circuit breaker at -5% P&L (stops all trading)
- Max 7 positions, sector diversification enforced via `sectors` dict in `advanced_risk.py`
- Stop losses calculated as `price - (atr * 2)` - see `live_trader.py` L90-150

### State Files (JSON)
These files persist critical state across restarts:
- `daily_tracker.json` - Daily P&L, trade count, target hit flag
- `risk_state.json` - Consecutive wins/losses, circuit breaker status
- `open_positions.json` - Active positions for limit checking
- `performance_history.json` - All trades + ticker statistics
- `.idempotency.json` - Prevents duplicate orders (SHA256 fingerprints)

**Important:** When modifying trading logic, preserve these files or bot loses learning context.

### Environment Variables (.env)
```bash
TRADING212_API_KEY=<live_key>
TRADING212_API_SECRET=<live_secret>
TRADING212_BASE_URL=https://live.trading212.com/api/v0  # LIVE MODE (was demo)
TRADING212_MODE=live
TRADING212_RISK_PER_TRADE=0.95  # 95% (aggressive for $47 small account)
TRADING212_MAX_POSITIONS=1  # Focused trading
CONFIDENCE_THRESHOLD=0.65  # Quality signals only (was 0.15)
TRADING212_AUTO_CONFIRM=1  # Autonomous operation
TRADING212_DAILY_PROFIT_TARGET=250  # GBP
TRADING212_DAILY_TICKERS="AAPL,MSFT,GOOGL,TSLA,NVDA,NOK,CCL,..."  # 12-15 stocks
```

**CRITICAL: Account switched from demo to LIVE on Feb 4, 2026. Real money at risk.**

## Multi-Strategy Signal Logic + AI Enhancement

`live_trader.py` implements 7+ base strategies (lines 77-250), then applies AI enhancement layers:

**Base Strategies (priority order):**
1. **Golden Cross** (0.95) - SMA breakthrough + RSI 30-70 + MACD+
2. **Momentum Breakout** (0.90) - All indicators bullish + volume surge
3. **BB Bounce** (0.85) - Bollinger Band mean reversion
4. **RSI Reversal** (0.75) - Oversold bounce with trend confirmation
5. **MACD Momentum** (0.70) - MACD crossover with volume
6. **Volume Surge** (0.65) - Unusual volume with price confirmation

**AI Enhancement Layers (lines 485-540):**
1. **Multi-Timeframe** - +20% if all 4 timeframes align (5m/15m/1h/daily)
2. **Pattern Recognition** - +25% if chart pattern confirms (double bottom, H&S, triangles)
3. **Sentiment Analysis** - Variable boost from news/social sentiment
4. **Ensemble Voting** - +15% if LSTM model agrees, -30% if disagrees

**When adding strategies:**
- Return dict: `action`, `price`, `confidence`, `reason`, `stop_loss`, `atr`
- Base confidence 0.5-0.95, AI layers multiply (can exceed 1.0, gets capped)
- Test with `--dry-run` before live
- Check AI boost messages in logs: `grep -E "(MTF|Pattern|Sentiment)" auto_trader.log`

## ML Pipeline

### Training Models
```bash
cd ml/
python3 train_signal_model.py  # RandomForest on historical signals
python3 train_deep_model.py    # LSTM ensemble
```

### Model Files
- `ml/signal_model.pkl` - RandomForest (used by default)
- `ml/deep_learning_model.py` - Ensemble predictor class
- `ml/historical_signals.csv` - Training data (auto-updated by trades)

### Sentiment Analysis
- `ml/sentiment_analysis.py` contains `SentimentAnalyzer` and `MarketMoodAnalyzer`
- Uses keyword-based scoring (no external API required)
- Called in `live_trader.py` L15-25 when `ENHANCED_AI_AVAILABLE`

## Testing

Run tests from repo root:
```bash
pytest tests/ -v
# Key test files: tests/test_bot.py, tests/test_signals.py
```

**Mock Mode:** Set `TRADING212_USE_MOCK=1` to test without real API calls (see `bot.py` L62-64)

## Dashboard Generation

Multiple dashboard scripts coexist (evolutionary development):
- `generate_pro_terminal.py` - Current production dashboard
- `generate_enhanced_dashboard.py` - AI-focused metrics
- `status_dashboard.html` - Generated HTML output

Update dashboard: `./update_dashboard.sh` (generates HTML from JSON state files)

## Common Pitfalls

1. **DataFrames with MultiIndex columns** - yfinance returns MultiIndex, must flatten with `df.columns = df.columns.get_level_values(0)` before computing indicators (appears in `live_trader.py` L52, `demo_pipeline.py` L41, all new ML modules)
2. **Market hours check** - Always use `is_market_hours()` from `auto_trader.py` (checks ET timezone + weekdays), runs 9:30 AM - 4:00 PM ET only
3. **Order idempotency** - Never bypass `_ensure_client_order_id()` in `bot.py` - prevents double orders on retry (SHA256 hash stored in `.idempotency.json`)
4. **ATR calculation** - Uses 14-period True Range, critical for stop loss = `price - (atr * 2)` 
5. **GBP vs USD** - API returns USD, targets in GBP (conversion in trackers)
6. **Python environment** - Bot MUST use `/home/tradebot/.venv/bin/python` for AI libraries (TensorFlow, TextBlob). System python3 lacks these packages.
7. **Phantom positions** - Trading212 API bug leaves 0-quantity OPEN positions. Bot runs `cleanup_positions.py` before each scan to remove them.
8. **Watchdog protection** - `watchdog.sh` monitors bot process, auto-restarts if crashed (checks every 60s)

## Key Files for Pattern Examples

- `live_trader.py` L50-250 - Multi-strategy signal patterns
- `advanced_risk.py` L80-120 - Dynamic risk scaling logic
- `demo_pipeline.py` L40-70 - Indicator computation standard
- `bot.py` L80-100 - Idempotency and order submission
- `performance_tracker.py` - Trade logging and statistics

## Integration Points

- **Trading212 API:** REST API with Basic Auth (base64 encoded), rate limits unknown but handled by 2-min intervals
- **yfinance:** Free market data (15-min delay acceptable for intraday)
- **Notification system:** `notify.py` logs to file (email/SMS requires SMTP setup in .env)
- **No external databases** - all state in JSON files for simplicity

## Development Notes

- **Production mode:** Bot runs on Linux VPS, uses `nohup` for persistence
- **Logging:** Append-only to `auto_trader.log` (rotate manually if >100MB)
- **No Docker/containers** - direct Python execution for debugging ease
- **Git workflow:** Main branch is production, test changes with `--dry-run` first
- **Dashboard:** http://localhost:8080/status_dashboard.html (professional Bloomberg-style UI)
- **Account:** LIVE Trading212 with $47.50 capital (switched from demo Feb 4, 2026)
- **Current status:** First profitable trades executed Feb 6 (CCL +$0.18, NOK +$0.03)

## Recent Major Changes (Feb 6, 2026)

1. **Full AI Power Mode Installed** - TensorFlow, TextBlob, OpenCV, Stable-Baselines3
2. **Multi-timeframe analysis** - Checks 5m/15m/1h/daily confluence before entry
3. **Pattern recognition** - Auto-detects double tops/bottoms, H&S, triangles, breakouts
4. **Sentiment analysis** - Real-time news/social sentiment boosts
5. **Dashboard redesigned** - Professional terminal UI (from basic Courier New theme)
6. **Crypto bot stopped** - Coinbase trading blocked ("account not available")
7. **Protection systems** - Watchdog auto-restart + phantom position cleanup

## AI Module Dependencies

**Required packages in venv:**
- `tensorflow` - LSTM deep learning
- `textblob` - Sentiment analysis (+ NLTK corpora)
- `opencv-python` - Pattern recognition
- `stable-baselines3` - Reinforcement learning framework
- `arch` - Volatility forecasting (GARCH models)
- `gymnasium` - RL environment
- `scikit-image` - Image-based pattern detection

**Install command:**
```bash
/home/tradebot/.venv/bin/pip install tensorflow textblob tweepy opencv-python arch stable-baselines3 scikit-image gymnasium
/home/tradebot/.venv/bin/python -m textblob.download_corpora
```

**CRITICAL:** Bot MUST use `/home/tradebot/.venv/bin/python` not system python3

````
