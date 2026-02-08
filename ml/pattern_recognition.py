"""
Pattern Recognition Module
Detects classic chart patterns using technical analysis
"""
import numpy as np
import pandas as pd
from scipy.signal import argrelextrema

def detect_support_resistance(prices, order=5):
    """
    Detect support and resistance levels
    """
    local_max = argrelextrema(prices, np.greater, order=order)[0]
    local_min = argrelextrema(prices, np.less, order=order)[0]
    
    resistance_levels = prices[local_max] if len(local_max) > 0 else []
    support_levels = prices[local_min] if len(local_min) > 0 else []
    
    return list(support_levels), list(resistance_levels)

def detect_double_top(prices, tolerance=0.02):
    """
    Detect double top pattern (bearish reversal)
    """
    if len(prices) < 50:
        return False, 0
    
    local_max_idx = argrelextrema(prices, np.greater, order=10)[0]
    
    if len(local_max_idx) < 2:
        return False, 0
    
    # Check last two peaks
    last_peaks = prices[local_max_idx[-2:]]
    
    if len(last_peaks) == 2:
        diff = abs(last_peaks[0] - last_peaks[1]) / last_peaks[0]
        if diff < tolerance:
            return True, 0.75  # High confidence bearish
    
    return False, 0

def detect_double_bottom(prices, tolerance=0.02):
    """
    Detect double bottom pattern (bullish reversal)
    """
    if len(prices) < 50:
        return False, 0
    
    local_min_idx = argrelextrema(prices, np.less, order=10)[0]
    
    if len(local_min_idx) < 2:
        return False, 0
    
    # Check last two troughs
    last_troughs = prices[local_min_idx[-2:]]
    
    if len(last_troughs) == 2:
        diff = abs(last_troughs[0] - last_troughs[1]) / last_troughs[0]
        if diff < tolerance:
            return True, 0.75  # High confidence bullish
    
    return False, 0

def detect_head_shoulders(prices, tolerance=0.03):
    """
    Detect head and shoulders pattern (bearish reversal)
    Returns: (is_pattern, confidence)
    """
    if len(prices) < 100:
        return False, 0
    
    local_max_idx = argrelextrema(prices, np.greater, order=15)[0]
    
    if len(local_max_idx) < 3:
        return False, 0
    
    # Need exactly 3 peaks for head & shoulders
    last_peaks = prices[local_max_idx[-3:]]
    
    if len(last_peaks) == 3:
        left_shoulder, head, right_shoulder = last_peaks
        
        # Head should be higher than shoulders
        if head > left_shoulder and head > right_shoulder:
            # Shoulders should be similar height
            shoulder_diff = abs(left_shoulder - right_shoulder) / left_shoulder
            if shoulder_diff < tolerance:
                return True, 0.8
    
    return False, 0

def detect_triangle(prices, window=50):
    """
    Detect triangle pattern (consolidation before breakout)
    """
    if len(prices) < window:
        return 'none', 0
    
    recent = prices[-window:]
    
    # Calculate trend of highs and lows
    highs = argrelextrema(recent, np.greater, order=5)[0]
    lows = argrelextrema(recent, np.less, order=5)[0]
    
    if len(highs) < 2 or len(lows) < 2:
        return 'none', 0
    
    high_slope = np.polyfit(highs, recent[highs], 1)[0]
    low_slope = np.polyfit(lows, recent[lows], 1)[0]
    
    # Ascending triangle: flat resistance, rising support
    if abs(high_slope) < 0.01 and low_slope > 0.02:
        return 'ascending', 0.7  # Bullish
    
    # Descending triangle: declining resistance, flat support
    elif high_slope < -0.02 and abs(low_slope) < 0.01:
        return 'descending', 0.7  # Bearish
    
    # Symmetrical triangle: converging
    elif abs(high_slope + low_slope) < 0.01:
        return 'symmetrical', 0.5  # Neutral, wait for breakout
    
    return 'none', 0

def detect_breakout(prices, volume, support_resistance_levels):
    """
    Detect breakout from key levels with volume confirmation
    """
    if len(prices) < 20 or len(volume) < 20:
        return False, 'none', 0
    
    current_price = prices[-1]
    recent_volume = volume[-10:]
    avg_volume = np.mean(volume[-50:-10]) if len(volume) > 50 else np.mean(volume[:-10])
    
    # Check for volume surge
    volume_surge = np.mean(recent_volume) > avg_volume * 1.5
    
    if not volume_surge:
        return False, 'none', 0
    
    # Check breakout through resistance
    for resistance in support_resistance_levels[1]:  # Resistance levels
        if resistance * 0.995 < current_price < resistance * 1.005:
            # Currently at resistance
            if prices[-2] < resistance < current_price:
                # Breakout above
                return True, 'bullish', 0.8
    
    # Check breakdown through support
    for support in support_resistance_levels[0]:  # Support levels
        if support * 0.995 < current_price < support * 1.005:
            if prices[-2] > support > current_price:
                # Breakdown below
                return True, 'bearish', 0.8
    
    return False, 'none', 0

def analyze_patterns(df):
    """
    Comprehensive pattern analysis
    Returns: dict with all detected patterns
    """
    if df.empty or len(df) < 100:
        return {}
    
    # Flatten MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    prices = df['Close'].values
    volume = df['Volume'].values if 'Volume' in df.columns else np.zeros(len(prices))
    
    # Detect all patterns
    support, resistance = detect_support_resistance(prices)
    double_top_detected, dt_conf = detect_double_top(prices)
    double_bottom_detected, db_conf = detect_double_bottom(prices)
    head_shoulders_detected, hs_conf = detect_head_shoulders(prices)
    triangle_type, triangle_conf = detect_triangle(prices)
    breakout_detected, breakout_dir, breakout_conf = detect_breakout(
        prices, volume, (support, resistance)
    )
    
    return {
        'support_levels': support[-3:] if len(support) > 0 else [],
        'resistance_levels': resistance[-3:] if len(resistance) > 0 else [],
        'double_top': {'detected': double_top_detected, 'confidence': dt_conf},
        'double_bottom': {'detected': double_bottom_detected, 'confidence': db_conf},
        'head_shoulders': {'detected': head_shoulders_detected, 'confidence': hs_conf},
        'triangle': {'type': triangle_type, 'confidence': triangle_conf},
        'breakout': {
            'detected': breakout_detected,
            'direction': breakout_dir,
            'confidence': breakout_conf
        }
    }

def get_pattern_signal(patterns):
    """
    Convert pattern analysis to trading signal
    Returns: 'buy', 'sell', 'hold', confidence
    """
    if not patterns:
        return 'hold', 0
    
    bullish_score = 0
    bearish_score = 0
    max_confidence = 0
    
    # Double bottom = bullish
    if patterns.get('double_bottom', {}).get('detected'):
        conf = patterns['double_bottom']['confidence']
        bullish_score += conf
        max_confidence = max(max_confidence, conf)
    
    # Double top = bearish
    if patterns.get('double_top', {}).get('detected'):
        conf = patterns['double_top']['confidence']
        bearish_score += conf
        max_confidence = max(max_confidence, conf)
    
    # Head & shoulders = bearish
    if patterns.get('head_shoulders', {}).get('detected'):
        conf = patterns['head_shoulders']['confidence']
        bearish_score += conf
        max_confidence = max(max_confidence, conf)
    
    # Triangle patterns
    triangle = patterns.get('triangle', {})
    if triangle.get('type') == 'ascending':
        bullish_score += triangle.get('confidence', 0)
    elif triangle.get('type') == 'descending':
        bearish_score += triangle.get('confidence', 0)
    
    # Breakout patterns
    breakout = patterns.get('breakout', {})
    if breakout.get('detected'):
        conf = breakout.get('confidence', 0)
        if breakout.get('direction') == 'bullish':
            bullish_score += conf
        elif breakout.get('direction') == 'bearish':
            bearish_score += conf
        max_confidence = max(max_confidence, conf)
    
    # Determine signal
    if bullish_score > bearish_score and bullish_score > 0.5:
        return 'buy', min(bullish_score, 1.0)
    elif bearish_score > bullish_score and bearish_score > 0.5:
        return 'sell', min(bearish_score, 1.0)
    else:
        return 'hold', 0
