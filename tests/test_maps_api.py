"""Unit tests for OpenStreetMap API client module."""
import pytest
from unittest.mock import patch, Mock
from maps_api import get_distance


class TestSuccessfulAPIResponse:
    """Test successful API response parsing."""
    
    @patch('maps_api.requests.get')
    def test_successful_response_parsing(self, mock_get):
        """Test successful API response parsing with sample JSON."""
        # Mock geocoding responses
        geocode_response = Mock()
        geocode_response.status_code = 200
        geocode_response.json.return_value = [
            {'lat': '-6.2088', 'lon': '106.8456'}
        ]
        
        # Mock routing response
        routing_response = Mock()
        routing_response.status_code = 200
        routing_response.json.return_value = {
            'code': 'Ok',
            'routes': [{
                'distance': 150500  # meters
            }]
        }
        
        # Set up mock to return different responses for geocoding and routing
        mock_get.side_effect = [geocode_response, geocode_response, routing_response]
        
        # Call function
        distance = get_distance('Jakarta', 'Bandung')
        
        # Verify result
        assert distance == 150.5
        
        # Verify API was called 3 times (2 geocoding + 1 routing)
        assert mock_get.call_count == 3


class TestDistanceConversion:
    """Test meter to kilometer conversion."""
    
    @patch('maps_api.requests.get')
    def test_meter_to_kilometer_conversion(self, mock_get):
        """Test meter to kilometer conversion (e.g., 5000 m = 5.0 km)."""
        # Mock geocoding responses
        geocode_response = Mock()
        geocode_response.status_code = 200
        geocode_response.json.return_value = [
            {'lat': '-6.2088', 'lon': '106.8456'}
        ]
        
        # Mock routing response with 5000 meters
        routing_response = Mock()
        routing_response.status_code = 200
        routing_response.json.return_value = {
            'code': 'Ok',
            'routes': [{
                'distance': 5000  # meters
            }]
        }
        
        mock_get.side_effect = [geocode_response, geocode_response, routing_response]
        
        # Call function
        distance = get_distance('Location A', 'Location B')
        
        # Verify conversion: 5000 meters = 5.0 km
        assert distance == 5.0


class TestGeocodingErrors:
    """Test error handling when geocoding fails."""
    
    @patch('maps_api.requests.get')
    def test_address_not_found_error(self, mock_get):
        """Test error handling when address cannot be geocoded."""
        # Mock empty geocoding response
        geocode_response = Mock()
        geocode_response.status_code = 200
        geocode_response.json.return_value = []
        
        mock_get.return_value = geocode_response
        
        # Verify exception is raised with descriptive message
        with pytest.raises(Exception) as exc_info:
            get_distance('InvalidAddress123', 'Bandung')
        
        assert 'tidak ditemukan' in str(exc_info.value)
    
    @patch('maps_api.requests.get')
    def test_geocoding_timeout_error(self, mock_getenv):
        """Test error handling when geocoding times out."""
        # Mock timeout exception
        mock_getenv.side_effect = __import__('requests').exceptions.Timeout()
        
        # Verify exception is raised
        with pytest.raises(Exception) as exc_info:
            get_distance('Jakarta', 'Bandung')
        
        assert 'timeout' in str(exc_info.value)


class TestRoutingErrorStatus:
    """Test error handling when routing API returns error status."""
    
    @patch('maps_api.requests.get')
    def test_routing_error_status(self, mock_get):
        """Test error handling when routing returns error status."""
        # Mock successful geocoding
        geocode_response = Mock()
        geocode_response.status_code = 200
        geocode_response.json.return_value = [
            {'lat': '-6.2088', 'lon': '106.8456'}
        ]
        
        # Mock routing response with error
        routing_response = Mock()
        routing_response.status_code = 200
        routing_response.json.return_value = {
            'code': 'NoRoute',
            'routes': []
        }
        
        mock_get.side_effect = [geocode_response, geocode_response, routing_response]
        
        # Verify exception is raised
        with pytest.raises(Exception) as exc_info:
            get_distance('Invalid', 'Address')
        
        assert 'Tidak dapat menghitung rute' in str(exc_info.value)
    
    @patch('maps_api.requests.get')
    def test_no_routes_found(self, mock_get):
        """Test error handling when no route is found."""
        # Mock successful geocoding
        geocode_response = Mock()
        geocode_response.status_code = 200
        geocode_response.json.return_value = [
            {'lat': '-6.2088', 'lon': '106.8456'}
        ]
        
        # Mock routing response with no routes
        routing_response = Mock()
        routing_response.status_code = 200
        routing_response.json.return_value = {
            'code': 'Ok',
            'routes': []
        }
        
        mock_get.side_effect = [geocode_response, geocode_response, routing_response]
        
        # Verify exception is raised
        with pytest.raises(Exception) as exc_info:
            get_distance('Invalid', 'Address')
        
        assert 'Tidak ada rute ditemukan' in str(exc_info.value)
    
    @patch('maps_api.requests.get')
    def test_missing_distance_data(self, mock_get):
        """Test error handling when distance data is missing."""
        # Mock successful geocoding
        geocode_response = Mock()
        geocode_response.status_code = 200
        geocode_response.json.return_value = [
            {'lat': '-6.2088', 'lon': '106.8456'}
        ]
        
        # Mock routing response with missing distance
        routing_response = Mock()
        routing_response.status_code = 200
        routing_response.json.return_value = {
            'code': 'Ok',
            'routes': [{}]  # Route without distance field
        }
        
        mock_get.side_effect = [geocode_response, geocode_response, routing_response]
        
        # Verify exception is raised
        with pytest.raises(Exception) as exc_info:
            get_distance('Nonexistent', 'Address')
        
        assert 'Format respons tidak valid' in str(exc_info.value)


class TestNetworkFailures:
    """Test error handling for network failures."""
    
    @patch('maps_api.requests.get')
    def test_routing_timeout_error(self, mock_get):
        """Test error handling for routing timeout."""
        # Mock successful geocoding
        geocode_response = Mock()
        geocode_response.status_code = 200
        geocode_response.json.return_value = [
            {'lat': '-6.2088', 'lon': '106.8456'}
        ]
        
        # Mock timeout exception on routing call
        mock_get.side_effect = [
            geocode_response, 
            geocode_response, 
            __import__('requests').exceptions.Timeout()
        ]
        
        # Verify exception is raised with descriptive message
        with pytest.raises(Exception) as exc_info:
            get_distance('Jakarta', 'Bandung')
        
        assert 'timeout' in str(exc_info.value)
    
    @patch('maps_api.requests.get')
    def test_connection_error(self, mock_get):
        """Test error handling for connection error."""
        # Mock connection exception
        mock_get.side_effect = __import__('requests').exceptions.ConnectionError()
        
        # Verify exception is raised with descriptive message
        with pytest.raises(Exception) as exc_info:
            get_distance('Jakarta', 'Bandung')
        
        assert 'Tidak dapat terhubung' in str(exc_info.value)



# Property-Based Tests
from hypothesis import given, strategies as st


class TestPropertyDistanceExtractionAndConversion:
    """Property-based tests for distance extraction and conversion."""
    
    @given(distance_meters=st.integers(min_value=1, max_value=10000000))
    @patch('maps_api.requests.get')
    def test_distance_extraction_and_conversion(self, mock_get, distance_meters):
        """
        **Feature: carbon-emission-calculator, Property 3: Distance extraction and conversion**
        **Validates: Requirements 2.2, 2.3**
        
        For any valid API response containing distance in meters, the extracted 
        distance in kilometers should equal the meter value divided by 1000.
        """
        # Mock geocoding responses
        geocode_response = Mock()
        geocode_response.status_code = 200
        geocode_response.json.return_value = [
            {'lat': '-6.2088', 'lon': '106.8456'}
        ]
        
        # Mock routing response with random meter value
        routing_response = Mock()
        routing_response.status_code = 200
        routing_response.json.return_value = {
            'code': 'Ok',
            'routes': [{
                'distance': distance_meters
            }]
        }
        
        mock_get.side_effect = [geocode_response, geocode_response, routing_response]
        
        # Call function
        distance_km = get_distance('Origin', 'Destination')
        
        # Verify conversion: meters / 1000 = kilometers
        expected_km = distance_meters / 1000.0
        assert abs(distance_km - expected_km) < 0.001  # Allow small floating point error



class TestPropertyAPICallParameters:
    """Property-based tests for API call parameters."""
    
    @given(
        origin=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',))),
        destination=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',)))
    )
    @patch('maps_api.requests.get')
    def test_api_call_with_correct_parameters(self, mock_get, origin, destination):
        """
        **Feature: carbon-emission-calculator, Property 2: API call with correct parameters**
        **Validates: Requirements 2.1**
        
        For any pair of origin and destination addresses, when calling the 
        OpenStreetMap API, the request should geocode both addresses.
        """
        # Mock geocoding responses
        geocode_response = Mock()
        geocode_response.status_code = 200
        geocode_response.json.return_value = [
            {'lat': '-6.2088', 'lon': '106.8456'}
        ]
        
        # Mock routing response
        routing_response = Mock()
        routing_response.status_code = 200
        routing_response.json.return_value = {
            'code': 'Ok',
            'routes': [{
                'distance': 10000
            }]
        }
        
        mock_get.side_effect = [geocode_response, geocode_response, routing_response]
        
        # Call function
        get_distance(origin, destination)
        
        # Verify API was called 3 times (2 geocoding + 1 routing)
        assert mock_get.call_count == 3
        
        # Check that first two calls were geocoding with origin and destination
        first_call_params = mock_get.call_args_list[0][1]['params']
        second_call_params = mock_get.call_args_list[1][1]['params']
        
        assert first_call_params['q'] == origin
        assert second_call_params['q'] == destination
