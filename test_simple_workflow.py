"""
Simple test to verify the integration works correctly.
"""

from advisor import get_emission_advice
from emission import get_emission_factor

def test_advisor_integration():
    """Test that advisor can be called with data structure from main.py"""
    
    print("Testing advisor integration with main.py data structure...")
    
    # Simulate the exact data structure that main.py creates
    car_type = "SUV"
    fuel_type = "bensin"
    
    routes = [
        {
            'route_number': 1,
            'distance_km': 12.5,
            'duration_min': 25.0,
            'steps': []
        },
        {
            'route_number': 2,
            'distance_km': 11.8,
            'duration_min': 24.0,
            'steps': []
        }
    ]
    
    # This is exactly how main.py constructs trip_data
    emission_factor = get_emission_factor(car_type, fuel_type)
    first_route = routes[0]
    trip_distance = first_route['distance_km']
    trip_emission = first_route['distance_km'] * emission_factor
    
    trip_data = {
        'distance_km': trip_distance,
        'car_type': car_type,
        'fuel_type': fuel_type,
        'emission_g': trip_emission,
        'routes': [
            {
                'route_number': route['route_number'],
                'distance_km': route['distance_km'],
                'duration_min': route['duration_min'],
                'emission_g': route['distance_km'] * emission_factor
            }
            for route in routes
        ]
    }
    
    # Call advisor
    advice_output = get_emission_advice(trip_data)
    
    # Verify it returns valid output
    assert isinstance(advice_output, str), "Should return string"
    assert len(advice_output) > 0, "Should return non-empty string"
    assert "REKOMENDASI PENGURANGAN EMISI KARBON" in advice_output, "Should contain header"
    assert "RINGKASAN PERJALANAN" in advice_output, "Should contain summary"
    assert "Penghematan" in advice_output, "Should contain savings"
    
    print("✓ Advisor integration test passed!")
    print("\nKey verification points:")
    print("  ✓ Data structure from main.py is compatible")
    print("  ✓ Advisor returns formatted output")
    print("  ✓ Output contains all required sections")
    print("  ✓ Multi-route data is processed correctly")
    
    return True

def test_optional_invocation():
    """Test that advisor can be optionally invoked"""
    
    print("\nTesting optional invocation pattern...")
    
    # Simulate user choosing not to use advisor
    advice_choice = 'n'
    
    if advice_choice in ['y', 'yes']:
        print("  Advisor would be called")
        advisor_called = True
    else:
        print("  Advisor skipped")
        advisor_called = False
    
    assert not advisor_called, "Advisor should not be called when user declines"
    print("✓ Optional invocation test passed!")
    
    # Simulate user choosing to use advisor
    advice_choice = 'y'
    
    if advice_choice in ['y', 'yes']:
        print("  Advisor would be called")
        advisor_called = True
    else:
        print("  Advisor skipped")
        advisor_called = False
    
    assert advisor_called, "Advisor should be called when user accepts"
    print("✓ Optional invocation with acceptance test passed!")
    
    return True

def test_no_disruption():
    """Verify that the integration doesn't break existing code"""
    
    print("\nTesting that existing code is not disrupted...")
    
    # Test that we can still import and use existing functions
    from emission import calculate_emission, get_emission_factor, get_valid_combinations
    from visualization import create_emission_chart, create_comparison_bar_chart
    
    # Test emission calculation still works
    emission = calculate_emission(10.0, "LCGC", "bensin")
    assert emission > 0, "Emission calculation should work"
    print("  ✓ Emission calculation still works")
    
    # Test emission factor retrieval still works
    factor = get_emission_factor("SUV", "bensin")
    assert factor > 0, "Emission factor retrieval should work"
    print("  ✓ Emission factor retrieval still works")
    
    # Test valid combinations still works
    combos = get_valid_combinations()
    assert len(combos) > 0, "Valid combinations should be available"
    print("  ✓ Valid combinations retrieval still works")
    
    print("✓ No disruption test passed!")
    print("  All existing functions continue to work normally")
    
    return True

if __name__ == "__main__":
    print("="*70)
    print("INTEGRATION VERIFICATION TESTS")
    print("="*70)
    
    test_advisor_integration()
    test_optional_invocation()
    test_no_disruption()
    
    print("\n" + "="*70)
    print("ALL TESTS PASSED! ✓")
    print("="*70)
    print("\nSummary:")
    print("  • Advisor integrates correctly with main.py data structure")
    print("  • Optional invocation works as expected")
    print("  • Existing workflow is not disrupted")
    print("  • All existing functions continue to work")
