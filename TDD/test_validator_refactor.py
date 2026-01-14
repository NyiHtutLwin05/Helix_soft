"""
REFACTOR STAGE - Improved implementation with better structure
"""

import pytest
import tempfile
import os
import re
import uuid
import requests
from datetime import datetime
from unittest.mock import patch, Mock
from dataclasses import dataclass
from typing import List, Tuple, Optional

# ============================================
# REFACTORED IMPLEMENTATION
# ============================================

@dataclass
class ValidationResult:
    """Data class for validation results"""
    is_valid: bool
    errors: List[str]
    record_count: int = 0


class UUIDGenerator:
    """Refactored UUID generator with better error handling"""
    
    @staticmethod
    def get_guid(use_api=True):
        """Get UUID from API or local generator"""
        if use_api:
            try:
                response = requests.get(
                    "https://www.uuidtools.com/api/generate/v4",
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and data:
                        return data[0]
            except:
                pass  # Fall through to local generation
        
        # Local fallback
        return str(uuid.uuid4())


class CSVValidator:
    """Refactored validator class with better structure"""
    
    EXPECTED_HEADER = [
        "PatientID", "TrialCode", "DrugCode", "Dosage_mg",
        "StartDate", "EndDate", "Outcome", "SideEffects", "Analyst"
    ]
    
    VALID_OUTCOMES = {"Improved", "No Change", "Worsened"}
    
    def __init__(self):
        self.uuid_generator = UUIDGenerator()
    
    def validate_filename(self, filename: str) -> bool:
        """Validate filename pattern"""
        pattern = r'^CLINICALDATA_\d{14}\.csv$'
        return bool(re.match(pattern, filename, re.IGNORECASE))
    
    def validate_csv(self, filepath: str) -> ValidationResult:
        """Validate CSV content with detailed error reporting"""
        errors = []
        record_count = 0
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                
                try:
                    header = next(reader)
                    if header != self.EXPECTED_HEADER:
                        errors.append(f"Invalid header. Expected: {self.EXPECTED_HEADER}")
                        return ValidationResult(False, errors, 0)
                except StopIteration:
                    errors.append("File is empty")
                    return ValidationResult(False, errors, 0)
                
                for i, row in enumerate(reader, 1):
                    record_count += 1
                    
                    # Check row length
                    if len(row) != 9:
                        errors.append(f"Row {i}: Expected 9 fields, got {len(row)}")
                        continue
                    
                    # Check for empty required fields
                    if any(not field.strip() for field in row[:9]):
                        errors.append(f"Row {i}: Missing required fields")
                        continue
                    
                    # Validate dosage
                    try:
                        dosage = int(row[3])
                        if dosage <= 0:
                            errors.append(f"Row {i}: Dosage must be positive")
                    except ValueError:
                        errors.append(f"Row {i}: Dosage must be a number")
                    
                    # Validate dates
                    try:
                        start_date = datetime.strptime(row[4], "%Y-%m-%d")
                        end_date = datetime.strptime(row[5], "%Y-%m-%d")
                        if end_date < start_date:
                            errors.append(f"Row {i}: End date before start date")
                    except ValueError:
                        errors.append(f"Row {i}: Invalid date format")
                    
                    # Validate outcome
                    if row[6] not in self.VALID_OUTCOMES:
                        errors.append(f"Row {i}: Invalid outcome '{row[6]}'. Must be one of: {self.VALID_OUTCOMES}")
                
            return ValidationResult(len(errors) == 0, errors, record_count)
            
        except Exception as e:
            return ValidationResult(False, [f"File read error: {str(e)}"], 0)
    
    def log_error(self, filename: str, error_details: str, use_api=True) -> str:
        """Log error with API UUID"""
        guid = self.uuid_generator.get_guid(use_api)
        timestamp = datetime.now().isoformat()
        
        log_entry = f"[{timestamp}] GUID: {guid} | File: {filename} | Error: {error_details}"
        
        # In real implementation, write to file
        print(f"LOG: {log_entry}")
        
        return log_entry


# ============================================
# REFACTORED TESTS
# ============================================

class TestCSVValidator:
    """Refactored test class"""
    
    def setup_method(self):
        self.validator = CSVValidator()
    
    def test_validate_filename_refactored(self):
        """Test filename validation with edge cases"""
        test_cases = [
            ("CLINICALDATA_20250114123045.csv", True),
            ("CLINICALDATA_20250114123045.CSV", True),  # uppercase
            ("clinicaldata_20250114123045.csv", True),  # lowercase
            ("wrongname.csv", False),
            ("CLINICALDATA_2025.csv", False),  # wrong format
            ("", False),  # empty
            (None, False),  # None
        ]
        
        for filename, expected in test_cases:
            result = self.validator.validate_filename(filename if filename else "")
            assert result == expected, f"Failed for: {filename}"
    
    
    @patch('requests.get')
    def test_log_error_with_api_mock(self, mock_get):
        """Test error logging with mocked API"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["test-uuid-1234"]
        mock_get.return_value = mock_response
        
        filename = "test.csv"
        error_msg = "Validation failed"
        
        log_entry = self.validator.log_error(filename, error_msg, use_api=True)
        
        assert "GUID:" in log_entry
        assert "test-uuid-1234" in log_entry
        assert filename in log_entry
        assert error_msg in log_entry
    
    def test_log_error_without_api(self):
        """Test error logging without API (local fallback)"""
        filename = "test.csv"
        error_msg = "Validation failed"
        
        log_entry = self.validator.log_error(filename, error_msg, use_api=False)
        
        assert "GUID:" in log_entry
        assert filename in log_entry
        assert error_msg in log_entry
        # Should contain a UUID (36 characters with hyphens)
        guid_part = log_entry.split("GUID: ")[1].split(" |")[0]
        assert len(guid_part) == 36
        assert guid_part.count('-') == 4


# ============================================
# RUN REFACTORED TESTS
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("REFACTOR STAGE TESTS")
    print("=" * 60)
    
    # Import csv module for refactored tests
    import csv
    
    # Run pytest programmatically
    test_instance = TestCSVValidator()
    
    tests = [
        ("Filename Validation", test_instance.test_validate_filename_refactored),
        ("CSV Validation", test_instance.test_validate_csv_refactored),
        ("Error Logging with API", test_instance.test_log_error_with_api_mock),
        ("Error Logging without API", test_instance.test_log_error_without_api),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        try:
            test_instance.setup_method()
            test_func()
            print(f"  ✅ PASSED")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"REFACTOR RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ REFACTOR STAGE COMPLETE: All tests passed!")
        print("✅ Code has been refactored with better structure")
    else:
        print("❌ Some tests failed during refactoring")
    
    print("=" * 60)