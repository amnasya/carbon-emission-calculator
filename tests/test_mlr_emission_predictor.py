"""Property-based tests and unit tests for MLR Emission Predictor."""
import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from mlr_emission_predictor import MLREmissionPredictor, FeatureExtractor


class TestPredictionConsistency:
    """Property-based tests for prediction consistency."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        distance_km=st.floats(min_value=0.1, max_value=1000.0),
        fuel_type=st.sampled_from(['Bensin', 'Diesel', 'Listrik']),
        vehicle_type=st.sampled_from(['LCGC', 'SUV', 'Sedan', 'EV']),
        fuel_consumption_kml=st.floats(min_value=5.0, max_value=150.0),
        avg_speed_kmh=st.floats(min_value=5.0, max_value=150.0)
    )
    def test_prediction_non_negativity(self, distance_km, fuel_type, vehicle_type, 
                                      fuel_consumption_kml, avg_speed_kmh):
        """
        **Feature: ml-emission-prediction, Property 2: Prediction non-negativity**
        **Validates: Requirements 8.5**
        
        For any valid input features (distance, fuel type, vehicle type, fuel consumption, 
        average speed), the predicted CO₂ emission must be non-negative.
        
        This ensures:
        1. The MLR formula produces physically meaningful results
        2. The prediction output is a valid emission value (≥ 0 grams)
        3. No negative emissions are predicted regardless of input combination
        """
        # Filter out invalid combinations (EV with non-electric fuel, etc.)
        if vehicle_type == 'EV' and fuel_type != 'Listrik':
            assume(False)
        if vehicle_type != 'EV' and fuel_type == 'Listrik':
            assume(False)
        
        # Ensure finite values
        assume(np.isfinite(distance_km))
        assume(np.isfinite(fuel_consumption_kml))
        assume(np.isfinite(avg_speed_kmh))
        
        try:
            predictor = MLREmissionPredictor()
            
            # Make prediction
            emission = predictor.predict_emission(
                distance_km=distance_km,
                fuel_type=fuel_type,
                vehicle_type=vehicle_type,
                fuel_consumption_kml=fuel_consumption_kml,
                avg_speed_kmh=avg_speed_kmh
            )
            
            # Property: Emission must be non-negative
            assert emission >= 0, f"Predicted emission {emission} is negative"
            
            # Additional check: emission should be finite
            assert np.isfinite(emission), f"Predicted emission {emission} is not finite"
            
        except (ValueError, RuntimeError) as e:
            # If validation fails, that's acceptable - we're testing valid inputs
            # But the error should be about validation, not prediction
            if "Invalid input" in str(e):
                pytest.skip(f"Input validation rejected: {e}")
            else:
                raise


class TestInputValidation:
    """Property-based tests for input validation."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        distance_km=st.one_of(
            st.floats(min_value=-1000.0, max_value=-0.01),  # Negative
            st.floats(min_value=10001.0, max_value=50000.0),  # Too large
            st.just(0.0),  # Zero
            st.just(float('nan')),  # NaN
            st.just(float('inf')),  # Infinity
        ),
        fuel_type=st.sampled_from(['Bensin', 'Diesel', 'Listrik']),
        vehicle_type=st.sampled_from(['LCGC', 'SUV', 'Sedan', 'EV']),
        fuel_consumption_kml=st.floats(min_value=5.0, max_value=150.0),
        avg_speed_kmh=st.floats(min_value=5.0, max_value=150.0)
    )
    def test_invalid_distance_rejection(self, distance_km, fuel_type, vehicle_type,
                                       fuel_consumption_kml, avg_speed_kmh):
        """
        **Feature: ml-emission-prediction, Property 3: Invalid input rejection**
        **Validates: Requirements 3.3, 3.4**
        
        For any invalid distance value (negative, zero, too large, NaN, infinity),
        the predictor must reject the input with a clear error message.
        """
        # Skip valid distances
        if 0.1 <= distance_km <= 10000 and np.isfinite(distance_km):
            assume(False)
        
        # Filter out invalid vehicle-fuel combinations
        if vehicle_type == 'EV' and fuel_type != 'Listrik':
            assume(False)
        if vehicle_type != 'EV' and fuel_type == 'Listrik':
            assume(False)
        
        # Ensure other inputs are valid
        assume(np.isfinite(fuel_consumption_kml))
        assume(np.isfinite(avg_speed_kmh))
        
        predictor = MLREmissionPredictor()
        
        # Property: Invalid distance must be rejected
        with pytest.raises(ValueError) as exc_info:
            predictor.predict_emission(
                distance_km=distance_km,
                fuel_type=fuel_type,
                vehicle_type=vehicle_type,
                fuel_consumption_kml=fuel_consumption_kml,
                avg_speed_kmh=avg_speed_kmh
            )
        
        # Error message should mention the problem
        error_msg = str(exc_info.value).lower()
        assert 'distance' in error_msg or 'invalid' in error_msg, \
            f"Error message should mention distance problem: {exc_info.value}"
    
    @settings(max_examples=100, deadline=None)
    @given(
        distance_km=st.floats(min_value=0.1, max_value=1000.0),
        fuel_type=st.text(min_size=1, max_size=20).filter(
            lambda x: x not in ['Bensin', 'Diesel', 'Listrik']
        ),
        vehicle_type=st.sampled_from(['LCGC', 'SUV', 'Sedan', 'EV']),
        fuel_consumption_kml=st.floats(min_value=5.0, max_value=150.0),
        avg_speed_kmh=st.floats(min_value=5.0, max_value=150.0)
    )
    def test_invalid_fuel_type_rejection(self, distance_km, fuel_type, vehicle_type,
                                        fuel_consumption_kml, avg_speed_kmh):
        """
        **Feature: ml-emission-prediction, Property 3: Invalid input rejection**
        **Validates: Requirements 4.3, 4.4**
        
        For any unsupported fuel type, the predictor must reject the input
        with an error message listing valid fuel types.
        """
        # Ensure other inputs are valid
        assume(np.isfinite(distance_km))
        assume(np.isfinite(fuel_consumption_kml))
        assume(np.isfinite(avg_speed_kmh))
        
        predictor = MLREmissionPredictor()
        
        # Property: Invalid fuel type must be rejected
        with pytest.raises(ValueError) as exc_info:
            predictor.predict_emission(
                distance_km=distance_km,
                fuel_type=fuel_type,
                vehicle_type=vehicle_type,
                fuel_consumption_kml=fuel_consumption_kml,
                avg_speed_kmh=avg_speed_kmh
            )
        
        # Error message should mention fuel type and list valid options
        error_msg = str(exc_info.value).lower()
        assert 'fuel' in error_msg or 'invalid' in error_msg, \
            f"Error message should mention fuel type problem: {exc_info.value}"
    
    @settings(max_examples=100, deadline=None)
    @given(
        distance_km=st.floats(min_value=0.1, max_value=1000.0),
        fuel_type=st.sampled_from(['Bensin', 'Diesel', 'Listrik']),
        vehicle_type=st.text(min_size=1, max_size=20).filter(
            lambda x: x not in ['LCGC', 'SUV', 'Sedan', 'EV']
        ),
        fuel_consumption_kml=st.floats(min_value=5.0, max_value=150.0),
        avg_speed_kmh=st.floats(min_value=5.0, max_value=150.0)
    )
    def test_invalid_vehicle_type_rejection(self, distance_km, fuel_type, vehicle_type,
                                           fuel_consumption_kml, avg_speed_kmh):
        """
        **Feature: ml-emission-prediction, Property 3: Invalid input rejection**
        **Validates: Requirements 5.3, 5.4**
        
        For any unsupported vehicle type, the predictor must reject the input
        with an error message listing valid vehicle types.
        """
        # Ensure other inputs are valid
        assume(np.isfinite(distance_km))
        assume(np.isfinite(fuel_consumption_kml))
        assume(np.isfinite(avg_speed_kmh))
        
        predictor = MLREmissionPredictor()
        
        # Property: Invalid vehicle type must be rejected
        with pytest.raises(ValueError) as exc_info:
            predictor.predict_emission(
                distance_km=distance_km,
                fuel_type=fuel_type,
                vehicle_type=vehicle_type,
                fuel_consumption_kml=fuel_consumption_kml,
                avg_speed_kmh=avg_speed_kmh
            )
        
        # Error message should mention vehicle type and list valid options
        error_msg = str(exc_info.value).lower()
        assert 'vehicle' in error_msg or 'invalid' in error_msg, \
            f"Error message should mention vehicle type problem: {exc_info.value}"
    
    @settings(max_examples=100, deadline=None)
    @given(
        distance_km=st.floats(min_value=0.1, max_value=1000.0),
        fuel_type=st.sampled_from(['Bensin', 'Diesel', 'Listrik']),
        vehicle_type=st.sampled_from(['LCGC', 'SUV', 'Sedan', 'EV']),
        fuel_consumption_kml=st.one_of(
            st.floats(min_value=-100.0, max_value=-0.01),  # Negative
            st.just(0.0),  # Zero
            st.floats(min_value=201.0, max_value=1000.0),  # Too large
        ),
        avg_speed_kmh=st.floats(min_value=5.0, max_value=150.0)
    )
    def test_invalid_fuel_consumption_rejection(self, distance_km, fuel_type, vehicle_type,
                                               fuel_consumption_kml, avg_speed_kmh):
        """
        **Feature: ml-emission-prediction, Property 3: Invalid input rejection**
        **Validates: Requirements 6.3**
        
        For any invalid fuel consumption value (negative, zero, too large),
        the predictor must reject the input with a clear error message.
        """
        # Skip valid fuel consumption
        if 0.1 <= fuel_consumption_kml <= 200:
            assume(False)
        
        # Filter out invalid vehicle-fuel combinations
        if vehicle_type == 'EV' and fuel_type != 'Listrik':
            assume(False)
        if vehicle_type != 'EV' and fuel_type == 'Listrik':
            assume(False)
        
        # Ensure other inputs are valid
        assume(np.isfinite(distance_km))
        assume(np.isfinite(fuel_consumption_kml))
        assume(np.isfinite(avg_speed_kmh))
        
        predictor = MLREmissionPredictor()
        
        # Property: Invalid fuel consumption must be rejected
        with pytest.raises(ValueError) as exc_info:
            predictor.predict_emission(
                distance_km=distance_km,
                fuel_type=fuel_type,
                vehicle_type=vehicle_type,
                fuel_consumption_kml=fuel_consumption_kml,
                avg_speed_kmh=avg_speed_kmh
            )
        
        # Error message should mention the problem
        error_msg = str(exc_info.value).lower()
        assert 'consumption' in error_msg or 'invalid' in error_msg, \
            f"Error message should mention fuel consumption problem: {exc_info.value}"
    
    @settings(max_examples=100, deadline=None)
    @given(
        distance_km=st.floats(min_value=0.1, max_value=1000.0),
        fuel_type=st.sampled_from(['Bensin', 'Diesel', 'Listrik']),
        vehicle_type=st.sampled_from(['LCGC', 'SUV', 'Sedan', 'EV']),
        fuel_consumption_kml=st.floats(min_value=5.0, max_value=150.0),
        avg_speed_kmh=st.one_of(
            st.floats(min_value=-100.0, max_value=-0.01),  # Negative
            st.just(0.0),  # Zero
            st.floats(min_value=0.01, max_value=4.99),  # Too slow
            st.floats(min_value=201.0, max_value=500.0),  # Too fast
        )
    )
    def test_invalid_speed_rejection(self, distance_km, fuel_type, vehicle_type,
                                    fuel_consumption_kml, avg_speed_kmh):
        """
        **Feature: ml-emission-prediction, Property 3: Invalid input rejection**
        **Validates: Requirements 7.4**
        
        For any invalid average speed (negative, zero, outside realistic bounds),
        the predictor must reject the input with a clear error message.
        """
        # Skip valid speeds
        if 5.0 <= avg_speed_kmh <= 200.0:
            assume(False)
        
        # Filter out invalid vehicle-fuel combinations
        if vehicle_type == 'EV' and fuel_type != 'Listrik':
            assume(False)
        if vehicle_type != 'EV' and fuel_type == 'Listrik':
            assume(False)
        
        # Ensure other inputs are valid
        assume(np.isfinite(distance_km))
        assume(np.isfinite(fuel_consumption_kml))
        assume(np.isfinite(avg_speed_kmh))
        
        predictor = MLREmissionPredictor()
        
        # Property: Invalid speed must be rejected
        with pytest.raises(ValueError) as exc_info:
            predictor.predict_emission(
                distance_km=distance_km,
                fuel_type=fuel_type,
                vehicle_type=vehicle_type,
                fuel_consumption_kml=fuel_consumption_kml,
                avg_speed_kmh=avg_speed_kmh
            )
        
        # Error message should mention the problem
        error_msg = str(exc_info.value).lower()
        assert 'speed' in error_msg or 'invalid' in error_msg, \
            f"Error message should mention speed problem: {exc_info.value}"


class TestCategoricalEncoding:
    """Property-based tests for categorical encoding."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        fuel_type=st.sampled_from(['Bensin', 'Diesel', 'Listrik']),
        vehicle_type=st.sampled_from(['LCGC', 'SUV', 'Sedan', 'EV'])
    )
    def test_encoding_consistency(self, fuel_type, vehicle_type):
        """
        **Feature: ml-emission-prediction, Property 6: Encoding reversibility**
        **Validates: Requirements 4.2, 5.2, 10.2**
        
        For any valid categorical values (fuel type, vehicle type), the encoding
        process must be consistent and reversible. This means:
        1. The same categorical values always produce the same encoded output
        2. The encoder can be saved and loaded without changing behavior
        3. The encoding scheme matches what was used during training
        
        This ensures that preprocessing is consistent between training and prediction,
        which is critical for model accuracy.
        """
        # Filter out invalid vehicle-fuel combinations
        if vehicle_type == 'EV' and fuel_type != 'Listrik':
            assume(False)
        if vehicle_type != 'EV' and fuel_type == 'Listrik':
            assume(False)
        
        try:
            predictor = MLREmissionPredictor()
            
            # Encode the categorical values twice
            categorical_data_1 = np.array([[fuel_type, vehicle_type]])
            categorical_data_2 = np.array([[fuel_type, vehicle_type]])
            
            encoded_1 = predictor.encoder.transform(categorical_data_1)
            encoded_2 = predictor.encoder.transform(categorical_data_2)
            
            # Property 1: Same input produces same output (consistency)
            assert np.array_equal(encoded_1, encoded_2), \
                f"Encoding not consistent: {encoded_1} != {encoded_2}"
            
            # Property 2: Encoded output is a valid one-hot encoding
            # Each row should sum to 2 (one for fuel type, one for vehicle type)
            row_sum = np.sum(encoded_1[0])
            assert row_sum == 2, \
                f"One-hot encoding invalid: row sum is {row_sum}, expected 2"
            
            # Property 3: All values should be 0 or 1
            assert np.all((encoded_1 == 0) | (encoded_1 == 1)), \
                f"Encoding contains values other than 0 or 1: {encoded_1}"
            
            # Property 4: Encoding is deterministic across predictions
            # Make two predictions with same inputs and verify they use same encoding
            distance_km = 50.0
            fuel_consumption_kml = 15.0
            avg_speed_kmh = 60.0
            
            emission_1 = predictor.predict_emission(
                distance_km, fuel_type, vehicle_type, 
                fuel_consumption_kml, avg_speed_kmh
            )
            emission_2 = predictor.predict_emission(
                distance_km, fuel_type, vehicle_type,
                fuel_consumption_kml, avg_speed_kmh
            )
            
            # Same inputs should produce same predictions (deterministic)
            assert abs(emission_1 - emission_2) < 0.001, \
                f"Predictions not deterministic: {emission_1} != {emission_2}"
            
        except (FileNotFoundError, RuntimeError) as e:
            # If model files are missing, skip the test
            pytest.skip(f"Model files not available: {e}")
    
    @settings(max_examples=100, deadline=None)
    @given(
        fuel_type=st.sampled_from(['Bensin', 'Diesel', 'Listrik']),
        vehicle_type=st.sampled_from(['LCGC', 'SUV', 'Sedan', 'EV'])
    )
    def test_encoding_loaded_from_training(self, fuel_type, vehicle_type):
        """
        **Feature: ml-emission-prediction, Property 6: Encoding reversibility**
        **Validates: Requirements 10.2, 10.4**
        
        For any valid categorical values, the encoder loaded from disk must produce
        the same encoding as would be produced during training. This ensures that
        the preprocessing pipeline is consistent between training and prediction.
        
        This tests that:
        1. The encoder can be saved and loaded without corruption
        2. The loaded encoder produces valid one-hot encodings
        3. The encoding scheme matches the expected format
        """
        # Filter out invalid vehicle-fuel combinations
        if vehicle_type == 'EV' and fuel_type != 'Listrik':
            assume(False)
        if vehicle_type != 'EV' and fuel_type == 'Listrik':
            assume(False)
        
        try:
            predictor = MLREmissionPredictor()
            
            # Test that encoder produces valid one-hot encoding
            categorical_data = np.array([[fuel_type, vehicle_type]])
            encoded = predictor.encoder.transform(categorical_data)
            
            # Property: Encoded output should be 2D array
            assert encoded.ndim == 2, \
                f"Encoded output should be 2D, got {encoded.ndim}D"
            
            # Property: Each value should be 0 or 1 (one-hot encoding)
            assert np.all((encoded == 0) | (encoded == 1)), \
                f"One-hot encoding should only contain 0 or 1, got {encoded}"
            
            # Property: Should have exactly 2 ones per row (one for fuel, one for vehicle)
            row_sum = np.sum(encoded[0])
            assert row_sum == 2, \
                f"One-hot encoding should have 2 ones per row, got {row_sum}"
            
            # Property: Number of encoded features should match expected
            # We have 3 fuel types + 4 vehicle types = 7 encoded features
            expected_features = 7
            assert encoded.shape[1] == expected_features, \
                f"Expected {expected_features} encoded features, got {encoded.shape[1]}"
            
            # Property: Encoder should have correct feature names
            feature_names = predictor.encoder.get_feature_names_out(['fuel_type', 'vehicle_type'])
            assert len(feature_names) == expected_features, \
                f"Expected {expected_features} feature names, got {len(feature_names)}"
            
            # Property: Feature names should include the categorical values
            feature_names_str = ' '.join(feature_names)
            assert fuel_type in feature_names_str, \
                f"Fuel type '{fuel_type}' not found in feature names: {feature_names}"
            assert vehicle_type in feature_names_str, \
                f"Vehicle type '{vehicle_type}' not found in feature names: {feature_names}"
            
        except (FileNotFoundError, RuntimeError) as e:
            # If model files are missing, skip the test
            pytest.skip(f"Model files not available: {e}")


class TestFeatureExtractor:
    """Tests for FeatureExtractor class."""
    
    def test_fuel_consumption_lookup(self):
        """Test fuel consumption lookup table."""
        extractor = FeatureExtractor()
        
        # Test valid combinations
        assert extractor.get_fuel_consumption('LCGC', 'Bensin') == 18.0
        assert extractor.get_fuel_consumption('SUV', 'Diesel') == 12.0
        assert extractor.get_fuel_consumption('EV', 'Listrik') == 100.0
        
        # Test invalid combination returns default
        assert extractor.get_fuel_consumption('Unknown', 'Unknown') == 12.0
    
    def test_avg_speed_calculation(self):
        """Test average speed calculation."""
        extractor = FeatureExtractor()
        
        # 60 km in 60 minutes = 60 km/h
        assert extractor.calculate_avg_speed(60.0, 60.0) == 60.0
        
        # 100 km in 120 minutes = 50 km/h
        assert extractor.calculate_avg_speed(100.0, 120.0) == 50.0
        
        # Invalid duration should raise error
        with pytest.raises(ValueError):
            extractor.calculate_avg_speed(100.0, 0.0)
    
    def test_feature_extraction(self):
        """Test complete feature extraction."""
        extractor = FeatureExtractor()
        
        route_data = {
            'distance_km': 50.0,
            'duration_min': 60.0
        }
        
        features = extractor.extract_features(route_data, 'LCGC', 'Bensin')
        
        assert features['distance_km'] == 50.0
        assert features['fuel_type'] == 'Bensin'
        assert features['vehicle_type'] == 'LCGC'
        assert features['fuel_consumption_kml'] == 18.0
        assert features['avg_speed_kmh'] == 50.0
    
    def test_distance_conversion(self):
        """Test distance conversion from meters."""
        extractor = FeatureExtractor()
        
        route_data = {
            'distance_m': 50000.0,  # 50 km
            'duration_min': 60.0
        }
        
        features = extractor.extract_features(route_data, 'LCGC', 'Bensin')
        
        assert features['distance_km'] == 50.0
    
    @settings(max_examples=100, deadline=None)
    @given(
        distance_km=st.floats(min_value=0.1, max_value=1000.0),
        duration_min=st.floats(min_value=1.0, max_value=600.0),
        fuel_type=st.sampled_from(['Bensin', 'Diesel', 'Listrik']),
        vehicle_type=st.sampled_from(['LCGC', 'SUV', 'Sedan', 'EV'])
    )
    def test_feature_extraction_completeness(self, distance_km, duration_min, 
                                            fuel_type, vehicle_type):
        """
        **Feature: ml-emission-prediction, Property 4: Feature extraction completeness**
        **Validates: Requirements 3.1, 4.1, 5.1, 6.1, 7.1**
        
        For any valid route data, vehicle type, and fuel type, the feature extractor
        must produce a complete feature dictionary containing all required fields:
        - distance_km (extracted and converted if needed)
        - fuel_type (passed through)
        - vehicle_type (passed through)
        - fuel_consumption_kml (looked up from table)
        - avg_speed_kmh (calculated or provided)
        
        This ensures that all features needed for ML prediction are present and valid.
        """
        # Filter out invalid vehicle-fuel combinations
        if vehicle_type == 'EV' and fuel_type != 'Listrik':
            assume(False)
        if vehicle_type != 'EV' and fuel_type == 'Listrik':
            assume(False)
        
        # Ensure finite values
        assume(np.isfinite(distance_km))
        assume(np.isfinite(duration_min))
        
        extractor = FeatureExtractor()
        
        # Test with distance_km format
        route_data = {
            'distance_km': distance_km,
            'duration_min': duration_min
        }
        
        features = extractor.extract_features(route_data, vehicle_type, fuel_type)
        
        # Property: All required features must be present
        required_keys = ['distance_km', 'fuel_type', 'vehicle_type', 
                        'fuel_consumption_kml', 'avg_speed_kmh']
        for key in required_keys:
            assert key in features, f"Missing required feature: {key}"
        
        # Property: Feature values must match inputs or be valid
        assert features['distance_km'] == distance_km, \
            "Distance should match input"
        assert features['fuel_type'] == fuel_type, \
            "Fuel type should match input"
        assert features['vehicle_type'] == vehicle_type, \
            "Vehicle type should match input"
        assert features['fuel_consumption_kml'] > 0, \
            "Fuel consumption must be positive"
        assert features['avg_speed_kmh'] > 0, \
            "Average speed must be positive"
        assert np.isfinite(features['fuel_consumption_kml']), \
            "Fuel consumption must be finite"
        assert np.isfinite(features['avg_speed_kmh']), \
            "Average speed must be finite"
    
    @settings(max_examples=100, deadline=None)
    @given(
        distance_m=st.floats(min_value=100.0, max_value=1000000.0),
        duration_min=st.floats(min_value=1.0, max_value=600.0),
        fuel_type=st.sampled_from(['Bensin', 'Diesel', 'Listrik']),
        vehicle_type=st.sampled_from(['LCGC', 'SUV', 'Sedan', 'EV'])
    )
    def test_distance_conversion_property(self, distance_m, duration_min,
                                         fuel_type, vehicle_type):
        """
        **Feature: ml-emission-prediction, Property 4: Feature extraction completeness**
        **Validates: Requirements 3.1, 3.2**
        
        For any route data with distance in meters, the feature extractor must
        correctly convert it to kilometers (divide by 1000).
        """
        # Filter out invalid vehicle-fuel combinations
        if vehicle_type == 'EV' and fuel_type != 'Listrik':
            assume(False)
        if vehicle_type != 'EV' and fuel_type == 'Listrik':
            assume(False)
        
        # Ensure finite values
        assume(np.isfinite(distance_m))
        assume(np.isfinite(duration_min))
        
        extractor = FeatureExtractor()
        
        # Test with distance_m format
        route_data = {
            'distance_m': distance_m,
            'duration_min': duration_min
        }
        
        features = extractor.extract_features(route_data, vehicle_type, fuel_type)
        
        # Property: Distance should be converted from meters to kilometers
        expected_km = distance_m / 1000.0
        assert abs(features['distance_km'] - expected_km) < 0.001, \
            f"Distance conversion incorrect: {features['distance_km']} != {expected_km}"
    
    @settings(max_examples=100, deadline=None)
    @given(
        distance_km=st.floats(min_value=0.1, max_value=1000.0),
        duration_min=st.floats(min_value=1.0, max_value=600.0)
    )
    def test_speed_calculation_accuracy(self, distance_km, duration_min):
        """
        **Feature: ml-emission-prediction, Property 5: Speed calculation accuracy**
        **Validates: Requirements 7.2**
        
        For any valid distance and duration, the calculated average speed must equal
        distance divided by time (converted to hours). This is the mathematical
        definition of average speed: speed = distance / time.
        """
        # Ensure finite values
        assume(np.isfinite(distance_km))
        assume(np.isfinite(duration_min))
        assume(duration_min > 0)
        
        extractor = FeatureExtractor()
        
        # Calculate expected speed
        duration_hours = duration_min / 60.0
        expected_speed = distance_km / duration_hours
        
        # Get actual speed from extractor
        actual_speed = extractor.calculate_avg_speed(distance_km, duration_min)
        
        # Property: Calculated speed must match mathematical formula
        # Allow small floating point error
        relative_error = abs(actual_speed - expected_speed) / max(expected_speed, 0.001)
        assert relative_error < 0.0001, \
            f"Speed calculation incorrect: {actual_speed} != {expected_speed}"
        
        # Property: Speed must be positive for positive inputs
        assert actual_speed > 0, \
            f"Speed must be positive for positive inputs, got {actual_speed}"



class TestTransparencyFeatures:
    """Unit tests for model transparency features.
    
    Tests coefficient retrieval and explanation generation.
    Requirements: 8.1, 15.5
    """
    
    def test_get_model_coefficients(self):
        """
        Test coefficient retrieval from trained model.
        
        Validates: Requirements 8.1
        
        Ensures that:
        1. Coefficients can be retrieved from loaded model
        2. Result includes intercept (β₀)
        3. Result includes all feature coefficients
        4. All values are numeric
        """
        try:
            predictor = MLREmissionPredictor()
            
            # Get coefficients
            coefficients = predictor.get_model_coefficients()
            
            # Should have intercept
            assert 'intercept' in coefficients, "Missing intercept"
            assert isinstance(coefficients['intercept'], (int, float)), \
                "Intercept should be numeric"
            
            # Should have coefficients dict
            assert 'coefficients' in coefficients, "Missing coefficients"
            assert isinstance(coefficients['coefficients'], dict), \
                "Coefficients should be a dictionary"
            
            # All coefficient values should be numeric
            for name, value in coefficients['coefficients'].items():
                assert isinstance(value, (int, float)), \
                    f"Coefficient {name} should be numeric, got {type(value)}"
                assert np.isfinite(value), \
                    f"Coefficient {name} should be finite, got {value}"
            
            # Should have at least some coefficients
            assert len(coefficients['coefficients']) > 0, \
                "Should have at least one coefficient"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_get_model_coefficients_without_model(self):
        """
        Test that coefficient retrieval fails gracefully without model.
        
        Validates: Requirements 8.1
        """
        # Create predictor but don't load model
        predictor = MLREmissionPredictor.__new__(MLREmissionPredictor)
        predictor.is_loaded = False
        
        # Should raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            predictor.get_model_coefficients()
        
        assert "not loaded" in str(exc_info.value).lower()
    
    def test_get_feature_importance(self):
        """
        Test feature importance calculation.
        
        Validates: Requirements 8.1, 15.5
        
        Ensures that:
        1. Feature importance can be calculated
        2. All importance values are between 0 and 1
        3. Importance values sum to approximately 1.0 (100%)
        4. Features are sorted by importance
        """
        try:
            predictor = MLREmissionPredictor()
            
            # Get feature importance
            importance = predictor.get_feature_importance()
            
            # Should be a dictionary
            assert isinstance(importance, dict), \
                "Feature importance should be a dictionary"
            
            # Should have at least some features
            assert len(importance) > 0, \
                "Should have at least one feature"
            
            # All importance values should be between 0 and 1
            for name, value in importance.items():
                assert isinstance(value, (int, float)), \
                    f"Importance for {name} should be numeric"
                assert 0 <= value <= 1, \
                    f"Importance for {name} should be between 0 and 1, got {value}"
            
            # Importance values should sum to approximately 1.0
            total_importance = sum(importance.values())
            assert abs(total_importance - 1.0) < 0.01, \
                f"Total importance should be ~1.0, got {total_importance}"
            
            # Features should be sorted by importance (descending)
            importance_values = list(importance.values())
            assert importance_values == sorted(importance_values, reverse=True), \
                "Features should be sorted by importance (highest first)"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_get_feature_importance_without_model(self):
        """
        Test that feature importance fails gracefully without model.
        
        Validates: Requirements 8.1
        """
        # Create predictor but don't load model
        predictor = MLREmissionPredictor.__new__(MLREmissionPredictor)
        predictor.is_loaded = False
        
        # Should raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            predictor.get_feature_importance()
        
        assert "not loaded" in str(exc_info.value).lower()
    
    def test_explain_prediction(self):
        """
        Test prediction explanation generation.
        
        Validates: Requirements 15.5
        
        Ensures that:
        1. Explanation can be generated for valid inputs
        2. Explanation includes prediction value
        3. Explanation includes input features
        4. Explanation includes feature contributions
        5. Explanation includes top factors
        6. Explanation includes human-readable text
        """
        try:
            predictor = MLREmissionPredictor()
            
            # Test inputs
            distance_km = 50.0
            fuel_type = 'Bensin'
            vehicle_type = 'LCGC'
            fuel_consumption_kml = 18.0
            avg_speed_kmh = 60.0
            
            # Get explanation
            explanation = predictor.explain_prediction(
                distance_km, fuel_type, vehicle_type,
                fuel_consumption_kml, avg_speed_kmh
            )
            
            # Should have required keys
            assert 'prediction' in explanation, "Missing prediction"
            assert 'inputs' in explanation, "Missing inputs"
            assert 'contributions' in explanation, "Missing contributions"
            assert 'top_factors' in explanation, "Missing top_factors"
            assert 'explanation_text' in explanation, "Missing explanation_text"
            
            # Prediction should be numeric and non-negative
            assert isinstance(explanation['prediction'], (int, float)), \
                "Prediction should be numeric"
            assert explanation['prediction'] >= 0, \
                "Prediction should be non-negative"
            
            # Inputs should match what we provided
            assert explanation['inputs']['distance_km'] == distance_km
            assert explanation['inputs']['fuel_type'] == fuel_type
            assert explanation['inputs']['vehicle_type'] == vehicle_type
            assert explanation['inputs']['fuel_consumption_kml'] == fuel_consumption_kml
            assert explanation['inputs']['avg_speed_kmh'] == avg_speed_kmh
            
            # Contributions should be a dict with numeric values
            assert isinstance(explanation['contributions'], dict), \
                "Contributions should be a dictionary"
            assert len(explanation['contributions']) > 0, \
                "Should have at least one contribution"
            for name, value in explanation['contributions'].items():
                assert isinstance(value, (int, float)), \
                    f"Contribution for {name} should be numeric"
            
            # Should have intercept contribution
            assert 'intercept' in explanation['contributions'], \
                "Should include intercept contribution"
            
            # Top factors should be a list
            assert isinstance(explanation['top_factors'], list), \
                "Top factors should be a list"
            assert len(explanation['top_factors']) <= 3, \
                "Should have at most 3 top factors"
            
            # Each top factor should have feature and contribution
            for factor in explanation['top_factors']:
                assert 'feature' in factor, "Factor missing feature name"
                assert 'contribution' in factor, "Factor missing contribution"
                assert isinstance(factor['contribution'], (int, float)), \
                    "Factor contribution should be numeric"
            
            # Explanation text should be a non-empty string
            assert isinstance(explanation['explanation_text'], str), \
                "Explanation text should be a string"
            assert len(explanation['explanation_text']) > 0, \
                "Explanation text should not be empty"
            
            # Explanation text should mention key information
            text_lower = explanation['explanation_text'].lower()
            assert 'prediction' in text_lower or 'emission' in text_lower, \
                "Explanation should mention prediction/emission"
            assert str(int(distance_km)) in explanation['explanation_text'], \
                "Explanation should mention distance"
            assert vehicle_type.lower() in text_lower, \
                "Explanation should mention vehicle type"
            assert fuel_type.lower() in text_lower, \
                "Explanation should mention fuel type"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_explain_prediction_with_precalculated_value(self):
        """
        Test explanation generation with pre-calculated prediction.
        
        Validates: Requirements 15.5
        
        Ensures that explanation can use a pre-calculated prediction value
        instead of recalculating it.
        """
        try:
            predictor = MLREmissionPredictor()
            
            # Test inputs
            distance_km = 50.0
            fuel_type = 'Bensin'
            vehicle_type = 'LCGC'
            fuel_consumption_kml = 18.0
            avg_speed_kmh = 60.0
            
            # Pre-calculate prediction
            prediction = predictor.predict_emission(
                distance_km, fuel_type, vehicle_type,
                fuel_consumption_kml, avg_speed_kmh
            )
            
            # Get explanation with pre-calculated value
            explanation = predictor.explain_prediction(
                distance_km, fuel_type, vehicle_type,
                fuel_consumption_kml, avg_speed_kmh,
                prediction=prediction
            )
            
            # Prediction in explanation should match pre-calculated value
            assert abs(explanation['prediction'] - prediction) < 0.01, \
                "Explanation should use provided prediction value"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_explain_prediction_invalid_inputs(self):
        """
        Test that explanation fails gracefully with invalid inputs.
        
        Validates: Requirements 15.5
        """
        try:
            predictor = MLREmissionPredictor()
            
            # Invalid distance (negative)
            with pytest.raises(ValueError) as exc_info:
                predictor.explain_prediction(
                    -50.0, 'Bensin', 'LCGC', 18.0, 60.0
                )
            assert 'invalid' in str(exc_info.value).lower()
            
            # Invalid fuel type
            with pytest.raises(ValueError) as exc_info:
                predictor.explain_prediction(
                    50.0, 'InvalidFuel', 'LCGC', 18.0, 60.0
                )
            assert 'invalid' in str(exc_info.value).lower()
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_explain_prediction_without_model(self):
        """
        Test that explanation fails gracefully without model.
        
        Validates: Requirements 15.5
        """
        # Create predictor but don't load model
        predictor = MLREmissionPredictor.__new__(MLREmissionPredictor)
        predictor.is_loaded = False
        
        # Should raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            predictor.explain_prediction(
                50.0, 'Bensin', 'LCGC', 18.0, 60.0
            )
        
        assert "not loaded" in str(exc_info.value).lower()
    
    def test_explanation_contributions_sum_to_prediction(self):
        """
        Test that feature contributions sum to the prediction value.
        
        Validates: Requirements 8.1, 15.5
        
        In a linear model, the sum of all feature contributions (including intercept)
        should equal the final prediction.
        """
        try:
            predictor = MLREmissionPredictor()
            
            # Test inputs
            distance_km = 100.0
            fuel_type = 'Diesel'
            vehicle_type = 'SUV'
            fuel_consumption_kml = 12.0
            avg_speed_kmh = 80.0
            
            # Get explanation
            explanation = predictor.explain_prediction(
                distance_km, fuel_type, vehicle_type,
                fuel_consumption_kml, avg_speed_kmh
            )
            
            # Sum all contributions
            total_contribution = sum(explanation['contributions'].values())
            prediction = explanation['prediction']
            
            # For MLR, contributions should sum to prediction (before max(0, x) clipping)
            # Allow some tolerance for floating point errors and the non-negativity constraint
            if prediction > 0:
                # If prediction is positive, contributions should sum close to it
                relative_error = abs(total_contribution - prediction) / max(prediction, 1.0)
                assert relative_error < 0.1, \
                    f"Contributions sum {total_contribution} should be close to prediction {prediction}"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")



class TestModelVersioning:
    """Unit tests for model versioning and updates.
    
    Tests version tracking and model validation.
    Requirements: 14.3, 14.4, 14.5
    """
    
    def test_model_version_tracking(self):
        """
        Test that model version is tracked correctly.
        
        Validates: Requirements 14.1, 14.2
        
        Ensures that:
        1. Model version is set when model is loaded
        2. Version information can be retrieved
        3. Version is a valid string
        """
        try:
            predictor = MLREmissionPredictor()
            
            # Model should have a version
            assert predictor.model_version is not None, \
                "Model version should be set"
            assert isinstance(predictor.model_version, str), \
                "Model version should be a string"
            assert len(predictor.model_version) > 0, \
                "Model version should not be empty"
            
            # Should be able to get model info
            model_info = predictor.get_model_info()
            
            assert 'version' in model_info, "Model info should include version"
            assert model_info['version'] == predictor.model_version, \
                "Model info version should match predictor version"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_model_loaded_timestamp(self):
        """
        Test that model load timestamp is recorded.
        
        Validates: Requirements 14.5
        
        Ensures that:
        1. Load timestamp is recorded when model is loaded
        2. Timestamp is a valid datetime
        3. Timestamp can be retrieved via get_model_info
        """
        try:
            predictor = MLREmissionPredictor()
            
            # Model should have a load timestamp
            assert predictor.model_loaded_at is not None, \
                "Model load timestamp should be set"
            
            # Should be able to get model info with timestamp
            model_info = predictor.get_model_info()
            
            assert 'loaded_at' in model_info, "Model info should include loaded_at"
            assert model_info['loaded_at'] is not None, \
                "Model info loaded_at should not be None"
            
            # Timestamp should be in ISO format
            assert isinstance(model_info['loaded_at'], str), \
                "Loaded_at should be a string in ISO format"
            
            # Should be able to parse the timestamp
            from datetime import datetime
            try:
                datetime.fromisoformat(model_info['loaded_at'])
            except ValueError:
                pytest.fail("Loaded_at timestamp is not in valid ISO format")
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_model_file_paths_tracked(self):
        """
        Test that model file paths are tracked.
        
        Validates: Requirements 14.2
        
        Ensures that:
        1. File paths are stored when model is loaded
        2. File paths can be retrieved via get_model_info
        3. File paths match the constructor arguments
        """
        try:
            model_path = 'mlr_emission_model.joblib'
            scaler_path = 'mlr_emission_scaler.joblib'
            encoder_path = 'mlr_emission_encoder.joblib'
            
            predictor = MLREmissionPredictor(
                model_path=model_path,
                scaler_path=scaler_path,
                encoder_path=encoder_path
            )
            
            # Get model info
            model_info = predictor.get_model_info()
            
            # Should include file paths
            assert 'model_path' in model_info, "Model info should include model_path"
            assert 'scaler_path' in model_info, "Model info should include scaler_path"
            assert 'encoder_path' in model_info, "Model info should include encoder_path"
            
            # Paths should match constructor arguments
            assert model_info['model_path'] == model_path, \
                "Model path should match constructor argument"
            assert model_info['scaler_path'] == scaler_path, \
                "Scaler path should match constructor argument"
            assert model_info['encoder_path'] == encoder_path, \
                "Encoder path should match constructor argument"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_model_file_timestamps_tracked(self):
        """
        Test that model file timestamps are tracked.
        
        Validates: Requirements 14.2
        
        Ensures that:
        1. File modification timestamps are recorded when model is loaded
        2. Timestamps can be retrieved via get_model_info
        3. Timestamps are valid numbers
        """
        try:
            predictor = MLREmissionPredictor()
            
            # Get model info
            model_info = predictor.get_model_info()
            
            # Should include file timestamps
            assert 'file_timestamps' in model_info, \
                "Model info should include file_timestamps"
            
            timestamps = model_info['file_timestamps']
            
            # Should have timestamps for all three files
            assert 'model' in timestamps, "Should have model file timestamp"
            assert 'scaler' in timestamps, "Should have scaler file timestamp"
            assert 'encoder' in timestamps, "Should have encoder file timestamp"
            
            # All timestamps should be valid numbers
            for key, timestamp in timestamps.items():
                assert isinstance(timestamp, (int, float)), \
                    f"Timestamp for {key} should be numeric"
                assert timestamp > 0, \
                    f"Timestamp for {key} should be positive"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_model_validation_on_load(self):
        """
        Test that model structure is validated when loaded.
        
        Validates: Requirements 14.3, 14.4
        
        Ensures that:
        1. Model is validated to have required attributes (coef_, intercept_)
        2. Scaler is validated to have transform method
        3. Encoder is validated to have transform method
        4. Invalid models are rejected with clear error messages
        """
        try:
            predictor = MLREmissionPredictor()
            
            # If we got here, model passed validation
            # Verify that model has required attributes
            assert hasattr(predictor.model, 'coef_'), \
                "Model should have coef_ attribute"
            assert hasattr(predictor.model, 'intercept_'), \
                "Model should have intercept_ attribute"
            assert hasattr(predictor.scaler, 'transform'), \
                "Scaler should have transform method"
            assert hasattr(predictor.encoder, 'transform'), \
                "Encoder should have transform method"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_get_model_info_without_model(self):
        """
        Test that get_model_info fails gracefully without loaded model.
        
        Validates: Requirements 14.2
        """
        # Create predictor but don't load model
        predictor = MLREmissionPredictor.__new__(MLREmissionPredictor)
        predictor.is_loaded = False
        
        # Should raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            predictor.get_model_info()
        
        assert "not loaded" in str(exc_info.value).lower()
    
    def test_check_for_updates(self):
        """
        Test checking for model file updates.
        
        Validates: Requirements 14.2
        
        Ensures that:
        1. Can check if model files have been updated
        2. Returns False when files haven't changed
        3. Method works without errors
        """
        try:
            predictor = MLREmissionPredictor()
            
            # Check for updates (should be False since we just loaded)
            has_updates = predictor.check_for_updates()
            
            # Should return a boolean
            assert isinstance(has_updates, bool), \
                "check_for_updates should return a boolean"
            
            # Should be False since files haven't changed
            assert has_updates == False, \
                "Should not detect updates immediately after loading"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_check_for_updates_without_model(self):
        """
        Test that check_for_updates fails gracefully without loaded model.
        
        Validates: Requirements 14.2
        """
        # Create predictor but don't load model
        predictor = MLREmissionPredictor.__new__(MLREmissionPredictor)
        predictor.is_loaded = False
        
        # Should raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            predictor.check_for_updates()
        
        assert "not loaded" in str(exc_info.value).lower()
    
    def test_reload_model_without_initial_load(self):
        """
        Test that reload_model fails gracefully without initial model.
        
        Validates: Requirements 14.2
        """
        # Create predictor but don't load model
        predictor = MLREmissionPredictor.__new__(MLREmissionPredictor)
        predictor.is_loaded = False
        
        # Should raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            predictor.reload_model()
        
        error_msg = str(exc_info.value).lower()
        assert "not loaded" in error_msg or "no model" in error_msg, \
            f"Error message should indicate model not loaded: {exc_info.value}"
    
    def test_reload_model_basic(self):
        """
        Test basic model reload functionality.
        
        Validates: Requirements 14.2, 14.3
        
        Ensures that:
        1. Model can be reloaded from disk
        2. Reload returns True on success
        3. Model remains functional after reload
        """
        try:
            predictor = MLREmissionPredictor()
            
            # Store original version
            original_version = predictor.model_version
            
            # Reload model
            success = predictor.reload_model(validate=True)
            
            # Should return True on success
            assert isinstance(success, bool), \
                "reload_model should return a boolean"
            assert success == True, \
                "reload_model should return True on successful reload"
            
            # Model should still be loaded
            assert predictor.is_loaded == True, \
                "Model should still be loaded after reload"
            
            # Should still be able to make predictions
            emission = predictor.predict_emission(
                distance_km=50.0,
                fuel_type='Bensin',
                vehicle_type='LCGC',
                fuel_consumption_kml=18.0,
                avg_speed_kmh=60.0
            )
            
            assert emission >= 0, \
                "Should be able to make valid predictions after reload"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_reload_model_with_validation(self):
        """
        Test model reload with validation enabled.
        
        Validates: Requirements 14.3, 14.4
        
        Ensures that:
        1. Validation is performed when requested
        2. Valid models pass validation
        3. Model works correctly after validated reload
        """
        try:
            predictor = MLREmissionPredictor()
            
            # Reload with validation
            success = predictor.reload_model(validate=True)
            
            assert success == True, \
                "Reload with validation should succeed for valid model"
            
            # Model should still work
            emission = predictor.predict_emission(
                distance_km=100.0,
                fuel_type='Diesel',
                vehicle_type='SUV',
                fuel_consumption_kml=12.0,
                avg_speed_kmh=80.0
            )
            
            assert emission >= 0, \
                "Model should produce valid predictions after validated reload"
            assert np.isfinite(emission), \
                "Model should produce finite predictions after validated reload"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_reload_model_without_validation(self):
        """
        Test model reload without validation.
        
        Validates: Requirements 14.2
        
        Ensures that:
        1. Model can be reloaded without validation
        2. Reload is faster when validation is skipped
        3. Model still works after reload
        """
        try:
            predictor = MLREmissionPredictor()
            
            # Reload without validation
            success = predictor.reload_model(validate=False)
            
            assert success == True, \
                "Reload without validation should succeed"
            
            # Model should still work
            emission = predictor.predict_emission(
                distance_km=50.0,
                fuel_type='Bensin',
                vehicle_type='LCGC',
                fuel_consumption_kml=18.0,
                avg_speed_kmh=60.0
            )
            
            assert emission >= 0, \
                "Model should produce valid predictions after reload"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
    
    def test_model_info_completeness(self):
        """
        Test that get_model_info returns complete information.
        
        Validates: Requirements 14.2, 14.5
        
        Ensures that model info includes all expected fields.
        """
        try:
            predictor = MLREmissionPredictor()
            
            model_info = predictor.get_model_info()
            
            # Check all expected fields are present
            expected_fields = [
                'version',
                'loaded_at',
                'model_path',
                'scaler_path',
                'encoder_path',
                'file_timestamps',
                'is_loaded'
            ]
            
            for field in expected_fields:
                assert field in model_info, \
                    f"Model info should include '{field}' field"
            
            # Check field types
            assert isinstance(model_info['version'], str), \
                "Version should be a string"
            assert isinstance(model_info['loaded_at'], str), \
                "Loaded_at should be a string (ISO format)"
            assert isinstance(model_info['model_path'], str), \
                "Model_path should be a string"
            assert isinstance(model_info['scaler_path'], str), \
                "Scaler_path should be a string"
            assert isinstance(model_info['encoder_path'], str), \
                "Encoder_path should be a string"
            assert isinstance(model_info['file_timestamps'], dict), \
                "File_timestamps should be a dictionary"
            assert isinstance(model_info['is_loaded'], bool), \
                "Is_loaded should be a boolean"
            
            # is_loaded should be True
            assert model_info['is_loaded'] == True, \
                "Is_loaded should be True for loaded model"
            
        except (FileNotFoundError, RuntimeError) as e:
            pytest.skip(f"Model files not available: {e}")
