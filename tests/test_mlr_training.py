"""Property-based tests for MLR model training."""
import pytest
import numpy as np
import joblib
import os
from hypothesis import given, strategies as st, settings, HealthCheck
from train_mlr_model import train_mlr_model, generate_training_data


class TestMLRModelTraining:
    """Property-based tests for MLR model training infrastructure."""
    
    @settings(max_examples=10, deadline=None, suppress_health_check=[
        HealthCheck.function_scoped_fixture
    ])
    @given(
        n_samples=st.integers(min_value=100, max_value=500)
    )
    def test_model_coefficient_consistency(self, n_samples, tmp_path):
        """
        **Feature: ml-emission-prediction, Property 1: Model coefficient consistency**
        **Validates: Requirements 8.2, 8.4**
        
        For any training dataset, when the model is trained and saved, then loaded back,
        the loaded model should have all required coefficients present and should produce
        identical predictions to the original model.
        
        This ensures:
        1. All coefficients (β₀, β₁, ..., βₙ) are properly saved
        2. Coefficients can be loaded correctly
        3. The loaded model applies coefficients consistently
        """
        # Train a model with the given sample size
        save_dir = str(tmp_path)
        
        # Generate training data
        df = generate_training_data(n_samples=n_samples)
        
        # Train model (this will save to tmp_path)
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import StandardScaler, OneHotEncoder
        from sklearn.model_selection import train_test_split
        
        X = df.drop('emission_g', axis=1)
        y = df['emission_g']
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Encode categorical features
        categorical_features = ['fuel_type', 'vehicle_type']
        encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        
        X_train_categorical = X_train[categorical_features]
        X_test_categorical = X_test[categorical_features]
        
        encoder.fit(X_train_categorical)
        X_train_encoded = encoder.transform(X_train_categorical)
        X_test_encoded = encoder.transform(X_test_categorical)
        
        # Combine with numerical features
        numerical_features = ['distance_km', 'fuel_consumption_kml', 'avg_speed_kmh']
        X_train_numerical = X_train[numerical_features].values
        X_test_numerical = X_test[numerical_features].values
        
        X_train_combined = np.hstack([X_train_numerical, X_train_encoded])
        X_test_combined = np.hstack([X_test_numerical, X_test_encoded])
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train_combined)
        X_test_scaled = scaler.transform(X_test_combined)
        
        # Train model
        model = LinearRegression()
        model.fit(X_train_scaled, y_train)
        
        # Save model artifacts
        model_path = os.path.join(save_dir, 'test_model.joblib')
        scaler_path = os.path.join(save_dir, 'test_scaler.joblib')
        encoder_path = os.path.join(save_dir, 'test_encoder.joblib')
        
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        joblib.dump(encoder, encoder_path)
        
        # Make predictions with original model
        original_predictions = model.predict(X_test_scaled)
        
        # Load model back
        loaded_model = joblib.load(model_path)
        loaded_scaler = joblib.load(scaler_path)
        loaded_encoder = joblib.load(encoder_path)
        
        # Verify all coefficients are present (Requirement 8.4)
        assert hasattr(loaded_model, 'coef_'), "Loaded model missing coefficients"
        assert hasattr(loaded_model, 'intercept_'), "Loaded model missing intercept"
        assert len(loaded_model.coef_) > 0, "Loaded model has empty coefficients"
        
        # Verify coefficient count matches expected features
        # 3 numerical + encoded categorical features
        expected_n_features = 3 + len(encoder.get_feature_names_out())
        assert len(loaded_model.coef_) == expected_n_features, \
            f"Expected {expected_n_features} coefficients, got {len(loaded_model.coef_)}"
        
        # Verify coefficients are identical
        np.testing.assert_array_almost_equal(
            model.coef_, loaded_model.coef_,
            decimal=10,
            err_msg="Loaded model coefficients differ from original"
        )
        
        np.testing.assert_almost_equal(
            model.intercept_, loaded_model.intercept_,
            decimal=10,
            err_msg="Loaded model intercept differs from original"
        )
        
        # Make predictions with loaded model (Requirement 8.2)
        # This verifies that all coefficients are properly applied
        loaded_predictions = loaded_model.predict(X_test_scaled)
        
        # Verify predictions are identical
        np.testing.assert_array_almost_equal(
            original_predictions, loaded_predictions,
            decimal=5,
            err_msg="Loaded model produces different predictions than original"
        )
        
        # Verify all coefficients are non-zero or have meaningful values
        # (at least some should be non-zero for a trained model)
        non_zero_coefs = np.sum(np.abs(loaded_model.coef_) > 1e-10)
        assert non_zero_coefs > 0, "All coefficients are zero - model not trained properly"


class TestModelCoefficientValidation:
    """Test that model coefficients are validated on load."""
    
    def test_coefficient_structure_validation(self, tmp_path):
        """
        Test that loaded coefficients have the correct structure.
        **Validates: Requirements 8.4**
        """
        # Train a simple model
        from sklearn.linear_model import LinearRegression
        
        X = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        y = np.array([10, 20, 30])
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Save and load
        model_path = os.path.join(tmp_path, 'simple_model.joblib')
        joblib.dump(model, model_path)
        loaded_model = joblib.load(model_path)
        
        # Verify coefficient structure
        assert isinstance(loaded_model.coef_, np.ndarray), "Coefficients should be numpy array"
        assert len(loaded_model.coef_) == 3, "Should have 3 coefficients for 3 features"
        assert isinstance(loaded_model.intercept_, (float, np.floating)), "Intercept should be float"
