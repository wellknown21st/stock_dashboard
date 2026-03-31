"""
ML Prediction Module.

Provides simple price prediction using Linear Regression
and feature engineering on historical stock data.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from datetime import timedelta


def prepare_features(df: pd.DataFrame, lookback: int = 5) -> tuple:
    """
    Prepare features for ML model from stock data.
    
    Features include:
    - Lagged close prices (1 to `lookback` days)
    - Moving averages (7-day, 20-day)
    - Volume
    - Daily return
    - Day of week
    
    Args:
        df: DataFrame with stock data
        lookback: Number of lagged days to use as features
    
    Returns:
        X (features), y (target), feature_names
    """
    data = df.copy()
    
    # Create lagged features
    for i in range(1, lookback + 1):
        data[f'close_lag_{i}'] = data['close'].shift(i)
    
    # Additional features
    data['volume_norm'] = data['volume'] / data['volume'].max() if data['volume'].max() > 0 else 0
    data['price_range'] = data['high'] - data['low']
    data['close_to_open'] = data['close'] - data['open']
    
    # Drop rows with NaN from lagging
    data = data.dropna()
    
    feature_cols = [f'close_lag_{i}' for i in range(1, lookback + 1)]
    feature_cols += ['ma_7', 'ma_20', 'volume_norm', 'price_range', 'close_to_open', 'daily_return']
    
    # Filter to columns that exist
    feature_cols = [c for c in feature_cols if c in data.columns]
    
    X = data[feature_cols].values
    y = data['close'].values
    
    return X, y, feature_cols, data


def predict_prices(df: pd.DataFrame, days_ahead: int = 7) -> dict:
    """
    Predict stock prices for the next `days_ahead` trading days
    using Linear Regression.
    
    Args:
        df: DataFrame with historical stock data (must have close, ma_7, ma_20, etc.)
        days_ahead: Number of days to predict
    
    Returns:
        Dictionary with predictions and model metrics
    """
    if len(df) < 30:
        return {
            "error": "Insufficient data for prediction (need at least 30 rows)",
            "predictions": []
        }
    
    lookback = 5
    X, y, feature_cols, clean_data = prepare_features(df, lookback)
    
    if len(X) < 20:
        return {
            "error": "Insufficient clean data for prediction",
            "predictions": []
        }
    
    # Split: use last 20% for validation
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model
    model = LinearRegression()
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    train_score = model.score(X_train_scaled, y_train)
    test_score = model.score(X_test_scaled, y_test)
    
    # Predict future prices
    predictions = []
    last_known = df.tail(lookback + 20).copy()
    
    last_date = pd.to_datetime(df['date'].iloc[-1])
    current_close_values = list(df['close'].tail(lookback).values)
    
    for day in range(1, days_ahead + 1):
        # Build feature vector from recent history
        features = []
        
        # Lagged closes
        for i in range(lookback):
            features.append(current_close_values[-(i + 1)])
        
        # Moving averages (approximate from recent values)
        recent_closes = current_close_values[-7:] if len(current_close_values) >= 7 else current_close_values
        features.append(np.mean(recent_closes))  # ma_7 approx
        
        recent_20 = current_close_values[-20:] if len(current_close_values) >= 20 else current_close_values
        features.append(np.mean(recent_20))  # ma_20 approx
        
        # volume_norm, price_range, close_to_open, daily_return (use last known)
        features.append(0.5)  # normalized volume estimate
        features.append(float(df['high'].iloc[-1] - df['low'].iloc[-1]))
        features.append(float(df['close'].iloc[-1] - df['open'].iloc[-1]))
        features.append(float(df['daily_return'].iloc[-1]) if 'daily_return' in df.columns else 0.0)
        
        # Ensure feature vector matches training dimensions
        feature_vector = np.array(features[:len(feature_cols)]).reshape(1, -1)
        
        # Pad or trim to match
        if feature_vector.shape[1] < X_train_scaled.shape[1]:
            padding = np.zeros((1, X_train_scaled.shape[1] - feature_vector.shape[1]))
            feature_vector = np.hstack([feature_vector, padding])
        elif feature_vector.shape[1] > X_train_scaled.shape[1]:
            feature_vector = feature_vector[:, :X_train_scaled.shape[1]]
        
        feature_vector_scaled = scaler.transform(feature_vector)
        predicted_price = model.predict(feature_vector_scaled)[0]
        
        pred_date = last_date + timedelta(days=day)
        # Skip weekends
        while pred_date.weekday() >= 5:
            pred_date += timedelta(days=1)
        
        predictions.append({
            "date": pred_date.strftime("%Y-%m-%d"),
            "predicted_close": round(float(predicted_price), 2)
        })
        
        current_close_values.append(predicted_price)
    
    return {
        "model": "Linear Regression",
        "train_r2_score": round(train_score, 4),
        "test_r2_score": round(test_score, 4),
        "days_predicted": days_ahead,
        "predictions": predictions,
        "disclaimer": "This is a simplified model for educational purposes only. Not financial advice."
    }
