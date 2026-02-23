import sys
import requests

print("Testing alternative routes API...")

# Geocode
print("\n1. Geocoding Jakarta...")
url = "https://nominatim.openstreetmap.org/search"
params = {'q': 'Jakarta, Indonesia', 'format': 'json', 'limit': 1}
headers = {'User-Agent': 'Test/1.0'}
r = requests.get(url, params=params, headers=headers, timeout=10)
data = r.json()
origin = (float(data[0]['lat']), float(data[0]['lon']))
print(f"   OK: {origin}")

print("\n2. Geocoding Bandung...")
params2 = {'q': 'Bandung, Indonesia', 'format': 'json', 'limit': 1}
r2 = requests.get(url, params=params2, headers=headers, timeout=10)
data2 = r2.json()
dest = (float(data2[0]['lat']), float(data2[0]['lon']))
print(f"   OK: {dest}")

print("\n3. Getting alternative routes...")
route_url = f"http://router.project-osrm.org/route/v1/driving/{origin[1]},{origin[0]};{dest[1]},{dest[0]}"
route_params = {
    'alternatives': 'true',
    'steps': 'true',
    'overview': 'full'
}

print(f"   URL: {route_url}")
print("   Requesting...")

r3 = requests.get(route_url, params=route_params, timeout=20)
data3 = r3.json()

if data3.get('code') == 'Ok':
    routes = data3.get('routes', [])
    print(f"\n   SUCCESS! Found {len(routes)} routes:")
    
    for idx, route in enumerate(routes, 1):
        distance_km = route['distance'] / 1000.0
        duration_min = route['duration'] / 60.0
        print(f"\n   Route {idx}:")
        print(f"     Distance: {distance_km:.2f} km")
        print(f"     Duration: {duration_min:.1f} min")
        
        # Show first 3 steps
        legs = route.get('legs', [])
        if legs and legs[0].get('steps'):
            steps = legs[0]['steps']
            print(f"     Steps: {len(steps)} total")
            for i, step in enumerate(steps[:3], 1):
                name = step.get('name', 'unnamed')
                dist = step.get('distance', 0) / 1000.0
                print(f"       {i}. {name} ({dist:.2f} km)")
else:
    print(f"   ERROR: {data3.get('code')}")

print("\nTest complete!")
