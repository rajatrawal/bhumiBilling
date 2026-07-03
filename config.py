import os
import sys

# Core Application Information
APP_NAME = "Bhumi Billing"
VERSION = "1.0.0"
AUTHOR = "Bhumi Jewellers"

# Directory Structure Config
# Resolve base path (works when running as script or bundled EXE via PyInstaller)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data directory next to the binary/script (fully portable)
DATA_DIR = os.path.join(BASE_DIR, "data")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
PDF_DIR = os.path.join(DATA_DIR, "invoices")

# Ensure necessary directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

# File Paths
DB_PATH = os.path.join(DATA_DIR, "bhumi_billing.db")

# Default settings keys and fallback values
DEFAULT_SETTINGS = {
    "business_name": "Bhumi Jewellers",
    "business_address": "Main Bazaar, Gold Market, India",
    "mobile_number": "+91 98765 43210",
    "whatsapp_number": "+91 98765 43210",
    "gst_number": "",
    "footer_message": "Thank you for shopping with us!",
    "default_customer_name": "Walk-in Customer",
    "default_customer_mobile": "0000000000",
    "default_customer_address": "Counter",

    "default_mode": "retail",  # retail or wholesale
    "business_logo_path": "",
    "theme": "dark"  # dark or light
}
