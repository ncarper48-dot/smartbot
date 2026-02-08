"""
Market Regime Classifier
Classifies a ticker's regime using trend strength and volatility.
"""
import numpy as np
import pandas as pd


def classify_regime(df, short_window=20, long_window=50, vol_window=50):
    """
    Returns dict: {regime, trend_strength, vol, multiplier}
    Regimes: 'trend', 'range', 'volatile', 'normal'
    """
    if df is None or df.empty or len(df) < max(long_window, vol_window) + 5:
        return {"regime": "normal", "trend_strength": 0.0, "vol": 0.0, "multiplier": 1.0}

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    close = df["Close"].astype(float)
    returns = close.pct_change().dropna()

    sma_short = close.rolling(short_window).mean().iloc[-1]
    sma_long = close.rolling(long_window).mean().iloc[-1]
    trend_strength = abs(sma_short - sma_long) / close.iloc[-1]

    rolling_vol = returns.rolling(vol_window).std().iloc[-1] if len(returns) >= vol_window else returns.std()
    vol_series = returns.rolling(vol_window).std().dropna()

    if vol_series.empty:
        vol_low, vol_high = rolling_vol, rolling_vol
    else:
        vol_low = vol_series.quantile(0.25)
        vol_high = vol_series.quantile(0.75)

    if rolling_vol >= vol_high * 1.25:
        return {"regime": "volatile", "trend_strength": float(trend_strength), "vol": float(rolling_vol), "multiplier": 0.85}

    if trend_strength >= 0.02:
        return {"regime": "trend", "trend_strength": float(trend_strength), "vol": float(rolling_vol), "multiplier": 1.10}

    if rolling_vol <= vol_low * 0.9:
        return {"regime": "range", "trend_strength": float(trend_strength), "vol": float(rolling_vol), "multiplier": 0.95}

    return {"regime": "normal", "trend_strength": float(trend_strength), "vol": float(rolling_vol), "multiplier": 1.0}
