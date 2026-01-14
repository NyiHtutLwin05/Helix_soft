import pytest
import requests
from unittest.mock import patch, Mock
import sys
import os
import uuid

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from helixsoft_avalon import UUIDGenerator  
    IMPORT_SUCCESS = True
    print("✓ Successfully imported UUIDGenerator from helixsoft_avalon")
except ImportError as e:
    print(f"Warning: Could not import from helixsoft_avalon: {e}")
    print("Creating mock UUIDGenerator for testing...")
    IMPORT_SUCCESS = False
    
    class UUIDGenerator:
        @staticmethod
        def get_guid_from_api():
            return str(uuid.uuid4())


class TestUUIDAPI:
    """Test cases for UUID API integration"""
    
    def test_api_connectivity(self):
        """Test that we can connect to the UUID API"""
        try:
            response = requests.get("https://www.uuidtools.com/api/generate/v4", timeout=10)
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            print("✓ API connectivity test passed")
        except requests.RequestException as e:
            pytest.skip(f"API not available: {e}")
    
    def test_api_response_format(self):
        """Test that API returns valid UUID format"""
        try:
            response = requests.get("https://www.uuidtools.com/api/generate/v4", timeout=10)
            data = response.json()
            
            # API returns a list with one UUID string
            assert isinstance(data, list), "API should return a list"
            assert len(data) > 0, "API list should not be empty"
            
            uuid_str = data[0]
            # Check UUID format (version 4)
            assert len(uuid_str) == 36, f"UUID should be 36 chars, got {len(uuid_str)}"
            assert uuid_str[14] == '4', "Should be UUID version 4"
            assert uuid_str[19] in ['8', '9', 'a', 'b'], "Should have correct variant"
            
            print(f"✓ API response format test passed: {uuid_str}")
        except requests.RequestException as e:
            pytest.skip(f"API not available: {e}")
    
    def test_uuid_generator_class(self):
        """Test the UUIDGenerator class - calling static method correctly"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["bbe77b81-5a21-426f-b2bf-99df83c163e1"]
        
        # Patch requests.get globally since UUIDGenerator.get_guid_from_api uses it
        with patch('requests.get', return_value=mock_response):
            # Call the static method correctly
            result = UUIDGenerator.get_guid_from_api()
            
            assert result == "bbe77b81-5a21-426f-b2bf-99df83c163e1"
            print("✓ UUIDGenerator API success test passed")
    
    def test_uuid_generator_fallback(self):
        """Test UUIDGenerator fallback when API fails"""
        # Test failed API response
        with patch('requests.get', side_effect=requests.RequestException("API Error")):
            # Mock uuid.uuid4 to return a known value
            with patch('uuid.uuid4', return_value=uuid.UUID('12345678-1234-5678-1234-567812345678')):
                result = UUIDGenerator.get_guid_from_api()
                
                assert result == "12345678-1234-5678-1234-567812345678"
                print("✓ UUIDGenerator fallback test passed")
    
    


if __name__ == "__main__":
    print("=" * 60)
    print("Running GUID API Integration Tests")
    print("=" * 60)
    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)