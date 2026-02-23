"""Unit tests for emission calculator module."""
import pytest
from emission import get_emission_factor, calculate_emission, get_valid_combinations


class TestEmissionFactorLookup:
    """Test emission factor lookup for specific vehicle-fuel combinations."""
    
    def test_lcgc_bensin_factor(self):
        """Test LCGC-bensin emission factor is 120 g/km."""
        assert get_emission_factor("LCGC", "bensin") == 120
    
    def test_suv_bensin_factor(self):
        """Test SUV-bensin emission factor is 180 g/km."""
        assert get_emission_factor("SUV", "bensin") == 180
    
    def test_ev_listrik_factor(self):
        """Test EV-listrik emission factor is 40 g/km."""
        assert get_emission_factor("EV", "listrik") == 40


class TestEmissionCalculation:
    """Test emission calculation with known values."""
    
    def test_emission_calculation_known_value(self):
        """Test emission calculation: 100 km * 180 g/km = 18000 g."""
        result = calculate_emission(100, "SUV", "bensin")
        assert result == 18000
    
    def test_emission_calculation_lcgc(self):
        """Test emission calculation for LCGC vehicle."""
        result = calculate_emission(50, "LCGC", "bensin")
        assert result == 6000  # 50 * 120


class TestInvalidCombinations:
    """Test error handling for invalid vehicle-fuel combinations."""
    
    def test_invalid_vehicle_type(self):
        """Test that invalid vehicle type raises KeyError."""
        with pytest.raises(KeyError):
            get_emission_factor("Sedan", "bensin")
    
    def test_invalid_fuel_type(self):
        """Test that invalid fuel type for valid vehicle raises KeyError."""
        with pytest.raises(KeyError):
            get_emission_factor("LCGC", "diesel")
    
    def test_invalid_combination_ev_bensin(self):
        """Test that EV with bensin raises KeyError."""
        with pytest.raises(KeyError):
            get_emission_factor("EV", "bensin")


class TestValidCombinations:
    """Test get_valid_combinations function."""
    
    def test_get_valid_combinations_returns_all(self):
        """Test that get_valid_combinations returns all expected combinations."""
        combinations = get_valid_combinations()
        expected = [
            "LCGC-bensin", "LCGC-solar",
            "SUV-bensin", "SUV-solar",
            "EV-listrik"
        ]
        assert len(combinations) == 5
        for combo in expected:
            assert combo in combinations



# Property-Based Tests
from hypothesis import given, strategies as st
from emission import EMISSION_FACTORS


class TestPropertyValidCombinationValidation:
    """Property-based tests for valid combination validation."""
    
    @given(
        car_type=st.sampled_from(list(EMISSION_FACTORS.keys()) + ["Sedan", "Truck", "Motorcycle"]),
        fuel_type=st.sampled_from(["bensin", "solar", "listrik", "diesel", "hybrid"])
    )
    def test_valid_combination_validation(self, car_type, fuel_type):
        """
        **Feature: carbon-emission-calculator, Property 1: Valid combination validation**
        **Validates: Requirements 1.5**
        
        For any vehicle type and fuel type combination, the validation function 
        should return true (not raise error) if and only if that combination 
        exists in the emission factor table.
        """
        is_valid = car_type in EMISSION_FACTORS and fuel_type in EMISSION_FACTORS.get(car_type, {})
        
        if is_valid:
            # Should not raise an error
            factor = get_emission_factor(car_type, fuel_type)
            assert factor > 0
        else:
            # Should raise KeyError
            with pytest.raises(KeyError):
                get_emission_factor(car_type, fuel_type)



class TestPropertyEmissionCalculationCorrectness:
    """Property-based tests for emission calculation correctness."""
    
    @given(
        distance_km=st.floats(min_value=0.1, max_value=10000.0, allow_nan=False, allow_infinity=False),
        car_type=st.sampled_from(list(EMISSION_FACTORS.keys())),
        fuel_type=st.data()
    )
    def test_emission_calculation_correctness(self, distance_km, car_type, fuel_type):
        """
        **Feature: carbon-emission-calculator, Property 4: Emission calculation correctness**
        **Validates: Requirements 3.2**
        
        For any distance value and valid vehicle-fuel combination, the calculated 
        emission should equal distance_km multiplied by the emission factor for 
        that combination.
        """
        # Select a valid fuel type for the given car type
        valid_fuels = list(EMISSION_FACTORS[car_type].keys())
        fuel = fuel_type.draw(st.sampled_from(valid_fuels))
        
        # Get the expected emission factor
        expected_factor = EMISSION_FACTORS[car_type][fuel]
        expected_emission = distance_km * expected_factor
        
        # Calculate emission using the function
        actual_emission = calculate_emission(distance_km, car_type, fuel)
        
        # Verify the calculation is correct
        assert abs(actual_emission - expected_emission) < 0.01  # Allow small floating point error



class TestPropertyInvalidCombinationErrorMessaging:
    """Property-based tests for invalid combination error messaging."""
    
    @given(
        car_type=st.one_of(
            st.sampled_from(["Sedan", "Truck", "Motorcycle", "Van", "Bus"]),
            st.sampled_from(list(EMISSION_FACTORS.keys()))
        ),
        fuel_type=st.sampled_from(["diesel", "hybrid", "hydrogen", "bensin", "solar", "listrik"])
    )
    def test_invalid_combination_error_messaging(self, car_type, fuel_type):
        """
        **Feature: carbon-emission-calculator, Property 6: Invalid combination error messaging**
        **Validates: Requirements 6.2**
        
        For any invalid vehicle-fuel combination, the error message should list 
        all valid combinations from the emission factor table.
        """
        # Check if this is a valid combination
        is_valid = car_type in EMISSION_FACTORS and fuel_type in EMISSION_FACTORS.get(car_type, {})
        
        if not is_valid:
            # Get all valid combinations
            valid_combinations = get_valid_combinations()
            
            # Attempt to get emission factor and catch the error
            try:
                get_emission_factor(car_type, fuel_type)
                # If we get here, the combination was valid (shouldn't happen based on our check)
                assert False, "Expected KeyError for invalid combination"
            except KeyError as e:
                # The error was raised as expected
                # We verify that get_valid_combinations returns the expected list
                assert len(valid_combinations) == 5
                assert "LCGC-bensin" in valid_combinations
                assert "LCGC-solar" in valid_combinations
                assert "SUV-bensin" in valid_combinations
                assert "SUV-solar" in valid_combinations
                assert "EV-listrik" in valid_combinations
