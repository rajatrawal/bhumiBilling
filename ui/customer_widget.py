from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QDialog, QFormLayout, QDialogButtonBox)
from PySide6.QtCore import Qt, Signal

class QuickCustomerDialog(QDialog):
    """
    Inline modal dialog triggered by Ctrl+N to add customers
    without breaking the keyboard flow.
    """
    customer_created = Signal(int) # Emits the newly created customer's database ID

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle("Quick Add Customer")
        self.setMinimumWidth(350)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Customer Name (Required)")
        
        self.mobile_input = QLineEdit()
        self.mobile_input.setPlaceholderText("10-Digit Mobile Number")
        
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Address Details")
        
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Important billing notes / GST details")

        form_layout.addRow(QLabel("<b>Name:</b>"), self.name_input)
        form_layout.addRow(QLabel("<b>Mobile:</b>"), self.mobile_input)
        form_layout.addRow(QLabel("<b>Address:</b>"), self.address_input)
        form_layout.addRow(QLabel("<b>Notes:</b>"), self.notes_input)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_customer)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Hotkeys: Enter submits, Esc closes
        self.name_input.setFocus()

    def save_customer(self):
        name = self.name_input.text().strip()
        mobile = self.mobile_input.text().strip()
        address = self.address_input.text().strip()
        notes = self.notes_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation Error", "Customer Name is required.")
            self.name_input.setFocus()
            return

        try:
            cust_id = self.db.add_customer(name, mobile, address, notes)
            self.customer_created.emit(cust_id)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save customer: {e}")


class CustomerManagerWidget(QWidget):
    """
    Standard customer view to search, inspect, add, edit, and delete customers.
    """
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.selected_customer_id = None
        self.init_ui()
        self.refresh_table()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Top Bar: Add & Search
        top_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search customers by name or mobile...")
        self.search_input.textChanged.connect(self.search_customers)
        top_bar.addWidget(self.search_input)

        add_btn = QPushButton("Add Customer")
        add_btn.setObjectName("primary_btn")
        add_btn.clicked.connect(self.open_add_dialog)
        top_bar.addWidget(add_btn)
        
        layout.addLayout(top_bar)

        # Split layout: List and Quick Edit pane
        split_layout = QHBoxLayout()
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Mobile", "Address", "Notes"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        
        # Header formatting
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch) # Stretch Address
        
        split_layout.addWidget(self.table, 3)

        # Quick Edit Form Panel
        edit_panel = QWidget()
        edit_panel.setMaximumWidth(320)
        edit_layout = QVBoxLayout(edit_panel)
        
        form_layout = QFormLayout()
        self.edit_name = QLineEdit()
        self.edit_mobile = QLineEdit()
        self.edit_address = QLineEdit()
        self.edit_notes = QLineEdit()
        
        form_layout.addRow(QLabel("Name:"), self.edit_name)
        form_layout.addRow(QLabel("Mobile:"), self.edit_mobile)
        form_layout.addRow(QLabel("Address:"), self.edit_address)
        form_layout.addRow(QLabel("Notes:"), self.edit_notes)
        
        edit_layout.addLayout(form_layout)

        # Actions
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.setObjectName("success_btn")
        self.save_btn.clicked.connect(self.save_customer_changes)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setObjectName("danger_btn")
        self.delete_btn.clicked.connect(self.delete_customer)
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.delete_btn)
        edit_layout.addLayout(btn_layout)
        edit_layout.addStretch()

        split_layout.addWidget(edit_panel, 1)
        layout.addLayout(split_layout)

    def refresh_table(self, rows=None):
        if rows is None:
            rows = self.db.get_all_customers()
            
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(row["name"]))
            self.table.setItem(i, 2, QTableWidgetItem(row["mobile"]))
            self.table.setItem(i, 3, QTableWidgetItem(row["address"]))
            self.table.setItem(i, 4, QTableWidgetItem(row["notes"]))
            
        self.clear_form()

    def search_customers(self):
        query = self.search_input.text()
        if not query:
            self.refresh_table()
        else:
            self.refresh_table(self.db.search_customers(query))

    def on_row_selected(self):
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            self.clear_form()
            return
            
        row = selected_ranges[0].topRow()
        self.selected_customer_id = int(self.table.item(row, 0).text())
        self.edit_name.setText(self.table.item(row, 1).text())
        self.edit_mobile.setText(self.table.item(row, 2).text())
        self.edit_address.setText(self.table.item(row, 3).text())
        self.edit_notes.setText(self.table.item(row, 4).text())

    def clear_form(self):
        self.selected_customer_id = None
        self.edit_name.clear()
        self.edit_mobile.clear()
        self.edit_address.clear()
        self.edit_notes.clear()

    def open_add_dialog(self):
        dialog = QuickCustomerDialog(self.db, self)
        dialog.customer_created.connect(lambda: self.refresh_table())
        dialog.exec()

    def save_customer_changes(self):
        if not self.selected_customer_id:
            QMessageBox.information(self, "Notice", "Please select a customer from the table to edit.")
            return

        name = self.edit_name.text().strip()
        mobile = self.edit_mobile.text().strip()
        address = self.edit_address.text().strip()
        notes = self.edit_notes.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation Error", "Name is required.")
            return

        try:
            self.db.update_customer(self.selected_customer_id, name, mobile, address, notes)
            self.refresh_table()
            QMessageBox.information(self, "Success", "Customer details updated successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update customer: {e}")

    def delete_customer(self):
        if not self.selected_customer_id:
            QMessageBox.information(self, "Notice", "Please select a customer from the table to delete.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete", 
            "Are you sure you want to delete this customer? This will NOT delete past invoices.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.db.delete_customer(self.selected_customer_id)
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete customer: {e}")
