"""
Deep Learning Model for SmartBot
Advanced LSTM-based price prediction and signal generation
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

# TensorFlow can crash on some CPUs; allow opt-out via env flag.
_disable_tf = os.getenv("SMARTBOT_DISABLE_TF", "0") == "1"

try:
    if _disable_tf:
        raise ImportError("SMARTBOT_DISABLE_TF=1")
    from tensorflow import keras
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional
    from tensorflow.keras.optimizers import Adam
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False
    print("⚠️ TensorFlow disabled/unavailable. Deep learning features disabled.")

class DeepLearningPredictor:
    """
    Advanced LSTM model for price prediction and signal generation
    """
    def __init__(self, model_path="ml/lstm_model.h5", scaler_path="ml/lstm_scaler.pkl"):
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.model = None
        self.scaler = None
        self.sequence_length = 60  # 60 time steps
        
    def load_model(self):
        """Load trained LSTM model and scaler"""
        if not KERAS_AVAILABLE:
            return False
            
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            try:
                self.model = load_model(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                return True
            except Exception as e:
                print(f"⚠️ Error loading LSTM model: {e}")
                return False
        return False
    
    def create_model(self, input_shape):
        """Create LSTM model architecture"""
        if not KERAS_AVAILABLE:
            return None
            
        model = Sequential([
            Bidirectional(LSTM(128, return_sequences=True, input_shape=input_shape)),
            Dropout(0.2),
            Bidirectional(LSTM(64, return_sequences=True)),
            Dropout(0.2),
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(1, activation='linear')
        ])
        
        model.compile(optimizer=Adam(learning_rate=0.001), 
                     loss='mse', 
                     metrics=['mae'])
        return model
    
    def prepare_sequences(self, data, sequence_length=60):
        """Prepare sequences for LSTM input"""
        sequences = []
        targets = []
        
        for i in range(len(data) - sequence_length):
            sequences.append(data[i:i+sequence_length])
            targets.append(data[i+sequence_length])
            
        return np.array(sequences), np.array(targets)
    
    def train(self, price_data, epochs=50, batch_size=32):
        """Train LSTM model on historical price data"""
        if not KERAS_AVAILABLE:
            print("⚠️ TensorFlow not installed. Cannot train deep learning model.")
            return False
            
        try:
            # Normalize data
            self.scaler = MinMaxScaler()
            scaled_data = self.scaler.fit_transform(price_data.reshape(-1, 1))
            
            # Create sequences
            X, y = self.prepare_sequences(scaled_data, self.sequence_length)
            
            # Split train/test
            split = int(0.8 * len(X))
            X_train, X_test = X[:split], X[split:]
            y_train, y_test = y[:split], y[split:]
            
            # Create and train model
            self.model = self.create_model((X_train.shape[1], X_train.shape[2]))
            
            history = self.model.fit(
                X_train, y_train,
                epochs=epochs,
                batch_size=batch_size,
                validation_data=(X_test, y_test),
                verbose=1
            )
            
            # Save model and scaler
            self.model.save(self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            
            print(f"✅ LSTM model trained and saved to {self.model_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error training LSTM model: {e}")
            return False
    
    def predict_next_prices(self, recent_prices, n_steps=5):
        """Predict next N price movements"""
        if self.model is None or self.scaler is None:
            if not self.load_model():
                return None
        
        try:
            # Prepare input sequence
            scaled_prices = self.scaler.transform(recent_prices.reshape(-1, 1))
            
            if len(scaled_prices) < self.sequence_length:
                return None
                
            sequence = scaled_prices[-self.sequence_length:]
            predictions = []
            
            # Predict next n_steps
            current_sequence = sequence.copy()
            for _ in range(n_steps):
                pred_scaled = self.model.predict(current_sequence.reshape(1, self.sequence_length, 1), verbose=0)
                pred_price = self.scaler.inverse_transform(pred_scaled)[0][0]
                predictions.append(pred_price)
                
                # Update sequence for next prediction
                current_sequence = np.append(current_sequence[1:], pred_scaled, axis=0)
            
            return predictions
            
        except Exception as e:
            print(f"⚠️ Prediction error: {e}")
            return None
    
    def get_signal(self, recent_prices):
        """Generate trading signal based on predictions"""
        predictions = self.predict_next_prices(recent_prices, n_steps=3)
        
        if predictions is None:
            return 0, 0.0  # Hold, no confidence
        
        current_price = recent_prices[-1]
        avg_predicted_price = np.mean(predictions)
        price_change = (avg_predicted_price - current_price) / current_price
        
        # Generate signal with confidence
        if price_change > 0.005:  # Predicted 0.5% gain
            signal = 1  # Buy
            confidence = min(abs(price_change) * 100, 1.0)
        elif price_change < -0.005:  # Predicted 0.5% loss
            signal = -1  # Sell
            confidence = min(abs(price_change) * 100, 1.0)
        else:
            signal = 0  # Hold
            confidence = 0.0
        
        return signal, confidence


class EnsemblePredictor:
    """
    Ensemble model combining multiple ML approaches
    """
    def __init__(self):
        self.lstm_predictor = DeepLearningPredictor()
        self.random_forest_model = None
        
    def load_models(self):
        """Load all ensemble models"""
        lstm_loaded = self.lstm_predictor.load_model()
        
        rf_path = "ml/signal_model.pkl"
        if os.path.exists(rf_path):
            self.random_forest_model = joblib.load(rf_path)
        
        return lstm_loaded or self.random_forest_model is not None
    
    def get_ensemble_signal(self, recent_prices, features):
        """
        Get signal from ensemble of models
        Returns: (signal, confidence, details)
        """
        signals = []
        confidences = []
        
        # LSTM prediction
        if self.lstm_predictor.model is not None:
            lstm_signal, lstm_conf = self.lstm_predictor.get_signal(recent_prices)
            signals.append(lstm_signal)
            confidences.append(lstm_conf)
        
        # Random Forest prediction
        if self.random_forest_model is not None:
            try:
                X = pd.DataFrame([features])
                rf_signal = int(self.random_forest_model.predict(X)[0])
                rf_proba = self.random_forest_model.predict_proba(X)[0]
                rf_conf = max(rf_proba)
                signals.append(rf_signal)
                confidences.append(rf_conf)
            except:
                pass
        
        if not signals:
            return 0, 0.0, "No models available"
        
        # Weighted voting (LSTM gets higher weight)
        weights = [0.6, 0.4] if len(signals) == 2 else [1.0]
        weighted_signal = sum(s * w for s, w in zip(signals, weights[:len(signals)]))
        avg_confidence = np.mean(confidences)
        
        # Final signal
        if weighted_signal > 0.3:
            final_signal = 1  # Buy
        elif weighted_signal < -0.3:
            final_signal = -1  # Sell
        else:
            final_signal = 0  # Hold
        
        details = {
            'lstm_signal': signals[0] if len(signals) > 0 else None,
            'rf_signal': signals[1] if len(signals) > 1 else None,
            'confidence': avg_confidence,
            'models_used': len(signals)
        }
        
        return final_signal, avg_confidence, details


# Quick test functionality
if __name__ == "__main__":
    print("🤖 SmartBot Deep Learning Module")
    print("=" * 50)
    
    if KERAS_AVAILABLE:
        print("✅ TensorFlow/Keras available")
        predictor = DeepLearningPredictor()
        print(f"📁 Model path: {predictor.model_path}")
        
        if predictor.load_model():
            print("✅ LSTM model loaded successfully")
        else:
            print("⚠️ No trained model found. Train first with train_deep_model.py")
    else:
        print("❌ TensorFlow not installed")
        print("   Install with: pip install tensorflow")
    
    print("\n🔄 Testing ensemble predictor...")
    ensemble = EnsemblePredictor()
    if ensemble.load_models():
        print("✅ Ensemble models loaded")
    else:
        print("⚠️ No models available")
