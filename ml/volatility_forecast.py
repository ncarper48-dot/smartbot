"""
Volatility Regime Detection
Lightweight volatility forecasting using rolling returns.
"""
import numpy as np
import pandas as pd

def get_volatility_regime(df, window=60):
    """
    Analyze recent volatility and return a regime with a confidence multiplier.

    Returns dict:
    - regime: low/normal/high
    - vol: rolling std of returns
    - multiplier: confidence multiplier based on regime
    """
    if df is None or df.empty or len(df) < window + 1:
        return {"regime": "unknown", "vol": None, "multiplier": 1.0}

    # Flatten MultiIndex if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    close = df["Close"].astype(float)
    returns = close.pct_change().dropna()
    if len(returns) < window:
        return {"regime": "unknown", "vol": None, "multiplier": 1.0}

    rolling_vol = returns.rolling(window=window).std().iloc[-1]
    historical = returns.rolling(window=window).std().dropna()

    if historical.empty:
        return {"regime": "unknown", "vol": float(rolling_vol), "multiplier": 1.0}

    low_thresh = historical.quantile(0.25)
    high_thresh = historical.quantile(0.75)

    if rolling_vol <= low_thresh:
        return {"regime": "low", "vol": float(rolling_vol), "multiplier": 1.05}
    if rolling_vol >= high_thresh:
        return {"regime": "high", "vol": float(rolling_vol), "multiplier": 0.85}

    return {"regime": "normal", "vol": float(rolling_vol), "multiplier": 1.0}
