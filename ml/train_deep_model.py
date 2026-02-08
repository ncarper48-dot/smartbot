"""
Train Deep Learning LSTM Model for SmartBot
Downloads historical data and trains advanced price prediction model
"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from deep_learning_model import DeepLearningPredictor, KERAS_AVAILABLE

def download_training_data(symbols=['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'], 
                           period='2y'):
    """Download historical price data for training"""
    print("📥 Downloading historical data...")
    all_prices = []
    
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if len(hist) > 0:
                prices = hist['Close'].values
                all_prices.extend(prices)
                print(f"  ✅ {symbol}: {len(prices)} data points")
        except Exception as e:
            print(f"  ⚠️ {symbol}: {e}")
    
    return np.array(all_prices)


def main():
    print("🚀 SmartBot Deep Learning Training")
    print("=" * 60)
    
    if not KERAS_AVAILABLE:
        print("❌ TensorFlow is not installed!")
        print("   Install with: pip install tensorflow")
        print("   Or: pip install tensorflow-cpu  (for CPU-only)")
        return
    
    # Download training data
    price_data = download_training_data()
    
    if len(price_data) < 1000:
        print("❌ Not enough training data!")
        return
    
    print(f"\n📊 Total training samples: {len(price_data)}")
    
    # Train model
    predictor = DeepLearningPredictor()
    print("\n🤖 Training LSTM model...")
    print("   This may take several minutes...")
    
    success = predictor.train(price_data, epochs=30, batch_size=32)
    
    if success:
        print("\n✅ Training complete!")
        print("=" * 60)
        print("🎯 LSTM model is ready for SmartBot")
        print("   Model will be automatically used in live trading")
    else:
        print("\n❌ Training failed!")
    

if __name__ == "__main__":
    main()
