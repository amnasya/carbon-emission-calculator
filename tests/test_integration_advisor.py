"""
Integration tests for Emission Reduction Advisor with main application flow.

This test suite verifies that the advisor integrates correctly with the main
application without breaking existing workflows.

Requirements Addressed:
- 4.5: Optional invocation without breaking existing workflows
"""

import pytest
from unittest.mock import patch, MagicMock
from advisor import get_emission_advice
from emission import EMISSION_FACTORS, get_emission_factor


class TestAdvisorIntegration:
    """
    Integration tests for advisor module with main application flow.
    
    **Validates: Requirements 4.5**
    """
    
    def test_advisor_can_be_called_from_main_flow(self):
        """
        Test that advisor can be called from main flow.
        
        This test verifies that the advisor can be invoked with trip data
        constructed from the main application's variables (distance, car_type,
        fuel_type, emission) and returns a properly formatted string output.
        
        **Validates: Requirements 4.5**
        """
        # Simulate data that would be available in main.py after route calculation
        distance_km = 12.5
        car_type = "SUV"
        fuel_type = "bensin"
        emission_factor = get_emission_factor(car_type, fuel_type)
        emission_g = distance_km * emission_factor
        
        # Construct trip data dictionary as main.py would
        trip_data = {
            'distance_km': distance_km,
            'car_type': car_type,
            'fuel_type': fuel_type,
            'emission_g': emission_g
        }
        
        # Call advisor
        result = get_emission_advice(trip_data)
        
        # Verify result is a string
        assert isinstance(result, str), "Advisor should return a string"
        
        # Verify result contains expected sections
        assert "REKOMENDASI PENGURANGAN EMISI KARBON" in result, \
            "Result should contain header"
        assert "RINGKASAN PERJALANAN" in result, \
            "Result should contain summary section"
        assert "REKOMENDASI PENGURANGAN EMISI" in result, \
            "Result should contain recommendations section"
        
        # Verify result contains trip data
        assert str(distance_km) in result or f"{distance_km:.1f}" in result, \
            "Result should contain distance"
        assert car_type in result, "Result should contain vehicle type"
        assert fuel_type in result, "Result should contain fuel type"
    
    def test_advisor_works_with_single_route_scenario(self):
        """
        Test that advisor works correctly with single route scenario.
        
        This test simulates the case where the user gets a single route from
        the maps API and the advisor is called with that data. The advisor
        should generate appropriate recommendations without route comparison.
        
        **Validates: Requirements 4.5**
        """
        # Simulate single route scenario (no routes list)
        distance_km = 8.3
        car_type = "LCGC"
        fuel_type = "bensin"
        emission_factor = get_emission_factor(car_type, fuel_type)
        emission_g = distance_km * emission_factor
        
        trip_data = {
            'distance_km': distance_km,
            'car_type': car_type,
            'fuel_type': fuel_type,
            'emission_g': emission_g
            # No 'routes' key - single route scenario
        }
        
        # Call advisor
        result = get_emission_advice(trip_data)
        
        # Verify result is valid
        assert isinstance(result, str), "Advisor should return a string"
        assert "Error" not in result or "REKOMENDASI" in result, \
            "Advisor should not error on single route scenario"
        
        # Verify result contains recommendations
        assert "REKOMENDASI PENGURANGAN EMISI" in result, \
            "Result should contain recommendations section"
        
        # Verify result contains trip summary
        assert "RINGKASAN PERJALANAN" in result, \
            "Result should contain summary section"
        assert str(distance_km) in result or f"{distance_km:.1f}" in result, \
            "Result should contain distance"
        
        # For medium distance (5-15km), should recommend public transport
        assert "transportasi umum" in result.lower() or "public" in result.lower(), \
            "For medium distance, should recommend public transportation"
    
    def test_advisor_works_with_multi_route_scenario(self):
        """
        Test that advisor works correctly with multi-route scenario.
        
        This test simulates the case where the user gets multiple alternative
        routes from the maps API. The advisor should analyze all routes and
        recommend the one with lowest emission if the current route is not optimal.
        
        **Validates: Requirements 4.5**
        """
        # Simulate multi-route scenario as constructed in main.py
        car_type = "SUV"
        fuel_type = "solar"
        emission_factor = get_emission_factor(car_type, fuel_type)
        
        # Create multiple routes with different distances
        routes = [
            {
                'route_number': 1,
                'distance_km': 15.2,
                'duration_min': 25.0,
                'emission_g': 15.2 * emission_factor
            },
            {
                'route_number': 2,
                'distance_km': 13.8,  # Shorter route - lower emission
                'duration_min': 28.0,
                'emission_g': 13.8 * emission_factor
            },
            {
                'route_number': 3,
                'distance_km': 16.5,
                'duration_min': 23.0,
                'emission_g': 16.5 * emission_factor
            }
        ]
        
        # Use first route as current trip (as main.py does)
        trip_data = {
            'distance_km': routes[0]['distance_km'],
            'car_type': car_type,
            'fuel_type': fuel_type,
            'emission_g': routes[0]['emission_g'],
            'routes': routes
        }
        
        # Call advisor
        result = get_emission_advice(trip_data)
        
        # Verify result is valid
        assert isinstance(result, str), "Advisor should return a string"
        assert "Error" not in result or "REKOMENDASI" in result, \
            "Advisor should not error on multi-route scenario"
        
        # Verify result contains recommendations
        assert "REKOMENDASI PENGURANGAN EMISI" in result, \
            "Result should contain recommendations section"
        
        # Since route 2 has lower emission than route 1 (current),
        # advisor should recommend switching routes
        result_lower = result.lower()
        assert "rute" in result_lower or "route" in result_lower, \
            "Should mention route in recommendations"
        
        # Verify route number 2 is mentioned (the best route)
        assert "2" in result or "#2" in result, \
            "Should recommend route 2 (the lowest emission route)"
    
    def test_optional_invocation_does_not_break_existing_flow(self):
        """
        Test that optional invocation doesn't break existing flow.
        
        This test verifies that:
        1. The advisor can be called optionally (with user choice)
        2. If not called, the main flow continues normally
        3. If called, it doesn't interfere with subsequent operations
        4. The advisor doesn't modify any shared state
        
        **Validates: Requirements 4.5**
        """
        # Simulate the main flow variables
        distance_km = 20.0
        car_type = "EV"
        fuel_type = "listrik"
        emission_factor = get_emission_factor(car_type, fuel_type)
        emission_g = distance_km * emission_factor
        
        # Store original emission factor to verify it's not modified
        original_emission_factor = emission_factor
        
        # Simulate optional invocation (user says yes)
        trip_data = {
            'distance_km': distance_km,
            'car_type': car_type,
            'fuel_type': fuel_type,
            'emission_g': emission_g
        }
        
        # Call advisor
        result = get_emission_advice(trip_data)
        
        # Verify advisor returns valid output
        assert isinstance(result, str), "Advisor should return a string"
        assert len(result) > 0, "Advisor should return non-empty output"
        
        # Verify advisor doesn't modify EMISSION_FACTORS
        assert EMISSION_FACTORS[car_type][fuel_type] == original_emission_factor, \
            "Advisor should not modify EMISSION_FACTORS"
        
        # Verify advisor doesn't modify the emission calculation function
        recalculated_emission = distance_km * get_emission_factor(car_type, fuel_type)
        assert recalculated_emission == emission_g, \
            "Emission calculation should still work correctly after advisor call"
        
        # Verify trip_data is not modified (immutability)
        assert trip_data['distance_km'] == distance_km, \
            "Trip data should not be modified"
        assert trip_data['car_type'] == car_type, \
            "Trip data should not be modified"
        assert trip_data['fuel_type'] == fuel_type, \
            "Trip data should not be modified"
        assert trip_data['emission_g'] == emission_g, \
            "Trip data should not be modified"
    
    def test_advisor_integration_with_all_vehicle_types(self):
        """
        Test that advisor integrates correctly with all valid vehicle types.
        
        This test verifies that the advisor works correctly when called from
        main flow with any valid vehicle-fuel combination from EMISSION_FACTORS.
        
        **Validates: Requirements 4.5**
        """
        # Test all valid combinations
        for car_type, fuels in EMISSION_FACTORS.items():
            for fuel_type, emission_factor in fuels.items():
                # Simulate main flow data
                distance_km = 10.0
                emission_g = distance_km * emission_factor
                
                trip_data = {
                    'distance_km': distance_km,
                    'car_type': car_type,
                    'fuel_type': fuel_type,
                    'emission_g': emission_g
                }
                
                # Call advisor
                result = get_emission_advice(trip_data)
                
                # Verify result is valid for each combination
                assert isinstance(result, str), \
                    f"Advisor should return string for {car_type}-{fuel_type}"
                assert "Error" not in result or "REKOMENDASI" in result, \
                    f"Advisor should not error for valid combination {car_type}-{fuel_type}"
                assert "REKOMENDASI PENGURANGAN EMISI KARBON" in result, \
                    f"Result should contain header for {car_type}-{fuel_type}"
    
    def test_advisor_handles_edge_case_very_short_distance(self):
        """
        Test that advisor handles very short distances correctly.
        
        This test verifies that the advisor provides appropriate recommendations
        for very short trips (< 1 km) where walking is most appropriate.
        
        **Validates: Requirements 4.5, 6.1**
        """
        # Very short distance
        distance_km = 0.5
        car_type = "LCGC"
        fuel_type = "bensin"
        emission_factor = get_emission_factor(car_type, fuel_type)
        emission_g = distance_km * emission_factor
        
        trip_data = {
            'distance_km': distance_km,
            'car_type': car_type,
            'fuel_type': fuel_type,
            'emission_g': emission_g
        }
        
        # Call advisor
        result = get_emission_advice(trip_data)
        
        # Verify result is valid
        assert isinstance(result, str), "Advisor should return a string"
        assert "Error" not in result or "REKOMENDASI" in result, \
            "Advisor should not error on very short distance"
        
        # For very short distance, should recommend walking or cycling
        result_lower = result.lower()
        assert "jalan" in result_lower or "sepeda" in result_lower or \
               "walking" in result_lower or "cycling" in result_lower, \
            "For very short distance, should recommend walking or cycling"
    
    def test_advisor_handles_edge_case_very_long_distance(self):
        """
        Test that advisor handles very long distances correctly.
        
        This test verifies that the advisor provides appropriate recommendations
        for very long trips (> 100 km) where vehicle efficiency is most important.
        
        **Validates: Requirements 4.5, 6.3**
        """
        # Very long distance
        distance_km = 150.0
        car_type = "SUV"
        fuel_type = "bensin"
        emission_factor = get_emission_factor(car_type, fuel_type)
        emission_g = distance_km * emission_factor
        
        trip_data = {
            'distance_km': distance_km,
            'car_type': car_type,
            'fuel_type': fuel_type,
            'emission_g': emission_g
        }
        
        # Call advisor
        result = get_emission_advice(trip_data)
        
        # Verify result is valid
        assert isinstance(result, str), "Advisor should return a string"
        assert "Error" not in result or "REKOMENDASI" in result, \
            "Advisor should not error on very long distance"
        
        # For very long distance, should focus on vehicle efficiency
        result_lower = result.lower()
        assert "kendaraan" in result_lower or "vehicle" in result_lower or \
               "listrik" in result_lower or "electric" in result_lower or \
               "efisiensi" in result_lower or "efficiency" in result_lower, \
            "For very long distance, should focus on vehicle efficiency"
        
        # Should NOT primarily recommend walking or cycling for 150km
        # (they might be mentioned in passing, but shouldn't be main recommendation)
        assert "REKOMENDASI PENGURANGAN EMISI" in result, \
            "Should still provide recommendations"
    
    def test_advisor_integration_preserves_emission_factors(self):
        """
        Test that advisor integration preserves EMISSION_FACTORS consistency.
        
        This test verifies that the advisor uses the same EMISSION_FACTORS
        as the main emission calculation module, ensuring consistency.
        
        **Validates: Requirements 4.4, 4.5**
        """
        # Test with each vehicle type
        for car_type, fuels in EMISSION_FACTORS.items():
            for fuel_type, expected_factor in fuels.items():
                distance_km = 10.0
                
                # Calculate emission using main module
                main_emission = distance_km * get_emission_factor(car_type, fuel_type)
                
                # Create trip data
                trip_data = {
                    'distance_km': distance_km,
                    'car_type': car_type,
                    'fuel_type': fuel_type,
                    'emission_g': main_emission
                }
                
                # Call advisor
                result = get_emission_advice(trip_data)
                
                # Verify advisor doesn't recalculate emission
                # The emission value in the output should match the input
                assert str(int(main_emission)) in result or \
                       f"{main_emission:,.0f}" in result, \
                    f"Advisor should use the same emission value for {car_type}-{fuel_type}"
                
                # Verify EMISSION_FACTORS is unchanged
                assert EMISSION_FACTORS[car_type][fuel_type] == expected_factor, \
                    f"EMISSION_FACTORS should not be modified for {car_type}-{fuel_type}"


class TestAdvisorErrorHandlingIntegration:
    """
    Integration tests for advisor error handling in main flow context.
    
    **Validates: Requirements 4.5, 7.5**
    """
    
    def test_advisor_handles_invalid_data_gracefully_in_main_flow(self):
        """
        Test that advisor handles invalid data gracefully without crashing main flow.
        
        This test verifies that if invalid data is passed to the advisor
        (which shouldn't happen in normal flow, but could happen due to bugs),
        the advisor returns an error message instead of crashing.
        
        **Validates: Requirements 4.5, 7.5**
        """
        # Invalid trip data (missing required field)
        invalid_trip_data = {
            'distance_km': 10.0,
            'car_type': 'SUV'
            # Missing fuel_type and emission_g
        }
        
        # Call advisor - should not crash
        result = get_emission_advice(invalid_trip_data)
        
        # Verify it returns an error message, not crash
        assert isinstance(result, str), "Should return a string"
        assert "Error" in result or "error" in result, \
            "Should return error message for invalid data"
    
    def test_advisor_handles_invalid_combination_gracefully_in_main_flow(self):
        """
        Test that advisor handles invalid vehicle-fuel combination gracefully.
        
        This test verifies that if an invalid combination is passed
        (which shouldn't happen if main.py validates correctly, but could
        happen due to bugs), the advisor returns an error message.
        
        **Validates: Requirements 4.5, 7.4, 7.5**
        """
        # Invalid combination
        invalid_trip_data = {
            'distance_km': 10.0,
            'car_type': 'EV',
            'fuel_type': 'bensin',  # Invalid: EV doesn't use bensin
            'emission_g': 1200.0
        }
        
        # Call advisor - should not crash
        result = get_emission_advice(invalid_trip_data)
        
        # Verify it returns an error message
        assert isinstance(result, str), "Should return a string"
        assert "Error" in result or "error" in result, \
            "Should return error message for invalid combination"
        assert "Invalid" in result or "invalid" in result, \
            "Error message should indicate invalid combination"
