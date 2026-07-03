from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QFormLayout)
from PySide6.QtCore import Qt

class ProductManagerWidget(QWidget):
    """
    Standard interface to search, update, add, and inspect inventory products.
    """
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.selected_product_id = None
        self.init_ui()
        self.refresh_table()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Top Bar: Add & Search
        top_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search products by name or code...")
        self.search_input.textChanged.connect(self.search_products)
        top_bar.addWidget(self.search_input)
        
        layout.addLayout(top_bar)

        # Split layout: List and Quick Edit panel
        split_layout = QHBoxLayout()
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Code", "Name", "Retail Rate (₹)", "Wholesale Rate (₹)", "Notes"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        
        # Header formatting
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch) # Stretch Name
        
        split_layout.addWidget(self.table, 3)

        # Form Panel for Add / Edit
        self.form_panel = QWidget()
        self.form_panel.setMaximumWidth(320)
        form_panel_layout = QVBoxLayout(self.form_panel)
        
        self.form_title = QLabel("<b>Add New Product</b>")
        self.form_title.setStyleSheet("font-size: 14px; color: #0d6efd;")
        form_panel_layout.addWidget(self.form_title)
        
        form_layout = QFormLayout()
        self.edit_code = QLineEdit()
        self.edit_code.setPlaceholderText("e.g. 101")
        
        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText("e.g. Nath Gold")
        
        self.edit_retail = QLineEdit()
        self.edit_retail.setPlaceholderText("e.g. 15000.00")
        
        self.edit_wholesale = QLineEdit()
        self.edit_wholesale.setPlaceholderText("e.g. 14200.00")
        
        self.edit_notes = QLineEdit()
        self.edit_notes.setPlaceholderText("Additional info")
        
        form_layout.addRow(QLabel("Product Code:"), self.edit_code)
        form_layout.addRow(QLabel("Product Name:"), self.edit_name)
        form_layout.addRow(QLabel("Retail Rate (₹):"), self.edit_retail)
        form_layout.addRow(QLabel("Wholesale Rate (₹):"), self.edit_wholesale)
        form_layout.addRow(QLabel("Notes:"), self.edit_notes)
        
        form_panel_layout.addLayout(form_layout)

        # Actions
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("primary_btn")
        self.save_btn.clicked.connect(self.save_product)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_form)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setObjectName("danger_btn")
        self.delete_btn.clicked.connect(self.delete_product)
        self.delete_btn.setEnabled(False) # Enable only when editing
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.clear_btn)
        form_panel_layout.addLayout(btn_layout)
        form_panel_layout.addWidget(self.delete_btn)
        form_panel_layout.addStretch()

        split_layout.addWidget(self.form_panel, 1)
        layout.addLayout(split_layout)

    def refresh_table(self, rows=None):
        if rows is None:
            rows = self.db.get_all_products()
            
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(row["code"]))
            self.table.setItem(i, 2, QTableWidgetItem(row["name"]))
            self.table.setItem(i, 3, QTableWidgetItem(f"{row['retail_rate']:,.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem(f"{row['wholesale_rate']:,.2f}"))
            self.table.setItem(i, 5, QTableWidgetItem(row["notes"]))
            
        self.clear_form()

    def search_products(self):
        query = self.search_input.text()
        if not query:
            self.refresh_table()
        else:
            self.refresh_table(self.db.search_products(query))

    def on_row_selected(self):
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            self.clear_form()
            return
            
        row = selected_ranges[0].topRow()
        self.selected_product_id = int(self.table.item(row, 0).text())
        self.edit_code.setText(self.table.item(row, 1).text())
        self.edit_name.setText(self.table.item(row, 2).text())
        
        # Clean comma separators for numeric parsing
        retail_str = self.table.item(row, 3).text().replace(",", "")
        wholesale_str = self.table.item(row, 4).text().replace(",", "")
        
        self.edit_retail.setText(retail_str)
        self.edit_wholesale.setText(wholesale_str)
        self.edit_notes.setText(self.table.item(row, 5).text())
        
        self.form_title.setText("<b>Edit Product</b>")
        self.delete_btn.setEnabled(True)
        self.save_btn.setText("Update")

    def clear_form(self):
        self.selected_product_id = None
        self.edit_code.clear()
        self.edit_name.clear()
        self.edit_retail.clear()
        self.edit_wholesale.clear()
        self.edit_notes.clear()
        self.form_title.setText("<b>Add New Product</b>")
        self.delete_btn.setEnabled(False)
        self.save_btn.setText("Save")

    def save_product(self):
        code = self.edit_code.text().strip()
        name = self.edit_name.text().strip()
        retail = self.edit_retail.text().strip()
        wholesale = self.edit_wholesale.text().strip()
        notes = self.edit_notes.text().strip()

        if not code or not name:
            QMessageBox.warning(self, "Validation Error", "Product Code and Product Name are required.")
            return

        try:
            retail_val = float(retail) if retail else 0.0
            wholesale_val = float(wholesale) if wholesale else 0.0
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Rates must be valid numeric values.")
            return

        try:
            if self.selected_product_id:
                # Update mode
                # Ensure unique check doesn't clash with others
                existing = self.db.get_product_by_code(code)
                if existing and existing["id"] != self.selected_product_id:
                    QMessageBox.warning(self, "Validation Error", f"Product code '{code}' is already assigned to '{existing['name']}'.")
                    return
                self.db.update_product(self.selected_product_id, code, name, retail_val, wholesale_val, notes)
                QMessageBox.information(self, "Success", "Product updated successfully.")
            else:
                # Add mode
                existing = self.db.get_product_by_code(code)
                if existing:
                    QMessageBox.warning(self, "Validation Error", f"Product code '{code}' is already assigned to '{existing['name']}'.")
                    return
                self.db.add_product(code, name, retail_val, wholesale_val, notes)
                QMessageBox.information(self, "Success", "Product added successfully.")
            
            self.refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save product: {e}")

    def delete_product(self):
        if not self.selected_product_id:
            return

        reply = QMessageBox.question(
            self, "Confirm Delete", 
            "Are you sure you want to delete this product? This will NOT delete past invoices.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.db.delete_product(self.selected_product_id)
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete product: {e}")
            self.clear_form()
