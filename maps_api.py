# OpenStreetMap API Client
# This module manages communication with OpenStreetMap services (Nominatim + OSRM)

import requests

def _geocode_address(address: str) -> tuple:
    """
    Convert address to coordinates using Nominatim geocoding service.
    
    Args:
        address: Location address to geocode
        
    Returns:
        Tuple of (latitude, longitude)
        
    Raises:
        Exception: If address cannot be geocoded
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': address,
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'CarbonEmissionCalculator/1.0'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data or len(data) == 0:
            raise Exception(
                f"Error: Alamat '{address}' tidak ditemukan. "
                f"Silakan periksa alamat Anda dan coba lagi."
            )
        
        lat = float(data[0]['lat'])
        lon = float(data[0]['lon'])
        
        return (lat, lon)
        
    except requests.exceptions.Timeout:
        raise Exception(
            "Error: Permintaan ke layanan geocoding timeout. "
            "Silakan periksa koneksi internet Anda dan coba lagi."
        )
    except requests.exceptions.ConnectionError:
        raise Exception(
            "Error: Tidak dapat terhubung ke layanan geocoding. "
            "Silakan periksa koneksi internet Anda."
        )
    except (KeyError, ValueError, IndexError) as e:
        raise Exception(
            f"Error: Format respons tidak valid dari layanan geocoding: {str(e)}"
        )

def get_distance(origin: str, destination: str) -> float:
    """
    Get distance between two addresses using OpenStreetMap services.
    Uses Nominatim for geocoding and OSRM for routing.
    
    Args:
        origin: Starting location address
        destination: Ending location address
        
    Returns:
        Distance in kilometers as float
        
    Raises:
        Exception: With descriptive message on API errors
    """
    try:
        # Geocode both addresses
        origin_coords = _geocode_address(origin)
        destination_coords = _geocode_address(destination)
        
        # Use OSRM to calculate route distance
        url = f"http://router.project-osrm.org/route/v1/driving/{origin_coords[1]},{origin_coords[0]};{destination_coords[1]},{destination_coords[0]}"
        params = {
            'overview': 'false',
            'steps': 'false'
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Check OSRM response status
        if data.get('code') != 'Ok':
            raise Exception(
                f"Error: Tidak dapat menghitung rute. Status: {data.get('code')}. "
                f"Silakan periksa bahwa kedua alamat valid dan dapat diakses."
            )
        
        # Extract distance from response
        routes = data.get('routes', [])
        if not routes:
            raise Exception(
                "Error: Tidak ada rute ditemukan antara alamat-alamat tersebut. "
                "Silakan periksa bahwa kedua alamat valid dan dapat diakses."
            )
        
        # Distance is in meters
        distance_meters = routes[0].get('distance')
        if distance_meters is None:
            raise Exception(
                "Error: Format respons tidak valid dari layanan routing. "
                "Data jarak tidak ditemukan."
            )
        
        # Convert meters to kilometers
        distance_km = distance_meters / 1000.0
        
        return distance_km
        
    except requests.exceptions.Timeout:
        raise Exception(
            "Error: Permintaan ke layanan routing timeout. "
            "Silakan periksa koneksi internet Anda dan coba lagi."
        )
    except requests.exceptions.ConnectionError:
        raise Exception(
            "Error: Tidak dapat terhubung ke layanan routing. "
            "Silakan periksa koneksi internet Anda."
        )
    except requests.exceptions.RequestException as e:
        raise Exception(
            f"Error: Terjadi kesalahan jaringan saat menghubungi layanan routing: {str(e)}"
        )


def get_alternative_routes(origin: str, destination: str) -> list:
    """
    Get multiple alternative routes with detailed steps.
    
    Args:
        origin: Starting location address or "lat,lng" coordinates
        destination: Ending location address or "lat,lng" coordinates
        
    Returns:
        List of route dictionaries containing:
        - distance_km: Distance in kilometers
        - duration_min: Duration in minutes
        - steps: List of turn-by-turn directions
        
    Raises:
        Exception: With descriptive message on API errors
    """
    try:
        # Check if origin/destination are coordinates or addresses
        if ',' in origin and origin.replace(',', '').replace('.', '').replace('-', '').replace(' ', '').isdigit():
            # Already coordinates
            origin_parts = origin.split(',')
            origin_coords = (float(origin_parts[0]), float(origin_parts[1]))
        else:
            # Geocode address
            origin_coords = _geocode_address(origin)
        
        if ',' in destination and destination.replace(',', '').replace('.', '').replace('-', '').replace(' ', '').isdigit():
            # Already coordinates
            dest_parts = destination.split(',')
            destination_coords = (float(dest_parts[0]), float(dest_parts[1]))
        else:
            # Geocode address
            destination_coords = _geocode_address(destination)
        
        # Use OSRM to get alternative routes with steps
        url = f"http://router.project-osrm.org/route/v1/driving/{origin_coords[1]},{origin_coords[0]};{destination_coords[1]},{destination_coords[0]}"
        params = {
            'alternatives': 'true',  # Request alternative routes
            'steps': 'true',         # Include turn-by-turn directions
            'overview': 'full',      # Include route geometry
            'geometries': 'geojson'
        }
        
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        
        data = response.json()
        
        # Check OSRM response status
        if data.get('code') != 'Ok':
            raise Exception(
                f"Error: Tidak dapat menghitung rute. Status: {data.get('code')}. "
                f"Silakan periksa bahwa kedua alamat valid dan dapat diakses."
            )
        
        # Extract routes from response
        routes = data.get('routes', [])
        if not routes:
            raise Exception(
                "Error: Tidak ada rute ditemukan antara alamat-alamat tersebut. "
                "Silakan periksa bahwa kedua alamat valid dan dapat diakses."
            )
        
        # Process each route
        processed_routes = []
        for idx, route in enumerate(routes[:3]):  # Limit to 3 routes
            distance_km = route.get('distance', 0) / 1000.0
            duration_min = route.get('duration', 0) / 60.0
            
            # Extract steps (turn-by-turn directions)
            steps = []
            legs = route.get('legs', [])
            if legs:
                for step in legs[0].get('steps', []):
                    step_distance = step.get('distance', 0) / 1000.0
                    step_name = step.get('name', 'Jalan tanpa nama')
                    maneuver = step.get('maneuver', {})
                    instruction = maneuver.get('type', 'continue')
                    
                    # Translate maneuver types to Indonesian
                    instruction_id = _translate_maneuver(instruction)
                    
                    if step_distance > 0.1:  # Only include steps > 100m
                        steps.append({
                            'instruction': instruction_id,
                            'road': step_name,
                            'distance_km': round(step_distance, 2)
                        })
            
            # Extract geometry for map display
            geometry = route.get('geometry', {})
            coordinates = geometry.get('coordinates', []) if geometry else []
            
            processed_routes.append({
                'route_number': idx + 1,
                'distance_km': round(distance_km, 2),
                'duration_min': round(duration_min, 1),
                'steps': steps,
                'geometry': coordinates  # Add geometry for map display
            })
        
        return processed_routes
        
    except requests.exceptions.Timeout:
        raise Exception(
            "Error: Permintaan ke layanan routing timeout. "
            "Silakan periksa koneksi internet Anda dan coba lagi."
        )
    except requests.exceptions.ConnectionError:
        raise Exception(
            "Error: Tidak dapat terhubung ke layanan routing. "
            "Silakan periksa koneksi internet Anda."
        )
    except requests.exceptions.RequestException as e:
        raise Exception(
            f"Error: Terjadi kesalahan jaringan saat menghubungi layanan routing: {str(e)}"
        )


def _translate_maneuver(maneuver_type: str) -> str:
    """Translate OSRM maneuver types to Indonesian instructions."""
    translations = {
        'depart': 'Mulai perjalanan',
        'arrive': 'Tiba di tujuan',
        'turn': 'Belok',
        'new name': 'Lanjutkan ke',
        'continue': 'Lurus terus',
        'merge': 'Bergabung',
        'on ramp': 'Masuk jalan tol',
        'off ramp': 'Keluar jalan tol',
        'fork': 'Ambil percabangan',
        'end of road': 'Di ujung jalan',
        'roundabout': 'Di bundaran',
        'rotary': 'Di bundaran'
    }
    return translations.get(maneuver_type, 'Lanjutkan')
