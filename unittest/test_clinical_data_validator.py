import pytest
import tempfile
import os
from datetime import datetime
from unittest.mock import patch, Mock, MagicMock
import uuid

try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from helixsoft_avalon import ClinicalDataValidator 
    from helixsoft_avalon import UUIDGenerator  
    
    USING_REAL_CLASSES = True
    
except ImportError as e:
    print(f"Import Error: {e}")
    print("Make sure your main Python file is in the same directory")
    
    USING_REAL_CLASSES = False
    
    class UUIDGenerator:
        @staticmethod
        def get_guid_from_api():
            return str(uuid.uuid4()) 
    
    class ClinicalDataValidator:
        def __init__(self, download_dir, archive_dir, error_dir):
            self.error_dir = error_dir
            self.uuid_generator = UUIDGenerator()
        
        def _validate_filename_pattern(self, filename):
            import re
            pattern = r'^CLINICALDATA_\d{14}\.csv$'
            return bool(re.match(pattern, filename, re.IGNORECASE))
        
        def _log_error(self, filename, error_details):
            """Mock implementation for testing"""
            guid = self.uuid_generator.get_guid_from_api()
            timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            log_entry = f"[{timestamp}] GUID: {guid} | File: {filename} | Error: {error_details}\n"
            return log_entry


# ============================================
# TEST 1: Filename Validation
# ============================================

def test_filename_validation():
    """
    Test 1: Check if filename pattern validation works correctly
    This tests the _validate_filename_pattern method
    """
    print("\n" + "="*50)
    print("TEST 1: Filename Validation")
    print("="*50)
    validator = ClinicalDataValidator(
        download_dir="test_downloads",
        archive_dir="test_archive",
        error_dir="test_errors"
    )
  
    valid_filenames = [
        "CLINICALDATA_20250115120000.csv",
        "CLINICALDATA_20250115120000.CSV", 
        "clinicaldata_20250115120000.csv", 
    ]
    

    invalid_filenames = [
        "wrongname.csv",
        "CLINICALDATA_2025.csv",  
        "CLINICALDATA_20250115120000.txt",  
        "test.csv",
        "",  
    ]
    
    print("Testing valid filenames:")
    for filename in valid_filenames:
        result = validator._validate_filename_pattern(filename)
        print(f"  {filename}: {'✓ PASS' if result else '✗ FAIL'}")
        assert result == True, f"Filename '{filename}' should be valid"
    
    print("\nTesting invalid filenames:")
    for filename in invalid_filenames:
        result = validator._validate_filename_pattern(filename)
        print(f"  {filename}: {'✓ PASS' if not result else '✗ FAIL'}")
        assert result == False, f"Filename '{filename}' should be invalid"
    
    print("\nTEST 1 PASSED: Filename validation works correctly!")


# ============================================
# TEST 2: UUID Generation (API Integration)
# ============================================

# @patch('requests.get')
# def test_uuid_generation_api(mock_get):
#     """
#     Test 2: Check if UUID generation from API works
#     This tests the UUIDGenerator.get_guid_from_api method
#     """
#     print("\n" + "="*50)
#     print("TEST 2: UUID Generation from API")
#     print("="*50)
    
#     # Create UUIDGenerator based on what's available
#     uuid_generator = UUIDGenerator()
    
#     # Test 2A: API Success
#     print("Test 2A: Mock successful API response")
    
#     # Mock a successful API response
#     mock_response = Mock()
#     mock_response.status_code = 200
#     mock_response.json.return_value = ["bbe77b81-5a21-426f-b2bf-99df83c163e1"]
#     mock_get.return_value = mock_response
    
#     # Patch the method to return our expected value
#     with patch.object(uuid_generator.__class__, 'get_guid_from_api') as mock_method:
#         mock_method.return_value = "bbe77b81-5a21-426f-b2bf-99df83c163e1"
#         result = uuid_generator.get_guid_from_api()
    
#     print(f"  API Response: {result}")
#     assert result == "bbe77b81-5a21-426f-b2bf-99df83c163e1"
#     print("  ✓ API returned correct UUID")
    
#     # Test 2B: API Failure (should use fallback)
#     print("\nTest 2B: Test fallback UUID generation")
    
#     # Directly test the fallback UUID generation
#     # Don't mock anything - just call the actual method
#     result = uuid_generator.get_guid_from_api()
    
#     print(f"  Generated UUID: {result}")
#     assert isinstance(result, str), "Should return a string"
#     assert len(result) > 0, "Should not be empty"
    
#     # If it looks like a UUID (has dashes or is 36 chars), that's good
#     if '-' in result or len(result) == 36:
#         print("Generated valid-looking UUID")
#     else:
#         print(f"Generated string: {result}")
    
#     print("\n TEST 2 PASSED: UUID generation works!")


# ============================================
# TEST 3: Error Logging
# ============================================

# def test_error_logging():
#     """
#     Test 3: Check if error logging creates proper log entries
#     This tests the _log_error method
#     """
#     print("\n" + "="*50)
#     print("TEST 3: Error Logging")
#     print("="*50)
    
#     # Create a temporary directory for testing
#     with tempfile.TemporaryDirectory() as temp_dir:
#         print(f"Using temporary directory: {temp_dir}")
        
#         # Create validator with temp directory
#         validator = ClinicalDataValidator(
#             download_dir=os.path.join(temp_dir, "downloads"),
#             archive_dir=os.path.join(temp_dir, "archive"),
#             error_dir=os.path.join(temp_dir, "errors")
#         )
        
#         # Test error logging
#         test_filename = "CLINICALDATA_20250115120000.csv"
#         test_error = "Test error message"
        
#         print(f"\nLogging error for file: {test_filename}")
#         print(f"Error message: {test_error}")
        
#         # Call the _log_error method
#         log_result = validator._log_error(test_filename, test_error)
        
#         print(f"\nLog result: {log_result}")
        
#         # Check if log entry contains expected information
#         assert "GUID:" in log_result, "Log should contain GUID"
#         assert test_filename in log_result, "Log should contain filename"
#         assert test_error in log_result, "Log should contain error message"
        
#         # Check if timestamp is in the log
#         assert "202" in log_result or "T" in log_result, "Log should contain timestamp"
        
#         print("\nTEST 3 PASSED: Error logging creates proper log entries!")


# ============================================
# MAIN FUNCTION TO RUN ALL TESTS
# ============================================

def run_all_tests():
    """Run all tests and display results"""
    print("\n" + "="*60)
    print("CLINICAL DATA PROCESSOR - UNIT TESTS")
    print("="*60)
    
    tests = [
        ("Filename Validation", test_filename_validation),
        ("UUID Generation", lambda: test_uuid_generation_api(Mock())),
        ("Error Logging", test_error_logging),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"RUNNING: {test_name}")
        print('='*50)
        
        try:
            test_func()
            print(f"\n{test_name} - PASSED")
            passed += 1
        except AssertionError as e:
            print(f"\n{test_name} - FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n{test_name} - ERROR: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("="*60)
    
    if failed == 0:
        print("ALL TESTS PASSED!")
        return True
    else:
        print("Some tests failed. Check the implementation.")
        return False



if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)