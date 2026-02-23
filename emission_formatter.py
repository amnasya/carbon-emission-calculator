#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Emission Display Formatter
Format emission values for display with proper units and ML indicators
"""

from typing import Dict, List, Optional


class EmissionFormatter:
    """
    Format emission values for display with proper units and ML indicators.
    
    Handles:
    - Gram to kilogram conversion for values > 1000g
    - ML indicator display
    - Formatting for multiple routes
    """
    
    @staticmethod
    def format_emission(emission_g: float, 
                       show_both_units: bool = True,
                       precision: int = 2) -> str:
        """
        Format emission value with appropriate units.
        
        Args:
            emission_g: Emission value in grams
            show_both_units: If True and emission > 1000g, show both g and kg
            precision: Decimal precision for kg values
            
        Returns:
            Formatted emission string (e.g., "1,234 g (1.23 kg)" or "567 g")
        """
        if emission_g > 1000:
            emission_kg = emission_g / 1000.0
            if show_both_units:
                return f"{emission_g:,.0f} g ({emission_kg:.{precision}f} kg)"
            else:
                return f"{emission_kg:.{precision}f} kg"
        else:
            return f"{emission_g:,.0f} g"
    
    @staticmethod
    def format_emission_with_ml_indicator(emission_g: float,
                                         prediction_method: str,
                                         show_both_units: bool = True,
                                         precision: int = 2) -> str:
        """
        Format emission value with ML indicator.
        
        Args:
            emission_g: Emission value in grams
            prediction_method: Method used for prediction (e.g., "ML", "Static")
            show_both_units: If True and emission > 1000g, show both g and kg
            precision: Decimal precision for kg values
            
        Returns:
            Formatted emission string with ML indicator
            (e.g., "1,234 g (1.23 kg) [ML]" or "567 g [Static]")
        """
        emission_str = EmissionFormatter.format_emission(
            emission_g, show_both_units, precision
        )
        
        # Add ML indicator
        if prediction_method.upper() == "ML":
            indicator = "[AI/ML]"
        elif "ML" in prediction_method.upper():
            indicator = f"[{prediction_method}]"
        else:
            indicator = f"[{prediction_method}]"
        
        return f"{emission_str} {indicator}"
    
    @staticmethod
    def format_route_emission(route_data: Dict,
                             include_ml_indicator: bool = True,
                             show_both_units: bool = True,
                             precision: int = 2) -> str:
        """
        Format emission for a single route with all details.
        
        Args:
            route_data: Route dictionary with keys:
                - predicted_emission_g or emission_g: Emission in grams
                - prediction_method: Method used (optional)
                - route_number: Route identifier (optional)
                - distance_km: Distance in km (optional)
                - duration_min: Duration in minutes (optional)
            include_ml_indicator: Whether to include ML indicator
            show_both_units: If True and emission > 1000g, show both g and kg
            precision: Decimal precision for kg values
            
        Returns:
            Formatted route emission string
        """
        # Get emission value (support both key names)
        emission_g = route_data.get('predicted_emission_g', 
                                    route_data.get('emission_g', 0))
        
        # Get prediction method
        prediction_method = route_data.get('prediction_method', 'Unknown')
        
        # Format emission
        if include_ml_indicator:
            emission_str = EmissionFormatter.format_emission_with_ml_indicator(
                emission_g, prediction_method, show_both_units, precision
            )
        else:
            emission_str = EmissionFormatter.format_emission(
                emission_g, show_both_units, precision
            )
        
        return emission_str
    
    @staticmethod
    def format_all_routes(routes: List[Dict],
                         include_ml_indicator: bool = True,
                         show_both_units: bool = True,
                         precision: int = 2,
                         highlight_best: bool = True) -> str:
        """
        Format emissions for all routes with comparison.
        
        Args:
            routes: List of route dictionaries (should be sorted by emission)
            include_ml_indicator: Whether to include ML indicator
            show_both_units: If True and emission > 1000g, show both g and kg
            precision: Decimal precision for kg values
            highlight_best: Whether to highlight the best (lowest emission) route
            
        Returns:
            Formatted string with all routes and their emissions
        """
        if not routes:
            return "No routes available"
        
        lines = []
        lines.append("Route Emissions:")
        lines.append("-" * 70)
        
        for idx, route in enumerate(routes):
            is_best = idx == 0 and highlight_best
            
            # Get route number
            route_number = route.get('route_number', idx + 1)
            
            # Format emission
            emission_str = EmissionFormatter.format_route_emission(
                route, include_ml_indicator, show_both_units, precision
            )
            
            # Build route line
            prefix = ">>> " if is_best else "    "
            suffix = " (RECOMMENDED - LOWEST EMISSION)" if is_best else ""
            
            route_line = f"{prefix}Route {route_number}: {emission_str}{suffix}"
            lines.append(route_line)
            
            # Add distance and duration if available
            if 'distance_km' in route:
                lines.append(f"    Distance: {route['distance_km']:.2f} km")
            if 'duration_min' in route:
                lines.append(f"    Duration: {route['duration_min']:.0f} minutes")
            
            # Add savings information for best route
            if is_best and len(routes) > 1:
                worst_emission = routes[-1].get('predicted_emission_g',
                                               routes[-1].get('emission_g', 0))
                best_emission = route.get('predicted_emission_g',
                                         route.get('emission_g', 0))
                
                if worst_emission > 0:
                    savings_g = worst_emission - best_emission
                    savings_pct = (savings_g / worst_emission) * 100
                    savings_kg = savings_g / 1000.0
                    
                    lines.append(f"    Savings: {savings_g:,.0f} g ({savings_kg:.2f} kg) "
                               f"- {savings_pct:.1f}% lower than worst route")
            
            lines.append("")  # Empty line between routes
        
        return "\n".join(lines)
    
    @staticmethod
    def format_comparison_summary(best_route: Dict,
                                 alternative_routes: List[Dict],
                                 precision: int = 2) -> str:
        """
        Format a comparison summary between best and alternative routes.
        
        Args:
            best_route: Best route dictionary
            alternative_routes: List of alternative route dictionaries
            precision: Decimal precision for values
            
        Returns:
            Formatted comparison summary string
        """
        lines = []
        
        # Get best route emission
        best_emission_g = best_route.get('predicted_emission_g',
                                        best_route.get('emission_g', 0))
        best_route_num = best_route.get('route_number', 1)
        
        # Format best route
        best_emission_str = EmissionFormatter.format_emission(
            best_emission_g, show_both_units=True, precision=precision
        )
        
        lines.append(f"Best Route: Route {best_route_num}")
        lines.append(f"Emission: {best_emission_str}")
        
        if alternative_routes:
            lines.append("\nAlternative Routes:")
            
            for alt in alternative_routes:
                alt_route_num = alt.get('route_number', 0)
                alt_emission_g = alt.get('predicted_emission_g',
                                        alt.get('emission_g', 0))
                
                # Calculate difference
                diff_g = alt_emission_g - best_emission_g
                diff_pct = (diff_g / best_emission_g) * 100 if best_emission_g > 0 else 0
                
                alt_emission_str = EmissionFormatter.format_emission(
                    alt_emission_g, show_both_units=True, precision=precision
                )
                
                lines.append(f"  Route {alt_route_num}: {alt_emission_str} "
                           f"(+{diff_g:,.0f} g, +{diff_pct:.1f}%)")
        
        return "\n".join(lines)
