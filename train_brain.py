#!/usr/bin/env python3
"""
SmartBot Brain Trainer — Backtest & Learn from Historical Data
================================================================
Downloads historical price data for all tickers, runs SmartBot's 
momentum scoring engine on every bar, simulates trades, and feeds 
results to the brain.

This turns months of price history into hundreds of learning experiences,
rapidly growing the brain from LOW to HIGH confidence.
"""
import os
import sys
os.environ["SMARTBOT_DISABLE_TF"] = "1"

import json
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from demo_pipeline import compute_indicators
from smartbot_brain import SmartBotBrain

# Tickers to learn from (current + historical)
TRAIN_TICKERS = [
    "RIVN", "TSLA", "NVDA", "AMD", "COIN", "SOFI", "PLTR",
    "GME", "AMC", "SNAP", "AAL", "CCL", "NIO", "LCID", "HOOD",
    "NOK", "AAPL", "MSFT", "GOOGL", "META", "F", "PLUG", "PTON",
]

# Simulated trade parameters
ENTRY_SCORE_MIN = 50       # Same as live
EXIT_PROFIT_PCT = 5.0      # Take profit at +5%
EXIT_LOSS_PCT = -4.0       # Stop loss at -4%
EXIT_MAX_BARS = 20         # Max hold = 20 bars (~5 hours at 15min)


def compute_momentum_score_simple(df: pd.DataFrame, idx: int) -> dict:
    """Simplified momentum scoring for backtesting (matches live logic)."""
    if idx < 30:
        return {"score": 0, "action": "hold", "factors": [], "rsi": 50}
    
    latest = df.iloc[idx]
    prev = df.iloc[idx - 1]
    price = float(latest["Close"])
    atr = float(latest["atr"]) if "atr" in latest and not pd.isna(latest["atr"]) else price * 0.02

    score = 0
    factors = []

    # SMA trend
    if latest["sma_short"] > latest["sma_long"]:
        score += 10
        factors.append("SMA+")
        if prev["sma_short"] <= prev["sma_long"]:
            score += 5
            factors.append("GoldenX")

    # RSI
    rsi = float(latest["rsi"]) if not pd.isna(latest["rsi"]) else 50
    if 30 <= rsi <= 50:
        score += 15
        factors.append("RSI:buy_zone")
    elif 50 < rsi <= 65:
        score += 10
        factors.append("RSI:neutral")
    elif rsi < 30:
        score += 8
        factors.append("RSI:oversold")
    elif rsi > 75:
        score -= 5
        factors.append("RSI:overbought")

    # MACD
    macd_hist = float(latest["macd_hist"]) if not pd.isna(latest["macd_hist"]) else 0
    macd_prev = float(prev["macd_hist"]) if not pd.isna(prev["macd_hist"]) else 0
    if macd_hist > 0:
        score += 8
        factors.append("MACD+")
        if macd_hist > macd_prev:
            score += 7
            factors.append("MACD++")

    # Bollinger Bands
    bb_range = latest["bb_upper"] - latest["bb_lower"]
    if bb_range > 0:
        bb_pos = (price - latest["bb_lower"]) / bb_range
        if 0.3 <= bb_pos <= 0.6:
            score += 10
            factors.append("BB:mid")
        elif bb_pos < 0.3:
            score += 7
            factors.append("BB:low")
        elif bb_pos > 0.85:
            score -= 3
            factors.append("BB:hi!")

    # Volume
    vol_mean = df["Volume"].iloc[max(0, idx-20):idx].mean() if "Volume" in df.columns else 0
    if vol_mean > 0 and latest["Volume"] > vol_mean * 1.3:
        score += 10
        factors.append("Vol+")

    # Price momentum
    pct_1h = (price - float(prev["Close"])) / float(prev["Close"]) * 100
    if pct_1h > 0.5:
        score += 10
        factors.append("momentum:strong_up")
    elif pct_1h > 0.2:
        score += 6
        factors.append("momentum:up")

    # VWAP
    if "vwap" in latest.index and not pd.isna(latest.get("vwap")):
        vwap = float(latest["vwap"])
        if price < vwap * 0.998:
            score += 10
            factors.append("VWAP:buy")
        elif price < vwap * 1.002:
            score += 5
            factors.append("VWAP:at")

    score = max(0, min(100, score))

    # Regime detection (simple)
    returns = df["Close"].iloc[max(0, idx-20):idx].pct_change().dropna()
    trend_strength = abs(returns.mean()) if len(returns) > 5 else 0
    vol = returns.std() if len(returns) > 5 else 0
    
    if trend_strength > 0.02:
        regime = "trend"
    elif vol > 0.03:
        regime = "volatile"
    elif trend_strength < 0.005:
        regime = "range"
    else:
        regime = "normal"

    return {
        "score": score,
        "action": "buy" if score >= ENTRY_SCORE_MIN else "hold",
        "factors": factors,
        "rsi": rsi,
        "price": price,
        "atr": atr,
        "regime": regime,
    }


def backtest_ticker(ticker: str, brain: SmartBotBrain, 
                    period: str = "60d", interval: str = "15m") -> dict:
    """Backtest a single ticker and feed results to brain."""
    
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty or len(df) < 50:
            # Fallback to 1h data for 6 months if 15m not available
            df = yf.download(ticker, period="6mo", interval="1h", progress=False)
            if df.empty or len(df) < 50:
                # Final fallback to daily data for 2 years
                df = yf.download(ticker, period="2y", interval="1d", progress=False)
                if df.empty or len(df) < 50:
                    return {"ticker": ticker, "error": "no_data", "trades": 0}
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df = compute_indicators(df, sma_short=10, sma_long=30)
        
    except Exception as e:
        return {"ticker": ticker, "error": str(e), "trades": 0}

    trades = []
    position = None  # {"entry_idx", "entry_price", "entry_score", "entry_factors", "regime"}
    
    for i in range(35, len(df) - 1):
        signal = compute_momentum_score_simple(df, i)
        
        if position is None:
            # Look for entry
            if signal["action"] == "buy" and signal["score"] >= ENTRY_SCORE_MIN:
                position = {
                    "entry_idx": i,
                    "entry_price": signal["price"],
                    "entry_score": signal["score"],
                    "entry_factors": signal["factors"],
                    "entry_rsi": signal["rsi"],
                    "regime": signal["regime"],
                    "entry_time": df.index[i],
                }
        else:
            # Check exit conditions
            current_price = float(df.iloc[i]["Close"])
            entry_price = position["entry_price"]
            pnl_pct = (current_price - entry_price) / entry_price * 100
            bars_held = i - position["entry_idx"]
            
            should_exit = False
            exit_reason = ""
            
            if pnl_pct >= EXIT_PROFIT_PCT:
                should_exit = True
                exit_reason = f"PROFIT_TARGET: {pnl_pct:+.1f}%"
            elif pnl_pct <= EXIT_LOSS_PCT:
                should_exit = True
                exit_reason = f"STOP_LOSS: {pnl_pct:+.1f}%"
            elif bars_held >= EXIT_MAX_BARS:
                should_exit = True
                exit_reason = f"TIME_EXIT: {bars_held} bars, {pnl_pct:+.1f}%"
            
            if should_exit:
                # Calculate hold hours
                try:
                    entry_dt = position["entry_time"]
                    exit_dt = df.index[i]
                    hold_hours = (exit_dt - entry_dt).total_seconds() / 3600
                except:
                    hold_hours = bars_held * 0.25  # 15min bars

                pnl_dollar = pnl_pct / 100 * 10  # Simulate $10 position
                
                trade = {
                    "ticker": ticker + "_US_EQ",
                    "pnl": pnl_dollar,
                    "pnl_pct": pnl_pct,
                    "entry_score": position["entry_score"],
                    "entry_factors": position["entry_factors"],
                    "entry_rsi": position["entry_rsi"],
                    "regime": position["regime"],
                    "hold_hours": hold_hours,
                    "reason": exit_reason,
                    "timestamp": str(df.index[i]),
                }
                
                brain.learn_from_trade(trade)
                trades.append(trade)
                position = None
    
    # Stats
    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    total_pnl = sum(t["pnl"] for t in trades)
    
    return {
        "ticker": ticker,
        "trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": len(wins) / len(trades) if trades else 0,
        "total_pnl": round(total_pnl, 2),
    }


def train_brain():
    """Run full backtest training across all tickers."""
    brain = SmartBotBrain()
    initial_trades = brain.brain["total_trades_learned"]
    
    print("=" * 60)
    print("🧠 SMARTBOT BRAIN TRAINER — Backtesting Historical Data")
    print("=" * 60)
    print(f"   Brain has {initial_trades} trades learned")
    print(f"   Training on {len(TRAIN_TICKERS)} tickers")
    print(f"   Period: 3 months of 15-min bars")
    print(f"   Entry: Score ≥{ENTRY_SCORE_MIN}")
    print(f"   Exit: +{EXIT_PROFIT_PCT}% TP / {EXIT_LOSS_PCT}% SL / {EXIT_MAX_BARS} bar timeout")
    print("=" * 60)
    
    all_results = []
    total_new_trades = 0
    
    for ticker in TRAIN_TICKERS:
        print(f"\n📊 Training on {ticker}...", end=" ", flush=True)
        result = backtest_ticker(ticker, brain)
        all_results.append(result)
        
        if result.get("error"):
            print(f"⚠️ {result['error']}")
        else:
            wr = result["win_rate"]
            icon = "🟢" if wr >= 0.5 else "🔴"
            print(f"{icon} {result['trades']}T | WR:{wr:.0%} | P&L:${result['total_pnl']:+.2f}")
            total_new_trades += result["trades"]
    
    # Final report
    final_trades = brain.brain["total_trades_learned"]
    
    print("\n" + "=" * 60)
    print("🧠 BRAIN TRAINING COMPLETE")
    print("=" * 60)
    print(f"   New trades learned: {total_new_trades}")
    print(f"   Total brain experience: {final_trades} trades")
    
    confidence = "LOW" if final_trades < 10 else "MEDIUM" if final_trades < 30 else "HIGH" if final_trades < 100 else "EXPERT"
    print(f"   Brain confidence: {confidence}")
    
    # Show ticker rankings
    print("\n" + brain.get_insights())
    
    # Top/bottom tickers
    valid = [r for r in all_results if not r.get("error") and r["trades"] > 0]
    if valid:
        print("\n🏆 BEST TICKERS (by backtest):")
        top = sorted(valid, key=lambda x: x["win_rate"], reverse=True)[:5]
        for r in top:
            print(f"   🟢 {r['ticker']:6s} WR:{r['win_rate']:.0%} | {r['trades']}T | ${r['total_pnl']:+.2f}")
        
        print("\n⛔ WORST TICKERS (by backtest):")
        bottom = sorted(valid, key=lambda x: x["win_rate"])[:5]
        for r in bottom:
            print(f"   🔴 {r['ticker']:6s} WR:{r['win_rate']:.0%} | {r['trades']}T | ${r['total_pnl']:+.2f}")

    return brain


if __name__ == "__main__":
    brain = train_brain()
