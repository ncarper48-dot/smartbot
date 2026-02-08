"""
Multi-Timeframe Analysis Module
Analyzes multiple timeframes (5m, 15m, 1h, 1d) for confluence
"""
import yfinance as yf
import pandas as pd
import numpy as np

def get_timeframe_signal(ticker, interval, periods):
    """
    Get trend signal for a specific timeframe
    Returns: 1 (bullish), 0 (neutral), -1 (bearish), None (error)
    """
    try:
        if interval == '1d':
            df = yf.download(ticker, period='90d', interval=interval, progress=False)
        elif interval == '1h':
            df = yf.download(ticker, period='30d', interval=interval, progress=False)
        else:
            df = yf.download(ticker, period='5d', interval=interval, progress=False)
        
        if df.empty or len(df) < 20:
            return None
        
        # Flatten MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        close = df['Close'].values
        
        # Calculate SMAs
        sma_short = np.mean(close[-5:])
        sma_long = np.mean(close[-20:])
        current = close[-1]
        
        # Trend determination
        if current > sma_short > sma_long:
            return 1  # Strong bullish
        elif current < sma_short < sma_long:
            return -1  # Strong bearish
        else:
            return 0  # Neutral/mixed
    
    except Exception as e:
        return None

def analyze_all_timeframes(ticker):
    """
    Analyze all timeframes and return confluence score
    Returns: dict with signals and overall score
    """
    timeframes = {
        '5m': get_timeframe_signal(ticker, '5m', 100),
        '15m': get_timeframe_signal(ticker, '15m', 100),
        '1h': get_timeframe_signal(ticker, '1h', 60),
        '1d': get_timeframe_signal(ticker, '1d', 90)
    }
    
    # Calculate confluence
    valid_signals = [s for s in timeframes.values() if s is not None]
    
    if not valid_signals:
        return {'timeframes': timeframes, 'confluence': 0, 'signal': 'hold'}
    
    confluence_score = sum(valid_signals) / len(valid_signals)
    
    # Determine overall signal
    if confluence_score >= 0.75:
        signal = 'strong_buy'
    elif confluence_score >= 0.25:
        signal = 'buy'
    elif confluence_score <= -0.75:
        signal = 'strong_sell'
    elif confluence_score <= -0.25:
        signal = 'sell'
    else:
        signal = 'hold'
    
    return {
        'timeframes': timeframes,
        'confluence': confluence_score,
        'signal': signal,
        'strength': abs(confluence_score)
    }

def check_timeframe_alignment(ticker, required_agreement=0.75):
    """
    Check if enough timeframes agree for high-confidence trade
    Returns: True if aligned, False otherwise
    """
    result = analyze_all_timeframes(ticker)
    return abs(result['confluence']) >= required_agreement
