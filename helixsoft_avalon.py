import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import ftplib
import csv
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
import threading
import queue
import time
import random
import requests

# =============================================
# DECORATOR PATTERN IMPLEMENTATION for Error Handling
# =============================================


class ErrorHandler:
    """Base error handler component"""

    def handle_error(self, error_msg, filename=""):
        pass


class BasicErrorHandler(ErrorHandler):
    """Concrete component - basic error handling"""

    def handle_error(self, error_msg, filename=""):
        return f"Error: {error_msg}"


class ErrorHandlerDecorator(ErrorHandler):
    """Base decorator class"""

    def __init__(self, error_handler):
        self._error_handler = error_handler

    def handle_error(self, error_msg, filename=""):
        return self._error_handler.handle_error(error_msg, filename)


class TimestampErrorDecorator(ErrorHandlerDecorator):
    """Adds timestamp to error messages"""

    def handle_error(self, error_msg, filename=""):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        base_error = self._error_handler.handle_error(error_msg, filename)
        return f"[{timestamp}] {base_error}"
import requests

class UUIDGenerator:
    """Handles UUID generation using external API with fallback"""
    
    @staticmethod
    def get_guid_from_api():
        """Fetch a UUID v4 from external API with error handling"""
        try:
            response = requests.get("https://www.uuidtools.com/api/generate/v4", timeout=5)
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


class GUIDErrorDecorator(ErrorHandlerDecorator):
    """Adds GUID to error messages using external API"""
    
    def __init__(self, error_handler):
        super().__init__(error_handler)
        self.uuid_generator = UUIDGenerator()
    
    def handle_error(self, error_msg, filename=""):
        guid = self.uuid_generator.get_guid_from_api()
        base_error = self._error_handler.handle_error(error_msg, filename)
        return f"{base_error} | GUID: {guid}"


class FileContextErrorDecorator(ErrorHandlerDecorator):
    """Adds file context to error messages"""

    def handle_error(self, error_msg, filename=""):
        base_error = self._error_handler.handle_error(error_msg, filename)
        if filename:
            return f"{base_error} | File: {filename}"
        return base_error


def create_error_handler():
    """Creates a decorated error handler with timestamp, GUID, and file context"""
    handler = BasicErrorHandler()
    handler = TimestampErrorDecorator(handler)
    handler = GUIDErrorDecorator(handler)
    handler = FileContextErrorDecorator(handler)
    return handler

# =============================================
# MAIN APPLICATION
# =============================================


class ClinicalDataProcessor:
    """Handles FTP connection and file operations"""

    def __init__(self, ftp_host, ftp_user, ftp_pass, remote_dir=""):
        self.ftp_host = ftp_host
        self.ftp_user = ftp_user
        self.ftp_pass = ftp_pass
        self.remote_dir = remote_dir
        self.ftp = None
        self.connected = False

    def connect(self, status_queue=None):
        """Connect to FTP server with passive mode"""
        try:
            if self.ftp:
                try:
                    self.ftp.quit()
                except:
                    pass

            self.ftp = ftplib.FTP(self.ftp_host, timeout=30)
            self.ftp.set_pasv(True)
            self.ftp.login(self.ftp_user, self.ftp_pass)

            if self.remote_dir:
                try:
                    self.ftp.cwd(self.remote_dir)
                except:
                    if status_queue:
                        status_queue.put(
                            ("Warning: Could not change to remote directory", "warning"))

            self.connected = True
            if status_queue:
                status_queue.put(("FTP connection successful", "success"))
            return True
        except Exception as e:
            self.connected = False
            if status_queue:
                status_queue.put((f"Connection failed: {e}", "error"))
            return False

    def disconnect(self):
        """Safely disconnect from FTP"""
        if self.ftp:
            try:
                self.ftp.quit()
                self.connected = False
            except:
                pass

    def get_file_list(self, status_queue=None):
        """Get list of CSV files from server"""
        if not self.ftp or not self.connected:
            if status_queue:
                status_queue.put(("Not connected to FTP server", "error"))
            return []

        try:
            files = self.ftp.nlst()
            csv_files = [f for f in files if f.upper().endswith('.CSV')]

            if status_queue and csv_files:
                status_queue.put(
                    (f"Found {len(csv_files)} CSV files", "success"))
            elif status_queue:
                status_queue.put(("No CSV files found", "warning"))

            return sorted(csv_files)
        except Exception as e:
            if status_queue:
                status_queue.put(
                    (f"Failed to retrieve file list: {e}", "error"))
            return []

    def download_file_with_new_name(self, filename, local_dir, status_queue=None):
        """Download file with today's date in filename"""
        try:
            # Generate new filename with today's date
            today_date = datetime.now().strftime("%Y%m%d")
            base_name = filename.replace('.CSV', '').replace('.csv', '')
            new_filename = f"CLINICALDATA_{today_date}.CSV"
            local_path = Path(local_dir) / new_filename

            # Download file
            with open(local_path, 'wb') as f:
                self.ftp.retrbinary(f'RETR {filename}', f.write)

            if status_queue:
                status_queue.put((f"Downloaded as: {new_filename}", "success"))

            return local_path, new_filename
        except Exception as e:
            if status_queue:
                status_queue.put((f"Download failed: {e}", "error"))
            return None, None


class ClinicalDataValidator:
    """Handles file validation logic with Decorator Pattern error handling"""

    def __init__(self, download_dir, archive_dir, error_dir):
            self.download_dir = Path(download_dir)
            self.archive_dir = Path(archive_dir)
            self.error_dir = Path(error_dir)
            
            for directory in [self.download_dir, self.archive_dir, self.error_dir]:
                directory.mkdir(parents=True, exist_ok=True)
            
            self.processed_files_log = self.download_dir / "processed_files.txt"
            self.processed_files = self._load_processed_files()
            
            # Initialize decorated error handler
            self.error_handler = create_error_handler()
            
            # Add UUID generator
            self.uuid_generator = UUIDGenerator()

    def _load_processed_files(self):
        if self.processed_files_log.exists():
            return set(self.processed_files_log.read_text().splitlines())
        return set()

    def _save_processed_file(self, filename):
        self.processed_files.add(filename)
        self.processed_files_log.write_text(
            "\n".join(sorted(self.processed_files)))

    def _log_error(self, filename, error_details):
        """Uses the decorated error handler with API-based UUIDs"""
        try:
            # Get GUID from external API
            guid = self.uuid_generator.get_guid_from_api()
            
            timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            log_entry = f"[{timestamp}] GUID: {guid} | File: {filename} | Error: {error_details}\n"
            
            error_log_path = self.error_dir / "error_report.log"
            with open(error_log_path, "a", encoding='utf-8') as f:
                f.write(log_entry)
            
            # Also print to console for debugging
            print(f"Error logged with API GUID: {log_entry.strip()}")
            
            return log_entry
        except Exception as e:
            print(f"Failed to log error: {e}")
            return f"Logging failed: {e}\n"

    def _validate_filename_pattern(self, filename, status_queue=None):
        pattern = r'^CLINICALDATA_\d{14}\.CSV$'
        # TEMPORARILY BREAK THE CODE FOR RED STAGE
        is_valid = re.match(pattern, filename, re.IGNORECASE) is not None
        # is_valid = False  # Always return False to make tests fail
        if status_queue:
            if is_valid:
                status_queue.put(("✓ Filename pattern valid", "success"))
            else:
                status_queue.put(("✗ Invalid filename pattern", "error"))
        return is_valid

    def _validate_csv_content(self, file_path, status_queue=None):
        errors = []
        valid_records = []
        seen_records = set()

        if status_queue:
            status_queue.put(("Validating content...", "info"))

        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)

                try:
                    header = next(reader)
                    expected_fields = ["PatientID", "TrialCode", "DrugCode", "Dosage_mg",
                                       "StartDate", "EndDate", "Outcome", "SideEffects", "Analyst"]
                    if header != expected_fields:
                        errors.append("Invalid header structure")
                        if status_queue:
                            status_queue.put(("✗ Header mismatch", "error"))
                        return False, errors, 0
                    elif status_queue:
                        status_queue.put(("✓ Header valid", "success"))
                except StopIteration:
                    errors.append("File is empty")
                    if status_queue:
                        status_queue.put(("✗ File is empty", "error"))
                    return False, errors, 0

                row_num = 1
                for row in reader:
                    row_num += 1
                    record_errors = []

                    if len(row) != 9:
                        errors.append(
                            f"Row {row_num}: Expected 9 fields, got {len(row)}")
                        continue

                    (patient_id, trial_code, drug_code, dosage,
                     start_date, end_date, outcome, side_effects, analyst) = row

                    # Check for missing required fields
                    if not all([patient_id, trial_code, drug_code, dosage,
                               start_date, end_date, outcome, side_effects, analyst]):
                        record_errors.append("Missing required fields")

                    # Validate dosage
                    try:
                        dosage_val = int(dosage)
                        if dosage_val <= 0:
                            record_errors.append(f"Invalid dosage: {dosage}")
                    except:
                        record_errors.append(f"Non-numeric dosage: {dosage}")

                    # Validate dates
                    try:
                        start = datetime.strptime(start_date, "%Y-%m-%d")
                        end = datetime.strptime(end_date, "%Y-%m-%d")
                        if end < start:
                            record_errors.append(f"End date before start date")
                    except:
                        record_errors.append("Invalid date format")

                    # Validate outcome
                    if outcome not in ["Improved", "No Change", "Worsened"]:
                        record_errors.append(f"Invalid outcome: {outcome}")

                    # Check for duplicates
                    key = f"{patient_id}_{trial_code}_{drug_code}"
                    if key in seen_records:
                        record_errors.append("Duplicate record")
                    else:
                        seen_records.add(key)

                    if record_errors:
                        errors.append(
                            f"Row {row_num}: {', '.join(record_errors)}")
                    else:
                        valid_records.append(row)

                if status_queue:
                    status_queue.put((f"Scanned {row_num - 1} rows", "info"))
                    status_queue.put(
                        (f"Valid records: {len(valid_records)}", "success"))
                    if errors:
                        status_queue.put(
                            (f"Errors found: {len(errors)}", "error"))

            if errors:
                return False, errors, len(valid_records)
            return True, [], len(valid_records)

        except Exception as e:
            return False, [f"File read error: {str(e)}"], 0

    def validate_file(self, ftp, filename, status_queue, progress_callback=None):
        """Validate a single file without archiving"""
        if filename in self.processed_files:
            status_queue.put(
                (f"Skipping: {filename} (already processed)", "warning"))
            return

        status_queue.put((f"Validating: {filename}", "info"))

        temp_path = self.download_dir / f"temp_validate_{filename}"
        try:
            # Generate today's date for log filename
            today_date = datetime.now().strftime("%Y%m%d")
            log_filename = f"CLINICALDATA{today_date}.CSV"

            # Simulate progress for download
            if progress_callback:
                for i in range(0, 101, 20):
                    progress_callback(i, f"Downloading {filename}...")
                    time.sleep(0.2)

            with open(temp_path, 'wb') as f:
                ftp.retrbinary(f'RETR {filename}', f.write)

            # Simulate progress for validation
            if progress_callback:
                for i in range(20, 81, 30):
                    progress_callback(i, f"Validating {filename}...")
                    time.sleep(0.3)

            if self._validate_filename_pattern(filename, status_queue):
                is_valid, errors, record_count = self._validate_csv_content(
                    temp_path, status_queue)

                # Simulate final progress
                if progress_callback:
                    progress_callback(100, "Validation complete!")
                    time.sleep(0.5)

                if is_valid:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    status_queue.put(
                        (f"VALID: {log_filename} ({record_count} records)", "valid"))
                    status_queue.put(
                        (f"[{timestamp}] {log_filename} - Valid ({record_count} records)", "valid_log"))
                else:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    status_queue.put(
                        (f"INVALID: {log_filename} ({len(errors)} errors)", "invalid"))
                    status_queue.put(
                        (f"[{timestamp}] {log_filename} - Invalid ({len(errors)} errors)", "invalid_log"))
                    # Log errors to error report
                    for error in errors:
                        self._log_error(log_filename, error)

            else:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                status_queue.put(
                    (f"INVALID: {log_filename} (invalid filename pattern)", "invalid"))
                status_queue.put(
                    (f"[{timestamp}] {log_filename} - Invalid filename pattern", "invalid_log"))
                self._log_error(log_filename, "Invalid filename pattern")

            temp_path.unlink()
        except Exception as e:
            today_date = datetime.now().strftime("%Y%m%d")
            log_filename = f"CLINICALDATA{today_date}.CSV"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status_queue.put((f"Error validating {filename}: {e}", "error"))
            status_queue.put(
                (f"[{timestamp}] {log_filename} - Error: {e}", "invalid_log"))
            self._log_error(log_filename, f"Validation error: {e}")
            if temp_path.exists():
                temp_path.unlink()

    def process_file(self, ftp, filename, status_queue, progress_callback=None):
        """Process a single file: download, validate, archive or reject"""
        if filename in self.processed_files:
            status_queue.put(
                (f"Skipping: {filename} (already processed)", "warning"))
            return

        status_queue.put((f"Processing: {filename}", "info"))

        local_path = self.download_dir / filename
        try:
            # Generate today's date for filename
            current_date = datetime.now().strftime("%Y%m%d")
            archive_filename = f"CLINICALDATA{current_date}.CSV"
            log_filename = archive_filename  # Use the same name for logs

            # Simulate progress for download
            if progress_callback:
                for i in range(0, 31, 10):
                    progress_callback(i, f"Downloading {filename}...")
                    time.sleep(0.2)

            # Download file
            with open(local_path, 'wb') as f:
                ftp.retrbinary(f'RETR {filename}', f.write)
            status_queue.put(("Downloaded successfully", "success"))

            # Simulate progress for filename validation
            if progress_callback:
                for i in range(30, 51, 10):
                    progress_callback(i, "Validating filename pattern...")
                    time.sleep(0.2)

            # Validate filename
            if not self._validate_filename_pattern(filename, status_queue):
                error_file = self.error_dir / filename
                local_path.rename(error_file)
                self._log_error(log_filename, "Invalid filename pattern")
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                status_queue.put(
                    ("Rejected - Invalid filename pattern", "error"))
                status_queue.put(
                    (f"[{timestamp}] {log_filename} - Invalid filename pattern", "invalid_log"))

                if progress_callback:
                    progress_callback(100, "File rejected - invalid filename")
                return

            # Simulate progress for content validation
            if progress_callback:
                for i in range(50, 81, 15):
                    progress_callback(i, "Validating file content...")
                    time.sleep(0.3)

            # Validate content
            is_valid, errors, record_count = self._validate_csv_content(
                local_path, status_queue)

            if is_valid:
                # Simulate progress for archiving
                if progress_callback:
                    for i in range(80, 101, 10):
                        progress_callback(i, "Archiving valid file...")
                        time.sleep(0.2)

                # Archive valid file with today's date
                archive_path = self.archive_dir / archive_filename

                local_path.rename(archive_path)
                self._save_processed_file(filename)

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                status_queue.put(
                    (f"Archived as: {archive_filename} ({record_count} records)", "success"))
                status_queue.put(
                    (f"[{timestamp}] {log_filename} - Valid ({record_count} records)", "valid_log"))
            else:
                # Simulate progress for error handling
                if progress_callback:
                    progress_callback(90, "Moving file to error directory...")
                    time.sleep(0.3)
                    progress_callback(100, "File processed with errors")

                # Move invalid file to error directory
                error_file = self.error_dir / filename
                local_path.rename(error_file)

                # Log all errors
                for error in errors:
                    self._log_error(log_filename, error)

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                status_queue.put((f"Rejected ({len(errors)} errors)", "error"))
                status_queue.put(
                    (f"[{timestamp}] {log_filename} - Invalid ({len(errors)} errors)", "invalid_log"))

        except Exception as e:
            current_date = datetime.now().strftime("%Y%m%d")
            log_filename = f"CLINICALDATA{current_date}.CSV"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status_queue.put((f"Fatal error: {e}", "error"))
            status_queue.put(
                (f"[{timestamp}] {log_filename} - Error: {e}", "invalid_log"))
            self._log_error(log_filename, f"Processing error: {e}")
            if local_path.exists():
                local_path.unlink()

            if progress_callback:
                progress_callback(100, "Processing failed!")


class ClinicalDataGUI:
    """UI Design aligned with Schneiderman's and Nielsen's principles"""

    def __init__(self, root):
        self.root = root
        self.root.title("Clinical Data Processor - Secure File Management")
        self.root.geometry("700x500")
        self.root.minsize(900, 600)
        self.root.configure(bg='#f5f5f5')

        # Apply modern theme
        self.setup_styles()

        self.processor = None
        self.validator = None
        self.is_processing = False

        self.all_files = []
        self.displayed_files = []
        self.selected_file = None

        # Default settings
        self.ftp_host = tk.StringVar(value="host.docker.internal")
        self.ftp_user = tk.StringVar(value="nhl")
        self.ftp_pass = tk.StringVar(value="123")
        self.download_dir = tk.StringVar(
            value=str(Path.home() / "ClinicalData" / "Downloads"))
        self.archive_dir = tk.StringVar(
            value=str(Path.home() / "ClinicalData" / "Archive"))
        self.error_dir = tk.StringVar(
            value=str(Path.home() / "ClinicalData" / "Errors"))
        self.search_var = tk.StringVar()

        # Status tracking
        self.current_operation = tk.StringVar(value="Ready")
        self.operation_status = tk.StringVar(value="⚪ Idle")

        self.create_modern_widgets()
        self.setup_directories()

        # Bind search variable to update filter
        self.search_var.trace('w', self.filter_file_list)

    def setup_styles(self):
        """Configure modern styling"""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure colors
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'),
                        background='#f5f5f5', foreground='#2c3e50')
        style.configure('Subtitle.TLabel', font=('Arial', 10, 'bold'),
                        background='#f5f5f5', foreground='#34495e')
        style.configure('Success.TLabel', font=('Arial', 9),
                        background='#f5f5f5', foreground='#27ae60')
        style.configure('Error.TLabel', font=('Arial', 9),
                        background='#f5f5f5', foreground='#e74c3c')
        style.configure('Accent.TButton', font=('Arial', 9),
                        background='#3498db', foreground='white')
        style.configure('Modern.TFrame', background='#ffffff',
                        relief='flat', borderwidth=1)
        style.configure('Header.TFrame', background='#2c3e50')

        # Configure button styles
        style.configure('TButton', font=('Arial', 9))
        style.configure('Small.TButton', font=('Arial', 8))

    def setup_directories(self):
        for var in [self.download_dir, self.archive_dir, self.error_dir]:
            Path(var.get()).mkdir(parents=True, exist_ok=True)

    def create_modern_widgets(self):
        # Main container with modern styling
        main_frame = ttk.Frame(self.root, style='Modern.TFrame', padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main_frame, style='Header.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text="🏥 Clinical Data Processor",
                  style='Title.TLabel', background='#2c3e50', foreground='white').pack(side=tk.LEFT, pady=8)

        # Status indicator in header
        status_frame = ttk.Frame(header_frame, style='Header.TFrame')
        status_frame.pack(side=tk.RIGHT, pady=8)
        ttk.Label(status_frame, textvariable=self.operation_status,
                  font=('Arial', 9, 'bold'), background='#2c3e50', foreground='white').pack()

        # Connection Frame
        conn_frame = ttk.LabelFrame(
            main_frame, text="🔗 Server Connection", padding="10")
        conn_frame.pack(fill=tk.X, pady=(0, 10))

        # Connection inputs in a grid
        input_frame = ttk.Frame(conn_frame)
        input_frame.pack(fill=tk.X)

        ttk.Label(input_frame, text="Server:", font=('Arial', 9)).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        ttk.Entry(input_frame, textvariable=self.ftp_host, width=18, font=(
            'Arial', 9)).grid(row=0, column=1, sticky=tk.W, pady=2, padx=(0, 15))

        ttk.Label(input_frame, text="Username:", font=('Arial', 9)).grid(
            row=0, column=2, sticky=tk.W, padx=(0, 5), pady=2)
        ttk.Entry(input_frame, textvariable=self.ftp_user, width=12, font=(
            'Arial', 9)).grid(row=0, column=3, sticky=tk.W, pady=2, padx=(0, 15))

        ttk.Label(input_frame, text="Password:", font=('Arial', 9)).grid(
            row=0, column=4, sticky=tk.W, padx=(0, 5), pady=2)
        ttk.Entry(input_frame, textvariable=self.ftp_pass, show="•", width=12, font=(
            'Arial', 9)).grid(row=0, column=5, sticky=tk.W, pady=2, padx=(0, 15))

        # Connection buttons
        btn_frame = ttk.Frame(conn_frame)
        btn_frame.pack(fill=tk.X, pady=(8, 0))

        self.connect_btn = ttk.Button(
            btn_frame, text="🔌 Connect", command=self.connect_to_server, style='Accent.TButton')
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.disconnect_btn = ttk.Button(
            btn_frame, text="🔒 Disconnect", command=self.disconnect_from_server, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=(0, 8))

        # Quick stats
        stats_frame = ttk.Frame(btn_frame)
        stats_frame.pack(side=tk.RIGHT)
        self.stats_label = ttk.Label(
            stats_frame, text="📊 Files: 0", font=('Arial', 9, 'bold'))
        self.stats_label.pack()

        # Main Content Area - Split view
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Left Panel - File Management
        left_panel = ttk.LabelFrame(
            content_frame, text="📁 Server Files", padding="8")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Search
        search_frame = ttk.Frame(left_panel)
        search_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(search_frame, text="🔍 Search:", font=(
            'Arial', 9)).pack(side=tk.LEFT, padx=(0, 8))
        self.search_entry = ttk.Entry(
            search_frame, textvariable=self.search_var, width=20, font=('Arial', 9))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X,
                               expand=True, padx=(0, 8))
        ttk.Button(search_frame, text="Clear", command=self.clear_search,
                   style='Small.TButton').pack(side=tk.LEFT)

        # File list
        list_container = ttk.Frame(left_panel)
        list_container.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # File list header
        list_header = ttk.Frame(list_container)
        list_header.pack(fill=tk.X)
        ttk.Label(list_header, text="Available Files:",
                  font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        self.selected_label = ttk.Label(
            list_header, text="No file selected", font=('Arial', 9), foreground='#7f8c8d')
        self.selected_label.pack(side=tk.RIGHT)

        self.file_listbox = tk.Listbox(list_container, height=10, selectmode=tk.SINGLE,
                                       font=('Arial', 9), bg='white', relief='flat',
                                       highlightthickness=1, highlightcolor='#3498db')
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH,
                               expand=True, pady=(3, 0))

        scrollbar = ttk.Scrollbar(
            list_container, command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_selection)

        # Action buttons
        action_frame = ttk.Frame(left_panel)
        action_frame.pack(fill=tk.X, pady=(10, 0))

        # Primary actions - arranged horizontally
        self.validate_btn = ttk.Button(
            action_frame, text="Validate", command=self.validate_file, state=tk.DISABLED, width=12)
        self.validate_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.process_btn = ttk.Button(
            action_frame, text=" Process", command=self.process_file, state=tk.DISABLED, width=12)
        self.process_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.download_btn = ttk.Button(
            action_frame, text=" Download", command=self.download_file, state=tk.DISABLED, width=12)
        self.download_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Secondary actions
        ttk.Button(action_frame, text="Refresh", command=self.refresh_files,
                   width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="Stats",
                   command=self.show_stats, width=8).pack(side=tk.LEFT)

        # Right Panel - Logs and Monitoring
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Log Frame with modern notebook
        log_notebook = ttk.Notebook(right_panel)
        log_notebook.pack(fill=tk.BOTH, expand=True)

        # Activity Log Tab
        activity_frame = ttk.Frame(log_notebook, padding="5")
        log_notebook.add(activity_frame, text="Activity")

        self.log_text = scrolledtext.ScrolledText(activity_frame, height=8, wrap=tk.WORD,
                                                  font=('Consolas', 8), bg='#f8f9fa')
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Valid Files Log Tab
        valid_frame = ttk.Frame(log_notebook, padding="5")
        log_notebook.add(valid_frame, text="Valid")

        self.valid_text = scrolledtext.ScrolledText(valid_frame, height=8, wrap=tk.WORD,
                                                    font=('Consolas', 8), bg='#f8f9fa')
        self.valid_text.pack(fill=tk.BOTH, expand=True)

        # Invalid Files Log Tab
        invalid_frame = ttk.Frame(log_notebook, padding="5")
        log_notebook.add(invalid_frame, text=" Invalid")

        self.invalid_text = scrolledtext.ScrolledText(invalid_frame, height=8, wrap=tk.WORD,
                                                      font=('Consolas', 8), bg='#f8f9fa')
        self.invalid_text.pack(fill=tk.BOTH, expand=True)

        # Error Log Tab
        error_frame = ttk.Frame(log_notebook, padding="5")
        log_notebook.add(error_frame, text=" Errors")

        self.error_text = scrolledtext.ScrolledText(error_frame, height=8, wrap=tk.WORD,
                                                    font=('Consolas', 8), bg='#f8f9fa')
        self.error_text.pack(fill=tk.BOTH, expand=True)

        # Bottom Action Bar
        bottom_bar = ttk.Frame(main_frame)
        bottom_bar.pack(fill=tk.X, pady=(5, 0))

        # Current operation status
        ttk.Label(bottom_bar, textvariable=self.current_operation,
                  font=('Arial', 9)).pack(side=tk.LEFT)

        # Utility buttons with Error Log button
        util_buttons = ttk.Frame(bottom_bar)
        util_buttons.pack(side=tk.RIGHT)
        ttk.Button(util_buttons, text="Clear Logs",
                   command=self.clear_all_logs, width=10).pack(side=tk.LEFT, padx=3)
        ttk.Button(util_buttons, text="ℹ️ Help",
                   command=self.show_help, width=8).pack(side=tk.LEFT, padx=3)

        # Configure log tags for better visual feedback
        self.configure_log_tags()

        # Queue for thread-safe logging
        self.status_queue = queue.Queue()
        self.root.after(100, self.check_queue)

    def configure_log_tags(self):
        """Configure text tags for better visual feedback"""
        # Activity log tags
        self.log_text.tag_configure(
            "success", foreground="#27ae60", font=('Consolas', 8, 'bold'))
        self.log_text.tag_configure(
            "error", foreground="#e74c3c", font=('Consolas', 8, 'bold'))
        self.log_text.tag_configure(
            "warning", foreground="#f39c12", font=('Consolas', 8, 'bold'))
        self.log_text.tag_configure(
            "info", foreground="#3498db", font=('Consolas', 8))
        self.log_text.tag_configure(
            "valid", foreground="#27ae60", font=('Consolas', 8, 'bold'))
        self.log_text.tag_configure(
            "invalid", foreground="#e74c3c", font=('Consolas', 8, 'bold'))

        # Specialized log tags
        self.valid_text.tag_configure(
            "valid_log", foreground="#27ae60", font=('Consolas', 8))
        self.invalid_text.tag_configure(
            "invalid_log", foreground="#e74c3c", font=('Consolas', 8))
        self.error_text.tag_configure(
            "error_log", foreground="#e74c3c", font=('Consolas', 8))

    def filter_file_list(self, *args):
        """Filter files based on search term"""
        search_term = self.search_var.get().lower()

        # Clear current selection when filtering
        self.file_listbox.selection_clear(0, tk.END)
        self.selected_file = None
        self.update_action_buttons()

        # Filter files
        if search_term:
            self.displayed_files = [
                f for f in self.all_files if search_term in f.lower()]
        else:
            self.displayed_files = self.all_files.copy()

        # Update listbox
        self.file_listbox.delete(0, tk.END)
        for file in self.displayed_files:
            self.file_listbox.insert(tk.END, file)

        # Update stats
        self.update_stats()

        # Show message if no results
        if search_term and not self.displayed_files:
            self.log_message(
                f"No files found matching '{search_term}'", "warning")
        elif search_term:
            self.log_message(
                f"Found {len(self.displayed_files)} files matching '{search_term}'", "info")

    def clear_search(self):
        """Clear search field and show all files"""
        self.search_var.set("")

    def update_error_log_display(self):
        """Update the error log display with content from error_report.log"""
        error_log_path = Path(self.error_dir.get()) / "error_report.log"

        if error_log_path.exists():
            try:
                with open(error_log_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                self.error_text.delete(1.0, tk.END)
                self.error_text.insert(tk.END, content)
                self.error_text.see(tk.END)
            except Exception as e:
                self.error_text.delete(1.0, tk.END)
                self.error_text.insert(tk.END, f"Error reading log file: {e}")
        else:
            self.error_text.delete(1.0, tk.END)
            self.error_text.insert(tk.END, "No error log file found yet.")

    def refresh_error_log(self):
        """Refresh error log display"""
        self.update_error_log_display()

    def update_stats(self):
        """Update file statistics"""
        total_files = len(self.all_files)
        displayed_files = len(self.displayed_files)
        stats_text = f"📊 Files: {displayed_files}/{total_files}"
        if hasattr(self, 'stats_label'):
            self.stats_label.config(text=stats_text)

    def update_action_buttons(self):
        """Update button states based on current selection"""
        if self.selected_file and self.processor and self.processor.connected:
            self.validate_btn.config(state=tk.NORMAL)
            self.process_btn.config(state=tk.NORMAL)
            self.download_btn.config(state=tk.NORMAL)
            self.selected_label.config(text=f"Selected: {self.selected_file}")
        else:
            self.validate_btn.config(state=tk.DISABLED)
            self.process_btn.config(state=tk.DISABLED)
            self.download_btn.config(state=tk.DISABLED)
            self.selected_label.config(text="No file selected")

    def log_message(self, message, tag="info"):
        """Enhanced logging with better visual feedback"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        if tag == "valid_log":
            self.valid_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
            self.valid_text.see(tk.END)
        elif tag == "invalid_log":
            self.invalid_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
            self.invalid_text.see(tk.END)
        elif tag == "error_log":
            self.error_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
            self.error_text.see(tk.END)
        else:
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
            self.log_text.see(tk.END)

    def check_queue(self):
        """Check for messages from worker threads"""
        try:
            while True:
                message, tag = self.status_queue.get_nowait()
                self.log_message(message, tag)

                # Refresh error log when new errors are logged
                if "error" in tag.lower() or "invalid" in tag.lower():
                    try:
                        self.root.after(100, self.update_error_log_display)
                    except Exception as e:
                        print(f"Error updating error log display: {e}")

                # Update operation status
                if "processing" in message.lower():
                    self.operation_status.set("🟡 Processing...")
                elif "valid" in message.lower() and "invalid" not in message.lower():
                    self.operation_status.set("🟢 Valid")
                elif "error" in message.lower() or "invalid" in message.lower():
                    self.operation_status.set("🔴 Error")
                elif "complete" in message.lower():
                    self.operation_status.set("🟢 Ready")

                if tag in ["complete", "error"]:
                    self.is_processing = False
                    self.update_action_buttons()
        except queue.Empty:
            pass

        self.root.after(100, self.check_queue)

    def update_connection_status(self):
        """Update connection status and UI state"""
        if self.processor and self.processor.connected:
            self.operation_status.set("🟢 Connected")
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.current_operation.set("✅ Connected to server")
        else:
            self.operation_status.set("🔴 Disconnected")
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.update_action_buttons()
            self.current_operation.set("⚠️ Disconnected from server")

    def on_file_selection(self, event):
        """Handle file selection with better feedback"""
        selection = self.file_listbox.curselection()
        if selection and self.processor and self.processor.connected:
            self.selected_file = self.displayed_files[selection[0]]
            self.current_operation.set(f"📄 Selected: {self.selected_file}")
        else:
            self.selected_file = None
            self.current_operation.set("📁 No file selected")

        self.update_action_buttons()

    def connect_to_server(self):
        """Connect to FTP server with better user feedback"""
        if self.is_processing:
            return

        if not all([self.ftp_host.get(), self.ftp_user.get(), self.ftp_pass.get()]):
            messagebox.showerror("Connection Error",
                                 "Please fill in all server connection fields.\n\n"
                                 "• Server address\n• Username\n• Password",
                                 icon='warning')
            return

        self.log_text.delete(1.0, tk.END)
        self.is_processing = True
        self.current_operation.set("🔄 Connecting to server...")

        thread = threading.Thread(target=self._connect_worker)
        thread.daemon = True
        thread.start()

    def _connect_worker(self):
        try:
            self.processor = ClinicalDataProcessor(
                self.ftp_host.get(),
                self.ftp_user.get(),
                self.ftp_pass.get()
            )

            if self.processor.connect(self.status_queue):
                self.all_files = self.processor.get_file_list(
                    self.status_queue)
                self.root.after(0, self._update_file_list)
                self.root.after(0, self.update_connection_status)
            else:
                self.status_queue.put(("Connection failed", "error"))

            self.status_queue.put(("complete", "complete"))
        except Exception as e:
            self.status_queue.put((f"Connection error: {e}", "error"))
            self.status_queue.put(("complete", "complete"))

    def _update_file_list(self):
        self.displayed_files = self.all_files.copy()
        self.file_listbox.delete(0, tk.END)
        for file in self.displayed_files:
            self.file_listbox.insert(tk.END, file)
        self.update_stats()
        self.log_message(
            f"Loaded {len(self.all_files)} files from server", "success")

    def disconnect_from_server(self):
        """Disconnect from server with confirmation"""
        if self.is_processing:
            return

        if messagebox.askyesno("Disconnect", "Are you sure you want to disconnect from the server?"):
            self.is_processing = True
            self.current_operation.set("🔌 Disconnecting...")

            thread = threading.Thread(target=self._disconnect_worker)
            thread.daemon = True
            thread.start()

    def _disconnect_worker(self):
        try:
            self.processor.disconnect()
            self.all_files = []
            self.displayed_files = []
            self.root.after(0, self._update_file_list)
            self.root.after(0, self.update_connection_status)
            self.status_queue.put(("Disconnected successfully", "success"))
            self.status_queue.put(("complete", "complete"))
        except Exception as e:
            self.status_queue.put((f"Disconnect failed: {e}", "error"))
            self.status_queue.put(("complete", "complete"))

    def refresh_files(self):
        """Refresh file list with better feedback"""
        if not self.processor:
            messagebox.showwarning(
                "Not Connected", "Please connect to the server first.")
            return

        if self.is_processing:
            return

        self.clear_search()
        self.is_processing = True
        self.current_operation.set("🔄 Refreshing file list...")

        thread = threading.Thread(target=self._refresh_worker)
        thread.daemon = True
        thread.start()

    def _refresh_worker(self):
        try:
            if not self.processor.connected:
                self.processor.connect(self.status_queue)

            self.all_files = self.processor.get_file_list(self.status_queue)
            self.root.after(0, self._update_file_list)
            self.status_queue.put(("File list refreshed", "success"))
            self.status_queue.put(("complete", "complete"))
        except Exception as e:
            self.status_queue.put((f"Refresh failed: {e}", "error"))
            self.status_queue.put(("complete", "complete"))

    def validate_file(self):
        """Validate selected file"""
        if self.is_processing or not self.selected_file:
            return

        self.log_text.delete(1.0, tk.END)
        self.is_processing = True
        self.current_operation.set(f"🔍 Validating: {self.selected_file}")

        self.validator = ClinicalDataValidator(
            self.download_dir.get(),
            self.archive_dir.get(),
            self.error_dir.get()
        )

        thread = threading.Thread(target=self._validate_worker)
        thread.daemon = True
        thread.start()

    def _validate_worker(self):
        try:
            if not self.processor.connected:
                self.processor.connect(self.status_queue)

            self.validator.validate_file(
                self.processor.ftp,
                self.selected_file,
                self.status_queue
            )
            self.status_queue.put(("complete", "complete"))
        except Exception as e:
            self.status_queue.put((f"Validation failed: {e}", "error"))
            self.status_queue.put(("complete", "complete"))

    def process_file(self):
        """Process selected file with confirmation"""
        if self.is_processing or not self.selected_file:
            return

        confirm = messagebox.askyesno("Process File",
                                      f"Process and validate file:\n\n"
                                      f"'{self.selected_file}'\n\n"
                                      f"This will download, validate, and archive the file.",
                                      icon='question')
        if not confirm:
            return

        self.log_text.delete(1.0, tk.END)
        self.is_processing = True
        self.current_operation.set(f"⚙️ Processing: {self.selected_file}")

        self.validator = ClinicalDataValidator(
            self.download_dir.get(),
            self.archive_dir.get(),
            self.error_dir.get()
        )

        thread = threading.Thread(target=self._process_worker)
        thread.daemon = True
        thread.start()

    def _process_worker(self):
        try:
            if not self.processor.connected:
                self.processor.connect(self.status_queue)

            self.validator.process_file(
                self.processor.ftp,
                self.selected_file,
                self.status_queue
            )
            self.status_queue.put(("complete", "complete"))
        except Exception as e:
            self.status_queue.put((f"Processing failed: {e}", "error"))
            self.status_queue.put(("complete", "complete"))

    def download_file(self):
        """Download file with today's date"""
        if self.is_processing or not self.selected_file:
            return

        confirm = messagebox.askyesno("Download File",
                                      f"Download file with today's date:\n\n"
                                      f"Original: {self.selected_file}\n"
                                      f"New name: CLINICALDATA{datetime.now().strftime('%Y%m%d')}.CSV\n\n"
                                      f"Continue?",
                                      icon='question')
        if not confirm:
            return

        self.log_text.delete(1.0, tk.END)
        self.is_processing = True
        self.current_operation.set(f"📥 Downloading: {self.selected_file}")

        thread = threading.Thread(target=self._download_worker)
        thread.daemon = True
        thread.start()

    def _download_worker(self):
        try:
            if not self.processor.connected:
                self.processor.connect(self.status_queue)

            local_path, new_filename = self.processor.download_file_with_new_name(
                self.selected_file,
                self.download_dir.get(),
                self.status_queue
            )

            if local_path:
                self.status_queue.put(
                    (f"File downloaded successfully as: {new_filename}", "success"))
                self.current_operation.set(f"✅ Downloaded: {new_filename}")
            else:
                self.status_queue.put(("Download failed", "error"))

            self.status_queue.put(("complete", "complete"))
        except Exception as e:
            self.status_queue.put((f"Download failed: {e}", "error"))
            self.status_queue.put(("complete", "complete"))

    def open_error_log(self):
        """Open the error log file and refresh display"""
        error_log_path = Path(self.error_dir.get()) / "error_report.log"

        if error_log_path.exists():
            try:
                # Update the GUI display first
                self.update_error_log_display()

                # Also open with default text editor
                os.startfile(str(error_log_path))
                self.log_message("Opened error log file", "info")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open error log: {e}")
        else:
            messagebox.showinfo(
                "Error Log", "No error log file found yet. Errors will be logged here when they occur.")

    def clear_all_logs(self):
        """Clear all log areas with confirmation"""
        if messagebox.askyesno("Clear Logs", "Clear all log contents?"):
            for text_widget in [self.log_text, self.valid_text, self.invalid_text, self.error_text]:
                text_widget.delete(1.0, tk.END)
            self.log_message("All logs cleared", "info")

    def show_stats(self):
        """Show application statistics"""
        error_log_path = Path(self.error_dir.get()) / "error_report.log"
        error_count = 0
        if error_log_path.exists():
            try:
                with open(error_log_path, 'r', encoding='utf-8') as f:
                    error_count = len(f.readlines())
            except:
                error_count = 0

        stats = f"""
📊 Application Statistics:

• Total Files on Server: {len(self.all_files)}
• Displayed Files: {len(self.displayed_files)}
• Selected File: {self.selected_file or 'None'}
• Connection Status: {'Connected' if self.processor and self.processor.connected else 'Disconnected'}
• Processing: {'Yes' if self.is_processing else 'No'}
• Error Log Entries: {error_count}

📁 Directories:
• Downloads: {self.download_dir.get()}
• Archive: {self.archive_dir.get()}
• Errors: {self.error_dir.get()}
        """
        messagebox.showinfo("Application Statistics", stats.strip())

    def show_help(self):
        """Show help information"""
        help_text = """
🤖 Clinical Data Processor Help

📋 Basic Usage:
1. Connect to FTP server using your credentials
2. Select a file from the list
3. Choose an action: Validate, Process, or Download

⚡ Actions:
• Validate: Check file without downloading
• Process: Download, validate, and archive
• Download: Save file with today's date

📊 Logs:
• Activity: General operations
• Valid Files: Successfully processed files
• Invalid Files: Failed validations
• Error Log: Detailed error information

💡 Tips:
• Use search to filter files
• Check different log tabs for details
• Files are renamed with today's date when downloaded
• Use the 'Error Log' button to view detailed error reports
        """
        messagebox.showinfo("Help", help_text.strip())


def main():
    root = tk.Tk()
    app = ClinicalDataGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
