from PySide6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                             QLabel, QHBoxLayout, QMessageBox, QStatusBar)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QIcon

from ui.billing_widget import BillingWidget
from ui.product_widget import ProductManagerWidget
from ui.customer_widget import CustomerManagerWidget
from ui.tally_widget import TallyWidget
from ui.settings_widget import SettingsWidget
from ui.styles import DARK_QSS, LIGHT_QSS

class MainWindow(QMainWindow):
    """
    Core Main Window frame managing views, tab switching,
    QSS stylesheets, and routing global key shortcuts.
    """
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.setWindowTitle("Bhumi Billing - Ultra-Fast Jewellery Billing")
        self.resize(1150, 700)
        
        self.init_ui()
        self.apply_theme()
        
        # Check for draft crash recovery on start
        self.check_draft_recovery()

    def init_ui(self):
        # Main Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setFocusPolicy(Qt.NoFocus)
        self.setCentralWidget(self.tabs)

        # Initialize View Widgets
        self.billing_view = BillingWidget(self.db, self)
        self.products_view = ProductManagerWidget(self.db, self)
        self.customers_view = CustomerManagerWidget(self.db, self)
        self.tally_view = TallyWidget(self.db, self)
        self.settings_view = SettingsWidget(self.db, self)

        # Add tabs
        self.tabs.addTab(self.billing_view, "Billing (F2)")
        self.tabs.addTab(self.products_view, "Products (F10)")
        self.tabs.addTab(self.customers_view, "Customers (F11)")
        self.tabs.addTab(self.tally_view, "Daily Tally (F8)")
        self.tabs.addTab(self.settings_view, "Settings (F12)")

        # Hook settings saved triggers
        self.settings_view.settings_saved.connect(self.on_settings_saved)

        # Status Bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("System Ready | Press F2 for Billing | F1 for Shortcut Help", 5000)

        # Connect tab change to refresh statistics
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def apply_theme(self):
        theme = self.db.get_setting("theme", "dark")
        if theme == "light":
            self.setStyleSheet(LIGHT_QSS)
        else:
            self.setStyleSheet(DARK_QSS)

    def on_settings_saved(self):
        # Refresh theme & configurations across views
        self.apply_theme()
        self.billing_view.reset_billing_session()
        self.tally_view.refresh_all()

    def on_tab_changed(self, index):
        """Pre-focus or refresh views when tabs change."""
        if index == 0: # Billing Tab
            self.billing_view.prod_search.setFocus()
            self.billing_view.prod_search.selectAll()
        elif index == 3: # Daily Tally Tab
            self.tally_view.refresh_all()
        elif index == 4: # Settings Tab
            self.settings_view.load_settings()

    def check_draft_recovery(self):
        """Auto-recovers previous session details on boot after crashes."""
        draft = self.db.load_draft()
        if draft and draft.get("items"):
            reply = QMessageBox.question(
                self, "Recover Draft Invoice",
                "Bhumi Billing recovered an unsaved draft from a previous session.\n"
                "Would you like to restore it?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.billing_view.load_recovered_draft(draft)
                self.status.showMessage("Draft invoice recovered successfully.", 4000)
            else:
                self.db.clear_draft()
                self.status.showMessage("Draft invoice cleared.", 4000)

    # ==========================================
    # GLOBAL KEYBOARD SHORTCUTS INTERCEPTOR
    # ==========================================
    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()

        # F1 Help
        if key == Qt.Key_F1:
            self.show_shortcuts_help()
            return

        # F2: Go to Billing & focus search input
        if key == Qt.Key_F2:
            self.tabs.setCurrentIndex(0)
            self.billing_view.prod_search.setFocus()
            self.billing_view.prod_search.selectAll()
            return

        # F3: Toggle Billing Mode (Retail/Wholesale)
        if key == Qt.Key_F3:
            self.tabs.setCurrentIndex(0)
            current_mode = self.billing_view.mode_combo.currentText()
            next_mode = "Wholesale" if current_mode == "Retail" else "Retail"
            self.billing_view.mode_combo.setCurrentText(next_mode)
            self.status.showMessage(f"Billing mode changed to: {next_mode}", 2000)
            return

        # F4: Trigger Product Recents Popover / tray focus
        if key == Qt.Key_F4:
            self.tabs.setCurrentIndex(0)
            # Focus the first item in the recents tray if any exists
            recents = self.db.get_recent_products()
            if recents:
                # Trigger click of first recent
                self.billing_view.on_recent_clicked(recents[0])
                self.status.showMessage(f"Loaded recent: {recents[0]['name']}", 2000)
            else:
                self.status.showMessage("No recent products found.", 2000)
            return

        # F6: Jump to Discount
        if key == Qt.Key_F6:
            self.tabs.setCurrentIndex(0)
            self.billing_view.discount_input.setFocus()
            self.billing_view.discount_input.selectAll()
            return

        # F7: Settle outstanding bill (Tally mode shortcut)
        if key == Qt.Key_F7:
            self.tabs.setCurrentIndex(3)
            self.tally_view.settle_invoice_payment()
            return

        # F8: Go to Daily Tally
        if key == Qt.Key_F8:
            self.tabs.setCurrentIndex(3)
            return

        # F9: Print Thermal
        if key == Qt.Key_F9:
            self.tabs.setCurrentIndex(0)
            self.billing_view.save_and_print_action()
            return

        # F10: Go to Product Manager
        if key == Qt.Key_F10:
            self.tabs.setCurrentIndex(1)
            return

        # F11: Go to Customer Manager
        if key == Qt.Key_F11:
            self.tabs.setCurrentIndex(2)
            return

        # F12: Go to Settings
        if key == Qt.Key_F12:
            self.tabs.setCurrentIndex(4)
            return

        # Ctrl+S: Save invoice (No print)
        if modifiers == Qt.ControlModifier and key == Qt.Key_S:
            self.tabs.setCurrentIndex(0)
            self.billing_view.save_invoice_action()
            return

        # Ctrl+P: Print Thermal (identical to F9 for standards)
        if modifiers == Qt.ControlModifier and key == Qt.Key_P:
            self.tabs.setCurrentIndex(0)
            self.billing_view.save_and_print_action()
            return

        # Ctrl+N: Quick create Customer Dialog
        if modifiers == Qt.ControlModifier and key == Qt.Key_N:
            self.billing_view.open_quick_customer_dialog()
            return

        # Ctrl+M: Focus Customer search
        if modifiers == Qt.ControlModifier and key == Qt.Key_M:
            self.tabs.setCurrentIndex(0)
            self.billing_view.cust_search.setFocus()
            self.billing_view.cust_search.selectAll()
            return

        # Ctrl+D: Cycle Payment Status (PAID -> PENDING -> PARTIAL)
        if modifiers == Qt.ControlModifier and key == Qt.Key_D:
            self.tabs.setCurrentIndex(0)
            idx = self.billing_view.pay_status_combo.currentIndex()
            next_idx = (idx + 1) % 3
            self.billing_view.pay_status_combo.setCurrentIndex(next_idx)
            self.status.showMessage(f"Payment status changed to: {self.billing_view.pay_status_combo.currentText()}", 2000)
            return

        # Ctrl+W: WhatsApp Share active bill
        if modifiers == Qt.ControlModifier and key == Qt.Key_W:
            self.tabs.setCurrentIndex(0)
            self.billing_view.whatsapp_share_action()
            return

        # Delete key: Remove item from billing table
        if key == Qt.Key_Delete:
            if self.tabs.currentIndex() == 0:
                self.billing_view.delete_selected_item()
                return

        # Pass through remaining events
        super().keyPressEvent(event)

    def show_shortcuts_help(self):
        shortcuts_text = (
            "<b>Bhumi Billing Shortcuts Map:</b><br/>"
            "---------------------------------------<br/>"
            "<b>F2</b>: Go to Billing Tab & Focus Product Search<br/>"
            "<b>F3</b>: Toggle Billing Mode (Retail / Wholesale)<br/>"
            "<b>F4</b>: Load Quick Recent Product Item<br/>"
            "<b>F6</b>: Jump to Discount Input Field<br/>"
            "<b>F8</b>: Go to Daily Tally / Cashbook Screen<br/>"
            "<b>F9 / Ctrl+P</b>: Save Invoice & Print Thermal Spool<br/>"
            "<b>F10</b>: Go to Products Tab<br/>"
            "<b>F11</b>: Go to Customers Tab<br/>"
            "<b>F12</b>: Go to Settings Tab<br/><br/>"
            "<b>Ctrl+S</b>: Save Invoice (No thermal print output)<br/>"
            "<b>Ctrl+N</b>: Inline Add New Customer Dialog<br/>"
            "<b>Ctrl+M</b>: Jump to Customer Search field<br/>"
            "<b>Ctrl+D</b>: Cycle Payment Status (PAID -> PENDING -> PARTIAL)<br/>"
            "<b>Ctrl+W</b>: Share invoice via WhatsApp Link<br/>"
            "<b>DEL (Delete Key)</b>: Delete selected item from billing table"
        )
        QMessageBox.information(self, "Keyboard Shortcut Help", shortcuts_text)
