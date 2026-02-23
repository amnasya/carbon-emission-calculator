"""Property-based tests for RouteEmissionComparator."""
import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from route_comparator import RouteEmissionComparator
from mlr_emission_predictor import MLREmissionPredictor


# Strategy for generating valid route data
def route_strategy():
    """Generate valid route data for testing."""
    return st.fixed_dictionaries({
        'route_number': st.integers(min_value=1, max_value=10),
        'distance_km': st.floats(min_value=0.1, max_value=500.0),
        'duration_min': st.floats(min_value=1.0, max_value=600.0)
    })


class TestBestRouteSelection:
    """Property-based tests for best route selection."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_routes=st.integers(min_value=2, max_value=5),
        vehicle_type=st.sampled_from(['LCGC', 'SUV', 'Sedan', 'EV']),
        fuel_type=st.sampled_from(['Bensin', 'Diesel', 'Listrik'])
    )
    def test_best_route_selection_correctness(self, num_routes, vehicle_type, fuel_type):
        """
        **Feature: ml-emission-prediction, Property 7: Best route selection correctness**
        **Validates: Requirements 2.2, 2.3**
        
        For any set of routes with predicted emissions, the system must correctly
        identify the route with the minimum predicted CO₂ emission as the best route.
        
        This ensures:
        1. The comparison logic correctly identifies the minimum emission
        2. The best route is marked as recommended
        3. The selection is based on ML predictions, not static calculations
        """
        # Filter out invalid vehicle-fuel combinations
        if vehicle_type == 'EV' and fuel_type != 'Listrik':
            assume(False)
        if vehicle_type != 'EV' and fuel_type == 'Listrik':
            assume(False)
        
        try:
            comparator = RouteEmissionComparator()
            
            # Generate random routes with varying distances
            routes = []
            for i in range(num_routes):
                # Generate routes with different distances to ensure different emissions
                base_distance = 10.0 + (i * 20.0)
                distance_km = base_distance + np.random.uniform(0, 10)
                duration_min = distance_km * np.random.uniform(1.0, 2.0)
                
                routes.append({
                    'route_number': i + 1,
                    'distance_km': distance_km,
                    'duration_min': duration_min
                })
            
            # Compare routes
            result = comparator.compare_routes(routes, vehicle_type, fuel_type)
            
            # Property 1: Result must contain best_route
            assert 'best_route' in result, "Result must contain best_route"
            assert result['best_route'] is not None, "best_route cannot be None"
            
            # Property 2: Result must contain all_routes
            assert 'all_routes' in result, "Result must contain all_routes"
            assert len(result['all_routes']) == num_routes, \
                f"all_routes should contain {num_routes} routes, got {len(result['all_routes'])}"
            
            # Property 3: Best route must have the minimum emission
            best_route = result['best_route']
            all_routes = result['all_routes']
            
            best_emission = best_route['predicted_emission_g']
            
            for route in all_routes:
                assert route['predicted_emission_g'] >= best_emission, \
                    f"Found route with lower emission ({route['predicted_emission_g']}) " \
                    f"than best route ({best_emission})"
            
            # Property 4: Best route must be marked as recommended
            assert best_route.get('is_recommended', False) == True, \
                "Best route must be marked as recommended"
            
            # Property 5: Best route must use ML prediction method
            assert best_route.get('prediction_method') == 'ML', \
                "Best route must use ML prediction method"
            
            # Property 6: ML must be enabled in result
            assert result.get('ml_enabled') == True, \
                "ML must be enabled in result"
            
            # Property 7: Best route must be the first in all_routes (sorted by emission)
            assert all_routes[0]['route_number'] == best_route['route_number'], \
                "Best route must be first in sorted all_routes list"
            
            # Property 8: All routes must be sorted by emission (ascending)
            for i in range(len(all_routes) - 1):
                assert all_routes[i]['predicted_emission_g'] <= all_routes[i + 1]['predicted_emission_g'], \
                    f"Routes not sorted by emission: {all_routes[i]['predicted_emission_g']} > " \
                    f"{all_routes[i + 1]['predicted_emission_g']}"
            
        except (FileNotFoundError, RuntimeError) as e:
            # If model files are missing, skip the test
            if "model" in str(e).lower() or "file" in str(e).lower():
                pytest.skip(f"Model files not available: {e}")
            else:
                raise
    
    @settings(max_examples=100, deadline=None)
    @given(
        distance_km=st.floats(min_value=0.1, max_value=500.0),
        duration_min=st.floats(min_value=1.0, max_value=600.0),
        vehicle_type=st.sampled_from(['LCGC', 'SUV', 'Sedan', 'EV']),
        fuel_type=st.sampled_from(['Bensin', 'Diesel', 'Listrik'])
    )
    def test_single_route_is_best(self, distance_km, duration_min, vehicle_type, fuel_type):
        """
        **Feature: ml-emission-prediction, Property 7: Best route selection correctness**
        **Validates: Requirements 2.2, 2.3**
        
        For any single route, that route must be selected as the best route.
        This is a degenerate case that tests the boundary condition.
        """
        # Filter out invalid vehicle-fuel combinations
        if vehicle_type == 'EV' and fuel_type != 'Listrik':
            assume(False)
        if vehicle_type != 'EV' and fuel_type == 'Listrik':
            assume(False)
        
        # Ensure finite values
        assume(np.isfinite(distance_km))
        assume(np.isfinite(duration_min))
        
        try:
            comparator = RouteEmissionComparator()
            
            routes = [{
                'route_number': 1,
                'distance_km': distance_km,
                'duration_min': duration_min
            }]
            
            result = comparator.compare_routes(routes, vehicle_type, fuel_type)
            
            # Property: Single route must be the best route
            assert result['best_route']['route_number'] == 1, \
                "Single route must be selected as best"
            
            # Property: No alternative routes
            assert len(result.get('alternative_routes', [])) == 0, \
                "Single route should have no alternatives"
            
            # Property: Savings should be zero (no worse route to compare)
            assert result['savings']['vs_worst_route_g'] == 0, \
                "Savings should be zero for single route"
            assert result['savings']['vs_worst_route_pct'] == 0, \
                "Savings percentage should be zero for single route"
            
        except (FileNotFoundError, RuntimeError) as e:
            if "model" in str(e).lower() or "file" in str(e).lower():
                pytest.skip(f"Model files not available: {e}")
            else:
                raise
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_routes=st.integers(min_value=2, max_value=5),
        vehicle_type=st.sampled_from(['LCGC', 'SUV', 'Sedan', 'EV']),
        fuel_type=st.sampled_from(['Bensin', 'Diesel', 'Listrik'])
    )
    def test_best_route_has_minimum_emission(self, num_routes, vehicle_type, fuel_type):
        """
        **Feature: ml-emission-prediction, Property 7: Best route selection correctness**
        **Validates: Requirements 2.2**
        
        For any set of routes, the best route must have an emission value that is
        less than or equal to all other routes. This is the mathematical definition
        of "minimum".
        """
        # Filter out invalid vehicle-fuel combinations
        if vehicle_type == 'EV' and fuel_type != 'Listrik':
            assume(False)
        if vehicle_type != 'EV' and fuel_type == 'Listrik':
            assume(False)
        
        try:
            comparator = RouteEmissionComparator()
            
            # Generate routes with clearly different distances
            routes = []
            for i in range(num_routes):
                distance_km = 10.0 + (i * 30.0)  # Ensure different distances
                duration_min = distance_km + np.random.uniform(10, 50)
                
                routes.append({
                    'route_number': i + 1,
                    'distance_km': distance_km,
                    'duration_min': duration_min
                })
            
            result = comparator.compare_routes(routes, vehicle_type, fuel_type)
            
            best_emission = result['best_route']['predicted_emission_g']
            
            # Property: Best route emission <= all other route emissions
            for route in result['all_routes']:
                assert best_emission <= route['predicted_emission_g'], \
                    f"Best route emission {best_emission} > route emission {route['predicted_emission_g']}"
            
            # Property: At least one route has emission equal to best (the best route itself)
            min_emission_in_all = min(r['predicted_emission_g'] for r in result['all_routes'])
            assert abs(best_emission - min_emission_in_all) < 0.001, \
                f"Best route emission {best_emission} != minimum in all routes {min_emission_in_all}"
            
        except (FileNotFoundError, RuntimeError) as e:
            if "model" in str(e).lower() or "file" in str(e).lower():
                pytest.skip(f"Model files not available: {e}")
            else:
                raise


class TestEmissionDifferenceCalculation:
    """Property-based tests for emission difference calculation."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_routes=st.integers(min_value=2, max_value=5),
        vehicle_type=st.sampled_from(['LCGC', 'SUV', 'Sedan', 'EV']),
        fuel_type=st.sampled_from(['Bensin', 'Diesel', 'Listrik'])
    )
    def test_emission_difference_accuracy(self, num_routes, vehicle_type, fuel_type):
        """
        **Feature: ml-emission-prediction, Property 8: Emission difference accuracy**
        **Validates: Requirements 2.4**
        
        For any pair of routes, the emission difference must be calculated as:
        difference = alternative_emission - best_emission
        
        This ensures:
        1. Differences are calculated correctly using subtraction
        2. Percentage differences are calculated correctly
        3. All alternative routes have positive differences (since best has minimum)
        """
        # Filter out invalid vehicle-fuel combinations
        if vehicle_type == 'EV' and fuel_type != 'Listrik':
            assume(False)
        if vehicle_type != 'EV' and fuel_type == 'Listrik':
            assume(False)
        
        try:
            comparator = RouteEmissionComparator()
            
            # Generate routes with clearly different distances
            routes = []
            for i in range(num_routes):
                distance_km = 20.0 + (i * 40.0)  # Ensure significantly different distances
                duration_min = distance_km + np.random.uniform(20, 60)
                
                routes.append({
                    'route_number': i + 1,
                    'distance_km': distance_km,
                    'duration_min': duration_min
                })
            
            result = comparator.compare_routes(routes, vehicle_type, fuel_type)
            
            best_emission = result['best_route']['predicted_emission_g']
            alternative_routes = result.get('alternative_routes', [])
            
            # Property 1: Number of alternatives = total routes - 1
            assert len(alternative_routes) == num_routes - 1, \
                f"Expected {num_routes - 1} alternatives, got {len(alternative_routes)}"
            
            # Property 2: Each alternative has correct emission difference
            for alt in alternative_routes:
                expected_diff = alt['predicted_emission_g'] - best_emission
                actual_diff = alt['emission_difference_g']
                
                # Allow small floating point error
                assert abs(actual_diff - expected_diff) < 0.01, \
                    f"Emission difference incorrect: {actual_diff} != {expected_diff}"
                
                # Property 3: Difference must be non-negative (best has minimum)
                assert actual_diff >= 0, \
                    f"Emission difference must be non-negative, got {actual_diff}"
            
            # Property 4: Percentage differences are calculated correctly
            for alt in alternative_routes:
                # Handle zero emission case
                if best_emission > 0:
                    expected_pct = (alt['emission_difference_g'] / best_emission) * 100
                else:
                    expected_pct = 0.0
                actual_pct = alt['emission_difference_pct']
                
                # Allow small floating point error
                if expected_pct > 0:
                    relative_error = abs(actual_pct - expected_pct) / max(expected_pct, 0.001)
                    assert relative_error < 0.01, \
                        f"Percentage difference incorrect: {actual_pct} != {expected_pct}"
                else:
                    assert actual_pct == 0.0, \
                        f"Percentage should be 0 when best emission is 0, got {actual_pct}"
            
            # Property 5: Savings calculation is correct
            worst_emission = max(r['predicted_emission_g'] for r in result['all_routes'])
            expected_savings = worst_emission - best_emission
            actual_savings = result['savings']['vs_worst_route_g']
            
            assert abs(actual_savings - expected_savings) < 0.01, \
                f"Savings calculation incorrect: {actual_savings} != {expected_savings}"
            
            # Property 6: Savings percentage is correct
            if worst_emission > 0:
                expected_savings_pct = (expected_savings / worst_emission) * 100
                actual_savings_pct = result['savings']['vs_worst_route_pct']
                
                relative_error = abs(actual_savings_pct - expected_savings_pct) / max(expected_savings_pct, 0.001)
                assert relative_error < 0.01, \
                    f"Savings percentage incorrect: {actual_savings_pct} != {expected_savings_pct}"
            
        except (FileNotFoundError, RuntimeError) as e:
            if "model" in str(e).lower() or "file" in str(e).lower():
                pytest.skip(f"Model files not available: {e}")
            else:
                raise
    
    @settings(max_examples=100, deadline=None)
    @given(
        distance_1=st.floats(min_value=10.0, max_value=100.0),
        distance_2=st.floats(min_value=101.0, max_value=300.0),
        vehicle_type=st.sampled_from(['LCGC', 'SUV', 'Sedan', 'EV']),
        fuel_type=st.sampled_from(['Bensin', 'Diesel', 'Listrik'])
    )
    def test_difference_is_positive_for_longer_route(self, distance_1, distance_2, 
                                                     vehicle_type, fuel_type):
        """
        **Feature: ml-emission-prediction, Property 8: Emission difference accuracy**
        **Validates: Requirements 2.4**
        
        For any two routes where one is significantly longer than the other,
        the longer route should have higher emissions, and thus a positive
        emission difference when compared to the shorter route.
        """
        # Filter out invalid vehicle-fuel combinations
        if vehicle_type == 'EV' and fuel_type != 'Listrik':
            assume(False)
        if vehicle_type != 'EV' and fuel_type == 'Listrik':
            assume(False)
        
        # Ensure finite values and distance_2 > distance_1
        assume(np.isfinite(distance_1))
        assume(np.isfinite(distance_2))
        assume(distance_2 > distance_1)
        
        try:
            comparator = RouteEmissionComparator()
            
            routes = [
                {
                    'route_number': 1,
                    'distance_km': distance_1,
                    'duration_min': distance_1 + 30.0
                },
                {
                    'route_number': 2,
                    'distance_km': distance_2,
                    'duration_min': distance_2 + 30.0
                }
            ]
            
            result = comparator.compare_routes(routes, vehicle_type, fuel_type)
            
            # Property: Shorter route should be best (assuming similar speeds)
            # Since distance_1 < distance_2, route 1 should have lower emissions
            best_route_num = result['best_route']['route_number']
            
            # Find emissions for both routes
            route_1_emission = next(r['predicted_emission_g'] for r in result['all_routes'] 
                                   if r['route_number'] == 1)
            route_2_emission = next(r['predicted_emission_g'] for r in result['all_routes']
                                   if r['route_number'] == 2)
            
            # Property: Longer route should have higher emission
            # Note: If both emissions are zero (e.g., EV with zero-emission model), skip this check
            if route_1_emission == 0 and route_2_emission == 0:
                assume(False)  # Skip this test case as it's not meaningful
            
            assert route_2_emission > route_1_emission, \
                f"Longer route should have higher emission: {route_2_emission} <= {route_1_emission}"
            
            # Property: If route 1 is best, route 2 should have positive difference
            if best_route_num == 1:
                alt_route = next(r for r in result['alternative_routes'] if r['route_number'] == 2)
                assert alt_route['emission_difference_g'] > 0, \
                    "Alternative route should have positive emission difference"
            
        except (FileNotFoundError, RuntimeError) as e:
            if "model" in str(e).lower() or "file" in str(e).lower():
                pytest.skip(f"Model files not available: {e}")
            else:
                raise


class TestExplanationGeneration:
    """Tests for explanation generation."""
    
    def test_explanation_contains_route_number(self):
        """Test that explanation contains the recommended route number."""
        try:
            comparator = RouteEmissionComparator()
            
            routes = [
                {'route_number': 1, 'distance_km': 50.0, 'duration_min': 60.0},
                {'route_number': 2, 'distance_km': 70.0, 'duration_min': 80.0}
            ]
            
            result = comparator.compare_routes(routes, 'LCGC', 'Bensin')
            
            explanation = result['explanation']
            best_route_num = result['best_route']['route_number']
            
            # Explanation should mention the route number
            assert f"Route {best_route_num}" in explanation, \
                "Explanation should mention the recommended route number"
            
        except (FileNotFoundError, RuntimeError) as e:
            if "model" in str(e).lower() or "file" in str(e).lower():
                pytest.skip(f"Model files not available: {e}")
            else:
                raise
    
    def test_explanation_contains_emission_value(self):
        """Test that explanation contains the emission value."""
        try:
            comparator = RouteEmissionComparator()
            
            routes = [
                {'route_number': 1, 'distance_km': 50.0, 'duration_min': 60.0}
            ]
            
            result = comparator.compare_routes(routes, 'LCGC', 'Bensin')
            
            explanation = result['explanation']
            
            # Explanation should mention CO₂ or emission
            assert 'CO₂' in explanation or 'emission' in explanation.lower(), \
                "Explanation should mention CO₂ or emission"
            
            # Explanation should mention the unit (g or kg)
            assert ' g' in explanation or ' kg' in explanation, \
                "Explanation should mention emission unit"
            
        except (FileNotFoundError, RuntimeError) as e:
            if "model" in str(e).lower() or "file" in str(e).lower():
                pytest.skip(f"Model files not available: {e}")
            else:
                raise
    
    def test_explanation_mentions_ml_factors(self):
        """Test that explanation mentions ML prediction factors."""
        try:
            comparator = RouteEmissionComparator()
            
            routes = [
                {'route_number': 1, 'distance_km': 50.0, 'duration_min': 60.0}
            ]
            
            result = comparator.compare_routes(routes, 'LCGC', 'Bensin')
            
            explanation = result['explanation']
            
            # Explanation should mention multiple factors
            assert 'distance' in explanation.lower(), \
                "Explanation should mention distance"
            assert 'vehicle' in explanation.lower() or 'fuel' in explanation.lower(), \
                "Explanation should mention vehicle or fuel type"
            
        except (FileNotFoundError, RuntimeError) as e:
            if "model" in str(e).lower() or "file" in str(e).lower():
                pytest.skip(f"Model files not available: {e}")
            else:
                raise


class TestErrorHandling:
    """Tests for error handling in route comparison."""
    
    def test_empty_routes_raises_error(self):
        """Test that empty routes list raises ValueError."""
        try:
            comparator = RouteEmissionComparator()
            
            with pytest.raises(ValueError) as exc_info:
                comparator.compare_routes([], 'LCGC', 'Bensin')
            
            assert 'empty' in str(exc_info.value).lower(), \
                "Error message should mention empty routes"
            
        except (FileNotFoundError, RuntimeError) as e:
            if "model" in str(e).lower() or "file" in str(e).lower():
                pytest.skip(f"Model files not available: {e}")
            else:
                raise
    
    def test_invalid_routes_type_raises_error(self):
        """Test that invalid routes type raises ValueError."""
        try:
            comparator = RouteEmissionComparator()
            
            with pytest.raises(ValueError) as exc_info:
                comparator.compare_routes("not a list", 'LCGC', 'Bensin')
            
            assert 'list' in str(exc_info.value).lower(), \
                "Error message should mention list type"
            
        except (FileNotFoundError, RuntimeError) as e:
            if "model" in str(e).lower() or "file" in str(e).lower():
                pytest.skip(f"Model files not available: {e}")
            else:
                raise
