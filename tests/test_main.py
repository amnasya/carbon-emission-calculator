"""Unit tests for main command-line interface module."""
import pytest
from unittest.mock import patch, call
from main import get_user_input, display_results, main


class TestInputPromptSequence:
    """Test input prompt sequence (origin → destination → vehicle → fuel)."""
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_input_prompt_sequence(self, mock_print, mock_input):
        """Test that inputs are prompted in correct order."""
        # Mock user inputs
        mock_input.side_effect = [
            'Jakarta, Indonesia',
            'Bandung, Indonesia',
            'SUV',
            'bensin'
        ]
        
        # Call function
        origin, destination, car_type, fuel_type = get_user_input()
        
        # Verify results
        assert origin == 'Jakarta, Indonesia'
        assert destination == 'Bandung, Indonesia'
        assert car_type == 'SUV'
        assert fuel_type == 'bensin'
        
        # Verify prompts were in correct order
        input_calls = mock_input.call_args_list
        assert 'origin' in str(input_calls[0]).lower()
        assert 'destination' in str(input_calls[1]).lower()
        assert 'vehicle' in str(input_calls[2]).lower()
        assert 'fuel' in str(input_calls[3]).lower()
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_empty_input_validation(self, mock_print, mock_input):
        """Test that empty inputs are rejected and re-prompted."""
        # Mock user inputs with empty strings followed by valid inputs
        mock_input.side_effect = [
            '',  # Empty origin
            'Jakarta',  # Valid origin
            '   ',  # Whitespace-only destination
            'Bandung',  # Valid destination
            'SUV',
            'bensin'
        ]
        
        # Call function
        origin, destination, car_type, fuel_type = get_user_input()
        
        # Verify results
        assert origin == 'Jakarta'
        assert destination == 'Bandung'
        assert car_type == 'SUV'
        assert fuel_type == 'bensin'
        
        # Verify error messages were shown
        print_calls = [str(call) for call in mock_print.call_args_list]
        error_messages = [c for c in print_calls if 'Error' in c or 'empty' in c]
        assert len(error_messages) >= 2  # At least 2 error messages


class TestOutputFormatting:
    """Test output formatting contains distance, emission, and summary."""
    
    @patch('builtins.print')
    def test_output_contains_distance(self, mock_print):
        """Test that output contains distance value."""
        display_results(150.5, 27090.0, 'SUV', 'bensin')
        
        # Get all print calls
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ' '.join(print_calls)
        
        # Verify distance is displayed
        assert '150.5' in output or '150.50' in output
        assert 'km' in output.lower()
    
    @patch('builtins.print')
    def test_output_contains_emission_grams(self, mock_print):
        """Test that output contains emission in grams."""
        display_results(150.5, 27090.0, 'SUV', 'bensin')
        
        # Get all print calls
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ' '.join(print_calls)
        
        # Verify emission in grams is displayed
        assert '27,090' in output or '27090' in output
        assert 'g' in output
    
    @patch('builtins.print')
    def test_output_contains_emission_kg(self, mock_print):
        """Test that output contains emission in kg."""
        display_results(150.5, 27090.0, 'SUV', 'bensin')
        
        # Get all print calls
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ' '.join(print_calls)
        
        # Verify emission in kg is displayed
        assert '27.09' in output
        assert 'kg' in output.lower()
    
    @patch('builtins.print')
    def test_output_contains_summary(self, mock_print):
        """Test that output contains explanatory summary."""
        display_results(150.5, 27090.0, 'SUV', 'bensin')
        
        # Get all print calls
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ' '.join(print_calls).lower()
        
        # Verify summary contains key information
        assert 'trip' in output or 'journey' in output
        assert 'suv' in output
        assert 'bensin' in output
        assert 'emission' in output or 'carbon' in output


class TestErrorHandling:
    """Test error handling displays appropriate messages."""
    
    @patch('builtins.input')
    @patch('builtins.print')
    def test_invalid_combination_error(self, mock_print, mock_input):
        """Test that invalid vehicle-fuel combination shows error with valid options."""
        # Mock user inputs with invalid combination
        mock_input.side_effect = [
            'Jakarta',
            'Bandung',
            'EV',
            'bensin'  # Invalid: EV doesn't use bensin
        ]
        
        # Call main function
        main()
        
        # Get all print calls
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ' '.join(print_calls)
        
        # Verify error message is shown
        assert 'Error' in output or 'Invalid' in output
        assert 'Valid combinations' in output or 'valid' in output.lower()
    
    @patch('builtins.input')
    @patch('builtins.print')
    @patch('main.get_distance')
    def test_api_error_handling(self, mock_get_distance, mock_print, mock_input):
        """Test that API errors are displayed to user."""
        # Mock user inputs
        mock_input.side_effect = [
            'Invalid Address',
            'Another Invalid',
            'SUV',
            'bensin'
        ]
        
        # Mock API error
        mock_get_distance.side_effect = Exception("Error: Could not find addresses")
        
        # Call main function
        main()
        
        # Get all print calls
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ' '.join(print_calls)
        
        # Verify error message is displayed (supports both English and Indonesian)
        assert 'error' in output.lower()
        assert ('could not find' in output.lower() or 
                'addresses' in output.lower() or 
                'alamat' in output.lower() or 
                'tidak ditemukan' in output.lower())



# Property-Based Tests
from hypothesis import given, strategies as st
from emission import EMISSION_FACTORS


class TestPropertyCompleteOutputDisplay:
    """Property-based tests for complete output display."""
    
    @given(
        distance=st.floats(min_value=0.1, max_value=10000.0, allow_nan=False, allow_infinity=False),
        car_type=st.sampled_from(list(EMISSION_FACTORS.keys())),
        fuel_type=st.data()
    )
    @patch('builtins.print')
    def test_complete_output_display(self, mock_print, distance, car_type, fuel_type):
        """
        **Feature: carbon-emission-calculator, Property 5: Complete output display**
        **Validates: Requirements 3.3, 3.4, 3.5**
        
        For any calculated result, the displayed output should contain the distance 
        value, the emission value, and explanatory text describing the calculation.
        """
        # Select a valid fuel type for the given car type
        valid_fuels = list(EMISSION_FACTORS[car_type].keys())
        fuel = fuel_type.draw(st.sampled_from(valid_fuels))
        
        # Calculate emission
        emission_factor = EMISSION_FACTORS[car_type][fuel]
        emission = distance * emission_factor
        
        # Call display_results
        display_results(distance, emission, car_type, fuel)
        
        # Get all print calls
        print_calls = [str(call) for call in mock_print.call_args_list]
        output = ' '.join(print_calls).lower()
        
        # Verify distance value is present
        distance_str = f"{distance:.2f}"
        assert distance_str in output or distance_str.replace('.', ',') in output, \
            f"Distance {distance_str} not found in output"
        
        # Verify emission value is present (in grams or kg)
        emission_kg = emission / 1000.0
        emission_kg_str = f"{emission_kg:.2f}"
        assert emission_kg_str in output or str(int(emission)) in output, \
            f"Emission value not found in output"
        
        # Verify explanatory text is present
        assert 'trip' in output or 'journey' in output, \
            "Explanatory text about trip not found"
        assert 'emission' in output or 'carbon' in output, \
            "Explanatory text about emissions not found"
        assert car_type.lower() in output, \
            f"Vehicle type {car_type} not found in output"
        assert fuel.lower() in output, \
            f"Fuel type {fuel} not found in output"
