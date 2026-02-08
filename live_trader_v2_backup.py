import json
#!/usr/bin/env python3
"""
Real-time trading engine - makes live decisions based on current market data
ENHANCED with Advanced Risk Management System
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os
from bot import place_market_order, get_account_cash
from demo_pipeline import compute_indicators
from performance_tracker import log_trade
from advanced_risk import AdvancedRiskManager
from notify import notify_trade, notify_bot_status
# ML integration
import sys
sys.path.append('ml')
from ml.predict_signal import predict_signal, load_model

# Enhanced AI/ML integration - FULL POWER MODE
try:
    from ml.deep_learning_model import EnsemblePredictor
    from ml.sentiment_analysis import get_sentiment_boost, MarketMoodAnalyzer
    from ml.multi_timeframe import analyze_all_timeframes, check_timeframe_alignment
    from ml.pattern_recognition import analyze_patterns, get_pattern_signal
    from ml.volatility_forecast import get_volatility_regime
    from ml.regime_classifier import classify_regime
    ENHANCED_AI_AVAILABLE = True
    print("🚀 FULL AI POWER MODE ENABLED")
except ImportError as e:
    ENHANCED_AI_AVAILABLE = False
    print(f"⚠️ Enhanced AI features not fully available: {e}")

def get_current_signal(ticker_yf: str, lookback_periods: int = 100) -> dict:
    """WORLD-CLASS signal generator with multiple strategies and advanced logic.
    
    Args:
        ticker_yf: Yahoo Finance ticker (e.g., 'AAPL')
        lookback_periods: How many periods of history to use for indicators
    
    Returns:
        dict with 'action' (buy/sell/hold), 'price', 'confidence', 'reason'
    """
    try:
        # Get recent 15min data - more granular for intraday opportunities
        df = yf.download(ticker_yf, period='5d', interval='15m', progress=False)
        
        if df.empty or len(df) < 60:  # 60 bars = 15 hours of 15min data
            return {"action": "hold", "reason": "insufficient data"}
        
        # Flatten MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Compute indicators
        df = compute_indicators(df, sma_short=10, sma_long=30)
        
        # Get latest rows for pattern recognition
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        prev2 = df.iloc[-3] if len(df) >= 3 else prev
        
        current_price = float(latest["Close"])
        
        # === CORE INDICATORS ===
        sma_bullish = latest["sma_short"] > latest["sma_long"]
        sma_was_bearish = prev["sma_short"] <= prev["sma_long"]
        sma_gap = (latest["sma_short"] - latest["sma_long"]) / latest["sma_long"] * 100
        
        rsi = float(latest["rsi"])
        rsi_prev = float(prev["rsi"])
        macd_hist = float(latest["macd_hist"])
        macd_hist_prev = float(prev["macd_hist"])
        
        above_bb_middle = latest["Close"] > latest["bb_middle"]
        bb_width = (latest["bb_upper"] - latest["bb_lower"]) / latest["bb_middle"] * 100
        
        # Volume analysis
        volume_surge = latest["Volume"] > df["Volume"].rolling(20).mean().iloc[-1] * 1.3
        
        # Price momentum
        price_change_1h = (current_price - float(prev["Close"])) / float(prev["Close"]) * 100
        price_change_3h = (current_price - float(prev2["Close"])) / float(prev2["Close"]) * 100
        
        atr = float(latest["atr"])
        
        # === STRATEGY 1: GOLDEN CROSSOVER (ENABLED - high confidence) ===
        if sma_bullish and sma_was_bearish and 30 < rsi < 70 and macd_hist > 0:
            return {
                "action": "buy",
                "price": current_price,
                "confidence": 0.95,
                "reason": "🌟 GOLDEN CROSS: SMA breakthrough + perfect RSI + MACD confirm",
                "stop_loss": current_price - (atr * 2),
                "atr": atr
            }
        
        # === STRATEGY 2: MOMENTUM BREAKOUT (AGGRESSIVE - primary strategy) ===
        if (sma_bullish and macd_hist > 0 and macd_hist > macd_hist_prev and 
            rsi > 55 and rsi < 75 and above_bb_middle and volume_surge):
            return {
                "action": "buy",
                "price": current_price,
                "confidence": 0.88,
                "reason": "🚀 MOMENTUM BREAKOUT: Strong trend + volume surge + MACD rising",
                "stop_loss": current_price - (atr * 1.8),
                "atr": atr
            }
        
        # === STRATEGY 3: RSI BOUNCE (RE-ENABLED for more opportunities) ===
        if (rsi > 35 and rsi < 50 and rsi_prev < 35 and sma_bullish and 
            price_change_1h > 0.3 and above_bb_middle):
            return {
                "action": "buy",
                "price": current_price,
                "confidence": 0.80,
                "reason": "💪 RSI BOUNCE: Oversold recovery + trend support + price surge",
                "stop_loss": current_price - (atr * 2.2),
                "atr": atr
            }
        
        # === STRATEGY 4: MACD MOMENTUM (ENABLED - momentum trading) ===
        if (macd_hist > 0 and macd_hist > macd_hist_prev and sma_bullish and 
            rsi > 45 and rsi < 70):
            return {
                "action": "buy",
                "price": current_price,
                "confidence": 0.75,
                "reason": "📈 MACD MOMENTUM: Histogram growing + trend intact + RSI healthy",
                "stop_loss": current_price - (atr * 2),
                "atr": atr
            }
        
        # === STRATEGY 5: BOLLINGER BOUNCE (ENABLED - volatility trading) ===
        price_position = (current_price - latest["bb_lower"]) / (latest["bb_upper"] - latest["bb_lower"])
        if (price_position > 0.4 and price_position < 0.7 and sma_bullish and 
            bb_width > 3 and rsi > 40 and rsi < 65):
            return {
                "action": "buy",
                "price": current_price,
                "confidence": 0.70,
                "reason": "🎯 BB BOUNCE: Mid-band position + wide bands + trend + RSI ok",
                "stop_loss": current_price - (atr * 2),
                "atr": atr
            }
        
        # === STRATEGY 6: TREND CONTINUATION (ENABLED - trend riding) ===
        if (sma_bullish and sma_gap > 0.3 and macd_hist > 0 and 
            rsi > 45 and rsi < 80 and price_change_3h > 0.3):
            return {
                "action": "buy",
                "price": current_price,
                "confidence": 0.68,
                "reason": "⚡ TREND CONTINUATION: Strong uptrend + momentum + 3h gain",
                "stop_loss": current_price - (atr * 2.5),
                "atr": atr
            }
        
        # === STRATEGY 8: AGGRESSIVE MOMENTUM (PRIMARY - Ultra Fast) ===
        if (sma_bullish and price_change_1h > 0.5 and rsi > 40 and rsi < 75):
            return {
                "action": "buy",
                "price": current_price,
                "confidence": 0.62,
                "reason": "💥 FAST MOMENTUM: Quick price surge + trend support",
                "stop_loss": current_price - (atr * 2),
                "atr": atr
            }
        
        # === STRATEGY 9: VOLUME SURGE (NEW - Breakout Hunter) ===
        if (volume_surge and price_change_1h > 0.4 and sma_bullish):
            return {
                "action": "buy",
                "price": current_price,
                "confidence": 0.65,
                "reason": "🔥 VOLUME SURGE: Massive volume + price up + trend",
                "stop_loss": current_price - (atr * 1.8),
                "atr": atr
            }
        
        # === STRATEGY 7: VOLUME SPIKE BREAKOUT ===
        if (volume_surge and price_change_1h > 0.8 and sma_bullish and 
            rsi > 50 and rsi < 75 and macd_hist > 0):
            return {
                "action": "buy",
                "price": current_price,
                "confidence": 0.82,
                "reason": "📊 VOLUME BREAKOUT: Huge volume + price surge + all indicators align",
                "stop_loss": current_price - (atr * 1.5),
                "atr": atr
            }
        
        # === STRATEGY 10: OVERSOLD BOUNCE (NO TREND REQUIRED) - ULTRA AGGRESSIVE ===
        if (rsi < 40 and rsi_prev < rsi and price_change_1h > 0.1):
            return {
                "action": "buy",
                "price": current_price,
                "confidence": 0.55,
                "reason": "⚡ OVERSOLD BOUNCE: RSI < 40 recovering + price turning up",
                "stop_loss": current_price - (atr * 2),
                "atr": atr
            }
        
        # === STRATEGY 11: RECOVERY PLAY (NO TREND REQUIRED) - ULTRA AGGRESSIVE ===
        if (rsi < 45 and price_change_1h > 0.3 and volume_surge):
            return {
                "action": "buy",
                "price": current_price,
                "confidence": 0.52,
                "reason": "💪 RECOVERY: Bounce + volume on weak stock",
                "stop_loss": current_price - (atr * 2),
                "atr": atr
            }
        
        # === STRATEGY 12: QUICK SCALP (NO TREND REQUIRED) - ULTRA AGGRESSIVE ===
        if (price_change_1h > 0.5 and rsi > 25 and rsi < 75):
            return {
                "action": "buy",
                "price": current_price,
                "confidence": 0.50,
                "reason": "🎯 QUICK SCALP: 0.5%+ move + RSI ok",
                "stop_loss": current_price - (atr * 1.5),
                "atr": atr
            }
        
        # === STRATEGY 13: MICRO MOMENTUM (ULTRA AGGRESSIVE) ===
        if (price_change_1h > 0.3 and rsi > 30 and rsi < 65):
            return {
                "action": "buy",
                "price": current_price,
                "confidence": 0.48,
                "reason": "🔥 MICRO MOMENTUM: Small 1h move detected",
                "stop_loss": current_price - (atr * 1.5),
                "atr": atr
            }
        
        # === STRATEGY 14: VOLUME SPIKE (ANY RSI) ===
        if (volume_surge and price_change_1h > 0.2):
            return {
                "action": "buy",
                "price": current_price,
                "confidence": 0.46,
                "reason": "📢 VOLUME SPIKE: Unusual activity detected",
                "stop_loss": current_price - (atr * 2),
                "atr": atr
            }
        
        # === STRATEGY 15: RSI RECOVERY (NO PRICE REQUIREMENT) ===
        if (rsi < 45 and rsi_prev < rsi and rsi > rsi_prev + 2):
            return {
                "action": "buy",
                "price": current_price,
                "confidence": 0.45,
                "reason": "📈 RSI RECOVERY: RSI turning up from oversold",
                "stop_loss": current_price - (atr * 2),
                "atr": atr
            }
        
        # === STRATEGY 16: ANY POSITIVE MOVE (HYPER-AGGRESSIVE) ===
        if (price_change_1h > 0.10 and rsi > 20 and rsi < 80):
            return {
                "action": "buy",
                "price": current_price,
                "confidence": 0.42,
                "reason": f"⚡ TINY MOVE: +{price_change_1h:.2f}% detected (RSI={rsi:.0f})",
                "stop_loss": current_price - (atr * 2),
                "atr": atr
            }
        
        # === STRATEGY 17: MARKET OPEN SURGE (NEW - catches opening volatility) ===
        from datetime import datetime
        import pytz
        et = pytz.timezone('America/New_York')
        now_et = datetime.now(et)
        market_open_time = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
        minutes_since_open = (now_et - market_open_time).total_seconds() / 60
        
        # First 30 minutes after market open - catch momentum
        if (0 <= minutes_since_open <= 30 and price_change_1h > 0.05 and 
            volume_surge and rsi > 30 and rsi < 75):
            return {
                "action": "buy",
                "price": current_price,
                "confidence": 0.65,
                "reason": f"🔥 OPENING SURGE: +{price_change_1h:.2f}% in first 30min + volume",
                "stop_loss": current_price - (atr * 1.5),
                "atr": atr
            }
        
        # === SELL SIGNALS ===
        # Strong sell: trend break
        if not sma_bullish and prev["sma_short"] > prev["sma_long"]:
            return {
                "action": "sell",
                "price": current_price,
                "confidence": 0.85,
                "reason": "❌ TREND BREAK: SMA death cross"
            }
        
        # Overbought sell
        if rsi > 75 and rsi_prev > 70 and macd_hist < macd_hist_prev:
            return {
                "action": "sell",
                "price": current_price,
                "confidence": 0.75,
                "reason": "⚠️ OVERBOUGHT: RSI extreme + MACD declining"
            }
        
        # Hold otherwise
        return {
            "action": "hold",
            "price": current_price,
            "confidence": 0.50,
            "reason": "No strong signal"
        }
        
    except Exception as e:
        return {"action": "hold", "reason": f"error: {e}"}


def execute_live_trading(tickers_212: list, dry_run: bool = False) -> dict:
    """Execute live trading decisions for multiple tickers with ADVANCED RISK MANAGEMENT.
    
    Args:
        tickers_212: List of Trading212 tickers (e.g., ['AAPL_US_EQ', 'MSFT_US_EQ'])
        dry_run: If True, don't actually place orders
    
    Returns:
        dict with results for each ticker
    """
    # Prepare ML status dict for dashboard
    ml_status = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ml_signal": "",
        "confidence": "",
        "model_status": "Loaded" if 'ml_model' in locals() and ml_model else "Unavailable"
    }
    results = {}
    notify_bot_status("RUNNING", f"SmartBot live_trader started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize advanced risk manager
    risk_mgr = AdvancedRiskManager()

    def _compute_feature_pack(df_15m, signal_data):
        """Extra features for training/logging (not used by current ML model)."""
        features = {
            "price_change_1h": signal_data.get("price_change_1h", 0),
            "price_change_3h": signal_data.get("price_change_3h", 0),
            "rsi": signal_data.get("rsi", 0),
            "macd": signal_data.get("macd", 0),
        }

        if df_15m is not None and not df_15m.empty:
            if isinstance(df_15m.columns, pd.MultiIndex):
                df_15m.columns = df_15m.columns.get_level_values(0)
            close = df_15m["Close"].astype(float)
            vol = df_15m["Volume"].astype(float) if "Volume" in df_15m.columns else None
            if len(close) >= 5:
                features["price_change_1d"] = float((close.iloc[-1] - close.iloc[-5]) / close.iloc[-5])
            if vol is not None and len(vol) >= 20:
                v_mean = vol.rolling(20).mean().iloc[-1]
                v_std = vol.rolling(20).std().iloc[-1]
                if v_std and v_std > 0:
                    features["volume_zscore"] = float((vol.iloc[-1] - v_mean) / v_std)
        return features
    
    # Update current prices for all positions first
    print("\n📊 Updating position prices...")
    positions = risk_mgr.load_positions()
    for ticker in list(positions.keys()):
        try:
            ticker_yf = ticker.replace("_US_EQ", "")
            current_data = yf.download(ticker_yf, period='1d', interval='1h', progress=False)
            if not current_data.empty:
                if isinstance(current_data.columns, pd.MultiIndex):
                    current_data.columns = current_data.columns.get_level_values(0)
                current_price = float(current_data['Close'].iloc[-1])
                risk_mgr.update_position(ticker_yf, current_price)
        except Exception as e:
            print(f"   ⚠️ Could not update {ticker}: {e}")
    
    # Check exit signals for existing positions FIRST
    print("\n🔍 Checking exit signals for open positions...")
    exit_signals = risk_mgr.check_exit_signals()
    
    for exit_sig in exit_signals:
        ticker = exit_sig['ticker']
        ticker_212 = ticker + "_US_EQ"  # Convert to T212 format
        action = exit_sig['action']
        reason = exit_sig['reason']
        price = exit_sig['price']
        
        if action == 'SELL':
            # Get position quantity
            positions = risk_mgr.get_open_positions()
            qty = positions.get(ticker, {}).get('quantity', 0)
            
            if qty > 0:
                print(f"🔴 EXIT: {ticker} {qty} shares @ ${price:.2f} - {reason}")
                notify_trade(ticker, "sell", qty, price, reason)
                
                if not dry_run:
                    try:
                        # Place sell order (negative quantity)
                        order_result = place_market_order(ticker_212, -qty, confirm=True)
                        print(f"   ✅ Sell order placed: {order_result.get('id', 'N/A')}")
                        notify_trade(ticker, "sell", qty, price, f"Order ID: {order_result.get('id', 'N/A')}")
                        
                        # Close position in risk manager
                        risk_mgr.close_position(ticker, price, reason)
                        log_trade(ticker_212, "sell", qty, price, reason=reason, metadata={
                            "exit_reason": reason,
                            "order_id": order_result.get('id', 'N/A')
                        })
                        
                        results[ticker_212] = {"action": "sell", "qty": qty, "reason": reason}
                    except Exception as e:
                        print(f"   ❌ Sell order failed: {e}")
                        notify_bot_status("ERROR", f"Sell order failed for {ticker}: {e}")
                        results[ticker_212] = {"action": "error", "error": str(e)}
        
        elif action == 'SELL_PARTIAL':
            # Take partial profit
            positions = risk_mgr.get_open_positions()
            qty = positions.get(ticker, {}).get('quantity', 0)
            portion = exit_sig.get('portion', 0.5)
            qty_to_sell = max(1, round(qty * portion))
            
            print(f"💰 PARTIAL EXIT: {ticker} {qty_to_sell}/{qty} shares @ ${price:.2f} - {reason}")
            
            if not dry_run:
                try:
                    order_result = place_market_order(ticker_212, -qty_to_sell, confirm=True)
                    print(f"   ✅ Partial sell placed: {order_result.get('id', 'N/A')}")
                    
                    # Update position quantity
                    positions[ticker]['quantity'] -= qty_to_sell
                    risk_mgr.save_positions(positions)
                    log_trade(ticker_212, "sell_partial", qty_to_sell, price, reason=reason, metadata={
                        "exit_reason": reason,
                        "order_id": order_result.get('id', 'N/A'),
                        "portion": portion
                    })
                    
                    results[ticker_212] = {"action": "sell_partial", "qty": qty_to_sell}
                except Exception as e:
                    print(f"   ❌ Partial sell failed: {e}")
                    notify_bot_status("ERROR", f"Partial sell failed for {ticker}: {e}")
    
    # Get account cash
    try:
        account = get_account_cash()
        free_cash = account.get('free', 0)
        total_cash = account.get('total', 0)
        print(f"\n💰 Account: ${total_cash:.2f} total | ${free_cash:.2f} free")
    except Exception as e:
        print(f"⚠️  Could not fetch account cash: {e}")
        notify_bot_status("ERROR", f"Could not fetch account cash: {e}")
        free_cash = 0
        total_cash = 5000
    
    # Get dynamic risk percentage
    dynamic_risk = risk_mgr.get_dynamic_risk()
    
    if dynamic_risk == 0:
        print("\n🛑 CIRCUIT BREAKER ACTIVE - No new positions allowed")
        return results
    
    # Get market regime
    regime, regime_mult = risk_mgr.get_market_regime()
    
    # Adjust risk based on market regime
    adjusted_risk = dynamic_risk * regime_mult
    adjusted_risk = max(0.01, min(0.30, adjusted_risk))  # Keep between 1% and 30% (was 15%)
    
    print(f"📊 Dynamic Risk: {dynamic_risk*100:.1f}% × {regime_mult:.2f} = {adjusted_risk*100:.1f}%")
    
    max_risk_amount = total_cash * adjusted_risk
    account_balance = total_cash  # Store for later use
    
    # NEW ENTRY SIGNALS
    print(f"\n🔍 Scanning {len(tickers_212)} tickers for entry signals...")
    
    # Load ML model once per scan
    try:
        ml_model = load_model()
    except Exception as e:
        print(f"⚠️  ML model not loaded: {e}")
        ml_model = None
    
    # Initialize enhanced AI systems
    ensemble_predictor = None
    market_mood_analyzer = None
    
    if ENHANCED_AI_AVAILABLE:
        try:
            ensemble_predictor = EnsemblePredictor()
            ensemble_predictor.load_models()
            market_mood_analyzer = MarketMoodAnalyzer()
            
            # Check overall market mood
            market_mood, mood_desc = market_mood_analyzer.get_market_mood()
            should_trade, trade_reason = market_mood_analyzer.should_trade_today()
            print(f"🌐 Market Mood: {mood_desc} (Score: {market_mood:.3f})")
            
            if not should_trade:
                print(f"⚠️  {trade_reason}")
                # Still allow trading but reduce risk
                adjusted_risk *= 0.7
                print(f"   📊 Risk reduced to {adjusted_risk*100:.1f}% due to market conditions")
        except Exception as e:
            print(f"⚠️  Enhanced AI initialization failed: {e}")

    for ticker_212 in tickers_212:
        # Convert to Yahoo Finance format
        ticker_yf = ticker_212.replace("_US_EQ", "").replace("_UK_EQ", "").replace("_DE_EQ", "")
        
        # Check position limits before analyzing
        if not risk_mgr.check_position_limits(ticker_yf):
            continue
        
        print(f"\n🔍 Analyzing {ticker_yf}...")
        
        signal = get_current_signal(ticker_yf)
        action = signal.get("action")
        price = signal.get("price", 0)
        reason = signal.get("reason", "")
        confidence = signal.get("confidence", 0.5)
        
        # === FULL AI ANALYSIS ===
        ai_boosts = []
        regime_info = {"regime": "normal", "trend_strength": 0.0, "vol": 0.0, "multiplier": 1.0}
        vol_info = {"regime": "unknown", "vol": None, "multiplier": 1.0}
        
        # 1. Multi-Timeframe Analysis
        if ENHANCED_AI_AVAILABLE:
            try:
                mtf = analyze_all_timeframes(ticker_yf)
                if mtf['confluence'] > 0.75 and action == "buy":
                    confidence *= 1.2
                    ai_boosts.append(f"MTF:{mtf['confluence']:.2f}")
                    print(f"   ⏰ Multi-Timeframe: ALL BULLISH ({mtf['confluence']:.2f}) +20%")
                elif mtf['confluence'] < -0.75 and action == "sell":
                    confidence *= 1.2
                    ai_boosts.append(f"MTF:{mtf['confluence']:.2f}")
                    print(f"   ⏰ Multi-Timeframe: ALL BEARISH ({mtf['confluence']:.2f}) +20%")
                elif abs(mtf['confluence']) < 0.3:
                    confidence *= 0.8
                    print(f"   ⏰ Multi-Timeframe: Mixed signals ({mtf['confluence']:.2f}) -20%")
            except Exception as e:
                print(f"   ⚠️  MTF analysis error: {e}")

        # 1b. Regime Classifier (trend vs range vs volatile)
        if ENHANCED_AI_AVAILABLE:
            try:
                df_regime = yf.download(ticker_yf, period='10d', interval='1h', progress=False)
                if not df_regime.empty:
                    regime_info = classify_regime(df_regime)
                    print(f"   🧭 Regime: {regime_info['regime'].upper()} | Trend={regime_info['trend_strength']:.3f}")
            except Exception as e:
                print(f"   ⚠️  Regime analysis error: {e}")
        
        # 2. Pattern Recognition
        if ENHANCED_AI_AVAILABLE:
            try:
                df_pattern = yf.download(ticker_yf, period='60d', interval='1d', progress=False)
                if not df_pattern.empty:
                    patterns = analyze_patterns(df_pattern)
                    pattern_signal, pattern_conf = get_pattern_signal(patterns)
                    
                    if pattern_signal == action and pattern_conf > 0.6:
                        confidence *= 1.25
                        ai_boosts.append(f"Pattern:{pattern_conf:.2f}")
                        print(f"   📊 Pattern: {action.upper()} confirmed ({pattern_conf:.2f}) +25%")
                    elif pattern_signal != 'hold' and pattern_signal != action:
                        confidence *= 0.75
                        print(f"   📊 Pattern: Conflicting signal -25%")
            except Exception as e:
                print(f"   ⚠️  Pattern analysis error: {e}")
        
        # 3. Sentiment Analysis
        sentiment_boost = 1.0
        if ENHANCED_AI_AVAILABLE:
            try:
                sentiment_boost, sentiment_conf = get_sentiment_boost(ticker_yf)
                if sentiment_boost != 1.0:
                    ai_boosts.append(f"Sent:{sentiment_boost:.2f}")
                    print(f"   📰 Sentiment: {sentiment_boost:.2f}x (confidence: {sentiment_conf:.2f})")
                    confidence = confidence * sentiment_boost
            except Exception as e:
                print(f"   ⚠️  Sentiment analysis error: {e}")

        # 4. Volatility Regime Filter
        if ENHANCED_AI_AVAILABLE:
            try:
                df_vol = yf.download(ticker_yf, period='5d', interval='15m', progress=False)
                vol_info = get_volatility_regime(df_vol, window=60)
                if vol_info["regime"] == "high":
                    confidence *= vol_info["multiplier"]
                    print(f"   📉 Volatility: HIGH ({vol_info['vol']:.4f}) -15% confidence")
                elif vol_info["regime"] == "low":
                    confidence *= vol_info["multiplier"]
                    print(f"   📈 Volatility: LOW ({vol_info['vol']:.4f}) +5% confidence")
            except Exception as e:
                print(f"   ⚠️  Volatility analysis error: {e}")

        # 5. Strategy/regime alignment boosts
        if action in ["buy", "sell"]:
            reason_upper = reason.upper()
            trend_strats = ["GOLDEN", "MOMENTUM", "MACD", "BREAKOUT", "VOLUME"]
            range_strats = ["BB BOUNCE", "RSI"]

            if regime_info["regime"] == "trend":
                if any(s in reason_upper for s in trend_strats):
                    confidence *= 1.10
                    ai_boosts.append("RegimeTrend")
                    print("   📌 Regime match: TREND strategy +10%")
                elif any(s in reason_upper for s in range_strats):
                    confidence *= 0.85
                    print("   📌 Regime mismatch: Range strategy in TREND -15%")
            elif regime_info["regime"] == "range":
                if any(s in reason_upper for s in range_strats):
                    confidence *= 1.10
                    ai_boosts.append("RegimeRange")
                    print("   📌 Regime match: RANGE strategy +10%")
                elif any(s in reason_upper for s in trend_strats):
                    confidence *= 0.85
                    print("   📌 Regime mismatch: Trend strategy in RANGE -15%")
            elif regime_info["regime"] == "volatile":
                confidence *= 0.80
                print("   📌 Regime: VOLATILE -20% confidence")
        
        # Cap confidence
        confidence = min(confidence, 1.0)
        
        # Enhanced AI: Ensemble prediction
        if ENHANCED_AI_AVAILABLE and ensemble_predictor and action in ["buy", "sell"]:
            try:
                # Get recent price history
                df = yf.download(ticker_yf, period='5d', interval='15m', progress=False)
                if not df.empty and len(df) >= 60:
                    recent_prices = df['Close'].values[-60:]
                    
                    # Get features for ensemble
                    features = {}
                    for key in ["rsi", "macd", "sma_short", "sma_long", "bb_upper", "bb_lower", "Volume"]:
                        val = signal.get(key)
                        if val is None and key == "Volume":
                            val = signal.get("volume")
                        features[key.lower()] = val if val is not None else 0
                    
                    # Get ensemble signal
                    ensemble_signal, ensemble_conf, ensemble_details = ensemble_predictor.get_ensemble_signal(
                        recent_prices, features
                    )
                    
                    print(f"   🤖 Ensemble AI: Signal={ensemble_signal} | Confidence={ensemble_conf:.2f}")
                    
                    # Boost confidence if ensemble agrees
                    if (action == "buy" and ensemble_signal == 1) or (action == "sell" and ensemble_signal == -1):
                        confidence = min(confidence * 1.15, 1.0)  # 15% boost for agreement
                        print(f"   ✅ Ensemble CONFIRMS {action.upper()} - Confidence boosted to {confidence:.2f}")
                    elif (action == "buy" and ensemble_signal == -1) or (action == "sell" and ensemble_signal == 1):
                        confidence *= 0.7  # Reduce confidence if ensemble disagrees
                        print(f"   ⚠️  Ensemble DISAGREES - Confidence reduced to {confidence:.2f}")
            except Exception as e:
                print(f"   ⚠️  Ensemble prediction error: {e}")

        # For dashboard: record the first actionable ML signal per scan
        if ml_model and action in ["buy", "sell"] and not ml_status["ml_signal"]:
            features = {}
            for key in ["rsi", "macd", "sma_short", "sma_long", "bb_upper", "bb_lower", "Volume", "price_change_1h", "price_change_3h"]:
                val = signal.get(key)
                if val is None and key == "Volume":
                    val = signal.get("volume")
                features[key.lower()] = val if val is not None else 0
            try:
                ml_pred = predict_signal(features, ml_model)
                ml_status["ml_signal"] = "BUY" if ml_pred == 1 else ("SELL" if ml_pred == -1 else "HOLD")
                ml_status["confidence"] = str(confidence)
            except Exception as e:
                ml_status["ml_signal"] = "ERROR"
                ml_status["confidence"] = str(e)

        # Write ML status to JSON for dashboard
        try:
            with open("ml/ml_status.json", "w") as f:
                json.dump(ml_status, f, indent=2)
        except Exception as e:
            pass

        # ML signal boosting: use model to confirm or boost signal
        if ml_model and action in ["buy", "sell"]:
            # Prepare features for ML model (must match training features)
            features = {}
            for key in ["rsi", "macd", "sma_short", "sma_long", "bb_upper", "bb_lower", "Volume", "price_change_1h", "price_change_3h"]:
                val = signal.get(key)
                if val is None and key == "Volume":
                    val = signal.get("volume")
                features[key.lower()] = val if val is not None else 0
            try:
                ml_pred = predict_signal(features, ml_model)
                # ML output: 1=buy, 0=hold, -1=sell
                if action == "buy" and ml_pred != 1:
                    print(f"   🤖 ML veto: Model does not confirm BUY (pred={ml_pred})")
                    results[ticker_212] = {"action": "hold", "reason": "ML vetoed buy"}
                    pass  # replaced 'continue' with 'pass' to avoid SyntaxError
                elif action == "sell" and ml_pred != -1:
                    print(f"   🤖 ML veto: Model does not confirm SELL (pred={ml_pred})")
                    results[ticker_212] = {"action": "hold", "reason": "ML vetoed sell"}
                    pass
                else:
                    if ml_pred == 1 and action != "buy":
                        print(f"   🤖 ML boost: Model suggests BUY (pred=1), overriding action")
                        action = "buy"
                        reason += " | ML boost"
                    if ml_pred == -1 and action != "sell":
                        print(f"   🤖 ML boost: Model suggests SELL (pred=-1), overriding action")
                        action = "sell"
                        reason += " | ML boost"
            except Exception as e:
                print(f"   ⚠️  ML prediction failed: {e}")

        if action == "hold":
            print(f"   ⏸️  HOLD - {reason}")
            results[ticker_212] = {"action": "hold", "reason": reason}
            pass
        
        # Dynamic confidence and risk based on signal strength - CASH POT MODE
        trading_mode = os.getenv('TRADING212_MODE', 'DEMO')
        confidence_threshold = float(os.getenv('CONFIDENCE_THRESHOLD', '0.40'))
        
        # Use BIGGER positions for high-confidence signals (65%+)
        base_risk = float(os.getenv('TRADING212_RISK_PER_TRADE', '0.18'))
        high_conf_risk = float(os.getenv('TRADING212_RISK_HIGH_CONFIDENCE', '0.25'))
        min_qty = float(os.getenv('TRADING212_MIN_QTY', '0.2'))
        min_order_value = float(os.getenv('TRADING212_MIN_ORDER_VALUE', '5'))
        min_avg_volume = float(os.getenv('TRADING212_MIN_AVG_VOLUME', '200000'))
        max_atr_pct = float(os.getenv('TRADING212_MAX_ATR_PCT', '0.05'))
        
        # SMART CASH USAGE: Use free cash when tight, total balance when plenty
        # This allows SmartBot to prove itself with limited funds!
        if free_cash < account_balance * 0.10:  # Less than 10% cash available
            # Use ALL available free cash aggressively
            max_risk_amount = free_cash * 0.95  # Use 95% of free cash
            print(f"   💪 TIGHT CASH MODE: Using {max_risk_amount:.2f} of ${free_cash:.2f} available")
        else:
            # Normal mode - use percentage of total balance
            if confidence >= 0.65:
                max_risk_amount = account_balance * high_conf_risk  # 40% for high-confidence
                print(f"   💎 HIGH CONFIDENCE ({confidence*100:.0f}%) - Using {high_conf_risk*100:.0f}% position size")
            else:
                max_risk_amount = account_balance * base_risk  # 35% for normal signals

        # AI position sizing multiplier (confidence + regime + volatility)
        conf_floor = max(confidence_threshold, 0.4)
        conf_norm = min(1.0, max(0.0, (confidence - conf_floor) / (1.0 - conf_floor)))
        conf_multiplier = 0.6 + (conf_norm * 0.8)  # 0.6x to 1.4x
        size_multiplier = conf_multiplier * float(regime_info.get("multiplier", 1.0)) * float(vol_info.get("multiplier", 1.0))
        size_multiplier = max(0.5, min(1.5, size_multiplier))
        max_risk_amount *= size_multiplier
        print(f"   🧠 AI SIZING: ×{size_multiplier:.2f} (conf/regime/vol) => ${max_risk_amount:.2f}")
        
        if action == "buy" and confidence >= confidence_threshold:
            # Calculate position size with ATR-based stops
            stop_loss = signal.get("stop_loss", price * 0.98)
            risk_per_share = price - stop_loss
            atr = signal.get("atr", price * 0.02)  # Fallback ATR estimate
            atr_pct = atr / price if price else 0

            # Liquidity + volatility guardrails (advanced risk controls)
            try:
                if 'df_vol' in locals() and df_vol is not None and not df_vol.empty:
                    if isinstance(df_vol.columns, pd.MultiIndex):
                        df_vol.columns = df_vol.columns.get_level_values(0)
                    if 'Volume' in df_vol.columns:
                        avg_volume = float(df_vol['Volume'].tail(20).mean())
                        if avg_volume < min_avg_volume:
                            print(f"   💧 SKIP - Low liquidity (avg vol {avg_volume:,.0f} < {min_avg_volume:,.0f})")
                            notify_bot_status("WARNING", f"Low liquidity for {ticker_212}: {avg_volume:,.0f}")
                            continue
            except Exception as e:
                print(f"   ⚠️  Liquidity check failed: {e}")

            if atr_pct > max_atr_pct:
                print(f"   🌪️  SKIP - Volatility too high (ATR {atr_pct*100:.1f}% > {max_atr_pct*100:.1f}%)")
                notify_bot_status("WARNING", f"Volatility too high for {ticker_212}: {atr_pct*100:.1f}%")
                continue
            
            if risk_per_share > 0:
                # Calculate ideal quantity based on risk
                qty = max_risk_amount / price  # Use price directly for max shares we can afford
                
                # Trading212 supports fractional shares! Use them when cash is tight
                if free_cash < 10:  # Less than $10 free - use fractional shares
                    qty = min(qty, free_cash / price * 0.95)  # Use 95% of free cash
                    qty = round(qty, 3)  # Round to 3 decimal places for fractional
                    
                    # Trading212 supports fractional shares - allow micro trades
                    min_order_value = 0.10  # $0.10 minimum for micro accounts
                    if qty * price < min_order_value:
                        print(f"   💸 SKIP - Below minimum order (need ${min_order_value:.2f}, have ${free_cash:.2f})")
                        continue
                    
                    if qty < 0.001:  # Minimum fractional share
                        print(f"   💸 SKIP - Amount too small (${free_cash:.2f} free)")
                        notify_bot_status("WARNING", f"Amount too small for {ticker_212}: ${free_cash:.2f}")
                        continue
                    print(f"   🔸 FRACTIONAL: Buying {qty:.3f} shares with ${free_cash:.2f}")
                else:
                    # Normal mode - whole shares
                    qty = max(1, round(qty))  # At least 1 share, round to whole number
                    qty = min(qty, 100)  # Cap at 100 shares (Trading212 limit)
                
                cost = qty * price
                if qty < min_qty:
                    print(f"   💸 SKIP - Below minimum quantity ({qty:.3f} < {min_qty})")
                    notify_bot_status("WARNING", f"Min qty not met for {ticker_212}: {qty:.3f} < {min_qty}")
                    continue
                if cost < min_order_value:
                    print(f"   💸 SKIP - Below minimum order value (${cost:.2f} < ${min_order_value})")
                    notify_bot_status("WARNING", f"Min order value not met for {ticker_212}: ${cost:.2f} < ${min_order_value}")
                    continue
                if cost > free_cash:
                    qty = max(1, int(free_cash / price))
                    qty = min(qty, 100)  # Still enforce cap
                    cost = qty * price
                    if cost > free_cash:  # Can't afford even 1 share
                        print(f"   💸 SKIP - Insufficient funds (need ${cost:.2f}, have ${free_cash:.2f})")
                        notify_bot_status("WARNING", f"Insufficient funds for {ticker_212}: need ${cost:.2f}, have ${free_cash:.2f}")
                        continue
                
                # Calculate profit targets (dynamic by regime)
                regime_rr = 1.0
                if regime_info.get("regime") == "trend":
                    regime_rr = 1.5
                elif regime_info.get("regime") == "range":
                    regime_rr = 0.8
                elif regime_info.get("regime") == "volatile":
                    regime_rr = 0.7
                profit_target = risk_mgr.calculate_profit_target(price, atr, risk_reward_ratio=regime_rr)
                
                print(f"   🟢 BUY {qty} shares @ ${price:.2f} - {reason}")
                print(f"      Confidence: {confidence*100:.0f}% | Risk: ${risk_per_share * qty:.2f}")
                print(f"      Stop: ${stop_loss:.2f} | Target: ${profit_target:.2f}")
                
                if not dry_run:
                    try:
                        order_result = place_market_order(ticker_212, qty, confirm=True)
                        order_id = order_result.get('id')
                        # Verify order has valid ID
                        if not order_id or order_id == 'N/A':
                            raise RuntimeError(f"Order missing ID: {order_result}")
                        print(f"      ✅ Order placed: {order_id}")
                        risk_mgr.add_position(ticker_yf, qty, price, atr, reason, stop_loss=stop_loss, profit_target=profit_target)
                        extra_features = _compute_feature_pack(df_vol if 'df_vol' in locals() else None, signal)
                        log_trade(ticker_212, "buy", qty, price, confidence=confidence, reason=reason, metadata={
                            "ai_boosts": ai_boosts,
                            "regime": regime_info,
                            "volatility": vol_info,
                            "features": extra_features
                        })
                        results[ticker_212] = {"action": "buy", "qty": qty, "order_id": order_id}
                        notify_trade(ticker_212, "buy", qty, price, reason)
                        time.sleep(1)
                    except Exception as e:
                        error_msg = str(e)
                        print(f"      ❌ Order failed: {error_msg}")
                        notify_bot_status("ERROR", f"Order failed for {ticker_212}: {error_msg}")
                        results[ticker_212] = {"action": "error", "error": error_msg}
                        if "rate limit" in error_msg.lower() or "429" in error_msg:
                            print(f"      ⏳ Rate limited - waiting 5 seconds...")
                            time.sleep(5)
                else:
                    print(f"      🔵 DRY RUN - No order placed")
                    results[ticker_212] = {"action": "buy_dryrun", "qty": qty}
        
        elif action == "sell":
            # Execute sell for positions we own
            if ticker_yf in positions:
                qty_owned = positions[ticker_yf].get('quantity', 0)
                
                print(f"   🔴 SELL {qty_owned} shares @ ${price:.2f} - {reason}")
                
                if not dry_run and qty_owned > 0:
                    try:
                        order_result = place_market_order(ticker_212, -qty_owned, confirm=True)
                        print(f"      ✅ Sell order placed: {order_result.get('id', 'N/A')}")
                        
                        # Remove from positions
                        del positions[ticker_yf]
                        risk_mgr.save_positions(positions)
                        
                        log_trade(ticker_212, "sell", qty_owned, price, reason=reason, metadata={
                            "regime": regime_info,
                            "volatility": vol_info,
                            "ai_boosts": ai_boosts
                        })
                        
                        results[ticker_212] = {"action": "sell", "qty": qty_owned, "order": order_result}
                    except Exception as e:
                        print(f"      ❌ Sell failed: {e}")
                        results[ticker_212] = {"action": "error", "error": str(e)}
                else:
                    print(f"      🔵 DRY RUN - No sell order placed")
                    results[ticker_212] = {"action": "sell_dryrun", "qty": qty_owned}
            else:
                print(f"   🔴 SELL signal but no position - {reason}")
                results[ticker_212] = {"action": "sell_signal", "reason": reason}
        
        time.sleep(0.5)  # Rate limiting
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Live trading engine")
    parser.add_argument("--dry-run", action="store_true", help="Simulate orders without placing them")
    parser.add_argument("--tickers", nargs="+", help="Specific tickers to trade (e.g., AAPL_US_EQ MSFT_US_EQ)")
    args = parser.parse_args()
    
    # Get tickers from args or env
    if args.tickers:
        tickers = args.tickers
    else:
        tickers_str = os.getenv("TRADING212_DAILY_TICKERS", "AAPL_US_EQ,MSFT_US_EQ,GOOGL_US_EQ")
        tickers = [t.strip() for t in tickers_str.split(",")]
    
    print("=" * 60)
    print(f"🤖 LIVE TRADING ENGINE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Tickers: {len(tickers)}")
    print("=" * 60)
    
    results = execute_live_trading(tickers, dry_run=args.dry_run)
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    for ticker, result in results.items():
        action = result.get("action", "unknown")
        print(f"{ticker:15s} | {action.upper():12s} | {result.get('reason', '')[:30]}")
    print("=" * 60)
