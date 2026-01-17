import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helixsoft_avalon import ClinicalDataProcessor
from unittest.mock import Mock


def test_get_file_list():
    """Test successful CSV file retrieval from FTP"""
    processor = ClinicalDataProcessor("test", "user", "pass")
    processor.ftp = Mock()
    processor.connected = True
    
    processor.ftp.nlst.return_value = [
        "CLINICALDATA_20250115120000.csv",
        "report.pdf",
        "data.CSV",
        "notes.txt"
    ]
    
    mock_queue = Mock()

    result = processor.get_file_list(mock_queue)
    
    # Assertions
    assert result == ["CLINICALDATA_20250115120000.csv", "data.CSV"]
    processor.ftp.nlst.assert_called_once()
    mock_queue.put.assert_called_with(("Found 2 CSV files", "success"))
    print("Test passed: get_file_list filters CSV files correctly")