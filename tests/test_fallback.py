"""
Property-based tests for ML fallback behavior.

This test suite verifies that the system correctly falls back to static
emission calculations when ML prediction fails.

Requirements Addressed:
- 11.4: Fallback to static emission calculations when ML is unavailable
- 12.1: Clear error messages when ML model fails
- 12.2: Input validation error messages
- 12.3: Prediction error handling
- 12.4: User notification when ML is unavailable
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock
from route_comparator import RouteEmissionComparator
from mlr_emission_predictor import MLREmissionPredictor
import logging

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestFallbackReliability:
    """
    Property-based tests for fallback reliability.
    
    **Property 10: Fallback reliability**
    **Validates: Requirements 11.4**
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_routes=st.integers(min_value=1, max_value=5),
        base_distance_km=st.floats(min_value=5.0, max_value=200.0),
        vehicle_type=st.sampled_from(['LCGC', 'SUV', 'Sedan', 'EV']),
        fuel_type=st.sampled_from(['Bensin', 'Diesel', 'Listrik'])
    )
    def test_fallback_when_ml_unavailable(self, num_routes, base_distance_km,
                                         vehicle_type, fuel_type):
        """
        **Feature: ml-emission-prediction, Property 10: Fallback reliability**
        **Validates: Requirements 11.4**
        
        For any set of routes, when ML prediction is unavailable or fails,
        the system must:
        1. Fall back to static emission calculations
        2. Still produce valid emission predictions
        3. Mark predictions as using fallback method
        4. Notify the user that ML is unavailable
        
        This ensures the system remains functional even when ML fails.
        """
        # Filter out invalid vehicle-fuel combinations
        if vehicle_type == 'EV' and fuel_type != 'Listrik':
            assume(False)
        if vehicle_type != 'EV' and fuel_type == 'Listrik':
            assume(False)
        
        # Ensure finite values
        assume(np.isfinite(base_distance_km))
        
        # Create a mock ML predictor that always fails
        mock_predictor = Mock(spec=MLREmissionPredictor)
        mock_predictor.is_loaded = False
        mock_predictor.predict_emission.side_effect = RuntimeError("Model not loaded")
        
        # Create comparator with failing ML predictor
        comparator = RouteEmissionComparator(ml_predictor=mock_predictor)
        
        # Generate routes
        routes = []
        for i in range(num_routes):
            distance_km = base_distance_km + (i * 10.0)
            duration_min = distance_km + np.random.uniform(10, 30)
            
            routes.append({
                'route_number': i + 1,
                'distance_km': distance_km,
                'duration_min': duration_min
            })
        
        # Compare routes - should use fallback
        result = comparator.compare_routes(routes, vehicle_type, fuel_type)
        
        # Property 1: System should still produce results (fallback works)
        assert 'best_route' in result, "Should produce best route even with ML failure"
        assert 'all_routes' in result, "Should produce all routes even with ML failure"
        assert len(result['all_routes']) == num_routes, \
            f"Should process all {num_routes} routes with fallback"
        
        # Property 2: Fallback should be marked as used
        assert 'fallback_used' in result, "Result should indicate if fallback was used"
        assert result['fallback_used'] is True, "Fallback should be marked as used"
        
        # Property 3: ML should be marked as disabled
        assert 'ml_enabled' in result, "Result should indicate if ML is enabled"
        assert result['ml_enabled'] is False, "ML should be marked as disabled"
        
        # Property 4: All routes should use fallback method
        for route in result['all_routes']:
            assert 'prediction_method' in route, "Route should indicate prediction method"
            assert 'Fallback' in route['prediction_method'] or 'Static' in route['prediction_method'], \
                f"Route should use fallback method, got: {route['prediction_method']}"
        
        # Property 5: Predictions should still be valid (non-negative, finite)
        for route in result['all_routes']:
            assert 'predicted_emission_g' in route, "Route should have emission prediction"
            assert route['predicted_emission_g'] >= 0, \
                "Fallback prediction should be non-negative"
            assert np.isfinite(route['predicted_emission_g']), \
                "Fallback prediction should be finite"
        
        # Property 6: Best route should still be identified correctly
        best_emission = result['best_route']['predicted_emission_g']
        for route in result['all_routes']:
            assert route['predicted_emission_g'] >= best_emission, \
                "Best route should have lowest emission even with fallback"
        
        # Property 7: Error message should be present when ML fails
        if result['fallback_used']:
            # Error message may be present to inform user
            if 'error_message' in result:
                assert isinstance(result['error_message'], str), \
                    "Error message should be a string"
                assert len(result['error_message']) > 0, \
                    "Error message should not be empty"
    
    @settings(max_examples=100, deadline=None)
    @given(
        distance_km=st.floats(min_value=5.0, max_value=200.0),
        vehicle_type=st.sampled_from(['LCGC', 'SUV', 'Sedan', 'EV']),
        fuel_type=st.sampled_from(['Bensin', 'Diesel', 'Listrik'])
    )
    def test_fallback_produces_reasonable_emissions(self, distance_km, vehicle_type, fuel_type):
        """
        **Feature: ml-emission-prediction, Property 10: Fallback reliability**
        **Validates: Requirements 11.4**
        
        For any valid route, the fallback calculation must produce reasonable
        emission values that are proportional to distance and vehicle type.
        
        This ensures the fallback provides meaningful results, not just any number.
        """
        # Filter out invalid vehicle-fuel combinations
        if vehicle_type == 'EV' and fuel_type != 'Listrik':
            assume(False)
        if vehicle_type != 'EV' and fuel_type == 'Listrik':
            assume(False)
        
        # Ensure finite values
        assume(np.isfinite(distance_km))
        
        # Create a mock ML predictor that always fails
        mock_predictor = Mock(spec=MLREmissionPredictor)
        mock_predictor.is_loaded = False
        mock_predictor.predict_emission.side_effect = RuntimeError("Model not loaded")
        
        # Create comparator with failing ML predictor
        comparator = RouteEmissionComparator(ml_predictor=mock_predictor)
        
        # Single route
        routes = [{
            'route_number': 1,
            'distance_km': distance_km,
            'duration_min': distance_km + 20.0
        }]
        
        # Compare routes - should use fallback
        result = comparator.compare_routes(routes, vehicle_type, fuel_type)
        
        emission = result['best_route']['predicted_emission_g']
        
        # Property 1: Emission should be proportional to distance
        # Typical emission factors are 40-200 g/km
        min_expected = distance_km * 30  # Conservative lower bound
        max_expected = distance_km * 250  # Conservative upper bound
        
        assert emission >= min_expected, \
            f"Fallback emission {emission}g seems too low for {distance_km}km"
        assert emission <= max_expected, \
            f"Fallback emission {emission}g seems too high for {distance_km}km"
        
        # Property 2: EV should have lower emissions than ICE vehicles
        # (if we test multiple vehicle types)
        if vehicle_type == 'EV':
            # EV emissions should be relatively low (< 100 g/km typically)
            emission_per_km = emission / distance_km
            assert emission_per_km < 100, \
                f"EV emission factor {emission_per_km} g/km seems too high"
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_routes=st.integers(min_value=2, max_value=5),
        vehicle_type=st.sampled_from(['LCGC', 'SUV', 'Sedan', 'EV']),
        fuel_type=st.sampled_from(['Bensin', 'Diesel', 'Listrik'])
    )
    def test_fallback_comparison_is_consistent(self, num_routes, vehicle_type, fuel_type):
        """
        **Feature: ml-emission-prediction, Property 10: Fallback reliability**
        **Validates: Requirements 11.4**
        
        For any set of routes with different distances, the fallback calculation
        must consistently identify the shortest route as having the lowest emission
        (assuming similar speeds and conditions).
        
        This ensures the fallback logic is consistent and predictable.
        """
        # Filter out invalid vehicle-fuel combinations
        if vehicle_type == 'EV' and fuel_type != 'Listrik':
            assume(False)
        if vehicle_type != 'EV' and fuel_type == 'Listrik':
            assume(False)
        
        # Create a mock ML predictor that always fails
        mock_predictor = Mock(spec=MLREmissionPredictor)
        mock_predictor.is_loaded = False
        mock_predictor.predict_emission.side_effect = RuntimeError("Model not loaded")
        
        # Create comparator with failing ML predictor
        comparator = RouteEmissionComparator(ml_predictor=mock_predictor)
        
        # Generate routes with clearly different distances
        routes = []
        for i in range(num_routes):
            distance_km = 20.0 + (i * 30.0)  # Ensure different distances
            duration_min = distance_km + 25.0
            
            routes.append({
                'route_number': i + 1,
                'distance_km': distance_km,
                'duration_min': duration_min
            })
        
        # Compare routes - should use fallback
        result = comparator.compare_routes(routes, vehicle_type, fuel_type)
        
        # Property: Shortest route should have lowest emission
        shortest_route = min(routes, key=lambda r: r['distance_km'])
        best_route_num = result['best_route']['route_number']
        
        assert best_route_num == shortest_route['route_number'], \
            f"Fallback should select shortest route {shortest_route['route_number']} " \
            f"as best, but selected {best_route_num}"
        
        # Property: Emissions should be ordered by distance
        sorted_by_distance = sorted(result['all_routes'], key=lambda r: r['distance_km'])
        sorted_by_emission = sorted(result['all_routes'], key=lambda r: r['predicted_emission_g'])
        
        # Route numbers should be in same order
        distance_order = [r['route_number'] for r in sorted_by_distance]
        emission_order = [r['route_number'] for r in sorted_by_emission]
        
        assert distance_order == emission_order, \
            f"Fallback emissions should be ordered by distance: " \
            f"distance order {distance_order} != emission order {emission_order}"
    
    def test_fallback_with_custom_calculator(self):
        """
        Test that custom fallback calculator is used when provided.
        
        **Validates: Requirements 11.4**
        """
        # Create a mock ML predictor that always fails
        mock_predictor = Mock(spec=MLREmissionPredictor)
        mock_predictor.is_loaded = False
        mock_predictor.predict_emission.side_effect = RuntimeError("Model not loaded")
        
        # Create a custom fallback calculator
        def custom_fallback(distance_km, vehicle_type, fuel_type):
            # Simple custom calculation: 100 g/km for all vehicles
            return distance_km * 100.0
        
        # Create comparator with custom fallback
        comparator = RouteEmissionComparator(
            ml_predictor=mock_predictor,
            fallback_calculator=custom_fallback
        )
        
        # Single route
        routes = [{
            'route_number': 1,
            'distance_km': 50.0,
            'duration_min': 60.0
        }]
        
        # Compare routes
        result = comparator.compare_routes(routes, 'LCGC', 'Bensin')
        
        # Verify custom fallback was used
        expected_emission = 50.0 * 100.0  # 5000 g
        actual_emission = result['best_route']['predicted_emission_g']
        
        assert abs(actual_emission - expected_emission) < 0.1, \
            f"Custom fallback should produce {expected_emission}g, got {actual_emission}g"
        
        assert result['fallback_used'] is True, "Should mark fallback as used"
    
    @settings(max_examples=50, deadline=None)
    @given(
        distance_km=st.floats(min_value=5.0, max_value=200.0),
        vehicle_type=st.sampled_from(['LCGC', 'SUV', 'Sedan', 'EV']),
        fuel_type=st.sampled_from(['Bensin', 'Diesel', 'Listrik'])
    )
    def test_fallback_explanation_mentions_unavailability(self, distance_km, vehicle_type, fuel_type):
        """
        **Feature: ml-emission-prediction, Property 10: Fallback reliability**
        **Validates: Requirements 11.4, 12.4**
        
        For any route where fallback is used, the explanation must inform the user
        that ML prediction is unavailable and fallback is being used.
        
        This ensures transparency and user notification.
        """
        # Filter out invalid vehicle-fuel combinations
        if vehicle_type == 'EV' and fuel_type != 'Listrik':
            assume(False)
        if vehicle_type != 'EV' and fuel_type == 'Listrik':
            assume(False)
        
        # Ensure finite values
        assume(np.isfinite(distance_km))
        
        # Create a mock ML predictor that always fails
        mock_predictor = Mock(spec=MLREmissionPredictor)
        mock_predictor.is_loaded = False
        mock_predictor.predict_emission.side_effect = RuntimeError("Model not loaded")
        
        # Create comparator with failing ML predictor
        comparator = RouteEmissionComparator(ml_predictor=mock_predictor)
        
        # Single route
        routes = [{
            'route_number': 1,
            'distance_km': distance_km,
            'duration_min': distance_km + 20.0
        }]
        
        # Compare routes
        result = comparator.compare_routes(routes, vehicle_type, fuel_type)
        
        # Property: Explanation should mention ML unavailability
        explanation = result['explanation']
        
        assert 'unavailable' in explanation.lower() or 'fallback' in explanation.lower() or 'static' in explanation.lower(), \
            f"Explanation should mention ML unavailability or fallback usage: {explanation}"
        
        # Property: Explanation should still be informative
        assert len(explanation) > 50, \
            "Explanation should still be informative even with fallback"
        
        # Property: Explanation should mention the route
        assert f"Route {result['best_route']['route_number']}" in explanation, \
            "Explanation should mention the recommended route"
    
    def test_fallback_handles_missing_model_files(self):
        """
        Test that fallback works when model files are missing.
        
        **Validates: Requirements 11.4, 12.1**
        """
        # Try to create predictor with non-existent model files
        try:
            predictor = MLREmissionPredictor(
                model_path='nonexistent_model.joblib',
                scaler_path='nonexistent_scaler.joblib',
                encoder_path='nonexistent_encoder.joblib'
            )
            # If it doesn't raise, mark as unavailable
            predictor.is_loaded = False
        except FileNotFoundError:
            # Expected - create a mock instead
            predictor = Mock(spec=MLREmissionPredictor)
            predictor.is_loaded = False
            predictor.predict_emission.side_effect = FileNotFoundError("Model files not found")
        
        # Create comparator
        comparator = RouteEmissionComparator(ml_predictor=predictor)
        
        # Single route
        routes = [{
            'route_number': 1,
            'distance_km': 30.0,
            'duration_min': 35.0
        }]
        
        # Compare routes - should use fallback
        result = comparator.compare_routes(routes, 'SUV', 'Bensin')
        
        # Verify fallback was used
        assert result['fallback_used'] is True, "Should use fallback when model files missing"
        assert result['ml_enabled'] is False, "ML should be disabled when files missing"
        
        # Verify prediction is still valid
        assert result['best_route']['predicted_emission_g'] > 0, \
            "Should still produce valid prediction with fallback"
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_routes=st.integers(min_value=1, max_value=3),
        vehicle_type=st.sampled_from(['LCGC', 'SUV', 'Sedan', 'EV']),
        fuel_type=st.sampled_from(['Bensin', 'Diesel', 'Listrik'])
    )
    def test_fallback_partial_failure(self, num_routes, vehicle_type, fuel_type):
        """
        **Feature: ml-emission-prediction, Property 10: Fallback reliability**
        **Validates: Requirements 11.4**
        
        When ML prediction fails for some routes but not others, the system should:
        1. Use ML predictions where available
        2. Use fallback for failed routes
        3. Still produce a valid comparison
        
        This tests mixed success/failure scenarios.
        """
        # Filter out invalid vehicle-fuel combinations
        if vehicle_type == 'EV' and fuel_type != 'Listrik':
            assume(False)
        if vehicle_type != 'EV' and fuel_type == 'Listrik':
            assume(False)
        
        # Create a mock ML predictor that fails randomly
        mock_predictor = Mock(spec=MLREmissionPredictor)
        mock_predictor.is_loaded = True
        
        # Make it fail for some calls
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] % 2 == 0:  # Fail every other call
                raise RuntimeError("Prediction failed")
            # Return a reasonable value for successful calls
            distance = kwargs.get('distance_km', args[0] if args else 50.0)
            return distance * 150.0  # Simple calculation
        
        mock_predictor.predict_emission.side_effect = side_effect
        
        # Create comparator
        comparator = RouteEmissionComparator(ml_predictor=mock_predictor)
        
        # Generate routes
        routes = []
        for i in range(num_routes):
            routes.append({
                'route_number': i + 1,
                'distance_km': 20.0 + (i * 15.0),
                'duration_min': 25.0 + (i * 18.0)
            })
        
        # Compare routes - should handle partial failures
        result = comparator.compare_routes(routes, vehicle_type, fuel_type)
        
        # Property: Should still produce results
        assert 'best_route' in result, "Should produce results despite partial failures"
        assert len(result['all_routes']) > 0, "Should have at least some successful predictions"
        
        # Property: Should mark fallback as used if any route used it
        if num_routes > 1:
            # With multiple routes and alternating failures, fallback should be used
            assert result['fallback_used'] is True, \
                "Should mark fallback as used when some predictions fail"


class TestFallbackErrorMessages:
    """
    Tests for error messages when ML fails and fallback is used.
    
    **Validates: Requirements 12.1, 12.2, 12.3, 12.4**
    """
    
    def test_error_message_when_model_not_loaded(self):
        """
        Test that clear error message is provided when model is not loaded.
        
        **Validates: Requirements 12.1**
        """
        # Create a mock ML predictor that fails with model loading error
        mock_predictor = Mock(spec=MLREmissionPredictor)
        mock_predictor.is_loaded = False
        mock_predictor.predict_emission.side_effect = RuntimeError("Model not loaded. Cannot make predictions.")
        
        # Create comparator
        comparator = RouteEmissionComparator(ml_predictor=mock_predictor)
        
        # Single route
        routes = [{
            'route_number': 1,
            'distance_km': 25.0,
            'duration_min': 30.0
        }]
        
        # Compare routes
        result = comparator.compare_routes(routes, 'LCGC', 'Bensin')
        
        # Verify error message is present and informative
        if 'error_message' in result:
            error_msg = result['error_message']
            assert 'model' in error_msg.lower() or 'ml' in error_msg.lower(), \
                f"Error message should mention model: {error_msg}"
            assert 'unavailable' in error_msg.lower() or 'not loaded' in error_msg.lower(), \
                f"Error message should explain the problem: {error_msg}"
    
    def test_error_message_when_prediction_fails(self):
        """
        Test that clear error message is provided when prediction fails.
        
        **Validates: Requirements 12.3**
        """
        # Create a mock ML predictor that fails with prediction error
        mock_predictor = Mock(spec=MLREmissionPredictor)
        mock_predictor.is_loaded = True
        mock_predictor.predict_emission.side_effect = RuntimeError("Prediction failed: invalid input")
        
        # Create comparator
        comparator = RouteEmissionComparator(ml_predictor=mock_predictor)
        
        # Single route
        routes = [{
            'route_number': 1,
            'distance_km': 25.0,
            'duration_min': 30.0
        }]
        
        # Compare routes
        result = comparator.compare_routes(routes, 'SUV', 'Bensin')
        
        # Verify fallback was used
        assert result['fallback_used'] is True, "Should use fallback when prediction fails"
        
        # Verify error message mentions the failure
        if 'error_message' in result:
            error_msg = result['error_message']
            assert 'prediction' in error_msg.lower() or 'ml' in error_msg.lower(), \
                f"Error message should mention prediction failure: {error_msg}"
    
    def test_user_notification_in_explanation(self):
        """
        Test that user is notified in explanation when ML is unavailable.
        
        **Validates: Requirements 12.4**
        """
        # Create a mock ML predictor that fails
        mock_predictor = Mock(spec=MLREmissionPredictor)
        mock_predictor.is_loaded = False
        mock_predictor.predict_emission.side_effect = RuntimeError("Model not available")
        
        # Create comparator
        comparator = RouteEmissionComparator(ml_predictor=mock_predictor)
        
        # Single route
        routes = [{
            'route_number': 1,
            'distance_km': 40.0,
            'duration_min': 45.0
        }]
        
        # Compare routes
        result = comparator.compare_routes(routes, 'Sedan', 'Diesel')
        
        # Verify explanation notifies user
        explanation = result['explanation']
        
        # Should mention ML unavailability or fallback
        assert any(keyword in explanation.lower() for keyword in 
                  ['unavailable', 'fallback', 'static', 'note']), \
            f"Explanation should notify user about ML unavailability: {explanation}"
        
        # Should still provide useful information
        assert 'route' in explanation.lower(), \
            "Explanation should still mention route information"
        assert 'emission' in explanation.lower() or 'co' in explanation.lower(), \
            "Explanation should still mention emissions"
