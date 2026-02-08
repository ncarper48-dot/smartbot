import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

# Example: ML pipeline for trade signal prediction
# This script can be scheduled to retrain regularly or run on demand

def load_data(csv_path):
    """Load historical features and labels for training."""
    df = pd.read_csv(csv_path)
    X = df.drop(['signal'], axis=1)
    y = df['signal']
    return X, y

def train_model(X, y):
    """Train a RandomForest model for signal prediction."""
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred))
    return clf

def save_model(model, path):
    joblib.dump(model, path)
    print(f"Model saved to {path}")

if __name__ == "__main__":
    # Example usage: python ml/train_signal_model.py
    X, y = load_data("ml/historical_signals.csv")
    model = train_model(X, y)
    save_model(model, "ml/signal_model.pkl")
