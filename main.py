# Carbon Emission Calculator - Main Interface
# This module handles user interaction and orchestrates the calculation flow

from maps_api import get_distance, get_alternative_routes
from emission import calculate_emission, get_emission_factor, get_valid_combinations
from visualization import create_emission_chart, create_comparison_bar_chart, display_chart_info
from advisor import get_emission_advice
from mlr_emission_predictor import MLREmissionPredictor, FeatureExtractor
from route_comparator import RouteEmissionComparator
from emission_formatter import EmissionFormatter
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize ML predictor (with error handling)
try:
    mlr_predictor = MLREmissionPredictor()
    feature_extractor = FeatureExtractor()
    route_comparator = RouteEmissionComparator(mlr_predictor)
    ml_available = True
    logger.info("MLR Emission Predictor loaded successfully")
except Exception as e:
    mlr_predictor = None
    feature_extractor = None
    route_comparator = None
    ml_available = False
    logger.warning(f"MLR Emission Predictor not available: {e}. Will use static calculations.")


def get_user_input():
    """
    Collect origin, destination, vehicle type, and fuel type from user.
    
    Returns:
        tuple: (origin, destination, car_type, fuel_type)
    """
    print("\nCarbon Emission Calculator")
    print("=" * 50)
    print()
    
    # Get origin address
    while True:
        origin = input("Enter origin address: ").strip()
        if origin:
            break
        print("Error: Origin address cannot be empty. Please try again.")
    
    # Get destination address
    while True:
        destination = input("Enter destination address: ").strip()
        if destination:
            break
        print("Error: Destination address cannot be empty. Please try again.")
    
    # Get vehicle type
    while True:
        car_type = input("Enter vehicle type (LCGC/SUV/EV): ").strip()
        if car_type:
            break
        print("Error: Vehicle type cannot be empty. Please try again.")
    
    # Get fuel type
    while True:
        fuel_type = input("Enter fuel type (bensin/solar/listrik): ").strip()
        if fuel_type:
            break
        print("Error: Fuel type cannot be empty. Please try again.")
    
    return origin, destination, car_type, fuel_type


def display_results(distance, emission, car_type, fuel_type):
    """
    Format and display calculation results.
    
    Args:
        distance: Distance in kilometers
        emission: Emission in grams of CO2
        car_type: Vehicle type
        fuel_type: Fuel type
    """
    # Get emission factor for summary
    emission_factor = get_emission_factor(car_type, fuel_type)
    
    # Convert emission to kg
    emission_kg = emission / 1000.0
    
    print("\nResults:")
    print("-" * 50)
    print(f"Distance: {distance:.2f} km")
    print(f"Carbon Emission: {emission:,.0f} g CO2 ({emission_kg:.2f} kg CO2)")
    print()
    print("Summary:")
    print(f"Your trip covers {distance:.2f} kilometers. Using a {car_type}")
    print(f"with {fuel_type} fuel (emission factor: {emission_factor} g CO2/km),")
    print(f"this trip produces approximately {emission_kg:.2f} kg of carbon")
    print("dioxide emissions.")
    print()


def display_route_comparison(routes, car_type, fuel_type):
    """
    Display comparison of alternative routes with emissions.
    
    Args:
        routes: List of route dictionaries
        car_type: Vehicle type
        fuel_type: Fuel type
    """
    emission_factor = get_emission_factor(car_type, fuel_type)
    
    # Normalize vehicle and fuel types for ML predictor
    vehicle_type_map = {
        'LCGC': 'LCGC',
        'SUV': 'SUV',
        'EV': 'EV',
        'Sedan': 'Sedan'
    }
    fuel_type_map = {
        'bensin': 'Bensin',
        'solar': 'Diesel',
        'listrik': 'Listrik'
    }
    
    vehicle_type_ml = vehicle_type_map.get(car_type, car_type)
    fuel_type_ml = fuel_type_map.get(fuel_type, fuel_type.capitalize())
    
    print("\n" + "="*70)
    print("PERBANDINGAN RUTE ALTERNATIF")
    print("="*70)
    
    # Try to use ML predictor if available
    use_ml = ml_available
    route_emissions = []
    
    if use_ml:
        try:
            logger.info("Using ML predictor for route comparison")
            
            for route in routes:
                try:
                    # Extract features
                    features = feature_extractor.extract_features(
                        route, vehicle_type_ml, fuel_type_ml
                    )
                    
                    # Predict emission using ML
                    emission = mlr_predictor.predict_emission(
                        distance_km=features['distance_km'],
                        fuel_type=features['fuel_type'],
                        vehicle_type=features['vehicle_type'],
                        fuel_consumption_kml=features['fuel_consumption_kml'],
                        avg_speed_kmh=features['avg_speed_kmh']
                    )
                    
                    route_emissions.append({
                        'route': route,
                        'emission_g': emission,
                        'emission_kg': emission / 1000.0,
                        'prediction_method': 'ML',
                        'avg_speed_kmh': features['avg_speed_kmh']
                    })
                    
                except Exception as e:
                    logger.warning(f"ML prediction failed for route {route['route_number']}: {e}")
                    # Fallback to static calculation for this route
                    emission = route['distance_km'] * emission_factor
                    route_emissions.append({
                        'route': route,
                        'emission_g': emission,
                        'emission_kg': emission / 1000.0,
                        'prediction_method': 'Static (ML fallback)'
                    })
            
        except Exception as e:
            logger.error(f"ML prediction system failed: {e}. Falling back to static calculation.")
            use_ml = False
    
    # Use static calculation if ML is not available
    if not use_ml:
        logger.info("Using static calculation for route comparison")
        
        for route in routes:
            emission = route['distance_km'] * emission_factor
            route_emissions.append({
                'route': route,
                'emission_g': emission,
                'emission_kg': emission / 1000.0,
                'prediction_method': 'Static'
            })
    
    # Sort by emission (lowest first)
    route_emissions.sort(key=lambda x: x['emission_g'])
    
    # Display prediction method
    if use_ml:
        print("(Menggunakan prediksi AI berbasis Machine Learning)")
    else:
        print("(Menggunakan perhitungan statis)")
    
    # Display each route
    for idx, route_data in enumerate(route_emissions):
        route = route_data['route']
        is_best = idx == 0
        
        print(f"\n{'>>> ' if is_best else ''}RUTE {route['route_number']}{' (REKOMENDASI - EMISI TERENDAH) <<<' if is_best else ''}")
        print("-" * 70)
        print(f"Jarak        : {route['distance_km']:.2f} km")
        print(f"Waktu Tempuh : {route['duration_min']:.1f} menit")
        
        # Display average speed if available (ML prediction)
        if 'avg_speed_kmh' in route_data:
            print(f"Kecepatan Rata-rata : {route_data['avg_speed_kmh']:.1f} km/h")
        
        # Use EmissionFormatter to format emission with ML indicator
        emission_formatted = EmissionFormatter.format_emission_with_ml_indicator(
            route_data['emission_g'],
            route_data['prediction_method'],
            show_both_units=True,
            precision=2
        )
        print(f"Emisi Karbon : {emission_formatted}")
        
        if is_best and len(route_emissions) > 1:
            savings = route_emissions[-1]['emission_g'] - route_data['emission_g']
            savings_pct = (savings / route_emissions[-1]['emission_g']) * 100 if route_emissions[-1]['emission_g'] > 0 else 0
            # Use EmissionFormatter for savings display
            savings_formatted = EmissionFormatter.format_emission(savings, show_both_units=True, precision=2)
            print(f"Penghematan  : {savings_formatted} - {savings_pct:.1f}% lebih rendah")
        
        # Display turn-by-turn directions
        if route['steps']:
            print(f"\nPetunjuk Arah:")
            for step_idx, step in enumerate(route['steps'][:10], 1):  # Limit to 10 steps
                print(f"  {step_idx}. {step['instruction']} di {step['road']} ({step['distance_km']:.2f} km)")
            
            if len(route['steps']) > 10:
                print(f"  ... dan {len(route['steps']) - 10} langkah lainnya")
    
    print("\n" + "="*70)
    print(f">> REKOMENDASI: Gunakan Rute {route_emissions[0]['route']['route_number']} untuk emisi karbon terendah!")
    print("="*70)


def main():
    """Entry point for the Carbon Emission Calculator application."""
    try:
        # Get user input
        origin, destination, car_type, fuel_type = get_user_input()
        
        print("\nMencari rute alternatif dan menghitung emisi...")
        print("(Ini mungkin memakan waktu beberapa detik)")
        
        # Validate vehicle-fuel combination before making API call
        try:
            get_emission_factor(car_type, fuel_type)
        except KeyError:
            # Invalid combination - show valid options
            valid_combos = get_valid_combinations()
            print(f"\nError: Invalid vehicle-fuel combination '{car_type}-{fuel_type}'.")
            print("Valid combinations are:")
            for combo in valid_combos:
                parts = combo.split('-')
                print(f"  - {parts[0]}: {parts[1]}")
            return
        
        # Get alternative routes with detailed steps
        try:
            routes = get_alternative_routes(origin, destination)
        except Exception as e:
            print(f"\n{str(e)}")
            return
        
        # Display route comparison with emissions
        display_route_comparison(routes, car_type, fuel_type)
        
        # Ask user if they want emission reduction advice
        print("\n" + "="*70)
        while True:
            advice_choice = input("Apakah Anda ingin mendapatkan rekomendasi pengurangan emisi? (y/n): ").strip().lower()
            if advice_choice in ['y', 'n', 'yes', 'no']:
                break
            print("Pilihan tidak valid. Silakan masukkan 'y' atau 'n'.")
        
        if advice_choice in ['y', 'yes']:
            # Construct trip data dictionary from existing variables
            # Calculate total emission from the first route (or average if multiple)
            emission_factor = get_emission_factor(car_type, fuel_type)
            
            # Use the first route's data for the trip data
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
            
            # Get and display emission reduction advice
            print("\nMenghasilkan rekomendasi pengurangan emisi...")
            advice_output = get_emission_advice(trip_data)
            print("\n" + advice_output)
        
        # Generate visualization charts
        emission_factor = get_emission_factor(car_type, fuel_type)
        
        print("\nMembuat grafik visualisasi...")
        chart_files = []
        
        try:
            # Create emission progression chart (per 25km)
            chart1 = create_emission_chart(routes, car_type, fuel_type, emission_factor)
            chart_files.append(chart1)
            
            # Create comparison bar chart
            chart2 = create_comparison_bar_chart(routes, emission_factor)
            chart_files.append(chart2)
            
            # Display chart information
            display_chart_info(chart_files)
            
        except Exception as e:
            print(f"\nPeringatan: Tidak dapat membuat grafik - {str(e)}")
            print("Perhitungan emisi tetap valid, hanya visualisasi yang gagal.")
        
    except KeyboardInterrupt:
        print("\n\nCalculation cancelled by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}")


if __name__ == "__main__":
    main()
