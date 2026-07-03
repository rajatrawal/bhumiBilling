import re
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QComboBox, QFileDialog, 
                             QMessageBox, QFormLayout, QGroupBox, QTextEdit)
from PySide6.QtCore import Qt, Signal
# import get_installed_printers removed

class SettingsWidget(QWidget):
    """
    Settings interface to configure retail parameters, printer names,
    business headers, and light/dark theme variables.
    """
    settings_saved = Signal()  # Emits to trigger main window stylesheet/config refreshes

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 1. Business Info Group
        biz_group = QGroupBox("Business Profile Details")
        biz_layout = QFormLayout(biz_group)
        
        self.edit_name = QLineEdit()
        self.edit_address = QTextEdit()
        self.edit_address.setMaximumHeight(60)

        
        # Logo Select
        logo_layout = QHBoxLayout()
        self.edit_logo = QLineEdit()
        self.edit_logo.setReadOnly(True)
        self.logo_browse_btn = QPushButton("Browse...")
        self.logo_browse_btn.clicked.connect(self.browse_logo)
        logo_layout.addWidget(self.edit_logo)
        logo_layout.addWidget(self.logo_browse_btn)
        
        # PDF Save Directory field
        self.edit_pdf_dir = QLineEdit()
        self.edit_pdf_dir.setPlaceholderText("PDF Save Directory (optional)")
        self.pdf_dir_browse_btn = QPushButton("Browse...")
        self.pdf_dir_browse_btn.clicked.connect(self.browse_pdf_dir)
        
        # Footer message field (new)
        self.edit_footer = QLineEdit()
        self.edit_footer.setPlaceholderText("Footer Message (optional)")

        # Business Mobile
        self.edit_mobile = QLineEdit()
        self.edit_mobile.setPlaceholderText("Business Mobile (e.g. +919876543210)")
        
        biz_layout.addRow(QLabel("Business Name:"), self.edit_name)
        biz_layout.addRow(QLabel("Address:"), self.edit_address)
        biz_layout.addRow(QLabel("Business Mobile:"), self.edit_mobile)
        biz_layout.addRow(QLabel("Business Logo Path:"), logo_layout)
        biz_layout.addRow(QLabel("PDF Save Directory:"), self.edit_pdf_dir)
        
        # Footer Message
        biz_layout.addRow(QLabel("Footer Message:"), self.edit_footer)

        layout.addWidget(biz_group)

        # Legacy printer settings removed # 3. Application Defaults
        app_group = QGroupBox("Billing & UI Settings")
        app_layout = QFormLayout(app_group)
        
        self.combo_default_mode = QComboBox()
        self.combo_default_mode.addItems(["retail", "wholesale"])
        
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["dark", "light"])
        
        # Default customer presets
        self.edit_def_cust_name = QLineEdit()
        self.edit_def_cust_mobile = QLineEdit()
        self.edit_def_cust_address = QLineEdit()
        
        app_layout.addRow(QLabel("Default Billing Mode:"), self.combo_default_mode)
        app_layout.addRow(QLabel("UI Theme Style:"), self.combo_theme)
        app_layout.addRow(QLabel("Default Customer Name:"), self.edit_def_cust_name)
        app_layout.addRow(QLabel("Default Customer Mobile:"), self.edit_def_cust_mobile)
        app_layout.addRow(QLabel("Default Customer Address:"), self.edit_def_cust_address)
        
        layout.addWidget(app_group)

        # Bottom Buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        
        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("primary_btn")
        save_btn.setMinimumWidth(150)
        save_btn.clicked.connect(self.save_settings)
        bottom_layout.addWidget(save_btn)
        
        layout.addLayout(bottom_layout)
        layout.addStretch()

    def browse_pdf_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select PDF Save Directory")
        if directory:
            self.edit_pdf_dir.setText(directory)

# Legacy printer refresh method removed

    def browse_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Business Logo Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.edit_logo.setText(file_path)

    def load_settings(self):
        settings = self.db.get_all_settings()
        
        self.edit_name.setText(settings.get("business_name", ""))
        self.edit_address.setPlainText(settings.get("business_address", ""))
        self.edit_mobile.setText(settings.get("business_mobile", ""))
        
        # Logo path
        self.edit_logo.setText(settings.get("business_logo_path", ""))
        
# Removed printer config loading    
        self.edit_footer.setText(settings.get("footer_message", ""))
        
        # PDF Save Directory
        self.edit_pdf_dir.setText(settings.get("pdf_save_dir", ""))
        
        # UI configuration values
        mode_idx = self.combo_default_mode.findText(settings.get("default_mode", "retail"))
        if mode_idx >= 0:
            self.combo_default_mode.setCurrentIndex(mode_idx)
            
        theme_idx = self.combo_theme.findText(settings.get("theme", "dark"))
        if theme_idx >= 0:
            self.combo_theme.setCurrentIndex(theme_idx)
            
        self.edit_def_cust_name.setText(settings.get("default_customer_name", "Walk-in Customer"))
        self.edit_def_cust_mobile.setText(settings.get("default_customer_mobile", "0000000000"))
        self.edit_def_cust_address.setText(settings.get("default_customer_address", "Counter"))

    def save_settings(self):
        # Validate mobile number format (allows optional + and 10-15 digits)

        mobile = self.edit_def_cust_mobile.text().strip()
        # Validate business mobile (optional)
        bus_mobile = self.edit_mobile.text().strip()

            
        settings = {
            "business_name": self.edit_name.text().strip(),
            "business_address": self.edit_address.toPlainText().strip(),
            "business_mobile": bus_mobile,
            "business_logo_path": self.edit_logo.text().strip(),
            "footer_message": self.edit_footer.text().strip(),
            "pdf_save_dir": self.edit_pdf_dir.text().strip(),
# Removed printer config saving
            "default_mode": self.combo_default_mode.currentText(),
            "theme": self.combo_theme.currentText(),
            "default_customer_name": self.edit_def_cust_name.text().strip(),
            "default_customer_mobile": mobile,
            "default_customer_address": self.edit_def_cust_address.text().strip()
        }

        if not settings["business_name"]:
            QMessageBox.warning(self, "Validation Error", "Business Name is required.")
            return

        try:
            self.db.save_settings(settings)
            self.settings_saved.emit()
            QMessageBox.information(self, "Success", "Configuration settings saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
