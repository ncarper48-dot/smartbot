#!/usr/bin/env python3
"""
SmartBot Brain — Self-Learning Trading Intelligence
=====================================================
The brain learns from EVERY trade and gets smarter over time.

What it learns:
  1. TICKER MEMORY — Which tickers make money, which lose money
  2. FACTOR MEMORY — Which technical factors (RSI, MACD, BB, etc.) predict wins
  3. CONDITION MEMORY — What market conditions (regime, volatility, time) lead to profits
  4. STRATEGY TUNING — Auto-adjusts entry/exit thresholds based on actual results
  5. PATTERN MEMORY — Remembers winning/losing score ranges, RSI zones, etc.

The brain persists to disk (smartbot_brain.json) and loads on every cycle.
It never forgets — every trade makes it smarter.
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

BRAIN_FILE = "/home/tradebot/smartbot_brain.json"


def _default_brain() -> dict:
    """Create a fresh brain structure."""
    return {
        "version": 2,
        "created": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "total_trades_learned": 0,

        # --- TICKER MEMORY ---
        # Tracks win rate, avg P&L, best/worst trades per ticker
        "ticker_memory": {},

        # --- FACTOR MEMORY ---
        # Which technical factors (SMA+, GoldenX, RSI:45*, MACD+, etc.) 
        # appeared in winning vs losing trades
        "factor_memory": {},

        # --- CONDITION MEMORY ---
        # What market regimes/volatility/time-of-day lead to profits
        "condition_memory": {
            "regime_wins": {"trend": 0, "range": 0, "volatile": 0, "normal": 0},
            "regime_losses": {"trend": 0, "range": 0, "volatile": 0, "normal": 0},
            "hour_wins": {},    # hour -> count
            "hour_losses": {},  # hour -> count
            "day_wins": {},     # day_of_week -> count
            "day_losses": {},   # day_of_week -> count
        },

        # --- SCORE MEMORY ---
        # What momentum scores led to wins vs losses
        "score_memory": {
            "winning_scores": [],   # scores of trades that made money
            "losing_scores": [],    # scores of trades that lost money
        },

        # --- ADAPTIVE PARAMETERS ---
        # Self-tuning thresholds that evolve with experience
        "adaptive_params": {
            "optimal_score_min": 50,        # Best entry score (adjusts over time)
            "optimal_rsi_buy_low": 30,      # Best RSI range for buys
            "optimal_rsi_buy_high": 60,     
            "confidence_boost_tickers": {},  # ticker -> boost multiplier
            "confidence_penalty_tickers": {},# ticker -> penalty multiplier
            "best_factors": [],              # top 5 winning factors
            "worst_factors": [],             # top 5 losing factors
            "preferred_regime": "trend",     # regime with best win rate
            "learning_rate": 0.1,            # how fast to adjust (increases with data)
        },

        # --- TRADE LOG (for deep analysis) ---
        "trade_log": [],  # Last 200 trades with full context
    }


class SmartBotBrain:
    """Self-learning brain that gets smarter with every trade."""

    def __init__(self):
        self.brain = self._load()
        self._dirty = False

    def _load(self) -> dict:
        """Load brain from disk or create new one."""
        if os.path.exists(BRAIN_FILE):
            try:
                with open(BRAIN_FILE, "r") as f:
                    brain = json.load(f)
                # Migrate old versions
                if brain.get("version", 1) < 2:
                    fresh = _default_brain()
                    fresh.update(brain)
                    brain = fresh
                    brain["version"] = 2
                return brain
            except Exception as e:
                print(f"⚠️ Brain load error: {e} — starting fresh")
        return _default_brain()

    def save(self):
        """Persist brain to disk."""
        self.brain["last_updated"] = datetime.now().isoformat()
        try:
            with open(BRAIN_FILE, "w") as f:
                json.dump(self.brain, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️ Brain save error: {e}")

    # ===================================================================
    #  LEARNING — Called after every trade closes
    # ===================================================================
    def learn_from_trade(self, trade: dict):
        """Learn from a completed trade. Call this after every buy+sell pair.
        
        trade dict should contain:
            ticker, action (buy/sell), quantity, price, pnl, pnl_pct,
            entry_score, entry_factors, entry_rsi, entry_confidence,
            regime, volatility, hold_hours, reason
        """
        ticker = trade.get("ticker", "UNKNOWN").replace("_US_EQ", "")
        pnl = float(trade.get("pnl", 0))
        pnl_pct = float(trade.get("pnl_pct", 0))
        is_win = pnl > 0
        entry_score = trade.get("entry_score", 50)
        entry_factors = trade.get("entry_factors", [])
        entry_rsi = trade.get("entry_rsi", 50)
        regime = trade.get("regime", "normal")
        hold_hours = trade.get("hold_hours", 0)
        
        # Timestamp info
        ts = trade.get("timestamp", datetime.now().isoformat())
        try:
            dt = datetime.fromisoformat(ts) if isinstance(ts, str) else datetime.now()
        except:
            dt = datetime.now()
        hour = dt.hour
        day_name = dt.strftime("%A")

        # --- 1. UPDATE TICKER MEMORY ---
        tm = self.brain["ticker_memory"]
        if ticker not in tm:
            tm[ticker] = {
                "wins": 0, "losses": 0, "total_pnl": 0,
                "avg_pnl": 0, "best_trade": 0, "worst_trade": 0,
                "total_trades": 0, "win_streak": 0, "lose_streak": 0,
                "last_trade": "", "avg_hold_hours": 0,
            }
        t = tm[ticker]
        t["total_trades"] += 1
        t["total_pnl"] += pnl
        t["avg_pnl"] = t["total_pnl"] / t["total_trades"]
        t["last_trade"] = ts
        t["avg_hold_hours"] = (t["avg_hold_hours"] * (t["total_trades"] - 1) + hold_hours) / t["total_trades"]
        if is_win:
            t["wins"] += 1
            t["win_streak"] += 1
            t["lose_streak"] = 0
            t["best_trade"] = max(t["best_trade"], pnl)
        else:
            t["losses"] += 1
            t["lose_streak"] += 1
            t["win_streak"] = 0
            t["worst_trade"] = min(t["worst_trade"], pnl)

        # --- 2. UPDATE FACTOR MEMORY ---
        fm = self.brain["factor_memory"]
        for factor in entry_factors:
            # Normalize factor names (remove numbers): "RSI:45*" -> "RSI:zone*"
            factor_key = self._normalize_factor(factor)
            if factor_key not in fm:
                fm[factor_key] = {"wins": 0, "losses": 0, "total_pnl": 0, "avg_pnl": 0}
            fm[factor_key]["wins" if is_win else "losses"] += 1
            fm[factor_key]["total_pnl"] += pnl
            total = fm[factor_key]["wins"] + fm[factor_key]["losses"]
            fm[factor_key]["avg_pnl"] = fm[factor_key]["total_pnl"] / total if total else 0

        # --- 3. UPDATE CONDITION MEMORY ---
        cm = self.brain["condition_memory"]
        bucket = "regime_wins" if is_win else "regime_losses"
        if regime in cm[bucket]:
            cm[bucket][regime] += 1
        
        hour_key = str(hour)
        hour_bucket = "hour_wins" if is_win else "hour_losses"
        cm[hour_bucket][hour_key] = cm[hour_bucket].get(hour_key, 0) + 1

        day_bucket = "day_wins" if is_win else "day_losses"
        cm[day_bucket][day_name] = cm[day_bucket].get(day_name, 0) + 1

        # --- 4. UPDATE SCORE MEMORY ---
        sm = self.brain["score_memory"]
        if is_win:
            sm["winning_scores"].append(entry_score)
        else:
            sm["losing_scores"].append(entry_score)
        # Keep last 100 each
        sm["winning_scores"] = sm["winning_scores"][-100:]
        sm["losing_scores"] = sm["losing_scores"][-100:]

        # --- 5. ADD TO TRADE LOG ---
        log_entry = {
            "timestamp": ts,
            "ticker": ticker,
            "pnl": round(pnl, 4),
            "pnl_pct": round(pnl_pct, 2),
            "win": is_win,
            "score": entry_score,
            "factors": entry_factors[:6],
            "rsi": round(entry_rsi, 1),
            "regime": regime,
            "hold_hours": round(hold_hours, 1),
            "reason": trade.get("reason", "")[:60],
        }
        self.brain["trade_log"].append(log_entry)
        self.brain["trade_log"] = self.brain["trade_log"][-200:]  # Keep last 200

        self.brain["total_trades_learned"] += 1
        
        # --- 6. RECALCULATE ADAPTIVE PARAMETERS ---
        self._recalculate_params()

        self.save()
        
        outcome = "WIN" if is_win else "LOSS"
        print(f"🧠 Brain learned: {ticker} {outcome} ${pnl:+.2f} "
              f"(Score:{entry_score}, {len(entry_factors)} factors, {regime})")

    def _normalize_factor(self, factor: str) -> str:
        """Normalize factor names for consistent tracking.
        RSI:45* -> RSI:buy_zone, RSI:80X -> RSI:overbought, etc.
        """
        if factor.startswith("RSI:"):
            val_str = factor[4:].rstrip("*!X")
            try:
                val = float(val_str)
                if val < 30:
                    return "RSI:oversold"
                elif val <= 50:
                    return "RSI:buy_zone"
                elif val <= 65:
                    return "RSI:neutral"
                else:
                    return "RSI:overbought"
            except:
                return factor
        if factor.startswith("+") or factor.startswith("-"):
            try:
                pct = float(factor.rstrip("%!"))
                if pct > 0.5:
                    return "momentum:strong_up"
                elif pct > 0:
                    return "momentum:up"
                elif pct < -0.5:
                    return "momentum:strong_down"
                else:
                    return "momentum:down"
            except:
                return factor
        return factor

    def _recalculate_params(self):
        """Recalculate adaptive parameters from accumulated data."""
        ap = self.brain["adaptive_params"]
        total = self.brain["total_trades_learned"]

        # Learning rate increases with data (more data = more confident)
        ap["learning_rate"] = min(0.5, 0.05 + total * 0.005)

        # --- OPTIMAL SCORE ---
        sm = self.brain["score_memory"]
        if len(sm["winning_scores"]) >= 3:
            avg_win_score = np.mean(sm["winning_scores"])
            avg_lose_score = np.mean(sm["losing_scores"]) if sm["losing_scores"] else 50
            # Optimal minimum = midpoint between avg losing and avg winning score
            optimal = (avg_win_score + avg_lose_score) / 2
            ap["optimal_score_min"] = max(40, min(70, round(optimal)))

        # --- BEST/WORST FACTORS ---
        fm = self.brain["factor_memory"]
        if fm:
            # Sort by win rate (minimum 3 trades to count)
            qualified = {k: v for k, v in fm.items() 
                        if (v["wins"] + v["losses"]) >= 2}
            if qualified:
                by_winrate = sorted(qualified.items(), 
                                   key=lambda x: x[1]["wins"] / (x[1]["wins"] + x[1]["losses"]),
                                   reverse=True)
                ap["best_factors"] = [f[0] for f in by_winrate[:5]]
                ap["worst_factors"] = [f[0] for f in by_winrate[-5:]]

        # --- TICKER CONFIDENCE BOOSTS ---
        tm = self.brain["ticker_memory"]
        ap["confidence_boost_tickers"] = {}
        ap["confidence_penalty_tickers"] = {}
        for ticker, stats in tm.items():
            if stats["total_trades"] < 2:
                continue
            win_rate = stats["wins"] / stats["total_trades"]
            if win_rate >= 0.6 and stats["avg_pnl"] > 0:
                # Good ticker — boost confidence
                boost = 1.0 + min(0.3, (win_rate - 0.5) * ap["learning_rate"])
                ap["confidence_boost_tickers"][ticker] = round(boost, 3)
            elif win_rate <= 0.35 and stats["avg_pnl"] < 0:
                # Bad ticker — penalize confidence
                penalty = 1.0 - min(0.3, (0.5 - win_rate) * ap["learning_rate"])
                ap["confidence_penalty_tickers"][ticker] = round(penalty, 3)

        # --- PREFERRED REGIME ---
        cm = self.brain["condition_memory"]
        best_regime = "normal"
        best_wr = 0
        for regime in ["trend", "range", "volatile", "normal"]:
            wins = cm["regime_wins"].get(regime, 0)
            losses = cm["regime_losses"].get(regime, 0)
            total = wins + losses
            if total >= 2:
                wr = wins / total
                if wr > best_wr:
                    best_wr = wr
                    best_regime = regime
        ap["preferred_regime"] = best_regime

    # ===================================================================
    #  INTELLIGENCE — Query the brain for trading decisions
    # ===================================================================
    def get_ticker_score(self, ticker: str) -> dict:
        """Get brain's assessment of a ticker based on learning.
        
        Returns:
            confidence_mult: multiply trade confidence by this (>1 = boost, <1 = penalize)
            reason: why
            win_rate: historical win rate
            avg_pnl: average P&L per trade
        """
        ticker = ticker.replace("_US_EQ", "")
        tm = self.brain["ticker_memory"].get(ticker, None)
        
        if not tm or tm["total_trades"] < 2:
            return {"confidence_mult": 1.0, "reason": "new_ticker", 
                    "win_rate": 0.5, "avg_pnl": 0, "trades": 0}

        win_rate = tm["wins"] / tm["total_trades"] if tm["total_trades"] > 0 else 0.5
        
        # Confidence multiplier based on track record
        ap = self.brain["adaptive_params"]
        mult = ap["confidence_boost_tickers"].get(ticker, 
               ap["confidence_penalty_tickers"].get(ticker, 1.0))
        
        # Streak bonus/penalty
        if tm["win_streak"] >= 3:
            mult *= 1.1  # Hot ticker
            reason = f"🔥 hot_streak({tm['win_streak']})"
        elif tm["lose_streak"] >= 3:
            mult *= 0.8  # Cold ticker
            reason = f"🥶 cold_streak({tm['lose_streak']})"
        elif win_rate >= 0.6:
            reason = f"✅ winner({win_rate:.0%})"
        elif win_rate <= 0.35:
            reason = f"⛔ loser({win_rate:.0%})"
        else:
            reason = f"📊 neutral({win_rate:.0%})"

        return {
            "confidence_mult": round(mult, 3),
            "reason": reason,
            "win_rate": round(win_rate, 3),
            "avg_pnl": round(tm["avg_pnl"], 4),
            "trades": tm["total_trades"],
            "best": round(tm["best_trade"], 2),
            "worst": round(tm["worst_trade"], 2),
        }

    def get_factor_score(self, factors: list) -> dict:
        """Score a set of factors based on historical performance.
        
        Returns boost/penalty multiplier and which factors are strong/weak.
        """
        fm = self.brain["factor_memory"]
        ap = self.brain["adaptive_params"]
        
        good_factors = []
        bad_factors = []
        net_mult = 1.0
        
        for factor in factors:
            factor_key = self._normalize_factor(factor)
            if factor_key in fm:
                stats = fm[factor_key]
                total = stats["wins"] + stats["losses"]
                if total >= 2:
                    wr = stats["wins"] / total
                    if wr >= 0.6:
                        good_factors.append(factor_key)
                        net_mult *= 1.0 + (wr - 0.5) * 0.2  # Up to +10%
                    elif wr <= 0.35:
                        bad_factors.append(factor_key)
                        net_mult *= 1.0 - (0.5 - wr) * 0.2  # Down to -10%

        net_mult = max(0.7, min(1.3, net_mult))

        return {
            "factor_mult": round(net_mult, 3),
            "good_factors": good_factors,
            "bad_factors": bad_factors,
        }

    def get_regime_score(self, regime: str) -> float:
        """Get confidence multiplier for current market regime."""
        cm = self.brain["condition_memory"]
        wins = cm["regime_wins"].get(regime, 0)
        losses = cm["regime_losses"].get(regime, 0)
        total = wins + losses
        if total < 3:
            return 1.0
        
        wr = wins / total
        if wr >= 0.6:
            return min(1.2, 1.0 + (wr - 0.5) * 0.4)
        elif wr <= 0.35:
            return max(0.7, 1.0 - (0.5 - wr) * 0.4)
        return 1.0

    def get_time_score(self) -> float:
        """Get confidence multiplier based on current hour's track record."""
        import pytz
        et = pytz.timezone('America/New_York')
        hour = str(datetime.now(et).hour)
        
        cm = self.brain["condition_memory"]
        wins = cm["hour_wins"].get(hour, 0)
        losses = cm["hour_losses"].get(hour, 0)
        total = wins + losses
        if total < 3:
            return 1.0
        
        wr = wins / total
        if wr >= 0.6:
            return 1.1
        elif wr <= 0.35:
            return 0.85
        return 1.0

    def get_combined_intelligence(self, ticker: str, factors: list, 
                                  regime: str = "normal") -> dict:
        """Get the brain's full assessment for a potential trade.
        
        Combines ticker memory, factor analysis, regime, and time of day
        into a single confidence multiplier + reasoning.
        """
        ticker_intel = self.get_ticker_score(ticker)
        factor_intel = self.get_factor_score(factors)
        regime_mult = self.get_regime_score(regime)
        time_mult = self.get_time_score()

        # Combined multiplier
        combined = (ticker_intel["confidence_mult"] * 
                   factor_intel["factor_mult"] * 
                   regime_mult * 
                   time_mult)
        
        # Clamp to reasonable range
        combined = max(0.5, min(1.5, combined))

        reasons = [ticker_intel["reason"]]
        if factor_intel["good_factors"]:
            reasons.append(f"✅factors:{','.join(factor_intel['good_factors'][:3])}")
        if factor_intel["bad_factors"]:
            reasons.append(f"⚠️factors:{','.join(factor_intel['bad_factors'][:3])}")
        if regime_mult != 1.0:
            reasons.append(f"regime:{regime}({regime_mult:.2f})")
        if time_mult != 1.0:
            reasons.append(f"time({time_mult:.2f})")

        return {
            "confidence_mult": round(combined, 3),
            "reasons": reasons,
            "ticker_trades": ticker_intel["trades"],
            "ticker_winrate": ticker_intel["win_rate"],
            "ticker_avg_pnl": ticker_intel["avg_pnl"],
        }

    # ===================================================================
    #  INSIGHTS — Brain's self-analysis
    # ===================================================================
    def get_insights(self) -> str:
        """Generate a human-readable intelligence report."""
        b = self.brain
        total = b["total_trades_learned"]
        
        lines = [
            f"🧠 SMARTBOT BRAIN — {total} trades learned",
            f"   Last updated: {b['last_updated'][:16]}",
            "",
        ]

        # Ticker rankings
        tm = b["ticker_memory"]
        if tm:
            ranked = sorted(tm.items(), 
                          key=lambda x: x[1]["avg_pnl"], reverse=True)
            lines.append("📊 TICKER RANKINGS (by avg P&L):")
            for ticker, stats in ranked:
                wr = stats["wins"] / stats["total_trades"] if stats["total_trades"] else 0
                icon = "🟢" if stats["avg_pnl"] > 0 else "🔴"
                lines.append(f"   {icon} {ticker:6s} WR:{wr:.0%} "
                           f"Avg:${stats['avg_pnl']:+.3f} "
                           f"Best:${stats['best_trade']:+.2f} "
                           f"({stats['total_trades']} trades)")

        # Best/worst factors
        ap = b["adaptive_params"]
        if ap["best_factors"]:
            lines.append(f"\n✅ BEST FACTORS: {', '.join(ap['best_factors'])}")
        if ap["worst_factors"]:
            lines.append(f"⛔ WORST FACTORS: {', '.join(ap['worst_factors'])}")

        # Optimal settings
        lines.append(f"\n⚙️ ADAPTIVE SETTINGS:")
        lines.append(f"   Optimal entry score: ≥{ap['optimal_score_min']}")
        lines.append(f"   Preferred regime: {ap['preferred_regime']}")
        lines.append(f"   Learning rate: {ap['learning_rate']:.3f}")
        lines.append(f"   Brain confidence: {'LOW' if total < 10 else 'MEDIUM' if total < 30 else 'HIGH'}")

        # Boosted/penalized tickers
        if ap["confidence_boost_tickers"]:
            lines.append(f"\n🚀 BOOSTED: {ap['confidence_boost_tickers']}")
        if ap["confidence_penalty_tickers"]:
            lines.append(f"⚠️ PENALIZED: {ap['confidence_penalty_tickers']}")

        return "\n".join(lines)

    def seed_from_history(self, history_file: str = "/home/tradebot/performance_history.json"):
        """Seed the brain from existing trade history."""
        try:
            with open(history_file) as f:
                data = json.load(f)
            trades = data.get("trades", [])
            
            # Pair up buys and sells per ticker to calculate P&L
            open_trades = {}  # ticker -> list of buy entries
            learned = 0
            
            for trade in trades:
                ticker = trade["ticker"]
                action = trade.get("action", "")
                price = trade.get("price", 0)
                qty = trade.get("quantity", 0)
                
                if action == "buy":
                    if ticker not in open_trades:
                        open_trades[ticker] = []
                    open_trades[ticker].append(trade)
                
                elif action == "sell" and ticker in open_trades and open_trades[ticker]:
                    # Match with earliest buy
                    buy_trade = open_trades[ticker].pop(0)
                    buy_price = buy_trade.get("price", price)
                    pnl = (price - buy_price) * qty
                    pnl_pct = ((price - buy_price) / buy_price * 100) if buy_price > 0 else 0
                    
                    # Calculate hold hours
                    hold_hours = 6  # default
                    try:
                        buy_dt = datetime.fromisoformat(buy_trade["timestamp"])
                        sell_dt = datetime.fromisoformat(trade["timestamp"])
                        hold_hours = (sell_dt - buy_dt).total_seconds() / 3600
                    except:
                        pass
                    
                    # Extract context from buy trade
                    meta = buy_trade.get("meta", {})
                    factors = meta.get("factors", [])
                    regime = meta.get("regime", {}).get("regime", "normal") if isinstance(meta.get("regime"), dict) else "normal"
                    
                    learning_trade = {
                        "ticker": ticker,
                        "pnl": pnl,
                        "pnl_pct": pnl_pct,
                        "entry_score": meta.get("score", 50),
                        "entry_factors": factors,
                        "entry_rsi": meta.get("rsi", 50),
                        "entry_confidence": buy_trade.get("confidence", 0.5),
                        "regime": regime,
                        "hold_hours": hold_hours,
                        "timestamp": trade["timestamp"],
                        "reason": trade.get("reason", ""),
                    }
                    
                    self.learn_from_trade(learning_trade)
                    learned += 1
            
            print(f"🧠 Brain seeded with {learned} completed trades from history")
            return learned
            
        except Exception as e:
            print(f"⚠️ Brain seed error: {e}")
            return 0


# ===================================================================
#  STANDALONE — Run brain analysis
# ===================================================================
if __name__ == "__main__":
    brain = SmartBotBrain()
    
    # Seed from history if brain is empty
    if brain.brain["total_trades_learned"] == 0:
        print("🧠 Brain is empty — seeding from trade history...")
        brain.seed_from_history()
    
    print("\n" + brain.get_insights())
    
    # Show intelligence for current tickers
    print("\n\n📡 TICKER INTELLIGENCE:")
    tickers = ["RIVN", "SNAP", "AMC", "NOK", "TSLA", "NVDA", "SOFI", "COIN"]
    for t in tickers:
        intel = brain.get_ticker_score(t)
        if intel["trades"] > 0:
            print(f"   {t:6s} → x{intel['confidence_mult']:.2f} {intel['reason']} "
                  f"(WR:{intel['win_rate']:.0%}, {intel['trades']}T, avg:${intel['avg_pnl']:+.3f})")
