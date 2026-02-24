"""
Emission Reduction Advisor Module

This module provides AI-powered recommendations for reducing carbon emissions
based on trip data from the Carbon Emission Calculator. It analyzes trip
characteristics (distance, vehicle type, fuel type, emissions) and generates
2-3 personalized, actionable recommendations with estimated emission savings.

The advisor operates as a standalone module that:
- Accepts pre-calculated trip data without recalculating emissions
- Uses existing EMISSION_FACTORS for consistency
- Provides distance-appropriate recommendations
- Calculates potential emission savings for each recommendation
- Formats output in clear, readable Indonesian language

Basic Usage Example:
    from advisor import get_emission_advice
    
    # Simple single-route trip
    trip_data = {
        "distance_km": 12.5,
        "car_type": "SUV",
        "fuel_type": "bensin",
        "emission_g": 2250.0
    }
    
    advice = get_emission_advice(trip_data)
    print(advice)

Multi-Route Usage Example:
    from advisor import get_emission_advice
    
    # Trip with multiple route alternatives
    trip_data = {
        "distance_km": 15.3,
        "car_type": "LCGC",
        "fuel_type": "bensin",
        "emission_g": 1836.0,
        "routes": [
            {
                "route_number": 1,
                "distance_km": 15.3,
                "duration_min": 25.0,
                "emission_g": 1836.0
            },
            {
                "route_number": 2,
                "distance_km": 14.8,
                "duration_min": 28.0,
                "emission_g": 1776.0
            },
            {
                "route_number": 3,
                "distance_km": 16.1,
                "duration_min": 23.0,
                "emission_g": 1932.0
            }
        ]
    }
    
    advice = get_emission_advice(trip_data)
    print(advice)

Electric Vehicle Usage Example:
    from advisor import get_emission_advice
    
    # Trip with electric vehicle
    trip_data = {
        "distance_km": 45.0,
        "car_type": "EV",
        "fuel_type": "listrik",
        "emission_g": 450.0
    }
    
    advice = get_emission_advice(trip_data)
    print(advice)

Error Handling Example:
    from advisor import get_emission_advice
    
    # Invalid vehicle-fuel combination
    trip_data = {
        "distance_km": 10.0,
        "car_type": "EV",
        "fuel_type": "bensin",  # Invalid: EV cannot use bensin
        "emission_g": 1200.0
    }
    
    advice = get_emission_advice(trip_data)
    # Returns: "Error: Invalid vehicle-fuel combination: EV-bensin. Valid combinations are: ..."

Integration with Main Application:
    # In main.py, after calculating emissions:
    from advisor import get_emission_advice
    
    # Construct trip data from existing variables
    trip_data = {
        "distance_km": distance,
        "car_type": car_type,
        "fuel_type": fuel_type,
        "emission_g": total_emission
    }
    
    # Optionally get advice
    user_wants_advice = input("\\nIngin mendapat rekomendasi pengurangan emisi? (y/n): ")
    if user_wants_advice.lower() == 'y':
        advice = get_emission_advice(trip_data)
        print("\\n" + advice)

Requirements Addressed:
- 4.1: Separate Python module implementation
- 7.4: Validation of vehicle-fuel combinations
- 7.5: Graceful error handling for invalid inputs

Module Components:
- TripAnalyzer: Analyzes trip data and categorizes distance
- RecommendationEngine: Generates 2-3 personalized recommendations
- SavingsCalculator: Calculates emission savings for each recommendation
- validate_trip_data: Validates input data before processing
- format_advice_output: Formats output in readable Indonesian
- get_emission_advice: Main entry point (facade function)
"""

from typing import TypedDict, List, Optional, Union
from dataclasses import dataclass
from src.emission import EMISSION_FACTORS, get_emission_factor


# ============================================================================
# Data Models
# ============================================================================

class RouteData(TypedDict):
    """Data model for individual route information."""
    route_number: int
    distance_km: float
    duration_min: float
    emission_g: float


class TripData(TypedDict):
    """
    Input data model for trip information.
    
    Required fields:
        distance_km: Total distance traveled in kilometers
        car_type: Vehicle type (LCGC, SUV, or EV)
        fuel_type: Fuel type (bensin, solar, or listrik)
        emission_g: Pre-calculated emission in grams of CO2
    
    Optional fields:
        routes: List of alternative routes with individual emissions
    """
    distance_km: float
    car_type: str
    fuel_type: str
    emission_g: float
    routes: Optional[List[RouteData]]


@dataclass
class VehicleInfo:
    """Vehicle information extracted from trip data."""
    car_type: str
    fuel_type: str
    emission_factor: float
    is_ev: bool


@dataclass
class TripAnalysis:
    """Analysis results from trip data processing."""
    total_distance: float
    total_emission_g: float
    total_emission_kg: float
    vehicle_info: VehicleInfo
    distance_category: str  # 'short', 'medium', 'long'
    best_route_index: int  # -1 if single route
    current_route_index: int  # -1 if single route


@dataclass
class EmissionSavings:
    """Emission savings calculation results."""
    savings_g: float
    savings_kg: float
    savings_percentage: float


@dataclass
class Recommendation:
    """Individual recommendation with savings information."""
    title: str
    description: str
    type: str  # 'vehicle_switch', 'route_change', 'mode_shift', 'efficiency'
    priority: int  # 1-3, lower is higher priority
    savings: EmissionSavings


class AdvisorError(TypedDict):
    """Error response model."""
    success: bool
    error: str
    error_type: str  # 'validation_error', 'calculation_error', 'system_error'


# ============================================================================
# Input Validation
# ============================================================================

def validate_trip_data(trip_data: dict) -> Union[None, AdvisorError]:
    """
    Validate trip data input for required fields and valid values.
    
    This function checks:
    - Presence of all required fields
    - Correct data types for all fields
    - Positive values for distance and emission
    - Valid vehicle-fuel combination exists in EMISSION_FACTORS
    
    Args:
        trip_data: Dictionary containing trip information
    
    Returns:
        None if validation passes
        AdvisorError dict if validation fails
    
    Requirements:
        - 7.4: Validates vehicle-fuel combination exists in EMISSION_FACTORS
        - 7.5: Returns error message without crashing on invalid input
    """
    # Check required fields
    required_fields = ['distance_km', 'car_type', 'fuel_type', 'emission_g']
    for field in required_fields:
        if field not in trip_data:
            return {
                'success': False,
                'error': f"Missing required field: {field}",
                'error_type': 'validation_error'
            }
    
    # Validate data types
    try:
        distance = float(trip_data['distance_km'])
        emission = float(trip_data['emission_g'])
    except (ValueError, TypeError) as e:
        return {
            'success': False,
            'error': f"Invalid data type: distance_km and emission_g must be numeric",
            'error_type': 'validation_error'
        }
    
    # Validate string fields
    if not isinstance(trip_data['car_type'], str) or not trip_data['car_type']:
        return {
            'success': False,
            'error': "Invalid data type: car_type must be a non-empty string",
            'error_type': 'validation_error'
        }
    
    if not isinstance(trip_data['fuel_type'], str) or not trip_data['fuel_type']:
        return {
            'success': False,
            'error': "Invalid data type: fuel_type must be a non-empty string",
            'error_type': 'validation_error'
        }
    
    # Validate positive values
    if distance <= 0:
        return {
            'success': False,
            'error': "Distance must be positive",
            'error_type': 'validation_error'
        }
    
    if emission <= 0:
        return {
            'success': False,
            'error': "Emission must be positive",
            'error_type': 'validation_error'
        }
    
    # Validate vehicle-fuel combination exists in EMISSION_FACTORS
    car_type = trip_data['car_type']
    fuel_type = trip_data['fuel_type']
    
    try:
        get_emission_factor(car_type, fuel_type)
    except KeyError:
        # Build list of valid combinations for error message
        valid_combinations = []
        for vehicle, fuels in EMISSION_FACTORS.items():
            for fuel in fuels.keys():
                valid_combinations.append(f"{vehicle}-{fuel}")
        
        return {
            'success': False,
            'error': f"Invalid vehicle-fuel combination: {car_type}-{fuel_type}. "
                    f"Valid combinations are: {', '.join(valid_combinations)}",
            'error_type': 'validation_error'
        }
    
    # Validate routes if provided
    if 'routes' in trip_data and trip_data['routes'] is not None:
        if not isinstance(trip_data['routes'], list):
            return {
                'success': False,
                'error': "Invalid data type: routes must be a list",
                'error_type': 'validation_error'
            }
        
        if len(trip_data['routes']) == 0:
            return {
                'success': False,
                'error': "Routes list cannot be empty if provided",
                'error_type': 'validation_error'
            }
        
        # Validate each route has required fields
        for idx, route in enumerate(trip_data['routes']):
            route_required = ['route_number', 'distance_km', 'duration_min', 'emission_g']
            for field in route_required:
                if field not in route:
                    return {
                        'success': False,
                        'error': f"Route {idx} missing required field: {field}",
                        'error_type': 'validation_error'
                    }
    
    return None


# ============================================================================
# TripAnalyzer Component
# ============================================================================

class TripAnalyzer:
    """
    Analyzes trip data and generates insights for recommendation engine.
    
    This component:
    - Categorizes trip distance (short/medium/long)
    - Detects vehicle type and EV status
    - Analyzes multiple routes to find best option
    - Calculates emission metrics in both grams and kilograms
    
    Requirements:
        - 1.1: Analyzes distance, vehicle type, fuel type, and emission
        - 1.2: Generates summary with distance and emission
        - 1.3: Presents emission in both g and kg
        - 1.4: Analyzes multiple routes and identifies lowest emission
        - 6.1, 6.2, 6.3: Distance categorization for appropriate recommendations
    """
    
    def analyze_trip(self, trip_data: dict) -> TripAnalysis:
        """
        Analyze trip data and generate insights.
        
        Args:
            trip_data: Dictionary containing:
                - distance_km: float
                - car_type: str
                - fuel_type: str
                - emission_g: float
                - routes: list (optional, for multi-route analysis)
        
        Returns:
            TripAnalysis object containing:
                - total_distance: float
                - total_emission_g: float
                - total_emission_kg: float
                - vehicle_info: VehicleInfo
                - distance_category: str ('short', 'medium', 'long')
                - best_route_index: int (-1 if single route)
                - current_route_index: int (-1 if single route)
        
        Requirements:
            - 1.1: Processes all input fields (distance, vehicle, fuel, emission)
            - 1.2: Calculates total distance and emission
            - 1.3: Converts emission to both g and kg
            - 1.4: Identifies route with lowest emission
            - 6.1: Categorizes distance < 5km as 'short'
            - 6.2: Categorizes distance 5-15km as 'medium'
            - 6.3: Categorizes distance > 15km as 'long'
        """
        # Extract basic trip information
        distance_km = float(trip_data['distance_km'])
        car_type = trip_data['car_type']
        fuel_type = trip_data['fuel_type']
        emission_g = float(trip_data['emission_g'])
        
        # Get emission factor for vehicle-fuel combination
        emission_factor = get_emission_factor(car_type, fuel_type)
        
        # Determine if vehicle is EV
        is_ev = (car_type == 'EV' and fuel_type == 'listrik')
        
        # Create vehicle info
        vehicle_info = VehicleInfo(
            car_type=car_type,
            fuel_type=fuel_type,
            emission_factor=emission_factor,
            is_ev=is_ev
        )
        
        # Categorize distance
        # Requirements 6.1, 6.2, 6.3: Distance-based categorization
        if distance_km < 5.0:
            distance_category = 'short'
        elif distance_km <= 15.0:
            distance_category = 'medium'
        else:
            distance_category = 'long'
        
        # Convert emission to kg
        emission_kg = emission_g / 1000.0
        
        # Analyze routes if multiple routes provided
        best_route_index = -1
        current_route_index = -1
        
        if 'routes' in trip_data and trip_data['routes'] is not None and len(trip_data['routes']) > 0:
            routes = trip_data['routes']
            
            # Find route with minimum emission
            min_emission = float('inf')
            min_index = 0
            
            for idx, route in enumerate(routes):
                route_emission = float(route['emission_g'])
                if route_emission < min_emission:
                    min_emission = route_emission
                    min_index = idx
            
            best_route_index = min_index
            
            # Assume current route is the first one (or could be passed in trip_data)
            # For now, we'll use index 0 as current route
            current_route_index = 0
        
        # Create and return analysis
        return TripAnalysis(
            total_distance=distance_km,
            total_emission_g=emission_g,
            total_emission_kg=emission_kg,
            vehicle_info=vehicle_info,
            distance_category=distance_category,
            best_route_index=best_route_index,
            current_route_index=current_route_index
        )


# ============================================================================
# SavingsCalculator Component
# ============================================================================

class SavingsCalculator:
    """
    Calculates emission savings for different types of recommendations.
    
    This component:
    - Calculates vehicle switch savings using EMISSION_FACTORS
    - Calculates route change savings from emission differences
    - Calculates mode shift savings (to zero emission alternatives)
    - Computes percentage reduction for all savings
    - Ensures consistency with emission.py EMISSION_FACTORS
    
    Requirements:
        - 3.1: Calculates estimated emission savings in grams of CO2
        - 3.2: Presents values in both grams and kilograms
        - 3.3: Uses emission factors from existing emission calculation system
        - 3.4: Uses difference between route emissions
        - 3.5: Displays percentage reduction alongside absolute savings
        - 4.4: Uses existing EMISSION_FACTORS for consistency
    """
    
    def calculate_savings(self, recommendation_type: str, current_trip: dict, 
                         target_vehicle: Optional[str] = None,
                         target_fuel: Optional[str] = None,
                         target_route_emission: Optional[float] = None,
                         reduction_factor: Optional[float] = None) -> EmissionSavings:
        """
        Calculate emission savings for a recommendation.
        
        Args:
            recommendation_type: Type of recommendation ('vehicle_switch', 'route_change', 'mode_shift', 'efficiency')
            current_trip: Dictionary with current trip data (distance_km, car_type, fuel_type, emission_g)
            target_vehicle: Target vehicle type for vehicle_switch (optional)
            target_fuel: Target fuel type for vehicle_switch (optional)
            target_route_emission: Target route emission for route_change (optional)
            reduction_factor: Reduction factor for efficiency improvements (optional, 0.0-1.0)
        
        Returns:
            EmissionSavings object with savings_g, savings_kg, and savings_percentage
        
        Requirements:
            - 3.1: Returns savings in grams of CO2
            - 3.2: Returns savings in both grams and kilograms
            - 3.3: Uses EMISSION_FACTORS for vehicle switch calculations
            - 3.4: Uses emission difference for route calculations
            - 3.5: Calculates percentage reduction
        """
        distance_km = float(current_trip['distance_km'])
        current_emission_g = float(current_trip['emission_g'])
        
        savings_g = 0.0
        
        if recommendation_type == 'vehicle_switch':
            # Calculate savings from switching vehicles (Requirement 3.3)
            # Use EMISSION_FACTORS to ensure consistency with emission.py
            if target_vehicle is None or target_fuel is None:
                raise ValueError("target_vehicle and target_fuel required for vehicle_switch")
            
            # Get current emission factor
            current_emission_factor = get_emission_factor(
                current_trip['car_type'], 
                current_trip['fuel_type']
            )
            
            # Get target emission factor
            target_emission_factor = get_emission_factor(target_vehicle, target_fuel)
            
            # Calculate savings: (current_factor - target_factor) * distance
            savings_g = (current_emission_factor - target_emission_factor) * distance_km
            
        elif recommendation_type == 'route_change':
            # Calculate savings from route change (Requirement 3.4)
            # Use difference between current route emission and recommended route emission
            if target_route_emission is None:
                raise ValueError("target_route_emission required for route_change")
            
            savings_g = current_emission_g - target_route_emission
            
        elif recommendation_type == 'mode_shift':
            # Calculate savings from mode shift to zero-emission alternative
            # Assumes complete elimination of emissions (walking, cycling, etc.)
            savings_g = current_emission_g
            
        elif recommendation_type == 'efficiency':
            # Calculate savings from efficiency improvements
            # Uses reduction_factor (e.g., 0.15 for 15% improvement)
            if reduction_factor is None:
                reduction_factor = 0.15  # Default 15% improvement
            
            savings_g = current_emission_g * reduction_factor
            
        else:
            raise ValueError(f"Unknown recommendation type: {recommendation_type}")
        
        # Ensure savings are non-negative
        savings_g = max(0.0, savings_g)
        
        # Convert to kilograms (Requirement 3.2)
        savings_kg = savings_g / 1000.0
        
        # Calculate percentage reduction (Requirement 3.5)
        if current_emission_g > 0:
            savings_percentage = (savings_g / current_emission_g) * 100.0
        else:
            savings_percentage = 0.0
        
        return EmissionSavings(
            savings_g=savings_g,
            savings_kg=savings_kg,
            savings_percentage=savings_percentage
        )


# ============================================================================
# RecommendationEngine Component
# ============================================================================

class RecommendationEngine:
    """
    Generates personalized recommendations based on trip analysis.
    
    This component:
    - Generates 2-3 actionable recommendations
    - Adapts recommendations based on distance category
    - Prioritizes by potential emission savings
    - Considers vehicle type (EV vs fossil fuel)
    
    Requirements:
        - 2.1: Provides 2-3 actionable suggestions
        - 2.2: Recommends EV for non-EV vehicles
        - 2.3: Recommends best route when multiple available
        - 2.4: Recommends alternative transport for suitable distances
        - 6.1: Walking/cycling for short trips (<5km)
        - 6.2: Public transport for medium trips (5-15km)
        - 6.3: Vehicle efficiency for long trips (>15km)
    """
    
    def __init__(self):
        """Initialize RecommendationEngine with SavingsCalculator."""
        self.savings_calculator = SavingsCalculator()
    
    def generate_recommendations(self, analysis: TripAnalysis, routes: Optional[List[RouteData]] = None) -> List[Recommendation]:
        """
        Generate 2-3 personalized recommendations based on trip analysis.
        
        This method implements a priority-based recommendation strategy:
        1. Route optimization (if multiple routes available and not using best)
        2. Distance-appropriate alternatives (walking/cycling/public transport)
        3. Vehicle upgrade to EV (for non-EV vehicles)
        4. Eco-driving efficiency tips (always applicable)
        
        The final output is limited to top 3 recommendations by priority.
        
        Args:
            analysis: TripAnalysis object with trip insights
            routes: Optional list of route data for multi-route recommendations
        
        Returns:
            List of 2-3 Recommendation objects, sorted by priority
        
        Recommendation Logic:
            Short trips (<5km):
                - Priority: Walking/Cycling > EV switch > Eco-driving
                - Rationale: Active mobility is practical and eliminates emissions
            
            Medium trips (5-15km):
                - Priority: Public transport > EV switch > Eco-driving
                - Rationale: Public transport significantly reduces per-capita emissions
            
            Long trips (>15km):
                - Priority: EV switch > Route optimization > Eco-driving
                - Rationale: Vehicle efficiency matters most for long distances
            
            Multi-route scenarios:
                - Route optimization becomes highest priority if not using best route
                - Provides immediate, actionable savings without behavior change
        """
        recommendations = []
        
        # Prepare current trip data for savings calculations
        current_trip = {
            'distance_km': analysis.total_distance,
            'car_type': analysis.vehicle_info.car_type,
            'fuel_type': analysis.vehicle_info.fuel_type,
            'emission_g': analysis.total_emission_g
        }
        
        # ====================================================================
        # RECOMMENDATION STRATEGY 1: Route Optimization
        # ====================================================================
        # Route-based recommendation (Requirements 2.3, 8.2)
        # This should be checked FIRST and given highest priority if applicable
        # Rationale: Route changes provide immediate savings without requiring
        # behavior change or vehicle purchase. If user has multiple routes
        # available and isn't using the most efficient one, this is the
        # quickest win.
        if routes is not None and len(routes) > 1 and analysis.best_route_index != -1:
            # Check if current route is not the best route
            current_route_index = analysis.current_route_index if analysis.current_route_index != -1 else 0
            
            if current_route_index != analysis.best_route_index:
                current_emission = routes[current_route_index]['emission_g']
                best_emission = routes[analysis.best_route_index]['emission_g']
                
                # Only recommend if there's meaningful savings (> 1g difference)
                # Small differences (<1g) are negligible and not worth mentioning
                if current_emission - best_emission > 1.0:
                    # Use SavingsCalculator for route change
                    savings = self.savings_calculator.calculate_savings(
                        recommendation_type='route_change',
                        current_trip=current_trip,
                        target_route_emission=best_emission
                    )
                    
                    recommendations.append(Recommendation(
                        title=f"Pilih Rute Alternatif #{analysis.best_route_index + 1}",
                        description=f"Rute alternatif #{analysis.best_route_index + 1} memiliki emisi lebih rendah "
                                   f"({best_emission:.0f}g vs {current_emission:.0f}g). "
                                   f"Dengan memilih rute ini, Anda dapat mengurangi emisi perjalanan.",
                        type='route_change',
                        priority=1,
                        savings=savings
                    ))
        
        # ====================================================================
        # RECOMMENDATION STRATEGY 2: Distance-Appropriate Alternatives
        # ====================================================================
        # Distance-based recommendations (Requirements 6.1, 6.2, 6.3)
        # The type of alternative recommended depends on trip distance:
        # - Short (<5km): Active mobility (walking/cycling) is practical
        # - Medium (5-15km): Public transport is efficient
        # - Long (>15km): Focus on vehicle efficiency rather than mode shift
        
        if analysis.distance_category == 'short':
            # Short trips: recommend walking or cycling
            # Rationale: Distances under 5km are practical for active mobility
            # Benefits: 100% emission reduction + health benefits
            savings = self.savings_calculator.calculate_savings(
                recommendation_type='mode_shift',
                current_trip=current_trip
            )
            
            recommendations.append(Recommendation(
                title="Pertimbangkan Berjalan Kaki atau Bersepeda",
                description=f"Untuk jarak {analysis.total_distance:.1f} km, berjalan kaki atau bersepeda adalah pilihan yang sangat baik. "
                           f"Ini akan mengurangi emisi hingga 100% dan memberikan manfaat kesehatan.",
                type='mode_shift',
                priority=2,
                savings=savings
            ))
        
        elif analysis.distance_category == 'medium':
            # Medium trips: recommend public transportation
            # Rationale: 5-15km is too far for walking but perfect for public transport
            # Assumption: Public transport reduces per-capita emissions by ~70%
            savings = self.savings_calculator.calculate_savings(
                recommendation_type='efficiency',
                current_trip=current_trip,
                reduction_factor=0.7
            )
            
            recommendations.append(Recommendation(
                title="Gunakan Transportasi Umum",
                description=f"Untuk jarak {analysis.total_distance:.1f} km, transportasi umum seperti bus atau kereta "
                           f"dapat mengurangi emisi secara signifikan dibandingkan kendaraan pribadi.",
                type='mode_shift',
                priority=2,
                savings=savings
            ))
        
        else:  # long distance
            # Long trips: focus on vehicle efficiency
            # Rationale: >15km makes mode shift impractical, focus on vehicle choice
            if not analysis.vehicle_info.is_ev:
                # For fossil fuel vehicles: recommend EV switch
                # This is the most impactful change for long-distance drivers
                savings = self.savings_calculator.calculate_savings(
                    recommendation_type='vehicle_switch',
                    current_trip=current_trip,
                    target_vehicle='EV',
                    target_fuel='listrik'
                )
                
                recommendations.append(Recommendation(
                    title="Pertimbangkan Kendaraan Listrik (EV)",
                    description=f"Untuk perjalanan jarak jauh {analysis.total_distance:.1f} km, kendaraan listrik "
                               f"dapat mengurangi emisi secara drastis dan lebih hemat dalam jangka panjang.",
                    type='vehicle_switch',
                    priority=2,
                    savings=savings
                ))
            else:
                # For EV users: recommend efficiency optimization
                # Since they're already using clean energy, focus on maximizing efficiency
                savings = self.savings_calculator.calculate_savings(
                    recommendation_type='efficiency',
                    current_trip=current_trip,
                    reduction_factor=0.15
                )
                
                recommendations.append(Recommendation(
                    title="Optimasi Rute Perjalanan",
                    description=f"Untuk perjalanan jarak jauh {analysis.total_distance:.1f} km dengan EV, "
                               f"optimalkan rute untuk efisiensi energi maksimal.",
                    type='efficiency',
                    priority=2,
                    savings=savings
                ))
        
        # ====================================================================
        # RECOMMENDATION STRATEGY 3: Vehicle Upgrade to EV
        # ====================================================================
        # EV recommendation for non-EV vehicles (Requirements 2.2, 7.3)
        # This applies to ALL non-EV vehicles, regardless of distance
        # Rationale: Switching to EV is one of the most impactful long-term
        # changes a driver can make. This recommendation is always included
        # for fossil fuel vehicles, even if it's not the top priority.
        if not analysis.vehicle_info.is_ev:
            # Calculate EV savings using SavingsCalculator
            # This uses actual emission factors from EMISSION_FACTORS for accuracy
            savings = self.savings_calculator.calculate_savings(
                recommendation_type='vehicle_switch',
                current_trip=current_trip,
                target_vehicle='EV',
                target_fuel='listrik'
            )
            
            recommendations.append(Recommendation(
                title="Beralih ke Kendaraan Listrik",
                description=f"Mengganti {analysis.vehicle_info.car_type} dengan kendaraan listrik dapat "
                           f"mengurangi emisi hingga {savings.savings_percentage:.0f}% untuk perjalanan serupa.",
                type='vehicle_switch',
                priority=3,
                savings=savings
            ))
        
        # ====================================================================
        # RECOMMENDATION STRATEGY 4: Eco-Driving Efficiency
        # ====================================================================
        # Eco-driving tips (always applicable)
        # Rationale: Regardless of vehicle type or distance, driving behavior
        # affects fuel/energy consumption. This is a low-cost, immediate action.
        # Assumption: Eco-driving can reduce consumption by ~15% based on studies
        savings = self.savings_calculator.calculate_savings(
            recommendation_type='efficiency',
            current_trip=current_trip,
            reduction_factor=0.15
        )
        
        recommendations.append(Recommendation(
            title="Terapkan Eco-Driving",
            description="Mengemudi dengan efisien (kecepatan stabil, hindari akselerasi mendadak) "
                       "dapat mengurangi konsumsi bahan bakar hingga 15%.",
            type='efficiency',
            priority=4,
            savings=savings
        ))
        
        # ====================================================================
        # FINAL SELECTION: Return top 2-3 recommendations
        # ====================================================================
        # Sort by priority (lower number = higher priority) and return top 3
        # This ensures we always provide 2-3 recommendations as per Requirement 2.1
        recommendations.sort(key=lambda r: r.priority)
        return recommendations[:3]


# ============================================================================
# Output Formatter
# ============================================================================

def format_advice_output(analysis: TripAnalysis, recommendations: List[Recommendation]) -> str:
    """
    Format the advice output in a clear, readable format.
    
    Args:
        analysis: TripAnalysis object
        recommendations: List of Recommendation objects
    
    Returns:
        Formatted string with summary, recommendations, and savings
    
    Requirements:
        - 5.1: Clear sections for summary, recommendations, and savings
        - 5.2: Sequential numbering of recommendations
        - 5.3: Consistent units and formatting
        - 5.4: Indonesian language
        - 5.5: Visual separators between sections
    """
    output = []
    
    # Header with visual separator (Requirement 5.5)
    output.append("═" * 63)
    output.append("           REKOMENDASI PENGURANGAN EMISI KARBON")
    output.append("═" * 63)
    output.append("")
    
    # Summary section (Requirements 1.2, 1.3, 5.1)
    output.append("📊 RINGKASAN PERJALANAN")
    output.append("─" * 63)
    output.append(f"Jarak Tempuh    : {analysis.total_distance:.1f} km")
    output.append(f"Jenis Kendaraan : {analysis.vehicle_info.car_type} ({analysis.vehicle_info.fuel_type})")
    output.append(f"Total Emisi     : {analysis.total_emission_g:,.0f} g CO2 ({analysis.total_emission_kg:.2f} kg CO2)")
    output.append("")
    
    # Recommendations section (Requirements 2.1, 5.1, 5.2)
    output.append("💡 REKOMENDASI PENGURANGAN EMISI")
    output.append("─" * 63)
    output.append("")
    
    # Number recommendations sequentially (Requirement 5.2)
    for idx, rec in enumerate(recommendations, 1):
        output.append(f"{idx}. {rec.title}")
        output.append(f"   {rec.description}")
        output.append(f"   💰 Penghematan: {rec.savings.savings_g:,.0f} g CO2 "
                     f"({rec.savings.savings_kg:.2f} kg) - {rec.savings.savings_percentage:.0f}%")
        output.append("")
    
    # Footer with total savings
    total_savings_g = sum(r.savings.savings_g for r in recommendations)
    total_savings_kg = total_savings_g / 1000.0
    output.append("═" * 63)
    output.append(f"🌱 Total Potensi Penghematan: {total_savings_g:,.0f} g CO2 ({total_savings_kg:.2f} kg)")
    output.append("═" * 63)
    
    return "\n".join(output)


# ============================================================================
# Main Entry Point
# ============================================================================

def get_emission_advice(trip_data: dict) -> str:
    """
    Main entry point for emission reduction advice.
    
    Coordinates all components to analyze trip data and generate
    personalized recommendations with emission savings.
    
    Args:
        trip_data: Dictionary containing trip information with keys:
            - distance_km: float
            - car_type: str
            - fuel_type: str
            - emission_g: float
            - routes: list (optional)
    
    Returns:
        Formatted string with summary, recommendations, and savings
        Or error message if validation fails
    
    Requirements:
        - 4.1: Separate module implementation
        - 4.2: Accepts trip data without modifying original
        - 4.5: Optional invocation without breaking workflows
    """
    # Validate input (Requirements 7.4, 7.5)
    validation_error = validate_trip_data(trip_data)
    if validation_error:
        return f"Error: {validation_error['error']}"
    
    try:
        # Analyze trip (Requirement 1.1)
        analyzer = TripAnalyzer()
        analysis = analyzer.analyze_trip(trip_data)
        
        # Extract routes if available
        routes = trip_data.get('routes', None)
        
        # Generate recommendations (Requirement 2.1)
        engine = RecommendationEngine()
        recommendations = engine.generate_recommendations(analysis, routes)
        
        # Format output (Requirement 5.1)
        output = format_advice_output(analysis, recommendations)
        
        return output
    
    except Exception as e:
        # Graceful error handling (Requirement 7.5)
        return f"Error: An unexpected error occurred while generating advice: {str(e)}"
