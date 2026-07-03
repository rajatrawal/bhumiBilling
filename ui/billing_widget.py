import os
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QListWidget,
    QListWidgetItem, QComboBox, QFormLayout, QSizePolicy, QFileDialog,
    QStyledItemDelegate, QSpinBox
)
from PySide6.QtGui import QDoubleValidator,QKeyEvent


class QtyDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QSpinBox(parent)
        editor.setMinimum(0)
        editor.setMaximum(10000)
        editor.setSingleStep(1)
        return editor
    def setEditorData(self, editor, index):
        value = int(index.model().data(index, Qt.EditRole))
        editor.setValue(value)
    def setModelData(self, editor, model, index):
        editor.interpretText()
        value = editor.value()
        model.setData(index, str(value), Qt.EditRole)
        # Update active_items
        row = index.row()
        if 0 <= row < len(self.parent().active_items):
            self.parent().active_items[row]["qty"] = float(value)
            self.parent().calculate_live_totals()


class RateDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(QDoubleValidator(0, 1e9, 2, editor))
        return editor
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        editor.setText(str(value))
    def setModelData(self, editor, model, index):
        text = editor.text()
        try:
            value = float(text)
        except ValueError:
            value = 0.0
        model.setData(index, f"{value:.2f}", Qt.EditRole)
        row = index.row()
        if 0 <= row < len(self.parent().active_items):
            self.parent().active_items[row]["rate"] = value
            self.parent().calculate_live_totals()
from PySide6.QtCore import Qt, QTimer, QPoint

# PDF generation for A5 layout
from pdf_generator_a5 import generate_invoice_pdf
from print_manager import PrintManager
from utils.whatsapp import share_invoice_via_whatsapp
from config import PDF_DIR
from ui.customer_widget import QuickCustomerDialog

class BillingWidget(QWidget):
    """
    Main invoice workspace layout. Optimizes speed of billing via keyboard focus routines,
    real-time autocomplete, and single-line expression processing.
    """
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.active_items = []
        self.selected_customer = None
        self.current_bill_no = ""
        self.app_settings = {}
        
        self.init_ui()
        self.reset_billing_session()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # ----------------------------------------------------
        # 1. Header Card (Bill No, Customer, Mode)
        # ----------------------------------------------------
        header_card = QWidget()
        header_card.setObjectName("HeaderCard")
        header_layout = QHBoxLayout(header_card)

        # Bill No & Date
        self.lbl_bill_no = QLabel("Bill No: BAJ-2026-0000")
        self.lbl_bill_no.setStyleSheet("font-size: 16px; font-weight: bold; color: #0d6efd;")
        header_layout.addWidget(self.lbl_bill_no)

        header_layout.addSpacing(20)

        # Customer Section
        header_layout.addWidget(QLabel("<b>Customer [Ctrl+M]:</b>"))
        self.cust_search = QLineEdit()
        self.cust_search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cust_search.setMinimumHeight(24)
        self.cust_search.setPlaceholderText("Search customer name / mobile...")
        self.cust_search.setMaximumWidth(280)
        self.cust_search.textChanged.connect(self.search_customers_dropdown)
        self.cust_search.installEventFilter(self)
        header_layout.addWidget(self.cust_search)

        # Add Customer Shortcut
        add_cust_btn = QPushButton("+ New [Ctrl+N]")
        add_cust_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        add_cust_btn.setMinimumHeight(24)
        add_cust_btn.setFocusPolicy(Qt.NoFocus)
        add_cust_btn.clicked.connect(self.open_quick_customer_dialog)
        header_layout.addWidget(add_cust_btn)

        header_layout.addStretch()

        # Billing Mode (Retail / Wholesale)
        header_layout.addWidget(QLabel("<b>Mode [F3]:</b>"))
        self.mode_combo = QComboBox()
        self.mode_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.mode_combo.setMinimumHeight(24)
        self.mode_combo.addItems(["Retail", "Wholesale"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        self.mode_combo.setFocusPolicy(Qt.NoFocus)
        header_layout.addWidget(self.mode_combo)

        main_layout.addWidget(header_card)

        # ----------------------------------------------------
        # 2. Product Search & Detail Inputs
        # ----------------------------------------------------
        search_layout = QHBoxLayout()
        
        # Product Search
        prod_search_layout = QVBoxLayout()
        lbl_search = QLabel("Smart Product Search [F2]")
        lbl_search.setObjectName("input_label")
        prod_search_layout.addWidget(lbl_search)
        
        self.prod_search = QLineEdit()
        self.prod_search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.prod_search.setMinimumHeight(24)
        self.prod_search.setPlaceholderText("Code, Name, or Expression (e.g. 101 2 15000)")
        self.prod_search.textChanged.connect(self.search_products_dropdown)
        self.prod_search.installEventFilter(self)
        prod_search_layout.addWidget(self.prod_search)
        search_layout.addLayout(prod_search_layout, 4)

        # Qty Input
        qty_layout = QVBoxLayout()
        lbl_qty = QLabel("Qty")
        lbl_qty.setObjectName("input_label")
        qty_layout.addWidget(lbl_qty)
        self.qty_input = QLineEdit()
        self.qty_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.qty_input.setMinimumHeight(24)
        self.qty_input.setText("1")
        self.qty_input.installEventFilter(self)
        qty_layout.addWidget(self.qty_input)
        search_layout.addLayout(qty_layout, 1)

        # Rate Input
        rate_layout = QVBoxLayout()
        lbl_rate = QLabel("Rate (₹)")
        lbl_rate.setObjectName("input_label")
        rate_layout.addWidget(lbl_rate)
        self.rate_input = QLineEdit()
        self.rate_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.rate_input.setMinimumHeight(24)
        self.rate_input.installEventFilter(self)
        rate_layout.addWidget(self.rate_input)
        search_layout.addLayout(rate_layout, 2)

        main_layout.addLayout(search_layout)

        # ----------------------------------------------------
        # Autocomplete Floaters (Created but invisible initially)
        # ----------------------------------------------------
        self.prod_popup = QListWidget(self)
        self.prod_popup.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.prod_popup.setFocusPolicy(Qt.NoFocus)
        self.prod_popup.itemClicked.connect(self.on_product_popup_selected)
        self.prod_popup.hide()

        self.cust_popup = QListWidget(self)
        self.cust_popup.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.cust_popup.setFocusPolicy(Qt.NoFocus)
        self.cust_popup.itemClicked.connect(self.on_customer_popup_selected)
        self.cust_popup.hide()

        # ----------------------------------------------------
        # 3. Item Table
        # ----------------------------------------------------
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Sr No",
            "Code",
            "Description",
            "Qty",
            "Rate (₹)",
            "Total (₹)"
        ])

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setFocusPolicy(Qt.ClickFocus)

        h_header = self.table.horizontalHeader()

        # Fixed widths for small columns
        h_header.setSectionResizeMode(0, QHeaderView.Fixed)      # Sr No
        h_header.setSectionResizeMode(1, QHeaderView.Fixed)      # Code
        h_header.setSectionResizeMode(2, QHeaderView.Stretch)    # Description
        h_header.setSectionResizeMode(3, QHeaderView.Fixed)      # Qty
        h_header.setSectionResizeMode(4, QHeaderView.Fixed)      # Rate
        h_header.setSectionResizeMode(5, QHeaderView.Fixed)      # Total

        # Column widths
        self.table.setColumnWidth(0, 60)    # Sr No
        self.table.setColumnWidth(1, 100)   # Code
        # Description automatically takes remaining space
        self.table.setColumnWidth(3, 100)   # Qty
        self.table.setColumnWidth(4, 120)   # Rate
        self.table.setColumnWidth(5, 140)   # Total

        # Delegates
        self.table.setItemDelegateForColumn(3, QtyDelegate(self))
        self.table.setItemDelegateForColumn(4, RateDelegate(self))
 
        
        main_layout.addWidget(self.table)

        # ----------------------------------------------------
        # 4. Summary & Billing Actions Drawer
        # ----------------------------------------------------
        bottom_drawer = QHBoxLayout()

        # Payment & Discount Left side Form
        form_panel = QFormLayout()
        
        self.discount_input = QLineEdit()
        self.discount_input.setPlaceholderText("e.g. 10% or 500")
        self.discount_input.textChanged.connect(self.calculate_live_totals)
        self.discount_input.installEventFilter(self)
        
        self.pay_status_combo = QComboBox()
        self.pay_status_combo.addItems(["PAID", "PENDING", "PARTIAL"])
        self.pay_status_combo.currentTextChanged.connect(self.on_payment_status_changed)
        self.pay_status_combo.setFocusPolicy(Qt.NoFocus)
        
        self.pay_mode_combo = QComboBox()
        self.pay_mode_combo.addItems(["Cash", "UPI", "Card", "Other"])
        self.pay_mode_combo.setFocusPolicy(Qt.NoFocus)
        
        self.paid_amt_input = QLineEdit()
        self.paid_amt_input.textChanged.connect(self.on_paid_amount_edited)
        self.paid_amt_input.installEventFilter(self)
        
        self.balance_label = QLabel("₹0.00")
        self.balance_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #dc3545;")

        form_panel.addRow(QLabel("<b>[F6] Discount:</b>"), self.discount_input)
        form_panel.addRow(QLabel("<b>[Ctrl+D] Payment:</b>"), self.pay_status_combo)
        form_panel.addRow(QLabel("<b>Payment Mode:</b>"), self.pay_mode_combo)
        form_panel.addRow(QLabel("<b>Paid Amt (₹):</b>"), self.paid_amt_input)
        form_panel.addRow(QLabel("<b>Balance Due:</b>"), self.balance_label)
        
        bottom_drawer.addLayout(form_panel, 2)

        # Space
        bottom_drawer.addStretch(1)

        # Totals Display Card
        totals_card = QWidget()
        totals_card.setObjectName("HeaderCard")
        totals_layout = QFormLayout(totals_card)
        
        self.lbl_gross = QLabel("₹0.00")
        self.lbl_gross.setStyleSheet("font-size: 14px;")
        
        self.lbl_discount_amt = QLabel("₹0.00")
        self.lbl_discount_amt.setStyleSheet("font-size: 14px; color: #ffc107;")
        
        self.lbl_net = QLabel("₹0.00")
        self.lbl_net.setStyleSheet("font-size: 20px; font-weight: bold; color: #198754;")

        totals_layout.addRow(QLabel("<b>Gross Total:</b>"), self.lbl_gross)
        totals_layout.addRow(QLabel("<b>Discount Amount:</b>"), self.lbl_discount_amt)
        totals_layout.addRow(QLabel("<b>Net Payable:</b>"), self.lbl_net)
        
        bottom_drawer.addWidget(totals_card, 2)

        # Action Buttons Right Column
        btn_col = QVBoxLayout()
        
        self.save_btn = QPushButton("Save Bill (Ctrl+S)")
        self.save_btn.clicked.connect(self.save_invoice_action)
        self.save_btn.setFocusPolicy(Qt.NoFocus)
        btn_col.addWidget(self.save_btn)
        
        self.print_btn = QPushButton("Print Invoice (F9)")
        self.print_btn.setObjectName("success_btn")
        self.print_btn.clicked.connect(self.save_and_print_action)
        self.print_btn.setFocusPolicy(Qt.NoFocus)
        btn_col.addWidget(self.print_btn)






        # New Bill button – clears UI for next invoice without losing saved one
        self.new_bill_btn = QPushButton("New Bill (Ctrl+N)")
        self.new_bill_btn.setObjectName("primary_btn")
        self.new_bill_btn.clicked.connect(self.new_bill_flow)
        self.new_bill_btn.setFocusPolicy(Qt.NoFocus)
        btn_col.addWidget(self.new_bill_btn)
        
        bottom_drawer.addLayout(btn_col, 2)

        main_layout.addLayout(bottom_drawer)

        # ----------------------------------------------------
        # 5. Recent Products Horizontal Tray
        # ----------------------------------------------------
        recents_bar = QHBoxLayout()
        recents_bar.addWidget(QLabel("<b>[F4] Recents:</b>"))
        self.recents_layout = QHBoxLayout()
        recents_bar.addLayout(self.recents_layout)
        recents_bar.addStretch()
        main_layout.addLayout(recents_bar)

    # ==========================================
    # WORKSPACE SESSION & RESET
    # ==========================================
    def reset_billing_session(self):
        """Clears billing table inputs, fetches next invoice sequential number, and loads recents."""
        self.active_items.clear()
        self.table.setRowCount(0)
        
        self.app_settings = self.db.get_all_settings()
        self.current_bill_no = self.db.generate_next_bill_number()
        self.lbl_bill_no.setText(f"Bill No: {self.current_bill_no}")
        
        # Load Defaults from settings
        mode = self.app_settings.get("default_mode", "retail")
        self.mode_combo.setCurrentText(mode.capitalize())
        
        self.selected_customer = {
            "name": self.app_settings.get("default_customer_name", "Walk-in Customer"),
            "mobile": self.app_settings.get("default_customer_mobile", "0000000000"),
            "address": self.app_settings.get("default_customer_address", "Counter")
        }
        self.cust_search.setText(f"{self.selected_customer['name']} ({self.selected_customer['mobile']})")
        
        self.prod_search.clear()
        self.qty_input.setText("1")
        self.rate_input.clear()
        self.discount_input.clear()
        
        self.pay_status_combo.setCurrentText("PAID")
        self.pay_mode_combo.setCurrentText("Cash")
        self.paid_amt_input.clear()
        
        # Refresh Recent products tray
        self.refresh_recents_tray()
        
        # Auto focus Smart Search
        QTimer.singleShot(50, self.prod_search.setFocus)
        self.db.clear_draft()

    def new_bill_flow(self):
        """Wraps reset logic."""
        self.reset_billing_session()

    def load_recovered_draft(self, draft):
        """Restore workspace details from database crash draft table."""
        self.active_items.clear()
        self.table.setRowCount(0)
        
        self.app_settings = self.db.get_all_settings()
        self.current_bill_no = self.db.generate_next_bill_number()
        
        # Retrieve customer
        cust_id = draft.get("customer_id")
        if cust_id:
            with self.db.get_connection() as conn:
                r = conn.execute("SELECT * FROM customers WHERE id = ?", (cust_id,)).fetchone()
                if r:
                    self.selected_customer = dict(r)
        else:
            self.selected_customer = {
                "name": self.app_settings.get("default_customer_name", "Walk-in Customer"),
                "mobile": self.app_settings.get("default_customer_mobile", "0000000000"),
                "address": self.app_settings.get("default_customer_address", "Counter")
            }
            
        self.cust_search.setText(f"{self.selected_customer['name']} ({self.selected_customer['mobile']})")
        self.mode_combo.setCurrentText(draft.get("mode", "retail").capitalize())
        
        # Restore Items
        for item in draft.get("items", []):
            self.active_items.append({
                "product_id": item.get("product_id"),
                "product_code": item["product_code"],
                "product_name": item["product_name"],
                "qty": float(item["qty"]),
                "rate": float(item["rate"])
            })
            
        self.discount_input.setText(str(draft.get("discount_value", "")))
        self.pay_status_combo.setCurrentText(draft.get("payment_status", "paid").upper())
        self.paid_amt_input.setText(str(draft.get("paid_amount", "")))
        
        self.refresh_table()
        self.calculate_live_totals()
        
        QTimer.singleShot(50, self.prod_search.setFocus)

    def trigger_draft_save(self):
        """Pushes active unsaved layout components to draft storage on keystroke ticks."""
        cust_id = self.selected_customer.get("id") if self.selected_customer else None
        mode = self.mode_combo.currentText().lower()
        
        disc_val = 0.0
        disc_type = "none"
        disc_str = self.discount_input.text().strip()
        if disc_str:
            if disc_str.endswith("%"):
                disc_type = "percentage"
                disc_val = float(disc_str[:-1]) if len(disc_str) > 1 else 0.0
            else:
                disc_type = "amount"
                disc_val = float(disc_str)
                
        payment_status = self.pay_status_combo.currentText().lower()
        
        try:
            paid_amt = float(self.paid_amt_input.text().strip()) if self.paid_amt_input.text().strip() else 0.0
        except ValueError:
            paid_amt = 0.0
            
        self.db.save_draft(cust_id, mode, disc_type, disc_val, payment_status, paid_amt, self.active_items)

    # ==========================================
    # RECENTS TRAY MANAGEMENT
    # ==========================================
    def refresh_recents_tray(self):
        # Clear layout
        while self.recents_layout.count():
            item = self.recents_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        recents = self.db.get_recent_products()
        for prod in recents[:5]: # Show top 5 recents in standard view
            btn = QPushButton(f"{prod['name']} ({prod['code']})")
            btn.setFocusPolicy(Qt.NoFocus)
            # Bind click
            btn.clicked.connect(lambda checked=False, p=prod: self.on_recent_clicked(p))
            self.recents_layout.addWidget(btn)

    def on_recent_clicked(self, product):
        # Auto-fill search with code and select it
        self.prod_search.setText(product["code"])
        self.on_product_selected(product)

    # ==========================================
    # SINGLE-LINE QUERY PARSING ENGINE
    # ==========================================
    def parse_single_line_expression(self, text):
        """
        Parses input string patterns like:
        - '101 2 12000' -> code/name='101', qty=2.0, rate=12000.0
        - 'Earrings 5' -> code/name='Earrings', qty=5.0
        - 'Earrings' -> code/name='Earrings'
        """
        parts = text.strip().split()
        if not parts:
            return None

        qty = 1.0
        rate = None
        search_parts = list(parts)

        # Evaluate token floats from right to left
        if len(search_parts) >= 3:
            try:
                # Check last two parts for qty and rate
                val_last = float(search_parts[-1])
                val_prev = float(search_parts[-2])
                rate = val_last
                qty = val_prev
                search_parts = search_parts[:-2]
            except ValueError:
                # Fallback: check only last part for qty
                try:
                    val_last = float(search_parts[-1])
                    qty = val_last
                    search_parts = search_parts[:-1]
                except ValueError:
                    pass
        elif len(search_parts) == 2:
            try:
                val_last = float(search_parts[-1])
                qty = val_last
                search_parts = search_parts[:-1]
            except ValueError:
                pass

        search_term = " ".join(search_parts)
        return search_term, qty, rate

    def process_smart_enter(self):
        """Processes single‑line expressions and adds them to the bill.
        If only a product code/name is entered (qty == 1.0 and no rate), focus on the quantity input for manual entry.
        """
        text = self.prod_search.text().strip()
        if not text:
            return
        parsed = self.parse_single_line_expression(text)
        if not parsed:
            return
        search_term, qty, rate = parsed
        matches = self.db.search_products(search_term)
        if not matches:
            QMessageBox.warning(self, "Search Warning", f"No products match: '{search_term}'")
            return
        prod = matches[0]
        if qty == 1.0 and rate is None:
            self.prod_search.setProperty("selected_product", prod)
            self.prod_search.setText(prod["name"])
            self.rate_input.clear()
            self.qty_input.setFocus()
            self.qty_input.selectAll()
            return
        if rate is None:
            mode = self.mode_combo.currentText().lower()
            rate = prod["wholesale_rate"] if mode == "wholesale" else prod["retail_rate"]
        self.add_item_to_bill(prod, qty, rate)
        self.prod_search.clear()
        self.prod_popup.hide()

    # ==========================================
    # AUTOCOMPLETE DROPDOWN UTILS
    # ==========================================
    def search_products_dropdown(self, text):
        # Position and display popup below the line input
        if not text:
            self.prod_popup.hide()
            return

        # If it looks like single line entry with spaces, don't show dropdown to prevent flicker
        if " " in text.strip():
            self.prod_popup.hide()
            return

        matches = self.db.search_products(text)
        if not matches:
            self.prod_popup.hide()
            return

        # Auto-selection rule: If only 1 match exists and matches code exactly
        if len(matches) == 1 and matches[0]["code"].lower() == text.strip().lower():
            self.on_product_selected(matches[0])
            self.prod_popup.hide()
            return

        # Pop dropdown list
        self.prod_popup.clear()
        for prod in matches:
            item = QListWidgetItem(f"{prod['code']} - {prod['name']} (Retail: ₹{prod['retail_rate']:.0f})")
            item.setData(Qt.UserRole, prod)
            self.prod_popup.addItem(item)

        # Reposition popover
        pos = self.prod_search.mapToGlobal(QPoint(0, self.prod_search.height()))
        self.prod_popup.setGeometry(pos.x(), pos.y(), self.prod_search.width(), 160)
        self.prod_popup.show()

    def search_customers_dropdown(self, text):
        if not text:
            self.cust_popup.hide()
            return

        # Skip if parenthesis match (indicating customer already selected)
        if "(" in text and ")" in text:
            return

        matches = self.db.search_customers(text)
        if not matches:
            self.cust_popup.hide()
            return

        self.cust_popup.clear()
        for cust in matches:
            item = QListWidgetItem(f"{cust['name']} ({cust['mobile']})")
            item.setData(Qt.UserRole, cust)
            self.cust_popup.addItem(item)

        pos = self.cust_search.mapToGlobal(QPoint(0, self.cust_search.height()))
        self.cust_popup.setGeometry(pos.x(), pos.y(), self.cust_search.width(), 160)
        self.cust_popup.show()

    def on_product_popup_selected(self, list_item):
        prod = list_item.data(Qt.UserRole)
        self.on_product_selected(prod)
        self.prod_popup.hide()

    def on_customer_popup_selected(self, list_item):
        cust = list_item.data(Qt.UserRole)
        self.selected_customer = cust
        self.cust_search.setText(f"{cust['name']} ({cust['mobile']})")
        self.cust_popup.hide()
        self.prod_search.setFocus()
        self.trigger_draft_save()

    def on_product_selected(self, product):
        """Called when a single product is definitively chosen."""
        # Lock selection details
        self.prod_search.setText(product["name"])
        self.prod_search.setProperty("selected_product", product)
        
        # Pick rate
        mode = self.mode_combo.currentText().lower()
        rate = product["wholesale_rate"] if mode == "wholesale" else product["retail_rate"]
        self.rate_input.setText(f"{rate:.2f}")
        
        # Shift focus
        self.qty_input.setFocus()
        self.qty_input.selectAll()

    def on_mode_changed(self):
        """Update active rate input if billing mode switches."""
        prod = self.prod_search.property("selected_product")
        if prod:
            mode = self.mode_combo.currentText().lower()
            rate = prod["wholesale_rate"] if mode == "wholesale" else prod["retail_rate"]
            self.rate_input.setText(f"{rate:.2f}")
        self.trigger_draft_save()

    # ==========================================
    # ITEM MANAGEMENT & TABLES
    # ==========================================
    def add_item_to_bill(self, product, qty, rate):
        # Verify duplicate code and same rate exists inside current session table
        for item in self.active_items:
            if item["product_code"] == product["code"] and item["rate"] == rate:
                item["qty"] += qty
                self.refresh_table()
                self.calculate_live_totals()
                self.trigger_draft_save()
                return

        self.active_items.append({
            "product_id": product["id"],
            "product_code": product["code"],
            "product_name": product["name"],
            "qty": qty,
            "rate": rate
        })
        self.refresh_table()
        self.calculate_live_totals()
        self.trigger_draft_save()

    def refresh_table(self):
        self.table.setRowCount(len(self.active_items))
        for idx, item in enumerate(self.active_items, 1):
            qty_val = item["qty"]
            qty_str = f"{qty_val:.3f}" if not qty_val.is_integer() else f"{int(qty_val)}"
            
            self.table.setItem(idx-1, 0, QTableWidgetItem(str(idx)))
            self.table.setItem(idx-1, 1, QTableWidgetItem(item["product_code"]))
            self.table.setItem(idx-1, 2, QTableWidgetItem(item["product_name"]))
            self.table.setItem(idx-1, 3, QTableWidgetItem(qty_str))
            self.table.setItem(idx-1, 4, QTableWidgetItem(f"{item['rate']:,.2f}"))
            # Set total amount for this row
            total = item["qty"] * item["rate"]
            self.table.setItem(idx-1, 5, QTableWidgetItem(f"{total:,.2f}"))
    def delete_selected_item(self):
        row = self.table.currentRow()
        if row >= 0 and row < len(self.active_items):
            self.active_items.pop(row)
            self.refresh_table()
            self.calculate_live_totals()
            self.trigger_draft_save()

    # ==========================================
    # TOTALS & PAYMENT LIVE LOGIC
    # ==========================================
    def calculate_live_totals(self):
        gross = sum(item["qty"] * item["rate"] for item in self.active_items)
        self.lbl_gross.setText(f"₹{gross:,.2f}")
        
        # Calculate discount
        disc_str = self.discount_input.text().strip()
        discount_amount = 0.0
        if disc_str:
            try:
                if disc_str.endswith("%"):
                    pct = float(disc_str[:-1])
                    discount_amount = (pct / 100.0) * gross
                else:
                    discount_amount = float(disc_str)
            except ValueError:
                pass
                
        self.lbl_discount_amt.setText(f"₹{discount_amount:,.2f}")
        
        net = max(0.0, gross - discount_amount)
        self.lbl_net.setText(f"₹{net:,.2f}")
        
        # Live payment updates
        status = self.pay_status_combo.currentText()
        if status == "PAID":
            self.paid_amt_input.setText(f"{net:.2f}")
            self.balance_label.setText("₹0.00")
        elif status == "PENDING":
            self.paid_amt_input.setText("0.00")
            self.balance_label.setText(f"₹{net:,.2f}")
        else: # Partial
            try:
                paid = float(self.paid_amt_input.text())
            except ValueError:
                paid = 0.0
            bal = max(0.0, net - paid)
            self.balance_label.setText(f"₹{bal:,.2f}")

    def on_payment_status_changed(self, text):
        self.calculate_live_totals()
        self.trigger_draft_save()

    def on_paid_amount_edited(self, text):
        if self.pay_status_combo.currentText() == "PARTIAL":
            self.calculate_live_totals()
            self.trigger_draft_save()

    # ==========================================
    # KEYBOARD ROUTINGS & INLINE EVENTS
    # ==========================================
    def eventFilter(self, obj, event):
        """Binds arrow navigate logic for autocompletes, Esc cancels, and Enter progressions."""
        if event.type() == QKeyEvent.KeyPress:
            key = event.key()
            
            # Autocomplete product dropdown routing
            if obj == self.prod_search and self.prod_popup.isVisible():
                if key in (Qt.Key_Up, Qt.Key_Down):
                    # Route navigation keystrokes directly to the popup list
                    self.prod_popup.setFocus()
                    self.prod_popup.keyPressEvent(event)
                    self.prod_search.setFocus() # Re-focus input immediately
                    return True
                elif key in (Qt.Key_Enter, Qt.Key_Return):
                    if self.prod_popup.currentItem():
                        self.on_product_popup_selected(self.prod_popup.currentItem())
                    else:
                        self.process_smart_enter()
                    return True
                elif key == Qt.Key_Escape:
                    self.prod_popup.hide()
                    return True

            # Autocomplete customer dropdown routing
            elif obj == self.cust_search and self.cust_popup.isVisible():
                if key in (Qt.Key_Up, Qt.Key_Down):
                    self.cust_popup.setFocus()
                    self.cust_popup.keyPressEvent(event)
                    self.cust_search.setFocus()
                    return True
                elif key in (Qt.Key_Enter, Qt.Key_Return):
                    if self.cust_popup.currentItem():
                        self.on_customer_popup_selected(self.cust_popup.currentItem())
                    return True
                elif key == Qt.Key_Escape:
                    self.cust_popup.hide()
                    return True

            # Standard Input Enter Advance workflows
            elif obj == self.prod_search and not self.prod_popup.isVisible():
                if key in (Qt.Key_Enter, Qt.Key_Return):
                    # Smart process line
                    self.process_smart_enter()
                    return True
                    
            elif obj == self.qty_input:
                if key in (Qt.Key_Enter, Qt.Key_Return):
                    self.rate_input.setFocus()
                    self.rate_input.selectAll()
                    return True

            elif obj == self.rate_input:
                if key in (Qt.Key_Enter, Qt.Key_Return):
                    prod = self.prod_search.property("selected_product")
                    if prod:
                        try:
                            qty = float(self.qty_input.text().strip())
                            rate = float(self.rate_input.text().strip())
                            self.add_item_to_bill(prod, qty, rate)
                            # Reset inputs for next entry
                            self.prod_search.clear()
                            self.qty_input.setText("1")
                            self.rate_input.clear()
                            self.prod_search.setFocus()
                        except ValueError:
                            QMessageBox.warning(self, "Input Error", "Please enter valid numeric values for quantity and rate.")
                    return True
                    
            elif obj == self.discount_input:
                if key in (Qt.Key_Enter, Qt.Key_Return):
                    self.prod_search.setFocus()
                    return True

            # Global escapes
            if key == Qt.Key_Escape:
                self.prod_popup.hide()
                self.cust_popup.hide()
                
        return super().eventFilter(obj, event)

    def open_quick_customer_dialog(self):
        dialog = QuickCustomerDialog(self.db, self)
        dialog.customer_created.connect(self.on_quick_customer_added)
        dialog.exec()

    def on_quick_customer_added(self, cust_id):
        # Load newly created customer instantly
        with self.db.get_connection() as conn:
            r = conn.execute("SELECT * FROM customers WHERE id = ?", (cust_id,)).fetchone()
            if r:
                self.selected_customer = dict(r)
                self.cust_search.setText(f"{r['name']} ({r['mobile']})")
                self.prod_search.setFocus()
                self.trigger_draft_save()

    # ==========================================
    # SAVE & PRINT INVOICE WORKFLOWS
    # ==========================================
    def prepare_invoice_data(self):
        if not self.active_items:
            QMessageBox.warning(self, "Warning", "Cannot save an empty invoice.")
            return None

        # Resolve discount properties
        disc_type = "none"
        disc_val = 0.0
        disc_str = self.discount_input.text().strip()
        if disc_str:
            if disc_str.endswith("%"):
                disc_type = "percentage"
                disc_val = float(disc_str[:-1]) if len(disc_str) > 1 else 0.0
            else:
                disc_type = "amount"
                disc_val = float(disc_str)

        # Totals
        gross = sum(it["qty"] * it["rate"] for it in self.active_items)
        disc_amt = (disc_val/100.0 * gross) if disc_type == "percentage" else disc_val
        net = max(0.0, gross - disc_amt)

        # Paid details
        pay_status = self.pay_status_combo.currentText().lower()
        try:
            paid = float(self.paid_amt_input.text().strip()) if self.paid_amt_input.text().strip() else 0.0
        except ValueError:
            paid = net if pay_status == "paid" else 0.0
            
        pending = max(0.0, net - paid)

        # Retrieve DB customer ID
        cust_id = self.selected_customer.get("id") if self.selected_customer else None

        return {
            "bill_no": self.current_bill_no,
            "customer_id": cust_id,
            "customer_name": self.selected_customer.get("name") if self.selected_customer else "Walk-in Customer",
            "customer_mobile": self.selected_customer.get("mobile") if self.selected_customer else "0000000000",
            "customer_address": self.selected_customer.get("address") if self.selected_customer else "Counter",
            "mode": self.mode_combo.currentText().lower(),
            "discount_type": disc_type,
            "discount_value": disc_val,
            "gross_total": gross,
            "net_total": net,
            "payment_status": pay_status,
            "paid_amount": paid,
            "pending_amount": pending,
            "notes": "",
            "items": self.active_items,
            "payment_mode": self.pay_mode_combo.currentText()
        }

    def save_invoice_action(self):
        inv_data = self.prepare_invoice_data()
        if not inv_data:
            return False

        try:
            # Commit to SQLite
            final_bill_no, inv_id = self.db.save_invoice(
                inv_data["bill_no"], inv_data["customer_id"], inv_data["mode"],
                inv_data["discount_type"], inv_data["discount_value"], inv_data["gross_total"],
                inv_data["net_total"], inv_data["payment_status"], inv_data["paid_amount"],
                inv_data["pending_amount"], inv_data["notes"], inv_data["items"], inv_data["payment_mode"]
            )
            
            # Generate A4 PDF invoice archive copy
            pdf_name = f"{final_bill_no.replace('-', '_')}.pdf"
            pdf_path = os.path.abspath(os.path.join(PDF_DIR, pdf_name))
            inv_data["bill_no"] = final_bill_no
            inv_data["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            generate_invoice_pdf(inv_data, self.app_settings, pdf_path)
            
            # After saving, keep the current bill visible. Offer to start a new one.
            QMessageBox.information(
                self, f"Invoice Details: {final_bill_no}",
                f"Customer: {inv_data['customer_name']}\n"
                f"Mobile: {inv_data.get('customer_mobile', 'N/A')}\n"
                f"Date: {inv_data['date']}\n"
                f"Mode: {inv_data['mode'].upper()}\n"
                f"Payment Status: {inv_data['payment_status'].upper()}\n\n"
                f"Gross: ₹{inv_data['gross_total']:,.2f}\n"
                f"Net: ₹{inv_data['net_total']:,.2f}\n"
                f"Paid: ₹{inv_data['paid_amount']:,.2f}\n"
                f"Pending: ₹{inv_data['pending_amount']:,.2f}"
            )
            # Prompt user for a new bill
            reply = QMessageBox.question(
                self, "Create New Bill",
                "Do you want to start a new bill?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.new_bill_flow()
            return True
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save invoice: {e}")
            return False

    def save_and_print_action(self):
        inv_data = self.prepare_invoice_data()
        if not inv_data:
            return False

        try:
            # Commit to SQLite
            final_bill_no, inv_id = self.db.save_invoice(
                inv_data["bill_no"], inv_data["customer_id"], inv_data["mode"],
                inv_data["discount_type"], inv_data["discount_value"], inv_data["gross_total"],
                inv_data["net_total"], inv_data["payment_status"], inv_data["paid_amount"],
                inv_data["pending_amount"], inv_data["notes"], inv_data["items"], inv_data["payment_mode"]
            )
            
            # Formulate dates
            inv_data["bill_no"] = final_bill_no
            inv_data["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # PDF generation is deprecated in A5‑only mode; skipping PDF creation.

            # Print receipt
            PrintManager().print_invoice(inv_data, self.app_settings)
            
            # After printing, keep the current invoice displayed. Offer new bill.
            QMessageBox.information(self, "Success", f"Invoice {final_bill_no} printed and saved.")
            reply = QMessageBox.question(
                self, "Create New Bill",
                "Do you want to start a new bill?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.new_bill_flow()
            return True
        except Exception as e:
            QMessageBox.critical(self, "Print Failure", f"Failed to finalize print job: {e}")
            return False

    def whatsapp_share_action(self):
        """Triggered from key shortcut or dialogs."""
        inv_data = self.prepare_invoice_data()
        if not inv_data:
            return
            
        # Ensure archived PDF file exists
        pdf_name = f"{self.current_bill_no.replace('-', '_')}.pdf"
        pdf_path = os.path.abspath(os.path.join(PDF_DIR, pdf_name))
        
        if not os.path.exists(pdf_path):
            # Save invoice first if not already saved
            reply = QMessageBox.question(
                self, "Save Invoice", 
                "Invoice must be saved before sharing. Save now?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                if self.save_invoice_action():
                    # Fetch saved PDF path
                    pdf_path = os.path.abspath(os.path.join(PDF_DIR, pdf_name))
                else:
                    return
            else:
                return

        # Settle share
        share_invoice_via_whatsapp(inv_data, self.app_settings, pdf_path)
    
        """Export the current invoice as PDF without saving to DB."""
        inv_data = self.prepare_invoice_data()
        if not inv_data:
            return False
        pdf_name = f"{inv_data['bill_no'].replace('-', '_')}_export.pdf"
        pdf_path = os.path.abspath(os.path.join(PDF_DIR, pdf_name))
        generate_invoice_pdf(inv_data, self.app_settings, pdf_path)
        QMessageBox.information(self, "PDF Exported", f"Invoice PDF saved to:\n{pdf_path}")
        return True
