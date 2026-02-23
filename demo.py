"""
Demo script untuk menguji Carbon Emission Calculator dengan OpenStreetMap
"""

import sys
import os

# Pastikan kita bisa import modul lokal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from maps_api import get_distance
from emission import calculate_emission, EMISSION_FACTORS

def demo():
    print("=== Demo Carbon Emission Calculator ===\n")
    
    # Test case 1: Jakarta to Bandung
    print("Test 1: Jakarta ke Bandung dengan SUV bensin")
    try:
        origin = "Jakarta, Indonesia"
        destination = "Bandung, Indonesia"
        car_type = "SUV"
        fuel_type = "bensin"
        
        print(f"Origin: {origin}")
        print(f"Destination: {destination}")
        print(f"Vehicle: {car_type} - {fuel_type}")
        print("Menghitung jarak...")
        
        distance = get_distance(origin, destination)
        emission = calculate_emission(distance, car_type, fuel_type)
        
        print(f"\nHasil:")
        print(f"Jarak: {distance:.2f} km")
        print(f"Emisi Karbon: {emission:,.0f} g CO2 ({emission/1000:.2f} kg CO2)")
        print(f"Faktor Emisi: {EMISSION_FACTORS[car_type][fuel_type]} g/km")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test case 2: Surabaya to Malang
    print("Test 2: Surabaya ke Malang dengan LCGC bensin")
    try:
        origin = "Surabaya, Indonesia"
        destination = "Malang, Indonesia"
        car_type = "LCGC"
        fuel_type = "bensin"
        
        print(f"Origin: {origin}")
        print(f"Destination: {destination}")
        print(f"Vehicle: {car_type} - {fuel_type}")
        print("Menghitung jarak...")
        
        distance = get_distance(origin, destination)
        emission = calculate_emission(distance, car_type, fuel_type)
        
        print(f"\nHasil:")
        print(f"Jarak: {distance:.2f} km")
        print(f"Emisi Karbon: {emission:,.0f} g CO2 ({emission/1000:.2f} kg CO2)")
        print(f"Faktor Emisi: {EMISSION_FACTORS[car_type][fuel_type]} g/km")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test case 3: Short distance with EV
    print("Test 3: Yogyakarta ke Solo dengan EV listrik")
    try:
        origin = "Yogyakarta, Indonesia"
        destination = "Solo, Indonesia"
        car_type = "EV"
        fuel_type = "listrik"
        
        print(f"Origin: {origin}")
        print(f"Destination: {destination}")
        print(f"Vehicle: {car_type} - {fuel_type}")
        print("Menghitung jarak...")
        
        distance = get_distance(origin, destination)
        emission = calculate_emission(distance, car_type, fuel_type)
        
        print(f"\nHasil:")
        print(f"Jarak: {distance:.2f} km")
        print(f"Emisi Karbon: {emission:,.0f} g CO2 ({emission/1000:.2f} kg CO2)")
        print(f"Faktor Emisi: {EMISSION_FACTORS[car_type][fuel_type]} g/km")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    demo()
