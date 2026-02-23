"""
Example Usage Script for Emission Reduction Advisor

This script demonstrates various usage scenarios for the Emission Reduction
Advisor module, including:
1. Basic single-route trip analysis
2. Multi-route trip comparison
3. Different vehicle types (LCGC, SUV, EV)
4. Different distance categories (short, medium, long)
5. Error handling for invalid inputs

Run this script to see how the advisor works with different trip scenarios.
"""

from advisor import get_emission_advice


def print_section_header(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def example_1_short_trip_lcgc():
    """Example 1: Short trip with LCGC vehicle."""
    print_section_header("Example 1: Short Trip with LCGC (3.5 km)")
    
    trip_data = {
        "distance_km": 3.5,
        "car_type": "LCGC",
        "fuel_type": "bensin",
        "emission_g": 420.0
    }
    
    print("\nInput Trip Data:")
    print(f"  Distance: {trip_data['distance_km']} km")
    print(f"  Vehicle: {trip_data['car_type']}")
    print(f"  Fuel: {trip_data['fuel_type']}")
    print(f"  Emission: {trip_data['emission_g']} g CO2")
    
    advice = get_emission_advice(trip_data)
    print("\n" + advice)


def example_2_medium_trip_suv():
    """Example 2: Medium trip with SUV vehicle."""
    print_section_header("Example 2: Medium Trip with SUV (12.5 km)")
    
    trip_data = {
        "distance_km": 12.5,
        "car_type": "SUV",
        "fuel_type": "bensin",
        "emission_g": 2250.0
    }
    
    print("\nInput Trip Data:")
    print(f"  Distance: {trip_data['distance_km']} km")
    print(f"  Vehicle: {trip_data['car_type']}")
    print(f"  Fuel: {trip_data['fuel_type']}")
    print(f"  Emission: {trip_data['emission_g']} g CO2")
    
    advice = get_emission_advice(trip_data)
    print("\n" + advice)


def example_3_long_trip_ev():
    """Example 3: Long trip with electric vehicle."""
    print_section_header("Example 3: Long Trip with EV (45.0 km)")
    
    trip_data = {
        "distance_km": 45.0,
        "car_type": "EV",
        "fuel_type": "listrik",
        "emission_g": 450.0
    }
    
    print("\nInput Trip Data:")
    print(f"  Distance: {trip_data['distance_km']} km")
    print(f"  Vehicle: {trip_data['car_type']}")
    print(f"  Fuel: {trip_data['fuel_type']}")
    print(f"  Emission: {trip_data['emission_g']} g CO2")
    
    advice = get_emission_advice(trip_data)
    print("\n" + advice)


def example_4_multi_route_comparison():
    """Example 4: Multi-route trip with route comparison."""
    print_section_header("Example 4: Multi-Route Trip Comparison (15.3 km)")
    
    trip_data = {
        "distance_km": 15.3,
        "car_type": "LCGC",
        "fuel_type": "bensin",
        "emission_g": 1836.0,
        "routes": [
            {
                "route_number": 1,
                "distance_km": 15.3,
                "duration_min": 25.0,
                "emission_g": 1836.0
            },
            {
                "route_number": 2,
                "distance_km": 14.8,
                "duration_min": 28.0,
                "emission_g": 1776.0
            },
            {
                "route_number": 3,
                "distance_km": 16.1,
                "duration_min": 23.0,
                "emission_g": 1932.0
            }
        ]
    }
    
    print("\nInput Trip Data:")
    print(f"  Distance: {trip_data['distance_km']} km")
    print(f"  Vehicle: {trip_data['car_type']}")
    print(f"  Fuel: {trip_data['fuel_type']}")
    print(f"  Emission: {trip_data['emission_g']} g CO2")
    print(f"  Routes: {len(trip_data['routes'])} alternatives")
    print("\n  Route Details:")
    for route in trip_data['routes']:
        print(f"    Route {route['route_number']}: {route['distance_km']} km, "
              f"{route['duration_min']} min, {route['emission_g']} g CO2")
    
    advice = get_emission_advice(trip_data)
    print("\n" + advice)


def example_5_diesel_suv():
    """Example 5: Long trip with diesel SUV."""
    print_section_header("Example 5: Long Trip with Diesel SUV (28.0 km)")
    
    trip_data = {
        "distance_km": 28.0,
        "car_type": "SUV",
        "fuel_type": "solar",
        "emission_g": 4480.0
    }
    
    print("\nInput Trip Data:")
    print(f"  Distance: {trip_data['distance_km']} km")
    print(f"  Vehicle: {trip_data['car_type']}")
    print(f"  Fuel: {trip_data['fuel_type']}")
    print(f"  Emission: {trip_data['emission_g']} g CO2")
    
    advice = get_emission_advice(trip_data)
    print("\n" + advice)


def example_6_error_handling_invalid_combination():
    """Example 6: Error handling - invalid vehicle-fuel combination."""
    print_section_header("Example 6: Error Handling - Invalid Combination")
    
    trip_data = {
        "distance_km": 10.0,
        "car_type": "EV",
        "fuel_type": "bensin",  # Invalid: EV cannot use bensin
        "emission_g": 1200.0
    }
    
    print("\nInput Trip Data (INVALID):")
    print(f"  Distance: {trip_data['distance_km']} km")
    print(f"  Vehicle: {trip_data['car_type']}")
    print(f"  Fuel: {trip_data['fuel_type']} (INVALID COMBINATION)")
    print(f"  Emission: {trip_data['emission_g']} g CO2")
    
    advice = get_emission_advice(trip_data)
    print("\n" + advice)


def example_7_error_handling_missing_field():
    """Example 7: Error handling - missing required field."""
    print_section_header("Example 7: Error Handling - Missing Field")
    
    trip_data = {
        "distance_km": 10.0,
        "car_type": "LCGC",
        # Missing fuel_type field
        "emission_g": 1200.0
    }
    
    print("\nInput Trip Data (MISSING FIELD):")
    print(f"  Distance: {trip_data['distance_km']} km")
    print(f"  Vehicle: {trip_data['car_type']}")
    print(f"  Fuel: (MISSING)")
    print(f"  Emission: {trip_data['emission_g']} g CO2")
    
    advice = get_emission_advice(trip_data)
    print("\n" + advice)


def example_8_error_handling_negative_value():
    """Example 8: Error handling - negative distance."""
    print_section_header("Example 8: Error Handling - Negative Value")
    
    trip_data = {
        "distance_km": -5.0,  # Invalid: negative distance
        "car_type": "LCGC",
        "fuel_type": "bensin",
        "emission_g": 600.0
    }
    
    print("\nInput Trip Data (NEGATIVE DISTANCE):")
    print(f"  Distance: {trip_data['distance_km']} km (INVALID)")
    print(f"  Vehicle: {trip_data['car_type']}")
    print(f"  Fuel: {trip_data['fuel_type']}")
    print(f"  Emission: {trip_data['emission_g']} g CO2")
    
    advice = get_emission_advice(trip_data)
    print("\n" + advice)


def main():
    """Run all example scenarios."""
    print("\n" + "=" * 70)
    print("  EMISSION REDUCTION ADVISOR - EXAMPLE USAGE SCENARIOS")
    print("=" * 70)
    print("\nThis script demonstrates various usage scenarios for the advisor.")
    print("Each example shows different trip characteristics and recommendations.")
    
    # Valid scenarios
    example_1_short_trip_lcgc()
    example_2_medium_trip_suv()
    example_3_long_trip_ev()
    example_4_multi_route_comparison()
    example_5_diesel_suv()
    
    # Error handling scenarios
    example_6_error_handling_invalid_combination()
    example_7_error_handling_missing_field()
    example_8_error_handling_negative_value()
    
    print("\n" + "=" * 70)
    print("  END OF EXAMPLES")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  1. Short trips (<5km): Advisor recommends walking/cycling")
    print("  2. Medium trips (5-15km): Advisor recommends public transport")
    print("  3. Long trips (>15km): Advisor recommends EV or efficiency")
    print("  4. Multi-route: Advisor identifies best route by emission")
    print("  5. EV users: Advisor focuses on efficiency, not vehicle switch")
    print("  6. Invalid inputs: Advisor provides clear error messages")
    print("\n")


if __name__ == "__main__":
    main()
