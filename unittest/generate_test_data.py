import csv
import random

def generate_test_files():
    header = ["PatientID", "TrialCode", "DrugCode", "Dosage_mg",
              "StartDate", "EndDate", "Outcome", "SideEffects", "Analyst"]
    
    print("Generating test files...")
    print("-" * 40)
    
    # Valid file
    with open('valid.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for i in range(5):
            writer.writerow([
                f"P{i+1000}", f"T{i+1:03d}", "DRUG001",
                random.randint(1, 500), "2024-01-15", "2024-12-31",
                random.choice(["Improved", "No Change", "Worsened"]),
                "None", "Analyst1"
            ])
    print("✓ valid.csv created (5 valid records)")
    
    # Invalid file with errors
    with open('invalid.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        # Negative dosage
        writer.writerow(["P1001", "T001", "DRUG001", -50, "2024-01-15", "2024-12-31", "Improved", "None", "Analyst1"])
        
        # Invalid outcome
        writer.writerow(["P1002", "T002", "DRUG001", 100, "2024-01-15", "2024-12-31", "Invalid", "None", "Analyst1"])
        
        # End date before start date
        writer.writerow(["P1003", "T003", "DRUG001", 150, "2024-12-31", "2024-01-15", "Improved", "None", "Analyst1"])
        
        # Missing Analyst field
        writer.writerow(["P1004", "T004", "DRUG001", 200, "2024-01-15", "2024-12-31", "Improved", "None", ""])
        
        # Duplicate record
        writer.writerow(["P1001", "T001", "DRUG001", 250, "2024-01-15", "2024-12-31", "No Change", "None", "Analyst2"])
    
    print("✓ invalid.csv created (5 invalid records)")
    print("\nError types in invalid.csv:")
    print("  1. Negative dosage (-50)")
    print("  2. Invalid outcome ('Invalid')")
    print("  3. End date before start date")
    print("  4. Missing Analyst field")
    print("  5. Duplicate record (P1001, T001, DRUG001)")
    
    # Test filename patterns
    with open('CLINICALDATA_20250115120000.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["PatientID"])
        writer.writerow(["TEST"])
    print("✓ CLINICALDATA_20250115120000.csv (correct filename)")
    
    with open('wrong_name.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["PatientID"])
        writer.writerow(["TEST"])
    print("✓ wrong_name.csv (incorrect filename)")
    
    print("-" * 40)
    print("Total: 4 test files generated")
    print("Use: python -m pytest test_validation.py")

if __name__ == "__main__":
    generate_test_files()