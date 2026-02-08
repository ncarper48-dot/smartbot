#!/usr/bin/env python3
"""
SmartBot Overnight Intelligence Engine
========================================
Runs after market close to gather edge for the next trading day.

Scans:
  1. News sentiment for every ticker (TextBlob on yfinance news)
  2. Global markets (Europe, Asia, futures) for overnight direction
  3. Daily chart technicals (support/resistance, trend, RSI extremes)
  4. After-hours / pre-market price moves
  5. Sector rotation signals (which sectors are leading/lagging)

Output: overnight_watchlist.json — ranked list of tickers with edge scores
        used by live_trader.py at next market open for priority trading.
"""

import json
import os
import sys
import time
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from textblob import TextBlob

sys.path.insert(0, "/home/tradebot")
from demo_pipeline import compute_indicators

WATCHLIST_FILE = "/home/tradebot/overnight_watchlist.json"
OVERNIGHT_LOG = "/home/tradebot/overnight_analysis.log"

# Global indices to check overnight direction
GLOBAL_INDICES = {
    # US futures
    "ES=F": "S&P 500 Futures",
    "NQ=F": "Nasdaq Futures",
    "YM=F": "Dow Futures",
    # European
    "^FTSE": "FTSE 100 (UK)",
    "^GDAXI": "DAX (Germany)",
    "^FCHI": "CAC 40 (France)",
    # Asian
    "^N225": "Nikkei 225 (Japan)",
    "^HSI": "Hang Seng (HK)",
    "000001.SS": "Shanghai Composite",
    # Volatility
    "^VIX": "VIX Fear Index",
    # Commodities
    "GC=F": "Gold",
    "CL=F": "Crude Oil",
    # Crypto (24/7 sentiment gauge)
    "BTC-USD": "Bitcoin",
}

# Sector ETFs for rotation analysis
SECTOR_ETFS = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLE": "Energy",
    "XLV": "Healthcare",
    "XLI": "Industrials",
    "XLC": "Communications",
    "XLY": "Consumer Disc.",
    "XLP": "Consumer Staples",
    "XLRE": "Real Estate",
}

# Map tickers to sectors
TICKER_SECTORS = {
    "AAPL": "XLK", "MSFT": "XLK", "GOOGL": "XLC", "NVDA": "XLK", "AMD": "XLK",
    "TSLA": "XLY", "RIVN": "XLY", "LCID": "XLY",
    "AMC": "XLC", "SNAP": "XLC",
    "SOFI": "XLF", "HOOD": "XLF", "COIN": "XLF",
    "NOK": "XLK", "PLTR": "XLK",
    "CCL": "XLY", "AAL": "XLI",
    "NIO": "XLY", "F": "XLY",
    "PLUG": "XLE", "PTON": "XLY",
    "SIRI": "XLC",
}


def _log(msg: str):
    """Append to overnight log."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(OVERNIGHT_LOG, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
#  1. NEWS SENTIMENT
# ---------------------------------------------------------------------------
def scan_ticker_news(symbol: str) -> dict:
    """Analyze recent news sentiment for a ticker via yfinance + TextBlob."""
    try:
        tk = yf.Ticker(symbol)
        news = tk.news or []

        if not news:
            return {"symbol": symbol, "news_count": 0, "sentiment": 0.0, "headlines": []}

        sentiments = []
        headlines = []
        for item in news[:10]:
            title = item.get("title", "")
            if not title:
                continue
            blob = TextBlob(title)
            pol = blob.sentiment.polarity
            sentiments.append(pol)
            headlines.append({"title": title, "polarity": round(pol, 3)})

        avg = float(np.mean(sentiments)) if sentiments else 0.0
        return {
            "symbol": symbol,
            "news_count": len(sentiments),
            "sentiment": round(avg, 4),
            "headlines": headlines[:3],
        }
    except Exception as e:
        return {"symbol": symbol, "news_count": 0, "sentiment": 0.0, "error": str(e)}


# ---------------------------------------------------------------------------
#  2. GLOBAL MARKET SCAN
# ---------------------------------------------------------------------------
def scan_global_markets() -> dict:
    """Check overnight direction of global indices, futures, commodities."""
    results = {}
    for sym, name in GLOBAL_INDICES.items():
        try:
            df = yf.download(sym, period="5d", interval="1d", progress=False)
            if df.empty or len(df) < 2:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            c = df["Close"]
            chg_1d = (float(c.iloc[-1]) - float(c.iloc[-2])) / float(c.iloc[-2])
            chg_5d = (float(c.iloc[-1]) - float(c.iloc[0])) / float(c.iloc[0])
            results[sym] = {
                "name": name,
                "price": round(float(c.iloc[-1]), 2),
                "chg_1d": round(chg_1d * 100, 2),
                "chg_5d": round(chg_5d * 100, 2),
            }
        except Exception:
            pass
    return results


# ---------------------------------------------------------------------------
#  3. DAILY CHART TECHNICALS
# ---------------------------------------------------------------------------
def scan_daily_technicals(symbol: str) -> dict:
    """Daily-timeframe technical scan: trend, RSI, support/resistance, ATR."""
    try:
        df = yf.download(symbol, period="60d", interval="1d", progress=False)
        if df.empty or len(df) < 30:
            return {}
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = compute_indicators(df, sma_short=10, sma_long=30)
        latest = df.iloc[-1]
        price = float(latest["Close"])
        rsi = float(latest["rsi"]) if not pd.isna(latest["rsi"]) else 50
        atr = float(latest["atr"]) if not pd.isna(latest["atr"]) else 0
        sma_short = float(latest["sma_short"]) if not pd.isna(latest["sma_short"]) else price
        sma_long = float(latest["sma_long"]) if not pd.isna(latest["sma_long"]) else price

        # Trend direction
        trend = "bullish" if sma_short > sma_long else "bearish"

        # Support/resistance from recent highs and lows
        recent = df.tail(20)
        support = float(recent["Low"].min())
        resistance = float(recent["High"].max())

        # Distance to support/resistance (% from price)
        dist_support = (price - support) / price * 100
        dist_resistance = (resistance - price) / price * 100

        # MACD
        macd_hist = float(latest["macd_hist"]) if not pd.isna(latest["macd_hist"]) else 0

        # Daily change
        if len(df) >= 2:
            prev_close = float(df.iloc[-2]["Close"])
            daily_chg = (price - prev_close) / prev_close * 100
        else:
            daily_chg = 0

        return {
            "price": round(price, 2),
            "rsi": round(rsi, 1),
            "trend": trend,
            "sma_gap_pct": round((sma_short - sma_long) / sma_long * 100, 2),
            "macd_hist": round(macd_hist, 4),
            "atr": round(atr, 4),
            "atr_pct": round(atr / price * 100, 2) if price else 0,
            "support": round(support, 2),
            "resistance": round(resistance, 2),
            "dist_support_pct": round(dist_support, 2),
            "dist_resistance_pct": round(dist_resistance, 2),
            "daily_chg_pct": round(daily_chg, 2),
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
#  4. SECTOR ROTATION
# ---------------------------------------------------------------------------
def scan_sector_rotation() -> dict:
    """Which sectors are leading/lagging over 1-day and 5-day periods."""
    results = {}
    for etf, name in SECTOR_ETFS.items():
        try:
            df = yf.download(etf, period="5d", interval="1d", progress=False)
            if df.empty or len(df) < 2:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            c = df["Close"]
            chg_1d = (float(c.iloc[-1]) - float(c.iloc[-2])) / float(c.iloc[-2]) * 100
            chg_5d = (float(c.iloc[-1]) - float(c.iloc[0])) / float(c.iloc[0]) * 100
            results[etf] = {"name": name, "chg_1d": round(chg_1d, 2), "chg_5d": round(chg_5d, 2)}
        except Exception:
            pass
    return results


# ---------------------------------------------------------------------------
#  5. EDGE SCORING — combine everything into a ranked watchlist
# ---------------------------------------------------------------------------
def compute_edge_score(
    news: dict, technicals: dict, sector_data: dict, global_data: dict,
    symbol: str
) -> float:
    """Combine all overnight signals into a single edge score (-100 to +100).
    
    Positive = bullish edge for next day.
    Negative = bearish / avoid.
    """
    score = 0.0

    # --- News sentiment (±25) ---
    sent = news.get("sentiment", 0)
    n_count = news.get("news_count", 0)
    if n_count >= 3:
        score += sent * 50  # Strong weight when many articles
    elif n_count >= 1:
        score += sent * 25

    # --- Daily technicals (±35) ---
    if technicals:
        rsi = technicals.get("rsi", 50)
        # Oversold bounce setup = bullish edge
        if rsi < 35:
            score += 15
        elif rsi < 45:
            score += 8
        elif rsi > 75:
            score -= 10  # Overbought = risky

        # Trend
        if technicals.get("trend") == "bullish":
            score += 10
        else:
            score -= 5

        # Near support = value buy
        if technicals.get("dist_support_pct", 99) < 3:
            score += 10

        # MACD positive
        if technicals.get("macd_hist", 0) > 0:
            score += 5

        # Daily momentum
        chg = technicals.get("daily_chg_pct", 0)
        if chg > 1.5:
            score += 5  # Strong day = momentum continues
        elif chg < -2:
            score += 3  # Big drop = mean reversion candidate

    # --- Sector rotation (±15) ---
    sector_etf = TICKER_SECTORS.get(symbol)
    if sector_etf and sector_etf in sector_data:
        sec = sector_data[sector_etf]
        if sec.get("chg_1d", 0) > 0.5:
            score += 10  # Leading sector
        elif sec.get("chg_1d", 0) < -0.5:
            score -= 8  # Lagging sector
        if sec.get("chg_5d", 0) > 1.5:
            score += 5  # 5-day sector momentum

    # --- Global markets direction (±15) ---
    futures_bullish = 0
    for sym in ("ES=F", "NQ=F"):
        gd = global_data.get(sym, {})
        if gd.get("chg_1d", 0) > 0.3:
            futures_bullish += 1
        elif gd.get("chg_1d", 0) < -0.3:
            futures_bullish -= 1
    score += futures_bullish * 5

    # VIX check
    vix = global_data.get("^VIX", {})
    vix_chg = vix.get("chg_1d", 0)
    if vix_chg < -3:
        score += 5  # VIX dropping = risk-on
    elif vix_chg > 5:
        score -= 10  # VIX spiking = danger

    # Clamp
    return max(-100, min(100, round(score, 1)))


# ---------------------------------------------------------------------------
#  MAIN — run full overnight analysis
# ---------------------------------------------------------------------------
def run_overnight_analysis(tickers: list = None) -> dict:
    """Run complete overnight analysis and save watchlist.
    
    Returns the full analysis report dict.
    """
    if tickers is None:
        tickers_str = os.getenv(
            "TRADING212_DAILY_TICKERS",
            "AAPL_US_EQ,MSFT_US_EQ,GOOGL_US_EQ,TSLA_US_EQ,NVDA_US_EQ"
        )
        tickers_212 = [t.strip() for t in tickers_str.split(",")]
        tickers = [t.replace("_US_EQ", "").replace("_UK_EQ", "").replace("_DE_EQ", "")
                    for t in tickers_212]

    _log("=" * 60)
    _log("🌙 SMARTBOT OVERNIGHT INTELLIGENCE ENGINE")
    _log("=" * 60)

    report = {
        "timestamp": datetime.now().isoformat(),
        "tickers_scanned": len(tickers),
        "global_markets": {},
        "sector_rotation": {},
        "ticker_analysis": {},
        "watchlist": [],
    }

    # 1. Global markets
    _log("🌍 Scanning global markets...")
    global_data = scan_global_markets()
    report["global_markets"] = global_data

    bullish_count = sum(1 for g in global_data.values() if g.get("chg_1d", 0) > 0)
    bearish_count = sum(1 for g in global_data.values() if g.get("chg_1d", 0) < 0)
    _log(f"   Global: {bullish_count} up / {bearish_count} down")

    for sym, gd in global_data.items():
        _log(f"   {gd['name']:25s} {gd['chg_1d']:+.2f}% (1d)  {gd['chg_5d']:+.2f}% (5d)")

    # 2. Sector rotation
    _log("\n📊 Scanning sector rotation...")
    sector_data = scan_sector_rotation()
    report["sector_rotation"] = sector_data

    sector_ranked = sorted(sector_data.items(), key=lambda x: x[1].get("chg_1d", 0), reverse=True)
    for etf, sd in sector_ranked:
        arrow = "🟢" if sd["chg_1d"] > 0 else "🔴"
        _log(f"   {arrow} {sd['name']:20s} {sd['chg_1d']:+.2f}% (1d)  {sd['chg_5d']:+.2f}% (5d)")

    # 3. Per-ticker analysis
    _log(f"\n📰 Analyzing {len(tickers)} tickers (news + technicals)...")
    scored_tickers = []

    for symbol in tickers:
        _log(f"   🔍 {symbol}...")
        
        # News
        news = scan_ticker_news(symbol)
        sent_emoji = "🟢" if news["sentiment"] > 0.05 else ("🔴" if news["sentiment"] < -0.05 else "⚪")
        _log(f"      {sent_emoji} News: {news['news_count']} articles, sentiment={news['sentiment']:+.3f}")
        for h in news.get("headlines", []):
            _log(f"         📰 [{h['polarity']:+.2f}] {h['title'][:70]}")

        # Technicals
        tech = scan_daily_technicals(symbol)
        if tech and "price" in tech:
            _log(f"      📊 RSI:{tech['rsi']} Trend:{tech['trend']} Support:${tech['support']} Resist:${tech['resistance']}")

        # Edge score
        edge = compute_edge_score(news, tech, sector_data, global_data, symbol)
        _log(f"      ⚡ Edge Score: {edge:+.1f}/100")

        report["ticker_analysis"][symbol] = {
            "news": news,
            "technicals": tech,
            "edge_score": edge,
        }
        scored_tickers.append((symbol, edge, news["sentiment"], tech))

        time.sleep(0.3)  # Rate limiting

    # 4. Build ranked watchlist
    scored_tickers.sort(key=lambda x: x[1], reverse=True)

    watchlist = []
    for rank, (symbol, edge, sent, tech) in enumerate(scored_tickers, 1):
        entry = {
            "rank": rank,
            "symbol": symbol,
            "ticker_212": symbol + "_US_EQ",
            "edge_score": edge,
            "sentiment": round(sent, 4),
            "trend": tech.get("trend", "unknown") if tech else "unknown",
            "rsi": tech.get("rsi", 50) if tech else 50,
            "support": tech.get("support", 0) if tech else 0,
            "resistance": tech.get("resistance", 0) if tech else 0,
            "recommendation": "PRIORITY BUY" if edge >= 25 else (
                "WATCH" if edge >= 10 else (
                    "NEUTRAL" if edge >= -10 else "AVOID"
                )
            ),
        }
        watchlist.append(entry)

    report["watchlist"] = watchlist

    # 5. Print summary
    _log("\n" + "=" * 60)
    _log("🏆 OVERNIGHT WATCHLIST — RANKED BY EDGE")
    _log("=" * 60)
    for w in watchlist:
        emoji = {"PRIORITY BUY": "🟢", "WATCH": "🟡", "NEUTRAL": "⚪", "AVOID": "🔴"}
        e = emoji.get(w["recommendation"], "⚪")
        _log(f"   #{w['rank']:2d} {e} {w['symbol']:6s} Edge:{w['edge_score']:+5.1f}  "
             f"Sent:{w['sentiment']:+.3f}  RSI:{w['rsi']:.0f}  {w['recommendation']}")

    # Global summary
    vix_data = global_data.get("^VIX", {})
    futures = global_data.get("ES=F", {})
    _log(f"\n🌐 Tomorrow's outlook:")
    _log(f"   S&P Futures: {futures.get('chg_1d', 0):+.2f}%")
    _log(f"   VIX: {vix_data.get('price', '?')} ({vix_data.get('chg_1d', 0):+.2f}%)")
    top_sector = sector_ranked[0] if sector_ranked else None
    if top_sector:
        _log(f"   Leading sector: {top_sector[1]['name']} ({top_sector[1]['chg_1d']:+.2f}%)")
    priority = [w for w in watchlist if w["recommendation"] == "PRIORITY BUY"]
    _log(f"   Priority buys: {len(priority)} tickers")
    _log("=" * 60)

    # 6. Save watchlist
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(report, f, indent=2)
    _log(f"💾 Saved to {WATCHLIST_FILE}")

    return report


if __name__ == "__main__":
    run_overnight_analysis()
