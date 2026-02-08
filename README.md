# 🤖 Autonomous Trading Bot - 24/7 Learning Mode

## 📋 Current Status
- **Mode:** Trading212 Demo Account (Paper Trading)
- **Execution:** Every 15 minutes, 24/7
- **Strategy:** Multi-indicator (SMA, RSI, MACD, Bollinger Bands, ATR)
- **Tickers:** 15 US stocks (AAPL, MSFT, GOOGL, TSLA, AMZN, NVDA, META, NFLX, AMD, BABA, COIN, PLTR, SOFI, RIVN, LCID)
- **Risk:** 8% per trade
- **Target:** £250/day (auto-stops when hit)

## 🎯 Learning Phase (Current)
Your bot is in **continuous learning mode** for 30-60 days:
- ✅ Runs 24/7 scanning market conditions
- ✅ Places live orders during US market hours (9:30 AM - 4:00 PM ET)
- ✅ Analyzes patterns and optimizes during off-hours
- ✅ Tracks every trade and performance metric
- ✅ Builds historical data for strategy refinement

## 📊 Quick Commands

### Status Dashboard
\`\`\`bash
/home/tradebot/status.sh
\`\`\`

### Monitor Live
\`\`\`bash
tail -f /home/tradebot/auto_trader.log
\`\`\`

### Performance Stats
\`\`\`bash
python3 /home/tradebot/performance_tracker.py --stats
\`\`\`

### Account Balance
\`\`\`bash
python3 /home/tradebot/bot.py --cash
\`\`\`

### Recent Orders
\`\`\`bash
python3 /home/tradebot/bot.py --orders
\`\`\`

### Manual Trade (Dry Run)
\`\`\`bash
python3 /home/tradebot/live_trader.py --dry-run --tickers AAPL_US_EQ
\`\`\`

### Manual Trade (Live)
\`\`\`bash
python3 /home/tradebot/live_trader.py --tickers AAPL_US_EQ
\`\`\`

## 📈 Learning Timeline

### Week 1-2: Data Collection
- Accumulate 50-100 trades
- Identify which tickers generate most signals
- Track win rate and P&L patterns

### Week 3-4: Optimization
- Review performance stats
- Adjust risk parameters if needed
- Remove underperforming tickers
- Add better performers

### Month 2: Validation
- Confirm consistent profitability
- Verify strategy works in different market conditions
- Build confidence before going live

## 🚀 Going Live Checklist

Before switching to real money:
- [ ] 30+ days of demo trading completed
- [ ] 100+ trades executed and tracked
- [ ] Win rate > 55% OR Sharpe ratio > 1.0
- [ ] Max drawdown understood and acceptable
- [ ] Reduce risk to 1-2% per trade (from current 8%)
- [ ] Start with small capital (£500-1000)
- [ ] Set max daily loss limit (£100-250)

## 🔧 Files
- \`auto_trader.py\` - Main autonomous bot (runs 24/7)
- \`live_trader.py\` - Real-time signal generator
- \`bot.py\` - Trading212 API integration
- \`demo_pipeline.py\` - Strategy indicators and backtesting
- \`performance_tracker.py\` - Learning and optimization
- \`daily_tracker.json\` - Daily P&L tracking
- \`performance_history.json\` - All trades history

## ⚙️ Configuration (.env)
Key settings:
- \`TRADING212_MODE=live\` (live API calls to demo account)
- \`TRADING212_RISK_PER_TRADE=0.08\` (8% - aggressive for learning)
- \`TRADING212_DAILY_PROFIT_TARGET=250\` (£250/day target)
- \`TRADING212_DAILY_TICKERS\` (15 stocks)

## 🎓 Learning Process
The bot improves by:
1. **Frequency:** Trading every 15min = 26 chances/day during market hours
2. **Diversity:** 15 tickers = multiple market conditions
3. **Tracking:** Logs every decision, success rate, patterns
4. **24/7 Analysis:** Even off-hours, analyzes historical patterns

## 📞 Support
Check status anytime: \`/home/tradebot/status.sh\`
View live activity: \`tail -f /home/tradebot/auto_trader.log\`

---
**Started:** January 5, 2026
**Target Go-Live:** February/March 2026 (after 30-60 days validation)
