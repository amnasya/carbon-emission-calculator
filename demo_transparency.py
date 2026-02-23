#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Demo script for ML model transparency features.

This script demonstrates the transparency features of the MLR Emission Predictor:
1. Model coefficients retrieval
2. Feature importance calculation
3. Prediction explanations
"""

from mlr_emission_predictor import MLREmissionPredictor


def demo_transparency_features():
    """Demonstrate model transparency features."""
    
    print("=" * 70)
    print("ML Emission Predictor - Transparency Features Demo")
    print("=" * 70)
    print()
    
    try:
        # Initialize predictor
        print("Loading ML model...")
        predictor = MLREmissionPredictor()
        print("✓ Model loaded successfully")
        print()
        
        # 1. Show model coefficients
        print("-" * 70)
        print("1. MODEL COEFFICIENTS")
        print("-" * 70)
        coefficients = predictor.get_model_coefficients()
        
        print(f"Intercept (β₀): {coefficients['intercept']:.4f}")
        print("\nFeature Coefficients:")
        for name, value in coefficients['coefficients'].items():
            print(f"  {name:30s}: {value:10.4f}")
        print()
        
        # 2. Show feature importance
        print("-" * 70)
        print("2. FEATURE IMPORTANCE")
        print("-" * 70)
        importance = predictor.get_feature_importance()
        
        print("Features ranked by importance:")
        for i, (name, value) in enumerate(importance.items(), 1):
            percentage = value * 100
            bar = "█" * int(percentage / 2)
            print(f"{i:2d}. {name:30s}: {percentage:5.2f}% {bar}")
        print()
        
        # 3. Demonstrate prediction explanation
        print("-" * 70)
        print("3. PREDICTION EXPLANATION")
        print("-" * 70)
        
        # Example 1: Short urban trip with LCGC
        print("\nExample 1: Short urban trip")
        print("-" * 40)
        explanation1 = predictor.explain_prediction(
            distance_km=10.0,
            fuel_type='Bensin',
            vehicle_type='LCGC',
            fuel_consumption_kml=18.0,
            avg_speed_kmh=40.0
        )
        print(explanation1['explanation_text'])
        print()
        
        # Example 2: Long highway trip with SUV
        print("\nExample 2: Long highway trip")
        print("-" * 40)
        explanation2 = predictor.explain_prediction(
            distance_km=200.0,
            fuel_type='Diesel',
            vehicle_type='SUV',
            fuel_consumption_kml=12.0,
            avg_speed_kmh=100.0
        )
        print(explanation2['explanation_text'])
        print()
        
        # Example 3: Electric vehicle
        print("\nExample 3: Electric vehicle")
        print("-" * 40)
        explanation3 = predictor.explain_prediction(
            distance_km=50.0,
            fuel_type='Listrik',
            vehicle_type='EV',
            fuel_consumption_kml=100.0,
            avg_speed_kmh=60.0
        )
        print(explanation3['explanation_text'])
        print()
        
        # 4. Show detailed contribution breakdown for one example
        print("-" * 70)
        print("4. DETAILED CONTRIBUTION BREAKDOWN")
        print("-" * 70)
        print("\nFor Example 1 (10km urban trip with LCGC):")
        print("\nAll feature contributions:")
        for name, contribution in explanation1['contributions'].items():
            print(f"  {name:30s}: {contribution:10.2f}g")
        
        total = sum(explanation1['contributions'].values())
        print(f"\n  {'Total (sum of contributions)':30s}: {total:10.2f}g")
        print(f"  {'Final prediction':30s}: {explanation1['prediction']:10.2f}g")
        print()
        
        print("=" * 70)
        print("Demo completed successfully!")
        print("=" * 70)
        
    except FileNotFoundError as e:
        print(f"❌ Error: Model files not found")
        print(f"   {e}")
        print("\nPlease train the model first using: python train_mlr_model.py")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    demo_transparency_features()
