import os
import logging
from datetime import datetime
from config import BACKUP_DIR

logger = logging.getLogger("BhumiBilling.Backup")

def run_auto_backup(db_manager):
    """
    Checks if a backup for today exists in BACKUP_DIR.
    If not, it checkpoints SQLite and makes a timestamped copy.
    """
    try:
        date_stamp = datetime.now().strftime("%Y%m%d")
        expected_backup = os.path.join(BACKUP_DIR, f"bhumi_billing_backup_{date_stamp}.db")
        
        # Check if already backed up today
        if not os.path.exists(expected_backup):
            logger.info("No backup found for today. Starting auto-backup...")
            backup_path = db_manager.backup_database()
            logger.info(f"Auto-backup completed: {backup_path}")
            return True
        else:
            logger.info("Backup for today already exists. Skipping auto-backup.")
            return False
    except Exception as e:
        logger.error(f"Auto backup failed: {e}")
        return False
