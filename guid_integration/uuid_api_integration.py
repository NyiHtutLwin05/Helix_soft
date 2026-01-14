import requests
import json
from datetime import datetime
import uuid

class UUIDGenerator:
    """Handles UUID generation using external API with fallback"""
    
    def __init__(self):
        self.api_url = "https://www.uuidtools.com/api/generate/v4"
    
    def get_uuid(self):
        """Fetch a UUID v4 from external API with error handling"""
        try:
            response = requests.get(self.api_url, timeout=5)
            if response.status_code == 200:
                # API returns: ["uuid-string"] 
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    return data[0]
                elif isinstance(data, dict) and 'uuid' in data:
                    return data['uuid']
                else:
                    # Fallback to local UUID
                    return str(uuid.uuid4())
            else:
                # Fallback to local UUID
                return str(uuid.uuid4())
        except (requests.RequestException, ValueError, KeyError) as e:
            # Log the error and use local fallback
            print(f"API UUID generation failed: {e}. Using local UUID.")
            return str(uuid.uuid4())

def create_error_entry(error_msg, filename, log_file="error_report.log"):
    """Create an error log entry with timestamp and UUID"""
    timestamp = datetime.now().isoformat()
    uuid_gen = UUIDGenerator()
    error_uuid = uuid_gen.get_uuid()
    
    # Format the log entry
    log_entry = f"[{timestamp}] | UUID: {error_uuid} | File: {filename} | Error: {error_msg}"
    
    # Write to error_report.log
    with open(log_file, "a") as f:
        f.write(log_entry + "\n")
    
    print(f"✓ Log entry created and saved to {log_file}")
    return log_entry

def test_api_connectivity():
    """Test if the UUID API is accessible"""
    try:
        response = requests.get("https://www.uuidtools.com/api/generate/v4", timeout=10)
        if response.status_code == 200:
            print("✓ API connectivity test: PASSED")
            return True
        else:
            print(f"✗ API connectivity test: FAILED (Status: {response.status_code})")
            return False
    except requests.RequestException as e:
        print(f"✗ API connectivity test: FAILED ({e})")
        return False

def test_uuid_generation():
    """Test UUID generation (both API and fallback)"""
    print("\n" + "="*50)
    print("Testing UUID Generation")
    print("="*50)
    
    # Test API connectivity first
    if test_api_connectivity():
        print("\nGenerating UUID via API...")
        uuid_gen = UUIDGenerator()
        api_uuid = uuid_gen.get_uuid()
        print(f"API Generated UUID: {api_uuid}")
        print(f"Length: {len(api_uuid)} chars")
        print(f"Is valid UUID: {'Yes' if len(api_uuid) == 36 else 'No'}")
    else:
        print("\nAPI not available, testing fallback...")
        uuid_gen = UUIDGenerator()
        fallback_uuid = uuid_gen.get_uuid()
        print(f"Fallback Generated UUID: {fallback_uuid}")
    
    return True

def create_sample_error_entries():
    """Create sample error entries for testing"""
    print("\n" + "="*50)
    print("Creating Sample Error Entries")
    print("="*50)
    
    sample_errors = [
        ("Invalid dosage value: -10", "CLINICALDATA_20250115120000.csv"),
        ("Missing required field: Outcome", "CLINICALDATA_20250115123000.csv"),
        ("End date before start date", "CLINICALDATA_20250115130000.csv"),
        ("Invalid filename pattern", "test_file.csv"),
        ("Duplicate record detected", "CLINICALDATA_20250115140000.csv")
    ]
    
    for error_msg, filename in sample_errors:
        log_entry = create_error_entry(error_msg, filename)
        print(f"Created: {log_entry[:80]}...")

def view_error_log(log_file="error_report.log"):
    """View contents of error log file"""
    print("\n" + "="*50)
    print("Viewing Error Log Contents")
    print("="*50)
    
    try:
        with open(log_file, "r") as f:
            lines = f.readlines()
        
        if lines:
            print(f"Found {len(lines)} entries in {log_file}:")
            for i, line in enumerate(lines, 1):
                print(f"{i}. {line.strip()}")
        else:
            print(f"No entries found in {log_file}")
    except FileNotFoundError:
        print(f"Error log file '{log_file}' not found yet.")
    except Exception as e:
        print(f"Error reading log file: {e}")

def main():
    """Main function to run all tests"""
    print("="*50)
    print("UUID API Integration Test Script")
    print("="*50)
    
    # Run tests
    test_uuid_generation()

    create_sample_error_entries()

    view_error_log()
    
    print("\n" + "="*50)
    print("Test Complete!")
    print("="*50)
    print("\nCheck the 'error_report.log' file in your current directory.")
    print("Each entry contains:")
    print("  • ISO 8601 timestamp")
    print("  • Unique UUID (from API or local fallback)")
    print("  • Filename")
    print("  • Error description")

if __name__ == "__main__":
    main()