#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test fitur visualisasi grafik
"""

import sys

# Test import matplotlib
try:
    import matplotlib
    print(f"✓ Matplotlib version: {matplotlib.__version__}")
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    print("✓ Matplotlib imported successfully")
except ImportError as e:
    print(f"✗ Error: Matplotlib not installed - {e}")
    print("\nInstall dengan: pip install matplotlib")
    sys.exit(1)

from visualization import create_emission_chart, create_comparison_bar_chart
from emission import get_emission_factor

def test_charts():
    print("\n" + "="*70)
    print("TEST: Visualisasi Grafik Emisi")
    print("="*70)
    
    # Sample route data (Jakarta to Bandung)
    routes = [
        {
            'route_number': 1,
            'distance_km': 168.50,
            'duration_min': 126.6,
            'steps': []
        },
        {
            'route_number': 2,
            'distance_km': 170.24,
            'duration_min': 131.0,
            'steps': []
        }
    ]
    
    car_type = "SUV"
    fuel_type = "bensin"
    emission_factor = get_emission_factor(car_type, fuel_type)
    
    print(f"\nData Test:")
    print(f"  Vehicle: {car_type} - {fuel_type}")
    print(f"  Emission Factor: {emission_factor} g CO2/km")
    print(f"  Routes: {len(routes)}")
    
    print("\n1. Membuat grafik emisi per 25 km...")
    try:
        chart1 = create_emission_chart(routes, car_type, fuel_type, emission_factor, 
                                       'test_emission_chart.png')
        print(f"   ✓ Berhasil: {chart1}")
    except Exception as e:
        print(f"   ✗ Gagal: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n2. Membuat grafik perbandingan bar...")
    try:
        chart2 = create_comparison_bar_chart(routes, emission_factor, 
                                            'test_comparison_chart.png')
        print(f"   ✓ Berhasil: {chart2}")
    except Exception as e:
        print(f"   ✗ Gagal: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "="*70)
    print("TEST SELESAI!")
    print("="*70)
    print("\nGrafik telah dibuat:")
    print("  - test_emission_chart.png")
    print("  - test_comparison_chart.png")
    print("\nSilakan buka file PNG untuk melihat hasilnya.")

if __name__ == "__main__":
    test_charts()
