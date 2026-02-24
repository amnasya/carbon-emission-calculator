#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configuration Management for MLR Emission Predictor

This module provides configuration management with support for:
- Environment variables
- Configuration files (JSON)
- Default values
- Configurable fallback behavior
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class MLRConfig:
    """
    Configuration manager for MLR Emission Predictor.
    
    Supports configuration from:
    1. Environment variables (highest priority)
    2. Configuration file (medium priority)
    3. Default values (lowest priority)
    """
    
    # Default configuration values
    DEFAULT_CONFIG = {
        'model_path': 'mlr_emission_model.joblib',
        'scaler_path': 'mlr_emission_scaler.joblib',
        'encoder_path': 'mlr_emission_encoder.joblib',
        'feature_info_path': 'mlr_feature_info.joblib',
        'fallback_enabled': True,
        'fallback_method': 'static',  # 'static' or 'simple'
        'auto_reload': False,
        'reload_check_interval': 300,  # seconds
        'log_level': 'INFO',
        'validate_on_load': True,
        'min_distance_km': 0.1,
        'max_distance_km': 10000.0,
        'min_speed_kmh': 5.0,
        'max_speed_kmh': 200.0,
        'min_fuel_consumption': 1.0,
        'max_fuel_consumption': 200.0
    }
    
    # Environment variable prefix
    ENV_PREFIX = 'MLR_'
    
    # Environment variable mappings
    ENV_MAPPINGS = {
        'MLR_MODEL_PATH': 'model_path',
        'MLR_SCALER_PATH': 'scaler_path',
        'MLR_ENCODER_PATH': 'encoder_path',
        'MLR_FEATURE_INFO_PATH': 'feature_info_path',
        'MLR_FALLBACK_ENABLED': 'fallback_enabled',
        'MLR_FALLBACK_METHOD': 'fallback_method',
        'MLR_AUTO_RELOAD': 'auto_reload',
        'MLR_RELOAD_CHECK_INTERVAL': 'reload_check_interval',
        'MLR_LOG_LEVEL': 'log_level',
        'MLR_VALIDATE_ON_LOAD': 'validate_on_load',
        'MLR_MIN_DISTANCE_KM': 'min_distance_km',
        'MLR_MAX_DISTANCE_KM': 'max_distance_km',
        'MLR_MIN_SPEED_KMH': 'min_speed_kmh',
        'MLR_MAX_SPEED_KMH': 'max_speed_kmh',
        'MLR_MIN_FUEL_CONSUMPTION': 'min_fuel_consumption',
        'MLR_MAX_FUEL_CONSUMPTION': 'max_fuel_consumption'
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to JSON configuration file (optional)
        """
        self.config_file = config_file
        self.config = self.DEFAULT_CONFIG.copy()
        
        # Load configuration in priority order
        self._load_config_file()
        self._load_environment_variables()
        
        # Apply configuration
        self._apply_config()
    
    def _load_config_file(self):
        """Load configuration from JSON file if it exists."""
        if not self.config_file:
            # Try default config file locations
            default_locations = [
                'mlr_config.json',
                '.mlr_config.json',
                os.path.join(os.path.expanduser('~'), '.mlr_config.json')
            ]
            
            for location in default_locations:
                if os.path.exists(location):
                    self.config_file = location
                    break
        
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                
                # Validate and merge with defaults
                for key, value in file_config.items():
                    if key in self.DEFAULT_CONFIG:
                        self.config[key] = value
                    else:
                        logger.warning(f"Unknown configuration key in file: {key}")
                
                logger.info(f"Loaded configuration from file: {self.config_file}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse configuration file {self.config_file}: {e}")
            except Exception as e:
                logger.error(f"Failed to load configuration file {self.config_file}: {e}")
    
    def _load_environment_variables(self):
        """Load configuration from environment variables."""
        for env_var, config_key in self.ENV_MAPPINGS.items():
            value = os.getenv(env_var)
            
            if value is not None:
                # Convert value to appropriate type
                converted_value = self._convert_env_value(config_key, value)
                self.config[config_key] = converted_value
                logger.debug(f"Loaded {config_key} from environment: {env_var}")
    
    def _convert_env_value(self, key: str, value: str) -> Any:
        """
        Convert environment variable string to appropriate type.
        
        Args:
            key: Configuration key
            value: String value from environment
            
        Returns:
            Converted value with appropriate type
        """
        # Get expected type from default config
        default_value = self.DEFAULT_CONFIG.get(key)
        
        if default_value is None:
            return value
        
        # Convert based on type
        if isinstance(default_value, bool):
            return value.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(default_value, int):
            try:
                return int(value)
            except ValueError:
                logger.warning(f"Invalid integer value for {key}: {value}, using default")
                return default_value
        elif isinstance(default_value, float):
            try:
                return float(value)
            except ValueError:
                logger.warning(f"Invalid float value for {key}: {value}, using default")
                return default_value
        else:
            return value
    
    def _apply_config(self):
        """Apply configuration settings (e.g., logging level)."""
        # Set logging level
        log_level = self.config.get('log_level', 'INFO')
        try:
            numeric_level = getattr(logging, log_level.upper())
            logging.getLogger('mlr_emission_predictor').setLevel(numeric_level)
        except AttributeError:
            logger.warning(f"Invalid log level: {log_level}, using INFO")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.
        
        Returns:
            Dictionary of all configuration values
        """
        return self.config.copy()
    
    def set(self, key: str, value: Any):
        """
        Set configuration value at runtime.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        if key in self.DEFAULT_CONFIG:
            self.config[key] = value
            logger.debug(f"Set configuration {key} = {value}")
        else:
            logger.warning(f"Attempting to set unknown configuration key: {key}")
    
    def save_to_file(self, filepath: Optional[str] = None):
        """
        Save current configuration to JSON file.
        
        Args:
            filepath: Path to save configuration (uses self.config_file if not provided)
        """
        save_path = filepath or self.config_file or 'mlr_config.json'
        
        try:
            with open(save_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Saved configuration to {save_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration to {save_path}: {e}")
            raise
    
    def get_model_paths(self) -> Dict[str, str]:
        """
        Get all model file paths.
        
        Returns:
            Dictionary with model, scaler, encoder, and feature_info paths
        """
        return {
            'model_path': self.config['model_path'],
            'scaler_path': self.config['scaler_path'],
            'encoder_path': self.config['encoder_path'],
            'feature_info_path': self.config['feature_info_path']
        }
    
    def get_fallback_config(self) -> Dict[str, Any]:
        """
        Get fallback configuration.
        
        Returns:
            Dictionary with fallback_enabled and fallback_method
        """
        return {
            'fallback_enabled': self.config['fallback_enabled'],
            'fallback_method': self.config['fallback_method']
        }
    
    def get_validation_bounds(self) -> Dict[str, tuple]:
        """
        Get validation bounds for input features.
        
        Returns:
            Dictionary mapping feature names to (min, max) tuples
        """
        return {
            'distance_km': (
                self.config['min_distance_km'],
                self.config['max_distance_km']
            ),
            'avg_speed_kmh': (
                self.config['min_speed_kmh'],
                self.config['max_speed_kmh']
            ),
            'fuel_consumption_kml': (
                self.config['min_fuel_consumption'],
                self.config['max_fuel_consumption']
            )
        }
    
    def is_fallback_enabled(self) -> bool:
        """
        Check if fallback is enabled.
        
        Returns:
            True if fallback is enabled
        """
        return self.config['fallback_enabled']
    
    def get_fallback_method(self) -> str:
        """
        Get fallback method.
        
        Returns:
            Fallback method ('static' or 'simple')
        """
        return self.config['fallback_method']
    
    def __repr__(self) -> str:
        """String representation of configuration."""
        return f"MLRConfig(config_file={self.config_file}, config={self.config})"


# Global configuration instance
_global_config: Optional[MLRConfig] = None


def get_config(config_file: Optional[str] = None, force_reload: bool = False) -> MLRConfig:
    """
    Get global configuration instance.
    
    Args:
        config_file: Path to configuration file (only used on first call)
        force_reload: Force reload of configuration
        
    Returns:
        MLRConfig instance
    """
    global _global_config
    
    if _global_config is None or force_reload:
        _global_config = MLRConfig(config_file)
    
    return _global_config


def reset_config():
    """Reset global configuration instance (mainly for testing)."""
    global _global_config
    _global_config = None
