#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test fitur perbandingan rute alternatif
"""

import sys
import os

# Ensure UTF-8 encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from maps_api import get_alternative_routes
from emission import calculate_emission, get_emission_factor

def main():
    print("="*70)
    print("TEST: Fitur Perbandingan Rute Alternatif")
    print("="*70)
    
    # Test case
    origin = "Jakarta, Indonesia"
    destination = "Bandung, Indonesia"
    car_type = "SUV"
    fuel_type = "bensin"
    
    print(f"\nOrigin      : {origin}")
    print(f"Destination : {destination}")
    print(f"Vehicle     : {car_type}")
    print(f"Fuel        : {fuel_type}")
    print("\nMencari rute alternatif...")
    
    try:
        # Get routes
        routes = get_alternative_routes(origin, destination)
        emission_factor = get_emission_factor(car_type, fuel_type)
        
        print(f"Ditemukan {len(routes)} rute alternatif\n")
        
        # Calculate emissions
        route_emissions = []
        for route in routes:
            emission_g = route['distance_km'] * emission_factor
            route_emissions.append({
                'route': route,
                'emission_g': emission_g,
                'emission_kg': emission_g / 1000.0
            })
        
        # Sort by emission (lowest first)
        route_emissions.sort(key=lambda x: x['emission_g'])
        
        # Display comparison
        print("="*70)
        print("PERBANDINGAN RUTE")
        print("="*70)
        
        for idx, route_data in enumerate(route_emissions):
            route = route_data['route']
            is_best = idx == 0
            
            print()
            if is_best:
                print(f">>> RUTE {route['route_number']} (REKOMENDASI) <<<")
            else:
                print(f"RUTE {route['route_number']}")
            print("-" * 70)
            
            print(f"Jarak        : {route['distance_km']:.2f} km")
            print(f"Waktu        : {route['duration_min']:.1f} menit")
            print(f"Emisi        : {route_data['emission_g']:,.0f} g CO2 ({route_data['emission_kg']:.2f} kg)")
            
            if is_best and len(route_emissions) > 1:
                worst = route_emissions[-1]
                savings = worst['emission_g'] - route_data['emission_g']
                savings_pct = (savings / worst['emission_g']) * 100
                print(f"Penghematan  : {savings:,.0f} g CO2 ({savings_pct:.1f}% lebih rendah)")
            
            # Show directions
            if route['steps']:
                print(f"\nPetunjuk Arah (5 langkah pertama):")
                for i, step in enumerate(route['steps'][:5], 1):
                    road = step['road'] if step['road'] else 'Jalan tanpa nama'
                    print(f"  {i}. {step['instruction']} - {road} ({step['distance_km']:.2f} km)")
                
                if len(route['steps']) > 5:
                    print(f"  ... dan {len(route['steps']) - 5} langkah lainnya")
        
        print("\n" + "="*70)
        best_route = route_emissions[0]['route']['route_number']
        print(f"REKOMENDASI: Gunakan Rute {best_route} untuk emisi terendah!")
        print("="*70)
        
        # Summary
        print("\nRingkasan:")
        print(f"- Rute terbaik menghemat {route_emissions[-1]['emission_g'] - route_emissions[0]['emission_g']:,.0f} g CO2")
        print(f"- Selisih jarak: {route_emissions[-1]['route']['distance_km'] - route_emissions[0]['route']['distance_km']:.2f} km")
        print(f"- Selisih waktu: {route_emissions[-1]['route']['duration_min'] - route_emissions[0]['route']['duration_min']:.1f} menit")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
