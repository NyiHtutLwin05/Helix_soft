import pytest
import requests
from unittest.mock import patch, Mock
import sys
import os
from helixsoft_avalon import UUIDGenerator  
from helixsoft_avalon import ClinicalDataValidator

# Add the parent directory to path to import your modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
        """Test the UUIDGenerator class"""
        # Mock import at the test level
        from unittest.mock import patch
        
        # Test successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["bbe77b81-5a21-426f-b2bf-99df83c163e1"]
        
        with patch('requests.get', return_value=mock_response):
            # Import here to avoid module loading issues
            
            generator = UUIDGenerator()
            result = generator.get_guid_from_api()
            
            assert result == "bbe77b81-5a21-426f-b2bf-99df83c163e1"
            print("✓ UUIDGenerator API success test passed")
    
    def test_uuid_generator_fallback(self):
        """Test UUIDGenerator fallback when API fails"""
        from unittest.mock import patch
        
        # Test failed API response
        with patch('requests.get', side_effect=requests.RequestException("API Error")):
            # Import here
            import uuid as uuid_module
            
            # Mock uuid4 to return a known value
            with patch.object(uuid_module, 'uuid4', return_value=uuid_module.UUID('12345678-1234-5678-1234-567812345678')):
                generator = UUIDGenerator()
                result = generator.get_guid_from_api()
                
                assert result == "12345678-1234-5678-1234-567812345678"
                print("✓ UUIDGenerator fallback test passed")
    
    def test_error_logging_with_api(self):
        """Test that error logging works with API GUID"""
        from unittest.mock import patch, mock_open
        
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["test-uuid-from-api-1234"]
        
        with patch('requests.get', return_value=mock_response):
            with patch('builtins.open', mock_open()) as mock_file:
                # Import here
                import tempfile
                import os
                
                # Create temp directories
                with tempfile.TemporaryDirectory() as tmpdir:
                    validator = ClinicalDataValidator(
                        os.path.join(tmpdir, "downloads"),
                        os.path.join(tmpdir, "archive"),
                        os.path.join(tmpdir, "errors")
                    )
                    
                    # Call _log_error
                    result = validator._log_error("test.csv", "Test error message")
                    
                    # Check that file was written
                    mock_file().write.assert_called()
                    
                    # Check that the log contains API GUID
                    assert "test-uuid-from-api-1234" in result
                    print("✓ Error logging with API GUID test passed")


def run_all_tests():
    """Run all tests and print summary"""
    print("=" * 60)
    print("Running GUID API Integration Tests")
    print("=" * 60)
    
    test_instance = TestUUIDAPI()
    
    tests = [
        ("API Connectivity", test_instance.test_api_connectivity),
        ("API Response Format", test_instance.test_api_response_format),
        ("UUIDGenerator Class", test_instance.test_uuid_generator_class),
        ("UUIDGenerator Fallback", test_instance.test_uuid_generator_fallback),
        ("Error Logging with API", test_instance.test_error_logging_with_api),
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        try:
            test_func()
            passed += 1
            print(f"  Result: PASSED ✓")
        except pytest.skip.Exception as e:
            skipped += 1
            print(f"  Result: SKIPPED - {e}")
        except AssertionError as e:
            failed += 1
            print(f"  Result: FAILED ✗ - {e}")
        except Exception as e:
            failed += 1
            print(f"  Result: ERROR ✗ - {e}")
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY:")
    print(f"  Passed:  {passed}")
    print(f"  Failed:  {failed}")
    print(f"  Skipped: {skipped}")
    print("=" * 60)
    
    if failed == 0:
        print("All tests passed! ✓")
        return True
    else:
        print(f"{failed} test(s) failed!")
        return False


if __name__ == "__main__":
    # Simple test runner
    success = run_all_tests()
    
    if success:
        print("\n✅ GUID API integration is working correctly!")
    else:
        print("\n❌ Some tests failed. Check the implementation.")
        sys.exit(1)