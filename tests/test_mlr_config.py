#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for MLR Configuration Management

Tests configuration loading from:
- Environment variables
- Configuration files
- Default values
- Fallback behavior configuration

**Validates: Requirements 9.5**
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from mlr_config import MLRConfig, get_config, reset_config


class TestMLRConfigDefaults:
    """Test default configuration values."""
    
    def test_default_config_initialization(self):
        """Test that config initializes with default values."""
        config = MLRConfig()
        
        # Check that all default keys are present
        assert 'model_path' in config.get_all()
        assert 'scaler_path' in config.get_all()
        assert 'encoder_path' in config.get_all()
        assert 'fallback_enabled' in config.get_all()
        assert 'fallback_method' in config.get_all()
    
    def test_default_model_paths(self):
        """Test default model file paths."""
        config = MLRConfig()
        
        assert config.get('model_path') == 'mlr_emission_model.joblib'
        assert config.get('scaler_path') == 'mlr_emission_scaler.joblib'
        assert config.get('encoder_path') == 'mlr_emission_encoder.joblib'
        assert config.get('feature_info_path') == 'mlr_feature_info.joblib'
    
    def test_default_fallback_config(self):
        """Test default fallback configuration."""
        config = MLRConfig()
        
        assert config.get('fallback_enabled') is True
        assert config.get('fallback_method') == 'static'
        assert config.is_fallback_enabled() is True
        assert config.get_fallback_method() == 'static'
    
    def test_default_validation_bounds(self):
        """Test default validation bounds."""
        config = MLRConfig()
        
        bounds = config.get_validation_bounds()
        
        assert 'distance_km' in bounds
        assert 'avg_speed_kmh' in bounds
        assert 'fuel_consumption_kml' in bounds
        
        # Check that bounds are tuples with min and max
        assert len(bounds['distance_km']) == 2
        assert bounds['distance_km'][0] < bounds['distance_km'][1]


class TestEnvironmentVariableLoading:
    """Test configuration loading from environment variables."""
    
    def test_load_model_path_from_env(self, monkeypatch):
        """Test loading model path from environment variable."""
        monkeypatch.setenv('MLR_MODEL_PATH', '/custom/path/model.joblib')
        
        config = MLRConfig()
        
        assert config.get('model_path') == '/custom/path/model.joblib'
    
    def test_load_multiple_paths_from_env(self, monkeypatch):
        """Test loading multiple paths from environment variables."""
        monkeypatch.setenv('MLR_MODEL_PATH', '/custom/model.joblib')
        monkeypatch.setenv('MLR_SCALER_PATH', '/custom/scaler.joblib')
        monkeypatch.setenv('MLR_ENCODER_PATH', '/custom/encoder.joblib')
        
        config = MLRConfig()
        
        assert config.get('model_path') == '/custom/model.joblib'
        assert config.get('scaler_path') == '/custom/scaler.joblib'
        assert config.get('encoder_path') == '/custom/encoder.joblib'
    
    def test_load_boolean_from_env(self, monkeypatch):
        """Test loading boolean values from environment variables."""
        # Test various boolean representations
        test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('1', True),
            ('yes', True),
            ('on', True),
            ('false', False),
            ('False', False),
            ('0', False),
            ('no', False),
            ('off', False)
        ]
        
        for env_value, expected in test_cases:
            monkeypatch.setenv('MLR_FALLBACK_ENABLED', env_value)
            config = MLRConfig()
            assert config.get('fallback_enabled') is expected, f"Failed for {env_value}"
    
    def test_load_integer_from_env(self, monkeypatch):
        """Test loading integer values from environment variables."""
        monkeypatch.setenv('MLR_RELOAD_CHECK_INTERVAL', '600')
        
        config = MLRConfig()
        
        assert config.get('reload_check_interval') == 600
        assert isinstance(config.get('reload_check_interval'), int)
    
    def test_load_float_from_env(self, monkeypatch):
        """Test loading float values from environment variables."""
        monkeypatch.setenv('MLR_MIN_DISTANCE_KM', '0.5')
        monkeypatch.setenv('MLR_MAX_SPEED_KMH', '150.5')
        
        config = MLRConfig()
        
        assert config.get('min_distance_km') == 0.5
        assert config.get('max_speed_kmh') == 150.5
        assert isinstance(config.get('min_distance_km'), float)
    
    def test_load_string_from_env(self, monkeypatch):
        """Test loading string values from environment variables."""
        monkeypatch.setenv('MLR_FALLBACK_METHOD', 'simple')
        monkeypatch.setenv('MLR_LOG_LEVEL', 'DEBUG')
        
        config = MLRConfig()
        
        assert config.get('fallback_method') == 'simple'
        assert config.get('log_level') == 'DEBUG'
    
    def test_invalid_integer_env_uses_default(self, monkeypatch):
        """Test that invalid integer values fall back to defaults."""
        monkeypatch.setenv('MLR_RELOAD_CHECK_INTERVAL', 'not_a_number')
        
        config = MLRConfig()
        
        # Should use default value
        assert config.get('reload_check_interval') == 300
    
    def test_invalid_float_env_uses_default(self, monkeypatch):
        """Test that invalid float values fall back to defaults."""
        monkeypatch.setenv('MLR_MIN_DISTANCE_KM', 'invalid')
        
        config = MLRConfig()
        
        # Should use default value
        assert config.get('min_distance_km') == 0.1
    
    def test_env_overrides_defaults(self, monkeypatch):
        """Test that environment variables override default values."""
        monkeypatch.setenv('MLR_MODEL_PATH', '/env/model.joblib')
        
        config = MLRConfig()
        
        # Environment variable should override default
        assert config.get('model_path') == '/env/model.joblib'
        assert config.get('model_path') != MLRConfig.DEFAULT_CONFIG['model_path']


class TestConfigFileLoading:
    """Test configuration loading from JSON files."""
    
    def test_load_from_config_file(self):
        """Test loading configuration from JSON file."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                'model_path': '/file/model.joblib',
                'scaler_path': '/file/scaler.joblib',
                'fallback_enabled': False,
                'fallback_method': 'simple'
            }
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            config = MLRConfig(config_file=config_file)
            
            assert config.get('model_path') == '/file/model.joblib'
            assert config.get('scaler_path') == '/file/scaler.joblib'
            assert config.get('fallback_enabled') is False
            assert config.get('fallback_method') == 'simple'
            
        finally:
            os.unlink(config_file)
    
    def test_partial_config_file(self):
        """Test that partial config file merges with defaults."""
        # Create config file with only some values
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                'model_path': '/custom/model.joblib',
                'fallback_enabled': False
            }
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            config = MLRConfig(config_file=config_file)
            
            # Custom values from file
            assert config.get('model_path') == '/custom/model.joblib'
            assert config.get('fallback_enabled') is False
            
            # Default values for unspecified keys
            assert config.get('scaler_path') == 'mlr_emission_scaler.joblib'
            assert config.get('encoder_path') == 'mlr_emission_encoder.joblib'
            
        finally:
            os.unlink(config_file)
    
    def test_invalid_json_file_uses_defaults(self):
        """Test that invalid JSON file falls back to defaults."""
        # Create invalid JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{ invalid json }')
            config_file = f.name
        
        try:
            config = MLRConfig(config_file=config_file)
            
            # Should use default values
            assert config.get('model_path') == 'mlr_emission_model.joblib'
            
        finally:
            os.unlink(config_file)
    
    def test_nonexistent_config_file_uses_defaults(self):
        """Test that nonexistent config file uses defaults."""
        config = MLRConfig(config_file='/nonexistent/config.json')
        
        # Should use default values
        assert config.get('model_path') == 'mlr_emission_model.joblib'
    
    def test_unknown_keys_in_config_file_ignored(self):
        """Test that unknown keys in config file are ignored."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                'model_path': '/custom/model.joblib',
                'unknown_key': 'unknown_value',
                'another_unknown': 123
            }
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            config = MLRConfig(config_file=config_file)
            
            # Known key should be loaded
            assert config.get('model_path') == '/custom/model.joblib'
            
            # Unknown keys should not be in config
            assert config.get('unknown_key') is None
            assert config.get('another_unknown') is None
            
        finally:
            os.unlink(config_file)


class TestConfigPriority:
    """Test configuration priority (env > file > defaults)."""
    
    def test_env_overrides_file(self, monkeypatch):
        """Test that environment variables override config file."""
        # Create config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                'model_path': '/file/model.joblib',
                'fallback_enabled': False
            }
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            # Set environment variable
            monkeypatch.setenv('MLR_MODEL_PATH', '/env/model.joblib')
            
            config = MLRConfig(config_file=config_file)
            
            # Environment should override file
            assert config.get('model_path') == '/env/model.joblib'
            
            # File value should be used for keys not in env
            assert config.get('fallback_enabled') is False
            
        finally:
            os.unlink(config_file)
    
    def test_file_overrides_defaults(self):
        """Test that config file overrides defaults."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                'model_path': '/file/model.joblib'
            }
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            config = MLRConfig(config_file=config_file)
            
            # File should override default
            assert config.get('model_path') == '/file/model.joblib'
            assert config.get('model_path') != MLRConfig.DEFAULT_CONFIG['model_path']
            
        finally:
            os.unlink(config_file)


class TestConfigGetters:
    """Test configuration getter methods."""
    
    def test_get_method(self):
        """Test get method with and without default."""
        config = MLRConfig()
        
        # Existing key
        assert config.get('model_path') is not None
        
        # Non-existing key with default
        assert config.get('nonexistent', 'default_value') == 'default_value'
        
        # Non-existing key without default
        assert config.get('nonexistent') is None
    
    def test_get_all_method(self):
        """Test get_all method returns all config."""
        config = MLRConfig()
        
        all_config = config.get_all()
        
        assert isinstance(all_config, dict)
        assert 'model_path' in all_config
        assert 'fallback_enabled' in all_config
        
        # Should be a copy, not reference
        all_config['model_path'] = 'modified'
        assert config.get('model_path') != 'modified'
    
    def test_get_model_paths(self):
        """Test get_model_paths method."""
        config = MLRConfig()
        
        paths = config.get_model_paths()
        
        assert 'model_path' in paths
        assert 'scaler_path' in paths
        assert 'encoder_path' in paths
        assert 'feature_info_path' in paths
        assert len(paths) == 4
    
    def test_get_fallback_config(self):
        """Test get_fallback_config method."""
        config = MLRConfig()
        
        fallback_config = config.get_fallback_config()
        
        assert 'fallback_enabled' in fallback_config
        assert 'fallback_method' in fallback_config
        assert isinstance(fallback_config['fallback_enabled'], bool)
        assert isinstance(fallback_config['fallback_method'], str)
    
    def test_get_validation_bounds(self):
        """Test get_validation_bounds method."""
        config = MLRConfig()
        
        bounds = config.get_validation_bounds()
        
        assert 'distance_km' in bounds
        assert 'avg_speed_kmh' in bounds
        assert 'fuel_consumption_kml' in bounds
        
        # Each bound should be a tuple of (min, max)
        for key, (min_val, max_val) in bounds.items():
            assert isinstance(min_val, (int, float))
            assert isinstance(max_val, (int, float))
            assert min_val < max_val
    
    def test_is_fallback_enabled(self):
        """Test is_fallback_enabled method."""
        config = MLRConfig()
        
        result = config.is_fallback_enabled()
        
        assert isinstance(result, bool)
        assert result == config.get('fallback_enabled')
    
    def test_get_fallback_method(self):
        """Test get_fallback_method method."""
        config = MLRConfig()
        
        method = config.get_fallback_method()
        
        assert isinstance(method, str)
        assert method in ['static', 'simple']


class TestConfigSetters:
    """Test configuration setter methods."""
    
    def test_set_method(self):
        """Test set method for runtime configuration changes."""
        config = MLRConfig()
        
        original_value = config.get('model_path')
        
        config.set('model_path', '/new/path/model.joblib')
        
        assert config.get('model_path') == '/new/path/model.joblib'
        assert config.get('model_path') != original_value
    
    def test_set_unknown_key_warning(self):
        """Test that setting unknown key logs warning but doesn't crash."""
        config = MLRConfig()
        
        # Should not raise exception
        config.set('unknown_key', 'value')
        
        # Unknown key should not be added
        assert config.get('unknown_key') is None
    
    def test_save_to_file(self):
        """Test saving configuration to file."""
        config = MLRConfig()
        config.set('model_path', '/custom/model.joblib')
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            save_path = f.name
        
        try:
            config.save_to_file(save_path)
            
            # Load and verify
            with open(save_path, 'r') as f:
                saved_config = json.load(f)
            
            assert saved_config['model_path'] == '/custom/model.joblib'
            
        finally:
            if os.path.exists(save_path):
                os.unlink(save_path)
    
    def test_save_to_default_file(self):
        """Test saving to default file location."""
        config = MLRConfig()
        config.set('model_path', '/custom/model.joblib')
        
        save_path = 'mlr_config.json'
        
        try:
            config.save_to_file()
            
            # Should create file at default location
            assert os.path.exists(save_path)
            
            # Load and verify
            with open(save_path, 'r') as f:
                saved_config = json.load(f)
            
            assert saved_config['model_path'] == '/custom/model.joblib'
            
        finally:
            if os.path.exists(save_path):
                os.unlink(save_path)


class TestGlobalConfig:
    """Test global configuration instance management."""
    
    def teardown_method(self):
        """Reset global config after each test."""
        reset_config()
    
    def test_get_config_singleton(self):
        """Test that get_config returns singleton instance."""
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
    
    def test_get_config_with_file(self):
        """Test get_config with config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {'model_path': '/global/model.joblib'}
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            config = get_config(config_file=config_file)
            
            assert config.get('model_path') == '/global/model.joblib'
            
        finally:
            os.unlink(config_file)
    
    def test_get_config_force_reload(self):
        """Test force reload of global config."""
        config1 = get_config()
        config1.set('model_path', '/modified/model.joblib')
        
        # Without force_reload, should return same instance
        config2 = get_config()
        assert config2.get('model_path') == '/modified/model.joblib'
        
        # With force_reload, should create new instance
        config3 = get_config(force_reload=True)
        assert config3.get('model_path') != '/modified/model.joblib'
    
    def test_reset_config(self):
        """Test reset_config clears global instance."""
        config1 = get_config()
        config1.set('model_path', '/modified/model.joblib')
        
        reset_config()
        
        config2 = get_config()
        
        # Should be new instance with default values
        assert config2 is not config1
        assert config2.get('model_path') == 'mlr_emission_model.joblib'


class TestFallbackConfiguration:
    """Test fallback-specific configuration."""
    
    def test_fallback_enabled_by_default(self):
        """Test that fallback is enabled by default."""
        config = MLRConfig()
        
        assert config.is_fallback_enabled() is True
    
    def test_disable_fallback_via_env(self, monkeypatch):
        """Test disabling fallback via environment variable."""
        monkeypatch.setenv('MLR_FALLBACK_ENABLED', 'false')
        
        config = MLRConfig()
        
        assert config.is_fallback_enabled() is False
    
    def test_disable_fallback_via_file(self):
        """Test disabling fallback via config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {'fallback_enabled': False}
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            config = MLRConfig(config_file=config_file)
            
            assert config.is_fallback_enabled() is False
            
        finally:
            os.unlink(config_file)
    
    def test_fallback_method_static_by_default(self):
        """Test that fallback method is 'static' by default."""
        config = MLRConfig()
        
        assert config.get_fallback_method() == 'static'
    
    def test_change_fallback_method_via_env(self, monkeypatch):
        """Test changing fallback method via environment variable."""
        monkeypatch.setenv('MLR_FALLBACK_METHOD', 'simple')
        
        config = MLRConfig()
        
        assert config.get_fallback_method() == 'simple'
    
    def test_change_fallback_method_via_file(self):
        """Test changing fallback method via config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {'fallback_method': 'simple'}
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            config = MLRConfig(config_file=config_file)
            
            assert config.get_fallback_method() == 'simple'
            
        finally:
            os.unlink(config_file)
    
    def test_fallback_config_getter(self):
        """Test get_fallback_config returns both settings."""
        config = MLRConfig()
        
        fallback_config = config.get_fallback_config()
        
        assert fallback_config['fallback_enabled'] is True
        assert fallback_config['fallback_method'] == 'static'
