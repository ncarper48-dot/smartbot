#!/usr/bin/env python3
"""
Performance tracking and learning system - tracks all trades and optimizes strategy
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
import statistics

PERFORMANCE_FILE = "/home/tradebot/performance_history.json"


def load_performance() -> Dict:
    """Load historical performance data."""
    if os.path.exists(PERFORMANCE_FILE):
        with open(PERFORMANCE_FILE, 'r') as f:
            data = json.load(f)
            # Backward compatibility: older formats stored a list of trades
            if isinstance(data, list):
                return {
                    "trades": data,
                    "daily_summary": {},
                    "ticker_stats": {},
                    "total_trades": len(data),
                    "total_pnl": 0,
                    "started": datetime.now().isoformat()
                }
            return data
    return {
        "trades": [],
        "daily_summary": {},
        "ticker_stats": {},
        "total_trades": 0,
        "total_pnl": 0,
        "started": datetime.now().isoformat()
    }


def save_performance(data: Dict):
    """Save performance data."""
    with open(PERFORMANCE_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def log_trade(ticker: str, action: str, quantity: int, price: float, 
              confidence: float = 0.5, reason: str = "", metadata: Dict = None):
    """Log a trade execution."""
    perf = load_performance()
    
    trade = {
        "timestamp": datetime.now().isoformat(),
        "ticker": ticker,
        "action": action,
        "quantity": quantity,
        "price": price,
        "cost": quantity * price,
        "confidence": confidence,
        "reason": reason
    }

    if metadata:
        trade["meta"] = metadata
    
    perf["trades"].append(trade)
    perf["total_trades"] += 1
    
    # Update ticker stats
    if ticker not in perf["ticker_stats"]:
        perf["ticker_stats"][ticker] = {
            "trades": 0,
            "buys": 0,
            "sells": 0,
            "total_cost": 0
        }
    
    perf["ticker_stats"][ticker]["trades"] += 1
    if action == "buy":
        perf["ticker_stats"][ticker]["buys"] += 1
        perf["ticker_stats"][ticker]["total_cost"] += quantity * price
    elif action == "sell":
        perf["ticker_stats"][ticker]["sells"] += 1
    
    save_performance(perf)
    return trade


def get_stats() -> Dict:
    """Get comprehensive performance statistics."""
    perf = load_performance()
    
    if not perf["trades"]:
        return {"message": "No trades yet"}
    
    # Calculate trading frequency
    first_trade = datetime.fromisoformat(perf["trades"][0]["timestamp"])
    last_trade = datetime.fromisoformat(perf["trades"][-1]["timestamp"])
    days_active = max(1, (last_trade - first_trade).days + 1)
    trades_per_day = perf["total_trades"] / days_active
    
    # Ticker performance
    ticker_stats = []
    for ticker, stats in perf["ticker_stats"].items():
        ticker_stats.append({
            "ticker": ticker,
            "trades": stats["trades"],
            "buys": stats["buys"],
            "sells": stats["sells"],
            "avg_cost": stats["total_cost"] / stats["buys"] if stats["buys"] > 0 else 0
        })
    
    ticker_stats.sort(key=lambda x: x["trades"], reverse=True)
    
    return {
        "total_trades": perf["total_trades"],
        "days_active": days_active,
        "trades_per_day": round(trades_per_day, 2),
        "started": perf.get("started"),
        "top_tickers": ticker_stats[:10],
        "last_24h_trades": len([t for t in perf["trades"] 
                                if datetime.fromisoformat(t["timestamp"]) > datetime.now() - timedelta(days=1)])
    }


def get_best_performers(min_trades: int = 5) -> List[str]:
    """Identify best performing tickers based on trade frequency and success."""
    perf = load_performance()
    
    # Tickers with at least min_trades
    active_tickers = [ticker for ticker, stats in perf["ticker_stats"].items() 
                      if stats["trades"] >= min_trades]
    
    # Sort by trade count (proxy for strategy finding opportunities)
    active_tickers.sort(key=lambda t: perf["ticker_stats"][t]["trades"], reverse=True)
    
    return active_tickers[:10]


def print_stats():
    """Print formatted performance statistics."""
    stats = get_stats()
    
    print("=" * 60)


def get_daily_summary(date_str: str = None) -> Dict:
    """Get daily summary of trades and P&L."""
    perf = load_performance()
    if not perf.get("trades"):
        return {"message": "No trades yet"}

    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')

    trades = [t for t in perf["trades"] if t["timestamp"].startswith(date_str)]
    if not trades:
        return {"message": f"No trades on {date_str}"}

    pnl = 0.0
    wins = 0
    losses = 0
    buys = 0
    sells = 0

    for t in trades:
        if t["action"] in ["sell", "sell_partial"]:
            # approximate pnl using metadata if available
            meta = t.get("meta", {})
            if "pnl" in meta:
                pnl += float(meta["pnl"])
            sells += 1
        elif t["action"] == "buy":
            buys += 1

    # If pnl not provided, fallback to 0
    if pnl > 0:
        wins += 1
    elif pnl < 0:
        losses += 1

    return {
        "date": date_str,
        "trades": len(trades),
        "buys": buys,
        "sells": sells,
        "pnl": pnl,
        "wins": wins,
        "losses": losses
    }
    print("📊 TRADING PERFORMANCE STATS")
    print("=" * 60)
    
    if "message" in stats:
        print(stats["message"])
        return
    
    print(f"Total Trades: {stats['total_trades']}")
    print(f"Days Active: {stats['days_active']}")
    print(f"Trades/Day: {stats['trades_per_day']}")
    print(f"Last 24h: {stats['last_24h_trades']} trades")
    print(f"Started: {stats['started'][:10]}")
    
    print("\n🏆 TOP TRADED TICKERS:")
    print("-" * 60)
    for t in stats['top_tickers']:
        print(f"{t['ticker']:12s} | Trades: {t['trades']:3d} | Buys: {t['buys']:3d} | Sells: {t['sells']:3d}")
    
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--stats", action="store_true", help="Show performance stats")
    parser.add_argument("--reset", action="store_true", help="Reset performance history")
    args = parser.parse_args()
    
    if args.reset:
        if os.path.exists(PERFORMANCE_FILE):
            os.remove(PERFORMANCE_FILE)
            print("✅ Performance history reset")
    elif args.stats:
        print_stats()
    else:
        print_stats()
