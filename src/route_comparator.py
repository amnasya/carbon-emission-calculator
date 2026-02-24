#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Route Emission Comparator
Compare emissions across routes and select the best option
"""

from typing import Dict, List, Optional, Callable
from src.mlr_emission_predictor import MLREmissionPredictor, FeatureExtractor
from src.emission_formatter import EmissionFormatter
import logging

# Configure logging
logger = logging.getLogger(__name__)


class RouteEmissionComparator:
    """
    Compare emissions across routes and select the best option.
    
    This class uses the ML Emission Predictor to calculate emissions for
    multiple routes and identifies the route with the lowest predicted emissions.
    """
    
    def __init__(self, ml_predictor: Optional[MLREmissionPredictor] = None,
                 fallback_calculator: Optional[Callable] = None):
        """
        Initialize with ML predictor and optional fallback calculator.
        
        Args:
            ml_predictor: MLREmissionPredictor instance. If None, creates a new one.
            fallback_calculator: Optional fallback function for static emission calculation.
                                Should accept (distance_km, vehicle_type, fuel_type) and return emission in grams.
        """
        self.ml_predictor = ml_predictor or MLREmissionPredictor()
        self.feature_extractor = FeatureExtractor()
        self.fallback_calculator = fallback_calculator
        self.ml_available = True  # Track if ML is available
        
        # Test if ML predictor is working
        try:
            # Try to access model to verify it's loaded
            if hasattr(self.ml_predictor, 'is_loaded'):
                self.ml_available = self.ml_predictor.is_loaded
        except Exception as e:
            logger.warning(f"ML predictor initialization check failed: {e}")
            self.ml_available = False
    
    def compare_routes(self, 
                      routes: List[Dict],
                      vehicle_type: str,
                      fuel_type: str) -> Dict:
        """
        Compare emissions for multiple routes with ML prediction and fallback support.
        
        Args:
            routes: List of route dicts from Maps API with keys:
                   - route_number: Route identifier
                   - distance_km or distance_m: Route distance
                   - duration_min: Route duration in minutes
                   - steps: Route steps (optional)
                   - geometry: Route geometry (optional)
            vehicle_type: Vehicle type (LCGC, SUV, Sedan, EV)
            fuel_type: Fuel type (Bensin, Diesel, Listrik)
            
        Returns:
            Dict with:
            - best_route: Route with lowest emission (dict)
            - all_routes: All routes with predictions (list of dicts)
            - savings: Emission savings vs worst route (dict)
            - explanation: Human-readable explanation (str)
            - ml_enabled: Whether ML predictions were used (bool)
            - fallback_used: Whether fallback was used for any routes (bool)
            - error_message: Error message if ML failed (optional)
            
        Raises:
            ValueError: If routes list is empty or invalid
            RuntimeError: If both ML and fallback fail for all routes
        """
        if not routes:
            raise ValueError("Routes list cannot be empty")
        
        if not isinstance(routes, list):
            raise ValueError("Routes must be a list")
        
        # Track if we're using ML or fallback
        ml_used = False
        fallback_used = False
        ml_error_message = None
        
        # Calculate emissions for each route
        route_predictions = []
        
        for route in routes:
            route_number = route.get('route_number', len(route_predictions) + 1)
            
            # Try ML prediction first
            ml_success = False
            
            if self.ml_available:
                try:
                    # Extract features from route data
                    features = self.feature_extractor.extract_features(
                        route, vehicle_type, fuel_type
                    )
                    
                    # Predict emission using ML
                    predicted_emission_g = self.ml_predictor.predict_emission(
                        distance_km=features['distance_km'],
                        fuel_type=features['fuel_type'],
                        vehicle_type=features['vehicle_type'],
                        fuel_consumption_kml=features['fuel_consumption_kml'],
                        avg_speed_kmh=features['avg_speed_kmh']
                    )
                    
                    # Build route prediction result
                    route_prediction = {
                        'route_number': route_number,
                        'distance_km': features['distance_km'],
                        'duration_min': route.get('duration_min', route.get('duration', 0)),
                        'avg_speed_kmh': features['avg_speed_kmh'],
                        'predicted_emission_g': predicted_emission_g,
                        'predicted_emission_kg': predicted_emission_g / 1000.0,
                        'prediction_method': 'ML',
                        'features_used': features
                    }
                    
                    # Include optional fields if present
                    if 'steps' in route:
                        route_prediction['steps'] = route['steps']
                    if 'geometry' in route:
                        route_prediction['geometry'] = route['geometry']
                    
                    route_predictions.append(route_prediction)
                    ml_success = True
                    ml_used = True
                    
                except Exception as e:
                    # Log ML prediction failure
                    error_msg = f"ML prediction failed for route {route_number}: {str(e)}"
                    logger.warning(error_msg)
                    
                    # Store error message for user notification
                    if ml_error_message is None:
                        ml_error_message = f"ML prediction unavailable: {str(e)}"
                    
                    # Mark ML as unavailable for subsequent routes
                    self.ml_available = False
            
            # If ML failed or unavailable, try fallback
            if not ml_success:
                try:
                    # Extract distance for fallback calculation
                    if 'distance_km' in route:
                        distance_km = route['distance_km']
                    elif 'distance_m' in route:
                        distance_km = route['distance_m'] / 1000.0
                    elif 'distance' in route:
                        distance_km = route['distance'] / 1000.0
                    else:
                        raise ValueError("Route data must contain distance information")
                    
                    # Use fallback calculator if provided
                    if self.fallback_calculator:
                        predicted_emission_g = self.fallback_calculator(
                            distance_km, vehicle_type, fuel_type
                        )
                    else:
                        # Default fallback: simple distance-based calculation
                        # Use conservative emission factors
                        emission_factors = {
                            ('LCGC', 'Bensin'): 120,
                            ('LCGC', 'Diesel'): 140,
                            ('SUV', 'Bensin'): 180,
                            ('SUV', 'Diesel'): 200,
                            ('Sedan', 'Bensin'): 150,
                            ('Sedan', 'Diesel'): 170,
                            ('EV', 'Listrik'): 40
                        }
                        
                        # Normalize fuel type for lookup
                        fuel_normalized = fuel_type
                        if fuel_type.lower() == 'solar':
                            fuel_normalized = 'Diesel'
                        elif fuel_type.lower() == 'bensin':
                            fuel_normalized = 'Bensin'
                        elif fuel_type.lower() == 'listrik':
                            fuel_normalized = 'Listrik'
                        
                        factor = emission_factors.get((vehicle_type, fuel_normalized), 150)
                        predicted_emission_g = distance_km * factor
                    
                    # Build route prediction result with fallback
                    route_prediction = {
                        'route_number': route_number,
                        'distance_km': distance_km,
                        'duration_min': route.get('duration_min', route.get('duration', 0)),
                        'predicted_emission_g': predicted_emission_g,
                        'predicted_emission_kg': predicted_emission_g / 1000.0,
                        'prediction_method': 'Static (Fallback)',
                        'features_used': {
                            'distance_km': distance_km,
                            'vehicle_type': vehicle_type,
                            'fuel_type': fuel_type
                        }
                    }
                    
                    # Include optional fields if present
                    if 'steps' in route:
                        route_prediction['steps'] = route['steps']
                    if 'geometry' in route:
                        route_prediction['geometry'] = route['geometry']
                    
                    route_predictions.append(route_prediction)
                    fallback_used = True
                    
                    logger.info(f"Used fallback calculation for route {route_number}")
                    
                except Exception as e:
                    # Both ML and fallback failed for this route
                    logger.error(f"Both ML and fallback failed for route {route_number}: {e}")
                    continue
        
        # Check if we got any predictions
        if not route_predictions:
            error_msg = "Failed to calculate emissions for all routes. "
            if ml_error_message:
                error_msg += f"ML error: {ml_error_message}. "
            error_msg += "Fallback calculation also failed."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Sort routes by emission (lowest first)
        route_predictions.sort(key=lambda x: x['predicted_emission_g'])
        
        # Identify best and worst routes
        best_route = route_predictions[0]
        worst_route = route_predictions[-1]
        
        # Mark best route as recommended
        best_route['is_recommended'] = True
        
        # Calculate emission differences for alternative routes
        alternative_routes = []
        for route in route_predictions[1:]:
            emission_diff_g = route['predicted_emission_g'] - best_route['predicted_emission_g']
            # Handle division by zero if best route has zero emission
            if best_route['predicted_emission_g'] > 0:
                emission_diff_pct = (emission_diff_g / best_route['predicted_emission_g']) * 100
            else:
                emission_diff_pct = 0.0
            
            alternative_routes.append({
                'route_number': route['route_number'],
                'predicted_emission_g': route['predicted_emission_g'],
                'predicted_emission_kg': route['predicted_emission_kg'],
                'distance_km': route['distance_km'],
                'duration_min': route['duration_min'],
                'emission_difference_g': emission_diff_g,
                'emission_difference_pct': emission_diff_pct,
                'is_recommended': False
            })
        
        # Calculate savings vs worst route
        savings_g = worst_route['predicted_emission_g'] - best_route['predicted_emission_g']
        savings_pct = (savings_g / worst_route['predicted_emission_g']) * 100 if worst_route['predicted_emission_g'] > 0 else 0
        
        savings = {
            'vs_worst_route_g': savings_g,
            'vs_worst_route_pct': savings_pct
        }
        
        # Generate explanation with fallback information
        explanation = self.generate_explanation(best_route, alternative_routes, savings, fallback_used)
        
        # Build result dictionary
        result = {
            'best_route': best_route,
            'all_routes': route_predictions,
            'alternative_routes': alternative_routes,
            'savings': savings,
            'explanation': explanation,
            'ml_enabled': ml_used,
            'fallback_used': fallback_used
        }
        
        # Add error message if ML failed
        if ml_error_message and fallback_used:
            result['error_message'] = ml_error_message
            logger.warning(f"ML prediction failed, using fallback: {ml_error_message}")
        
        return result
    
    def generate_explanation(self,
                           best_route: Dict,
                           alternative_routes: List[Dict],
                           savings: Dict,
                           fallback_used: bool = False) -> str:
        """
        Generate human-readable explanation of recommendation.
        
        Args:
            best_route: Best route dict with emission predictions
            alternative_routes: List of alternative route dicts
            savings: Savings dict with emission reductions
            fallback_used: Whether fallback calculation was used
            
        Returns:
            Human-readable explanation string
        """
        # Format emission values using EmissionFormatter
        best_emission_g = best_route['predicted_emission_g']
        
        # Use formatter to get properly formatted emission string
        emission_str = EmissionFormatter.format_emission(
            best_emission_g, show_both_units=False, precision=2
        )
        
        explanation = (
            f"Route {best_route['route_number']} is recommended as the lowest-emission option, "
            f"with a predicted CO₂ emission of {emission_str}. "
        )
        
        # Add distance and duration context
        explanation += (
            f"This route covers {best_route['distance_km']:.1f} km "
            f"in approximately {best_route['duration_min']:.0f} minutes. "
        )
        
        # Add comparison with alternatives if available
        if alternative_routes:
            explanation += (
                f"Compared to alternative routes, this option produces "
            )
            
            if len(alternative_routes) == 1:
                alt = alternative_routes[0]
                explanation += (
                    f"{alt['emission_difference_g']:.0f} g "
                    f"({alt['emission_difference_pct']:.1f}%) less CO₂. "
                )
            else:
                explanation += (
                    f"between {alternative_routes[0]['emission_difference_g']:.0f} g "
                    f"and {alternative_routes[-1]['emission_difference_g']:.0f} g less CO₂. "
                )
        
        # Add savings information
        if savings['vs_worst_route_g'] > 0:
            explanation += (
                f"By choosing this route, you can save up to "
                f"{savings['vs_worst_route_g']:.0f} g of CO₂ "
                f"({savings['vs_worst_route_pct']:.1f}% reduction). "
            )
        
        # Add prediction method context
        if fallback_used:
            explanation += (
                "Note: ML prediction is currently unavailable. "
                "This prediction uses static emission factors based on distance, "
                "vehicle type, and fuel type. "
            )
        else:
            explanation += (
                "This prediction is based on multiple factors including distance, "
                "vehicle type, fuel type, fuel consumption, and average speed. "
            )
        
        return explanation
