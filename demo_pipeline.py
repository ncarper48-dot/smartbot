"""Advanced demo pipeline with multiple indicators, risk management, and analytics.

Components:
- fetch_history(ticker, period): uses yfinance to get OHLCV
- compute_indicators(df): SMA, RSI, MACD, Bollinger Bands
- generate_signals(df): multi-indicator confirmation logic
- backtest_with_risk_management(df, signals): backtester with stop losses, position sizing
- run_demo_strategy(ticker,...): runs backtest and simulates demo orders
"""
from typing import Tuple, List, Dict
import pandas as pd
import numpy as np
import yfinance as yf
import logging
import time

logger = logging.getLogger(__name__)


def fetch_history(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """Fetch OHLCV history using yfinance."""
    data = yf.download(ticker, period=period, interval=interval, progress=False)
    if data.empty:
        raise RuntimeError(f"No data for {ticker}")
    
    # Handle MultiIndex columns from yfinance
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    data = data.dropna()
    return data


def compute_indicators(df: pd.DataFrame, sma_short: int = 10, sma_long: int = 30, rsi_period: int = 14, 
                       macd_fast: int = 12, macd_slow: int = 26, macd_signal: int = 9, bb_period: int = 20) -> pd.DataFrame:
    """Compute technical indicators: SMA, RSI, MACD, Bollinger Bands."""
    out = df.copy()
    close = out["Close"]
    high = out["High"]
    low = out["Low"]
    
    # SMA
    out["sma_short"] = close.rolling(sma_short).mean()
    out["sma_long"] = close.rolling(sma_long).mean()
    
    # RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    out["rsi"] = 100 - (100 / (1 + rs))
    
    # MACD
    ema_fast = close.ewm(span=macd_fast).mean()
    ema_slow = close.ewm(span=macd_slow).mean()
    out["macd"] = ema_fast - ema_slow
    out["macd_signal"] = out["macd"].ewm(span=macd_signal).mean()
    out["macd_hist"] = out["macd"] - out["macd_signal"]
    
    # Bollinger Bands
    sma_bb = close.rolling(bb_period).mean()
    std_bb = close.rolling(bb_period).std()
    out["bb_upper"] = sma_bb + (std_bb * 2)
    out["bb_lower"] = sma_bb - (std_bb * 2)
    out["bb_middle"] = sma_bb
    
    # ATR (volatility measure)
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    out["atr"] = tr.rolling(14).mean()
    
    # VWAP (Volume Weighted Average Price) - institutional intraday benchmark
    if "Volume" in out.columns:
        typical_price = (high + low + close) / 3
        cum_vol = out["Volume"].cumsum()
        cum_tp_vol = (typical_price * out["Volume"]).cumsum()
        out["vwap"] = cum_tp_vol / cum_vol.replace(0, np.nan)
    
    return out


def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Generate trading signals based on multiple indicators.
    
    BUY signal when:
    - SMA short > SMA long (trend confirmation)
    - RSI 30-70 (not overbought/oversold extremes)
    - MACD histogram positive
    - Price above Bollinger Band middle
    
    SELL signal when: trend reverses
    """
    out = df.copy()
    
    # SMA Trend
    out["sma_signal"] = (out["sma_short"] > out["sma_long"]).astype(int)
    
    # RSI condition: not in extreme
    out["rsi_ok"] = ((out["rsi"] > 30) & (out["rsi"] < 70)).astype(int)
    
    # MACD condition
    out["macd_ok"] = (out["macd_hist"] > 0).astype(int)
    
    # Bollinger Band position
    out["bb_ok"] = (out["Close"] > out["bb_middle"]).astype(int)
    
    # Combined signal: all conditions needed for entry
    out["signal"] = 0
    buy_cond = (out["sma_signal"] == 1) & (out["rsi_ok"] == 1) & (out["macd_ok"] == 1) & (out["bb_ok"] == 1)
    out.loc[buy_cond, "signal"] = 1
    
    # Sell if trend breaks
    out.loc[out["sma_signal"] == 0, "signal"] = -1
    
    out["signal_change"] = out["signal"].diff().fillna(0).astype(int)
    return out


def backtest_with_risk_management(df: pd.DataFrame, initial_cash: float = 10000.0, 
                                   risk_per_trade: float = 0.08, max_position_size: float = 0.25) -> Tuple[float, List[dict], Dict]:
    """Advanced backtester with stop losses, position sizing, and risk management.
    
    Returns: (final_pnl, trades, analytics_dict)
    """
    cash = initial_cash
    pos = 0.0
    entry_price = 0.0
    stop_loss = 0.0
    trades = []
    equity_curve = []
    max_equity = initial_cash
    max_drawdown = 0.0
    wins = 0
    losses = 0
    
    for idx, row in df.iterrows():
        signal_change = int(row["signal_change"].item() if hasattr(row["signal_change"], 'item') else row["signal_change"])
        current_price = float(row["Close"].item() if hasattr(row["Close"], 'item') else row["Close"])
        atr = float(row["atr"].item() if hasattr(row["atr"], 'item') else row["atr"]) if "atr" in row.index else current_price * 0.02
        
        # Update max equity and drawdown
        current_equity = cash + (pos * current_price if pos > 0 else 0)
        if current_equity > max_equity:
            max_equity = current_equity
        drawdown = (max_equity - current_equity) / max_equity if max_equity > 0 else 0
        if drawdown > max_drawdown:
            max_drawdown = drawdown
        equity_curve.append(current_equity)
        
        # Stop loss check
        if pos > 0 and current_price < stop_loss:
            cash += pos * current_price
            pnl_trade = (current_price - entry_price) * pos
            if pnl_trade < 0:
                losses += 1
            else:
                wins += 1
            trades.append({
                "ts": idx, 
                "action": "sell_stop", 
                "entry_price": entry_price,
                "exit_price": current_price,
                "qty": pos, 
                "pnl": pnl_trade
            })
            pos = 0
            stop_loss = 0
        
        # Entry signal
        if signal_change == 2:  # -1 -> 1: enter long
            if pos == 0 and cash > 0:
                # Position size based on risk
                risk_amount = cash * risk_per_trade
                stop_distance = max(atr * 2, current_price * 0.02)  # At least 2% or 2*ATR
                position_qty = min(risk_amount / stop_distance, (cash / current_price) * max_position_size)
                position_qty = max(1, position_qty)  # At least 1 share
                
                if cash >= position_qty * current_price:
                    cash -= position_qty * current_price
                    pos = position_qty
                    entry_price = current_price
                    stop_loss = current_price - stop_distance
                    trades.append({
                        "ts": idx,
                        "action": "buy",
                        "entry_price": current_price,
                        "stop_loss": stop_loss,
                        "qty": position_qty
                    })
        
        # Exit signal
        elif signal_change == -2:  # 1 -> -1: exit long
            if pos > 0:
                cash += pos * current_price
                pnl_trade = (current_price - entry_price) * pos
                if pnl_trade < 0:
                    losses += 1
                else:
                    wins += 1
                trades.append({
                    "ts": idx,
                    "action": "sell",
                    "entry_price": entry_price,
                    "exit_price": current_price,
                    "qty": pos,
                    "pnl": pnl_trade
                })
                pos = 0
                stop_loss = 0
    
    # Liquidate at last close
    if pos > 0:
        last_price = float(df.iloc[-1]["Close"].item() if hasattr(df.iloc[-1]["Close"], 'item') else df.iloc[-1]["Close"])
        cash += pos * last_price
        pnl_trade = (last_price - entry_price) * pos
        if pnl_trade < 0:
            losses += 1
        else:
            wins += 1
        trades.append({
            "ts": df.index[-1],
            "action": "sell_final",
            "entry_price": entry_price,
            "exit_price": last_price,
            "qty": pos,
            "pnl": pnl_trade
        })
        pos = 0
    
    pnl = cash - initial_cash
    
    # Calculate analytics
    total_trades = len([t for t in trades if "action" in t and "entry_price" in t])
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    
    # Sharpe ratio (simple)
    returns = pd.Series(equity_curve).pct_change().dropna()
    sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
    
    analytics = {
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "max_drawdown": max_drawdown * 100,
        "sharpe_ratio": sharpe,
        "final_equity": cash,
        "return_pct": (pnl / initial_cash) * 100
    }
    
    return pnl, trades, analytics


def run_demo_strategy(ticker: str, short: int = 10, long: int = 30, period: str = "1mo") -> dict:
    """Run the advanced multi-indicator strategy with risk management.

    Returns a report dict with pnl, trades, analytics and order results.
    """
    from bot import place_market_order

    # Map Trading212 ticker format to Yahoo Finance format
    # Remove Trading212 suffixes for data fetching
    yf_ticker = ticker.replace("_US_EQ", "").replace("_UK_EQ", "").replace("_DE_EQ", "")
    
    # Use hourly data for intraday trading
    df = fetch_history(yf_ticker, period=period, interval="1h")
    df = compute_indicators(df, sma_short=short, sma_long=long)
    df = generate_signals(df)
    pnl, trades, analytics = backtest_with_risk_management(df)

    # Place orders for trades (respects TRADING212_MODE env var)
    # Use original ticker format for Trading212 API
    demo_results = []
    for t in trades:
        action = t.get("action", "unknown")
        if action in ["buy", "sell", "sell_stop", "sell_final"]:
            qty = t.get("qty", 1)
            # Round quantity to whole shares (Trading212 requirement)
            qty_rounded = round(float(qty))
            if qty_rounded < 1:
                qty_rounded = 1  # Minimum 1 share
            # Don't pass mode - let it read from env (TRADING212_MODE)
            # confirm=True for live mode (TRADING212_AUTO_CONFIRM already set in .env)
            res = place_market_order(ticker, qty_rounded, confirm=True)
            demo_results.append({"trade": t, "demo_res": res})
            time.sleep(0.05)

    return {
        "ticker": ticker,
        "pnl": pnl,
        "trades": trades,
        "analytics": analytics,
        "demo_results": demo_results
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("ticker", help="Ticker symbol (e.g., AAPL)")
    parser.add_argument("--short", type=int, default=10)
    parser.add_argument("--long", type=int, default=30)
    parser.add_argument("--period", default="6mo")
    args = parser.parse_args()

    report = run_demo_strategy(args.ticker, args.short, args.long, period=args.period)
    print(report)