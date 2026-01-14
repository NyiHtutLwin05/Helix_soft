# 🏥 Clinical Data Processor (HelixSoft Avalon)

A secure, desktop-based clinical CSV file processing system built with **Python + Tkinter**, designed to connect to an **FTP server**, validate clinical trial data, and manage files using **Test-Driven Development (TDD)** principles.

This project demonstrates:
- Clean architecture
- Decorator Pattern
- Robust validation logic
- API integration with fallback
- GUI usability principles (Nielsen & Shneiderman)
- Automated testing with **pytest**

---

## ✨ Features

### 🔗 FTP Integration
- Connects securely to an FTP server
- Lists available `.CSV` files
- Supports passive FTP mode

### 📂 File Operations
- **Validate** files without downloading
- **Process** files (download → validate → archive or reject)
- **Download** files with standardized naming

### ✅ Validation Rules
- Filename pattern enforcement  

###

###
CLINICALDATA_YYYYMMDDHHMMSS.CSV

- CSV header validation
- Field count and data type checks
- Date consistency checks
- Duplicate record detection
- Outcome value validation

### 🧩 Design Patterns
- **Decorator Pattern** for error handling
- Timestamp
- GUID (UUID v4)
- File context
- Fallback UUID generation if API fails

### 🧪 Test-Driven Development
- RED → GREEN → REFACTOR workflow
- Isolated unit tests
- API mocking
- Temporary filesystem usage

### 🖥️ Modern GUI
- Tkinter + ttk (modern theme)
- Searchable file list
- Progress indicators
- Color-coded logs
- Error log viewer


---

## 🧱 Requirements

- Python **3.9+**
- Internet connection (for UUID API – optional fallback exists)

### Python Packages
```bash
pip install requests pytest
```

###  🧪 Running Tests

All tests are written using pytest.

```bash
pytest test_clinical_data_validator.py
```

Tested Components

Filename validation

UUID generation (API + fallback)

Error logging format and persistence


🧠 TDD Strategy

Defined in test_plan.md:

🔴 RED

Write failing tests

Break filename validation intentionally

🟢 GREEN

Implement minimum logic

Mock API calls

Pass all tests

🔵 REFACTOR

Improve error handling

Optimize validation logic

Maintain passing tests

🔐 Error Handling

Errors are logged using a decorated handler that adds:

Timestamp

GUID (from external API or local fallback)

File context

📄 Error logs are stored at:

~/ClinicalData/Errors/error_report.log

📊 CSV Format Specification
Expected Header
PatientID,TrialCode,DrugCode,Dosage_mg,StartDate,EndDate,Outcome,SideEffects,Analyst

Validation Rules

Dosage_mg must be a positive integer

Dates must follow YYYY-MM-DD

EndDate ≥ StartDate

Outcome must be:

Improved

No Change

Worsened

🎯 Educational Value

This project is ideal for demonstrating:

GUI-based Python applications

FTP file handling

Clean architecture

Design patterns

TDD with pytest

API resilience strategies

📜 License

This project is for educational and demonstration purposes.
You are free to modify and extend it.

👤 Author

HelixSoft Avalon
Clinical Data Processing System
Built with care, structure, and testing ❤️

If you want, I can also generate:

🔹 Architecture diagram

🔹 UML class diagram

🔹 GitHub badges

🔹 Installation screenshots

🔹 Academic-style project report

