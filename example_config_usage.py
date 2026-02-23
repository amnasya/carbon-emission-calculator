#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example: Using MLR Configuration Management

This example demonstrates how to use the configuration system
with the MLR Emission Predictor.
"""

from mlr_config import get_config, MLRConfig
from mlr_emission_predictor import MLREmissionPredictor
import os


def example_basic_usage():
    """Example 1: Basic configuration usage."""
    print("=" * 70)
    print("Example 1: Basic Configuration Usage")
    print("=" * 70)
    
    # Get global configuration instance
    config = get_config()
    
    # Display current configuration
    print("\nCurrent Configuration:")
    print(f"  Model path: {config.get('model_path')}")
    print(f"  Scaler path: {config.get('scaler_path')}")
    print(f"  Encoder path: {config.get('encoder_path')}")
    print(f"  Fallback enabled: {config.is_fallback_enabled()}")
    print(f"  Fallback method: {config.get_fallback_method()}")
    
    # Get model paths
    paths = config.get_model_paths()
    print("\nModel Paths:")
    for key, path in paths.items():
        print(f"  {key}: {path}")
    
    # Get validation bounds
    bounds = config.get_validation_bounds()
    print("\nValidation Bounds:")
    for feature, (min_val, max_val) in bounds.items():
        print(f"  {feature}: {min_val} - {max_val}")


def example_environment_variables():
    """Example 2: Using environment variables."""
    print("\n" + "=" * 70)
    print("Example 2: Environment Variables")
    print("=" * 70)
    
    # Set environment variables
    os.environ['MLR_MODEL_PATH'] = '/custom/path/model.joblib'
    os.environ['MLR_FALLBACK_ENABLED'] = 'false'
    os.environ['MLR_LOG_LEVEL'] = 'DEBUG'
    
    # Force reload to pick up environment variables
    config = get_config(force_reload=True)
    
    print("\nConfiguration from Environment Variables:")
    print(f"  Model path: {config.get('model_path')}")
    print(f"  Fallback enabled: {config.is_fallback_enabled()}")
    print(f"  Log level: {config.get('log_level')}")
    
    # Clean up
    del os.environ['MLR_MODEL_PATH']
    del os.environ['MLR_FALLBACK_ENABLED']
    del os.environ['MLR_LOG_LEVEL']


def example_config_file():
    """Example 3: Using configuration file."""
    print("\n" + "=" * 70)
    print("Example 3: Configuration File")
    print("=" * 70)
    
    # Create a temporary config file
    import json
    import tempfile
    
    config_data = {
        'model_path': '/file/custom/model.joblib',
        'fallback_enabled': False,
        'fallback_method': 'simple',
        'min_distance_km': 0.5,
        'max_speed_kmh': 150.0
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        config_file = f.name
    
    try:
        # Load configuration from file
        config = MLRConfig(config_file=config_file)
        
        print(f"\nConfiguration from File: {config_file}")
        print(f"  Model path: {config.get('model_path')}")
        print(f"  Fallback enabled: {config.is_fallback_enabled()}")
        print(f"  Fallback method: {config.get_fallback_method()}")
        print(f"  Min distance: {config.get('min_distance_km')} km")
        print(f"  Max speed: {config.get('max_speed_kmh')} km/h")
        
    finally:
        # Clean up
        os.unlink(config_file)


def example_with_predictor():
    """Example 4: Using configuration with MLR Predictor."""
    print("\n" + "=" * 70)
    print("Example 4: Integration with MLR Predictor")
    print("=" * 70)
    
    # Get configuration
    config = get_config(force_reload=True)
    
    # Get model paths from configuration
    paths = config.get_model_paths()
    
    print("\nInitializing MLR Predictor with configured paths:")
    print(f"  Model: {paths['model_path']}")
    print(f"  Scaler: {paths['scaler_path']}")
    print(f"  Encoder: {paths['encoder_path']}")
    
    try:
        # Initialize predictor with configured paths
        predictor = MLREmissionPredictor(
            model_path=paths['model_path'],
            scaler_path=paths['scaler_path'],
            encoder_path=paths['encoder_path']
        )
        
        print("\n✓ Predictor initialized successfully")
        
        # Check fallback configuration
        fallback_config = config.get_fallback_config()
        print(f"\nFallback Configuration:")
        print(f"  Enabled: {fallback_config['fallback_enabled']}")
        print(f"  Method: {fallback_config['fallback_method']}")
        
        # Make a prediction
        emission = predictor.predict_emission(
            distance_km=50.0,
            fuel_type='Bensin',
            vehicle_type='LCGC',
            fuel_consumption_kml=18.0,
            avg_speed_kmh=60.0
        )
        
        print(f"\nSample Prediction:")
        print(f"  Distance: 50 km")
        print(f"  Vehicle: LCGC (Bensin)")
        print(f"  Predicted emission: {emission:.2f} grams CO₂")
        
    except FileNotFoundError as e:
        print(f"\n✗ Model files not found: {e}")
        print("\nNote: Train the model first using train_mlr_model.py")
        
        if config.is_fallback_enabled():
            print(f"\nFallback is enabled ({config.get_fallback_method()} method)")
            print("System would fall back to static calculation in production")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def example_runtime_modification():
    """Example 5: Modifying configuration at runtime."""
    print("\n" + "=" * 70)
    print("Example 5: Runtime Configuration Modification")
    print("=" * 70)
    
    config = get_config(force_reload=True)
    
    print("\nOriginal Configuration:")
    print(f"  Fallback enabled: {config.is_fallback_enabled()}")
    print(f"  Fallback method: {config.get_fallback_method()}")
    print(f"  Log level: {config.get('log_level')}")
    
    # Modify configuration at runtime
    config.set('fallback_enabled', False)
    config.set('fallback_method', 'simple')
    config.set('log_level', 'DEBUG')
    
    print("\nModified Configuration:")
    print(f"  Fallback enabled: {config.is_fallback_enabled()}")
    print(f"  Fallback method: {config.get_fallback_method()}")
    print(f"  Log level: {config.get('log_level')}")
    
    # Save to file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        save_path = f.name
    
    try:
        config.save_to_file(save_path)
        print(f"\n✓ Configuration saved to: {save_path}")
        
        # Verify saved file
        import json
        with open(save_path, 'r') as f:
            saved_config = json.load(f)
        
        print("\nSaved Configuration (sample):")
        print(f"  fallback_enabled: {saved_config['fallback_enabled']}")
        print(f"  fallback_method: {saved_config['fallback_method']}")
        print(f"  log_level: {saved_config['log_level']}")
        
    finally:
        os.unlink(save_path)


def example_fallback_scenarios():
    """Example 6: Fallback configuration scenarios."""
    print("\n" + "=" * 70)
    print("Example 6: Fallback Configuration Scenarios")
    print("=" * 70)
    
    scenarios = [
        {
            'name': 'Production (Fallback Enabled)',
            'config': {'fallback_enabled': True, 'fallback_method': 'static'},
            'description': 'Recommended for production - falls back to static calculation'
        },
        {
            'name': 'Strict ML Only',
            'config': {'fallback_enabled': False},
            'description': 'Requires ML predictions - fails if model unavailable'
        },
        {
            'name': 'Simple Fallback',
            'config': {'fallback_enabled': True, 'fallback_method': 'simple'},
            'description': 'Uses simplified calculation as fallback'
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        print(f"  Description: {scenario['description']}")
        print(f"  Configuration:")
        for key, value in scenario['config'].items():
            print(f"    {key}: {value}")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("MLR Configuration Management Examples")
    print("=" * 70)
    
    # Run examples
    example_basic_usage()
    example_environment_variables()
    example_config_file()
    example_with_predictor()
    example_runtime_modification()
    example_fallback_scenarios()
    
    print("\n" + "=" * 70)
    print("Examples Complete")
    print("=" * 70)
    print("\nFor more information, see MLR_CONFIG_GUIDE.md")
