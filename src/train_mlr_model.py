#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Training Script for Multiple Linear Regression Emission Predictor
Trains MLR model and exports coefficients, scaler, and encoder
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import os


def generate_training_data(n_samples=1000):
    """
    Generate synthetic training dataset with realistic patterns
    
    Features:
    - distance_km: Route distance in kilometers (0.5 - 500)
    - fuel_type: Categorical (Bensin, Diesel, Listrik)
    - vehicle_type: Categorical (LCGC, SUV, Sedan, EV)
    - fuel_consumption_kml: Average fuel consumption in km/L (5 - 25)
    - avg_speed_kmh: Average speed in km/h (10 - 120)
    
    Target:
    - emission_g: CO₂ emission in grams
    
    Returns:
        DataFrame with features and target
    """
    np.random.seed(42)
    
    data = []
    
    # Define realistic parameters for each vehicle-fuel combination
    vehicle_configs = {
        'LCGC': {
            'fuels': ['Bensin'],
            'consumption': {'Bensin': (16, 20)},  # km/L range
            'base_emission': 120  # g/km
        },
        'SUV': {
            'fuels': ['Bensin', 'Diesel'],
            'consumption': {'Bensin': (8, 12), 'Diesel': (10, 14)},
            'base_emission': 180  # g/km for Bensin
        },
        'Sedan': {
            'fuels': ['Bensin', 'Diesel'],
            'consumption': {'Bensin': (12, 16), 'Diesel': (14, 18)},
            'base_emission': 140  # g/km
        },
        'EV': {
            'fuels': ['Listrik'],
            'consumption': {'Listrik': (80, 120)},  # km per kWh equivalent
            'base_emission': 40  # g/km (from electricity generation)
        }
    }
    
    for _ in range(n_samples):
        # Randomly select vehicle type
        vehicle_type = np.random.choice(list(vehicle_configs.keys()))
        config = vehicle_configs[vehicle_type]
        
        # Select compatible fuel type
        fuel_type = np.random.choice(config['fuels'])
        
        # Generate distance (more samples in common range 1-100 km)
        if np.random.random() < 0.7:
            distance_km = np.random.uniform(1, 100)
        else:
            distance_km = np.random.uniform(100, 500)
        
        # Generate fuel consumption within realistic range
        consumption_range = config['consumption'][fuel_type]
        fuel_consumption_kml = np.random.uniform(*consumption_range)
        
        # Generate average speed (more samples in common range 30-80 km/h)
        if np.random.random() < 0.7:
            avg_speed_kmh = np.random.uniform(30, 80)
        else:
            avg_speed_kmh = np.random.uniform(10, 120)
        
        # Calculate emission based on realistic physics
        base_emission_factor = config['base_emission']
        
        # Adjust for fuel type
        if fuel_type == 'Diesel':
            base_emission_factor *= 1.1  # Diesel typically higher emissions
        
        # Adjust for speed (U-shaped curve: optimal around 60-80 km/h)
        speed_factor = 1.0
        if avg_speed_kmh < 40:
            speed_factor = 1.0 + (40 - avg_speed_kmh) * 0.01  # Slower = more emissions
        elif avg_speed_kmh > 90:
            speed_factor = 1.0 + (avg_speed_kmh - 90) * 0.005  # Faster = more emissions
        else:
            speed_factor = 0.95  # Optimal speed range
        
        # Adjust for fuel consumption (inverse relationship)
        consumption_factor = 20.0 / fuel_consumption_kml  # Lower consumption = lower emissions
        
        # Calculate final emission
        emission_g = distance_km * base_emission_factor * speed_factor * consumption_factor
        
        # Add some realistic noise (±5%)
        emission_g *= np.random.uniform(0.95, 1.05)
        
        data.append({
            'distance_km': distance_km,
            'fuel_type': fuel_type,
            'vehicle_type': vehicle_type,
            'fuel_consumption_kml': fuel_consumption_kml,
            'avg_speed_kmh': avg_speed_kmh,
            'emission_g': emission_g
        })
    
    return pd.DataFrame(data)


def train_mlr_model(save_dir='models'):
    """
    Train Multiple Linear Regression model and save artifacts
    
    Args:
        save_dir: Directory to save model files
        
    Returns:
        dict with training metrics and model info
    """
    print("="*70)
    print("Training Multiple Linear Regression Emission Predictor")
    print("="*70)
    
    # Generate training data
    print("\n1. Generating training data...")
    df = generate_training_data(n_samples=1000)
    print(f"   Generated {len(df)} samples")
    print(f"   Features: {list(df.columns[:-1])}")
    print(f"   Target: emission_g")
    
    # Separate features and target
    X = df.drop('emission_g', axis=1)
    y = df['emission_g']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"   Train set: {len(X_train)} samples")
    print(f"   Test set: {len(X_test)} samples")
    
    # Encode categorical features
    print("\n2. Encoding categorical features...")
    categorical_features = ['fuel_type', 'vehicle_type']
    encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    
    # Fit encoder on training data
    X_train_categorical = X_train[categorical_features]
    X_test_categorical = X_test[categorical_features]
    
    encoder.fit(X_train_categorical)
    
    # Transform categorical features
    X_train_encoded = encoder.transform(X_train_categorical)
    X_test_encoded = encoder.transform(X_test_categorical)
    
    # Get feature names
    encoded_feature_names = encoder.get_feature_names_out(categorical_features)
    print(f"   Encoded features: {list(encoded_feature_names)}")
    
    # Combine with numerical features
    numerical_features = ['distance_km', 'fuel_consumption_kml', 'avg_speed_kmh']
    X_train_numerical = X_train[numerical_features].values
    X_test_numerical = X_test[numerical_features].values
    
    X_train_combined = np.hstack([X_train_numerical, X_train_encoded])
    X_test_combined = np.hstack([X_test_numerical, X_test_encoded])
    
    # Scale features
    print("\n3. Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_combined)
    X_test_scaled = scaler.transform(X_test_combined)
    
    # Train MLR model
    print("\n4. Training Multiple Linear Regression model...")
    model = LinearRegression()
    model.fit(X_train_scaled, y_train)
    
    # Evaluate model
    print("\n5. Evaluating model...")
    y_train_pred = model.predict(X_train_scaled)
    y_test_pred = model.predict(X_test_scaled)
    
    train_r2 = r2_score(y_train, y_train_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
    train_mae = mean_absolute_error(y_train, y_train_pred)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    
    print(f"   Training R²: {train_r2:.4f}")
    print(f"   Test R²: {test_r2:.4f}")
    print(f"   Training RMSE: {train_rmse:.2f} g")
    print(f"   Test RMSE: {test_rmse:.2f} g")
    print(f"   Training MAE: {train_mae:.2f} g")
    print(f"   Test MAE: {test_mae:.2f} g")
    
    # Display model coefficients
    print("\n6. Model coefficients:")
    print(f"   Intercept (β₀): {model.intercept_:.2f}")
    
    all_feature_names = numerical_features + list(encoded_feature_names)
    print("   Feature coefficients:")
    for i, (name, coef) in enumerate(zip(all_feature_names, model.coef_)):
        print(f"      β{i+1} ({name}): {coef:.4f}")
    
    # Save model artifacts
    print("\n7. Saving model artifacts...")
    model_path = os.path.join(save_dir, 'mlr_emission_model.joblib')
    scaler_path = os.path.join(save_dir, 'mlr_emission_scaler.joblib')
    encoder_path = os.path.join(save_dir, 'mlr_emission_encoder.joblib')
    
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    joblib.dump(encoder, encoder_path)
    
    print(f"   Model saved to: {model_path}")
    print(f"   Scaler saved to: {scaler_path}")
    print(f"   Encoder saved to: {encoder_path}")
    
    # Save feature names for reference
    feature_info = {
        'numerical_features': numerical_features,
        'categorical_features': categorical_features,
        'encoded_feature_names': list(encoded_feature_names),
        'all_feature_names': all_feature_names
    }
    feature_info_path = os.path.join(save_dir, 'mlr_feature_info.joblib')
    joblib.dump(feature_info, feature_info_path)
    print(f"   Feature info saved to: {feature_info_path}")
    
    print("\n" + "="*70)
    print("Training completed successfully!")
    print("="*70)
    
    return {
        'train_r2': train_r2,
        'test_r2': test_r2,
        'train_rmse': train_rmse,
        'test_rmse': test_rmse,
        'train_mae': train_mae,
        'test_mae': test_mae,
        'intercept': model.intercept_,
        'coefficients': dict(zip(all_feature_names, model.coef_)),
        'n_features': len(all_feature_names)
    }


if __name__ == "__main__":
    # Train and save model
    metrics = train_mlr_model()
    
    # Display summary
    print("\nModel Summary:")
    print(f"  R² Score (Test): {metrics['test_r2']:.4f}")
    print(f"  RMSE (Test): {metrics['test_rmse']:.2f} g")
    print(f"  MAE (Test): {metrics['test_mae']:.2f} g")
    print(f"  Number of features: {metrics['n_features']}")
