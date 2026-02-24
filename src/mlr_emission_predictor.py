#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLR Emission Predictor
Multiple Linear Regression model for CO₂ emission prediction
"""

import numpy as np
import joblib
import os
import logging
from typing import Dict, Tuple, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLREmissionPredictor:
    """
    Core ML prediction engine using Multiple Linear Regression.
    
    Predicts CO₂ emissions based on:
    - Distance (km)
    - Fuel type (Bensin, Diesel, Listrik)
    - Vehicle type (LCGC, SUV, Sedan, EV)
    - Fuel consumption (km/L)
    - Average speed (km/h)
    """
    
    # Supported categorical values
    SUPPORTED_FUEL_TYPES = ['Bensin', 'Diesel', 'Listrik']
    SUPPORTED_VEHICLE_TYPES = ['LCGC', 'SUV', 'Sedan', 'EV']
    
    # Model version tracking
    MODEL_VERSION = "1.0.0"
    
    def __init__(self, 
                 model_path: str = 'models/mlr_emission_model.joblib',
                 scaler_path: str = 'models/mlr_emission_scaler.joblib',
                 encoder_path: str = 'models/mlr_emission_encoder.joblib'):
        """
        Initialize predictor and load trained model.
        
        Args:
            model_path: Path to trained MLR model file
            scaler_path: Path to feature scaler file
            encoder_path: Path to categorical encoder file
            
        Raises:
            FileNotFoundError: If model files are missing
            ValueError: If model files are corrupted
        """
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.encoder_path = encoder_path
        
        self.model = None
        self.scaler = None
        self.encoder = None
        self.is_loaded = False
        
        # Version tracking
        self.model_version = None
        self.model_loaded_at = None
        self.model_file_timestamps = {}
        
        # Load model artifacts
        self._load_model()
    
    def _load_model(self):
        """
        Load model, scaler, and encoder from disk with version tracking.
        
        Raises:
            FileNotFoundError: If any required file is missing
            ValueError: If files are corrupted or invalid
        """
        # Check if all files exist
        missing_files = []
        if not os.path.exists(self.model_path):
            missing_files.append(self.model_path)
        if not os.path.exists(self.scaler_path):
            missing_files.append(self.scaler_path)
        if not os.path.exists(self.encoder_path):
            missing_files.append(self.encoder_path)
        
        if missing_files:
            raise FileNotFoundError(
                f"Missing required model files: {', '.join(missing_files)}. "
                f"Please train the model first using train_mlr_model.py"
            )
        
        try:
            # Store file timestamps for hot-swap detection
            self.model_file_timestamps = {
                'model': os.path.getmtime(self.model_path),
                'scaler': os.path.getmtime(self.scaler_path),
                'encoder': os.path.getmtime(self.encoder_path)
            }
            
            # Load model artifacts
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            self.encoder = joblib.load(self.encoder_path)
            
            # Validate loaded objects
            self._validate_model_structure()
            
            # Load or set version information
            self._load_version_info()
            
            # Record load time
            self.model_loaded_at = datetime.now()
            
            self.is_loaded = True
            
            # Log successful load
            logger.info(
                f"Model loaded successfully. Version: {self.model_version}, "
                f"Loaded at: {self.model_loaded_at.isoformat()}"
            )
            
        except Exception as e:
            if isinstance(e, (FileNotFoundError, ValueError)):
                raise
            raise ValueError(
                f"Failed to load model files. Files may be corrupted: {str(e)}"
            )
    
    def _validate_model_structure(self):
        """
        Validate that loaded model has the expected structure.
        
        Raises:
            ValueError: If model structure is invalid
        """
        # Validate model
        if not hasattr(self.model, 'coef_'):
            raise ValueError("Loaded model is missing coefficients")
        if not hasattr(self.model, 'intercept_'):
            raise ValueError("Loaded model is missing intercept")
        
        # Validate scaler
        if not hasattr(self.scaler, 'transform'):
            raise ValueError("Loaded scaler is invalid")
        
        # Validate encoder
        if not hasattr(self.encoder, 'transform'):
            raise ValueError("Loaded encoder is invalid")
        
        # Validate feature dimensions
        # Model should have coefficients for all features
        expected_num_features = len(self.model.coef_)
        
        # Encoder should produce correct number of categorical features
        # We have 3 fuel types + 4 vehicle types = 7 categorical features
        try:
            test_categorical = np.array([['Bensin', 'LCGC']])
            encoded = self.encoder.transform(test_categorical)
            num_categorical_features = encoded.shape[1]
            
            # We expect 3 numerical features + 7 categorical features = 10 total
            # But this can vary based on training, so we just check consistency
            if num_categorical_features > expected_num_features:
                raise ValueError(
                    f"Encoder produces {num_categorical_features} features but "
                    f"model expects {expected_num_features} total features"
                )
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            # If test encoding fails, log warning but don't fail
            logger.warning(f"Could not validate encoder dimensions: {e}")
    
    def _load_version_info(self):
        """
        Load version information from model metadata or use default.
        """
        # Try to load version from feature info file
        feature_info_path = 'models/mlr_feature_info.joblib'
        if os.path.exists(feature_info_path):
            try:
                feature_info = joblib.load(feature_info_path)
                self.model_version = feature_info.get('model_version', self.MODEL_VERSION)
            except Exception as e:
                logger.warning(f"Could not load version from feature info: {e}")
                self.model_version = self.MODEL_VERSION
        else:
            self.model_version = self.MODEL_VERSION
    
    def get_model_info(self) -> Dict[str, any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with:
            - version: Model version string
            - loaded_at: Timestamp when model was loaded
            - model_path: Path to model file
            - scaler_path: Path to scaler file
            - encoder_path: Path to encoder file
            - file_timestamps: Modification times of model files
            - is_loaded: Whether model is currently loaded
            
        Raises:
            RuntimeError: If model is not loaded
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Cannot retrieve model info.")
        
        return {
            'version': self.model_version,
            'loaded_at': self.model_loaded_at.isoformat() if self.model_loaded_at else None,
            'model_path': self.model_path,
            'scaler_path': self.scaler_path,
            'encoder_path': self.encoder_path,
            'file_timestamps': self.model_file_timestamps.copy(),
            'is_loaded': self.is_loaded
        }
    
    def check_for_updates(self) -> bool:
        """
        Check if model files have been updated on disk.
        
        Returns:
            True if any model file has been modified since loading
            
        Raises:
            RuntimeError: If model is not loaded
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Cannot check for updates.")
        
        # Check if files still exist
        if not all([
            os.path.exists(self.model_path),
            os.path.exists(self.scaler_path),
            os.path.exists(self.encoder_path)
        ]):
            logger.warning("One or more model files are missing")
            return False
        
        # Check timestamps
        current_timestamps = {
            'model': os.path.getmtime(self.model_path),
            'scaler': os.path.getmtime(self.scaler_path),
            'encoder': os.path.getmtime(self.encoder_path)
        }
        
        # Compare with stored timestamps
        for key in ['model', 'scaler', 'encoder']:
            if current_timestamps[key] != self.model_file_timestamps.get(key):
                logger.info(f"Model file {key} has been updated")
                return True
        
        return False
    
    def reload_model(self, validate: bool = True) -> bool:
        """
        Reload model from disk (hot-swap).
        
        This allows updating the model without restarting the application.
        If validation fails, the old model is kept.
        
        Args:
            validate: Whether to validate new model before replacing old one
            
        Returns:
            True if reload was successful, False otherwise
            
        Raises:
            RuntimeError: If model is not currently loaded
        """
        if not self.is_loaded:
            raise RuntimeError("No model currently loaded. Use constructor to load initial model.")
        
        logger.info("Attempting to reload model...")
        
        # Store old model in case we need to rollback
        old_model = self.model
        old_scaler = self.scaler
        old_encoder = self.encoder
        old_version = self.model_version
        old_timestamps = self.model_file_timestamps.copy()
        
        try:
            # Temporarily mark as not loaded
            self.is_loaded = False
            
            # Try to load new model
            self._load_model()
            
            # If validation is requested, test the new model
            if validate:
                logger.info("Validating new model...")
                
                # Test prediction with sample data
                try:
                    test_emission = self.predict_emission(
                        distance_km=50.0,
                        fuel_type='Bensin',
                        vehicle_type='LCGC',
                        fuel_consumption_kml=18.0,
                        avg_speed_kmh=60.0
                    )
                    
                    # Check that prediction is valid
                    if not np.isfinite(test_emission) or test_emission < 0:
                        raise ValueError(
                            f"New model produced invalid test prediction: {test_emission}"
                        )
                    
                    logger.info(f"Model validation passed. Test prediction: {test_emission:.2f}g")
                    
                except Exception as e:
                    raise ValueError(f"New model failed validation: {str(e)}")
            
            logger.info(
                f"Model reloaded successfully. "
                f"Old version: {old_version}, New version: {self.model_version}"
            )
            
            return True
            
        except Exception as e:
            # Rollback to old model
            logger.error(f"Model reload failed: {str(e)}. Rolling back to previous model.")
            
            self.model = old_model
            self.scaler = old_scaler
            self.encoder = old_encoder
            self.model_version = old_version
            self.model_file_timestamps = old_timestamps
            self.is_loaded = True
            
            return False
    
    def validate_inputs(self, 
                       distance_km: float,
                       fuel_type: str,
                       vehicle_type: str,
                       fuel_consumption_kml: float,
                       avg_speed_kmh: float) -> Tuple[bool, Optional[str]]:
        """
        Validate all input features.
        
        Args:
            distance_km: Route distance in kilometers
            fuel_type: Type of fuel (Bensin, Diesel, Listrik)
            vehicle_type: Type of vehicle (LCGC, SUV, Sedan, EV)
            fuel_consumption_kml: Average fuel consumption in km/L
            avg_speed_kmh: Average speed in km/h
            
        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if all inputs are valid
            - error_message: None if valid, error description if invalid
        """
        # Validate distance
        if not isinstance(distance_km, (int, float)):
            return False, f"Distance must be a number, got {type(distance_km).__name__}"
        if not np.isfinite(distance_km):
            return False, f"Distance must be a finite number, got {distance_km}"
        if distance_km <= 0:
            return False, f"Distance must be positive, got {distance_km}"
        if distance_km > 10000:  # Sanity check
            return False, f"Distance {distance_km} km seems unrealistic (max 10000 km)"
        
        # Validate fuel type
        if not isinstance(fuel_type, str):
            return False, f"Fuel type must be a string, got {type(fuel_type).__name__}"
        if fuel_type not in self.SUPPORTED_FUEL_TYPES:
            return False, (
                f"Unsupported fuel type '{fuel_type}'. "
                f"Valid options: {', '.join(self.SUPPORTED_FUEL_TYPES)}"
            )
        
        # Validate vehicle type
        if not isinstance(vehicle_type, str):
            return False, f"Vehicle type must be a string, got {type(vehicle_type).__name__}"
        if vehicle_type not in self.SUPPORTED_VEHICLE_TYPES:
            return False, (
                f"Unsupported vehicle type '{vehicle_type}'. "
                f"Valid options: {', '.join(self.SUPPORTED_VEHICLE_TYPES)}"
            )
        
        # Validate fuel consumption
        if not isinstance(fuel_consumption_kml, (int, float)):
            return False, f"Fuel consumption must be a number, got {type(fuel_consumption_kml).__name__}"
        if not np.isfinite(fuel_consumption_kml):
            return False, f"Fuel consumption must be a finite number, got {fuel_consumption_kml}"
        if fuel_consumption_kml <= 0:
            return False, f"Fuel consumption must be positive, got {fuel_consumption_kml}"
        if fuel_consumption_kml > 200:  # Sanity check
            return False, f"Fuel consumption {fuel_consumption_kml} km/L seems unrealistic (max 200)"
        
        # Validate average speed
        if not isinstance(avg_speed_kmh, (int, float)):
            return False, f"Average speed must be a number, got {type(avg_speed_kmh).__name__}"
        if not np.isfinite(avg_speed_kmh):
            return False, f"Average speed must be a finite number, got {avg_speed_kmh}"
        if avg_speed_kmh <= 0:
            return False, f"Average speed must be positive, got {avg_speed_kmh}"
        if avg_speed_kmh < 5 or avg_speed_kmh > 200:
            return False, f"Average speed {avg_speed_kmh} km/h is outside realistic bounds (5-200 km/h)"
        
        return True, None
    
    def predict_emission(self,
                        distance_km: float,
                        fuel_type: str,
                        vehicle_type: str,
                        fuel_consumption_kml: float,
                        avg_speed_kmh: float) -> float:
        """
        Predict CO₂ emission in grams using MLR formula.
        
        Formula: Emission = β₀ + β₁(Distance) + β₂(FuelType) + β₃(VehicleType) 
                          + β₄(FuelConsumption) + β₅(AvgSpeed)
        
        Args:
            distance_km: Route distance in kilometers
            fuel_type: Type of fuel (Bensin, Diesel, Listrik)
            vehicle_type: Type of vehicle (LCGC, SUV, Sedan, EV)
            fuel_consumption_kml: Average fuel consumption in km/L
            avg_speed_kmh: Average speed in km/h
            
        Returns:
            Predicted emission in grams of CO₂
            
        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If model is not loaded
        """
        # Check if model is loaded
        if not self.is_loaded:
            raise RuntimeError(
                "Model not loaded. Cannot make predictions. "
                "Please ensure model files exist and are valid."
            )
        
        # Validate inputs
        is_valid, error_msg = self.validate_inputs(
            distance_km, fuel_type, vehicle_type, 
            fuel_consumption_kml, avg_speed_kmh
        )
        
        if not is_valid:
            raise ValueError(f"Invalid input: {error_msg}")
        
        try:
            # Prepare categorical features for encoding
            categorical_data = np.array([[fuel_type, vehicle_type]])
            encoded_categorical = self.encoder.transform(categorical_data)
            
            # Prepare numerical features
            numerical_data = np.array([[distance_km, fuel_consumption_kml, avg_speed_kmh]])
            
            # Combine features (numerical first, then categorical)
            combined_features = np.hstack([numerical_data, encoded_categorical])
            
            # Scale features
            scaled_features = self.scaler.transform(combined_features)
            
            # Make prediction using MLR formula
            prediction = self.model.predict(scaled_features)[0]
            
            # Ensure non-negative prediction
            prediction = max(0.0, prediction)
            
            return float(prediction)
            
        except Exception as e:
            raise RuntimeError(
                f"Prediction failed: {str(e)}. "
                "This may indicate a problem with the model or preprocessing."
            )
    
    def get_model_coefficients(self) -> Dict[str, float]:
        """
        Return model coefficients for transparency.
        
        Returns:
            Dictionary with:
            - intercept: β₀
            - coefficients: Dict mapping feature names to coefficient values
            
        Raises:
            RuntimeError: If model is not loaded
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Cannot retrieve coefficients.")
        
        # Get feature names
        try:
            feature_info_path = 'models/mlr_feature_info.joblib'
            if os.path.exists(feature_info_path):
                feature_info = joblib.load(feature_info_path)
                feature_names = feature_info.get('all_feature_names', [])
            else:
                # Fallback: construct feature names
                numerical_features = ['distance_km', 'fuel_consumption_kml', 'avg_speed_kmh']
                encoded_features = self.encoder.get_feature_names_out(['fuel_type', 'vehicle_type'])
                feature_names = numerical_features + list(encoded_features)
        except Exception:
            # If we can't get feature names, use generic names
            feature_names = [f'feature_{i}' for i in range(len(self.model.coef_))]
        
        coefficients = {
            'intercept': float(self.model.intercept_),
            'coefficients': {
                name: float(coef) 
                for name, coef in zip(feature_names, self.model.coef_)
            }
        }
        
        return coefficients
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Calculate and return feature importance based on coefficient magnitudes.
        
        Feature importance is calculated as the absolute value of each coefficient,
        normalized so that all importances sum to 1.0 (100%).
        
        Returns:
            Dictionary mapping feature names to importance scores (0-1)
            Features are sorted by importance (highest first)
            
        Raises:
            RuntimeError: If model is not loaded
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Cannot calculate feature importance.")
        
        # Get coefficients
        coef_dict = self.get_model_coefficients()
        coefficients = coef_dict['coefficients']
        
        # Calculate absolute values
        abs_coefs = {name: abs(coef) for name, coef in coefficients.items()}
        
        # Calculate total for normalization
        total = sum(abs_coefs.values())
        
        # Normalize to get importance scores (0-1)
        if total > 0:
            importance = {name: abs_coef / total for name, abs_coef in abs_coefs.items()}
        else:
            # If all coefficients are zero, assign equal importance
            importance = {name: 1.0 / len(abs_coefs) for name in abs_coefs.keys()}
        
        # Sort by importance (highest first)
        importance_sorted = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
        
        return importance_sorted
    
    def explain_prediction(self,
                          distance_km: float,
                          fuel_type: str,
                          vehicle_type: str,
                          fuel_consumption_kml: float,
                          avg_speed_kmh: float,
                          prediction: Optional[float] = None) -> Dict[str, any]:
        """
        Generate a detailed explanation of how a prediction was made.
        
        This method provides transparency by showing:
        - The input features used
        - The contribution of each feature to the final prediction
        - The most important factors affecting the prediction
        
        Args:
            distance_km: Route distance in kilometers
            fuel_type: Type of fuel (Bensin, Diesel, Listrik)
            vehicle_type: Type of vehicle (LCGC, SUV, Sedan, EV)
            fuel_consumption_kml: Average fuel consumption in km/L
            avg_speed_kmh: Average speed in km/h
            prediction: Pre-calculated prediction (optional, will calculate if not provided)
            
        Returns:
            Dictionary with:
            - prediction: The predicted emission value
            - inputs: The input features used
            - contributions: How much each feature contributed to the prediction
            - top_factors: The top 3 factors affecting this prediction
            - explanation_text: Human-readable explanation
            
        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If model is not loaded
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Cannot generate explanation.")
        
        # Validate inputs
        is_valid, error_msg = self.validate_inputs(
            distance_km, fuel_type, vehicle_type,
            fuel_consumption_kml, avg_speed_kmh
        )
        
        if not is_valid:
            raise ValueError(f"Invalid input: {error_msg}")
        
        # Calculate prediction if not provided
        if prediction is None:
            prediction = self.predict_emission(
                distance_km, fuel_type, vehicle_type,
                fuel_consumption_kml, avg_speed_kmh
            )
        
        # Get coefficients
        coef_dict = self.get_model_coefficients()
        intercept = coef_dict['intercept']
        coefficients = coef_dict['coefficients']
        
        # Prepare features for encoding (same as in predict_emission)
        categorical_data = np.array([[fuel_type, vehicle_type]])
        encoded_categorical = self.encoder.transform(categorical_data)
        numerical_data = np.array([[distance_km, fuel_consumption_kml, avg_speed_kmh]])
        combined_features = np.hstack([numerical_data, encoded_categorical])
        scaled_features = self.scaler.transform(combined_features)[0]
        
        # Get feature names
        try:
            feature_info_path = 'models/mlr_feature_info.joblib'
            if os.path.exists(feature_info_path):
                feature_info = joblib.load(feature_info_path)
                feature_names = feature_info.get('all_feature_names', [])
            else:
                numerical_features = ['distance_km', 'fuel_consumption_kml', 'avg_speed_kmh']
                encoded_features = self.encoder.get_feature_names_out(['fuel_type', 'vehicle_type'])
                feature_names = numerical_features + list(encoded_features)
        except Exception:
            feature_names = [f'feature_{i}' for i in range(len(scaled_features))]
        
        # Calculate contribution of each feature
        contributions = {}
        for i, name in enumerate(feature_names):
            if name in coefficients:
                contribution = scaled_features[i] * coefficients[name]
                contributions[name] = float(contribution)
        
        # Add intercept contribution
        contributions['intercept'] = float(intercept)
        
        # Find top contributing factors (by absolute value)
        abs_contributions = {k: abs(v) for k, v in contributions.items() if k != 'intercept'}
        top_factors = sorted(abs_contributions.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Generate human-readable explanation
        explanation_parts = [
            f"Predicted CO₂ emission: {prediction:.2f} grams",
            f"\nInput factors:",
            f"  - Distance: {distance_km:.2f} km",
            f"  - Vehicle type: {vehicle_type}",
            f"  - Fuel type: {fuel_type}",
            f"  - Fuel consumption: {fuel_consumption_kml:.2f} km/L",
            f"  - Average speed: {avg_speed_kmh:.2f} km/h",
            f"\nTop factors affecting this prediction:"
        ]
        
        for i, (factor_name, contribution) in enumerate(top_factors, 1):
            # Make factor names more readable
            readable_name = factor_name.replace('_', ' ').title()
            explanation_parts.append(
                f"  {i}. {readable_name}: {contribution:.2f}g contribution"
            )
        
        explanation_text = '\n'.join(explanation_parts)
        
        return {
            'prediction': float(prediction),
            'inputs': {
                'distance_km': distance_km,
                'fuel_type': fuel_type,
                'vehicle_type': vehicle_type,
                'fuel_consumption_kml': fuel_consumption_kml,
                'avg_speed_kmh': avg_speed_kmh
            },
            'contributions': contributions,
            'top_factors': [
                {'feature': name, 'contribution': float(contrib)}
                for name, contrib in top_factors
            ],
            'explanation_text': explanation_text
        }


class FeatureExtractor:
    """
    Extract and prepare features from route and vehicle data.
    """
    
    # Fuel consumption lookup table (km/L or km/kWh for EV)
    FUEL_CONSUMPTION_TABLE = {
        'LCGC': {
            'Bensin': 18.0,
            'Diesel': 20.0
        },
        'SUV': {
            'Bensin': 10.0,
            'Diesel': 12.0
        },
        'Sedan': {
            'Bensin': 14.0,
            'Diesel': 16.0
        },
        'EV': {
            'Listrik': 100.0  # km per kWh equivalent
        }
    }
    
    # Default fuel consumption if not found
    DEFAULT_FUEL_CONSUMPTION = 12.0
    
    def get_fuel_consumption(self, vehicle_type: str, fuel_type: str) -> float:
        """
        Get fuel consumption from lookup table.
        
        Args:
            vehicle_type: Vehicle type
            fuel_type: Fuel type
            
        Returns:
            Fuel consumption in km/L (or km/kWh for EV)
        """
        if vehicle_type in self.FUEL_CONSUMPTION_TABLE:
            if fuel_type in self.FUEL_CONSUMPTION_TABLE[vehicle_type]:
                return self.FUEL_CONSUMPTION_TABLE[vehicle_type][fuel_type]
        
        # Return default if combination not found
        return self.DEFAULT_FUEL_CONSUMPTION
    
    def calculate_avg_speed(self, distance_km: float, duration_min: float) -> float:
        """
        Calculate average speed from distance and duration.
        
        Args:
            distance_km: Distance in kilometers
            duration_min: Duration in minutes
            
        Returns:
            Average speed in km/h
        """
        if duration_min <= 0:
            raise ValueError("Duration must be positive")
        
        duration_hours = duration_min / 60.0
        avg_speed = distance_km / duration_hours
        
        return avg_speed
    
    def extract_features(self, 
                        route_data: Dict,
                        vehicle_type: str,
                        fuel_type: str) -> Dict:
        """
        Extract all required features from route and vehicle data.
        
        Args:
            route_data: Dict with 'distance_km' or 'distance_m', 'duration_min', etc.
            vehicle_type: Vehicle type
            fuel_type: Fuel type
            
        Returns:
            Dict with all features ready for prediction:
            - distance_km
            - fuel_type
            - vehicle_type
            - fuel_consumption_kml
            - avg_speed_kmh
        """
        # Extract distance (convert from meters if needed)
        if 'distance_km' in route_data:
            distance_km = route_data['distance_km']
        elif 'distance_m' in route_data:
            distance_km = route_data['distance_m'] / 1000.0
        elif 'distance' in route_data:
            # Assume meters if unit not specified
            distance_km = route_data['distance'] / 1000.0
        else:
            raise ValueError("Route data must contain 'distance_km', 'distance_m', or 'distance'")
        
        # Extract or calculate average speed
        if 'avg_speed_kmh' in route_data:
            avg_speed_kmh = route_data['avg_speed_kmh']
        elif 'duration_min' in route_data:
            avg_speed_kmh = self.calculate_avg_speed(distance_km, route_data['duration_min'])
        elif 'duration' in route_data:
            # Assume minutes if unit not specified
            avg_speed_kmh = self.calculate_avg_speed(distance_km, route_data['duration'])
        else:
            # Use default estimate based on route type
            avg_speed_kmh = 50.0  # Default urban speed
        
        # Get fuel consumption
        fuel_consumption_kml = self.get_fuel_consumption(vehicle_type, fuel_type)
        
        return {
            'distance_km': distance_km,
            'fuel_type': fuel_type,
            'vehicle_type': vehicle_type,
            'fuel_consumption_kml': fuel_consumption_kml,
            'avg_speed_kmh': avg_speed_kmh
        }
