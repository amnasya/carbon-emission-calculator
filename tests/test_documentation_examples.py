#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Documentation Validation Tests
Verify that all code examples in documentation work correctly
**Validates: Requirements 13.5**
"""

import pytest
import os
import sys
from mlr_emission_predictor import MLREmissionPredictor, FeatureExtractor
from route_comparator import RouteEmissionComparator


class TestDocumentationExamples:
    """Test that all code examples from the documentation work correctly."""
    
    @pytest.fixture
    def predictor(self):
        """Create predictor instance for tests."""
        # Ensure model files exist
        if not os.path.exists('mlr_emission_model.joblib'):
            pytest.skip("Model files not found. Run train_mlr_model.py first.")
        return MLREmissionPredictor()
    
    @pytest.fixture
    def feature_extractor(self):
        """Create feature extractor instance for tests."""
        return FeatureExtractor()
    
    def test_example_1_basic_prediction(self, predictor):
        """
        Test Example 1: Basic Prediction from documentation.
        Verifies that basic prediction works as documented.
        """
        # Example from documentation
        emission = predictor.predict_emission(
            distance_km=50.0,
            fuel_type='Bensin',
            vehicle_type='LCGC',
            fuel_consumption_kml=18.0,
            avg_speed_kmh=60.0
        )
        
        # Verify prediction is a valid number
        assert isinstance(emission, float)
        assert emission > 0
        assert emission < 100000  # Reasonable upper bound
        
        # Verify prediction is in expected range for 50km LCGC trip
        # LCGC Bensin typically ~120 g/km, so 50km should be ~6000g
        assert 3000 < emission < 10000
    
    def test_example_2_route_comparison(self, predictor):
        """
        Test Example 2: Route Comparison from documentation.
        Verifies that route comparison works as documented.
        """
        comparator = RouteEmissionComparator(predictor)
        
        routes = [
            {'route_number': 1, 'distance_km': 50.0, 'duration_min': 45},
            {'route_number': 2, 'distance_km': 55.0, 'duration_min': 40},
            {'route_number': 3, 'distance_km': 48.0, 'duration_min': 50}
        ]
        
        result = comparator.compare_routes(routes, 'LCGC', 'Bensin')
        
        # Verify result structure matches documentation
        assert 'best_route' in result
        assert 'alternative_routes' in result
        assert 'savings' in result
        assert 'explanation' in result
        assert 'ml_enabled' in result
        assert 'fallback_used' in result
        
        # Verify best route has required fields
        best_route = result['best_route']
        assert 'route_number' in best_route
        assert 'distance_km' in best_route
        assert 'duration_min' in best_route
        assert 'predicted_emission_g' in best_route
        assert 'predicted_emission_kg' in best_route
        assert 'is_recommended' in best_route
        assert best_route['is_recommended'] is True
        
        # Verify alternative routes structure
        assert len(result['alternative_routes']) == 2
        for alt_route in result['alternative_routes']:
            assert 'route_number' in alt_route
            assert 'predicted_emission_g' in alt_route
            assert 'emission_difference_g' in alt_route
            assert 'emission_difference_pct' in alt_route
        
        # Verify savings structure
        savings = result['savings']
        assert 'vs_worst_route_g' in savings
        assert 'vs_worst_route_pct' in savings
        assert savings['vs_worst_route_g'] >= 0
    
    def test_example_3_feature_extraction(self, feature_extractor):
        """
        Test Example 3: Feature Extraction from documentation.
        Verifies that feature extraction works as documented.
        """
        route_data = {
            'distance_m': 50000,  # 50 km in meters
            'duration_min': 45
        }
        
        features = feature_extractor.extract_features(route_data, 'LCGC', 'Bensin')
        
        # Verify output structure matches documentation
        assert 'distance_km' in features
        assert 'fuel_type' in features
        assert 'vehicle_type' in features
        assert 'fuel_consumption_kml' in features
        assert 'avg_speed_kmh' in features
        
        # Verify values
        assert features['distance_km'] == 50.0
        assert features['fuel_type'] == 'Bensin'
        assert features['vehicle_type'] == 'LCGC'
        assert features['fuel_consumption_kml'] == 18.0
        assert 60.0 < features['avg_speed_kmh'] < 70.0  # ~66.67 km/h
    
    def test_example_4_model_coefficients(self, predictor):
        """
        Test Example 4: Model Coefficients from documentation.
        Verifies that coefficient retrieval works as documented.
        """
        coefficients = predictor.get_model_coefficients()
        
        # Verify output structure matches documentation
        assert 'intercept' in coefficients
        assert 'coefficients' in coefficients
        
        # Verify intercept is a number
        assert isinstance(coefficients['intercept'], float)
        
        # Verify coefficients dict contains expected features
        coef_dict = coefficients['coefficients']
        assert isinstance(coef_dict, dict)
        
        # Should have numerical features
        assert any('distance' in key.lower() for key in coef_dict.keys())
        assert any('consumption' in key.lower() for key in coef_dict.keys())
        assert any('speed' in key.lower() for key in coef_dict.keys())
        
        # Should have categorical features (encoded)
        assert any('fuel_type' in key.lower() for key in coef_dict.keys())
        assert any('vehicle_type' in key.lower() for key in coef_dict.keys())
    
    def test_example_5_prediction_explanation(self, predictor):
        """
        Test Example 5: Prediction Explanation from documentation.
        Verifies that prediction explanation works as documented.
        """
        explanation = predictor.explain_prediction(
            distance_km=50.0,
            fuel_type='Bensin',
            vehicle_type='SUV',
            fuel_consumption_kml=10.0,
            avg_speed_kmh=80.0
        )
        
        # Verify output structure matches documentation
        assert 'prediction' in explanation
        assert 'inputs' in explanation
        assert 'contributions' in explanation
        assert 'top_factors' in explanation
        assert 'explanation_text' in explanation
        
        # Verify prediction is valid
        assert isinstance(explanation['prediction'], float)
        assert explanation['prediction'] > 0
        
        # Verify inputs match what was provided
        inputs = explanation['inputs']
        assert inputs['distance_km'] == 50.0
        assert inputs['fuel_type'] == 'Bensin'
        assert inputs['vehicle_type'] == 'SUV'
        assert inputs['fuel_consumption_kml'] == 10.0
        assert inputs['avg_speed_kmh'] == 80.0
        
        # Verify contributions structure
        contributions = explanation['contributions']
        assert 'intercept' in contributions
        assert isinstance(contributions, dict)
        
        # Verify top factors structure
        top_factors = explanation['top_factors']
        assert isinstance(top_factors, list)
        assert len(top_factors) <= 3
        for factor in top_factors:
            assert 'feature' in factor
            assert 'contribution' in factor
        
        # Verify explanation text is a string
        assert isinstance(explanation['explanation_text'], str)
        assert len(explanation['explanation_text']) > 0
    
    def test_example_6_error_handling(self, predictor):
        """
        Test Example 6: Error Handling from documentation.
        Verifies that error handling works as documented.
        """
        # Test with invalid distance (negative)
        with pytest.raises(ValueError) as exc_info:
            predictor.predict_emission(
                distance_km=-10.0,
                fuel_type='Bensin',
                vehicle_type='LCGC',
                fuel_consumption_kml=18.0,
                avg_speed_kmh=60.0
            )
        
        # Verify error message is informative
        error_msg = str(exc_info.value)
        assert 'distance' in error_msg.lower()
        assert 'positive' in error_msg.lower()
    
    def test_supported_fuel_types(self, predictor):
        """
        Test that all documented fuel types are supported.
        """
        supported_types = ['Bensin', 'Diesel', 'Listrik']
        
        for fuel_type in supported_types:
            # Should not raise an error
            is_valid, error = predictor.validate_inputs(
                distance_km=50.0,
                fuel_type=fuel_type,
                vehicle_type='LCGC' if fuel_type != 'Listrik' else 'EV',
                fuel_consumption_kml=15.0,
                avg_speed_kmh=60.0
            )
            assert is_valid, f"Fuel type {fuel_type} should be valid but got error: {error}"
    
    def test_supported_vehicle_types(self, predictor):
        """
        Test that all documented vehicle types are supported.
        """
        supported_types = ['LCGC', 'SUV', 'Sedan', 'EV']
        
        for vehicle_type in supported_types:
            # Should not raise an error
            fuel_type = 'Listrik' if vehicle_type == 'EV' else 'Bensin'
            is_valid, error = predictor.validate_inputs(
                distance_km=50.0,
                fuel_type=fuel_type,
                vehicle_type=vehicle_type,
                fuel_consumption_kml=15.0,
                avg_speed_kmh=60.0
            )
            assert is_valid, f"Vehicle type {vehicle_type} should be valid but got error: {error}"
    
    def test_fuel_consumption_lookup_table(self, feature_extractor):
        """
        Test that fuel consumption lookup table matches documentation.
        """
        # Test documented values
        assert feature_extractor.get_fuel_consumption('LCGC', 'Bensin') == 18.0
        assert feature_extractor.get_fuel_consumption('LCGC', 'Diesel') == 20.0
        assert feature_extractor.get_fuel_consumption('SUV', 'Bensin') == 10.0
        assert feature_extractor.get_fuel_consumption('SUV', 'Diesel') == 12.0
        assert feature_extractor.get_fuel_consumption('Sedan', 'Bensin') == 14.0
        assert feature_extractor.get_fuel_consumption('Sedan', 'Diesel') == 16.0
        assert feature_extractor.get_fuel_consumption('EV', 'Listrik') == 100.0
    
    def test_validation_bounds(self, predictor):
        """
        Test that validation bounds match documentation.
        """
        # Test valid distance (should pass)
        is_valid, error = predictor.validate_inputs(
            distance_km=50.0,
            fuel_type='Bensin',
            vehicle_type='LCGC',
            fuel_consumption_kml=15.0,
            avg_speed_kmh=60.0
        )
        assert is_valid, f"Valid inputs should pass but got error: {error}"
        
        # Test zero distance (should fail)
        is_valid, error = predictor.validate_inputs(
            distance_km=0.0,
            fuel_type='Bensin',
            vehicle_type='LCGC',
            fuel_consumption_kml=15.0,
            avg_speed_kmh=60.0
        )
        assert not is_valid, "Zero distance should be invalid"
        
        # Test negative distance (should fail)
        is_valid, error = predictor.validate_inputs(
            distance_km=-10.0,
            fuel_type='Bensin',
            vehicle_type='LCGC',
            fuel_consumption_kml=15.0,
            avg_speed_kmh=60.0
        )
        assert not is_valid, "Negative distance should be invalid"
        
        # Test very high distance (should fail)
        is_valid, error = predictor.validate_inputs(
            distance_km=15000.0,  # Above maximum
            fuel_type='Bensin',
            vehicle_type='LCGC',
            fuel_consumption_kml=15.0,
            avg_speed_kmh=60.0
        )
        assert not is_valid, "Distance above 10000 km should be invalid"
        
        # Test minimum speed boundary
        is_valid, error = predictor.validate_inputs(
            distance_km=50.0,
            fuel_type='Bensin',
            vehicle_type='LCGC',
            fuel_consumption_kml=15.0,
            avg_speed_kmh=3.0  # Below minimum
        )
        assert not is_valid, "Speed below 5 km/h should be invalid"
        
        # Test maximum speed boundary
        is_valid, error = predictor.validate_inputs(
            distance_km=50.0,
            fuel_type='Bensin',
            vehicle_type='LCGC',
            fuel_consumption_kml=15.0,
            avg_speed_kmh=250.0  # Above maximum
        )
        assert not is_valid, "Speed above 200 km/h should be invalid"
    
    def test_model_info_api(self, predictor):
        """
        Test that get_model_info() returns documented structure.
        """
        model_info = predictor.get_model_info()
        
        # Verify structure matches documentation
        assert 'version' in model_info
        assert 'loaded_at' in model_info
        assert 'model_path' in model_info
        assert 'scaler_path' in model_info
        assert 'encoder_path' in model_info
        assert 'file_timestamps' in model_info
        assert 'is_loaded' in model_info
        
        # Verify types
        assert isinstance(model_info['version'], str)
        assert isinstance(model_info['is_loaded'], bool)
        assert model_info['is_loaded'] is True
    
    def test_feature_importance_api(self, predictor):
        """
        Test that get_feature_importance() returns documented structure.
        """
        importance = predictor.get_feature_importance()
        
        # Verify it's a dictionary
        assert isinstance(importance, dict)
        
        # Verify all values are between 0 and 1
        for feature, score in importance.items():
            assert 0 <= score <= 1
        
        # Verify scores sum to approximately 1.0
        total = sum(importance.values())
        assert 0.99 <= total <= 1.01
    
    def test_speed_calculation(self, feature_extractor):
        """
        Test that speed calculation matches documentation formula.
        """
        # Test: 50 km in 45 minutes should be ~66.67 km/h
        speed = feature_extractor.calculate_avg_speed(50.0, 45.0)
        expected = 50.0 / (45.0 / 60.0)  # distance / (duration_min / 60)
        assert abs(speed - expected) < 0.01
        
        # Test: 100 km in 60 minutes should be 100 km/h
        speed = feature_extractor.calculate_avg_speed(100.0, 60.0)
        assert abs(speed - 100.0) < 0.01
    
    def test_distance_unit_conversion(self, feature_extractor):
        """
        Test that distance conversion from meters to km works correctly.
        """
        # Test with distance in meters
        route_data = {'distance_m': 50000, 'duration_min': 45}
        features = feature_extractor.extract_features(route_data, 'LCGC', 'Bensin')
        assert features['distance_km'] == 50.0
        
        # Test with distance already in km
        route_data = {'distance_km': 50.0, 'duration_min': 45}
        features = feature_extractor.extract_features(route_data, 'LCGC', 'Bensin')
        assert features['distance_km'] == 50.0
        
        # Test with generic 'distance' field (assumes meters)
        route_data = {'distance': 50000, 'duration_min': 45}
        features = feature_extractor.extract_features(route_data, 'LCGC', 'Bensin')
        assert features['distance_km'] == 50.0


class TestDocumentationAccuracy:
    """Test that documentation claims are accurate."""
    
    def test_model_file_sizes(self):
        """
        Test that model files are approximately the sizes mentioned in documentation.
        Documentation mentions files are ~5 MB total.
        """
        if not os.path.exists('mlr_emission_model.joblib'):
            pytest.skip("Model files not found")
        
        total_size = 0
        files = [
            'mlr_emission_model.joblib',
            'mlr_emission_scaler.joblib',
            'mlr_emission_encoder.joblib',
            'mlr_feature_info.joblib'
        ]
        
        for filename in files:
            if os.path.exists(filename):
                size = os.path.getsize(filename)
                total_size += size
        
        # Total should be less than 10 MB (documentation says ~5 MB)
        assert total_size < 10 * 1024 * 1024
    
    def test_prediction_performance(self):
        """
        Test that predictions are fast (documentation mentions < 100ms).
        """
        if not os.path.exists('mlr_emission_model.joblib'):
            pytest.skip("Model files not found")
        
        import time
        
        predictor = MLREmissionPredictor()
        
        # Warm up
        predictor.predict_emission(50.0, 'Bensin', 'LCGC', 18.0, 60.0)
        
        # Time 10 predictions
        start = time.time()
        for _ in range(10):
            predictor.predict_emission(50.0, 'Bensin', 'LCGC', 18.0, 60.0)
        end = time.time()
        
        avg_time = (end - start) / 10
        
        # Should be much faster than 100ms (typically < 1ms)
        assert avg_time < 0.1  # 100ms


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
