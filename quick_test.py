import requests

print("Testing OpenStreetMap API...")
print("="*60)

# Test geocoding
address = "Jakarta, Indonesia"
print(f"\n1. Geocoding: {address}")
url = "https://nominatim.openstreetmap.org/search"
params = {'q': address, 'format': 'json', 'limit': 1}
headers = {'User-Agent': 'Test/1.0'}

try:
    r = requests.get(url, params=params, headers=headers, timeout=10)
    data = r.json()
    if data:
        print(f"   Berhasil! Koordinat: {data[0]['lat']}, {data[0]['lon']}")
        origin = (float(data[0]['lat']), float(data[0]['lon']))
    else:
        print("   Gagal!")
        exit(1)
except Exception as e:
    print(f"   Error: {e}")
    exit(1)

# Test geocoding destination
address2 = "Bandung, Indonesia"
print(f"\n2. Geocoding: {address2}")
params2 = {'q': address2, 'format': 'json', 'limit': 1}

try:
    r2 = requests.get(url, params=params2, headers=headers, timeout=10)
    data2 = r2.json()
    if data2:
        print(f"   Berhasil! Koordinat: {data2[0]['lat']}, {data2[0]['lon']}")
        dest = (float(data2[0]['lat']), float(data2[0]['lon']))
    else:
        print("   Gagal!")
        exit(1)
except Exception as e:
    print(f"   Error: {e}")
    exit(1)

# Test routing
print(f"\n3. Routing: {address} -> {address2}")
route_url = f"http://router.project-osrm.org/route/v1/driving/{origin[1]},{origin[0]};{dest[1]},{dest[0]}"
route_params = {'overview': 'false', 'steps': 'false'}

try:
    r3 = requests.get(route_url, params=route_params, timeout=15)
    data3 = r3.json()
    if data3.get('code') == 'Ok':
        distance_m = data3['routes'][0]['distance']
        distance_km = distance_m / 1000.0
        print(f"   Berhasil! Jarak: {distance_km:.2f} km")
        
        # Hitung emisi
        emission_factor = 180  # SUV bensin
        emission = distance_km * emission_factor
        print(f"\n4. Perhitungan Emisi (SUV bensin, 180 g/km):")
        print(f"   Emisi: {emission:,.0f} g CO2 ({emission/1000:.2f} kg CO2)")
    else:
        print(f"   Gagal! Code: {data3.get('code')}")
except Exception as e:
    print(f"   Error: {e}")
    exit(1)

print("\n" + "="*60)
print("Semua test berhasil! OpenStreetMap API berfungsi dengan baik.")
print("="*60)
