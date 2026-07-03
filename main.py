import sys
import os
import logging
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

from config import DATA_DIR, APP_NAME, VERSION
from db_manager import DatabaseManager
from ui.main_window import MainWindow
from utils.backup import run_auto_backup

# Set up logs file writing inside data directory
LOG_FILE = os.path.join(DATA_DIR, "bhumi_billing.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("BhumiBilling.Main")

def exception_hook(exctype, value, traceback):
    """Global unhandled exception hook to prevent silent terminal crashes."""
    logger.critical("Unhandled exception caught:", exc_info=(exctype, value, traceback))
    err_msg = f"An unexpected system error occurred:\n\n{value}\n\nCheck logs at: {LOG_FILE}"
    
    # Try displaying MessageBox safely
    try:
        QMessageBox.critical(None, "Critical System Error", err_msg)
    except Exception:
        pass
    
    sys.__excepthook__(exctype, value, traceback)

# Bind exception handler
sys.excepthook = exception_hook

def main():
    logger.info(f"Starting {APP_NAME} version {VERSION}...")
    
    # Enable High DPI scaling for modern displays
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    # Initialize Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(VERSION)
    
    try:
        # Initialize SQLite database context
        db_manager = DatabaseManager()
        
        # Run silent background auto-backup checks
        run_auto_backup(db_manager)
        
        # Start GUI Window
        window = MainWindow(db_manager)
        window.show()
        
        logger.info("Application initialized successfully. Running Qt main loop.")
        sys.exit(app.exec())
        
    except Exception as e:
        logger.critical(f"Failed to launch application context: {e}", exc_info=True)
        QMessageBox.critical(None, "Application Launch Failed", 
                             f"Bhumi Billing database or GUI failed to start.\n\nError: {e}\n\nSee log file for details: {LOG_FILE}")
        sys.exit(1)

if __name__ == "__main__":
    main()
