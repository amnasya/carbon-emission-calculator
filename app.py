#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flask Web Application for Carbon Emission Calculator
"""

from flask import Flask, render_template, request, jsonify
from src.maps_api import get_alternative_routes
from src.emission import calculate_emission, get_emission_factor, EMISSION_FACTORS
from src.ml_predictor import (calculate_adjusted_emission, FuelConsumptionPredictor,
                          DRIVING_STYLE_MAP, TRAFFIC_MAP, WEATHER_MAP, 
                          ROAD_TYPE_MAP, AC_USAGE_MAP)
from src.mlr_emission_predictor import MLREmissionPredictor, FeatureExtractor
from src.route_comparator import RouteEmissionComparator
from src.emission_formatter import EmissionFormatter
import traceback
import logging

app = Flask(__name__, 
            template_folder='src/templates',
            static_folder='src/static')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize ML predictor at startup
ml_predictor = FuelConsumptionPredictor()

# Initialize MLR emission predictor (with error handling)
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

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')

@app.route('/api/calculate', methods=['POST'])
def calculate():
    """Calculate emissions for routes with ML prediction"""
    try:
        data = request.json
        
        # Get parameters
        origin_lat = float(data.get('origin_lat'))
        origin_lng = float(data.get('origin_lng'))
        dest_lat = float(data.get('dest_lat'))
        dest_lng = float(data.get('dest_lng'))
        car_type = data.get('car_type')
        fuel_type = data.get('fuel_type')
        
        # Check if user wants to use ML (default: False - static is more reliable)
        use_ml = data.get('use_ml', False) and ml_available
        
        # Format as addresses for the API
        origin = f"{origin_lat},{origin_lng}"
        destination = f"{dest_lat},{dest_lng}"
        
        # Normalize vehicle and fuel types for ML predictor
        # Map from old format to new format
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
        
        # Validate vehicle-fuel combination for static calculation
        try:
            emission_factor = get_emission_factor(car_type, fuel_type)
        except KeyError:
            return jsonify({
                'success': False,
                'error': f'Kombinasi kendaraan-bahan bakar tidak valid: {car_type}-{fuel_type}'
            }), 400
        
        # Get alternative routes
        routes = get_alternative_routes(origin, destination)
        
        # Calculate emissions for each route
        route_emissions = []
        
        if use_ml and ml_available:
            # Use ML predictor for emission calculation
            try:
                logger.info(f"Using ML predictor for {len(routes)} routes")
                
                for route in routes:
                    try:
                        # Extract features
                        features = feature_extractor.extract_features(
                            route, vehicle_type_ml, fuel_type_ml
                        )
                        
                        # Predict emission using ML
                        emission_g = mlr_predictor.predict_emission(
                            distance_km=features['distance_km'],
                            fuel_type=features['fuel_type'],
                            vehicle_type=features['vehicle_type'],
                            fuel_consumption_kml=features['fuel_consumption_kml'],
                            avg_speed_kmh=features['avg_speed_kmh']
                        )
                        
                        # Calculate emission points per 25km using ML predictions
                        emission_points = []
                        distance_points = []
                        current_distance = 0
                        interval = 25
                        
                        while current_distance <= route['distance_km']:
                            distance_points.append(current_distance)
                            # Scale emission proportionally for visualization
                            if route['distance_km'] > 0:
                                point_emission = (current_distance / route['distance_km']) * emission_g / 1000.0
                            else:
                                point_emission = 0
                            emission_points.append(point_emission)
                            current_distance += interval
                        
                        if distance_points[-1] < route['distance_km']:
                            distance_points.append(route['distance_km'])
                            emission_points.append(emission_g / 1000.0)
                        
                        # Format emission for display
                        emission_formatted = EmissionFormatter.format_emission_with_ml_indicator(
                            emission_g, 'ML', show_both_units=True, precision=2
                        )
                        
                        route_emissions.append({
                            'route_number': route['route_number'],
                            'distance_km': route['distance_km'],
                            'duration_min': route['duration_min'],
                            'emission_g': emission_g,
                            'emission_kg': emission_g / 1000.0,
                            'emission_formatted': emission_formatted,
                            'steps': route['steps'],
                            'emission_points': emission_points,
                            'distance_points': distance_points,
                            'geometry': route.get('geometry', []),
                            'prediction_method': 'ML',
                            'avg_speed_kmh': features['avg_speed_kmh']
                        })
                        
                    except Exception as e:
                        logger.warning(f"ML prediction failed for route {route['route_number']}: {e}")
                        # Fallback to static calculation for this route
                        emission_g = route['distance_km'] * emission_factor
                        
                        # Calculate emission points per 25km
                        emission_points = []
                        distance_points = []
                        current_distance = 0
                        interval = 25
                        
                        while current_distance <= route['distance_km']:
                            distance_points.append(current_distance)
                            emission_points.append(current_distance * emission_factor / 1000.0)
                            current_distance += interval
                        
                        if distance_points[-1] < route['distance_km']:
                            distance_points.append(route['distance_km'])
                            emission_points.append(route['distance_km'] * emission_factor / 1000.0)
                        
                        # Format emission for display
                        emission_formatted = EmissionFormatter.format_emission_with_ml_indicator(
                            emission_g, 'Static (ML fallback)', show_both_units=True, precision=2
                        )
                        
                        route_emissions.append({
                            'route_number': route['route_number'],
                            'distance_km': route['distance_km'],
                            'duration_min': route['duration_min'],
                            'emission_g': emission_g,
                            'emission_kg': emission_g / 1000.0,
                            'emission_formatted': emission_formatted,
                            'steps': route['steps'],
                            'emission_points': emission_points,
                            'distance_points': distance_points,
                            'geometry': route.get('geometry', []),
                            'prediction_method': 'Static (ML fallback)'
                        })
                
            except Exception as e:
                logger.error(f"ML prediction system failed: {e}. Falling back to static calculation.")
                # Complete fallback to static calculation
                use_ml = False
        
        # Use static calculation if ML is not available or disabled
        if not use_ml or not ml_available:
            logger.info(f"Using static calculation for {len(routes)} routes")
            
            for route in routes:
                emission_g = route['distance_km'] * emission_factor
                
                # Calculate emission points per 25km
                emission_points = []
                distance_points = []
                current_distance = 0
                interval = 25
                
                while current_distance <= route['distance_km']:
                    distance_points.append(current_distance)
                    emission_points.append(current_distance * emission_factor / 1000.0)
                    current_distance += interval
                
                if distance_points[-1] < route['distance_km']:
                    distance_points.append(route['distance_km'])
                    emission_points.append(route['distance_km'] * emission_factor / 1000.0)
                
                # Format emission for display
                emission_formatted = EmissionFormatter.format_emission_with_ml_indicator(
                    emission_g, 'Static', show_both_units=True, precision=2
                )
                
                route_emissions.append({
                    'route_number': route['route_number'],
                    'distance_km': route['distance_km'],
                    'duration_min': route['duration_min'],
                    'emission_g': emission_g,
                    'emission_kg': emission_g / 1000.0,
                    'emission_formatted': emission_formatted,
                    'steps': route['steps'],
                    'emission_points': emission_points,
                    'distance_points': distance_points,
                    'geometry': route.get('geometry', []),
                    'prediction_method': 'Static'
                })
        
        # Sort by emission (lowest first)
        route_emissions.sort(key=lambda x: x['emission_g'])
        
        # Calculate savings
        if len(route_emissions) > 1:
            best = route_emissions[0]
            worst = route_emissions[-1]
            savings_g = worst['emission_g'] - best['emission_g']
            savings_pct = (savings_g / worst['emission_g']) * 100 if worst['emission_g'] > 0 else 0
            
            route_emissions[0]['savings_g'] = savings_g
            route_emissions[0]['savings_pct'] = savings_pct
        
        return jsonify({
            'success': True,
            'routes': route_emissions,
            'emission_factor': emission_factor,
            'car_type': car_type,
            'fuel_type': fuel_type,
            'ml_enabled': use_ml and ml_available,
            'ml_available': ml_available
        })
        
    except Exception as e:
        logger.error(f"Error in calculate endpoint: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/vehicle-types')
def get_vehicle_types():
    """Get available vehicle types and fuel types"""
    vehicle_data = {}
    for car_type, fuels in EMISSION_FACTORS.items():
        vehicle_data[car_type] = {
            'fuels': list(fuels.keys()),
            'factors': fuels
        }
    
    return jsonify({
        'success': True,
        'vehicles': vehicle_data
    })

if __name__ == '__main__':
    print("="*70)
    print("Carbon Emission Calculator - Web Application")
    print("="*70)
    print("\nStarting server...")
    print("Open your browser and go to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("="*70)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
