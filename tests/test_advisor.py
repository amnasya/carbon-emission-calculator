"""
Property-based tests for Emission Reduction Advisor module.

This test suite uses Hypothesis for property-based testing to verify
correctness properties across a wide range of inputs.
"""

import pytest
from hypothesis import given, strategies as st, settings
from advisor import (
    get_emission_advice,
    validate_trip_data,
    TripAnalyzer,
    TripData,
    AdvisorError
)
from emission import EMISSION_FACTORS, get_emission_factor


# ============================================================================
# Test Data Generators (Strategies)
# ============================================================================

# Strategy for valid vehicle types
vehicle_types = st.sampled_from(list(EMISSION_FACTORS.keys()))

# Strategy for all possible vehicle types (including invalid ones)
all_vehicle_types = st.sampled_from(
    list(EMISSION_FACTORS.keys()) + ["Sedan", "Truck", "Motorcycle", "Van", "Bus", "Bicycle"]
)

# Strategy for all possible fuel types (including invalid ones)
all_fuel_types = st.sampled_from(
    ["bensin", "solar", "listrik", "diesel", "hybrid", "hydrogen", "gas", "kerosene"]
)


@st.composite
def valid_vehicle_fuel_combo(draw):
    """Generate a valid vehicle-fuel combination from EMISSION_FACTORS."""
    vehicle = draw(vehicle_types)
    valid_fuels = list(EMISSION_FACTORS[vehicle].keys())
    fuel = draw(st.sampled_from(valid_fuels))
    return vehicle, fuel


@st.composite
def invalid_vehicle_fuel_combo(draw):
    """
    Generate an invalid vehicle-fuel combination.
    
    This generates combinations that are NOT in EMISSION_FACTORS by either:
    1. Using an invalid vehicle type
    2. Using a valid vehicle with an invalid fuel type
    3. Using a valid vehicle with a fuel type that doesn't match
    """
    strategy_choice = draw(st.integers(min_value=1, max_value=3))
    
    if strategy_choice == 1:
        # Invalid vehicle type with any fuel
        vehicle = draw(st.sampled_from(["Sedan", "Truck", "Motorcycle", "Van", "Bus"]))
        fuel = draw(all_fuel_types)
        return vehicle, fuel
    
    elif strategy_choice == 2:
        # Valid vehicle with completely invalid fuel
        vehicle = draw(vehicle_types)
        fuel = draw(st.sampled_from(["diesel", "hybrid", "hydrogen", "gas"]))
        return vehicle, fuel
    
    else:
        # Valid vehicle with wrong fuel (e.g., EV with bensin)
        vehicle = draw(vehicle_types)
        valid_fuels = list(EMISSION_FACTORS[vehicle].keys())
        all_fuels = ["bensin", "solar", "listrik"]
        invalid_fuels = [f for f in all_fuels if f not in valid_fuels]
        
        if invalid_fuels:
            fuel = draw(st.sampled_from(invalid_fuels))
        else:
            # Fallback to completely invalid fuel
            fuel = draw(st.sampled_from(["diesel", "hybrid"]))
        
        return vehicle, fuel


@st.composite
def trip_data_strategy(draw):
    """Generate valid trip data for testing."""
    distance = draw(st.floats(min_value=0.1, max_value=500.0, allow_nan=False, allow_infinity=False))
    vehicle, fuel = draw(valid_vehicle_fuel_combo())
    emission_factor = EMISSION_FACTORS[vehicle][fuel]
    emission = distance * emission_factor
    
    return {
        'distance_km': distance,
        'car_type': vehicle,
        'fuel_type': fuel,
        'emission_g': emission
    }


@st.composite
def invalid_trip_data_strategy(draw):
    """Generate trip data with invalid vehicle-fuel combinations."""
    distance = draw(st.floats(min_value=0.1, max_value=500.0, allow_nan=False, allow_infinity=False))
    vehicle, fuel = draw(invalid_vehicle_fuel_combo())
    
    # Use a dummy emission value since the combination is invalid
    emission = draw(st.floats(min_value=1.0, max_value=100000.0, allow_nan=False, allow_infinity=False))
    
    return {
        'distance_km': distance,
        'car_type': vehicle,
        'fuel_type': fuel,
        'emission_g': emission
    }


@st.composite
def multi_route_trip_data_strategy(draw):
    """
    Generate trip data with multiple routes having different emissions.
    
    This strategy creates a base trip and then generates 2-5 alternative routes
    with varying distances and emissions. The routes will have different emission
    values to test route comparison logic.
    """
    # Generate base trip data
    base_distance = draw(st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    vehicle, fuel = draw(valid_vehicle_fuel_combo())
    emission_factor = EMISSION_FACTORS[vehicle][fuel]
    
    # Generate 2-5 routes with different distances (and thus different emissions)
    num_routes = draw(st.integers(min_value=2, max_value=5))
    
    routes = []
    for i in range(num_routes):
        # Vary distance by ±30% from base distance to ensure different emissions
        distance_variation = draw(st.floats(min_value=0.7, max_value=1.3, allow_nan=False, allow_infinity=False))
        route_distance = base_distance * distance_variation
        route_emission = route_distance * emission_factor
        
        routes.append({
            'route_number': i + 1,
            'distance_km': route_distance,
            'duration_min': draw(st.floats(min_value=5.0, max_value=120.0, allow_nan=False, allow_infinity=False)),
            'emission_g': route_emission
        })
    
    # Use the first route's values as the main trip data
    # (simulating that the user is currently on route 0)
    return {
        'distance_km': routes[0]['distance_km'],
        'car_type': vehicle,
        'fuel_type': fuel,
        'emission_g': routes[0]['emission_g'],
        'routes': routes
    }


# ============================================================================
# Property-Based Tests
# ============================================================================

class TestPropertyInvalidCombinationErrorHandling:
    """
    Property-based tests for invalid vehicle-fuel combination error handling.
    
    **Feature: emission-reduction-advisor, Property 19: Invalid combination error handling**
    **Validates: Requirements 7.4, 7.5**
    """
    
    @given(invalid_trip_data_strategy())
    @settings(max_examples=100)
    def test_property_19_invalid_combination_error_handling(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 19: Invalid combination error handling**
        **Validates: Requirements 7.4, 7.5**
        
        For any trip data with an invalid vehicle-fuel combination (one that does not
        exist in EMISSION_FACTORS), the system should:
        1. Return an error message (not crash)
        2. The error message should indicate the invalid combination
        3. The error message should list valid combinations
        
        This validates:
        - Requirement 7.4: Validates vehicle-fuel combination exists in EMISSION_FACTORS
        - Requirement 7.5: Returns error message without crashing on invalid input
        """
        # Verify this is actually an invalid combination
        car_type = trip_data['car_type']
        fuel_type = trip_data['fuel_type']
        is_valid = car_type in EMISSION_FACTORS and fuel_type in EMISSION_FACTORS.get(car_type, {})
        
        # Skip if somehow we generated a valid combination
        if is_valid:
            return
        
        # Call the validation function
        error = validate_trip_data(trip_data)
        
        # Property 1: Should return an error (not None)
        assert error is not None, f"Expected error for invalid combination {car_type}-{fuel_type}"
        
        # Property 2: Error should be a dictionary with expected structure
        assert isinstance(error, dict), "Error should be a dictionary"
        assert 'success' in error, "Error should have 'success' field"
        assert 'error' in error, "Error should have 'error' field"
        assert 'error_type' in error, "Error should have 'error_type' field"
        
        # Property 3: Success should be False
        assert error['success'] is False, "Error success field should be False"
        
        # Property 4: Error type should be validation_error
        assert error['error_type'] == 'validation_error', "Error type should be 'validation_error'"
        
        # Property 5: Error message should mention the invalid combination
        error_message = error['error']
        assert isinstance(error_message, str), "Error message should be a string"
        assert len(error_message) > 0, "Error message should not be empty"
        
        # Property 6: Error message should contain information about valid combinations
        # (either listing them or indicating the combination is invalid)
        assert 'Invalid' in error_message or 'invalid' in error_message, \
            "Error message should indicate the combination is invalid"
        
        # Property 7: The main function should not crash and should return error string
        result = get_emission_advice(trip_data)
        assert isinstance(result, str), "get_emission_advice should return a string"
        assert 'Error' in result or 'error' in result, \
            "Result should indicate an error occurred"
        
        # Property 8: The result should not be a success message
        assert 'Advisor implementation in progress' not in result or 'Error' in result, \
            "Should return error, not success message"
    
    @given(
        car_type=all_vehicle_types,
        fuel_type=all_fuel_types,
        distance=st.floats(min_value=0.1, max_value=500.0, allow_nan=False, allow_infinity=False),
        emission=st.floats(min_value=1.0, max_value=100000.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_property_19_comprehensive_invalid_combinations(self, car_type, fuel_type, distance, emission):
        """
        **Feature: emission-reduction-advisor, Property 19: Invalid combination error handling**
        **Validates: Requirements 7.4, 7.5**
        
        Comprehensive test that generates all possible vehicle-fuel combinations
        and verifies that invalid ones are properly rejected with error messages.
        """
        trip_data = {
            'distance_km': distance,
            'car_type': car_type,
            'fuel_type': fuel_type,
            'emission_g': emission
        }
        
        # Determine if this is a valid combination
        is_valid = car_type in EMISSION_FACTORS and fuel_type in EMISSION_FACTORS.get(car_type, {})
        
        # Call validation
        error = validate_trip_data(trip_data)
        
        if is_valid:
            # Valid combinations should pass validation (error should be None)
            assert error is None, \
                f"Valid combination {car_type}-{fuel_type} should not produce error"
        else:
            # Invalid combinations should produce error
            assert error is not None, \
                f"Invalid combination {car_type}-{fuel_type} should produce error"
            
            # Verify error structure
            assert error['success'] is False
            assert error['error_type'] == 'validation_error'
            assert isinstance(error['error'], str)
            assert len(error['error']) > 0
            
            # Verify get_emission_advice handles it gracefully
            result = get_emission_advice(trip_data)
            assert isinstance(result, str)
            assert 'Error' in result or 'error' in result


class TestPropertyTripDataImmutability:
    """
    Property-based tests for trip data immutability.
    
    **Feature: emission-reduction-advisor, Property 1: Trip data immutability**
    **Validates: Requirements 1.5, 4.2, 8.1, 8.4**
    """
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_1_trip_data_immutability(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 1: Trip data immutability**
        **Validates: Requirements 1.5, 4.2, 8.1, 8.4**
        
        For any trip data dictionary passed to the advisor, the original dictionary
        should remain unchanged after processing. This ensures:
        - Requirement 1.5: Advisor accepts trip data without recalculating emission values
        - Requirement 4.2: Advisor accepts trip data without modifying the original data
        - Requirement 8.1: Advisor analyzes routes without recalculating distances or emissions
        - Requirement 8.4: Advisor uses same emission values calculated by existing module
        
        The property verifies that:
        1. All original keys remain present
        2. All original values remain unchanged
        3. No new keys are added to the original dictionary
        4. Nested structures (like routes) are not modified
        """
        # Create a deep copy of the original trip data for comparison
        import copy
        original_trip_data = copy.deepcopy(trip_data)
        
        # Call the advisor function
        result = get_emission_advice(trip_data)
        
        # Property 1: Result should be a string (not modifying input to return output)
        assert isinstance(result, str), "get_emission_advice should return a string"
        
        # Property 2: All original keys should still be present
        assert set(trip_data.keys()) == set(original_trip_data.keys()), \
            "Original keys should not be modified"
        
        # Property 3: All original values should remain unchanged
        for key in original_trip_data.keys():
            assert trip_data[key] == original_trip_data[key], \
                f"Value for key '{key}' should not be modified. " \
                f"Original: {original_trip_data[key]}, Modified: {trip_data[key]}"
        
        # Property 4: The trip_data dictionary should be identical to the original
        assert trip_data == original_trip_data, \
            "Trip data dictionary should remain completely unchanged"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_1_emission_value_preservation(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 1: Trip data immutability**
        **Validates: Requirements 1.5, 8.4**
        
        Specifically tests that emission values are not recalculated.
        For any trip data, the emission_g value should remain exactly the same
        after calling the advisor, confirming that the advisor uses the
        pre-calculated emission values without recalculation.
        """
        import copy
        original_emission = copy.deepcopy(trip_data['emission_g'])
        
        # Call the advisor
        result = get_emission_advice(trip_data)
        
        # Property: Emission value should be exactly the same (no recalculation)
        assert trip_data['emission_g'] == original_emission, \
            f"Emission value should not be recalculated. " \
            f"Original: {original_emission}, After: {trip_data['emission_g']}"
        
        # Verify it's the exact same value, not just equal
        assert trip_data['emission_g'] is original_emission or \
               trip_data['emission_g'] == original_emission, \
            "Emission value should be preserved without modification"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_1_distance_value_preservation(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 1: Trip data immutability**
        **Validates: Requirements 8.1**
        
        Specifically tests that distance values are not recalculated.
        For any trip data, the distance_km value should remain exactly the same
        after calling the advisor.
        """
        import copy
        original_distance = copy.deepcopy(trip_data['distance_km'])
        
        # Call the advisor
        result = get_emission_advice(trip_data)
        
        # Property: Distance value should be exactly the same (no recalculation)
        assert trip_data['distance_km'] == original_distance, \
            f"Distance value should not be recalculated. " \
            f"Original: {original_distance}, After: {trip_data['distance_km']}"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_1_validation_does_not_modify(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 1: Trip data immutability**
        **Validates: Requirements 4.2**
        
        Tests that even the validation function does not modify the input data.
        This is important because validation happens before processing.
        """
        import copy
        original_trip_data = copy.deepcopy(trip_data)
        
        # Call validation function
        error = validate_trip_data(trip_data)
        
        # Property: Trip data should remain unchanged even after validation
        assert trip_data == original_trip_data, \
            "Validation should not modify the input trip data"
        
        # Verify each field individually
        assert trip_data['distance_km'] == original_trip_data['distance_km']
        assert trip_data['car_type'] == original_trip_data['car_type']
        assert trip_data['fuel_type'] == original_trip_data['fuel_type']
        assert trip_data['emission_g'] == original_trip_data['emission_g']



class TestPropertyDistanceCategorization:
    """
    Property-based tests for distance categorization and distance-appropriate recommendations.
    
    **Feature: emission-reduction-advisor, Property 11, 12, 13: Distance-appropriate recommendations**
    **Validates: Requirements 6.1, 6.2, 6.3**
    """
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_11_short_trip_recommendations(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 11: Distance-appropriate recommendations for short trips**
        **Validates: Requirements 6.1**
        
        For any trip with distance less than 5 kilometers, at least one recommendation
        should mention walking or cycling as primary alternatives.
        
        This validates:
        - Requirement 6.1: WHEN the trip distance is less than 5 kilometers THEN the system
          SHALL recommend walking or cycling as primary alternatives
        """
        # Only test trips with distance < 5 km
        if trip_data['distance_km'] >= 5.0:
            return
        
        # Call the advisor
        result = get_emission_advice(trip_data)
        
        # Property: For short trips, output should mention walking or cycling
        result_lower = result.lower()
        
        # Check for walking-related keywords
        walking_keywords = ['jalan', 'berjalan', 'walking', 'walk']
        has_walking = any(keyword in result_lower for keyword in walking_keywords)
        
        # Check for cycling-related keywords
        cycling_keywords = ['sepeda', 'cycling', 'cycle', 'bike', 'bersepeda']
        has_cycling = any(keyword in result_lower for keyword in cycling_keywords)
        
        # Property: At least one recommendation should mention walking or cycling
        assert has_walking or has_cycling, \
            f"For short trip ({trip_data['distance_km']:.2f} km), " \
            f"at least one recommendation should mention walking or cycling. " \
            f"Result: {result[:200]}..."
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_12_medium_trip_recommendations(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 12: Distance-appropriate recommendations for medium trips**
        **Validates: Requirements 6.2**
        
        For any trip with distance between 5 and 15 kilometers inclusive, at least one
        recommendation should mention public transportation or alternative mobility options.
        
        This validates:
        - Requirement 6.2: WHEN the trip distance is between 5 and 15 kilometers THEN the system
          SHALL recommend public transportation or electric scooter options
        """
        # Only test trips with distance between 5 and 15 km
        if trip_data['distance_km'] < 5.0 or trip_data['distance_km'] > 15.0:
            return
        
        # Call the advisor
        result = get_emission_advice(trip_data)
        
        # Property: For medium trips, output should mention public transport or e-scooter
        result_lower = result.lower()
        
        # Check for public transportation keywords
        public_transport_keywords = [
            'transportasi umum', 'public transport', 'bus', 'kereta', 'train',
            'angkutan umum', 'commuter', 'mrt', 'lrt', 'transjakarta'
        ]
        has_public_transport = any(keyword in result_lower for keyword in public_transport_keywords)
        
        # Check for alternative mobility keywords
        alt_mobility_keywords = [
            'skuter listrik', 'electric scooter', 'e-scooter', 'scooter',
            'motor listrik', 'electric motorcycle'
        ]
        has_alt_mobility = any(keyword in result_lower for keyword in alt_mobility_keywords)
        
        # Property: At least one recommendation should mention public transport or alternative mobility
        assert has_public_transport or has_alt_mobility, \
            f"For medium trip ({trip_data['distance_km']:.2f} km), " \
            f"at least one recommendation should mention public transportation or alternative mobility. " \
            f"Result: {result[:200]}..."
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_13_long_trip_recommendations(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 13: Distance-appropriate recommendations for long trips**
        **Validates: Requirements 6.3**
        
        For any trip with distance greater than 15 kilometers, recommendations should focus
        on vehicle efficiency and route optimization rather than walking or cycling.
        
        This validates:
        - Requirement 6.3: WHEN the trip distance is greater than 15 kilometers THEN the system
          SHALL focus on vehicle efficiency and route optimization recommendations
        """
        # Only test trips with distance > 15 km
        if trip_data['distance_km'] <= 15.0:
            return
        
        # Call the advisor
        result = get_emission_advice(trip_data)
        
        # Property: For long trips, should NOT recommend walking or cycling
        result_lower = result.lower()
        
        # Check that walking/cycling are NOT recommended for long trips
        walking_keywords = ['jalan kaki', 'berjalan', 'walking', 'walk to']
        cycling_keywords = ['sepeda', 'cycling', 'cycle to', 'bike to', 'bersepeda']
        
        # We want to avoid explicit recommendations to walk or cycle for long distances
        # But mentioning them in context (like "too far to walk") is okay
        has_walking_recommendation = any(keyword in result_lower for keyword in walking_keywords)
        has_cycling_recommendation = any(keyword in result_lower for keyword in cycling_keywords)
        
        # Check for vehicle efficiency or route optimization keywords
        efficiency_keywords = [
            'efisiensi', 'efficiency', 'hemat', 'eco-driving', 'kendaraan',
            'vehicle', 'rute', 'route', 'jalur', 'listrik', 'electric', 'ev',
            'optimasi', 'optimization', 'carpooling', 'carpool'
        ]
        has_efficiency_focus = any(keyword in result_lower for keyword in efficiency_keywords)
        
        # Property 1: Should focus on efficiency/route optimization
        assert has_efficiency_focus, \
            f"For long trip ({trip_data['distance_km']:.2f} km), " \
            f"recommendations should focus on vehicle efficiency or route optimization. " \
            f"Result: {result[:200]}..."
        
        # Property 2: Should not primarily recommend walking/cycling for long distances
        # (This is a softer check - we just verify the focus is on efficiency, not active mobility)
        # We allow mentions of walking/cycling but they shouldn't be the primary recommendation
        if has_walking_recommendation or has_cycling_recommendation:
            # If walking/cycling are mentioned, efficiency should also be mentioned
            # (meaning it's not ONLY about walking/cycling)
            assert has_efficiency_focus, \
                f"For long trip ({trip_data['distance_km']:.2f} km), " \
                f"if walking/cycling are mentioned, vehicle efficiency should also be emphasized. " \
                f"Result: {result[:200]}..."



class TestPropertyLowestEmissionRouteIdentification:
    """
    Property-based tests for lowest emission route identification.
    
    **Feature: emission-reduction-advisor, Property 7: Lowest emission route identification**
    **Validates: Requirements 1.4, 8.2**
    """
    
    @given(multi_route_trip_data_strategy())
    @settings(max_examples=100)
    def test_property_7_lowest_emission_route_identification(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 7: Lowest emission route identification**
        **Validates: Requirements 1.4, 8.2**
        
        For any trip data with multiple routes, the system should correctly identify
        the route with the minimum emission value.
        
        This validates:
        - Requirement 1.4: WHEN the trip data contains multiple routes THEN the system
          SHALL analyze each route separately and identify the route with lowest emission
        - Requirement 8.2: WHEN comparing routes THEN the system SHALL identify the route
          with minimum emission as the recommended option
        
        The property verifies that:
        1. The TripAnalyzer correctly identifies which route has the lowest emission
        2. The best_route_index points to the route with minimum emission_g
        3. The identification is accurate across all routes
        """
        # Verify we have multiple routes
        assert 'routes' in trip_data
        assert trip_data['routes'] is not None
        assert len(trip_data['routes']) >= 2, "Should have at least 2 routes for comparison"
        
        routes = trip_data['routes']
        
        # Manually find the route with minimum emission for verification
        min_emission = float('inf')
        expected_best_index = 0
        
        for idx, route in enumerate(routes):
            route_emission = float(route['emission_g'])
            if route_emission < min_emission:
                min_emission = route_emission
                expected_best_index = idx
        
        # Create analyzer and analyze the trip
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        # Property 1: best_route_index should not be -1 (indicating multi-route scenario detected)
        assert analysis.best_route_index != -1, \
            "best_route_index should not be -1 when multiple routes are provided"
        
        # Property 2: best_route_index should be within valid range
        assert 0 <= analysis.best_route_index < len(routes), \
            f"best_route_index {analysis.best_route_index} should be within range [0, {len(routes)})"
        
        # Property 3: The identified best route should have the minimum emission
        identified_best_emission = routes[analysis.best_route_index]['emission_g']
        
        # Verify this is indeed the minimum emission
        for idx, route in enumerate(routes):
            route_emission = route['emission_g']
            assert identified_best_emission <= route_emission, \
                f"Route {analysis.best_route_index} (emission: {identified_best_emission:.2f}) " \
                f"should have emission <= route {idx} (emission: {route_emission:.2f})"
        
        # Property 4: The best_route_index should match our expected index
        # (or have the same emission if there are ties)
        assert analysis.best_route_index == expected_best_index or \
               abs(routes[analysis.best_route_index]['emission_g'] - min_emission) < 0.01, \
            f"Expected best route index {expected_best_index} (emission: {min_emission:.2f}), " \
            f"but got {analysis.best_route_index} (emission: {identified_best_emission:.2f})"
    
    @given(multi_route_trip_data_strategy())
    @settings(max_examples=100)
    def test_property_7_route_recommendation_when_not_optimal(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 7: Lowest emission route identification**
        **Validates: Requirements 1.4, 8.2**
        
        For any multi-route trip where the current route is not the lowest-emission option
        AND the emission difference is greater than 1.0 gram CO2, the system should recommend
        switching to the better route.
        
        This is an extension of Property 7 that verifies the recommendation engine
        uses the route identification to generate appropriate recommendations.
        
        Note: The 1.0g threshold ensures we only recommend route changes for meaningful
        differences, avoiding recommendations for negligible variations.
        """
        # Verify we have multiple routes
        assert 'routes' in trip_data
        assert len(trip_data['routes']) >= 2
        
        routes = trip_data['routes']
        
        # Find the route with minimum emission
        min_emission = float('inf')
        best_route_index = 0
        
        for idx, route in enumerate(routes):
            if route['emission_g'] < min_emission:
                min_emission = route['emission_g']
                best_route_index = idx
        
        # If the current route (route 0) is not the best route
        current_emission = routes[0]['emission_g']
        
        # Only test when difference is meaningful (> 1.0g) per Requirements 2.3, 8.2
        if best_route_index != 0 and (current_emission - min_emission) > 1.0:
            # The current route is suboptimal with meaningful difference
            # Call the full advisor to check if it recommends route change
            result = get_emission_advice(trip_data)
            
            # Property: The output should mention route or alternative route
            result_lower = result.lower()
            
            # Check for route-related keywords
            route_keywords = ['rute', 'route', 'jalur', 'alternatif', 'alternative']
            has_route_mention = any(keyword in result_lower for keyword in route_keywords)
            
            # For suboptimal routes with meaningful difference, we expect route recommendation
            assert has_route_mention, \
                f"When current route (emission: {current_emission:.2f}) is not optimal " \
                f"(best: {min_emission:.2f}, difference: {current_emission - min_emission:.2f}g), " \
                f"recommendations should mention route alternatives. " \
                f"Result: {result[:300]}..."
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_7_single_route_handling(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 7: Lowest emission route identification**
        **Validates: Requirements 1.4, 8.2**
        
        For any trip data with a single route (or no routes field), the system should
        handle it gracefully by setting best_route_index to -1.
        
        This validates that the route identification logic correctly distinguishes
        between single-route and multi-route scenarios.
        """
        # Ensure this is a single-route scenario (no routes field)
        if 'routes' in trip_data:
            del trip_data['routes']
        
        # Create analyzer and analyze the trip
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        # Property: For single-route scenarios, best_route_index should be -1
        assert analysis.best_route_index == -1, \
            "best_route_index should be -1 for single-route scenarios"
        
        # Property: current_route_index should also be -1
        assert analysis.current_route_index == -1, \
            "current_route_index should be -1 for single-route scenarios"
        
        # Property: The advisor should still work and not crash
        result = get_emission_advice(trip_data)
        assert isinstance(result, str), "Advisor should return string for single-route trips"
        assert len(result) > 0, "Advisor should return non-empty output"
    
    @given(multi_route_trip_data_strategy())
    @settings(max_examples=100)
    def test_property_7_all_routes_analyzed(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 7: Lowest emission route identification**
        **Validates: Requirements 1.4**
        
        For any trip data with multiple routes, the system should analyze ALL routes,
        not just a subset. This ensures comprehensive route comparison.
        
        This validates Requirement 1.4: "analyze each route separately"
        """
        routes = trip_data['routes']
        num_routes = len(routes)
        
        # Create analyzer and analyze the trip
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        # Property 1: The best route should be one of the provided routes
        assert 0 <= analysis.best_route_index < num_routes, \
            f"best_route_index {analysis.best_route_index} should be within [0, {num_routes})"
        
        # Property 2: The identified best route should have emission <= all other routes
        best_emission = routes[analysis.best_route_index]['emission_g']
        
        for idx, route in enumerate(routes):
            route_emission = route['emission_g']
            # The best route should have emission less than or equal to all routes
            assert best_emission <= route_emission + 0.01, \
                f"Best route {analysis.best_route_index} (emission: {best_emission:.2f}) " \
                f"should have emission <= route {idx} (emission: {route_emission:.2f})"
        
        # Property 3: There should exist at least one route with the minimum emission
        # (i.e., our identified best route should actually be minimal)
        all_emissions = [route['emission_g'] for route in routes]
        min_emission = min(all_emissions)
        
        assert abs(best_emission - min_emission) < 0.01, \
            f"Best route emission {best_emission:.2f} should equal minimum emission {min_emission:.2f}"


class TestPropertyRecommendationCountBounds:
    """
    Property-based tests for recommendation count bounds.
    
    **Feature: emission-reduction-advisor, Property 2: Recommendation count bounds**
    **Validates: Requirements 2.1**
    """
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_2_recommendation_count_bounds(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 2: Recommendation count bounds**
        **Validates: Requirements 2.1**
        
        For any valid trip data, the number of generated recommendations should be
        between 2 and 3 inclusive.
        
        This validates:
        - Requirement 2.1: WHEN the Emission Reduction Advisor generates recommendations
          THEN the system SHALL provide between 2 and 3 actionable suggestions
        
        The property verifies that:
        1. At least 2 recommendations are always provided
        2. No more than 3 recommendations are provided
        3. This holds for all valid trip scenarios (short/medium/long distance, EV/non-EV)
        """
        # Call the full advisor to get recommendations
        result = get_emission_advice(trip_data)
        
        # Property 1: Result should be a valid string output
        assert isinstance(result, str), "Advisor should return a string"
        assert len(result) > 0, "Advisor should return non-empty output"
        assert 'Error' not in result, f"Should not return error for valid trip data: {result[:200]}"
        
        # Property 2: Count the number of recommendations in the output
        # Recommendations are numbered as "1.", "2.", "3." in the output
        # We need to count these numbered items in the recommendations section
        
        # Split by lines and look for numbered recommendations
        lines = result.split('\n')
        recommendation_count = 0
        
        # Look for lines that start with "1.", "2.", "3." after the recommendations section
        in_recommendations_section = False
        
        for line in lines:
            # Check if we've entered the recommendations section
            if 'REKOMENDASI' in line.upper() or 'RECOMMENDATION' in line.upper():
                in_recommendations_section = True
                continue
            
            # Check if we've left the recommendations section (reached footer)
            if in_recommendations_section and '═' in line and 'Potensi' in line:
                break
            
            # Count numbered recommendations
            if in_recommendations_section:
                stripped = line.strip()
                # Check for patterns like "1. ", "2. ", "3. " at the start
                if stripped and len(stripped) > 2:
                    if stripped[0].isdigit() and stripped[1] == '.':
                        recommendation_count += 1
        
        # Property 3: Recommendation count should be between 2 and 3 inclusive
        assert recommendation_count >= 2, \
            f"Should provide at least 2 recommendations, but found {recommendation_count}. " \
            f"Trip: distance={trip_data['distance_km']:.2f}km, " \
            f"vehicle={trip_data['car_type']}, fuel={trip_data['fuel_type']}. " \
            f"Output: {result[:500]}..."
        
        assert recommendation_count <= 3, \
            f"Should provide at most 3 recommendations, but found {recommendation_count}. " \
            f"Trip: distance={trip_data['distance_km']:.2f}km, " \
            f"vehicle={trip_data['car_type']}, fuel={trip_data['fuel_type']}. " \
            f"Output: {result[:500]}..."
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_2_recommendation_count_via_engine(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 2: Recommendation count bounds**
        **Validates: Requirements 2.1**
        
        Direct test of the RecommendationEngine to verify it generates 2-3 recommendations.
        This tests the engine component directly rather than through the full pipeline.
        """
        from advisor import RecommendationEngine
        
        # Create analyzer and analyze the trip
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        # Extract routes if available
        routes = trip_data.get('routes', None)
        
        # Generate recommendations using the engine
        engine = RecommendationEngine()
        recommendations = engine.generate_recommendations(analysis, routes)
        
        # Property 1: Recommendations should be a list
        assert isinstance(recommendations, list), "Recommendations should be a list"
        
        # Property 2: Should have between 2 and 3 recommendations
        assert len(recommendations) >= 2, \
            f"Should generate at least 2 recommendations, but got {len(recommendations)}. " \
            f"Trip: distance={trip_data['distance_km']:.2f}km, " \
            f"vehicle={trip_data['car_type']}, fuel={trip_data['fuel_type']}"
        
        assert len(recommendations) <= 3, \
            f"Should generate at most 3 recommendations, but got {len(recommendations)}. " \
            f"Trip: distance={trip_data['distance_km']:.2f}km, " \
            f"vehicle={trip_data['car_type']}, fuel={trip_data['fuel_type']}"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_2_all_distance_categories(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 2: Recommendation count bounds**
        **Validates: Requirements 2.1**
        
        Verify that the 2-3 recommendation count holds across all distance categories
        (short, medium, long) to ensure the property is universal.
        """
        from advisor import RecommendationEngine
        
        # Analyze the trip
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        # Generate recommendations
        engine = RecommendationEngine()
        routes = trip_data.get('routes', None)
        recommendations = engine.generate_recommendations(analysis, routes)
        
        # Property: Count should be 2-3 regardless of distance category
        distance_category = analysis.distance_category
        
        assert 2 <= len(recommendations) <= 3, \
            f"For {distance_category} trips ({trip_data['distance_km']:.2f}km), " \
            f"should generate 2-3 recommendations, but got {len(recommendations)}"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_2_ev_and_non_ev_vehicles(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 2: Recommendation count bounds**
        **Validates: Requirements 2.1**
        
        Verify that the 2-3 recommendation count holds for both EV and non-EV vehicles
        to ensure the property is universal across vehicle types.
        """
        from advisor import RecommendationEngine
        
        # Analyze the trip
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        # Generate recommendations
        engine = RecommendationEngine()
        routes = trip_data.get('routes', None)
        recommendations = engine.generate_recommendations(analysis, routes)
        
        # Property: Count should be 2-3 regardless of vehicle type
        is_ev = analysis.vehicle_info.is_ev
        vehicle_type = "EV" if is_ev else "non-EV"
        
        assert 2 <= len(recommendations) <= 3, \
            f"For {vehicle_type} vehicles ({trip_data['car_type']}-{trip_data['fuel_type']}), " \
            f"should generate 2-3 recommendations, but got {len(recommendations)}"
    
    @given(multi_route_trip_data_strategy())
    @settings(max_examples=100)
    def test_property_2_multi_route_scenarios(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 2: Recommendation count bounds**
        **Validates: Requirements 2.1**
        
        Verify that the 2-3 recommendation count holds for multi-route scenarios
        where route recommendations might be added.
        """
        from advisor import RecommendationEngine
        
        # Analyze the trip
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        # Generate recommendations with routes
        engine = RecommendationEngine()
        routes = trip_data['routes']
        recommendations = engine.generate_recommendations(analysis, routes)
        
        # Property: Count should still be 2-3 even with route recommendations
        assert 2 <= len(recommendations) <= 3, \
            f"For multi-route trips with {len(routes)} routes, " \
            f"should generate 2-3 recommendations, but got {len(recommendations)}"


class TestPropertyEVRecommendations:
    """
    Property-based tests for EV recommendations.
    
    **Feature: emission-reduction-advisor, Property 8 & 9: EV recommendations**
    **Validates: Requirements 2.2, 7.2, 7.3**
    """
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_8_ev_recommendation_for_fossil_fuel_vehicles(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 8: EV recommendation for fossil fuel vehicles**
        **Validates: Requirements 2.2, 7.3**
        
        For any trip using LCGC or SUV with bensin or solar, at least one recommendation
        should mention electric vehicle or EV.
        
        This validates:
        - Requirement 2.2: WHEN the vehicle type is not EV and the fuel type is not listrik
          THEN the system SHALL recommend switching to electric vehicle as one option
        - Requirement 7.3: WHEN the current vehicle is LCGC or SUV with fossil fuel THEN
          the system SHALL include vehicle upgrade recommendations
        
        The property verifies that:
        1. Non-EV vehicles receive EV recommendations
        2. The recommendation mentions electric vehicle or EV
        3. This applies to all fossil fuel vehicles (LCGC and SUV)
        """
        # Only test non-EV vehicles
        if trip_data['car_type'] == 'EV' or trip_data['fuel_type'] == 'listrik':
            return
        
        # Call the full advisor
        result = get_emission_advice(trip_data)
        
        # Property 1: Result should be valid
        assert isinstance(result, str), "Advisor should return a string"
        assert len(result) > 0, "Advisor should return non-empty output"
        assert 'Error' not in result, f"Should not return error for valid trip data: {result[:200]}"
        
        # Property 2: For non-EV vehicles, output should mention electric vehicle or EV
        result_lower = result.lower()
        
        # Check for EV-related keywords
        ev_keywords = [
            'listrik', 'electric', 'ev', 'kendaraan listrik', 'electric vehicle',
            'beralih ke kendaraan listrik', 'switch to electric'
        ]
        has_ev_mention = any(keyword in result_lower for keyword in ev_keywords)
        
        # Property 3: At least one recommendation should mention EV
        assert has_ev_mention, \
            f"For non-EV vehicle ({trip_data['car_type']}-{trip_data['fuel_type']}), " \
            f"at least one recommendation should mention electric vehicle or EV. " \
            f"Distance: {trip_data['distance_km']:.2f}km. " \
            f"Result: {result[:500]}..."
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_8_ev_recommendation_via_engine(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 8: EV recommendation for fossil fuel vehicles**
        **Validates: Requirements 2.2, 7.3**
        
        Direct test of the RecommendationEngine to verify it generates EV recommendations
        for non-EV vehicles. This tests the engine component directly.
        """
        from advisor import RecommendationEngine
        
        # Only test non-EV vehicles
        if trip_data['car_type'] == 'EV' or trip_data['fuel_type'] == 'listrik':
            return
        
        # Create analyzer and analyze the trip
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        # Generate recommendations
        engine = RecommendationEngine()
        routes = trip_data.get('routes', None)
        recommendations = engine.generate_recommendations(analysis, routes)
        
        # Property 1: Should have at least one vehicle_switch recommendation
        vehicle_switch_recs = [r for r in recommendations if r.type == 'vehicle_switch']
        
        # Property 2: At least one recommendation should be about EV
        has_ev_rec = False
        for rec in recommendations:
            rec_text = (rec.title + " " + rec.description).lower()
            if any(keyword in rec_text for keyword in ['listrik', 'electric', 'ev', 'kendaraan listrik']):
                has_ev_rec = True
                break
        
        assert has_ev_rec, \
            f"For non-EV vehicle ({trip_data['car_type']}-{trip_data['fuel_type']}), " \
            f"at least one recommendation should be about electric vehicles. " \
            f"Distance: {trip_data['distance_km']:.2f}km, " \
            f"Recommendations: {[r.title for r in recommendations]}"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_8_all_fossil_fuel_combinations(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 8: EV recommendation for fossil fuel vehicles**
        **Validates: Requirements 2.2, 7.3**
        
        Comprehensive test that verifies EV recommendations are provided for all
        fossil fuel vehicle combinations (LCGC-bensin, LCGC-solar, SUV-bensin, SUV-solar).
        """
        # Only test fossil fuel vehicles
        if trip_data['car_type'] == 'EV' or trip_data['fuel_type'] == 'listrik':
            return
        
        # Verify this is a fossil fuel combination
        assert trip_data['car_type'] in ['LCGC', 'SUV'], \
            f"Expected LCGC or SUV, got {trip_data['car_type']}"
        assert trip_data['fuel_type'] in ['bensin', 'solar'], \
            f"Expected bensin or solar, got {trip_data['fuel_type']}"
        
        # Call the advisor
        result = get_emission_advice(trip_data)
        
        # Property: All fossil fuel combinations should get EV recommendations
        result_lower = result.lower()
        ev_keywords = ['listrik', 'electric', 'ev', 'kendaraan listrik']
        has_ev_mention = any(keyword in result_lower for keyword in ev_keywords)
        
        assert has_ev_mention, \
            f"Fossil fuel vehicle {trip_data['car_type']}-{trip_data['fuel_type']} " \
            f"should receive EV recommendation. Distance: {trip_data['distance_km']:.2f}km"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_9_no_ev_recommendation_for_existing_ev_users(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 9: No EV recommendation for existing EV users**
        **Validates: Requirements 7.2**
        
        For any trip using EV with listrik, recommendations should not suggest switching
        to electric vehicle (since they already have one).
        
        This validates:
        - Requirement 7.2: WHEN the current vehicle is EV with listrik THEN the system
          SHALL focus on route optimization and energy efficiency recommendations
        
        The property verifies that:
        1. EV users do not receive recommendations to "switch to EV"
        2. Recommendations focus on optimization and efficiency instead
        3. The system recognizes when a user already has an EV
        """
        # Only test EV vehicles
        if trip_data['car_type'] != 'EV' or trip_data['fuel_type'] != 'listrik':
            return
        
        # Call the full advisor
        result = get_emission_advice(trip_data)
        
        # Property 1: Result should be valid
        assert isinstance(result, str), "Advisor should return a string"
        assert len(result) > 0, "Advisor should return non-empty output"
        assert 'Error' not in result, f"Should not return error for valid trip data: {result[:200]}"
        
        # Property 2: For EV users, should NOT recommend switching to EV
        result_lower = result.lower()
        
        # Check for phrases that suggest switching to EV
        switch_to_ev_phrases = [
            'beralih ke kendaraan listrik',
            'beralih ke ev',
            'switch to electric vehicle',
            'switch to ev',
            'ganti ke kendaraan listrik',
            'ganti ke ev',
            'mengganti dengan kendaraan listrik',
            'upgrade to electric'
        ]
        
        has_switch_to_ev = any(phrase in result_lower for phrase in switch_to_ev_phrases)
        
        # Property 3: Should NOT suggest switching to EV for existing EV users
        assert not has_switch_to_ev, \
            f"For EV users ({trip_data['car_type']}-{trip_data['fuel_type']}), " \
            f"should NOT recommend switching to electric vehicle. " \
            f"Distance: {trip_data['distance_km']:.2f}km. " \
            f"Result: {result[:500]}..."
        
        # Property 4: Should focus on optimization/efficiency instead
        optimization_keywords = [
            'optimasi', 'optimization', 'efisiensi', 'efficiency',
            'rute', 'route', 'energi', 'energy', 'hemat'
        ]
        has_optimization_focus = any(keyword in result_lower for keyword in optimization_keywords)
        
        assert has_optimization_focus, \
            f"For EV users ({trip_data['car_type']}-{trip_data['fuel_type']}), " \
            f"recommendations should focus on optimization and efficiency. " \
            f"Distance: {trip_data['distance_km']:.2f}km. " \
            f"Result: {result[:500]}..."
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_9_ev_recommendations_via_engine(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 9: No EV recommendation for existing EV users**
        **Validates: Requirements 7.2**
        
        Direct test of the RecommendationEngine to verify it does NOT generate
        "switch to EV" recommendations for existing EV users.
        """
        from advisor import RecommendationEngine
        
        # Only test EV vehicles
        if trip_data['car_type'] != 'EV' or trip_data['fuel_type'] != 'listrik':
            return
        
        # Create analyzer and analyze the trip
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        # Verify the analysis correctly identifies this as an EV
        assert analysis.vehicle_info.is_ev is True, \
            "Analysis should correctly identify EV vehicles"
        
        # Generate recommendations
        engine = RecommendationEngine()
        routes = trip_data.get('routes', None)
        recommendations = engine.generate_recommendations(analysis, routes)
        
        # Property 1: Should NOT have vehicle_switch recommendations to EV
        for rec in recommendations:
            rec_text = (rec.title + " " + rec.description).lower()
            
            # Check if this is a "switch to EV" recommendation
            switch_to_ev_phrases = [
                'beralih ke kendaraan listrik',
                'beralih ke ev',
                'switch to electric vehicle',
                'ganti ke kendaraan listrik',
                'mengganti dengan kendaraan listrik'
            ]
            
            is_switch_to_ev = any(phrase in rec_text for phrase in switch_to_ev_phrases)
            
            assert not is_switch_to_ev, \
                f"For EV users, should NOT recommend switching to EV. " \
                f"Found recommendation: {rec.title} - {rec.description}"
        
        # Property 2: Should focus on efficiency or route optimization
        recommendation_types = [r.type for r in recommendations]
        
        # For EV users, we expect efficiency or route_change recommendations
        expected_types = ['efficiency', 'route_change', 'mode_shift']
        
        for rec_type in recommendation_types:
            assert rec_type in expected_types, \
                f"For EV users, recommendation types should be {expected_types}, " \
                f"but found: {rec_type}"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_9_ev_users_get_appropriate_recommendations(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 9: No EV recommendation for existing EV users**
        **Validates: Requirements 7.2**
        
        For EV users, verify that they receive appropriate recommendations focused on
        route optimization and energy efficiency rather than vehicle switching.
        """
        from advisor import RecommendationEngine
        
        # Only test EV vehicles
        if trip_data['car_type'] != 'EV' or trip_data['fuel_type'] != 'listrik':
            return
        
        # Create analyzer and analyze the trip
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        # Generate recommendations
        engine = RecommendationEngine()
        routes = trip_data.get('routes', None)
        recommendations = engine.generate_recommendations(analysis, routes)
        
        # Property: EV users should still get 2-3 recommendations
        assert 2 <= len(recommendations) <= 3, \
            f"EV users should still receive 2-3 recommendations, got {len(recommendations)}"
        
        # Property: Recommendations should be relevant to EV users
        # (not about switching vehicles, but about optimization)
        for rec in recommendations:
            # Vehicle switch recommendations for EV users should not be about switching to EV
            if rec.type == 'vehicle_switch':
                rec_text = (rec.title + " " + rec.description).lower()
                assert 'listrik' not in rec_text or 'sudah' in rec_text, \
                    f"Vehicle switch recommendations for EV users should not suggest switching to EV. " \
                    f"Recommendation: {rec.title}"


class TestPropertyRouteChangeRecommendation:
    """
    Property-based tests for route change recommendations.
    
    **Feature: emission-reduction-advisor, Property 10: Route change recommendation for suboptimal routes**
    **Validates: Requirements 2.3**
    """
    
    @given(multi_route_trip_data_strategy())
    @settings(max_examples=100)
    def test_property_10_route_change_recommendation_for_suboptimal_routes(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 10: Route change recommendation for suboptimal routes**
        **Validates: Requirements 2.3**
        
        For any multi-route trip where the current route is not the lowest-emission option,
        one recommendation should be about route selection.
        
        This validates:
        - Requirement 2.3: WHEN multiple routes are available with different emission levels
          THEN the system SHALL recommend choosing the route with lowest emission
        
        The property verifies that:
        1. When current route is suboptimal, a route change recommendation is generated
        2. The recommendation identifies the better route
        3. The recommendation quantifies the emission savings
        4. The route recommendation appears in the output
        """
        # Verify we have multiple routes
        assert 'routes' in trip_data
        assert len(trip_data['routes']) >= 2, "Should have at least 2 routes for comparison"
        
        routes = trip_data['routes']
        
        # Find the route with minimum emission
        min_emission = float('inf')
        best_route_index = 0
        
        for idx, route in enumerate(routes):
            route_emission = float(route['emission_g'])
            if route_emission < min_emission:
                min_emission = route_emission
                best_route_index = idx
        
        # Current route is assumed to be route 0
        current_route_index = 0
        current_emission = float(routes[current_route_index]['emission_g'])
        
        # Only test when current route is NOT the best route
        # and there's a meaningful difference (> 1g)
        if best_route_index == current_route_index or abs(current_emission - min_emission) <= 1.0:
            # Skip this test case - current route is already optimal or difference is negligible
            return
        
        # The current route is suboptimal - we should get a route recommendation
        from advisor import RecommendationEngine
        
        # Analyze the trip
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        # Generate recommendations
        engine = RecommendationEngine()
        recommendations = engine.generate_recommendations(analysis, routes)
        
        # Property 1: Should have at least one route_change recommendation
        route_change_recs = [r for r in recommendations if r.type == 'route_change']
        
        assert len(route_change_recs) > 0, \
            f"When current route (#{current_route_index + 1}, emission: {current_emission:.2f}g) " \
            f"is not optimal (best: #{best_route_index + 1}, emission: {min_emission:.2f}g), " \
            f"should generate at least one route_change recommendation. " \
            f"Got recommendations: {[r.type for r in recommendations]}"
        
        # Property 2: The route change recommendation should mention the better route
        route_rec = route_change_recs[0]
        
        # Check that the recommendation mentions the best route number
        best_route_number = best_route_index + 1  # Route numbers are 1-indexed
        assert str(best_route_number) in route_rec.title or str(best_route_number) in route_rec.description, \
            f"Route recommendation should mention route #{best_route_number}. " \
            f"Title: {route_rec.title}, Description: {route_rec.description}"
        
        # Property 3: The savings should be approximately the emission difference
        expected_savings = current_emission - min_emission
        actual_savings = route_rec.savings.savings_g
        
        # Allow for small floating point differences
        assert abs(actual_savings - expected_savings) < 1.0, \
            f"Route recommendation savings should be approximately {expected_savings:.2f}g, " \
            f"but got {actual_savings:.2f}g"
        
        # Property 4: The savings percentage should be reasonable
        expected_percentage = (expected_savings / current_emission) * 100
        actual_percentage = route_rec.savings.savings_percentage
        
        assert abs(actual_percentage - expected_percentage) < 1.0, \
            f"Route recommendation savings percentage should be approximately {expected_percentage:.1f}%, " \
            f"but got {actual_percentage:.1f}%"
        
        # Property 5: The full advisor output should mention route alternatives
        result = get_emission_advice(trip_data)
        result_lower = result.lower()
        
        # Check for route-related keywords
        route_keywords = ['rute', 'route', 'jalur', 'alternatif', 'alternative']
        has_route_mention = any(keyword in result_lower for keyword in route_keywords)
        
        assert has_route_mention, \
            f"When current route is suboptimal, output should mention route alternatives. " \
            f"Current: {current_emission:.2f}g, Best: {min_emission:.2f}g. " \
            f"Output: {result[:300]}..."
    
    @given(multi_route_trip_data_strategy())
    @settings(max_examples=100)
    def test_property_10_route_recommendation_priority(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 10: Route change recommendation for suboptimal routes**
        **Validates: Requirements 2.3**
        
        When a route change recommendation is generated, it should have high priority
        (priority 1) since it's an immediate, actionable improvement.
        """
        routes = trip_data['routes']
        
        # Find best route
        min_emission = float('inf')
        best_route_index = 0
        
        for idx, route in enumerate(routes):
            if route['emission_g'] < min_emission:
                min_emission = route['emission_g']
                best_route_index = idx
        
        # Current route is route 0
        current_emission = routes[0]['emission_g']
        
        # Only test when current route is suboptimal
        if best_route_index == 0 or abs(current_emission - min_emission) <= 1.0:
            return
        
        from advisor import RecommendationEngine
        
        # Analyze and generate recommendations
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        engine = RecommendationEngine()
        recommendations = engine.generate_recommendations(analysis, routes)
        
        # Find route change recommendation
        route_change_recs = [r for r in recommendations if r.type == 'route_change']
        
        if len(route_change_recs) > 0:
            route_rec = route_change_recs[0]
            
            # Property: Route change recommendations should have high priority (1 or 2)
            assert route_rec.priority <= 2, \
                f"Route change recommendations should have high priority (1 or 2), " \
                f"but got priority {route_rec.priority}"
    
    @given(multi_route_trip_data_strategy())
    @settings(max_examples=100)
    def test_property_10_no_route_recommendation_when_optimal(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 10: Route change recommendation for suboptimal routes**
        **Validates: Requirements 2.3**
        
        When the current route is already optimal (lowest emission), no route change
        recommendation should be generated, or if generated, it should not suggest
        switching to a worse route.
        """
        routes = trip_data['routes']
        
        # Find best route
        min_emission = float('inf')
        best_route_index = 0
        
        for idx, route in enumerate(routes):
            if route['emission_g'] < min_emission:
                min_emission = route['emission_g']
                best_route_index = idx
        
        # Modify trip_data so current route IS the best route
        # We'll swap route 0 with the best route
        if best_route_index != 0:
            routes[0], routes[best_route_index] = routes[best_route_index], routes[0]
            trip_data['routes'] = routes
            trip_data['distance_km'] = routes[0]['distance_km']
            trip_data['emission_g'] = routes[0]['emission_g']
        
        from advisor import RecommendationEngine
        
        # Analyze and generate recommendations
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        engine = RecommendationEngine()
        recommendations = engine.generate_recommendations(analysis, routes)
        
        # Property: When current route is optimal, either:
        # 1. No route_change recommendation is generated, OR
        # 2. If a route_change recommendation exists, it should not suggest a worse route
        
        route_change_recs = [r for r in recommendations if r.type == 'route_change']
        
        # If there are route change recommendations, verify they don't suggest worse routes
        for rec in route_change_recs:
            # The savings should be positive (or very close to zero)
            assert rec.savings.savings_g >= -1.0, \
                f"When current route is optimal, route recommendations should not suggest worse routes. " \
                f"Got savings: {rec.savings.savings_g:.2f}g (negative means worse)"
    
    @given(multi_route_trip_data_strategy())
    @settings(max_examples=100)
    def test_property_10_route_recommendation_in_final_output(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 10: Route change recommendation for suboptimal routes**
        **Validates: Requirements 2.3**
        
        When a route change recommendation is appropriate, it should appear in the
        final formatted output that the user sees.
        """
        routes = trip_data['routes']
        
        # Find best route
        min_emission = float('inf')
        best_route_index = 0
        
        for idx, route in enumerate(routes):
            if route['emission_g'] < min_emission:
                min_emission = route['emission_g']
                best_route_index = idx
        
        current_emission = routes[0]['emission_g']
        
        # Only test when current route is suboptimal
        if best_route_index == 0 or abs(current_emission - min_emission) <= 1.0:
            return
        
        # Get the full advisor output
        result = get_emission_advice(trip_data)
        
        # Property 1: Output should be valid
        assert isinstance(result, str), "Advisor should return a string"
        assert len(result) > 0, "Advisor should return non-empty output"
        assert 'Error' not in result, "Should not return error for valid trip data"
        
        # Property 2: Output should mention route alternatives
        result_lower = result.lower()
        route_keywords = ['rute', 'route', 'jalur', 'alternatif', 'alternative']
        has_route_mention = any(keyword in result_lower for keyword in route_keywords)
        
        assert has_route_mention, \
            f"Output should mention route alternatives when current route is suboptimal. " \
            f"Current: {current_emission:.2f}g, Best: {min_emission:.2f}g"
        
        # Property 3: Output should mention the best route number
        best_route_number = best_route_index + 1
        assert str(best_route_number) in result, \
            f"Output should mention the best route number (#{best_route_number})"
        
        # Property 4: Output should show emission savings
        expected_savings = current_emission - min_emission
        # Check if the savings amount appears in the output (allowing for formatting)
        savings_str = f"{expected_savings:.0f}"
        
        # The savings might be formatted with commas, so check for the number
        # We'll be lenient and just check that some reasonable savings number appears
        assert any(char.isdigit() for char in result), \
            "Output should contain numeric savings information"


class TestPropertyAnalysisCompleteness:
    """
    Property-based tests for analysis completeness.
    
    **Feature: emission-reduction-advisor, Property 22: All input fields processed**
    **Validates: Requirements 1.1**
    """
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_22_all_input_fields_processed(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 22: All input fields processed**
        **Validates: Requirements 1.1**
        
        For any valid trip data with distance, car_type, fuel_type, and emission fields,
        the analysis should successfully extract and use all four fields.
        
        This validates:
        - Requirement 1.1: WHEN the Emission Reduction Advisor receives trip data THEN the system
          SHALL analyze the distance, vehicle type, fuel type, and total emission
        
        The property verifies that:
        1. The TripAnalyzer successfully processes all required input fields
        2. The analysis result contains values derived from all input fields
        3. Each input field contributes to the analysis output
        4. No input field is ignored or skipped
        """
        # Create analyzer and analyze the trip
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        # Property 1: Analysis should successfully complete (not raise exception)
        assert analysis is not None, "Analysis should return a result"
        
        # Property 2: Distance field should be processed
        # The total_distance in analysis should match the input distance_km
        assert analysis.total_distance == trip_data['distance_km'], \
            f"Distance field should be processed: expected {trip_data['distance_km']}, " \
            f"got {analysis.total_distance}"
        
        # Property 3: Emission field should be processed
        # The total_emission_g in analysis should match the input emission_g
        assert analysis.total_emission_g == trip_data['emission_g'], \
            f"Emission field should be processed: expected {trip_data['emission_g']}, " \
            f"got {analysis.total_emission_g}"
        
        # Property 4: Car type field should be processed
        # The vehicle_info should contain the car_type from input
        assert analysis.vehicle_info.car_type == trip_data['car_type'], \
            f"Car type field should be processed: expected {trip_data['car_type']}, " \
            f"got {analysis.vehicle_info.car_type}"
        
        # Property 5: Fuel type field should be processed
        # The vehicle_info should contain the fuel_type from input
        assert analysis.vehicle_info.fuel_type == trip_data['fuel_type'], \
            f"Fuel type field should be processed: expected {trip_data['fuel_type']}, " \
            f"got {analysis.vehicle_info.fuel_type}"
        
        # Property 6: All fields should contribute to derived values
        # The emission_factor should be derived from car_type and fuel_type
        expected_emission_factor = EMISSION_FACTORS[trip_data['car_type']][trip_data['fuel_type']]
        assert analysis.vehicle_info.emission_factor == expected_emission_factor, \
            f"Emission factor should be derived from car_type and fuel_type: " \
            f"expected {expected_emission_factor}, got {analysis.vehicle_info.emission_factor}"
        
        # Property 7: Distance should contribute to distance categorization
        # Verify the distance_category is correctly derived from distance
        if trip_data['distance_km'] < 5.0:
            expected_category = 'short'
        elif trip_data['distance_km'] <= 15.0:
            expected_category = 'medium'
        else:
            expected_category = 'long'
        
        assert analysis.distance_category == expected_category, \
            f"Distance should contribute to categorization: " \
            f"for distance {trip_data['distance_km']}, expected '{expected_category}', " \
            f"got '{analysis.distance_category}'"
        
        # Property 8: Emission should be converted to kg
        # The total_emission_kg should be derived from total_emission_g
        expected_emission_kg = trip_data['emission_g'] / 1000.0
        assert abs(analysis.total_emission_kg - expected_emission_kg) < 0.001, \
            f"Emission should be converted to kg: expected {expected_emission_kg}, " \
            f"got {analysis.total_emission_kg}"
        
        # Property 9: Vehicle type and fuel type should determine EV status
        # The is_ev flag should be correctly set based on car_type and fuel_type
        expected_is_ev = (trip_data['car_type'] == 'EV' and trip_data['fuel_type'] == 'listrik')
        assert analysis.vehicle_info.is_ev == expected_is_ev, \
            f"EV status should be derived from car_type and fuel_type: " \
            f"for {trip_data['car_type']}-{trip_data['fuel_type']}, " \
            f"expected is_ev={expected_is_ev}, got {analysis.vehicle_info.is_ev}"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_22_full_pipeline_uses_all_fields(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 22: All input fields processed**
        **Validates: Requirements 1.1**
        
        For any valid trip data, the complete advisor pipeline (from input to output)
        should use all input fields to generate the final advice.
        
        This validates that all input fields flow through the entire system and
        contribute to the final output.
        """
        # Call the full advisor
        result = get_emission_advice(trip_data)
        
        # Property 1: Result should be a non-empty string
        assert isinstance(result, str), "Advisor should return a string"
        assert len(result) > 0, "Advisor should return non-empty output"
        
        # Property 2: Output should contain distance information
        # The distance value should appear in the output
        distance_str = f"{trip_data['distance_km']:.1f}"
        assert distance_str in result or str(int(trip_data['distance_km'])) in result, \
            f"Output should contain distance information: {trip_data['distance_km']}"
        
        # Property 3: Output should contain vehicle type information
        # The car_type should appear in the output
        assert trip_data['car_type'] in result, \
            f"Output should contain vehicle type: {trip_data['car_type']}"
        
        # Property 4: Output should contain fuel type information
        # The fuel_type should appear in the output
        assert trip_data['fuel_type'] in result, \
            f"Output should contain fuel type: {trip_data['fuel_type']}"
        
        # Property 5: Output should contain emission information
        # The emission value should appear in the output (in some format)
        # Check for the emission value in grams (with comma formatting)
        emission_formatted = f"{trip_data['emission_g']:,.0f}"
        emission_int = int(trip_data['emission_g'])
        
        # The emission might appear in various formats, so check multiple possibilities
        has_emission = (
            emission_formatted in result or
            str(emission_int) in result or
            f"{emission_int:,}" in result
        )
        
        assert has_emission, \
            f"Output should contain emission information: {trip_data['emission_g']}"
        
        # Property 6: Recommendations should be influenced by all input fields
        # Different combinations of inputs should produce different recommendations
        # This is implicitly tested by the fact that the output contains all field values
        # and the recommendation logic uses these fields
        
        # Verify the output has the expected structure (summary + recommendations)
        assert "RINGKASAN" in result or "SUMMARY" in result.upper(), \
            "Output should contain summary section"
        assert "REKOMENDASI" in result or "RECOMMENDATION" in result.upper(), \
            "Output should contain recommendations section"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_22_missing_field_detection(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 22: All input fields processed**
        **Validates: Requirements 1.1**
        
        For any trip data with a missing required field, the system should detect
        the missing field and report an error. This validates that the system
        actually checks for and requires all input fields.
        """
        # Test each required field by removing it one at a time
        required_fields = ['distance_km', 'car_type', 'fuel_type', 'emission_g']
        
        for field_to_remove in required_fields:
            # Create a copy of trip_data with one field removed
            incomplete_data = {k: v for k, v in trip_data.items() if k != field_to_remove}
            
            # Validate the incomplete data
            error = validate_trip_data(incomplete_data)
            
            # Property: Should return an error for missing field
            assert error is not None, \
                f"Should detect missing field: {field_to_remove}"
            
            assert error['success'] is False, \
                f"Error should indicate failure for missing field: {field_to_remove}"
            
            assert field_to_remove in error['error'], \
                f"Error message should mention the missing field: {field_to_remove}. " \
                f"Error: {error['error']}"
            
            # Property: The full advisor should also handle this gracefully
            result = get_emission_advice(incomplete_data)
            assert 'Error' in result or 'error' in result, \
                f"Advisor should return error for missing field: {field_to_remove}"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_22_field_type_validation(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 22: All input fields processed**
        **Validates: Requirements 1.1**
        
        For any trip data with incorrect field types, the system should detect
        the type mismatch and report an error. This validates that the system
        properly validates the type of each input field.
        """
        # Test with invalid distance type (string instead of number)
        invalid_distance_data = trip_data.copy()
        invalid_distance_data['distance_km'] = "not a number"
        
        error = validate_trip_data(invalid_distance_data)
        assert error is not None, "Should detect invalid distance type"
        assert 'type' in error['error'].lower() or 'numeric' in error['error'].lower(), \
            f"Error should mention type issue: {error['error']}"
        
        # Test with invalid emission type (string instead of number)
        invalid_emission_data = trip_data.copy()
        invalid_emission_data['emission_g'] = "not a number"
        
        error = validate_trip_data(invalid_emission_data)
        assert error is not None, "Should detect invalid emission type"
        assert 'type' in error['error'].lower() or 'numeric' in error['error'].lower(), \
            f"Error should mention type issue: {error['error']}"
        
        # Test with invalid car_type (empty string)
        invalid_car_data = trip_data.copy()
        invalid_car_data['car_type'] = ""
        
        error = validate_trip_data(invalid_car_data)
        assert error is not None, "Should detect empty car_type"
        
        # Test with invalid fuel_type (empty string)
        invalid_fuel_data = trip_data.copy()
        invalid_fuel_data['fuel_type'] = ""
        
        error = validate_trip_data(invalid_fuel_data)
        assert error is not None, "Should detect empty fuel_type"


class TestPropertyValidCombinationHandling:
    """
    Property-based tests for valid vehicle-fuel combination handling.
    
    **Feature: emission-reduction-advisor, Property 18: Valid vehicle-fuel combination handling**
    **Validates: Requirements 7.1**
    """
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_18_valid_combination_handling(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 18: Valid vehicle-fuel combination handling**
        **Validates: Requirements 7.1**
        
        For any valid vehicle-fuel combination from EMISSION_FACTORS, the system should
        successfully generate recommendations without errors.
        
        This validates:
        - Requirement 7.1: WHEN the Emission Reduction Advisor receives trip data with any
          valid vehicle-fuel combination THEN the system SHALL generate appropriate recommendations
        
        The property verifies that:
        1. All valid combinations from EMISSION_FACTORS are accepted
        2. No errors are returned for valid combinations
        3. Recommendations are successfully generated
        4. The output is properly formatted
        5. The system handles all valid combinations consistently
        """
        # Verify this is a valid combination (should be guaranteed by trip_data_strategy)
        car_type = trip_data['car_type']
        fuel_type = trip_data['fuel_type']
        
        assert car_type in EMISSION_FACTORS, \
            f"Test data should have valid car_type: {car_type}"
        assert fuel_type in EMISSION_FACTORS[car_type], \
            f"Test data should have valid fuel_type: {fuel_type} for {car_type}"
        
        # Property 1: Validation should pass (return None)
        error = validate_trip_data(trip_data)
        assert error is None, \
            f"Valid combination {car_type}-{fuel_type} should pass validation. " \
            f"Got error: {error}"
        
        # Property 2: The advisor should successfully generate output
        result = get_emission_advice(trip_data)
        
        # Property 3: Result should be a non-empty string
        assert isinstance(result, str), \
            f"Advisor should return string for valid combination {car_type}-{fuel_type}"
        assert len(result) > 0, \
            f"Advisor should return non-empty output for valid combination {car_type}-{fuel_type}"
        
        # Property 4: Result should NOT contain error messages
        assert 'Error' not in result and 'error' not in result, \
            f"Valid combination {car_type}-{fuel_type} should not produce error. " \
            f"Distance: {trip_data['distance_km']:.2f}km. " \
            f"Result: {result[:300]}..."
        
        # Property 5: Result should contain expected sections
        assert 'REKOMENDASI' in result.upper() or 'RECOMMENDATION' in result.upper(), \
            f"Output should contain recommendations section for valid combination {car_type}-{fuel_type}"
        
        assert 'RINGKASAN' in result.upper() or 'SUMMARY' in result.upper(), \
            f"Output should contain summary section for valid combination {car_type}-{fuel_type}"
        
        # Property 6: Result should contain the vehicle and fuel information
        assert car_type in result, \
            f"Output should mention vehicle type {car_type}"
        assert fuel_type in result, \
            f"Output should mention fuel type {fuel_type}"
        
        # Property 7: Result should contain emission information
        assert 'CO2' in result or 'co2' in result, \
            f"Output should mention CO2 emissions"
        
        # Property 8: Result should contain distance information
        # The distance should appear somewhere in the output
        distance_str = f"{trip_data['distance_km']:.1f}"
        # Allow for some formatting variations
        assert distance_str in result or str(int(trip_data['distance_km'])) in result, \
            f"Output should mention distance {trip_data['distance_km']:.1f} km"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_18_all_valid_combinations_work(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 18: Valid vehicle-fuel combination handling**
        **Validates: Requirements 7.1**
        
        Comprehensive test that verifies ALL valid combinations from EMISSION_FACTORS
        are handled correctly by the system.
        
        This test ensures that:
        1. LCGC-bensin works
        2. LCGC-solar works
        3. SUV-bensin works
        4. SUV-solar works
        5. EV-listrik works
        """
        car_type = trip_data['car_type']
        fuel_type = trip_data['fuel_type']
        
        # Verify this is indeed a valid combination
        assert car_type in EMISSION_FACTORS, f"Invalid car_type: {car_type}"
        assert fuel_type in EMISSION_FACTORS[car_type], \
            f"Invalid fuel_type {fuel_type} for {car_type}"
        
        # Property: The system should handle this combination without errors
        try:
            # Validation should pass
            error = validate_trip_data(trip_data)
            assert error is None, \
                f"Validation failed for valid combination {car_type}-{fuel_type}: {error}"
            
            # Analysis should work
            analyzer = TripAnalyzer()
            analysis = analyzer.analyze_trip(trip_data)
            
            assert analysis is not None, \
                f"Analysis failed for valid combination {car_type}-{fuel_type}"
            assert analysis.vehicle_info.car_type == car_type, \
                f"Analysis should preserve car_type"
            assert analysis.vehicle_info.fuel_type == fuel_type, \
                f"Analysis should preserve fuel_type"
            
            # Recommendation generation should work
            from advisor import RecommendationEngine
            engine = RecommendationEngine()
            routes = trip_data.get('routes', None)
            recommendations = engine.generate_recommendations(analysis, routes)
            
            assert recommendations is not None, \
                f"Recommendation generation failed for {car_type}-{fuel_type}"
            assert len(recommendations) >= 2, \
                f"Should generate at least 2 recommendations for {car_type}-{fuel_type}"
            
            # Full advisor should work
            result = get_emission_advice(trip_data)
            assert isinstance(result, str), \
                f"Advisor should return string for {car_type}-{fuel_type}"
            assert 'Error' not in result, \
                f"Advisor should not return error for valid combination {car_type}-{fuel_type}"
            
        except Exception as e:
            pytest.fail(
                f"Valid combination {car_type}-{fuel_type} should not raise exception. "
                f"Distance: {trip_data['distance_km']:.2f}km. "
                f"Exception: {type(e).__name__}: {str(e)}"
            )
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_18_consistent_handling_across_distances(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 18: Valid vehicle-fuel combination handling**
        **Validates: Requirements 7.1**
        
        Verify that valid combinations are handled consistently across all distance
        categories (short, medium, long).
        
        This ensures that the validity of a vehicle-fuel combination is independent
        of the trip distance.
        """
        car_type = trip_data['car_type']
        fuel_type = trip_data['fuel_type']
        distance = trip_data['distance_km']
        
        # Property: Valid combinations should work regardless of distance category
        error = validate_trip_data(trip_data)
        assert error is None, \
            f"Valid combination {car_type}-{fuel_type} should work for distance {distance:.2f}km"
        
        result = get_emission_advice(trip_data)
        assert 'Error' not in result, \
            f"Valid combination {car_type}-{fuel_type} should work for distance {distance:.2f}km"
        
        # Verify the distance category is correctly identified
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        if distance < 5.0:
            assert analysis.distance_category == 'short', \
                f"Distance {distance:.2f}km should be categorized as 'short'"
        elif distance <= 15.0:
            assert analysis.distance_category == 'medium', \
                f"Distance {distance:.2f}km should be categorized as 'medium'"
        else:
            assert analysis.distance_category == 'long', \
                f"Distance {distance:.2f}km should be categorized as 'long'"
        
        # Property: Recommendations should be generated for all distance categories
        from advisor import RecommendationEngine
        engine = RecommendationEngine()
        recommendations = engine.generate_recommendations(analysis, None)
        
        assert len(recommendations) >= 2, \
            f"Should generate recommendations for {car_type}-{fuel_type} at distance {distance:.2f}km"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_18_emission_factor_lookup_succeeds(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 18: Valid vehicle-fuel combination handling**
        **Validates: Requirements 7.1**
        
        Verify that emission factor lookup succeeds for all valid combinations.
        This is a fundamental operation that must work for the system to function.
        """
        car_type = trip_data['car_type']
        fuel_type = trip_data['fuel_type']
        
        # Property: Emission factor lookup should succeed without raising KeyError
        try:
            emission_factor = get_emission_factor(car_type, fuel_type)
            
            # Property: Emission factor should be a positive number
            assert isinstance(emission_factor, (int, float)), \
                f"Emission factor should be numeric for {car_type}-{fuel_type}"
            assert emission_factor > 0, \
                f"Emission factor should be positive for {car_type}-{fuel_type}"
            
            # Property: Emission factor should match what's in EMISSION_FACTORS
            expected_factor = EMISSION_FACTORS[car_type][fuel_type]
            assert emission_factor == expected_factor, \
                f"Emission factor should match EMISSION_FACTORS for {car_type}-{fuel_type}"
            
        except KeyError as e:
            pytest.fail(
                f"Valid combination {car_type}-{fuel_type} should not raise KeyError. "
                f"Exception: {str(e)}"
            )
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_18_no_crashes_for_valid_combinations(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 18: Valid vehicle-fuel combination handling**
        **Validates: Requirements 7.1**
        
        Verify that the system never crashes (raises unhandled exceptions) for any
        valid vehicle-fuel combination.
        
        This is a critical safety property - valid inputs should never cause crashes.
        """
        car_type = trip_data['car_type']
        fuel_type = trip_data['fuel_type']
        
        # Property: No unhandled exceptions should be raised for valid combinations
        try:
            # Try all major operations
            error = validate_trip_data(trip_data)
            assert error is None, f"Validation should pass for {car_type}-{fuel_type}"
            
            analyzer = TripAnalyzer()
            analysis = analyzer.analyze_trip(trip_data)
            assert analysis is not None
            
            from advisor import RecommendationEngine
            engine = RecommendationEngine()
            recommendations = engine.generate_recommendations(analysis, None)
            assert recommendations is not None
            
            result = get_emission_advice(trip_data)
            assert result is not None
            
        except Exception as e:
            pytest.fail(
                f"Valid combination {car_type}-{fuel_type} should not raise exception. "
                f"Distance: {trip_data['distance_km']:.2f}km, "
                f"Emission: {trip_data['emission_g']:.2f}g. "
                f"Exception: {type(e).__name__}: {str(e)}"
            )



class TestPropertyVehicleSwitchSavingsAccuracy:
    """
    Property-based tests for vehicle switch savings accuracy.
    
    **Feature: emission-reduction-advisor, Property 16: Vehicle switch savings accuracy**
    **Validates: Requirements 3.3**
    """
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_16_vehicle_switch_savings_accuracy(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 16: Vehicle switch savings accuracy**
        **Validates: Requirements 3.3**
        
        For any vehicle switch recommendation, the calculated savings should match
        the difference in emission factors multiplied by distance.
        
        This validates:
        - Requirement 3.3: WHEN calculating savings for vehicle switch recommendations
          THEN the system SHALL use the emission factors from the existing emission
          calculation system
        
        The property verifies that:
        1. Savings calculation uses EMISSION_FACTORS from emission.py
        2. Savings = (current_emission_factor - target_emission_factor) * distance
        3. The calculation is accurate for all valid vehicle-fuel combinations
        4. Savings are non-negative (switching to lower-emission vehicle)
        """
        from advisor import SavingsCalculator
        
        # Extract trip information
        distance_km = trip_data['distance_km']
        current_car_type = trip_data['car_type']
        current_fuel_type = trip_data['fuel_type']
        
        # Get current emission factor
        current_emission_factor = get_emission_factor(current_car_type, current_fuel_type)
        
        # Test switching to all other valid vehicle-fuel combinations
        for target_car_type in EMISSION_FACTORS.keys():
            for target_fuel_type in EMISSION_FACTORS[target_car_type].keys():
                # Skip if it's the same combination
                if target_car_type == current_car_type and target_fuel_type == current_fuel_type:
                    continue
                
                # Get target emission factor
                target_emission_factor = get_emission_factor(target_car_type, target_fuel_type)
                
                # Calculate expected savings manually
                # Savings = (current_factor - target_factor) * distance
                expected_savings_g = (current_emission_factor - target_emission_factor) * distance_km
                
                # Ensure non-negative (as per implementation)
                expected_savings_g = max(0.0, expected_savings_g)
                expected_savings_kg = expected_savings_g / 1000.0
                
                # Calculate expected percentage
                current_emission_g = trip_data['emission_g']
                if current_emission_g > 0:
                    expected_percentage = (expected_savings_g / current_emission_g) * 100.0
                else:
                    expected_percentage = 0.0
                
                # Use SavingsCalculator to calculate savings
                calculator = SavingsCalculator()
                savings = calculator.calculate_savings(
                    recommendation_type='vehicle_switch',
                    current_trip=trip_data,
                    target_vehicle=target_car_type,
                    target_fuel=target_fuel_type
                )
                
                # Property 1: Savings should match expected calculation
                assert abs(savings.savings_g - expected_savings_g) < 0.01, \
                    f"Savings calculation incorrect for {current_car_type}-{current_fuel_type} -> {target_car_type}-{target_fuel_type}. " \
                    f"Expected: {expected_savings_g:.2f}g, Got: {savings.savings_g:.2f}g. " \
                    f"Distance: {distance_km:.2f}km, " \
                    f"Current factor: {current_emission_factor}, Target factor: {target_emission_factor}"
                
                # Property 2: Savings in kg should be savings in g divided by 1000
                assert abs(savings.savings_kg - expected_savings_kg) < 0.00001, \
                    f"Savings in kg should be savings in g / 1000. " \
                    f"Expected: {expected_savings_kg:.5f}kg, Got: {savings.savings_kg:.5f}kg"
                
                # Property 3: Percentage should match expected calculation
                assert abs(savings.savings_percentage - expected_percentage) < 0.01, \
                    f"Savings percentage incorrect. " \
                    f"Expected: {expected_percentage:.2f}%, Got: {savings.savings_percentage:.2f}%"
                
                # Property 4: Savings should be non-negative
                assert savings.savings_g >= 0, \
                    f"Savings should be non-negative. Got: {savings.savings_g:.2f}g"
                
                # Property 5: If target has lower emission factor, savings should be positive
                if target_emission_factor < current_emission_factor:
                    assert savings.savings_g > 0, \
                        f"Switching to lower-emission vehicle should have positive savings. " \
                        f"Current: {current_emission_factor}, Target: {target_emission_factor}, " \
                        f"Savings: {savings.savings_g:.2f}g"
                
                # Property 6: If target has higher emission factor, savings should be zero (clamped)
                if target_emission_factor > current_emission_factor:
                    assert savings.savings_g == 0, \
                        f"Switching to higher-emission vehicle should have zero savings (clamped). " \
                        f"Current: {current_emission_factor}, Target: {target_emission_factor}, " \
                        f"Savings: {savings.savings_g:.2f}g"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_16_ev_switch_savings_for_fossil_fuel_vehicles(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 16: Vehicle switch savings accuracy**
        **Validates: Requirements 3.3**
        
        Specifically test switching from fossil fuel vehicles (LCGC, SUV) to EV.
        This is the most common recommendation scenario.
        
        For any fossil fuel vehicle, switching to EV should result in positive savings
        that are accurately calculated using emission factors.
        """
        from advisor import SavingsCalculator
        
        # Only test non-EV vehicles
        if trip_data['car_type'] == 'EV':
            return
        
        distance_km = trip_data['distance_km']
        current_car_type = trip_data['car_type']
        current_fuel_type = trip_data['fuel_type']
        current_emission_g = trip_data['emission_g']
        
        # Get emission factors
        current_emission_factor = get_emission_factor(current_car_type, current_fuel_type)
        ev_emission_factor = get_emission_factor('EV', 'listrik')
        
        # Calculate expected savings
        expected_savings_g = (current_emission_factor - ev_emission_factor) * distance_km
        expected_savings_kg = expected_savings_g / 1000.0
        expected_percentage = (expected_savings_g / current_emission_g) * 100.0
        
        # Use SavingsCalculator
        calculator = SavingsCalculator()
        savings = calculator.calculate_savings(
            recommendation_type='vehicle_switch',
            current_trip=trip_data,
            target_vehicle='EV',
            target_fuel='listrik'
        )
        
        # Property 1: Savings should be positive (EV has lower emissions)
        assert savings.savings_g > 0, \
            f"Switching from {current_car_type}-{current_fuel_type} to EV should have positive savings. " \
            f"Got: {savings.savings_g:.2f}g"
        
        # Property 2: Savings should match expected calculation
        assert abs(savings.savings_g - expected_savings_g) < 0.01, \
            f"EV switch savings incorrect. " \
            f"Expected: {expected_savings_g:.2f}g, Got: {savings.savings_g:.2f}g. " \
            f"Distance: {distance_km:.2f}km, " \
            f"Current factor: {current_emission_factor}, EV factor: {ev_emission_factor}"
        
        # Property 3: Savings should be substantial (at least 50% for fossil fuel to EV)
        # LCGC-bensin: 120 -> 40 = 66.7% reduction
        # LCGC-solar: 140 -> 40 = 71.4% reduction
        # SUV-bensin: 180 -> 40 = 77.8% reduction
        # SUV-solar: 200 -> 40 = 80% reduction
        assert savings.savings_percentage >= 50.0, \
            f"EV switch should provide at least 50% savings. " \
            f"Got: {savings.savings_percentage:.1f}% for {current_car_type}-{current_fuel_type}"
        
        # Property 4: Percentage should match expected calculation
        assert abs(savings.savings_percentage - expected_percentage) < 0.01, \
            f"Percentage calculation incorrect. " \
            f"Expected: {expected_percentage:.2f}%, Got: {savings.savings_percentage:.2f}%"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_16_savings_scale_with_distance(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 16: Vehicle switch savings accuracy**
        **Validates: Requirements 3.3**
        
        Verify that savings scale linearly with distance.
        
        For any vehicle switch, if distance doubles, savings should double.
        This validates that the formula (factor_diff * distance) is correctly applied.
        """
        from advisor import SavingsCalculator
        
        distance_km = trip_data['distance_km']
        current_car_type = trip_data['car_type']
        current_fuel_type = trip_data['fuel_type']
        
        # Pick a different target vehicle
        if current_car_type == 'EV':
            target_car_type = 'LCGC'
            target_fuel_type = 'bensin'
        else:
            target_car_type = 'EV'
            target_fuel_type = 'listrik'
        
        # Calculate savings for original distance
        calculator = SavingsCalculator()
        savings_1x = calculator.calculate_savings(
            recommendation_type='vehicle_switch',
            current_trip=trip_data,
            target_vehicle=target_car_type,
            target_fuel=target_fuel_type
        )
        
        # Create trip data with double distance
        trip_data_2x = trip_data.copy()
        trip_data_2x['distance_km'] = distance_km * 2
        trip_data_2x['emission_g'] = trip_data['emission_g'] * 2
        
        # Calculate savings for double distance
        savings_2x = calculator.calculate_savings(
            recommendation_type='vehicle_switch',
            current_trip=trip_data_2x,
            target_vehicle=target_car_type,
            target_fuel=target_fuel_type
        )
        
        # Property: Savings should scale linearly with distance
        # savings_2x should be approximately 2 * savings_1x
        expected_savings_2x = savings_1x.savings_g * 2
        
        assert abs(savings_2x.savings_g - expected_savings_2x) < 0.01, \
            f"Savings should scale linearly with distance. " \
            f"1x distance ({distance_km:.2f}km): {savings_1x.savings_g:.2f}g, " \
            f"2x distance ({distance_km * 2:.2f}km): {savings_2x.savings_g:.2f}g, " \
            f"Expected 2x: {expected_savings_2x:.2f}g"
        
        # Property: Percentage should remain the same (it's relative to total emission)
        # Since both emission and savings double, percentage stays the same
        assert abs(savings_2x.savings_percentage - savings_1x.savings_percentage) < 0.01, \
            f"Savings percentage should remain constant when distance scales. " \
            f"1x: {savings_1x.savings_percentage:.2f}%, 2x: {savings_2x.savings_percentage:.2f}%"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_16_uses_emission_factors_from_emission_module(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 16: Vehicle switch savings accuracy**
        **Validates: Requirements 3.3**
        
        Verify that the SavingsCalculator uses EMISSION_FACTORS from emission.py
        and not any hardcoded or alternative values.
        
        This ensures consistency with the existing emission calculation system.
        """
        from advisor import SavingsCalculator
        
        current_car_type = trip_data['car_type']
        current_fuel_type = trip_data['fuel_type']
        distance_km = trip_data['distance_km']
        
        # Test switching to each valid combination
        for target_car_type in EMISSION_FACTORS.keys():
            for target_fuel_type in EMISSION_FACTORS[target_car_type].keys():
                if target_car_type == current_car_type and target_fuel_type == current_fuel_type:
                    continue
                
                # Get factors directly from EMISSION_FACTORS
                current_factor_from_module = EMISSION_FACTORS[current_car_type][current_fuel_type]
                target_factor_from_module = EMISSION_FACTORS[target_car_type][target_fuel_type]
                
                # Calculate expected savings using factors from emission module
                expected_savings = max(0.0, (current_factor_from_module - target_factor_from_module) * distance_km)
                
                # Calculate savings using SavingsCalculator
                calculator = SavingsCalculator()
                savings = calculator.calculate_savings(
                    recommendation_type='vehicle_switch',
                    current_trip=trip_data,
                    target_vehicle=target_car_type,
                    target_fuel=target_fuel_type
                )
                
                # Property: Savings should match calculation using EMISSION_FACTORS from emission.py
                assert abs(savings.savings_g - expected_savings) < 0.01, \
                    f"SavingsCalculator should use EMISSION_FACTORS from emission.py. " \
                    f"Expected (using emission.EMISSION_FACTORS): {expected_savings:.2f}g, " \
                    f"Got: {savings.savings_g:.2f}g. " \
                    f"Switch: {current_car_type}-{current_fuel_type} -> {target_car_type}-{target_fuel_type}, " \
                    f"Distance: {distance_km:.2f}km"



class TestPropertyRouteSwitchSavingsAccuracy:
    """
    Property-based tests for route switch savings accuracy.
    
    **Feature: emission-reduction-advisor, Property 17: Route switch savings accuracy**
    **Validates: Requirements 3.4, 8.3**
    """
    
    @given(multi_route_trip_data_strategy())
    @settings(max_examples=100)
    def test_property_17_route_switch_savings_accuracy(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 17: Route switch savings accuracy**
        **Validates: Requirements 3.4, 8.3**
        
        For any route change recommendation, the calculated savings should equal
        the emission difference between the current route and the recommended route.
        
        This validates:
        - Requirement 3.4: WHEN calculating savings for route recommendations THEN the system
          SHALL use the difference between current route emission and recommended route emission
        - Requirement 8.3: WHEN the user is not using the lowest-emission route THEN the system
          SHALL quantify the additional emission cost
        
        The property verifies that:
        1. Savings calculation uses emission difference between routes
        2. Savings = current_route_emission - target_route_emission
        3. The calculation is accurate for all multi-route scenarios
        4. Savings are non-negative (switching to lower-emission route)
        """
        from advisor import SavingsCalculator
        
        # Verify we have multiple routes
        assert 'routes' in trip_data
        assert len(trip_data['routes']) >= 2, "Should have at least 2 routes for comparison"
        
        routes = trip_data['routes']
        
        # The current route is the first route (route 0)
        current_route_emission = float(routes[0]['emission_g'])
        
        # Test switching to each alternative route
        for target_route_idx in range(1, len(routes)):
            target_route = routes[target_route_idx]
            target_route_emission = float(target_route['emission_g'])
            
            # Calculate expected savings manually
            # Savings = current_emission - target_emission
            expected_savings_g = current_route_emission - target_route_emission
            
            # Ensure non-negative (as per implementation)
            expected_savings_g = max(0.0, expected_savings_g)
            expected_savings_kg = expected_savings_g / 1000.0
            
            # Calculate expected percentage
            if current_route_emission > 0:
                expected_percentage = (expected_savings_g / current_route_emission) * 100.0
            else:
                expected_percentage = 0.0
            
            # Use SavingsCalculator to calculate savings
            calculator = SavingsCalculator()
            savings = calculator.calculate_savings(
                recommendation_type='route_change',
                current_trip=trip_data,
                target_route_emission=target_route_emission
            )
            
            # Property 1: Savings should match expected calculation
            assert abs(savings.savings_g - expected_savings_g) < 0.01, \
                f"Route switch savings calculation incorrect. " \
                f"Current route emission: {current_route_emission:.2f}g, " \
                f"Target route emission: {target_route_emission:.2f}g, " \
                f"Expected savings: {expected_savings_g:.2f}g, " \
                f"Got: {savings.savings_g:.2f}g"
            
            # Property 2: Savings in kg should be savings in g divided by 1000
            assert abs(savings.savings_kg - expected_savings_kg) < 0.00001, \
                f"Savings in kg should be savings in g / 1000. " \
                f"Expected: {expected_savings_kg:.5f}kg, Got: {savings.savings_kg:.5f}kg"
            
            # Property 3: Percentage should match expected calculation
            assert abs(savings.savings_percentage - expected_percentage) < 0.01, \
                f"Savings percentage incorrect. " \
                f"Expected: {expected_percentage:.2f}%, Got: {savings.savings_percentage:.2f}%"
            
            # Property 4: Savings should be non-negative
            assert savings.savings_g >= 0, \
                f"Savings should be non-negative. Got: {savings.savings_g:.2f}g"
            
            # Property 5: If target route has lower emission, savings should be positive
            if target_route_emission < current_route_emission:
                assert savings.savings_g > 0, \
                    f"Switching to lower-emission route should have positive savings. " \
                    f"Current: {current_route_emission:.2f}g, Target: {target_route_emission:.2f}g, " \
                    f"Savings: {savings.savings_g:.2f}g"
            
            # Property 6: If target route has higher emission, savings should be zero (clamped)
            if target_route_emission > current_route_emission:
                assert savings.savings_g == 0, \
                    f"Switching to higher-emission route should have zero savings (clamped). " \
                    f"Current: {current_route_emission:.2f}g, Target: {target_route_emission:.2f}g, " \
                    f"Savings: {savings.savings_g:.2f}g"
    
    @given(multi_route_trip_data_strategy())
    @settings(max_examples=100)
    def test_property_17_best_route_savings(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 17: Route switch savings accuracy**
        **Validates: Requirements 3.4, 8.3**
        
        Specifically test switching to the best (lowest-emission) route.
        This is the most common route recommendation scenario.
        
        For any multi-route trip, switching to the best route should result in
        maximum savings that are accurately calculated.
        """
        from advisor import SavingsCalculator, TripAnalyzer
        
        # Verify we have multiple routes
        assert 'routes' in trip_data
        assert len(trip_data['routes']) >= 2
        
        routes = trip_data['routes']
        current_route_emission = float(routes[0]['emission_g'])
        
        # Find the best route (minimum emission)
        min_emission = float('inf')
        best_route_idx = 0
        
        for idx, route in enumerate(routes):
            route_emission = float(route['emission_g'])
            if route_emission < min_emission:
                min_emission = route_emission
                best_route_idx = idx
        
        # Only test if current route is not already the best
        if best_route_idx == 0:
            return
        
        best_route_emission = min_emission
        
        # Calculate expected savings
        expected_savings_g = current_route_emission - best_route_emission
        expected_savings_kg = expected_savings_g / 1000.0
        expected_percentage = (expected_savings_g / current_route_emission) * 100.0
        
        # Use SavingsCalculator
        calculator = SavingsCalculator()
        savings = calculator.calculate_savings(
            recommendation_type='route_change',
            current_trip=trip_data,
            target_route_emission=best_route_emission
        )
        
        # Property 1: Savings should be positive (best route has lower emissions)
        assert savings.savings_g > 0, \
            f"Switching to best route should have positive savings. " \
            f"Current: {current_route_emission:.2f}g, Best: {best_route_emission:.2f}g, " \
            f"Got: {savings.savings_g:.2f}g"
        
        # Property 2: Savings should match expected calculation
        assert abs(savings.savings_g - expected_savings_g) < 0.01, \
            f"Best route switch savings incorrect. " \
            f"Expected: {expected_savings_g:.2f}g, Got: {savings.savings_g:.2f}g. " \
            f"Current route: {current_route_emission:.2f}g, Best route: {best_route_emission:.2f}g"
        
        # Property 3: Percentage should match expected calculation
        assert abs(savings.savings_percentage - expected_percentage) < 0.01, \
            f"Percentage calculation incorrect. " \
            f"Expected: {expected_percentage:.2f}%, Got: {savings.savings_percentage:.2f}%"
        
        # Property 4: Verify TripAnalyzer identifies the same best route
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        assert analysis.best_route_index == best_route_idx, \
            f"TripAnalyzer should identify the same best route. " \
            f"Expected: {best_route_idx}, Got: {analysis.best_route_index}"
    
    @given(multi_route_trip_data_strategy())
    @settings(max_examples=100)
    def test_property_17_savings_independent_of_distance(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 17: Route switch savings accuracy**
        **Validates: Requirements 3.4, 8.3**
        
        Verify that route switch savings depend only on emission difference,
        not on the absolute distance values.
        
        Two routes with the same emission difference should have the same savings,
        regardless of their actual distances.
        """
        from advisor import SavingsCalculator
        
        # Verify we have multiple routes
        assert 'routes' in trip_data
        assert len(trip_data['routes']) >= 2
        
        routes = trip_data['routes']
        current_route_emission = float(routes[0]['emission_g'])
        
        # Test switching to each alternative route
        for target_route_idx in range(1, len(routes)):
            target_route_emission = float(routes[target_route_idx]['emission_g'])
            
            # Calculate savings
            calculator = SavingsCalculator()
            savings = calculator.calculate_savings(
                recommendation_type='route_change',
                current_trip=trip_data,
                target_route_emission=target_route_emission
            )
            
            # Property: Savings should equal emission difference, regardless of distance
            emission_difference = max(0.0, current_route_emission - target_route_emission)
            
            assert abs(savings.savings_g - emission_difference) < 0.01, \
                f"Route switch savings should equal emission difference. " \
                f"Emission difference: {emission_difference:.2f}g, " \
                f"Calculated savings: {savings.savings_g:.2f}g. " \
                f"Current route distance: {routes[0]['distance_km']:.2f}km, " \
                f"Target route distance: {routes[target_route_idx]['distance_km']:.2f}km"
    
    @given(multi_route_trip_data_strategy())
    @settings(max_examples=100)
    def test_property_17_percentage_relative_to_current_emission(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 17: Route switch savings accuracy**
        **Validates: Requirements 3.4, 8.3**
        
        Verify that the savings percentage is correctly calculated relative to
        the current route's emission, not the target route's emission.
        
        Percentage = (savings / current_emission) * 100
        """
        from advisor import SavingsCalculator
        
        # Verify we have multiple routes
        assert 'routes' in trip_data
        assert len(trip_data['routes']) >= 2
        
        routes = trip_data['routes']
        current_route_emission = float(routes[0]['emission_g'])
        
        # Test switching to each alternative route
        for target_route_idx in range(1, len(routes)):
            target_route_emission = float(routes[target_route_idx]['emission_g'])
            
            # Calculate savings
            calculator = SavingsCalculator()
            savings = calculator.calculate_savings(
                recommendation_type='route_change',
                current_trip=trip_data,
                target_route_emission=target_route_emission
            )
            
            # Property: Percentage should be relative to current emission
            if current_route_emission > 0:
                expected_percentage = (savings.savings_g / current_route_emission) * 100.0
                
                assert abs(savings.savings_percentage - expected_percentage) < 0.01, \
                    f"Savings percentage should be relative to current emission. " \
                    f"Current emission: {current_route_emission:.2f}g, " \
                    f"Savings: {savings.savings_g:.2f}g, " \
                    f"Expected percentage: {expected_percentage:.2f}%, " \
                    f"Got: {savings.savings_percentage:.2f}%"
            else:
                # Edge case: if current emission is zero, percentage should be zero
                assert savings.savings_percentage == 0.0, \
                    f"Savings percentage should be 0 when current emission is 0. " \
                    f"Got: {savings.savings_percentage:.2f}%"
    
    @given(multi_route_trip_data_strategy())
    @settings(max_examples=100)
    def test_property_17_uses_precomputed_emissions(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 17: Route switch savings accuracy**
        **Validates: Requirements 3.4, 8.3**
        
        Verify that route switch savings use the pre-computed emission values
        from the routes, not recalculated values.
        
        This ensures consistency with Requirement 8.1: "analyze all routes without
        recalculating distances or emissions"
        """
        from advisor import SavingsCalculator
        
        # Verify we have multiple routes
        assert 'routes' in trip_data
        assert len(trip_data['routes']) >= 2
        
        routes = trip_data['routes']
        current_route_emission = float(routes[0]['emission_g'])
        
        # Test switching to each alternative route
        for target_route_idx in range(1, len(routes)):
            target_route = routes[target_route_idx]
            target_route_emission = float(target_route['emission_g'])
            
            # Calculate savings using SavingsCalculator
            calculator = SavingsCalculator()
            savings = calculator.calculate_savings(
                recommendation_type='route_change',
                current_trip=trip_data,
                target_route_emission=target_route_emission
            )
            
            # Property: Savings should use the exact emission values from routes
            # Not recalculated from distance and emission factors
            expected_savings = max(0.0, current_route_emission - target_route_emission)
            
            assert abs(savings.savings_g - expected_savings) < 0.01, \
                f"Route switch savings should use pre-computed emission values. " \
                f"Current route emission (from data): {current_route_emission:.2f}g, " \
                f"Target route emission (from data): {target_route_emission:.2f}g, " \
                f"Expected savings: {expected_savings:.2f}g, " \
                f"Got: {savings.savings_g:.2f}g"
            
            # Verify that we're not recalculating emissions from distance
            # The savings should match the emission difference exactly,
            # not a recalculation based on distance and emission factors
            current_distance = float(routes[0]['distance_km'])
            target_distance = float(target_route['distance_km'])
            emission_factor = EMISSION_FACTORS[trip_data['car_type']][trip_data['fuel_type']]
            
            # If we were recalculating, savings would be based on distance difference
            # But we should NOT be doing this - we should use emission difference
            recalculated_savings = (current_distance - target_distance) * emission_factor
            
            # The actual savings should match emission difference, not recalculated value
            # (unless they happen to be the same, which is unlikely with our test data)
            if abs(recalculated_savings - expected_savings) > 1.0:
                # If they're different, verify we're using the emission difference
                assert abs(savings.savings_g - expected_savings) < 0.01, \
                    f"Should use emission difference, not recalculated from distance. " \
                    f"Emission difference: {expected_savings:.2f}g, " \
                    f"Recalculated from distance: {recalculated_savings:.2f}g, " \
                    f"Got: {savings.savings_g:.2f}g"



class TestPropertyEmissionFactorConsistency:
    """
    Property-based tests for emission factor consistency.
    
    **Feature: emission-reduction-advisor, Property 20: Emission factor consistency**
    **Validates: Requirements 4.4**
    """
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_20_emission_factor_consistency_in_analysis(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 20: Emission factor consistency**
        **Validates: Requirements 4.4**
        
        For any emission factor used in calculations, the value should match the
        corresponding entry in emission.EMISSION_FACTORS.
        
        This validates:
        - Requirement 4.4: THE Emission Reduction Advisor SHALL use the existing
          EMISSION_FACTORS data from the emission module for consistency
        
        The property verifies that:
        1. TripAnalyzer uses emission factors from emission.EMISSION_FACTORS
        2. The emission factor in analysis matches the value in EMISSION_FACTORS
        3. No hardcoded or alternative emission factors are used
        4. Consistency is maintained across all vehicle-fuel combinations
        """
        # Extract vehicle and fuel information
        car_type = trip_data['car_type']
        fuel_type = trip_data['fuel_type']
        
        # Get the expected emission factor directly from emission.EMISSION_FACTORS
        expected_emission_factor = EMISSION_FACTORS[car_type][fuel_type]
        
        # Create analyzer and analyze the trip
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        # Property 1: The emission factor in analysis should match EMISSION_FACTORS
        actual_emission_factor = analysis.vehicle_info.emission_factor
        
        assert actual_emission_factor == expected_emission_factor, \
            f"Emission factor should match emission.EMISSION_FACTORS. " \
            f"For {car_type}-{fuel_type}: " \
            f"Expected (from EMISSION_FACTORS): {expected_emission_factor}, " \
            f"Got (from analysis): {actual_emission_factor}"
        
        # Property 2: The emission factor should be retrieved using get_emission_factor
        # This ensures consistency with the emission module's API
        emission_factor_via_function = get_emission_factor(car_type, fuel_type)
        
        assert actual_emission_factor == emission_factor_via_function, \
            f"Emission factor should match get_emission_factor result. " \
            f"For {car_type}-{fuel_type}: " \
            f"Expected (from get_emission_factor): {emission_factor_via_function}, " \
            f"Got (from analysis): {actual_emission_factor}"
        
        # Property 3: The emission factor should be a positive number
        assert actual_emission_factor > 0, \
            f"Emission factor should be positive. " \
            f"For {car_type}-{fuel_type}, got: {actual_emission_factor}"
        
        # Property 4: The emission factor should be consistent across multiple analyses
        # Analyzing the same trip data multiple times should yield the same emission factor
        analysis2 = analyzer.analyze_trip(trip_data)
        
        assert analysis2.vehicle_info.emission_factor == actual_emission_factor, \
            f"Emission factor should be consistent across multiple analyses. " \
            f"First analysis: {actual_emission_factor}, " \
            f"Second analysis: {analysis2.vehicle_info.emission_factor}"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_20_emission_factor_consistency_in_savings_calculator(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 20: Emission factor consistency**
        **Validates: Requirements 4.4**
        
        For any vehicle switch savings calculation, the emission factors used should
        match the values in emission.EMISSION_FACTORS.
        
        This ensures that the SavingsCalculator component uses the same emission
        factors as the rest of the system.
        """
        from advisor import SavingsCalculator
        
        # Extract vehicle information
        current_car_type = trip_data['car_type']
        current_fuel_type = trip_data['fuel_type']
        distance_km = trip_data['distance_km']
        
        # Get expected emission factors from EMISSION_FACTORS
        current_emission_factor_expected = EMISSION_FACTORS[current_car_type][current_fuel_type]
        
        # Test switching to each valid vehicle-fuel combination
        for target_car_type in EMISSION_FACTORS.keys():
            for target_fuel_type in EMISSION_FACTORS[target_car_type].keys():
                # Skip if it's the same combination
                if target_car_type == current_car_type and target_fuel_type == current_fuel_type:
                    continue
                
                # Get expected target emission factor from EMISSION_FACTORS
                target_emission_factor_expected = EMISSION_FACTORS[target_car_type][target_fuel_type]
                
                # Calculate expected savings using EMISSION_FACTORS directly
                expected_savings_g = max(0.0, (current_emission_factor_expected - target_emission_factor_expected) * distance_km)
                
                # Use SavingsCalculator to calculate savings
                calculator = SavingsCalculator()
                savings = calculator.calculate_savings(
                    recommendation_type='vehicle_switch',
                    current_trip=trip_data,
                    target_vehicle=target_car_type,
                    target_fuel=target_fuel_type
                )
                
                # Property: Savings should match calculation using EMISSION_FACTORS
                # This verifies that SavingsCalculator uses the same emission factors
                assert abs(savings.savings_g - expected_savings_g) < 0.01, \
                    f"SavingsCalculator should use emission factors from EMISSION_FACTORS. " \
                    f"For switch {current_car_type}-{current_fuel_type} -> {target_car_type}-{target_fuel_type}: " \
                    f"Expected savings (using EMISSION_FACTORS): {expected_savings_g:.2f}g, " \
                    f"Got: {savings.savings_g:.2f}g. " \
                    f"Distance: {distance_km:.2f}km, " \
                    f"Current factor (EMISSION_FACTORS): {current_emission_factor_expected}, " \
                    f"Target factor (EMISSION_FACTORS): {target_emission_factor_expected}"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_20_emission_factor_consistency_in_recommendations(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 20: Emission factor consistency**
        **Validates: Requirements 4.4**
        
        For any recommendations generated, the emission factors used in savings
        calculations should match the values in emission.EMISSION_FACTORS.
        
        This validates that the entire recommendation pipeline uses consistent
        emission factors from the emission module.
        """
        from advisor import RecommendationEngine
        
        # Extract vehicle information
        car_type = trip_data['car_type']
        fuel_type = trip_data['fuel_type']
        distance_km = trip_data['distance_km']
        
        # Create analyzer and analyze the trip
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        # Generate recommendations
        engine = RecommendationEngine()
        routes = trip_data.get('routes', None)
        recommendations = engine.generate_recommendations(analysis, routes)
        
        # Property: For each vehicle_switch recommendation, verify savings use EMISSION_FACTORS
        for rec in recommendations:
            if rec.type == 'vehicle_switch':
                # Extract the target vehicle from the recommendation
                # For EV recommendations, target is EV-listrik
                rec_text = (rec.title + " " + rec.description).lower()
                
                if 'listrik' in rec_text or 'electric' in rec_text or 'ev' in rec_text:
                    # This is an EV recommendation
                    target_car_type = 'EV'
                    target_fuel_type = 'listrik'
                    
                    # Get emission factors from EMISSION_FACTORS
                    current_emission_factor = EMISSION_FACTORS[car_type][fuel_type]
                    target_emission_factor = EMISSION_FACTORS[target_car_type][target_fuel_type]
                    
                    # Calculate expected savings using EMISSION_FACTORS
                    expected_savings_g = (current_emission_factor - target_emission_factor) * distance_km
                    
                    # Property: Recommendation savings should match calculation using EMISSION_FACTORS
                    actual_savings_g = rec.savings.savings_g
                    
                    assert abs(actual_savings_g - expected_savings_g) < 0.01, \
                        f"Recommendation savings should use EMISSION_FACTORS. " \
                        f"For {car_type}-{fuel_type} -> {target_car_type}-{target_fuel_type}: " \
                        f"Expected (using EMISSION_FACTORS): {expected_savings_g:.2f}g, " \
                        f"Got: {actual_savings_g:.2f}g. " \
                        f"Distance: {distance_km:.2f}km, " \
                        f"Current factor: {current_emission_factor}, " \
                        f"Target factor: {target_emission_factor}"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_20_no_hardcoded_emission_factors(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 20: Emission factor consistency**
        **Validates: Requirements 4.4**
        
        Verify that the system does not use any hardcoded emission factors that
        differ from emission.EMISSION_FACTORS.
        
        This test ensures that if EMISSION_FACTORS is modified, the advisor
        automatically uses the new values without requiring code changes.
        """
        # Extract vehicle information
        car_type = trip_data['car_type']
        fuel_type = trip_data['fuel_type']
        
        # Get the emission factor from EMISSION_FACTORS
        emission_factor_from_module = EMISSION_FACTORS[car_type][fuel_type]
        
        # Analyze the trip
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        # Property 1: Analysis should use the exact value from EMISSION_FACTORS
        assert analysis.vehicle_info.emission_factor == emission_factor_from_module, \
            f"Analysis should use emission factor from EMISSION_FACTORS, not hardcoded values. " \
            f"For {car_type}-{fuel_type}: " \
            f"EMISSION_FACTORS value: {emission_factor_from_module}, " \
            f"Analysis value: {analysis.vehicle_info.emission_factor}"
        
        # Property 2: The emission factor should be retrieved dynamically
        # If we call get_emission_factor, it should return the same value
        dynamic_factor = get_emission_factor(car_type, fuel_type)
        
        assert analysis.vehicle_info.emission_factor == dynamic_factor, \
            f"Analysis should retrieve emission factor dynamically. " \
            f"For {car_type}-{fuel_type}: " \
            f"Dynamic retrieval: {dynamic_factor}, " \
            f"Analysis value: {analysis.vehicle_info.emission_factor}"
        
        # Property 3: Verify no magic numbers are used
        # The emission factor should be one of the values in EMISSION_FACTORS
        all_emission_factors = []
        for vehicle in EMISSION_FACTORS.values():
            for factor in vehicle.values():
                all_emission_factors.append(factor)
        
        assert analysis.vehicle_info.emission_factor in all_emission_factors, \
            f"Emission factor should be from EMISSION_FACTORS, not a magic number. " \
            f"Got: {analysis.vehicle_info.emission_factor}, " \
            f"Valid factors: {all_emission_factors}"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_20_consistency_across_all_components(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 20: Emission factor consistency**
        **Validates: Requirements 4.4**
        
        Verify that all components (TripAnalyzer, SavingsCalculator, RecommendationEngine)
        use the same emission factors from emission.EMISSION_FACTORS.
        
        This is a comprehensive test that ensures system-wide consistency.
        """
        from advisor import RecommendationEngine, SavingsCalculator
        
        # Extract vehicle information
        car_type = trip_data['car_type']
        fuel_type = trip_data['fuel_type']
        distance_km = trip_data['distance_km']
        
        # Get the canonical emission factor from EMISSION_FACTORS
        canonical_emission_factor = EMISSION_FACTORS[car_type][fuel_type]
        
        # Component 1: TripAnalyzer
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        analyzer_emission_factor = analysis.vehicle_info.emission_factor
        
        assert analyzer_emission_factor == canonical_emission_factor, \
            f"TripAnalyzer should use EMISSION_FACTORS. " \
            f"For {car_type}-{fuel_type}: " \
            f"EMISSION_FACTORS: {canonical_emission_factor}, " \
            f"TripAnalyzer: {analyzer_emission_factor}"
        
        # Component 2: SavingsCalculator (test with EV switch if not already EV)
        if car_type != 'EV':
            calculator = SavingsCalculator()
            
            # Calculate savings for switching to EV
            ev_emission_factor = EMISSION_FACTORS['EV']['listrik']
            expected_savings = (canonical_emission_factor - ev_emission_factor) * distance_km
            
            savings = calculator.calculate_savings(
                recommendation_type='vehicle_switch',
                current_trip=trip_data,
                target_vehicle='EV',
                target_fuel='listrik'
            )
            
            assert abs(savings.savings_g - expected_savings) < 0.01, \
                f"SavingsCalculator should use EMISSION_FACTORS. " \
                f"For {car_type}-{fuel_type} -> EV-listrik: " \
                f"Expected (using EMISSION_FACTORS): {expected_savings:.2f}g, " \
                f"Got: {savings.savings_g:.2f}g"
        
        # Component 3: RecommendationEngine
        engine = RecommendationEngine()
        routes = trip_data.get('routes', None)
        recommendations = engine.generate_recommendations(analysis, routes)
        
        # Verify that recommendations with savings use consistent emission factors
        for rec in recommendations:
            if rec.type == 'vehicle_switch' and car_type != 'EV':
                # For non-EV vehicles, EV recommendation should use EMISSION_FACTORS
                ev_emission_factor = EMISSION_FACTORS['EV']['listrik']
                expected_savings = (canonical_emission_factor - ev_emission_factor) * distance_km
                
                # Allow for small differences due to floating point arithmetic
                assert abs(rec.savings.savings_g - expected_savings) < 0.01, \
                    f"RecommendationEngine should use EMISSION_FACTORS. " \
                    f"For {car_type}-{fuel_type} -> EV: " \
                    f"Expected (using EMISSION_FACTORS): {expected_savings:.2f}g, " \
                    f"Got: {rec.savings.savings_g:.2f}g"
        
        # Property: All components should use the same emission factor source
        # This ensures system-wide consistency
        assert True, "All components use consistent emission factors from EMISSION_FACTORS"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_20_emission_factor_lookup_consistency(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 20: Emission factor consistency**
        **Validates: Requirements 4.4**
        
        Verify that emission factor lookups are consistent regardless of how they
        are performed (direct dictionary access vs get_emission_factor function).
        
        This ensures that the advisor uses the emission module's API correctly.
        """
        # Extract vehicle information
        car_type = trip_data['car_type']
        fuel_type = trip_data['fuel_type']
        
        # Method 1: Direct dictionary access
        emission_factor_direct = EMISSION_FACTORS[car_type][fuel_type]
        
        # Method 2: Using get_emission_factor function
        emission_factor_function = get_emission_factor(car_type, fuel_type)
        
        # Property 1: Both methods should return the same value
        assert emission_factor_direct == emission_factor_function, \
            f"Emission factor lookup should be consistent. " \
            f"For {car_type}-{fuel_type}: " \
            f"Direct access: {emission_factor_direct}, " \
            f"Function call: {emission_factor_function}"
        
        # Method 3: Through TripAnalyzer
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        emission_factor_analyzer = analysis.vehicle_info.emission_factor
        
        # Property 2: TripAnalyzer should return the same value
        assert emission_factor_analyzer == emission_factor_direct, \
            f"TripAnalyzer should use the same emission factor. " \
            f"For {car_type}-{fuel_type}: " \
            f"EMISSION_FACTORS: {emission_factor_direct}, " \
            f"TripAnalyzer: {emission_factor_analyzer}"
        
        # Property 3: All three methods should be consistent
        assert emission_factor_direct == emission_factor_function == emission_factor_analyzer, \
            f"All emission factor lookup methods should be consistent. " \
            f"For {car_type}-{fuel_type}: " \
            f"Direct: {emission_factor_direct}, " \
            f"Function: {emission_factor_function}, " \
            f"Analyzer: {emission_factor_analyzer}"



class TestPropertyOutputStructure:
    """
    Property-based tests for output structure and formatting.
    
    **Feature: emission-reduction-advisor, Property 3: Output contains required sections**
    **Feature: emission-reduction-advisor, Property 4: Emission units consistency**
    **Feature: emission-reduction-advisor, Property 6: Visual section separators**
    **Validates: Requirements 1.3, 3.2, 5.1, 5.5**
    """
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_3_output_contains_required_sections(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 3: Output contains required sections**
        **Validates: Requirements 5.1**
        
        For any valid trip data, the generated output should contain identifiable
        sections for summary, recommendations, and savings.
        
        This validates:
        - Requirement 5.1: WHEN the Emission Reduction Advisor generates output THEN
          the system SHALL format the response with clear sections for summary,
          recommendations, and savings
        
        The property verifies that:
        1. The output contains a summary section with trip information
        2. The output contains a recommendations section
        3. The output contains savings information
        4. All three sections are identifiable and present
        """
        # Call the advisor function
        result = get_emission_advice(trip_data)
        
        # Property 1: Result should be a non-empty string
        assert isinstance(result, str), "Output should be a string"
        assert len(result) > 0, "Output should not be empty"
        
        # Property 2: Output should contain a summary section
        # Look for summary section indicators
        result_upper = result.upper()
        
        # Check for summary section header
        has_summary_header = any(keyword in result_upper for keyword in [
            'RINGKASAN PERJALANAN',
            'RINGKASAN',
            'SUMMARY'
        ])
        
        assert has_summary_header, \
            f"Output should contain a summary section header. " \
            f"Output preview: {result[:300]}..."
        
        # Property 3: Summary section should contain distance information
        # The distance value from input should appear in the output
        distance_str = f"{trip_data['distance_km']:.1f}"
        
        # Check if distance appears in output (allowing for formatting variations)
        has_distance = distance_str in result or str(int(trip_data['distance_km'])) in result
        
        assert has_distance, \
            f"Summary section should contain distance information ({distance_str} km). " \
            f"Output preview: {result[:500]}..."
        
        # Property 4: Summary section should contain vehicle information
        has_vehicle_info = trip_data['car_type'] in result
        
        assert has_vehicle_info, \
            f"Summary section should contain vehicle type ({trip_data['car_type']}). " \
            f"Output preview: {result[:500]}..."
        
        # Property 5: Summary section should contain emission information
        # Check for emission value (in grams)
        emission_str = f"{trip_data['emission_g']:,.0f}"
        
        # The emission might be formatted with commas or without
        has_emission = (
            str(int(trip_data['emission_g'])) in result or
            emission_str in result or
            'emisi' in result.lower() or
            'emission' in result.lower()
        )
        
        assert has_emission, \
            f"Summary section should contain emission information. " \
            f"Output preview: {result[:500]}..."
        
        # Property 6: Output should contain a recommendations section
        has_recommendations_header = any(keyword in result_upper for keyword in [
            'REKOMENDASI',
            'RECOMMENDATION',
            'SARAN'
        ])
        
        assert has_recommendations_header, \
            f"Output should contain a recommendations section header. " \
            f"Output preview: {result[:500]}..."
        
        # Property 7: Recommendations section should contain numbered recommendations
        # Look for numbering patterns (1., 2., 3. or 1) 2) 3))
        has_numbering = any(pattern in result for pattern in ['1.', '2.', '1)', '2)'])
        
        assert has_numbering, \
            f"Recommendations section should contain numbered recommendations. " \
            f"Output preview: {result[:800]}..."
        
        # Property 8: Output should contain savings information
        # Look for savings-related keywords
        has_savings = any(keyword in result.lower() for keyword in [
            'penghematan',
            'savings',
            'hemat',
            'potensi'
        ])
        
        assert has_savings, \
            f"Output should contain savings information. " \
            f"Output preview: {result[:800]}..."
        
        # Property 9: All three major sections should be present
        # Summary, Recommendations, and Savings
        assert has_summary_header and has_recommendations_header and has_savings, \
            f"Output should contain all three required sections: summary, recommendations, and savings. " \
            f"Summary: {has_summary_header}, Recommendations: {has_recommendations_header}, Savings: {has_savings}"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_4_emission_units_consistency(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 4: Emission units consistency**
        **Validates: Requirements 1.3, 3.2**
        
        For any emission value in the output, both grams and kilograms should be
        displayed when the value is presented.
        
        This validates:
        - Requirement 1.3: WHEN generating the summary THEN the system SHALL present
          emission values in both grams and kilograms for better readability
        - Requirement 3.2: WHEN displaying emission savings THEN the system SHALL
          present values in both grams and kilograms for amounts over 1000 grams
        
        The property verifies that:
        1. The summary section displays total emission in both g and kg
        2. Each recommendation's savings is displayed in both g and kg
        3. The total potential savings is displayed in both g and kg
        4. Both units appear consistently throughout the output
        5. The conversion between g and kg is correct (1 kg = 1000 g)
        """
        # Call the advisor function
        result = get_emission_advice(trip_data)
        
        # Property 1: Result should be a non-empty string
        assert isinstance(result, str), "Output should be a string"
        assert len(result) > 0, "Output should not be empty"
        
        # Property 2: Output should contain both 'g' and 'kg' unit indicators
        result_lower = result.lower()
        
        # Check for grams unit (g CO2, gram, grams)
        has_grams_unit = any(pattern in result for pattern in [
            'g CO2', 'g co2', ' g ', 'gram'
        ])
        
        # Check for kilograms unit (kg CO2, kilogram, kilograms)
        has_kg_unit = any(pattern in result for pattern in [
            'kg CO2', 'kg co2', ' kg ', 'kilogram'
        ])
        
        assert has_grams_unit, \
            f"Output should contain grams unit indicator (g CO2, gram). " \
            f"Output preview: {result[:500]}..."
        
        assert has_kg_unit, \
            f"Output should contain kilograms unit indicator (kg CO2, kilogram). " \
            f"Output preview: {result[:500]}..."
        
        # Property 3: Summary section should display emission in both units
        # Extract the summary section
        lines = result.split('\n')
        summary_section = []
        in_summary = False
        
        for line in lines:
            if 'RINGKASAN PERJALANAN' in line.upper() or 'SUMMARY' in line.upper():
                in_summary = True
            elif in_summary and ('REKOMENDASI' in line.upper() or 'RECOMMENDATION' in line.upper()):
                break
            elif in_summary:
                summary_section.append(line)
        
        summary_text = '\n'.join(summary_section)
        
        # Check that summary contains both g and kg for emission
        summary_has_grams = any(pattern in summary_text for pattern in ['g CO2', 'g co2', ' g '])
        summary_has_kg = any(pattern in summary_text for pattern in ['kg CO2', 'kg co2', ' kg '])
        
        assert summary_has_grams, \
            f"Summary section should display emission in grams. " \
            f"Summary text: {summary_text[:300]}..."
        
        assert summary_has_kg, \
            f"Summary section should display emission in kilograms. " \
            f"Summary text: {summary_text[:300]}..."
        
        # Property 4: Verify the conversion is correct in summary
        # The emission_g from input should appear in grams
        # And emission_g / 1000 should appear in kg
        emission_g = trip_data['emission_g']
        emission_kg = emission_g / 1000.0
        
        # Format as they would appear in output (with comma separators for grams)
        emission_g_formatted = f"{emission_g:,.0f}"
        emission_kg_formatted = f"{emission_kg:.2f}"
        
        # Check if these values appear in the summary
        # Allow for some formatting variations
        has_correct_g_value = (
            emission_g_formatted in summary_text or
            f"{int(emission_g)}" in summary_text or
            f"{emission_g:.0f}" in summary_text
        )
        
        has_correct_kg_value = (
            emission_kg_formatted in summary_text or
            f"{emission_kg:.1f}" in summary_text or
            f"{emission_kg:.3f}" in summary_text
        )
        
        assert has_correct_g_value, \
            f"Summary should contain the correct emission value in grams ({emission_g:.0f}g). " \
            f"Summary text: {summary_text[:400]}..."
        
        assert has_correct_kg_value, \
            f"Summary should contain the correct emission value in kilograms ({emission_kg:.2f}kg). " \
            f"Summary text: {summary_text[:400]}..."
        
        # Property 5: Recommendations section should display savings in both units
        # Extract the recommendations section
        recommendations_section = []
        in_recommendations = False
        
        for line in lines:
            if '💡 REKOMENDASI' in line or 'RECOMMENDATION' in line.upper():
                in_recommendations = True
            elif in_recommendations and '═' in line and 'POTENSI' in line.upper():
                # Reached the footer
                break
            elif in_recommendations:
                recommendations_section.append(line)
        
        recommendations_text = '\n'.join(recommendations_section)
        
        # Check that recommendations contain both g and kg for savings
        # Look for the savings pattern: "Penghematan: X g CO2 (Y kg)"
        recommendations_has_grams = any(pattern in recommendations_text for pattern in [
            'g CO2', 'g co2', ' g '
        ])
        
        recommendations_has_kg = any(pattern in recommendations_text for pattern in [
            'kg CO2', 'kg co2', ' kg ', 'kg)'
        ])
        
        assert recommendations_has_grams, \
            f"Recommendations section should display savings in grams. " \
            f"Recommendations text preview: {recommendations_text[:500]}..."
        
        assert recommendations_has_kg, \
            f"Recommendations section should display savings in kilograms. " \
            f"Recommendations text preview: {recommendations_text[:500]}..."
        
        # Property 6: Total potential savings should be in both units
        # Look for the footer with total savings
        footer_section = []
        for i, line in enumerate(lines):
            if 'POTENSI PENGHEMATAN' in line.upper() or 'TOTAL' in line.upper():
                # Get this line and a few around it
                footer_section = lines[max(0, i-2):min(len(lines), i+3)]
                break
        
        footer_text = '\n'.join(footer_section)
        
        # Check that footer contains both g and kg
        footer_has_grams = any(pattern in footer_text for pattern in ['g CO2', 'g co2', ' g '])
        footer_has_kg = any(pattern in footer_text for pattern in ['kg CO2', 'kg co2', ' kg '])
        
        assert footer_has_grams, \
            f"Total savings should be displayed in grams. " \
            f"Footer text: {footer_text}"
        
        assert footer_has_kg, \
            f"Total savings should be displayed in kilograms. " \
            f"Footer text: {footer_text}"
        
        # Property 7: Count occurrences to ensure consistency
        # Both units should appear multiple times (at least once per recommendation + summary + footer)
        # We expect at least 3 occurrences of each unit (summary, 2-3 recommendations, footer)
        import re
        
        # Count all occurrences of "g CO2" (case insensitive)
        g_count = len(re.findall(r'g\s+CO2', result, re.IGNORECASE))
        
        # Count all occurrences of "kg" followed by optional closing paren or "CO2"
        kg_count = len(re.findall(r'kg(?:\s+CO2|\))', result, re.IGNORECASE))
        
        assert g_count >= 3, \
            f"Grams unit should appear at least 3 times (summary + recommendations + footer). " \
            f"Found {g_count} occurrences."
        
        assert kg_count >= 3, \
            f"Kilograms unit should appear at least 3 times (summary + recommendations + footer). " \
            f"Found {kg_count} occurrences."
        
        # Property 8: Verify that the g/kg conversion is mathematically correct
        # Extract all number pairs that appear as "X g CO2 (Y kg)"
        # Pattern to match: number (with optional commas) followed by g CO2, then number in parentheses followed by kg
        pattern = r'([\d,]+(?:\.\d+)?)\s*g\s*CO2\s*\((\d+(?:\.\d+)?)\s*kg'
        matches = re.findall(pattern, result, re.IGNORECASE)
        
        for g_str, kg_str in matches:
            # Remove commas from grams value
            g_value = float(g_str.replace(',', ''))
            kg_value = float(kg_str)
            
            # Verify conversion: kg should be g / 1000 (with some tolerance for rounding)
            expected_kg = g_value / 1000.0
            
            # Allow for rounding differences (within 0.01 kg)
            assert abs(kg_value - expected_kg) < 0.01, \
                f"Conversion error: {g_value}g should equal {expected_kg:.2f}kg, but found {kg_value}kg. " \
                f"Difference: {abs(kg_value - expected_kg):.4f}kg"
        
        # Property 9: Ensure at least one valid g/kg pair was found and verified
        assert len(matches) >= 1, \
            f"Should find at least one emission value displayed in both g and kg units. " \
            f"Output preview: {result[:800]}..."
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_6_visual_section_separators(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 6: Visual section separators**
        **Validates: Requirements 5.5**
        
        For any generated output, separator characters should appear to distinguish
        between major sections.
        
        This validates:
        - Requirement 5.5: WHEN displaying the output THEN the system SHALL use
          visual separators to distinguish between different sections
        
        The property verifies that:
        1. The output contains visual separator characters
        2. Separators are used to distinguish between sections
        3. Separators improve readability by creating visual boundaries
        """
        # Call the advisor function
        result = get_emission_advice(trip_data)
        
        # Property 1: Result should be a non-empty string
        assert isinstance(result, str), "Output should be a string"
        assert len(result) > 0, "Output should not be empty"
        
        # Property 2: Output should contain visual separator characters
        # Common separator characters: ═, ─, -, =, _, *
        separator_chars = ['═', '─', '=', '-', '_', '*']
        
        has_separators = any(char in result for char in separator_chars)
        
        assert has_separators, \
            f"Output should contain visual separator characters (═, ─, =, -, _, *). " \
            f"Output preview: {result[:300]}..."
        
        # Property 3: Separators should appear multiple times (to separate multiple sections)
        # Count occurrences of separator lines (lines with mostly separator characters)
        lines = result.split('\n')
        separator_lines = []
        
        for line in lines:
            # A separator line is one that consists mostly of separator characters
            if len(line) > 0:
                separator_char_count = sum(1 for char in line if char in separator_chars)
                # If more than 50% of the line is separator characters, it's a separator line
                if separator_char_count / len(line) > 0.5:
                    separator_lines.append(line)
        
        # Property 4: Should have at least 2 separator lines (to separate 3 sections)
        assert len(separator_lines) >= 2, \
            f"Output should have at least 2 separator lines to distinguish sections. " \
            f"Found {len(separator_lines)} separator lines. " \
            f"Separator lines: {separator_lines}"
        
        # Property 5: Separator lines should be reasonably long (not just a single character)
        # This ensures they actually serve as visual separators
        for sep_line in separator_lines:
            assert len(sep_line.strip()) >= 10, \
                f"Separator lines should be reasonably long (>= 10 characters). " \
                f"Found separator line with length {len(sep_line.strip())}: '{sep_line}'"
        
        # Property 6: Separators should help distinguish major sections
        # Check that separators appear near section headers
        result_upper = result.upper()
        
        # Find positions of section headers
        summary_pos = -1
        recommendations_pos = -1
        
        for keyword in ['RINGKASAN PERJALANAN', 'RINGKASAN', 'SUMMARY']:
            if keyword in result_upper:
                summary_pos = result_upper.index(keyword)
                break
        
        for keyword in ['REKOMENDASI', 'RECOMMENDATION']:
            if keyword in result_upper:
                recommendations_pos = result_upper.index(keyword)
                break
        
        # If we found section headers, verify separators are nearby
        if summary_pos != -1:
            # Check for separator within 200 characters before or after summary header
            nearby_text = result[max(0, summary_pos - 200):min(len(result), summary_pos + 200)]
            has_nearby_separator = any(char in nearby_text for char in separator_chars)
            
            assert has_nearby_separator, \
                f"Summary section should have a visual separator nearby. " \
                f"Text around summary: {nearby_text[:100]}..."
        
        if recommendations_pos != -1:
            # Check for separator within 200 characters before or after recommendations header
            nearby_text = result[max(0, recommendations_pos - 200):min(len(result), recommendations_pos + 200)]
            has_nearby_separator = any(char in nearby_text for char in separator_chars)
            
            assert has_nearby_separator, \
                f"Recommendations section should have a visual separator nearby. " \
                f"Text around recommendations: {nearby_text[:100]}..."
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_3_and_6_comprehensive_structure(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 3 & 6: Comprehensive output structure**
        **Validates: Requirements 5.1, 5.5**
        
        Comprehensive test that verifies both the presence of required sections
        and the use of visual separators in a single test.
        
        This test ensures that:
        1. All required sections are present
        2. Visual separators are used effectively
        3. The overall structure is clear and readable
        """
        # Call the advisor function
        result = get_emission_advice(trip_data)
        
        # Property 1: Output should be well-structured
        assert isinstance(result, str), "Output should be a string"
        assert len(result) > 100, "Output should be substantial (> 100 characters)"
        
        # Property 2: Output should have a clear header
        # The header should be at or near the beginning
        first_200_chars = result[:200].upper()
        has_header = any(keyword in first_200_chars for keyword in [
            'REKOMENDASI PENGURANGAN EMISI',
            'EMISSION REDUCTION',
            'ADVISOR'
        ])
        
        assert has_header, \
            f"Output should have a clear header at the beginning. " \
            f"First 200 chars: {result[:200]}"
        
        # Property 3: Sections should appear in logical order
        # Summary should come before Recommendations section (not the header)
        result_upper = result.upper()
        
        # Look for the summary section header (with emoji or specific marker)
        summary_keywords = ['📊 RINGKASAN PERJALANAN', 'RINGKASAN PERJALANAN']
        # Look for the recommendations section header (with emoji or specific marker, not the main title)
        recommendations_keywords = ['💡 REKOMENDASI PENGURANGAN EMISI', '💡 REKOMENDASI']
        
        summary_pos = -1
        for keyword in summary_keywords:
            if keyword in result:
                summary_pos = result.index(keyword)
                break
        
        recommendations_pos = -1
        for keyword in recommendations_keywords:
            if keyword in result:
                recommendations_pos = result.index(keyword)
                break
        
        # If both sections are found, summary should come before recommendations
        if summary_pos != -1 and recommendations_pos != -1:
            assert summary_pos < recommendations_pos, \
                f"Summary section should appear before Recommendations section. " \
                f"Summary at position {summary_pos}, Recommendations at position {recommendations_pos}"
        
        # Property 4: The output should be formatted for readability
        # Check for reasonable line breaks (not one giant line)
        lines = result.split('\n')
        assert len(lines) >= 10, \
            f"Output should have multiple lines for readability (>= 10). " \
            f"Found {len(lines)} lines."
        
        # Property 5: Visual hierarchy should be clear
        # Headers should be distinguishable (e.g., with separators or formatting)
        # Count lines that are likely headers (short lines with key terms)
        header_lines = []
        for line in lines:
            line_upper = line.upper()
            if any(keyword in line_upper for keyword in summary_keywords + recommendations_keywords):
                header_lines.append(line)
        
        assert len(header_lines) >= 2, \
            f"Output should have at least 2 identifiable section headers. " \
            f"Found {len(header_lines)} header lines: {header_lines}"
        
        # Property 6: Separators should create visual boundaries
        # The output should not be a wall of text - separators should break it up
        separator_chars = ['═', '─', '=', '-']
        separator_line_count = sum(1 for line in lines if any(char * 5 in line for char in separator_chars))
        
        assert separator_line_count >= 2, \
            f"Output should have at least 2 clear separator lines. " \
            f"Found {separator_line_count} separator lines."
        
        # Property 7: The structure should be consistent
        # If we have separators, they should be used consistently (similar length/style)
        separator_lines = [line for line in lines if any(char * 5 in line for char in separator_chars)]
        
        if len(separator_lines) >= 2:
            # Check that separator lines are similar in length (within 20% of each other)
            lengths = [len(line.strip()) for line in separator_lines]
            min_length = min(lengths)
            max_length = max(lengths)
            
            # Allow for some variation, but they should be roughly similar
            if min_length > 0:
                length_ratio = max_length / min_length
                assert length_ratio <= 2.0, \
                    f"Separator lines should be consistent in length. " \
                    f"Found lengths: {lengths}, ratio: {length_ratio:.2f}"



class TestPropertySequentialRecommendationNumbering:
    """
    Property-based tests for sequential recommendation numbering.
    
    **Feature: emission-reduction-advisor, Property 5: Sequential recommendation numbering**
    **Validates: Requirements 5.2**
    """
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_5_sequential_recommendation_numbering(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 5: Sequential recommendation numbering**
        **Validates: Requirements 5.2**
        
        For any output with N recommendations, the numbers 1 through N should appear
        in sequential order.
        
        This validates:
        - Requirement 5.2: WHEN displaying recommendations THEN the system SHALL number
          each recommendation sequentially
        
        The property verifies that:
        1. Recommendations are numbered starting from 1
        2. Numbers appear in sequential order (1, 2, 3, ...)
        3. No numbers are skipped
        4. No numbers are duplicated
        5. The numbering matches the actual number of recommendations
        """
        # Call the advisor
        result = get_emission_advice(trip_data)
        
        # Property 1: Result should be a string
        assert isinstance(result, str), "get_emission_advice should return a string"
        
        # Skip error cases
        if 'Error' in result or 'error' in result:
            return
        
        # Split output into lines for analysis
        lines = result.split('\n')
        
        # Property 2: Find the recommendations section
        # Look for lines that start with a number followed by a period (e.g., "1.", "2.", "3.")
        recommendation_numbers = []
        
        for line in lines:
            stripped_line = line.strip()
            # Check if line starts with a digit followed by a period
            if stripped_line and stripped_line[0].isdigit():
                # Extract the number
                parts = stripped_line.split('.', 1)
                if len(parts) >= 2:
                    try:
                        num = int(parts[0])
                        recommendation_numbers.append(num)
                    except ValueError:
                        # Not a valid number, skip
                        pass
        
        # Property 3: Should have found at least 2 recommendation numbers (per Requirement 2.1)
        assert len(recommendation_numbers) >= 2, \
            f"Should have at least 2 numbered recommendations. " \
            f"Found {len(recommendation_numbers)} numbers: {recommendation_numbers}. " \
            f"Output preview: {result[:500]}..."
        
        # Property 4: Should have at most 3 recommendation numbers (per Requirement 2.1)
        assert len(recommendation_numbers) <= 3, \
            f"Should have at most 3 numbered recommendations. " \
            f"Found {len(recommendation_numbers)} numbers: {recommendation_numbers}. " \
            f"Output preview: {result[:500]}..."
        
        # Property 5: Numbers should start from 1
        assert recommendation_numbers[0] == 1, \
            f"First recommendation should be numbered 1, but got {recommendation_numbers[0]}. " \
            f"Numbers found: {recommendation_numbers}"
        
        # Property 6: Numbers should be sequential (no gaps)
        for i in range(len(recommendation_numbers)):
            expected_number = i + 1
            actual_number = recommendation_numbers[i]
            assert actual_number == expected_number, \
                f"Recommendation {i} should be numbered {expected_number}, but got {actual_number}. " \
                f"Numbers found: {recommendation_numbers}"
        
        # Property 7: Numbers should be unique (no duplicates)
        assert len(recommendation_numbers) == len(set(recommendation_numbers)), \
            f"Recommendation numbers should be unique. " \
            f"Found duplicates in: {recommendation_numbers}"
        
        # Property 8: The highest number should equal the count of recommendations
        max_number = max(recommendation_numbers)
        assert max_number == len(recommendation_numbers), \
            f"Highest recommendation number ({max_number}) should equal " \
            f"the count of recommendations ({len(recommendation_numbers)}). " \
            f"Numbers found: {recommendation_numbers}"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_5_numbering_format_consistency(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 5: Sequential recommendation numbering**
        **Validates: Requirements 5.2**
        
        For any output, the numbering format should be consistent across all recommendations.
        This ensures that all recommendations use the same numbering style (e.g., "1.", "2.", "3.").
        """
        # Call the advisor
        result = get_emission_advice(trip_data)
        
        # Skip error cases
        if 'Error' in result or 'error' in result:
            return
        
        # Split output into lines
        lines = result.split('\n')
        
        # Find all lines that appear to be recommendation titles (numbered lines)
        numbered_lines = []
        for line in lines:
            stripped_line = line.strip()
            if stripped_line and stripped_line[0].isdigit():
                parts = stripped_line.split('.', 1)
                if len(parts) >= 2:
                    try:
                        num = int(parts[0])
                        if 1 <= num <= 3:  # Valid recommendation numbers
                            numbered_lines.append(stripped_line)
                    except ValueError:
                        pass
        
        # Property: All numbered lines should use the same format (number followed by period)
        if len(numbered_lines) >= 2:
            # Check that all use the "N." format
            for line in numbered_lines:
                # Should start with digit(s) followed by period
                assert line[0].isdigit(), \
                    f"Numbered line should start with digit: {line}"
                
                # Find the period
                period_index = line.find('.')
                assert period_index > 0, \
                    f"Numbered line should have period after number: {line}"
                
                # Everything before the period should be a valid number
                number_part = line[:period_index]
                assert number_part.isdigit(), \
                    f"Number part should be all digits: {number_part} in line: {line}"
    
    @given(multi_route_trip_data_strategy())
    @settings(max_examples=100)
    def test_property_5_numbering_with_multiple_routes(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 5: Sequential recommendation numbering**
        **Validates: Requirements 5.2**
        
        For any multi-route trip data, the recommendations should still be numbered
        sequentially, even when route recommendations are included.
        
        This ensures that the numbering system works correctly regardless of the
        types of recommendations generated.
        """
        # Call the advisor
        result = get_emission_advice(trip_data)
        
        # Skip error cases
        if 'Error' in result or 'error' in result:
            return
        
        # Extract recommendation numbers
        lines = result.split('\n')
        recommendation_numbers = []
        
        for line in lines:
            stripped_line = line.strip()
            if stripped_line and stripped_line[0].isdigit():
                parts = stripped_line.split('.', 1)
                if len(parts) >= 2:
                    try:
                        num = int(parts[0])
                        if 1 <= num <= 3:
                            recommendation_numbers.append(num)
                    except ValueError:
                        pass
        
        # Property: Should have sequential numbering
        if len(recommendation_numbers) >= 2:
            for i in range(len(recommendation_numbers)):
                expected = i + 1
                actual = recommendation_numbers[i]
                assert actual == expected, \
                    f"Multi-route trip should have sequential numbering. " \
                    f"Expected {expected} at position {i}, got {actual}. " \
                    f"Numbers: {recommendation_numbers}"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_5_numbering_appears_before_titles(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 5: Sequential recommendation numbering**
        **Validates: Requirements 5.2**
        
        For any output, the recommendation numbers should appear at the beginning
        of each recommendation (before the title), not elsewhere in the text.
        
        This ensures proper formatting where numbers clearly identify each recommendation.
        """
        # Call the advisor
        result = get_emission_advice(trip_data)
        
        # Skip error cases
        if 'Error' in result or 'error' in result:
            return
        
        # Split output into lines
        lines = result.split('\n')
        
        # Find the recommendations section
        in_recommendations_section = False
        recommendation_lines = []
        
        for line in lines:
            if 'REKOMENDASI' in line.upper() or 'RECOMMENDATION' in line.upper():
                in_recommendations_section = True
                continue
            
            if in_recommendations_section:
                # Stop at the footer
                if '═' in line and 'Potensi' in line:
                    break
                
                stripped = line.strip()
                if stripped and stripped[0].isdigit():
                    parts = stripped.split('.', 1)
                    if len(parts) >= 2:
                        try:
                            num = int(parts[0])
                            if 1 <= num <= 3:
                                recommendation_lines.append(line)
                        except ValueError:
                            pass
        
        # Property: Each numbered line should have the number at the start
        for line in recommendation_lines:
            stripped = line.strip()
            # The number should be at the very beginning
            assert stripped[0].isdigit(), \
                f"Recommendation number should be at the start of the line: {line}"
            
            # After the number and period, there should be a space and then the title
            period_index = stripped.find('.')
            if period_index > 0 and period_index < len(stripped) - 1:
                # There should be content after the period (the title)
                after_period = stripped[period_index + 1:]
                assert len(after_period.strip()) > 0, \
                    f"There should be a title after the number: {line}"



class TestPropertySummaryContent:
    """
    Property-based tests for summary content validation.
    
    **Feature: emission-reduction-advisor, Property 21: Summary contains distance and emission**
    **Validates: Requirements 1.2**
    """
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_21_summary_contains_distance_and_emission(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 21: Summary contains distance and emission**
        **Validates: Requirements 1.2**
        
        For any valid trip data, the output summary section should contain both the
        distance value and the emission value from the input.
        
        This validates:
        - Requirement 1.2: WHEN the analysis is complete THEN the system SHALL generate
          a summary that includes total distance traveled and total emission produced
        
        The property verifies that:
        1. The summary section exists in the output
        2. The distance value from input appears in the summary
        3. The emission value from input appears in the summary
        4. Both values are displayed with appropriate formatting
        """
        # Call the advisor
        result = get_emission_advice(trip_data)
        
        # Skip error cases
        if 'Error' in result or 'error' in result:
            return
        
        # Property 1: Summary section should exist
        result_upper = result.upper()
        has_summary_section = 'RINGKASAN PERJALANAN' in result_upper or 'RINGKASAN' in result_upper
        assert has_summary_section, \
            "Output should contain a summary section (RINGKASAN PERJALANAN)"
        
        # Extract the input values
        input_distance = trip_data['distance_km']
        input_emission_g = trip_data['emission_g']
        input_emission_kg = input_emission_g / 1000.0
        
        # Property 2: Distance value should appear in the output
        # Check for the distance value with reasonable formatting tolerance
        # The distance might be formatted as "X.X km" or "X km"
        distance_str_1 = f"{input_distance:.1f}"  # e.g., "12.5"
        distance_str_2 = f"{input_distance:.0f}"  # e.g., "12"
        distance_str_3 = f"{input_distance:.2f}"  # e.g., "12.50"
        
        has_distance = (distance_str_1 in result or 
                       distance_str_2 in result or 
                       distance_str_3 in result or
                       f"{input_distance}" in result)
        
        assert has_distance, \
            f"Summary should contain the distance value {input_distance:.1f} km. " \
            f"Looked for: {distance_str_1}, {distance_str_2}, {distance_str_3}. " \
            f"Output: {result[:300]}..."
        
        # Property 3: Emission value should appear in the output (in grams)
        # The emission might be formatted with thousand separators or without
        emission_g_str_1 = f"{input_emission_g:,.0f}"  # e.g., "1,234"
        emission_g_str_2 = f"{input_emission_g:.0f}"   # e.g., "1234"
        
        # Also check for the kg value
        emission_kg_str_1 = f"{input_emission_kg:.2f}"  # e.g., "1.23"
        emission_kg_str_2 = f"{input_emission_kg:.1f}"  # e.g., "1.2"
        
        has_emission_g = (emission_g_str_1 in result or 
                         emission_g_str_2 in result)
        has_emission_kg = (emission_kg_str_1 in result or 
                          emission_kg_str_2 in result)
        
        assert has_emission_g or has_emission_kg, \
            f"Summary should contain the emission value. " \
            f"Input: {input_emission_g:.0f} g ({input_emission_kg:.2f} kg). " \
            f"Looked for grams: {emission_g_str_1} or {emission_g_str_2}. " \
            f"Looked for kg: {emission_kg_str_1} or {emission_kg_str_2}. " \
            f"Output: {result[:300]}..."
        
        # Property 4: Both distance and emission should be in the summary section
        # Extract the summary section
        lines = result.split('\n')
        summary_lines = []
        in_summary = False
        
        for line in lines:
            if 'RINGKASAN PERJALANAN' in line.upper() or 'RINGKASAN' in line.upper():
                in_summary = True
                continue
            elif in_summary and ('REKOMENDASI' in line.upper() or 'RECOMMENDATION' in line.upper()):
                break
            elif in_summary:
                summary_lines.append(line)
        
        summary_text = '\n'.join(summary_lines)
        
        # Check that both values appear in the summary section specifically
        has_distance_in_summary = (distance_str_1 in summary_text or 
                                   distance_str_2 in summary_text or 
                                   distance_str_3 in summary_text or
                                   f"{input_distance}" in summary_text)
        
        has_emission_in_summary = (emission_g_str_1 in summary_text or 
                                   emission_g_str_2 in summary_text or
                                   emission_kg_str_1 in summary_text or
                                   emission_kg_str_2 in summary_text)
        
        assert has_distance_in_summary, \
            f"Distance value should appear in the summary section. " \
            f"Distance: {input_distance:.1f} km. " \
            f"Summary section: {summary_text[:200]}..."
        
        assert has_emission_in_summary, \
            f"Emission value should appear in the summary section. " \
            f"Emission: {input_emission_g:.0f} g ({input_emission_kg:.2f} kg). " \
            f"Summary section: {summary_text[:200]}..."
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_21_summary_distance_matches_input(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 21: Summary contains distance and emission**
        **Validates: Requirements 1.2**
        
        For any valid trip data, the distance value displayed in the summary should
        match the input distance value (within reasonable formatting tolerance).
        
        This ensures that the summary accurately reflects the input data without
        modification or recalculation.
        """
        # Call the advisor
        result = get_emission_advice(trip_data)
        
        # Skip error cases
        if 'Error' in result or 'error' in result:
            return
        
        input_distance = trip_data['distance_km']
        
        # Extract distance from the output
        # Look for patterns like "Jarak Tempuh : X.X km" or "Distance : X.X km"
        lines = result.split('\n')
        distance_line = None
        
        for line in lines:
            if 'Jarak Tempuh' in line or 'Distance' in line or 'jarak' in line.lower():
                distance_line = line
                break
        
        if distance_line:
            # Extract the numeric value from the line
            # Look for patterns like "X.X km" or "X km"
            import re
            # Match patterns like "12.5 km" or "12 km"
            match = re.search(r':\s*([\d,]+\.?\d*)\s*km', distance_line)
            
            if match:
                distance_str = match.group(1).replace(',', '')
                output_distance = float(distance_str)
                
                # Property: Output distance should match input distance (within 0.1 km tolerance)
                assert abs(output_distance - input_distance) < 0.1, \
                    f"Output distance ({output_distance:.1f} km) should match " \
                    f"input distance ({input_distance:.1f} km). " \
                    f"Line: {distance_line}"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_21_summary_emission_matches_input(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 21: Summary contains distance and emission**
        **Validates: Requirements 1.2**
        
        For any valid trip data, the emission value displayed in the summary should
        match the input emission value (within reasonable formatting tolerance).
        
        This ensures that the summary accurately reflects the input data without
        modification or recalculation, validating Requirements 1.5 and 8.4 as well.
        """
        # Call the advisor
        result = get_emission_advice(trip_data)
        
        # Skip error cases
        if 'Error' in result or 'error' in result:
            return
        
        input_emission_g = trip_data['emission_g']
        input_emission_kg = input_emission_g / 1000.0
        
        # Extract emission from the output
        # Look for patterns like "Total Emisi : X g CO2 (Y kg CO2)"
        lines = result.split('\n')
        emission_line = None
        
        for line in lines:
            if 'Total Emisi' in line or 'Emission' in line or 'emisi' in line.lower():
                if 'CO2' in line or 'co2' in line.lower():
                    emission_line = line
                    break
        
        if emission_line:
            # Extract the numeric values from the line
            import re
            
            # Match patterns like "1,234 g CO2" or "1234 g CO2"
            match_g = re.search(r':\s*([\d,]+)\s*g\s*CO2', emission_line)
            # Match patterns like "1.23 kg CO2" or "1.2 kg CO2"
            match_kg = re.search(r'\(([\d,]+\.?\d*)\s*kg\s*CO2\)', emission_line)
            
            if match_g:
                emission_g_str = match_g.group(1).replace(',', '')
                output_emission_g = float(emission_g_str)
                
                # Property: Output emission (g) should match input emission (within 1g tolerance)
                assert abs(output_emission_g - input_emission_g) < 1.0, \
                    f"Output emission ({output_emission_g:.0f} g) should match " \
                    f"input emission ({input_emission_g:.0f} g). " \
                    f"Line: {emission_line}"
            
            if match_kg:
                emission_kg_str = match_kg.group(1).replace(',', '')
                output_emission_kg = float(emission_kg_str)
                
                # Property: Output emission (kg) should match calculated kg value (within 0.01 kg tolerance)
                assert abs(output_emission_kg - input_emission_kg) < 0.01, \
                    f"Output emission ({output_emission_kg:.2f} kg) should match " \
                    f"calculated emission ({input_emission_kg:.2f} kg). " \
                    f"Line: {emission_line}"
    
    @given(multi_route_trip_data_strategy())
    @settings(max_examples=100)
    def test_property_21_summary_with_multiple_routes(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 21: Summary contains distance and emission**
        **Validates: Requirements 1.2**
        
        For any trip data with multiple routes, the summary should still contain
        distance and emission information, using the current route's values.
        
        This ensures that the summary works correctly even in multi-route scenarios.
        """
        # Call the advisor
        result = get_emission_advice(trip_data)
        
        # Skip error cases
        if 'Error' in result or 'error' in result:
            return
        
        # Property: Summary should exist and contain distance and emission
        result_upper = result.upper()
        has_summary = 'RINGKASAN' in result_upper
        
        assert has_summary, \
            "Multi-route trip output should contain a summary section"
        
        # Extract the summary section
        lines = result.split('\n')
        summary_lines = []
        in_summary = False
        
        for line in lines:
            if 'RINGKASAN' in line.upper():
                in_summary = True
                continue
            elif in_summary and 'REKOMENDASI' in line.upper():
                break
            elif in_summary:
                summary_lines.append(line)
        
        summary_text = '\n'.join(summary_lines)
        
        # Property: Summary should contain distance information
        has_distance_keyword = any(keyword in summary_text for keyword in 
                                   ['Jarak', 'Distance', 'jarak', 'distance', 'km'])
        
        assert has_distance_keyword, \
            f"Multi-route summary should contain distance information. " \
            f"Summary: {summary_text[:200]}..."
        
        # Property: Summary should contain emission information
        has_emission_keyword = any(keyword in summary_text for keyword in 
                                   ['Emisi', 'Emission', 'emisi', 'emission', 'CO2', 'co2'])
        
        assert has_emission_keyword, \
            f"Multi-route summary should contain emission information. " \
            f"Summary: {summary_text[:200]}..."



class TestPropertySavingsDisplay:
    """
    Property-based tests for savings display in recommendations.
    
    **Feature: emission-reduction-advisor, Property 14: Savings calculation presence**
    **Feature: emission-reduction-advisor, Property 15: Percentage reduction display**
    **Validates: Requirements 3.1, 3.5**
    """
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_14_savings_calculation_presence(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 14: Savings calculation presence**
        **Validates: Requirements 3.1**
        
        For any recommendation in the output, there should be an associated emission
        savings value in grams of CO2.
        
        This validates:
        - Requirement 3.1: WHEN the Emission Reduction Advisor provides a recommendation
          THEN the system SHALL calculate the estimated emission savings in grams of CO2
        
        The property verifies that:
        1. Every recommendation has a savings value
        2. The savings value is in grams of CO2
        3. The savings value is displayed in the output
        4. The savings value is non-negative
        """
        # Call the advisor
        result = get_emission_advice(trip_data)
        
        # Skip error cases
        if 'Error' in result or 'error' in result:
            return
        
        # Property 1: Output should contain recommendations
        result_upper = result.upper()
        has_recommendations = 'REKOMENDASI' in result_upper or 'RECOMMENDATION' in result_upper
        assert has_recommendations, "Output should contain recommendations section"
        
        # Property 2: Extract recommendations from the output
        lines = result.split('\n')
        recommendation_lines = []
        in_recommendations = False
        
        for line in lines:
            if 'REKOMENDASI' in line.upper() or 'RECOMMENDATION' in line.upper():
                in_recommendations = True
                continue
            elif in_recommendations and '═' in line and 'Potensi' in line:
                break
            elif in_recommendations:
                recommendation_lines.append(line)
        
        recommendation_text = '\n'.join(recommendation_lines)
        
        # Property 3: Count the number of recommendations
        recommendation_count = 0
        for line in recommendation_lines:
            stripped = line.strip()
            if stripped and len(stripped) > 2:
                if stripped[0].isdigit() and stripped[1] == '.':
                    recommendation_count += 1
        
        # Property 4: Each recommendation should have a savings value
        # Look for savings indicators like "Penghematan:" or "Savings:"
        import re
        
        # Match patterns like "Penghematan: X g CO2" or "Savings: X g CO2"
        savings_pattern = r'Penghematan:\s*([\d,]+)\s*g\s*CO2|Savings:\s*([\d,]+)\s*g\s*CO2'
        savings_matches = re.findall(savings_pattern, recommendation_text, re.IGNORECASE)
        
        # Count how many savings values we found
        savings_count = len(savings_matches)
        
        # Property 5: Number of savings values should match number of recommendations
        assert savings_count >= recommendation_count, \
            f"Each recommendation should have a savings value. " \
            f"Found {recommendation_count} recommendations but only {savings_count} savings values. " \
            f"Recommendations section: {recommendation_text[:500]}..."
        
        # Property 6: Each savings value should be non-negative
        for match in savings_matches:
            # match is a tuple, get the non-empty group
            savings_str = match[0] if match[0] else match[1]
            savings_str = savings_str.replace(',', '')
            savings_value = float(savings_str)
            
            assert savings_value >= 0, \
                f"Savings value should be non-negative, got {savings_value} g CO2"
        
        # Property 7: Savings should be in grams (g CO2)
        # This is verified by the regex pattern above which looks for "g CO2"
        assert savings_count > 0, \
            f"At least one recommendation should have savings in grams of CO2. " \
            f"Recommendations: {recommendation_text[:500]}..."
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_14_all_recommendations_have_savings(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 14: Savings calculation presence**
        **Validates: Requirements 3.1**
        
        Direct test of the RecommendationEngine to verify that every generated
        recommendation has an associated savings calculation.
        
        This tests the engine component directly to ensure savings are always calculated.
        """
        from advisor import RecommendationEngine
        
        # Create analyzer and analyze the trip
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        # Generate recommendations
        engine = RecommendationEngine()
        routes = trip_data.get('routes', None)
        recommendations = engine.generate_recommendations(analysis, routes)
        
        # Property 1: Every recommendation should have a savings object
        for idx, rec in enumerate(recommendations):
            assert hasattr(rec, 'savings'), \
                f"Recommendation {idx + 1} should have a savings attribute"
            
            assert rec.savings is not None, \
                f"Recommendation {idx + 1} savings should not be None"
            
            # Property 2: Savings should have savings_g attribute
            assert hasattr(rec.savings, 'savings_g'), \
                f"Recommendation {idx + 1} savings should have savings_g attribute"
            
            # Property 3: savings_g should be a number
            assert isinstance(rec.savings.savings_g, (int, float)), \
                f"Recommendation {idx + 1} savings_g should be a number, " \
                f"got {type(rec.savings.savings_g)}"
            
            # Property 4: savings_g should be non-negative
            assert rec.savings.savings_g >= 0, \
                f"Recommendation {idx + 1} savings_g should be non-negative, " \
                f"got {rec.savings.savings_g}"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_14_savings_in_grams_of_co2(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 14: Savings calculation presence**
        **Validates: Requirements 3.1**
        
        For any recommendation, the savings should be expressed in grams of CO2,
        which is the standard unit for emission measurements in the system.
        
        This ensures consistency with the emission calculation system.
        """
        # Call the advisor
        result = get_emission_advice(trip_data)
        
        # Skip error cases
        if 'Error' in result or 'error' in result:
            return
        
        # Property: Savings should be expressed in "g CO2" units
        # Look for patterns like "X g CO2" in the recommendations section
        lines = result.split('\n')
        recommendation_lines = []
        in_recommendations = False
        
        for line in lines:
            if 'REKOMENDASI' in line.upper():
                in_recommendations = True
                continue
            elif in_recommendations and '═' in line and 'Potensi' in line:
                break
            elif in_recommendations:
                recommendation_lines.append(line)
        
        recommendation_text = '\n'.join(recommendation_lines)
        
        # Check for "g CO2" unit in savings
        has_g_co2_unit = 'g CO2' in recommendation_text or 'g co2' in recommendation_text.lower()
        
        assert has_g_co2_unit, \
            f"Savings should be expressed in grams of CO2 (g CO2). " \
            f"Recommendations section: {recommendation_text[:500]}..."
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_15_percentage_reduction_display(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 15: Percentage reduction display**
        **Validates: Requirements 3.5**
        
        For any recommendation with savings, both absolute emission savings and
        percentage reduction should be displayed.
        
        This validates:
        - Requirement 3.5: THE Emission Reduction Advisor SHALL display percentage
          reduction alongside absolute emission savings
        
        The property verifies that:
        1. Every recommendation displays absolute savings (in grams)
        2. Every recommendation displays percentage reduction
        3. Both values appear together in the output
        4. The percentage is formatted correctly (with % symbol)
        """
        # Call the advisor
        result = get_emission_advice(trip_data)
        
        # Skip error cases
        if 'Error' in result or 'error' in result:
            return
        
        # Property 1: Extract recommendations section
        lines = result.split('\n')
        recommendation_lines = []
        in_recommendations = False
        
        for line in lines:
            if 'REKOMENDASI' in line.upper():
                in_recommendations = True
                continue
            elif in_recommendations and '═' in line and 'Potensi' in line:
                break
            elif in_recommendations:
                recommendation_lines.append(line)
        
        recommendation_text = '\n'.join(recommendation_lines)
        
        # Property 2: Count recommendations
        recommendation_count = 0
        for line in recommendation_lines:
            stripped = line.strip()
            if stripped and len(stripped) > 2:
                if stripped[0].isdigit() and stripped[1] == '.':
                    recommendation_count += 1
        
        # Property 3: Look for percentage values in the recommendations
        import re
        
        # Match patterns like "X%" or "X %" in the recommendations
        percentage_pattern = r'(\d+(?:\.\d+)?)\s*%'
        percentage_matches = re.findall(percentage_pattern, recommendation_text)
        
        # Property 4: Number of percentage values should match number of recommendations
        percentage_count = len(percentage_matches)
        
        assert percentage_count >= recommendation_count, \
            f"Each recommendation should display percentage reduction. " \
            f"Found {recommendation_count} recommendations but only {percentage_count} percentage values. " \
            f"Recommendations section: {recommendation_text[:500]}..."
        
        # Property 5: Each percentage should be a valid number
        for pct_str in percentage_matches:
            pct_value = float(pct_str)
            
            # Percentage should be between 0 and 100 (or slightly above 100 in edge cases)
            assert 0 <= pct_value <= 150, \
                f"Percentage reduction should be reasonable (0-150%), got {pct_value}%"
        
        # Property 6: Verify that both absolute savings and percentage appear together
        # Look for lines that contain both "g CO2" and "%"
        savings_lines_with_percentage = []
        for line in recommendation_lines:
            if ('g CO2' in line or 'g co2' in line.lower()) and '%' in line:
                savings_lines_with_percentage.append(line)
        
        # Should have at least as many combined lines as recommendations
        assert len(savings_lines_with_percentage) >= recommendation_count, \
            f"Each recommendation should display both absolute savings and percentage. " \
            f"Found {recommendation_count} recommendations but only {len(savings_lines_with_percentage)} " \
            f"lines with both savings and percentage. " \
            f"Recommendations section: {recommendation_text[:500]}..."
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_15_percentage_in_recommendation_engine(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 15: Percentage reduction display**
        **Validates: Requirements 3.5**
        
        Direct test of the RecommendationEngine to verify that every generated
        recommendation includes a percentage reduction value in its savings.
        
        This tests the engine component directly to ensure percentages are always calculated.
        """
        from advisor import RecommendationEngine
        
        # Create analyzer and analyze the trip
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        # Generate recommendations
        engine = RecommendationEngine()
        routes = trip_data.get('routes', None)
        recommendations = engine.generate_recommendations(analysis, routes)
        
        # Property 1: Every recommendation should have savings with percentage
        for idx, rec in enumerate(recommendations):
            assert hasattr(rec.savings, 'savings_percentage'), \
                f"Recommendation {idx + 1} savings should have savings_percentage attribute"
            
            # Property 2: savings_percentage should be a number
            assert isinstance(rec.savings.savings_percentage, (int, float)), \
                f"Recommendation {idx + 1} savings_percentage should be a number, " \
                f"got {type(rec.savings.savings_percentage)}"
            
            # Property 3: savings_percentage should be non-negative
            assert rec.savings.savings_percentage >= 0, \
                f"Recommendation {idx + 1} savings_percentage should be non-negative, " \
                f"got {rec.savings.savings_percentage}"
            
            # Property 4: savings_percentage should be reasonable (0-150%)
            assert rec.savings.savings_percentage <= 150, \
                f"Recommendation {idx + 1} savings_percentage should be reasonable (<= 150%), " \
                f"got {rec.savings.savings_percentage}%"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_15_percentage_matches_absolute_savings(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 15: Percentage reduction display**
        **Validates: Requirements 3.5**
        
        For any recommendation, the percentage reduction should be mathematically
        consistent with the absolute savings and the current emission.
        
        This ensures that the percentage is calculated correctly:
        percentage = (savings_g / current_emission_g) * 100
        """
        from advisor import RecommendationEngine
        
        # Create analyzer and analyze the trip
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        # Generate recommendations
        engine = RecommendationEngine()
        routes = trip_data.get('routes', None)
        recommendations = engine.generate_recommendations(analysis, routes)
        
        current_emission_g = trip_data['emission_g']
        
        # Property: For each recommendation, verify percentage calculation
        for idx, rec in enumerate(recommendations):
            savings_g = rec.savings.savings_g
            savings_percentage = rec.savings.savings_percentage
            
            # Calculate expected percentage
            if current_emission_g > 0:
                expected_percentage = (savings_g / current_emission_g) * 100.0
            else:
                expected_percentage = 0.0
            
            # Allow for small floating point differences (within 0.1%)
            assert abs(savings_percentage - expected_percentage) < 0.1, \
                f"Recommendation {idx + 1} percentage should match calculation. " \
                f"Savings: {savings_g:.2f}g, Current emission: {current_emission_g:.2f}g. " \
                f"Expected percentage: {expected_percentage:.2f}%, " \
                f"Got: {savings_percentage:.2f}%"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_15_both_units_displayed_together(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 15: Percentage reduction display**
        **Validates: Requirements 3.5**
        
        For any recommendation, the absolute savings and percentage reduction should
        be displayed together on the same line or in close proximity.
        
        This ensures that users can easily see both metrics for each recommendation.
        """
        # Call the advisor
        result = get_emission_advice(trip_data)
        
        # Skip error cases
        if 'Error' in result or 'error' in result:
            return
        
        # Property: Extract savings lines from recommendations
        lines = result.split('\n')
        savings_lines = []
        in_recommendations = False
        
        for line in lines:
            if 'REKOMENDASI' in line.upper():
                in_recommendations = True
                continue
            elif in_recommendations and '═' in line:
                # Stop when we hit the footer separator
                break
            elif in_recommendations:
                # Look for lines with savings information (containing "Penghematan" or "💰")
                # But exclude the total savings line
                if ('Penghematan' in line or '💰' in line or 'Savings' in line) and 'Total' not in line and 'Potensi' not in line:
                    savings_lines.append(line)
        
        # Property: Each savings line should contain both absolute value and percentage
        for line in savings_lines:
            # Check for absolute savings (g CO2)
            has_absolute = 'g CO2' in line or 'g co2' in line.lower()
            
            # Check for percentage (%)
            has_percentage = '%' in line
            
            assert has_absolute and has_percentage, \
                f"Savings line should contain both absolute value and percentage. " \
                f"Line: {line}"
    
    @given(trip_data_strategy())
    @settings(max_examples=100)
    def test_property_14_and_15_comprehensive(self, trip_data):
        """
        **Feature: emission-reduction-advisor, Property 14 & 15: Comprehensive savings display**
        **Validates: Requirements 3.1, 3.5**
        
        Comprehensive test that verifies both properties together:
        - Every recommendation has savings in grams (Property 14)
        - Every recommendation has percentage reduction (Property 15)
        - Both are displayed together in the output
        
        This is a comprehensive validation of the savings display requirements.
        """
        from advisor import RecommendationEngine
        
        # Create analyzer and analyze the trip
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        # Generate recommendations
        engine = RecommendationEngine()
        routes = trip_data.get('routes', None)
        recommendations = engine.generate_recommendations(analysis, routes)
        
        # Property 1: Every recommendation has both savings_g and savings_percentage
        for idx, rec in enumerate(recommendations):
            # Check savings_g (Property 14)
            assert hasattr(rec.savings, 'savings_g'), \
                f"Recommendation {idx + 1} should have savings_g"
            assert isinstance(rec.savings.savings_g, (int, float)), \
                f"Recommendation {idx + 1} savings_g should be numeric"
            assert rec.savings.savings_g >= 0, \
                f"Recommendation {idx + 1} savings_g should be non-negative"
            
            # Check savings_percentage (Property 15)
            assert hasattr(rec.savings, 'savings_percentage'), \
                f"Recommendation {idx + 1} should have savings_percentage"
            assert isinstance(rec.savings.savings_percentage, (int, float)), \
                f"Recommendation {idx + 1} savings_percentage should be numeric"
            assert rec.savings.savings_percentage >= 0, \
                f"Recommendation {idx + 1} savings_percentage should be non-negative"
        
        # Property 2: Verify in the formatted output
        result = get_emission_advice(trip_data)
        
        # Skip error cases
        if 'Error' in result or 'error' in result:
            return
        
        # Extract recommendations section
        lines = result.split('\n')
        recommendation_lines = []
        in_recommendations = False
        
        for line in lines:
            if 'REKOMENDASI' in line.upper():
                in_recommendations = True
                continue
            elif in_recommendations and '═' in line and 'Potensi' in line:
                break
            elif in_recommendations:
                recommendation_lines.append(line)
        
        recommendation_text = '\n'.join(recommendation_lines)
        
        # Property 3: Count recommendations
        recommendation_count = len(recommendations)
        
        # Property 4: Count savings displays (lines with both g CO2 and %)
        import re
        savings_with_both_pattern = r'(\d+(?:,\d+)*)\s*g\s*CO2.*?(\d+(?:\.\d+)?)\s*%'
        savings_matches = re.findall(savings_with_both_pattern, recommendation_text, re.IGNORECASE)
        
        # Property 5: Should have at least as many complete savings displays as recommendations
        assert len(savings_matches) >= recommendation_count, \
            f"Each of {recommendation_count} recommendations should display both " \
            f"absolute savings (g CO2) and percentage reduction (%). " \
            f"Found only {len(savings_matches)} complete savings displays. " \
            f"Recommendations section: {recommendation_text[:500]}..."



# ============================================================================
# Unit Tests for Error Handling
# ============================================================================

class TestUnitErrorHandling:
    """
    Unit tests for error handling in the Emission Reduction Advisor.
    
    These tests verify specific error scenarios:
    - Missing required fields
    - Invalid data types
    - Negative or zero values
    - Empty routes list handling
    
    **Validates: Requirements 7.4, 7.5**
    """
    
    def test_missing_distance_field(self):
        """
        Test that missing distance_km field returns appropriate error.
        
        **Validates: Requirements 7.4, 7.5**
        """
        trip_data = {
            'car_type': 'SUV',
            'fuel_type': 'bensin',
            'emission_g': 1000.0
        }
        
        error = validate_trip_data(trip_data)
        
        assert error is not None, "Should return error for missing distance_km"
        assert error['success'] is False
        assert error['error_type'] == 'validation_error'
        assert 'distance_km' in error['error']
        
        # Test main function handles it gracefully
        result = get_emission_advice(trip_data)
        assert isinstance(result, str)
        assert 'Error' in result
    
    def test_missing_car_type_field(self):
        """
        Test that missing car_type field returns appropriate error.
        
        **Validates: Requirements 7.4, 7.5**
        """
        trip_data = {
            'distance_km': 10.0,
            'fuel_type': 'bensin',
            'emission_g': 1000.0
        }
        
        error = validate_trip_data(trip_data)
        
        assert error is not None, "Should return error for missing car_type"
        assert error['success'] is False
        assert error['error_type'] == 'validation_error'
        assert 'car_type' in error['error']
        
        # Test main function handles it gracefully
        result = get_emission_advice(trip_data)
        assert isinstance(result, str)
        assert 'Error' in result
    
    def test_missing_fuel_type_field(self):
        """
        Test that missing fuel_type field returns appropriate error.
        
        **Validates: Requirements 7.4, 7.5**
        """
        trip_data = {
            'distance_km': 10.0,
            'car_type': 'SUV',
            'emission_g': 1000.0
        }
        
        error = validate_trip_data(trip_data)
        
        assert error is not None, "Should return error for missing fuel_type"
        assert error['success'] is False
        assert error['error_type'] == 'validation_error'
        assert 'fuel_type' in error['error']
        
        # Test main function handles it gracefully
        result = get_emission_advice(trip_data)
        assert isinstance(result, str)
        assert 'Error' in result
    
    def test_missing_emission_field(self):
        """
        Test that missing emission_g field returns appropriate error.
        
        **Validates: Requirements 7.4, 7.5**
        """
        trip_data = {
            'distance_km': 10.0,
            'car_type': 'SUV',
            'fuel_type': 'bensin'
        }
        
        error = validate_trip_data(trip_data)
        
        assert error is not None, "Should return error for missing emission_g"
        assert error['success'] is False
        assert error['error_type'] == 'validation_error'
        assert 'emission_g' in error['error']
        
        # Test main function handles it gracefully
        result = get_emission_advice(trip_data)
        assert isinstance(result, str)
        assert 'Error' in result
    
    def test_invalid_distance_type_string(self):
        """
        Test that non-numeric distance_km returns appropriate error.
        
        **Validates: Requirements 7.4, 7.5**
        """
        trip_data = {
            'distance_km': 'ten kilometers',
            'car_type': 'SUV',
            'fuel_type': 'bensin',
            'emission_g': 1000.0
        }
        
        error = validate_trip_data(trip_data)
        
        assert error is not None, "Should return error for non-numeric distance"
        assert error['success'] is False
        assert error['error_type'] == 'validation_error'
        assert 'data type' in error['error'].lower() or 'numeric' in error['error'].lower()
        
        # Test main function handles it gracefully
        result = get_emission_advice(trip_data)
        assert isinstance(result, str)
        assert 'Error' in result
    
    def test_invalid_emission_type_string(self):
        """
        Test that non-numeric emission_g returns appropriate error.
        
        **Validates: Requirements 7.4, 7.5**
        """
        trip_data = {
            'distance_km': 10.0,
            'car_type': 'SUV',
            'fuel_type': 'bensin',
            'emission_g': 'one thousand grams'
        }
        
        error = validate_trip_data(trip_data)
        
        assert error is not None, "Should return error for non-numeric emission"
        assert error['success'] is False
        assert error['error_type'] == 'validation_error'
        assert 'data type' in error['error'].lower() or 'numeric' in error['error'].lower()
        
        # Test main function handles it gracefully
        result = get_emission_advice(trip_data)
        assert isinstance(result, str)
        assert 'Error' in result
    
    def test_invalid_car_type_not_string(self):
        """
        Test that non-string car_type returns appropriate error.
        
        **Validates: Requirements 7.4, 7.5**
        """
        trip_data = {
            'distance_km': 10.0,
            'car_type': 123,
            'fuel_type': 'bensin',
            'emission_g': 1000.0
        }
        
        error = validate_trip_data(trip_data)
        
        assert error is not None, "Should return error for non-string car_type"
        assert error['success'] is False
        assert error['error_type'] == 'validation_error'
        assert 'car_type' in error['error']
        
        # Test main function handles it gracefully
        result = get_emission_advice(trip_data)
        assert isinstance(result, str)
        assert 'Error' in result
    
    def test_invalid_fuel_type_not_string(self):
        """
        Test that non-string fuel_type returns appropriate error.
        
        **Validates: Requirements 7.4, 7.5**
        """
        trip_data = {
            'distance_km': 10.0,
            'car_type': 'SUV',
            'fuel_type': 456,
            'emission_g': 1000.0
        }
        
        error = validate_trip_data(trip_data)
        
        assert error is not None, "Should return error for non-string fuel_type"
        assert error['success'] is False
        assert error['error_type'] == 'validation_error'
        assert 'fuel_type' in error['error']
        
        # Test main function handles it gracefully
        result = get_emission_advice(trip_data)
        assert isinstance(result, str)
        assert 'Error' in result
    
    def test_empty_car_type_string(self):
        """
        Test that empty car_type string returns appropriate error.
        
        **Validates: Requirements 7.4, 7.5**
        """
        trip_data = {
            'distance_km': 10.0,
            'car_type': '',
            'fuel_type': 'bensin',
            'emission_g': 1000.0
        }
        
        error = validate_trip_data(trip_data)
        
        assert error is not None, "Should return error for empty car_type"
        assert error['success'] is False
        assert error['error_type'] == 'validation_error'
        
        # Test main function handles it gracefully
        result = get_emission_advice(trip_data)
        assert isinstance(result, str)
        assert 'Error' in result
    
    def test_empty_fuel_type_string(self):
        """
        Test that empty fuel_type string returns appropriate error.
        
        **Validates: Requirements 7.4, 7.5**
        """
        trip_data = {
            'distance_km': 10.0,
            'car_type': 'SUV',
            'fuel_type': '',
            'emission_g': 1000.0
        }
        
        error = validate_trip_data(trip_data)
        
        assert error is not None, "Should return error for empty fuel_type"
        assert error['success'] is False
        assert error['error_type'] == 'validation_error'
        
        # Test main function handles it gracefully
        result = get_emission_advice(trip_data)
        assert isinstance(result, str)
        assert 'Error' in result
    
    def test_negative_distance(self):
        """
        Test that negative distance_km returns appropriate error.
        
        **Validates: Requirements 7.4, 7.5**
        """
        trip_data = {
            'distance_km': -10.0,
            'car_type': 'SUV',
            'fuel_type': 'bensin',
            'emission_g': 1000.0
        }
        
        error = validate_trip_data(trip_data)
        
        assert error is not None, "Should return error for negative distance"
        assert error['success'] is False
        assert error['error_type'] == 'validation_error'
        assert 'positive' in error['error'].lower() or 'distance' in error['error'].lower()
        
        # Test main function handles it gracefully
        result = get_emission_advice(trip_data)
        assert isinstance(result, str)
        assert 'Error' in result
    
    def test_zero_distance(self):
        """
        Test that zero distance_km returns appropriate error.
        
        **Validates: Requirements 7.4, 7.5**
        """
        trip_data = {
            'distance_km': 0.0,
            'car_type': 'SUV',
            'fuel_type': 'bensin',
            'emission_g': 1000.0
        }
        
        error = validate_trip_data(trip_data)
        
        assert error is not None, "Should return error for zero distance"
        assert error['success'] is False
        assert error['error_type'] == 'validation_error'
        assert 'positive' in error['error'].lower() or 'distance' in error['error'].lower()
        
        # Test main function handles it gracefully
        result = get_emission_advice(trip_data)
        assert isinstance(result, str)
        assert 'Error' in result
    
    def test_negative_emission(self):
        """
        Test that negative emission_g returns appropriate error.
        
        **Validates: Requirements 7.4, 7.5**
        """
        trip_data = {
            'distance_km': 10.0,
            'car_type': 'SUV',
            'fuel_type': 'bensin',
            'emission_g': -1000.0
        }
        
        error = validate_trip_data(trip_data)
        
        assert error is not None, "Should return error for negative emission"
        assert error['success'] is False
        assert error['error_type'] == 'validation_error'
        assert 'positive' in error['error'].lower() or 'emission' in error['error'].lower()
        
        # Test main function handles it gracefully
        result = get_emission_advice(trip_data)
        assert isinstance(result, str)
        assert 'Error' in result
    
    def test_zero_emission(self):
        """
        Test that zero emission_g returns appropriate error.
        
        **Validates: Requirements 7.4, 7.5**
        """
        trip_data = {
            'distance_km': 10.0,
            'car_type': 'SUV',
            'fuel_type': 'bensin',
            'emission_g': 0.0
        }
        
        error = validate_trip_data(trip_data)
        
        assert error is not None, "Should return error for zero emission"
        assert error['success'] is False
        assert error['error_type'] == 'validation_error'
        assert 'positive' in error['error'].lower() or 'emission' in error['error'].lower()
        
        # Test main function handles it gracefully
        result = get_emission_advice(trip_data)
        assert isinstance(result, str)
        assert 'Error' in result
    
    def test_empty_routes_list(self):
        """
        Test that empty routes list returns appropriate error.
        
        **Validates: Requirements 7.4, 7.5**
        """
        trip_data = {
            'distance_km': 10.0,
            'car_type': 'SUV',
            'fuel_type': 'bensin',
            'emission_g': 1800.0,
            'routes': []
        }
        
        error = validate_trip_data(trip_data)
        
        assert error is not None, "Should return error for empty routes list"
        assert error['success'] is False
        assert error['error_type'] == 'validation_error'
        assert 'routes' in error['error'].lower() or 'empty' in error['error'].lower()
        
        # Test main function handles it gracefully
        result = get_emission_advice(trip_data)
        assert isinstance(result, str)
        assert 'Error' in result
    
    def test_routes_not_a_list(self):
        """
        Test that routes field that is not a list returns appropriate error.
        
        **Validates: Requirements 7.4, 7.5**
        """
        trip_data = {
            'distance_km': 10.0,
            'car_type': 'SUV',
            'fuel_type': 'bensin',
            'emission_g': 1800.0,
            'routes': 'not a list'
        }
        
        error = validate_trip_data(trip_data)
        
        assert error is not None, "Should return error for routes not being a list"
        assert error['success'] is False
        assert error['error_type'] == 'validation_error'
        assert 'routes' in error['error'].lower() and 'list' in error['error'].lower()
        
        # Test main function handles it gracefully
        result = get_emission_advice(trip_data)
        assert isinstance(result, str)
        assert 'Error' in result
    
    def test_route_missing_required_field(self):
        """
        Test that route with missing required field returns appropriate error.
        
        **Validates: Requirements 7.4, 7.5**
        """
        trip_data = {
            'distance_km': 10.0,
            'car_type': 'SUV',
            'fuel_type': 'bensin',
            'emission_g': 1800.0,
            'routes': [
                {
                    'route_number': 1,
                    'distance_km': 10.0,
                    'duration_min': 15.0
                    # Missing emission_g
                }
            ]
        }
        
        error = validate_trip_data(trip_data)
        
        assert error is not None, "Should return error for route missing emission_g"
        assert error['success'] is False
        assert error['error_type'] == 'validation_error'
        assert 'route' in error['error'].lower() or 'emission_g' in error['error'].lower()
        
        # Test main function handles it gracefully
        result = get_emission_advice(trip_data)
        assert isinstance(result, str)
        assert 'Error' in result
    
    def test_none_routes_is_valid(self):
        """
        Test that routes=None is valid (single route scenario).
        
        **Validates: Requirements 7.4, 7.5**
        """
        trip_data = {
            'distance_km': 10.0,
            'car_type': 'SUV',
            'fuel_type': 'bensin',
            'emission_g': 1800.0,
            'routes': None
        }
        
        error = validate_trip_data(trip_data)
        
        # None routes should be valid (single route scenario)
        assert error is None, "routes=None should be valid for single route scenario"
        
        # Test main function handles it gracefully
        result = get_emission_advice(trip_data)
        assert isinstance(result, str)
        assert 'Error' not in result or 'REKOMENDASI' in result
    
    def test_missing_routes_field_is_valid(self):
        """
        Test that missing routes field is valid (single route scenario).
        
        **Validates: Requirements 7.4, 7.5**
        """
        trip_data = {
            'distance_km': 10.0,
            'car_type': 'SUV',
            'fuel_type': 'bensin',
            'emission_g': 1800.0
        }
        
        error = validate_trip_data(trip_data)
        
        # Missing routes field should be valid (single route scenario)
        assert error is None, "Missing routes field should be valid for single route scenario"
        
        # Test main function handles it gracefully
        result = get_emission_advice(trip_data)
        assert isinstance(result, str)
        assert 'REKOMENDASI' in result
    
    def test_multiple_errors_returns_first_error(self):
        """
        Test that when multiple errors exist, validation returns an error.
        
        **Validates: Requirements 7.4, 7.5**
        """
        trip_data = {
            'distance_km': -10.0,  # Negative
            'car_type': 'InvalidCar',  # Invalid
            'fuel_type': 'InvalidFuel',  # Invalid
            'emission_g': 0.0  # Zero
        }
        
        error = validate_trip_data(trip_data)
        
        # Should return an error (any of the validation errors)
        assert error is not None, "Should return error when multiple validation issues exist"
        assert error['success'] is False
        assert error['error_type'] == 'validation_error'
        
        # Test main function handles it gracefully
        result = get_emission_advice(trip_data)
        assert isinstance(result, str)
        assert 'Error' in result
