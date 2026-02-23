#!/usr/bin/env python3
"""
Script sederhana untuk menguji OpenStreetMap API
"""

import requests

def test_geocoding(address):
    """Test geocoding dengan Nominatim"""
    print(f"\nMencari koordinat untuk: {address}")
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': address,
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'CarbonEmissionCalculator/1.0'
    }
    
    response = requests.get(url, params=params, headers=headers, timeout=10)
    data = response.json()
    
    if data:
        lat = data[0]['lat']
        lon = data[0]['lon']
        print(f"  Koordinat: {lat}, {lon}")
        return (float(lat), float(lon))
    else:
        print("  Alamat tidak ditemukan!")
        return None

def test_routing(origin_coords, dest_coords):
    """Test routing dengan OSRM"""
    print(f"\nMenghitung rute...")
    url = f"http://router.project-osrm.org/route/v1/driving/{origin_coords[1]},{origin_coords[0]};{dest_coords[1]},{dest_coords[0]}"
    params = {
        'overview': 'false',
        'steps': 'false'
    }
    
    response = requests.get(url, params=params, timeout=15)
    data = response.json()
    
    if data.get('code') == 'Ok' and data.get('routes'):
        distance_m = data['routes'][0]['distance']
        distance_km = distance_m / 1000.0
        print(f"  Jarak: {distance_km:.2f} km")
        return distance_km
    else:
        print(f"  Error: {data.get('code')}")
        return None

def main():
    print("="*60)
    print("Test OpenStreetMap API untuk Carbon Emission Calculator")
    print("="*60)
    
    # Test 1: Jakarta to Bandung
    print("\n[Test 1] Jakarta ke Bandung")
    print("-"*60)
    origin = test_geocoding("Jakarta, Indonesia")
    dest = test_geocoding("Bandung, Indonesia")
    
    if origin and dest:
        distance = test_routing(origin, dest)
        if distance:
            # Hitung emisi dengan SUV bensin (180 g/km)
            emission = distance * 180
            print(f"\n  Emisi (SUV bensin): {emission:,.0f} g CO2 ({emission/1000:.2f} kg)")
    
    # Test 2: Surabaya to Malang
    print("\n\n[Test 2] Surabaya ke Malang")
    print("-"*60)
    origin = test_geocoding("Surabaya, Indonesia")
    dest = test_geocoding("Malang, Indonesia")
    
    if origin and dest:
        distance = test_routing(origin, dest)
        if distance:
            # Hitung emisi dengan LCGC bensin (120 g/km)
            emission = distance * 120
            print(f"\n  Emisi (LCGC bensin): {emission:,.0f} g CO2 ({emission/1000:.2f} kg)")
    
    print("\n" + "="*60)
    print("Test selesai!")
    print("="*60)

if __name__ == "__main__":
    main()
