#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for emission display formatting
Tests gram to kilogram conversion and ML indicator display
Requirements: 1.2, 1.3, 1.5
"""

import pytest
from emission_formatter import EmissionFormatter


class TestEmissionFormatting:
    """Test basic emission formatting with unit conversion"""
    
    def test_format_emission_below_1000g(self):
        """Test formatting for emissions below 1000g - should show only grams"""
        # Test small value
        result = EmissionFormatter.format_emission(500)
        assert "500 g" in result
        assert "kg" not in result
        
        # Test value just below threshold
        result = EmissionFormatter.format_emission(999)
        assert "999 g" in result
        assert "kg" not in result
    
    def test_format_emission_above_1000g_both_units(self):
        """Test formatting for emissions above 1000g - should show both g and kg"""
        # Test value just above threshold
        result = EmissionFormatter.format_emission(1001, show_both_units=True)
        assert "1,001 g" in result
        assert "1.00 kg" in result
        
        # Test larger value
        result = EmissionFormatter.format_emission(5432, show_both_units=True)
        assert "5,432 g" in result
        assert "5.43 kg" in result
    
    def test_format_emission_above_1000g_kg_only(self):
        """Test formatting for emissions above 1000g with kg only"""
        result = EmissionFormatter.format_emission(2500, show_both_units=False)
        assert "2.50 kg" in result
        assert "2,500 g" not in result
    
    def test_format_emission_at_1000g_boundary(self):
        """Test formatting at exactly 1000g boundary"""
        result = EmissionFormatter.format_emission(1000, show_both_units=True)
        # At 1000g, should not trigger kg conversion (> 1000, not >=)
        assert "1,000 g" in result
        assert "kg" not in result
    
    def test_format_emission_precision(self):
        """Test decimal precision for kg values"""
        # Default precision (2 decimals)
        result = EmissionFormatter.format_emission(1234.567, precision=2)
        assert "1.23 kg" in result
        
        # Higher precision
        result = EmissionFormatter.format_emission(1234.567, precision=3)
        assert "1.235 kg" in result
        
        # Lower precision
        result = EmissionFormatter.format_emission(1234.567, precision=1)
        assert "1.2 kg" in result
    
    def test_format_emission_zero(self):
        """Test formatting for zero emission"""
        result = EmissionFormatter.format_emission(0)
        assert "0 g" in result
    
    def test_format_emission_large_value(self):
        """Test formatting for very large emission values"""
        result = EmissionFormatter.format_emission(123456, show_both_units=True)
        assert "123,456 g" in result
        assert "123.46 kg" in result


class TestMLIndicatorDisplay:
    """Test ML indicator display in formatted emissions"""
    
    def test_ml_indicator_for_ml_prediction(self):
        """Test ML indicator is added for ML predictions"""
        result = EmissionFormatter.format_emission_with_ml_indicator(
            1500, "ML", show_both_units=True
        )
        assert "[AI/ML]" in result
        assert "1,500 g" in result
        assert "1.50 kg" in result
    
    def test_ml_indicator_for_static_prediction(self):
        """Test indicator for static predictions"""
        result = EmissionFormatter.format_emission_with_ml_indicator(
            800, "Static", show_both_units=True
        )
        assert "[Static]" in result
        assert "800 g" in result
    
    def test_ml_indicator_case_insensitive(self):
        """Test ML indicator works with different cases"""
        # Lowercase
        result = EmissionFormatter.format_emission_with_ml_indicator(
            1200, "ml", show_both_units=True
        )
        assert "[AI/ML]" in result
        
        # Mixed case
        result = EmissionFormatter.format_emission_with_ml_indicator(
            1200, "Ml", show_both_units=True
        )
        assert "[AI/ML]" in result
    
    def test_ml_indicator_for_fallback(self):
        """Test indicator for ML fallback scenarios"""
        result = EmissionFormatter.format_emission_with_ml_indicator(
            1500, "Static (ML fallback)", show_both_units=True
        )
        assert "[Static (ML fallback)]" in result
    
    def test_ml_indicator_with_different_methods(self):
        """Test indicator for various prediction methods"""
        methods = [
            "ML",
            "Static",
            "Static (Fallback)",
            "Random Forest",
            "Linear Regression"
        ]
        
        for method in methods:
            result = EmissionFormatter.format_emission_with_ml_indicator(
                1000, method, show_both_units=False
            )
            # Should contain some indicator
            assert "[" in result and "]" in result


class TestRouteEmissionFormatting:
    """Test formatting for individual route emissions"""
    
    def test_format_route_emission_basic(self):
        """Test basic route emission formatting"""
        route_data = {
            'predicted_emission_g': 1234,
            'prediction_method': 'ML',
            'route_number': 1
        }
        
        result = EmissionFormatter.format_route_emission(route_data)
        assert "1,234 g" in result
        assert "1.23 kg" in result
        assert "[AI/ML]" in result
    
    def test_format_route_emission_without_ml_indicator(self):
        """Test route formatting without ML indicator"""
        route_data = {
            'predicted_emission_g': 567,
            'prediction_method': 'Static'
        }
        
        result = EmissionFormatter.format_route_emission(
            route_data, include_ml_indicator=False
        )
        assert "567 g" in result
        assert "[" not in result
    
    def test_format_route_emission_alternative_key(self):
        """Test route formatting with alternative emission key"""
        route_data = {
            'emission_g': 2500,  # Alternative key name
            'prediction_method': 'ML'
        }
        
        result = EmissionFormatter.format_route_emission(route_data)
        assert "2,500 g" in result
        assert "2.50 kg" in result
    
    def test_format_route_emission_missing_method(self):
        """Test route formatting when prediction method is missing"""
        route_data = {
            'predicted_emission_g': 1000
        }
        
        result = EmissionFormatter.format_route_emission(route_data)
        assert "1,000 g" in result
        assert "[Unknown]" in result


class TestAllRoutesFormatting:
    """Test formatting for multiple routes with comparison"""
    
    def test_format_all_routes_single_route(self):
        """Test formatting with a single route"""
        routes = [
            {
                'route_number': 1,
                'predicted_emission_g': 1500,
                'prediction_method': 'ML',
                'distance_km': 10.5,
                'duration_min': 25
            }
        ]
        
        result = EmissionFormatter.format_all_routes(routes)
        assert "Route 1" in result
        assert "1,500 g" in result
        assert "1.50 kg" in result
        assert "RECOMMENDED" in result
        assert "Distance: 10.50 km" in result
        assert "Duration: 25 minutes" in result
    
    def test_format_all_routes_multiple_routes(self):
        """Test formatting with multiple routes"""
        routes = [
            {
                'route_number': 2,
                'predicted_emission_g': 1200,
                'prediction_method': 'ML',
                'distance_km': 9.0,
                'duration_min': 20
            },
            {
                'route_number': 1,
                'predicted_emission_g': 1500,
                'prediction_method': 'ML',
                'distance_km': 10.5,
                'duration_min': 25
            },
            {
                'route_number': 3,
                'predicted_emission_g': 1800,
                'prediction_method': 'ML',
                'distance_km': 12.0,
                'duration_min': 30
            }
        ]
        
        result = EmissionFormatter.format_all_routes(routes)
        
        # Check all routes are present
        assert "Route 1" in result
        assert "Route 2" in result
        assert "Route 3" in result
        
        # Check best route is highlighted
        assert ">>>" in result
        assert "RECOMMENDED" in result
        
        # Check savings calculation (vs worst route: 1800 - 1200 = 600)
        assert "Savings:" in result
        assert "600 g" in result  # 1800 - 1200
    
    def test_format_all_routes_no_highlight(self):
        """Test formatting without highlighting best route"""
        routes = [
            {'route_number': 1, 'predicted_emission_g': 1000, 'prediction_method': 'ML'},
            {'route_number': 2, 'predicted_emission_g': 1200, 'prediction_method': 'ML'}
        ]
        
        result = EmissionFormatter.format_all_routes(routes, highlight_best=False)
        assert "RECOMMENDED" not in result
        assert ">>>" not in result
    
    def test_format_all_routes_empty_list(self):
        """Test formatting with empty routes list"""
        result = EmissionFormatter.format_all_routes([])
        assert "No routes available" in result
    
    def test_format_all_routes_without_ml_indicator(self):
        """Test formatting without ML indicators"""
        routes = [
            {'route_number': 1, 'predicted_emission_g': 1000, 'prediction_method': 'ML'}
        ]
        
        result = EmissionFormatter.format_all_routes(routes, include_ml_indicator=False)
        assert "[AI/ML]" not in result
        assert "1,000 g" in result


class TestComparisonSummary:
    """Test comparison summary formatting"""
    
    def test_format_comparison_summary_with_alternatives(self):
        """Test comparison summary with alternative routes"""
        best_route = {
            'route_number': 1,
            'predicted_emission_g': 1000
        }
        
        alternative_routes = [
            {'route_number': 2, 'predicted_emission_g': 1200},
            {'route_number': 3, 'predicted_emission_g': 1500}
        ]
        
        result = EmissionFormatter.format_comparison_summary(
            best_route, alternative_routes
        )
        
        assert "Best Route: Route 1" in result
        assert "1,000 g" in result
        assert "Route 2" in result
        assert "1,200 g" in result
        assert "+200 g" in result
        assert "+20.0%" in result
        assert "Route 3" in result
        assert "+500 g" in result
        assert "+50.0%" in result
    
    def test_format_comparison_summary_no_alternatives(self):
        """Test comparison summary with no alternative routes"""
        best_route = {
            'route_number': 1,
            'predicted_emission_g': 1000
        }
        
        result = EmissionFormatter.format_comparison_summary(best_route, [])
        
        assert "Best Route: Route 1" in result
        assert "1,000 g" in result
        assert "Alternative Routes:" not in result
    
    def test_format_comparison_summary_precision(self):
        """Test comparison summary with different precision"""
        best_route = {
            'route_number': 1,
            'predicted_emission_g': 1234.567
        }
        
        alternative_routes = [
            {'route_number': 2, 'predicted_emission_g': 2345.678}
        ]
        
        # Test with precision 3
        result = EmissionFormatter.format_comparison_summary(
            best_route, alternative_routes, precision=3
        )
        
        assert "1.235 kg" in result
        assert "2.346 kg" in result


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_format_emission_negative_value(self):
        """Test formatting with negative emission (should not happen but handle gracefully)"""
        # This shouldn't happen in practice, but test defensive behavior
        result = EmissionFormatter.format_emission(-100)
        # Should still format, even if value is invalid
        assert "-100 g" in result
    
    def test_format_emission_very_small_value(self):
        """Test formatting with very small emission values"""
        result = EmissionFormatter.format_emission(0.5)
        assert "0 g" in result or "1 g" in result  # Depends on rounding
    
    def test_format_route_emission_missing_emission(self):
        """Test route formatting when emission value is missing"""
        route_data = {
            'route_number': 1,
            'prediction_method': 'ML'
        }
        
        result = EmissionFormatter.format_route_emission(route_data)
        assert "0 g" in result  # Should default to 0
    
    def test_format_all_routes_missing_optional_fields(self):
        """Test formatting routes with missing optional fields"""
        routes = [
            {
                'predicted_emission_g': 1000,
                'prediction_method': 'ML'
                # Missing route_number, distance_km, duration_min
            }
        ]
        
        result = EmissionFormatter.format_all_routes(routes)
        # Should still work, using defaults
        assert "Route 1" in result  # Default route number
        assert "1,000 g" in result
