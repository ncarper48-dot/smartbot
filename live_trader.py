#!/usr/bin/env python3
"""
SmartBot V3 — Precision Trading Engine
=======================================
POWER UPGRADES:
  1. Momentum Scoring System (replaces 17 overlapping strategies)
  2. VWAP-aware entries (institutional-grade timing)
  3. Relative Strength Ranking (only trade best movers)
  4. Kelly Criterion position sizing (mathematically optimal bets)
  5. Smart Capital Recycling (auto-close stale positions to free cash)
  6. Data Cache (each ticker downloaded ONCE, reused everywhere → 60% faster)
  7. Full AI layers retained (MTF, pattern, sentiment, regime, volatility, ensemble)
"""
import json
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
from smartbot_brain import SmartBotBrain
import sys
sys.path.append('ml')
from ml.predict_signal import predict_signal, load_model

# Enhanced AI/ML integration
try:
    from ml.deep_learning_model import EnsemblePredictor
    from ml.sentiment_analysis import get_sentiment_boost, MarketMoodAnalyzer
    from ml.multi_timeframe import analyze_all_timeframes, check_timeframe_alignment
    from ml.pattern_recognition import analyze_patterns, get_pattern_signal
    from ml.volatility_forecast import get_volatility_regime
    from ml.regime_classifier import classify_regime
    ENHANCED_AI_AVAILABLE = True
    print("🚀 FULL AI POWER MODE V3 ENABLED")
except ImportError as e:
    ENHANCED_AI_AVAILABLE = False
    print(f"⚠️ Enhanced AI features not fully available: {e}")

# ---------------------------------------------------------------------------
#  OVERNIGHT WATCHLIST — load pre-computed edge scores from overnight engine
# ---------------------------------------------------------------------------
OVERNIGHT_WATCHLIST_FILE = "/home/tradebot/overnight_watchlist.json"

def load_overnight_watchlist() -> dict:
    """Load overnight_watchlist.json. Returns dict: symbol -> edge data."""
    try:
        with open(OVERNIGHT_WATCHLIST_FILE) as f:
            data = json.load(f)
        # Check freshness (< 24 hours old)
        ts = data.get("timestamp", "")
        if ts:
            age = datetime.now() - datetime.fromisoformat(ts)
            if age.total_seconds() > 86400:
                print("   ⏳ Overnight watchlist stale (>24h), ignoring")
                return {}
        wl = {}
        for entry in data.get("watchlist", []):
            sym = entry.get("symbol", "")
            if sym:
                wl[sym] = entry
        return wl
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"   ⚠️ Watchlist load: {e}")
        return {}

# ---------------------------------------------------------------------------
#  DATA CACHE — download once per ticker, reuse everywhere
# ---------------------------------------------------------------------------
_data_cache: dict = {}

def _cached_download(ticker_yf: str, period: str, interval: str) -> pd.DataFrame:
    """Download data once per (ticker, period, interval) combo and cache it."""
    key = (ticker_yf, period, interval)
    if key not in _data_cache:
        df = yf.download(ticker_yf, period=period, interval=interval, progress=False)
        if not df.empty and isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        _data_cache[key] = df
    return _data_cache[key].copy() if not _data_cache[key].empty else pd.DataFrame()


# ---------------------------------------------------------------------------
#  MOMENTUM SCORING — one precise score replaces 17 overlapping strategies
# ---------------------------------------------------------------------------
def compute_momentum_score(df: pd.DataFrame) -> dict:
    """Compute a 0-100 momentum score from all indicators.

    Each factor contributes points. Higher score = stronger buy signal.
    Returns dict with total score, sub-scores, price, and stop/target info.
    """
    if df.empty or len(df) < 30:
        return {"score": 0, "action": "hold", "reason": "insufficient data"}

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3] if len(df) >= 3 else prev
    price = float(latest["Close"])
    atr = float(latest["atr"]) if "atr" in latest and not pd.isna(latest["atr"]) else price * 0.02

    score = 0
    factors = []

    # --- 1. SMA trend (0-15 pts) ---
    if latest["sma_short"] > latest["sma_long"]:
        score += 10
        factors.append("SMA+")
        if prev["sma_short"] <= prev["sma_long"]:
            score += 5
            factors.append("GoldenX")

    # --- 2. RSI zone (0-15 pts) ---
    rsi = float(latest["rsi"]) if not pd.isna(latest["rsi"]) else 50
    if 30 <= rsi <= 50:
        score += 15
        factors.append(f"RSI:{rsi:.0f}*")
    elif 50 < rsi <= 65:
        score += 10
        factors.append(f"RSI:{rsi:.0f}")
    elif rsi < 30:
        score += 8
        factors.append(f"RSI:{rsi:.0f}!")
    elif rsi > 75:
        score -= 5
        factors.append(f"RSI:{rsi:.0f}X")

    # --- 3. MACD momentum (0-15 pts) ---
    macd_hist = float(latest["macd_hist"]) if not pd.isna(latest["macd_hist"]) else 0
    macd_hist_prev = float(prev["macd_hist"]) if not pd.isna(prev["macd_hist"]) else 0
    if macd_hist > 0:
        score += 8
        factors.append("MACD+")
        if macd_hist > macd_hist_prev:
            score += 7
            factors.append("MACD++")

    # --- 4. Bollinger Band position (0-10 pts) ---
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

    # --- 5. Volume confirmation (0-10 pts) ---
    vol_mean = df["Volume"].rolling(20).mean().iloc[-1] if "Volume" in df.columns else 0
    if vol_mean > 0 and latest["Volume"] > vol_mean * 1.3:
        score += 10
        factors.append("Vol+")
    elif vol_mean > 0 and latest["Volume"] > vol_mean:
        score += 5
        factors.append("Vol")

    # --- 6. Price momentum (0-15 pts) ---
    pct_1h = (price - float(prev["Close"])) / float(prev["Close"]) * 100
    pct_3h = (price - float(prev2["Close"])) / float(prev2["Close"]) * 100
    if pct_1h > 0.5:
        score += 10
        factors.append(f"+{pct_1h:.1f}%")
    elif pct_1h > 0.2:
        score += 6
        factors.append(f"+{pct_1h:.1f}%")
    elif pct_1h < -0.5:
        score -= 5
        factors.append(f"{pct_1h:.1f}%!")

    if pct_3h > 0.8:
        score += 5
        factors.append("3h+")

    # --- 7. VWAP position (0-10 pts) ---
    if "vwap" in latest.index and not pd.isna(latest.get("vwap")):
        vwap = float(latest["vwap"])
        if price < vwap * 0.998:
            score += 10
            factors.append("VWAP:buy")
        elif price < vwap * 1.002:
            score += 5
            factors.append("VWAP:at")
        else:
            score -= 3
            factors.append("VWAP:hi!")

    # --- 8. Opening surge bonus (0-10 pts) ---
    try:
        import pytz
        et = pytz.timezone('America/New_York')
        now_et = datetime.now(et)
        market_open = now_et.replace(hour=9, minute=30, second=0)
        mins_since_open = (now_et - market_open).total_seconds() / 60
        if 0 <= mins_since_open <= 30 and pct_1h > 0.1:
            score += 10
            factors.append("OpenSurge")
    except Exception:
        pass

    # Clamp
    score = max(0, min(100, score))

    # Action + confidence from score
    if score >= 50:
        action = "buy"
        confidence = 0.50 + (score - 50) / 100
    elif score <= 15 and rsi > 75:
        action = "sell"
        confidence = 0.70
    else:
        action = "hold"
        confidence = 0.0

    confidence = min(confidence, 1.0)
    stop_loss = price - (atr * 2)
    reason_str = " + ".join(factors[:6]) if factors else "No signals"

    return {
        "action": action,
        "price": price,
        "confidence": confidence,
        "reason": f"Score:{score}/100 [{reason_str}]",
        "stop_loss": stop_loss,
        "atr": atr,
        "score": score,
        "factors": factors,
        "rsi": rsi,
        "pct_1h": pct_1h,
    }


# ---------------------------------------------------------------------------
#  RELATIVE STRENGTH RANKING — trade only the best movers
# ---------------------------------------------------------------------------
def rank_tickers_by_strength(tickers_212: list, max_tickers: int = 8) -> list:
    """Rank tickers by relative strength vs SPY. Return top movers only."""
    try:
        spy = _cached_download("SPY", period="2d", interval="1h")
        if spy.empty or len(spy) < 5:
            return tickers_212

        spy_change = (float(spy["Close"].iloc[-1]) - float(spy["Close"].iloc[-5])) / float(spy["Close"].iloc[-5])

        scored = []
        for t212 in tickers_212:
            tyf = t212.replace("_US_EQ", "").replace("_UK_EQ", "").replace("_DE_EQ", "")
            try:
                d = _cached_download(tyf, period="2d", interval="1h")
                if d.empty or len(d) < 5:
                    scored.append((t212, 0))
                    continue
                chg = (float(d["Close"].iloc[-1]) - float(d["Close"].iloc[-5])) / float(d["Close"].iloc[-5])
                rs = chg - spy_change
                scored.append((t212, rs))
            except Exception:
                scored.append((t212, 0))

        scored.sort(key=lambda x: abs(x[1]), reverse=True)
        top = [t for t, _ in scored[:max_tickers]]

        skipped = len(tickers_212) - len(top)
        if skipped > 0:
            print(f"   📊 RS Filter: Top {max_tickers}/{len(tickers_212)} selected, {skipped} flat skipped")

        return top
    except Exception as e:
        print(f"   ⚠️ RS ranking failed: {e}")
        return tickers_212


# ---------------------------------------------------------------------------
#  KELLY CRITERION — mathematically optimal position sizing
# ---------------------------------------------------------------------------
def kelly_fraction(win_rate: float = 0.55, avg_win: float = 0.015, avg_loss: float = 0.01) -> float:
    """Compute half-Kelly fraction for position sizing."""
    if avg_loss == 0 or avg_win == 0:
        return 0.15
    b = avg_win / avg_loss
    f = (win_rate * b - (1 - win_rate)) / b
    f = max(0.05, min(0.45, f))
    return f / 2  # Half-Kelly for safety


def get_historical_stats() -> dict:
    """Pull win rate and avg win/loss from performance history."""
    try:
        with open("performance_history.json", "r") as fp:
            data = json.load(fp)
        trades = data if isinstance(data, list) else data.get("trades", [])
        if not trades or len(trades) < 5:
            return {"win_rate": 0.55, "avg_win": 0.015, "avg_loss": 0.01}

        wins = [t for t in trades if t.get("pnl", t.get("result", 0)) > 0]
        losses = [t for t in trades if t.get("pnl", t.get("result", 0)) <= 0]

        win_rate = len(wins) / len(trades) if trades else 0.55
        avg_win = np.mean([abs(t.get("pnl", t.get("result", 0))) for t in wins]) if wins else 0.015
        avg_loss = np.mean([abs(t.get("pnl", t.get("result", 0))) for t in losses]) if losses else 0.01

        return {"win_rate": win_rate, "avg_win": avg_win, "avg_loss": avg_loss}
    except Exception:
        return {"win_rate": 0.55, "avg_win": 0.015, "avg_loss": 0.01}


# ---------------------------------------------------------------------------
#  SMART CAPITAL RECYCLING — close stale positions to free cash
# ---------------------------------------------------------------------------
def check_stale_positions(risk_mgr: AdvancedRiskManager, max_hours: float = 6.0, min_move_pct: float = 0.3) -> list:
    """Find positions held > max_hours that haven't gained > min_move_pct.
    Close them to free capital for better opportunities.
    """
    exits = []
    positions = risk_mgr.get_open_positions()
    now = datetime.now()

    for ticker, pos in positions.items():
        try:
            entry_time = datetime.fromisoformat(pos.get("entry_time", now.isoformat()))
            hours_held = (now - entry_time).total_seconds() / 3600
            if hours_held < max_hours:
                continue

            entry_price = pos["entry_price"]
            current_price = pos.get("current_price", entry_price)
            pnl_pct = (current_price - entry_price) / entry_price * 100

            if pnl_pct < min_move_pct:
                exits.append({
                    "ticker": ticker,
                    "action": "SELL",
                    "reason": f"RECYCLE: {hours_held:.0f}h held, {pnl_pct:+.2f}% — freeing capital",
                    "price": current_price,
                })
                print(f"   ♻️  STALE: {ticker} {hours_held:.0f}h {pnl_pct:+.2f}% — recycling")
        except Exception as e:
            print(f"   ⚠️ Stale check error {ticker}: {e}")

    return exits


# ---------------------------------------------------------------------------
#  END-OF-DAY PROFIT TAKING — Lock in gains before market close
# ---------------------------------------------------------------------------
def end_of_day_close(dry_run: bool = False) -> dict:
    """Close profitable positions before market close to lock in gains.
    
    Strategy:
    - Sell ALL positions in profit (lock in gains over weekend/overnight)
    - Sell positions with tiny losses < -1% (not worth holding)
    - Keep positions with larger losses (give them Monday to recover)
    - Log everything for tracking
    """
    import requests, base64
    from dotenv import load_dotenv
    load_dotenv()
    
    print("\n" + "=" * 60)
    print("🔔 END-OF-DAY PROFIT TAKING — Locking in gains before close")
    print("=" * 60)
    
    results = {}
    risk_mgr = AdvancedRiskManager()
    
    # Get REAL positions from Trading212 API (not local state)
    key = os.getenv('TRADING212_API_KEY')
    secret = os.getenv('TRADING212_API_SECRET')
    base_url = os.getenv('TRADING212_BASE_URL')
    auth = base64.b64encode(f'{key}:{secret}'.encode()).decode()
    headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
    
    try:
        r = requests.get(f'{base_url}/equity/portfolio', headers=headers, timeout=10)
        positions = r.json()
    except Exception as e:
        print(f"   ❌ Failed to fetch positions: {e}")
        return results
    
    if not isinstance(positions, list) or len(positions) == 0:
        print("   ℹ️  No open positions — nothing to close")
        return results
    
    total_locked = 0.0
    total_kept = 0.0
    
    for pos in positions:
        ticker_212 = pos.get('ticker', '')
        ticker = ticker_212.replace('_US_EQ', '')
        qty = pos.get('quantity', 0)
        avg_price = pos.get('averagePrice', 0)
        cur_price = pos.get('currentPrice', 0)
        ppl = pos.get('ppl', 0)
        fx_ppl = pos.get('fxPpl', 0)
        total_ppl = ppl + fx_ppl
        pct_change = ((cur_price - avg_price) / avg_price * 100) if avg_price > 0 else 0
        
        if qty <= 0:
            continue
        
        # Decision logic
        if total_ppl > 0:
            # IN PROFIT — SELL to lock in gains
            action = "SELL"
            reason = f"EOD PROFIT LOCK: {pct_change:+.1f}% (${total_ppl:+.2f})"
            icon = "💰"
        elif pct_change > -1.0:
            # Tiny loss (< 1%) — sell, not worth holding overnight
            action = "SELL"
            reason = f"EOD CLOSE: small loss {pct_change:+.1f}% (${total_ppl:+.2f})"
            icon = "🔄"
        else:
            # Bigger loss — keep for recovery
            action = "HOLD"
            reason = f"EOD HOLD: {pct_change:+.1f}% loss — hold for recovery"
            icon = "⏸️"
        
        print(f"   {icon} {ticker:6s} qty={qty} @ ${cur_price:.2f} | {pct_change:+.1f}% | ${total_ppl:+.2f} → {action}")
        
        if action == "SELL":
            if not dry_run:
                try:
                    order_result = place_market_order(ticker_212, -qty, confirm=True)
                    order_id = order_result.get('id', 'N/A') if isinstance(order_result, dict) else 'N/A'
                    print(f"         ✅ SOLD — Order {order_id}")
                    total_locked += total_ppl
                    # Update risk manager
                    try:
                        risk_mgr.close_position(ticker, cur_price, reason)
                    except Exception:
                        pass
                    log_trade(ticker_212, "sell", qty, cur_price, reason=reason,
                             metadata={"exit_reason": "EOD_PROFIT_TAKE", "pnl": total_ppl})
                    results[ticker_212] = {"action": "sell", "qty": qty, "pnl": total_ppl, "reason": reason}
                except Exception as e:
                    print(f"         ❌ Sell failed: {e}")
                    results[ticker_212] = {"action": "sell_failed", "error": str(e)}
            else:
                print(f"         🧪 DRY RUN — would sell")
                total_locked += total_ppl
                results[ticker_212] = {"action": "sell_dryrun", "qty": qty, "pnl": total_ppl}
        else:
            total_kept += total_ppl
            results[ticker_212] = {"action": "hold", "pnl": total_ppl, "reason": reason}
    
    print(f"\n   📊 EOD Summary: Locked ${total_locked:+.2f} profit | Holding ${total_kept:+.2f} in losses")
    print("=" * 60)
    
    # Notify
    notify_bot_status("EOD_CLOSE", f"Locked ${total_locked:+.2f} profit, holding ${total_kept:+.2f}")
    
    return results


# ---------------------------------------------------------------------------
#  INTRADAY PROFIT TAKING — Lock in gains during the trading day
# ---------------------------------------------------------------------------
def check_intraday_profits(risk_mgr: AdvancedRiskManager,
                          quick_profit_pct: float = 5.0,
                          big_profit_pct: float = 15.0) -> list:
    """Check positions for intraday profit targets + trailing stop protection.
    
    - Big profit (>=15%): Sell all — don't be greedy
    - Quick profit (>=5%): Sell half to lock in gains, let rest ride
    - Trailing stop: If was up >3% but now falling back, sell to protect gains
    - Deep loss (< -8%): Cut losses, brain says stop bleeding
    """
    exits = []
    positions = risk_mgr.get_open_positions()
    
    for ticker, pos in positions.items():
        try:
            entry_price = pos.get("entry_price", 0)
            current_price = pos.get("current_price", entry_price)
            qty = pos.get("quantity", 0)
            atr = pos.get("atr", entry_price * 0.02)
            if entry_price <= 0 or qty <= 0:
                continue
            
            pnl_pct = (current_price - entry_price) / entry_price * 100
            
            # Track highest price seen (trailing stop reference)
            high_price = pos.get("high_price", current_price)
            if current_price > high_price:
                high_price = current_price
                # Update stored high
                try:
                    all_pos = risk_mgr.load_positions()
                    if ticker in all_pos:
                        all_pos[ticker]["high_price"] = high_price
                        risk_mgr.save_positions(all_pos)
                except Exception:
                    pass
            
            if pnl_pct >= big_profit_pct:
                # BIG WIN — sell everything, don't be greedy
                exits.append({
                    "ticker": ticker,
                    "action": "SELL",
                    "reason": f"BIG PROFIT: {pnl_pct:+.1f}% — locking in full gain",
                    "price": current_price,
                })
                print(f"   🔥 BIG PROFIT: {ticker} {pnl_pct:+.1f}% — sell all")
            elif pnl_pct >= quick_profit_pct:
                # Quick profit — sell half, let rest ride
                exits.append({
                    "ticker": ticker,
                    "action": "SELL_PARTIAL",
                    "portion": 0.5,
                    "reason": f"QUICK PROFIT: {pnl_pct:+.1f}% — taking half off",
                    "price": current_price,
                })
                print(f"   💰 QUICK PROFIT: {ticker} {pnl_pct:+.1f}% — sell half")
            elif high_price > entry_price * 1.03 and current_price < high_price - (atr * 1.5):
                # TRAILING STOP: Was up >3% but dropped 1.5 ATR from peak
                drop_from_high = (high_price - current_price) / high_price * 100
                exits.append({
                    "ticker": ticker,
                    "action": "SELL",
                    "reason": f"TRAILING STOP: peaked at +{((high_price-entry_price)/entry_price*100):.1f}%, dropped {drop_from_high:.1f}% from high",
                    "price": current_price,
                })
                print(f"   🛡️ TRAILING STOP: {ticker} dropped {drop_from_high:.1f}% from peak — protecting gains")
            elif pnl_pct <= -8.0:
                # DEEP LOSS — cut it, stop bleeding
                exits.append({
                    "ticker": ticker,
                    "action": "SELL",
                    "reason": f"DEEP LOSS CUT: {pnl_pct:+.1f}% — brain says stop bleeding",
                    "price": current_price,
                })
                print(f"   ✂️ LOSS CUT: {ticker} {pnl_pct:+.1f}% — cutting losses")
        except Exception as e:
            print(f"   ⚠️ Profit check error {ticker}: {e}")
    
    return exits


# ---------------------------------------------------------------------------
#  AUTO-CANCEL STALE ORDERS — Never let capital get stuck again
# ---------------------------------------------------------------------------
def cancel_stale_orders():
    """Cancel any pending orders that are blocking capital."""
    import requests, base64
    from dotenv import load_dotenv
    load_dotenv()
    try:
        key = os.getenv('TRADING212_API_KEY', '')
        secret = os.getenv('TRADING212_API_SECRET', '')
        base_url = os.getenv('TRADING212_BASE_URL', '')
        cred = base64.b64encode(f'{key}:{secret}'.encode()).decode()
        headers = {'Authorization': f'Basic {cred}', 'Content-Type': 'application/json'}
        r = requests.get(f'{base_url}/equity/orders', headers=headers, timeout=10)
        orders = r.json()
        if not isinstance(orders, list) or len(orders) == 0:
            return 0
        cancelled = 0
        for o in orders:
            oid = o.get('id', '')
            status = o.get('status', '')
            if oid and status in ('NEW', 'PENDING', ''):
                try:
                    requests.delete(f'{base_url}/equity/orders/{oid}', headers=headers, timeout=10)
                    print(f"   🗑️ Cancelled stale order: {o.get('ticker','?')} qty={o.get('quantity',0)}")
                    cancelled += 1
                except Exception:
                    pass
        if cancelled:
            print(f"   ✅ Freed capital from {cancelled} stale order(s)")
            time.sleep(1)  # Let API settle
        return cancelled
    except Exception as e:
        print(f"   ⚠️ Order cleanup: {e}")
        return 0


# ---------------------------------------------------------------------------
#  BRAIN TICKER FILTER — Don't waste capital on proven losers
# ---------------------------------------------------------------------------
def brain_filter_tickers(tickers_212: list, brain: 'SmartBotBrain') -> list:
    """Remove tickers that the brain has learned are consistent losers.
    
    Rules:
    - Win rate < 28% with 10+ trades → BLOCKED (proven loser)
    - Win rate < 35% with 20+ trades → BLOCKED (confirmed bad)
    - Active lose streak ≥ 5 → BLOCKED temporarily
    - Win rate > 55% → PRIORITY (move to front)
    """
    filtered = []
    blocked = []
    boosted = []
    
    for t212 in tickers_212:
        ticker = t212.replace('_US_EQ', '').replace('_UK_EQ', '').replace('_DE_EQ', '')
        tm = brain.brain.get('ticker_memory', {}).get(ticker, {})
        trades = tm.get('total_trades', 0)
        wins = tm.get('wins', 0)
        wr = wins / trades if trades > 0 else 0.5
        lose_streak = tm.get('lose_streak', 0)
        avg_pnl = tm.get('avg_pnl', 0)
        
        # Block proven losers
        if trades >= 20 and wr < 0.35 and avg_pnl < -0.05:
            blocked.append(f"{ticker}({wr:.0%}/{trades}T)")
            continue
        if trades >= 10 and wr < 0.28:
            blocked.append(f"{ticker}({wr:.0%}/{trades}T)")
            continue
        if lose_streak >= 5 and trades >= 5:
            blocked.append(f"{ticker}(streak:{lose_streak})")
            continue
        
        # Boost proven winners to front
        if trades >= 10 and wr > 0.55 and avg_pnl > 0:
            boosted.append(t212)
        else:
            filtered.append(t212)
    
    # Boosted tickers go first
    result = boosted + filtered
    
    if blocked:
        print(f"   🧠 Brain BLOCKED {len(blocked)} losers: {', '.join(blocked)}")
    if boosted:
        print(f"   🧠 Brain PRIORITY: {', '.join(t.replace('_US_EQ','') for t in boosted)}")
    
    return result


# ---------------------------------------------------------------------------
#  MAIN EXECUTION ENGINE
# ---------------------------------------------------------------------------
def execute_live_trading(tickers_212: list, dry_run: bool = False) -> dict:
    """Execute live trading with all V4 power upgrades."""
    global _data_cache
    _data_cache = {}  # Fresh cache each cycle

    ml_status = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ml_signal": "",
        "confidence": "",
        "model_status": "V4-BrainArmed"
    }
    results = {}
    notify_bot_status("RUNNING", f"SmartBot V4 at {datetime.now().strftime('%H:%M:%S')}")

    # --- PHASE -1: Cancel any stale orders blocking capital ---
    print("\n🗑️ Checking for stale orders...")
    cancel_stale_orders()

    risk_mgr = AdvancedRiskManager()
    brain = SmartBotBrain()  # Self-learning intelligence

    # --- PHASE 0: Update position prices ---
    print("\n📊 Updating position prices...")
    positions = risk_mgr.load_positions()
    for ticker in list(positions.keys()):
        try:
            ticker_yf = ticker.replace("_US_EQ", "")
            d = _cached_download(ticker_yf, "1d", "1h")
            if not d.empty:
                risk_mgr.update_position(ticker_yf, float(d["Close"].iloc[-1]))
        except Exception as e:
            print(f"   ⚠️ Price update {ticker}: {e}")

    # --- PHASE 1: Smart Capital Recycling + Intraday Profit Taking ---
    print("\n♻️  Checking stale positions...")
    stale_exits = check_stale_positions(risk_mgr, max_hours=6.0, min_move_pct=0.3)
    exit_signals = risk_mgr.check_exit_signals()

    # --- INTRADAY PROFIT TAKING: Lock in gains at +5% ---
    print("\n💰 Checking intraday profit targets...")
    profit_exits = check_intraday_profits(risk_mgr)

    all_exits = profit_exits + stale_exits + exit_signals

    for exit_sig in all_exits:
        ticker = exit_sig["ticker"]
        ticker_212 = ticker + "_US_EQ"
        reason = exit_sig["reason"]
        price = exit_sig["price"]
        action = exit_sig["action"]

        positions = risk_mgr.get_open_positions()
        qty = positions.get(ticker, {}).get("quantity", 0)

        if action == "SELL" and qty > 0:
            print(f"🔴 EXIT: {ticker} {qty} @ ${price:.2f} — {reason}")
            notify_trade(ticker, "sell", qty, price, reason)
            if not dry_run:
                try:
                    order_result = place_market_order(ticker_212, -qty, confirm=True)
                    print(f"   ✅ Sold: {order_result.get('id', 'N/A')}")
                    # Teach brain from this trade
                    pos_data = positions.get(ticker, {})
                    entry_price = pos_data.get("entry_price", price)
                    entry_time = pos_data.get("entry_time", datetime.now().isoformat())
                    try:
                        hold_hours = (datetime.now() - datetime.fromisoformat(entry_time)).total_seconds() / 3600
                    except:
                        hold_hours = 6
                    pnl = (price - entry_price) * qty
                    pnl_pct = ((price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                    brain.learn_from_trade({
                        "ticker": ticker, "pnl": pnl, "pnl_pct": pnl_pct,
                        "entry_score": pos_data.get("score", 50),
                        "entry_factors": pos_data.get("factors", []),
                        "entry_rsi": pos_data.get("rsi", 50),
                        "regime": pos_data.get("regime", "normal"),
                        "hold_hours": hold_hours,
                        "reason": reason,
                    })
                    risk_mgr.close_position(ticker, price, reason)
                    log_trade(ticker_212, "sell", qty, price, reason=reason, metadata={"exit_reason": reason})
                    results[ticker_212] = {"action": "sell", "qty": qty, "reason": reason}
                except Exception as e:
                    print(f"   ❌ Sell failed: {e}")
            else:
                results[ticker_212] = {"action": "sell_dryrun", "qty": qty, "reason": reason}

        elif action == "SELL_PARTIAL":
            portion = exit_sig.get("portion", 0.5)
            qty_sell = max(0.1, round(qty * portion, 1))
            print(f"💰 PARTIAL: {ticker} {qty_sell}/{qty} @ ${price:.2f} — {reason}")
            if not dry_run and qty_sell > 0:
                try:
                    order_result = place_market_order(ticker_212, -qty_sell, confirm=True)
                    positions[ticker]["quantity"] -= qty_sell
                    risk_mgr.save_positions(positions)
                    log_trade(ticker_212, "sell_partial", qty_sell, price, reason=reason)
                    results[ticker_212] = {"action": "sell_partial", "qty": qty_sell}
                except Exception as e:
                    print(f"   ❌ Partial sell failed: {e}")

    # --- PHASE 2: Account + risk ---
    try:
        account = get_account_cash()
        free_cash = account.get("free", 0)
        total_cash = account.get("total", 0)
        print(f"\n💰 Account: ${total_cash:.2f} total | ${free_cash:.2f} free")
    except Exception as e:
        print(f"⚠️ Account fetch failed: {e}")
        free_cash, total_cash = 0, 100

    dynamic_risk = risk_mgr.get_dynamic_risk()
    if dynamic_risk == 0:
        print("\n🛑 CIRCUIT BREAKER — no new trades")
        return results

    regime_name, regime_mult = risk_mgr.get_market_regime()
    adjusted_risk = max(0.01, min(0.30, dynamic_risk * regime_mult))
    print(f"📊 Risk: {dynamic_risk*100:.1f}% x {regime_mult:.2f} = {adjusted_risk*100:.1f}%")

    hist_stats = get_historical_stats()
    kelly_f = kelly_fraction(hist_stats["win_rate"], hist_stats["avg_win"], hist_stats["avg_loss"])
    print(f"📐 Kelly: {kelly_f*100:.1f}% (WR={hist_stats['win_rate']:.0%})")

    # --- PHASE 3: Brain Filter + Relative Strength Ranking + Overnight Edge ---
    print(f"\n🧠 Brain filtering {len(tickers_212)} tickers...")
    tickers_brain_filtered = brain_filter_tickers(tickers_212, brain)
    print(f"\n📈 Ranking {len(tickers_brain_filtered)} tickers by relative strength...")
    tickers_ranked = rank_tickers_by_strength(tickers_brain_filtered, max_tickers=10)

    overnight_wl = load_overnight_watchlist()
    if overnight_wl:
        print(f"🌙 Overnight watchlist loaded ({len(overnight_wl)} tickers)")
        # Re-sort tickers: priority buys first, then by edge score, then original order
        def _sort_key(t):
            sym = t.replace("_US_EQ", "").replace("_UK_EQ", "").replace("_DE_EQ", "")
            entry = overnight_wl.get(sym, {})
            edge = entry.get("edge_score", 0)
            is_priority = 1 if entry.get("recommendation") == "PRIORITY BUY" else 0
            return (-is_priority, -edge)
        tickers_ranked.sort(key=_sort_key)
        # Show overnight picks
        for t in tickers_ranked[:5]:
            sym = t.replace("_US_EQ", "")
            entry = overnight_wl.get(sym, {})
            if entry:
                print(f"   🌙 {sym}: Edge {entry.get('edge_score', 0):+.1f} — {entry.get('recommendation', '?')}")
    else:
        print("   (No overnight watchlist — running without edge data)")

    print(f"   🏆 Trading: {', '.join(t.replace('_US_EQ','') for t in tickers_ranked)}")

    # --- PHASE 4: Load ML + AI once ---
    try:
        ml_model = load_model()
    except Exception:
        ml_model = None

    ensemble_predictor = None
    market_mood_mult = 1.0

    if ENHANCED_AI_AVAILABLE:
        try:
            ensemble_predictor = EnsemblePredictor()
            ensemble_predictor.load_models()
            mma = MarketMoodAnalyzer()
            mood_val, mood_desc = mma.get_market_mood()
            should_trade, trade_reason = mma.should_trade_today()
            print(f"🌐 Market Mood: {mood_desc} ({mood_val:.3f})")
            if not should_trade:
                print(f"   ⚠️ {trade_reason}")
                market_mood_mult = 0.7
        except Exception as e:
            print(f"⚠️ AI init: {e}")

    # --- PHASE 5: Scan with Momentum Scoring ---
    print(f"\n🔍 Scanning {len(tickers_ranked)} tickers — Momentum Scoring V3...")

    confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.40"))
    min_qty = float(os.getenv("TRADING212_MIN_QTY", "0.2"))
    min_order_value = float(os.getenv("TRADING212_MIN_ORDER_VALUE", "5"))
    min_avg_volume = float(os.getenv("TRADING212_MIN_AVG_VOLUME", "200000"))
    max_atr_pct = float(os.getenv("TRADING212_MAX_ATR_PCT", "0.05"))

    for ticker_212 in tickers_ranked:
        ticker_yf = ticker_212.replace("_US_EQ", "").replace("_UK_EQ", "").replace("_DE_EQ", "")

        if not risk_mgr.check_position_limits(ticker_yf):
            continue

        print(f"\n🔍 {ticker_yf}...")

        # --- Get cached data ---
        df_15m = _cached_download(ticker_yf, "5d", "15m")
        if df_15m.empty or len(df_15m) < 30:
            print(f"   ⏸️ No data")
            results[ticker_212] = {"action": "hold", "reason": "no data"}
            continue

        df_15m = compute_indicators(df_15m, sma_short=10, sma_long=30)

        # --- MOMENTUM SCORE ---
        signal = compute_momentum_score(df_15m)
        action = signal["action"]
        price = signal.get("price", 0)
        reason = signal.get("reason", "")
        confidence = signal.get("confidence", 0)
        mscore = signal.get("score", 0)
        atr = signal.get("atr", price * 0.02)

        print(f"   📊 {reason}")

        # === AI LAYERS ===
        ai_boosts = []
        regime_info = {"regime": "normal", "trend_strength": 0.0, "multiplier": 1.0}
        vol_info = {"regime": "unknown", "multiplier": 1.0}

        if ENHANCED_AI_AVAILABLE:
            # MTF
            try:
                mtf = analyze_all_timeframes(ticker_yf)
                if mtf["confluence"] > 0.75 and action == "buy":
                    confidence *= 1.2
                    ai_boosts.append(f"MTF:{mtf['confluence']:.2f}")
                    print(f"   ⏰ MTF BULLISH ({mtf['confluence']:.2f}) +20%")
                elif abs(mtf["confluence"]) < 0.3:
                    confidence *= 0.8
                    print(f"   ⏰ MTF Mixed ({mtf['confluence']:.2f}) -20%")
            except Exception as e:
                print(f"   ⚠️ MTF: {e}")

            # Regime
            try:
                df_regime = _cached_download(ticker_yf, "10d", "1h")
                if not df_regime.empty:
                    regime_info = classify_regime(df_regime)
                    print(f"   🧭 Regime: {regime_info['regime'].upper()} T={regime_info['trend_strength']:.3f}")
            except Exception as e:
                print(f"   ⚠️ Regime: {e}")

            # Pattern
            try:
                df_daily = _cached_download(ticker_yf, "60d", "1d")
                if not df_daily.empty:
                    patterns = analyze_patterns(df_daily)
                    ps, pc = get_pattern_signal(patterns)
                    if ps == action and pc > 0.6:
                        confidence *= 1.25
                        ai_boosts.append(f"Pat:{pc:.2f}")
                        print(f"   📊 Pattern confirms +25%")
                    elif ps != "hold" and ps != action:
                        confidence *= 0.75
                        print(f"   📊 Pattern conflicts -25%")
            except Exception as e:
                print(f"   ⚠️ Pattern: {e}")

            # Sentiment
            try:
                sb, sc = get_sentiment_boost(ticker_yf)
                if sb != 1.0:
                    confidence *= sb
                    ai_boosts.append(f"Sent:{sb:.2f}")
                    print(f"   📰 Sentiment: {sb:.2f}x")
            except Exception as e:
                print(f"   ⚠️ Sentiment: {e}")

            # Volatility
            try:
                vol_info = get_volatility_regime(df_15m, window=60)
                if vol_info["regime"] in ("high", "low"):
                    confidence *= vol_info["multiplier"]
                    print(f"   📉 Vol: {vol_info['regime'].upper()} ({vol_info['vol']:.4f})")
            except Exception as e:
                print(f"   ⚠️ Vol: {e}")

            # Regime alignment
            if action == "buy":
                if regime_info["regime"] == "trend":
                    confidence *= 1.10
                    ai_boosts.append("Trend")
                    print(f"   📌 TREND boost +10%")
                elif regime_info["regime"] == "volatile":
                    confidence *= 0.80
                    print(f"   📌 VOLATILE -20%")

        confidence *= market_mood_mult
        confidence = min(confidence, 1.0)

        # Ensemble
        if ENHANCED_AI_AVAILABLE and ensemble_predictor and action in ("buy", "sell"):
            try:
                if len(df_15m) >= 60:
                    recent = df_15m["Close"].values[-60:]
                    feats = {"rsi": signal.get("rsi", 50)}
                    es, ec, _ = ensemble_predictor.get_ensemble_signal(recent, feats)
                    print(f"   🤖 Ensemble: sig={es} conf={ec:.2f}")
                    if (action == "buy" and es == 1) or (action == "sell" and es == -1):
                        confidence = min(confidence * 1.15, 1.0)
                    elif (action == "buy" and es == -1):
                        confidence *= 0.7
            except Exception as e:
                print(f"   ⚠️ Ensemble: {e}")

        # --- OVERNIGHT EDGE BOOST ---
        if overnight_wl:
            owt = overnight_wl.get(ticker_yf, {})
            edge = owt.get("edge_score", 0)
            rec = owt.get("recommendation", "")
            if edge >= 25 and action == "buy":
                boost = 1.15 + (edge - 25) / 200  # +15% to +52% for edge 25-100
                boost = min(boost, 1.5)
                confidence *= boost
                ai_boosts.append(f"Night:{edge:+.0f}")
                print(f"   🌙 OVERNIGHT EDGE: {edge:+.1f} → {boost:.2f}x boost")
            elif edge >= 10 and action == "buy":
                confidence *= 1.05
                print(f"   🌙 Overnight watch: {edge:+.1f} → +5%")
            elif edge <= -15 and action == "buy":
                confidence *= 0.8
                print(f"   🌙 Overnight AVOID: {edge:+.1f} → -20%")

        confidence = min(confidence, 1.0)

        # === BRAIN INTELLIGENCE LAYER ===
        # The brain learns from every trade and adjusts confidence
        brain_intel = brain.get_combined_intelligence(
            ticker_yf, signal.get("factors", []),
            regime=regime_info.get("regime", "normal")
        )
        if brain_intel["ticker_trades"] > 0:
            old_conf = confidence
            confidence *= brain_intel["confidence_mult"]
            confidence = min(confidence, 1.0)
            brain_reasons = " | ".join(brain_intel["reasons"][:2])
            if brain_intel["confidence_mult"] != 1.0:
                print(f"   🧠 Brain: x{brain_intel['confidence_mult']:.2f} "
                      f"({brain_reasons}) "
                      f"WR:{brain_intel['ticker_winrate']:.0%} "
                      f"avg:${brain_intel['ticker_avg_pnl']:+.3f}")

        # === BRAIN-ADAPTIVE ENTRY THRESHOLD ===
        # Penalized tickers need HIGHER confidence to enter
        # Boosted tickers get a lower threshold
        ap = brain.brain.get('adaptive_params', {})
        ticker_penalty = ap.get('confidence_penalty_tickers', {}).get(ticker_yf, None)
        ticker_boost = ap.get('confidence_boost_tickers', {}).get(ticker_yf, None)
        if ticker_penalty and action == 'buy':
            # Require 20% more confidence for brain-penalized tickers
            confidence *= 0.85
            print(f"   🧠 Brain penalty gate: conf → {confidence:.2f}")
        elif ticker_boost and action == 'buy':
            # Slight extra boost for proven winners
            confidence = min(1.0, confidence * 1.05)
            print(f"   🧠 Brain boost gate: conf → {confidence:.2f}")

        # Dashboard ML status
        if ml_model and action in ("buy", "sell") and not ml_status["ml_signal"]:
            try:
                feats = {"rsi": signal.get("rsi", 50)}
                mp = predict_signal(feats, ml_model)
                ml_status["ml_signal"] = "BUY" if mp == 1 else ("SELL" if mp == -1 else "HOLD")
                ml_status["confidence"] = f"{confidence:.2f}"
            except Exception:
                pass

        try:
            with open("ml/ml_status.json", "w") as f:
                json.dump(ml_status, f, indent=2)
        except Exception:
            pass

        # ------------------------------------------------------------------
        #  EXECUTE TRADE
        # ------------------------------------------------------------------
        if action == "hold":
            print(f"   ⏸️ HOLD — {reason}")
            results[ticker_212] = {"action": "hold", "reason": reason}
            continue

        if action == "buy" and confidence >= confidence_threshold:
            stop_loss = signal.get("stop_loss", price * 0.98)
            atr_pct = atr / price if price else 0

            # Liquidity
            if "Volume" in df_15m.columns:
                avg_vol = float(df_15m["Volume"].tail(20).mean())
                if avg_vol < min_avg_volume:
                    print(f"   💧 SKIP — Low liq ({avg_vol:,.0f})")
                    continue

            if atr_pct > max_atr_pct:
                print(f"   🌪️ SKIP — ATR {atr_pct*100:.1f}% > {max_atr_pct*100:.1f}%")
                continue

            # Position sizing: Kelly + AI
            if free_cash < total_cash * 0.10:
                max_amt = free_cash * 0.95
                print(f"   💪 TIGHT CASH: ${max_amt:.2f} of ${free_cash:.2f}")
            else:
                max_amt = total_cash * kelly_f
                print(f"   📐 Kelly: ${max_amt:.2f}")

            conf_floor = max(confidence_threshold, 0.4)
            conf_norm = min(1.0, max(0.0, (confidence - conf_floor) / (1.0 - conf_floor)))
            sm = 0.6 + (conf_norm * 0.8)
            sm *= float(regime_info.get("multiplier", 1.0))
            sm *= float(vol_info.get("multiplier", 1.0))
            sm = max(0.5, min(1.5, sm))
            max_amt *= sm
            print(f"   🧠 AI size: x{sm:.2f} -> ${max_amt:.2f}")

            # Quantity
            if free_cash < 10:
                qty = min(max_amt / price, free_cash * 0.95 / price) if price > 0 else 0
                qty = round(qty, 1)
                if qty < 0.1 or qty * price < 0.10:
                    print(f"   💸 SKIP — too small (${free_cash:.2f})")
                    continue
                print(f"   🔸 FRACTIONAL: {qty:.1f} shares")
            else:
                qty = max(1, round(max_amt / price)) if price > 0 else 0
                qty = min(qty, 100)

            cost = qty * price
            if qty < min_qty:
                print(f"   💸 SKIP — qty {qty:.3f} < {min_qty}")
                continue
            if cost < min_order_value:
                print(f"   💸 SKIP — ${cost:.2f} < ${min_order_value}")
                continue
            if cost > free_cash:
                qty = int(free_cash / price) if price > 0 else 0
                cost = qty * price
                if cost > free_cash or qty < min_qty:
                    print(f"   💸 SKIP — can't afford")
                    continue

            rr = {"trend": 1.5, "range": 0.8, "volatile": 0.7}.get(regime_info.get("regime", ""), 1.0)
            profit_target = risk_mgr.calculate_profit_target(price, atr, risk_reward_ratio=rr)

            print(f"   🟢 BUY {qty} @ ${price:.2f} — Score:{mscore} Conf:{confidence:.0%}")
            print(f"      Stop: ${stop_loss:.2f} | Target: ${profit_target:.2f}")

            if not dry_run:
                try:
                    order_result = place_market_order(ticker_212, qty, confirm=True)
                    oid = order_result.get("id", "N/A")
                    if not oid or oid == "N/A":
                        raise RuntimeError(f"Missing order ID: {order_result}")
                    print(f"      ✅ Order: {oid}")
                    risk_mgr.add_position(ticker_yf, qty, price, atr, reason,
                                         stop_loss=stop_loss, profit_target=profit_target)
                    # Store brain-relevant data in position for learning on exit
                    try:
                        pos_all = risk_mgr.load_positions()
                        if ticker_yf in pos_all:
                            pos_all[ticker_yf]["score"] = mscore
                            pos_all[ticker_yf]["factors"] = signal.get("factors", [])[:6]
                            pos_all[ticker_yf]["rsi"] = signal.get("rsi", 50)
                            pos_all[ticker_yf]["regime"] = regime_info.get("regime", "normal")
                            risk_mgr.save_positions(pos_all)
                    except Exception:
                        pass
                    log_trade(ticker_212, "buy", qty, price, confidence=confidence, reason=reason, metadata={
                        "score": mscore, "ai_boosts": ai_boosts, "regime": regime_info,
                        "kelly_f": kelly_f, "factors": signal.get("factors", []),
                    })
                    results[ticker_212] = {"action": "buy", "qty": qty, "order_id": oid}
                    notify_trade(ticker_212, "buy", qty, price, reason)
                    free_cash -= cost
                    time.sleep(1)
                except Exception as e:
                    emsg = str(e)
                    print(f"      ❌ Failed: {emsg}")
                    results[ticker_212] = {"action": "error", "error": emsg}
                    if "rate limit" in emsg.lower() or "429" in emsg:
                        time.sleep(5)
            else:
                print(f"      🔵 DRY RUN")
                results[ticker_212] = {"action": "buy_dryrun", "qty": qty}

        elif action == "sell":
            positions = risk_mgr.get_open_positions()
            if ticker_yf in positions:
                qo = positions[ticker_yf].get("quantity", 0)
                print(f"   🔴 SELL {qo} @ ${price:.2f} — {reason}")
                if not dry_run and qo > 0:
                    try:
                        order_result = place_market_order(ticker_212, -qo, confirm=True)
                        risk_mgr.close_position(ticker_yf, price, reason)
                        log_trade(ticker_212, "sell", qo, price, reason=reason)
                        results[ticker_212] = {"action": "sell", "qty": qo}
                    except Exception as e:
                        print(f"      ❌ Sell failed: {e}")
                else:
                    results[ticker_212] = {"action": "sell_dryrun", "qty": qo}
            else:
                results[ticker_212] = {"action": "sell_signal", "reason": reason}

        time.sleep(0.5)

    return results


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SmartBot V3 — Precision Trading Engine")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--tickers", nargs="+")
    args = parser.parse_args()

    tickers = args.tickers or [t.strip() for t in os.getenv("TRADING212_DAILY_TICKERS", "AAPL_US_EQ,MSFT_US_EQ").split(",")]

    print("=" * 60)
    print(f"🤖 SMARTBOT V4 ARMED — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Tickers: {len(tickers)}")
    print("=" * 60)

    results = execute_live_trading(tickers, dry_run=args.dry_run)

    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    for t, r in results.items():
        a = r.get("action", "?")
        print(f"{t:15s} | {a.upper():12s} | {r.get('reason', '')[:40]}")
    print("=" * 60)
