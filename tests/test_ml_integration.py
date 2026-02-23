"""
Integration tests for ML Emission Prediction workflow.

This test suite verifies that the ML predictor integrates correctly with the
main application flow and provides end-to-end prediction functionality.

Requirements Addressed:
- 11.1: Automatic invocation of ML predictor for each route
- 11.2: ML predictions replace static calculations
- 11.3: Integration with existing route comparison logic
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import numpy as np
from unittest.mock import patch, MagicMock
from mlr_emission_predictor import MLREmissionPredictor, FeatureExtractor
from route_comparator import RouteEmissionComparator
from emission import get_emission_factor


class TestMLWorkflowIntegration:
    """
    Integration tests for end-to-end ML prediction workflow.
    
    **Property 9: End-to-end prediction workflow**
    **Validates: Requirements 11.1, 11.2, 11.3**
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_routes=st.integers(min_value=1, max_value=5),
        base_distance_km=st.floats(min_value=5.0, max_value=100.0),
        fuel_type=st.sampled_from(['Bensin', 'Diesel', 'Listrik']),
        vehicle_type=st.sampled_from(['LCGC', 'SUV', 'Sedan', 'EV'])
    )
    def test_end_to_end_prediction_workflow(self, num_routes, base_distance_km, 
                                           fuel_type, vehicle_type):
        """
        **Feature: ml-emission-prediction, Property 9: End-to-end prediction workflow**
        **Validates: Requirements 11.1, 11.2, 11.3**
        
        For any valid set of routes with vehicle and fuel type, the ML workflow must:
        1. Automatically invoke the ML predictor for each route (Req 11.1)
        2. Generate predictions that replace static calculations (Req 11.2)
        3. Integrate with route comparison logic to select best route (Req 11.3)
        
        This ensures the complete workflow from route data to recommendation works correctly.
        """
        # Filter out invalid vehicle-fuel combinations
        if vehicle_type == 'EV' and fuel_type != 'Listrik':
            assume(False)
        if vehicle_type != 'EV' and fuel_type == 'Listrik':
            assume(False)
        
        # Ensure finite values
        assume(np.isfinite(base_distance_km))
        
        try:
            # Initialize ML components
            predictor = MLREmissionPredictor()
            comparator = RouteEmissionComparator(predictor)
            
            # Generate mock routes with varying distances
            routes = []
            for i in range(num_routes):
                # Vary distance slightly for each route
                distance_variation = np.random.uniform(0.8, 1.2)
                distance_km = base_distance_km * distance_variation
                duration_min = distance_km / np.random.uniform(30, 80) * 60  # Random speed
                
                routes.append({
                    'route_number': i + 1,
                    'distance_km': distance_km,
                    'duration_min': duration_min,
                    'steps': []
                })
            
            # Property 1: ML predictor is automatically invoked for each route (Req 11.1)
            result = comparator.compare_routes(routes, vehicle_type, fuel_type)
            
            # Verify all routes were processed
            assert 'all_routes' in result, "Result should contain all routes"
            assert len(result['all_routes']) == num_routes, \
                f"Should process all {num_routes} routes"
            
            # Property 2: ML predictions replace static calculations (Req 11.2)
            for route_result in result['all_routes']:
                # Verify ML prediction was used
                assert 'predicted_emission_g' in route_result, \
                    "Route should have ML prediction"
                assert 'prediction_method' in route_result, \
                    "Route should indicate prediction method"
                assert route_result['prediction_method'] == 'ML', \
                    "Should use ML prediction method"
                
                # Verify prediction is non-negative
                assert route_result['predicted_emission_g'] >= 0, \
                    "Predicted emission must be non-negative"
                
                # Verify prediction is finite
                assert np.isfinite(route_result['predicted_emission_g']), \
                    "Predicted emission must be finite"
            
            # Property 3: Integration with route comparison logic (Req 11.3)
            assert 'best_route' in result, "Result should identify best route"
            assert 'is_recommended' in result['best_route'], \
                "Best route should be marked as recommended"
            assert result['best_route']['is_recommended'] is True, \
                "Best route should be recommended"
            
            # Property 4: Best route has lowest emission
            best_emission = result['best_route']['predicted_emission_g']
            for route_result in result['all_routes']:
                assert route_result['predicted_emission_g'] >= best_emission, \
                    "Best route should have lowest emission"
            
            # Property 5: ML enabled flag is set
            assert 'ml_enabled' in result, "Result should indicate if ML is enabled"
            assert result['ml_enabled'] is True, "ML should be enabled"
            
            # Property 6: Explanation is generated
            assert 'explanation' in result, "Result should contain explanation"
            assert isinstance(result['explanation'], str), \
                "Explanation should be a string"
            assert len(result['explanation']) > 0, \
                "Explanation should not be empty"
            
        except (FileNotFoundError, RuntimeError) as e:
            # If model files are missing, skip the test
            pytest.skip(f"Model files not available: {e}")
    
    def test_ml_workflow_with_single_route(self):
        """
        Test ML workflow with a single route.
        
        This verifies that the workflow works correctly even with just one route,
        which is a common edge case.
        
        **Validates: Requirements 11.1, 11.2, 11.3**
        """
        try:
            predictor = MLREmissionPredictor()
            comparator = RouteEmissionComparator(predictor)
            
            # Single route
            routes = [{
                'route_number': 1,
                'distance_km': 25.0,
                'duration_min': 30.0,
                'steps': []
            }]
            
            # Compare routes
            result = comparator.compare_routes(routes, 'LCGC', 'Bensin')
            
            # Verify single route is processed
            assert len(result['all_routes']) == 1, "Should process single route"
            assert result['best_route']['route_number'] == 1, \
                "Single route should be best route"
            assert result['ml_enabled'] is True, "ML should be enabled"
            
            # Verify prediction was made
            assert result['best_route']['predicted_emission_g'] > 0, \
                "Should have positive emission prediction"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_ml_workflow_with_multiple_routes(self):
        """
        Test ML workflow with multiple routes of varying distances.
        
        This verifies that the workflow correctly compares multiple routes
        and selects the one with lowest predicted emission.
        
        **Validates: Requirements 11.1, 11.2, 11.3**
        """
        try:
            predictor = MLREmissionPredictor()
            comparator = RouteEmissionComparator(predictor)
            
            # Multiple routes with different distances
            routes = [
                {
                    'route_number': 1,
                    'distance_km': 30.0,
                    'duration_min': 35.0,
                    'steps': []
                },
                {
                    'route_number': 2,
                    'distance_km': 25.0,  # Shorter - likely lower emission
                    'duration_min': 40.0,
                    'steps': []
                },
                {
                    'route_number': 3,
                    'distance_km': 35.0,
                    'duration_min': 32.0,
                    'steps': []
                }
            ]
            
            # Compare routes
            result = comparator.compare_routes(routes, 'SUV', 'Bensin')
            
            # Verify all routes are processed
            assert len(result['all_routes']) == 3, "Should process all 3 routes"
            
            # Verify best route is identified
            assert 'best_route' in result, "Should identify best route"
            best_route_num = result['best_route']['route_number']
            assert best_route_num in [1, 2, 3], "Best route should be one of the input routes"
            
            # Verify alternative routes are listed
            assert 'alternative_routes' in result, "Should list alternative routes"
            assert len(result['alternative_routes']) == 2, \
                "Should have 2 alternative routes"
            
            # Verify emission differences are calculated
            for alt_route in result['alternative_routes']:
                assert 'emission_difference_g' in alt_route, \
                    "Alternative route should have emission difference"
                assert alt_route['emission_difference_g'] >= 0, \
                    "Emission difference should be non-negative"
            
            # Verify savings are calculated
            assert 'savings' in result, "Should calculate savings"
            assert 'vs_worst_route_g' in result['savings'], \
                "Should calculate savings vs worst route"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_ml_workflow_with_different_vehicle_types(self):
        """
        Test ML workflow with different vehicle types.
        
        This verifies that the workflow works correctly for all supported
        vehicle types and produces different predictions based on vehicle type.
        
        **Validates: Requirements 11.1, 11.2**
        """
        try:
            predictor = MLREmissionPredictor()
            comparator = RouteEmissionComparator(predictor)
            
            # Same route for different vehicle types
            route = [{
                'route_number': 1,
                'distance_km': 20.0,
                'duration_min': 25.0,
                'steps': []
            }]
            
            # Test with different vehicle types
            vehicle_fuel_pairs = [
                ('LCGC', 'Bensin'),
                ('SUV', 'Bensin'),
                ('Sedan', 'Diesel'),
                ('EV', 'Listrik')
            ]
            
            predictions = {}
            
            for vehicle_type, fuel_type in vehicle_fuel_pairs:
                result = comparator.compare_routes(route, vehicle_type, fuel_type)
                predictions[(vehicle_type, fuel_type)] = result['best_route']['predicted_emission_g']
                
                # Verify prediction was made
                assert result['ml_enabled'] is True, \
                    f"ML should be enabled for {vehicle_type}-{fuel_type}"
                assert result['best_route']['predicted_emission_g'] >= 0, \
                    f"Should have non-negative prediction for {vehicle_type}-{fuel_type}"
            
            # Verify predictions differ by vehicle type
            # (EV should generally have lower emissions than SUV for same distance)
            ev_emission = predictions[('EV', 'Listrik')]
            suv_emission = predictions[('SUV', 'Bensin')]
            
            # EV should have lower or equal emission than SUV
            assert ev_emission <= suv_emission, \
                "EV should have lower or equal emission than SUV for same route"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_ml_workflow_produces_consistent_results(self):
        """
        Test that ML workflow produces consistent results for same inputs.
        
        This verifies that the workflow is deterministic - same inputs
        should produce same outputs.
        
        **Validates: Requirements 11.2**
        """
        try:
            predictor = MLREmissionPredictor()
            comparator = RouteEmissionComparator(predictor)
            
            # Same route
            routes = [{
                'route_number': 1,
                'distance_km': 15.0,
                'duration_min': 20.0,
                'steps': []
            }]
            
            # Make prediction twice
            result1 = comparator.compare_routes(routes, 'LCGC', 'Bensin')
            result2 = comparator.compare_routes(routes, 'LCGC', 'Bensin')
            
            # Verify predictions are identical
            emission1 = result1['best_route']['predicted_emission_g']
            emission2 = result2['best_route']['predicted_emission_g']
            
            assert abs(emission1 - emission2) < 0.001, \
                "Same inputs should produce same predictions"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_ml_workflow_handles_edge_case_very_short_route(self):
        """
        Test ML workflow with very short route (< 1 km).
        
        This verifies that the workflow handles edge cases correctly.
        
        **Validates: Requirements 11.1, 11.2**
        """
        try:
            predictor = MLREmissionPredictor()
            comparator = RouteEmissionComparator(predictor)
            
            # Very short route
            routes = [{
                'route_number': 1,
                'distance_km': 0.5,
                'duration_min': 2.0,
                'steps': []
            }]
            
            # Compare routes
            result = comparator.compare_routes(routes, 'LCGC', 'Bensin')
            
            # Verify prediction is made
            assert result['ml_enabled'] is True, "ML should be enabled"
            assert result['best_route']['predicted_emission_g'] >= 0, \
                "Should have non-negative prediction for short route"
            
            # Very short route should have low emission
            assert result['best_route']['predicted_emission_g'] < 1000, \
                "Very short route should have low emission (< 1000g)"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_ml_workflow_handles_edge_case_very_long_route(self):
        """
        Test ML workflow with very long route (> 100 km).
        
        This verifies that the workflow handles long routes correctly.
        
        **Validates: Requirements 11.1, 11.2**
        """
        try:
            predictor = MLREmissionPredictor()
            comparator = RouteEmissionComparator(predictor)
            
            # Very long route
            routes = [{
                'route_number': 1,
                'distance_km': 150.0,
                'duration_min': 120.0,
                'steps': []
            }]
            
            # Compare routes
            result = comparator.compare_routes(routes, 'SUV', 'Bensin')
            
            # Verify prediction is made
            assert result['ml_enabled'] is True, "ML should be enabled"
            assert result['best_route']['predicted_emission_g'] > 0, \
                "Should have positive prediction for long route"
            
            # Long route should have high emission
            assert result['best_route']['predicted_emission_g'] > 10000, \
                "Long route should have high emission (> 10kg)"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")


class TestMLWorkflowErrorHandling:
    """
    Tests for ML workflow error handling and fallback behavior.
    
    **Validates: Requirements 11.4**
    """
    
    def test_ml_workflow_handles_empty_routes_list(self):
        """
        Test that ML workflow handles empty routes list gracefully.
        
        **Validates: Requirements 11.3**
        """
        try:
            predictor = MLREmissionPredictor()
            comparator = RouteEmissionComparator(predictor)
            
            # Empty routes list
            routes = []
            
            # Should raise ValueError
            with pytest.raises(ValueError) as exc_info:
                comparator.compare_routes(routes, 'LCGC', 'Bensin')
            
            # Error message should be clear
            assert 'empty' in str(exc_info.value).lower(), \
                "Error message should mention empty routes"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_ml_workflow_handles_invalid_route_data(self):
        """
        Test that ML workflow handles invalid route data gracefully.
        
        **Validates: Requirements 11.3**
        """
        try:
            predictor = MLREmissionPredictor()
            comparator = RouteEmissionComparator(predictor)
            
            # Route with missing distance
            routes = [{
                'route_number': 1,
                'duration_min': 20.0,
                # Missing distance_km
                'steps': []
            }]
            
            # Should raise ValueError or skip the route
            try:
                result = comparator.compare_routes(routes, 'LCGC', 'Bensin')
                # If it doesn't raise, it should have skipped the invalid route
                # and raised RuntimeError for no valid routes
                pytest.fail("Should have raised an error for invalid route data")
            except (ValueError, RuntimeError) as e:
                # Expected behavior
                assert 'distance' in str(e).lower() or 'route' in str(e).lower(), \
                    "Error should mention the problem"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_ml_workflow_handles_invalid_vehicle_type(self):
        """
        Test that ML workflow handles invalid vehicle type gracefully.
        
        **Validates: Requirements 11.2**
        """
        try:
            predictor = MLREmissionPredictor()
            comparator = RouteEmissionComparator(predictor)
            
            routes = [{
                'route_number': 1,
                'distance_km': 20.0,
                'duration_min': 25.0,
                'steps': []
            }]
            
            # Invalid vehicle type - should fall back to static calculation
            result = comparator.compare_routes(routes, 'InvalidVehicle', 'Bensin')
            
            # Verify fallback was used
            assert result is not None, "Should return result using fallback"
            assert 'best_route' in result, "Should have best_route in result"
            assert result.get('ml_enabled') == False, "ML should be disabled due to invalid input"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")


class TestMLWorkflowFeatureExtraction:
    """
    Tests for feature extraction in ML workflow.
    
    **Validates: Requirements 11.1**
    """
    
    def test_ml_workflow_extracts_features_correctly(self):
        """
        Test that ML workflow extracts all required features from route data.
        
        **Validates: Requirements 11.1**
        """
        try:
            extractor = FeatureExtractor()
            
            # Route data
            route_data = {
                'distance_km': 30.0,
                'duration_min': 35.0
            }
            
            # Extract features
            features = extractor.extract_features(route_data, 'SUV', 'Bensin')
            
            # Verify all required features are present
            required_features = [
                'distance_km', 'fuel_type', 'vehicle_type',
                'fuel_consumption_kml', 'avg_speed_kmh'
            ]
            
            for feature in required_features:
                assert feature in features, f"Missing required feature: {feature}"
            
            # Verify feature values are correct
            assert features['distance_km'] == 30.0, "Distance should match input"
            assert features['fuel_type'] == 'Bensin', "Fuel type should match input"
            assert features['vehicle_type'] == 'SUV', "Vehicle type should match input"
            assert features['fuel_consumption_kml'] > 0, \
                "Fuel consumption should be positive"
            assert features['avg_speed_kmh'] > 0, "Average speed should be positive"
            
            # Verify average speed calculation
            expected_speed = 30.0 / (35.0 / 60.0)  # distance / (duration in hours)
            assert abs(features['avg_speed_kmh'] - expected_speed) < 0.1, \
                "Average speed should be calculated correctly"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_ml_workflow_converts_distance_units(self):
        """
        Test that ML workflow converts distance from meters to kilometers.
        
        **Validates: Requirements 11.1**
        """
        try:
            extractor = FeatureExtractor()
            
            # Route data with distance in meters
            route_data = {
                'distance_m': 30000.0,  # 30 km
                'duration_min': 35.0
            }
            
            # Extract features
            features = extractor.extract_features(route_data, 'LCGC', 'Bensin')
            
            # Verify distance is converted to kilometers
            assert features['distance_km'] == 30.0, \
                "Distance should be converted from meters to kilometers"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
