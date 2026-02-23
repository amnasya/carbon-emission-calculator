#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple Flask Web Application - No ML Dependencies
"""

from flask import Flask, render_template, request, jsonify
from maps_api import get_alternative_routes
from emission import calculate_emission, get_emission_factor, EMISSION_FACTORS
from advisor import get_emission_advice
import traceback

app = Flask(__name__)

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')

@app.route('/api/calculate', methods=['POST'])
def calculate():
    """Calculate emissions for routes"""
    try:
        data = request.json
        
        # Get parameters
        origin_lat = float(data.get('origin_lat'))
        origin_lng = float(data.get('origin_lng'))
        dest_lat = float(data.get('dest_lat'))
        dest_lng = float(data.get('dest_lng'))
        car_type = data.get('car_type')
        fuel_type = data.get('fuel_type')
        
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
            
            route_emissions.append({
                'route_number': route['route_number'],
                'distance_km': route['distance_km'],
                'duration_min': route['duration_min'],
                'emission_g': emission_g,
                'emission_kg': emission_g / 1000.0,
                'steps': route['steps'],
                'emission_points': emission_points,
                'distance_points': distance_points,
                'geometry': route.get('geometry', [])  # Add geometry for map display
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
        
        # Generate emission reduction advice
        trip_data = {
            'distance_km': route_emissions[0]['distance_km'],
            'car_type': car_type,
            'fuel_type': fuel_type,
            'emission_g': route_emissions[0]['emission_g'],
            'routes': [
                {
                    'route_number': route['route_number'],
                    'distance_km': route['distance_km'],
                    'duration_min': route['duration_min'],
                    'emission_g': route['emission_g']
                }
                for route in route_emissions
            ]
        }
        
        advice = get_emission_advice(trip_data)
        
        return jsonify({
            'success': True,
            'routes': route_emissions,
            'emission_factor': emission_factor,
            'car_type': car_type,
            'fuel_type': fuel_type,
            'advice': advice
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

if __name__ == '__main__':
    print("="*70)
    print("Carbon Emission Calculator - Web Application")
    print("="*70)
    print("\nStarting server...")
    print("Open your browser and go to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("="*70)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
