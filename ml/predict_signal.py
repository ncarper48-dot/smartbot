import pandas as pd
import numpy as np
import joblib
import os

def load_model(model_path="ml/signal_model.pkl"):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")
    return joblib.load(model_path)

def predict_signal(features, model=None):
    """Predict trade signal using trained ML model.
    features: dict of feature_name: value
    Returns: int (1=buy, 0=hold, -1=sell)
    """
    if model is None:
        model = load_model()
    X = pd.DataFrame([features])
    return int(model.predict(X)[0])

# Example usage:
if __name__ == "__main__":
    features = {
        'rsi': 42,
        'macd': 0.15,
        'sma_short': 10.8,
        'sma_long': 10.5,
        'bb_upper': 11.2,
        'bb_lower': 9.9,
        'volume': 105000,
        'price_change_1h': 0.4,
        'price_change_3h': 1.1
    }
    model = load_model()
    signal = predict_signal(features, model)
    print(f"Predicted signal: {signal}")
