#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flask Web Application for Carbon Emission Calculator with ML
"""

from flask import Flask, render_template, request, jsonify
from maps_api import get_alternative_routes
from emission import calculate_emission, get_emission_factor, EMISSION_FACTORS
from ml_predictor import (calculate_adjusted_emission, FuelConsumptionPredictor,
                          DRIVING_STYLE_MAP, TRAFFIC_MAP, WEATHER_MAP, 
                          ROAD_TYPE_MAP, AC_USAGE_MAP)
import traceback

app = Flask(__name__)

# Initialize ML predictor at startup
print("Initializing ML Predictor...")
ml_predictor = FuelConsumptionPredictor()
print("ML Predictor ready!")

@app.route('/')
def index():
    """Render main page"""
    return render_template('index_ml.html')

@app.route('/api/calculate', methods=['POST'])
def calculate():
    """Calculate emissions for routes with ML adjustment"""
    try:
        data = request.json
        
        # Get parameters
        origin_lat = float(data.get('origin_lat'))
        origin_lng = float(data.get('origin_lng'))
        dest_lat = float(data.get('dest_lat'))
        dest_lng = float(data.get('dest_lng'))
        car_type = data.get('car_type')
        fuel_type = data.get('fuel_type')
        
        # Get ML parameters (optional, with defaults)
        driving_style = DRIVING_STYLE_MAP.get(data.get('driving_style', 'normal'), 1)
        traffic_condition = TRAFFIC_MAP.get(data.get('traffic_condition', 'moderate'), 1)
        weather_condition = WEATHER_MAP.get(data.get('weather_condition', 'clear'), 0)
        road_type = ROAD_TYPE_MAP.get(data.get('road_type', 'mixed'), 2)
        ac_usage = AC_USAGE_MAP.get(data.get('ac_usage', 'on'), 1)
        
        # Format as addresses for the API
        origin = f"{origin_lat},{origin_lng}"
        destination = f"{dest_lat},{dest_lng}"
        
        # Validate vehicle-fuel combination
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
        for route in routes:
            # Estimate average speed based on distance and duration
            speed_avg = (route['distance_km'] / (route['duration_min'] / 60)) if route['duration_min'] > 0 else 60
            speed_avg = min(max(speed_avg, 20), 120)  # Clip to reasonable range
            
            # Calculate base emission
            base_emission_g = route['distance_km'] * emission_factor
            
            # Calculate ML-adjusted emission
            ml_result = calculate_adjusted_emission(
                route['distance_km'],
                emission_factor,
                driving_style,
                traffic_condition,
                weather_condition,
                road_type,
                speed_avg,
                ac_usage
            )
            
            # Calculate emission points per 25km (both base and adjusted)
            emission_points_base = []
            emission_points_adjusted = []
            distance_points = []
            current_distance = 0
            interval = 25
            
            while current_distance <= route['distance_km']:
                distance_points.append(current_distance)
                emission_points_base.append(current_distance * emission_factor / 1000.0)
                emission_points_adjusted.append(current_distance * ml_result['adjusted_emission_factor'] / 1000.0)
                current_distance += interval
            
            if distance_points[-1] < route['distance_km']:
                distance_points.append(route['distance_km'])
                emission_points_base.append(route['distance_km'] * emission_factor / 1000.0)
                emission_points_adjusted.append(route['distance_km'] * ml_result['adjusted_emission_factor'] / 1000.0)
            
            route_emissions.append({
                'route_number': route['route_number'],
                'distance_km': route['distance_km'],
                'duration_min': route['duration_min'],
                'speed_avg': round(speed_avg, 1),
                'emission_g': ml_result['adjusted_emission_g'],
                'emission_kg': ml_result['adjusted_emission_kg'],
                'base_emission_g': ml_result['base_emission_g'],
                'base_emission_kg': ml_result['base_emission_kg'],
                'adjustment_factor': ml_result['adjustment_factor'],
                'difference_g': ml_result['difference_g'],
                'difference_pct': ml_result['difference_pct'],
                'steps': route['steps'],
                'emission_points': emission_points_adjusted,
                'emission_points_base': emission_points_base,
                'distance_points': distance_points
            })
        
        # Sort by emission (lowest first)
        route_emissions.sort(key=lambda x: x['emission_g'])
        
        # Calculate savings
        if len(route_emissions) > 1:
            best = route_emissions[0]
            worst = route_emissions[-1]
            savings_g = worst['emission_g'] - best['emission_g']
            savings_pct = (savings_g / worst['emission_g']) * 100
            
            route_emissions[0]['savings_g'] = savings_g
            route_emissions[0]['savings_pct'] = savings_pct
        
        return jsonify({
            'success': True,
            'routes': route_emissions,
            'emission_factor': emission_factor,
            'car_type': car_type,
            'fuel_type': fuel_type,
            'ml_enabled': True,
            'conditions': {
                'driving_style': data.get('driving_style', 'normal'),
                'traffic_condition': data.get('traffic_condition', 'moderate'),
                'weather_condition': data.get('weather_condition', 'clear'),
                'road_type': data.get('road_type', 'mixed'),
                'ac_usage': data.get('ac_usage', 'on')
            }
        })
        
    except Exception as e:
        print(f"Error: {e}")
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

@app.route('/api/ml-info')
def get_ml_info():
    """Get ML model information"""
    try:
        importance = ml_predictor.get_feature_importance()
        return jsonify({
            'success': True,
            'model_trained': ml_predictor.is_trained,
            'feature_importance': importance
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    print("="*70)
    print("Carbon Emission Calculator - Web Application with ML")
    print("="*70)
    print("\nStarting server...")
    print("Open your browser and go to: http://localhost:5000")
    print("\nFeatures:")
    print("  - ML-based fuel consumption prediction")
    print("  - Driving style adjustment")
    print("  - Traffic condition impact")
    print("  - Weather condition impact")
    print("\nPress Ctrl+C to stop the server")
    print("="*70)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
