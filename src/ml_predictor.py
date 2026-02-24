#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Machine Learning Predictor for Fuel Consumption
Predicts actual fuel consumption based on driving style, traffic, and weather
"""

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os

class FuelConsumptionPredictor:
    """
    ML Model to predict fuel consumption adjustment factor
    based on driving conditions
    """
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.model_path = 'models/fuel_model.joblib'
        self.scaler_path = 'models/fuel_scaler.joblib'
        
        # Try to load existing model
        self._load_model()
        
        # If no model exists, train with synthetic data
        if not self.is_trained:
            self._train_initial_model()
    
    def _generate_training_data(self, n_samples=1000):
        """
        Generate synthetic training data based on real-world patterns
        
        Features:
        1. driving_style: 0=eco, 1=normal, 2=aggressive (0-2)
        2. traffic_condition: 0=smooth, 1=moderate, 2=heavy (0-2)
        3. weather_condition: 0=clear, 1=rain, 2=storm (0-2)
        4. road_type: 0=highway, 1=city, 2=mixed (0-2)
        5. speed_avg: Average speed in km/h (20-120)
        6. ac_usage: 0=off, 1=on (0-1)
        
        Target:
        - adjustment_factor: Multiplier for base emission factor (0.7-1.5)
          1.0 = normal conditions
          <1.0 = better than expected (eco driving, smooth traffic)
          >1.0 = worse than expected (aggressive, heavy traffic)
        """
        np.random.seed(42)
        
        X = []
        y = []
        
        for _ in range(n_samples):
            # Generate features
            driving_style = np.random.randint(0, 3)
            traffic = np.random.randint(0, 3)
            weather = np.random.randint(0, 3)
            road_type = np.random.randint(0, 3)
            speed_avg = np.random.uniform(20, 120)
            ac_usage = np.random.randint(0, 2)
            
            # Calculate adjustment factor based on conditions
            base_factor = 1.0
            
            # Driving style impact (±15%)
            if driving_style == 0:  # Eco
                base_factor *= 0.85
            elif driving_style == 2:  # Aggressive
                base_factor *= 1.15
            
            # Traffic impact (±20%)
            if traffic == 0:  # Smooth
                base_factor *= 0.90
            elif traffic == 2:  # Heavy
                base_factor *= 1.20
            
            # Weather impact (±10%)
            if weather == 0:  # Clear
                base_factor *= 0.95
            elif weather == 2:  # Storm
                base_factor *= 1.10
            
            # Road type impact (±10%)
            if road_type == 0:  # Highway
                base_factor *= 0.90
            elif road_type == 1:  # City
                base_factor *= 1.10
            
            # Speed impact
            if speed_avg < 40:  # Very slow (city traffic)
                base_factor *= 1.15
            elif speed_avg > 80:  # Highway speed (optimal)
                base_factor *= 0.95
            
            # AC usage impact (+5%)
            if ac_usage == 1:
                base_factor *= 1.05
            
            # Add some noise
            base_factor *= np.random.uniform(0.95, 1.05)
            
            # Clip to reasonable range
            base_factor = np.clip(base_factor, 0.7, 1.5)
            
            X.append([driving_style, traffic, weather, road_type, speed_avg, ac_usage])
            y.append(base_factor)
        
        return np.array(X), np.array(y)
    
    def _train_initial_model(self):
        """Train initial model with synthetic data"""
        print("Training initial ML model for fuel consumption prediction...")
        
        # Generate training data
        X_train, y_train = self._generate_training_data(1000)
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Train Random Forest model
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # Save model
        self._save_model()
        
        print("Model trained successfully!")
        print(f"Model score (R²): {self.model.score(X_train_scaled, y_train):.4f}")
    
    def _save_model(self):
        """Save model and scaler to disk"""
        try:
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            print(f"Model saved to {self.model_path}")
        except Exception as e:
            print(f"Warning: Could not save model: {e}")
    
    def _load_model(self):
        """Load model and scaler from disk"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.is_trained = True
                print("Loaded existing ML model")
        except Exception as e:
            print(f"Could not load model: {e}")
            self.is_trained = False
    
    def predict_adjustment_factor(self, driving_style, traffic_condition, 
                                  weather_condition, road_type, speed_avg, ac_usage):
        """
        Predict fuel consumption adjustment factor
        
        Args:
            driving_style: 0=eco, 1=normal, 2=aggressive
            traffic_condition: 0=smooth, 1=moderate, 2=heavy
            weather_condition: 0=clear, 1=rain, 2=storm
            road_type: 0=highway, 1=city, 2=mixed
            speed_avg: Average speed in km/h (20-120)
            ac_usage: 0=off, 1=on
        
        Returns:
            adjustment_factor: Multiplier for base emission factor (0.7-1.5)
        """
        if not self.is_trained:
            return 1.0  # Default to no adjustment
        
        # Prepare input
        X = np.array([[driving_style, traffic_condition, weather_condition, 
                      road_type, speed_avg, ac_usage]])
        
        # Scale input
        X_scaled = self.scaler.transform(X)
        
        # Predict
        adjustment = self.model.predict(X_scaled)[0]
        
        # Clip to reasonable range
        adjustment = np.clip(adjustment, 0.7, 1.5)
        
        return float(adjustment)
    
    def get_feature_importance(self):
        """Get feature importance from the model"""
        if not self.is_trained or self.model is None:
            return None
        
        feature_names = [
            'Driving Style',
            'Traffic Condition',
            'Weather Condition',
            'Road Type',
            'Average Speed',
            'AC Usage'
        ]
        
        importances = self.model.feature_importances_
        
        return dict(zip(feature_names, importances))


def calculate_adjusted_emission(distance_km, base_emission_factor, 
                                driving_style, traffic_condition, 
                                weather_condition, road_type, 
                                speed_avg, ac_usage):
    """
    Calculate emission with ML-based adjustment
    
    Args:
        distance_km: Distance in kilometers
        base_emission_factor: Base emission factor (g CO2/km)
        driving_style: 0=eco, 1=normal, 2=aggressive
        traffic_condition: 0=smooth, 1=moderate, 2=heavy
        weather_condition: 0=clear, 1=rain, 2=storm
        road_type: 0=highway, 1=city, 2=mixed
        speed_avg: Average speed in km/h
        ac_usage: 0=off, 1=on
    
    Returns:
        dict with:
        - base_emission: Emission without adjustment
        - adjusted_emission: Emission with ML adjustment
        - adjustment_factor: The multiplier used
        - difference: Difference between adjusted and base
    """
    # Initialize predictor
    predictor = FuelConsumptionPredictor()
    
    # Get adjustment factor from ML model
    adjustment_factor = predictor.predict_adjustment_factor(
        driving_style, traffic_condition, weather_condition,
        road_type, speed_avg, ac_usage
    )
    
    # Calculate emissions
    base_emission = distance_km * base_emission_factor
    adjusted_emission_factor = base_emission_factor * adjustment_factor
    adjusted_emission = distance_km * adjusted_emission_factor
    
    difference = adjusted_emission - base_emission
    difference_pct = (difference / base_emission) * 100
    
    return {
        'base_emission_g': base_emission,
        'base_emission_kg': base_emission / 1000,
        'adjusted_emission_g': adjusted_emission,
        'adjusted_emission_kg': adjusted_emission / 1000,
        'adjustment_factor': adjustment_factor,
        'difference_g': difference,
        'difference_kg': difference / 1000,
        'difference_pct': difference_pct,
        'adjusted_emission_factor': adjusted_emission_factor
    }


# Mapping untuk UI
DRIVING_STYLE_MAP = {
    'eco': 0,
    'normal': 1,
    'aggressive': 2
}

TRAFFIC_MAP = {
    'smooth': 0,
    'moderate': 1,
    'heavy': 2
}

WEATHER_MAP = {
    'clear': 0,
    'rain': 1,
    'storm': 2
}

ROAD_TYPE_MAP = {
    'highway': 0,
    'city': 1,
    'mixed': 2
}

AC_USAGE_MAP = {
    'off': 0,
    'on': 1
}


if __name__ == "__main__":
    # Test the predictor
    print("="*70)
    print("Testing Fuel Consumption ML Predictor")
    print("="*70)
    
    predictor = FuelConsumptionPredictor()
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Eco driving, smooth traffic, clear weather',
            'params': (0, 0, 0, 0, 80, 0)
        },
        {
            'name': 'Aggressive driving, heavy traffic, rain',
            'params': (2, 2, 1, 1, 30, 1)
        },
        {
            'name': 'Normal driving, moderate traffic, clear',
            'params': (1, 1, 0, 2, 60, 1)
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        factor = predictor.predict_adjustment_factor(*scenario['params'])
        print(f"  Adjustment Factor: {factor:.3f}")
        print(f"  Impact: {(factor - 1) * 100:+.1f}%")
    
    # Show feature importance
    print("\n" + "="*70)
    print("Feature Importance:")
    print("="*70)
    importance = predictor.get_feature_importance()
    if importance:
        for feature, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True):
            print(f"  {feature:20s}: {imp:.4f}")
