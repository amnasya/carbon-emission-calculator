"""
Test script to verify the integration of emission advisor with main.py
"""

from advisor import get_emission_advice
from emission import get_emission_factor

def test_integration():
    """Test that the advisor can be called with trip data constructed from main.py variables."""
    
    # Simulate variables that would exist in main.py
    car_type = "SUV"
    fuel_type = "bensin"
    
    # Simulate routes data structure from get_alternative_routes
    routes = [
        {
            'route_number': 1,
            'distance_km': 12.5,
            'duration_min': 25.0,
            'steps': []
        },
        {
            'route_number': 2,
            'distance_km': 14.2,
            'duration_min': 28.0,
            'steps': []
        },
        {
            'route_number': 3,
            'distance_km': 11.8,
            'duration_min': 24.0,
            'steps': []
        }
    ]
    
    # Construct trip data dictionary (same as in main.py)
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
    
    # Call the advisor
    print("Testing integration with multi-route scenario...")
    advice_output = get_emission_advice(trip_data)
    
    # Verify output is a string and contains expected sections
    assert isinstance(advice_output, str), "Output should be a string"
    assert "REKOMENDASI PENGURANGAN EMISI KARBON" in advice_output, "Output should contain header"
    assert "RINGKASAN PERJALANAN" in advice_output, "Output should contain summary section"
    assert "REKOMENDASI PENGURANGAN EMISI" in advice_output, "Output should contain recommendations section"
    assert "Penghematan" in advice_output, "Output should contain savings information"
    
    print("✓ Integration test passed!")
    print("\nSample output:")
    print(advice_output)
    
    # Test with single route scenario
    print("\n" + "="*70)
    print("Testing integration with single-route scenario...")
    
    single_route_data = {
        'distance_km': 8.5,
        'car_type': 'LCGC',
        'fuel_type': 'bensin',
        'emission_g': 8.5 * get_emission_factor('LCGC', 'bensin')
    }
    
    advice_output_single = get_emission_advice(single_route_data)
    assert isinstance(advice_output_single, str), "Output should be a string"
    assert "REKOMENDASI PENGURANGAN EMISI KARBON" in advice_output_single, "Output should contain header"
    
    print("✓ Single-route integration test passed!")
    print("\nSample output:")
    print(advice_output_single)
    
    # Test with EV
    print("\n" + "="*70)
    print("Testing integration with EV scenario...")
    
    ev_data = {
        'distance_km': 20.0,
        'car_type': 'EV',
        'fuel_type': 'listrik',
        'emission_g': 20.0 * get_emission_factor('EV', 'listrik')
    }
    
    advice_output_ev = get_emission_advice(ev_data)
    assert isinstance(advice_output_ev, str), "Output should be a string"
    assert "REKOMENDASI PENGURANGAN EMISI KARBON" in advice_output_ev, "Output should contain header"
    # EV should not get recommendation to switch to EV
    assert "Beralih ke Kendaraan Listrik" not in advice_output_ev, "EV should not get EV switch recommendation"
    
    print("✓ EV integration test passed!")
    print("\nSample output:")
    print(advice_output_ev)
    
    print("\n" + "="*70)
    print("All integration tests passed! ✓")
    print("The advisor can be successfully integrated with main.py")

if __name__ == "__main__":
    test_integration()
