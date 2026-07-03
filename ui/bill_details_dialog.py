import os
from datetime import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QLineEdit, QComboBox, 
                             QScrollArea, QFrame, QFormLayout, QWidget)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor

from print_manager import PrintManager
from utils.whatsapp import share_invoice_via_whatsapp
from pdf_generator_a5 import generate_invoice_pdf
from config import PDF_DIR

class BillDetailsDialog(QDialog):
    """
    Premium Invoice View Dialog.
    Displays customer details, invoice details, product lines (with inline editing/deleting),
    balance payment inputs, and payment history logs.
    """
    def __init__(self, db_manager, bill_no, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.bill_no = bill_no
        self.parent_widget = parent
        self.settings = self.db.get_all_settings()
        self.editing_row_index = None
        
        self.qty_edit_widget = None
        self.rate_edit_widget = None

        self.setWindowTitle(f"Invoice Details - {self.bill_no}")
        self.setMinimumSize(950, 750)
        # Set dialog to occupy 90% of screen width and height for a full-screen feel
        screen = self.screen()
        if screen:
            screen_geo = screen.availableGeometry()
            new_width = int(screen_geo.width() * 0.9)
            new_height = int(screen_geo.height() * 0.9)
            self.resize(new_width, new_height)
            self.move(
                (screen_geo.width() - new_width) // 2,
                (screen_geo.height() - new_height) // 2,
            )
        # Apply dark mode stylesheet for a modern look
        dark_style = """
            QDialog {
                background-color: #121212;
                color: #E0E0E0;
            }
            QLabel {
                color: #E0E0E0;
            }
            QLineEdit, QComboBox, QTableWidget {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #333333;
            }
            QPushButton {
                background-color: #3A3A3A;
                color: #E0E0E0;
                border: none;
                padding: 4px 8px;
            }
            QPushButton#primary_btn {
                background-color: #0d6efd;
                color: white;
            }
            QPushButton#success_btn {
                background-color: #198754;
                color: white;
            }
            QPushButton#danger_btn {
                background-color: #dc3545;
                color: white;
            }
        """
        self.setStyleSheet(dark_style)
        
        self.init_ui()
        self.refresh_ui()
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

    def init_ui(self):
        # Base scrollable layout for smaller displays
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        main_layout.addWidget(scroll)
        
        container = QWidget()
        scroll.setWidget(container)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # ----------------------------------------------------
        # 1. Header & Status Bar
        # ----------------------------------------------------
        header_layout = QHBoxLayout()
        self.lbl_title = QLabel(f"INVOICE {self.bill_no}")
        title_font = QFont("Segoe UI", 18, QFont.Bold)
        self.lbl_title.setFont(title_font)
        self.lbl_title.setStyleSheet("color: #0d6efd;")
        header_layout.addWidget(self.lbl_title)
        
        header_layout.addStretch()
        
        self.lbl_status_badge = QLabel("PAID")
        self.lbl_status_badge.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.lbl_status_badge.setAlignment(Qt.AlignCenter)
        self.lbl_status_badge.setFixedSize(100, 26)
        self.lbl_status_badge.setStyleSheet(
            "background-color: #198754; color: white; border-radius: 13px;"
        )
        header_layout.addWidget(self.lbl_status_badge)
        
        layout.addLayout(header_layout)

        # ----------------------------------------------------
        # 2. Main Info Split Panels (Customer & Invoice Details)
        # ----------------------------------------------------
        info_layout = QHBoxLayout()
        info_layout.setSpacing(15)
        
        # Customer Info Panel
        self.cust_card = QFrame()
        cust_layout = QFormLayout(self.cust_card)
        self.lbl_cust_name = QLabel()
        self.lbl_cust_mobile = QLabel()
        self.lbl_cust_address = QLabel()
        cust_layout.addRow("Customer Name:", self.lbl_cust_name)
        cust_layout.addRow("Mobile:", self.lbl_cust_mobile)
        cust_layout.addRow("Address:", self.lbl_cust_address)

        # Invoice Info Panel
        self.inv_card = QFrame()
        inv_layout = QFormLayout(self.inv_card)
        self.lbl_inv_no = QLabel()
        self.lbl_inv_date = QLabel()
        self.lbl_inv_time = QLabel()
        self.lbl_inv_creator = QLabel()
        inv_layout.addRow("Invoice No:", self.lbl_inv_no)
        inv_layout.addRow("Date:", self.lbl_inv_date)
        inv_layout.addRow("Time:", self.lbl_inv_time)
        inv_layout.addRow("Created By:", self.lbl_inv_creator)

        # Add panels to info layout
        # Minimal view: omit customer and invoice panels
        # info_layout.addWidget(self.cust_card, 1)
        # info_layout.addWidget(self.inv_card, 1)
        layout.addLayout(info_layout)

        # ----------------------------------------------------
        # 3. Product Details Table
        # ----------------------------------------------------
        layout.addWidget(QLabel("<b>Product Entries</b>"))
        
        self.prod_table = QTableWidget()
        self.prod_table.setColumnCount(6)
        self.prod_table.setHorizontalHeaderLabels(["Sr No.", "Product Name", "Quantity", "Rate (₹)", "Amount (₹)", "Actions"])
        self.prod_table.setSelectionMode(QTableWidget.NoSelection)
        self.prod_table.setFocusPolicy(Qt.NoFocus)
        self.prod_table.setMinimumHeight(180)
        # Hide the Actions column to remove edit/delete buttons from the UI
        self.prod_table.setColumnHidden(5, True)
        
        h_header = self.prod_table.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.ResizeToContents)
        h_header.setSectionResizeMode(1, QHeaderView.Stretch) # Stretch Product Name
        h_header.setSectionResizeMode(5, QHeaderView.ResizeToContents) # Actions fit buttons
        
        layout.addWidget(self.prod_table)

        # ----------------------------------------------------
        # 4. Totals Summary & Balance Payment Form
        # ----------------------------------------------------
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(15)
        
        # Left side: Balance Payment Section & History
        payment_layout = QVBoxLayout()
        payment_layout.setSpacing(10)
        
        # Add Balance Payment Box
        self.pay_box = QFrame()
        self.pay_box.setObjectName("HeaderCard")
        self.pay_box.setStyleSheet("border-radius: 8px;")
        pay_box_layout = QVBoxLayout(self.pay_box)
        pay_box_layout.setContentsMargins(12, 12, 12, 12)
        
        lbl_pay_header = QLabel("Record Balance Payment")
        lbl_pay_header.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl_pay_header.setStyleSheet("color: #198754;")
        pay_box_layout.addWidget(lbl_pay_header)
        
        pay_inputs = QHBoxLayout()
        self.lbl_pay_remaining = QLabel("Remaining: ₹0.00")
        self.lbl_pay_remaining.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.lbl_pay_remaining.setStyleSheet("color: #dc3545;")
        pay_inputs.addWidget(self.lbl_pay_remaining)
        
        pay_inputs.addSpacing(15)
        
        pay_inputs.addWidget(QLabel("<b>Amount to Pay (₹):</b>"))
        self.payment_amount_input = QLineEdit()
        self.payment_amount_input.setFixedWidth(100)
        self.payment_amount_input.setPlaceholderText("0.00")
        pay_inputs.addWidget(self.payment_amount_input)
        
        pay_inputs.addSpacing(10)
        
        pay_inputs.addWidget(QLabel("<b>Mode:</b>"))
        self.payment_mode_combo = QComboBox()
        self.payment_mode_combo.addItems(["Cash", "UPI", "Card", "Other"])
        pay_inputs.addWidget(self.payment_mode_combo)
        
        self.btn_add_payment = QPushButton("Add Payment")
        self.btn_add_payment.setObjectName("success_btn")
        self.btn_add_payment.clicked.connect(self.add_balance_payment)
        pay_inputs.addWidget(self.btn_add_payment)
        
        pay_box_layout.addLayout(pay_inputs)
        payment_layout.addWidget(self.pay_box)
        
        # Payment History Table
        payment_layout.addWidget(QLabel("<b>Payment Logs</b>"))
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["Date", "Time", "Amount (₹)", "Mode", "Remaining (₹)"])
        self.history_table.setSelectionMode(QTableWidget.NoSelection)
        self.history_table.setFocusPolicy(Qt.NoFocus)
        self.history_table.setMinimumHeight(140)
        
        h_hist = self.history_table.horizontalHeader()
        h_hist.setSectionResizeMode(QHeaderView.Stretch)
        payment_layout.addWidget(self.history_table)
        
        bottom_layout.addLayout(payment_layout, 3)
        
        # Right side: Totals summary
        self.totals_card = QFrame()
        self.totals_card.setObjectName("HeaderCard")
        self.totals_card.setStyleSheet("border-radius: 8px;")
        self.totals_card.setFixedWidth(300)
        totals_form = QFormLayout(self.totals_card)
        totals_form.setContentsMargins(15, 15, 15, 15)
        totals_form.setSpacing(10)
        
        lbl_totals_header = QLabel("Payment Summary")
        lbl_totals_header.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl_totals_header.setStyleSheet("color: #3b82f6;")
        totals_form.addRow(lbl_totals_header)
        
        self.lbl_subtotal = QLabel("₹0.00")
        self.lbl_discount = QLabel("₹0.00")
        self.lbl_grand_total = QLabel("₹0.00")
        self.lbl_paid_amount = QLabel("₹0.00")
        self.lbl_remaining_amount = QLabel("₹0.00")
        
        self.lbl_grand_total.setStyleSheet("font-size: 16px; font-weight: bold; color: #198754;")
        self.lbl_remaining_amount.setStyleSheet("font-size: 16px; font-weight: bold; color: #dc3545;")
        
        totals_form.addRow(QLabel("<b>Subtotal (Gross):</b>"), self.lbl_subtotal)
        totals_form.addRow(QLabel("<b>Discount:</b>"), self.lbl_discount)
        totals_form.addRow(QLabel("<b>Grand Total:</b>"), self.lbl_grand_total)
        totals_form.addRow(QLabel("<b>Paid Amount:</b>"), self.lbl_paid_amount)
        totals_form.addRow(QLabel("<b>Remaining Due:</b>"), self.lbl_remaining_amount)
        
        bottom_layout.addWidget(self.totals_card, 1)
        
        layout.addLayout(bottom_layout)

        # ----------------------------------------------------
        # 5. Footer Actions (Print, Share, Close)
        # ----------------------------------------------------
        footer_layout = QHBoxLayout()
        
        self.btn_print = QPushButton("Print Bill")
        self.btn_print.setObjectName("primary_btn")
        self.btn_print.clicked.connect(self.print_bill_action)
        footer_layout.addWidget(self.btn_print)
        
        self.btn_share = QPushButton("Share on WhatsApp")
        self.btn_share.setStyleSheet("background-color: #25d366; color: white; border: 1px solid #25d366;")
        self.btn_share.clicked.connect(self.share_whatsapp_action)
        footer_layout.addWidget(self.btn_share)
        
        footer_layout.addStretch()
        
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        footer_layout.addWidget(btn_close)
        
        layout.addLayout(footer_layout)

    def refresh_ui(self):
        # Fetch current invoice record
        self.invoice = self.db.get_invoice_by_bill_no(self.bill_no)
        if not self.invoice:
            QMessageBox.critical(self, "Error", f"Could not load invoice {self.bill_no}")
            self.reject()
            return

        # 1. Update Customer Information
        self.lbl_cust_name.setText(self.invoice.get("customer_name") or "Walk-in Customer")
        self.lbl_cust_mobile.setText(self.invoice.get("customer_mobile") or "0000000000")
        self.lbl_cust_address.setText(self.invoice.get("customer_address") or "Counter")

        # 2. Update Invoice Information
        self.lbl_inv_no.setText(self.invoice.get("bill_no"))
        
        dt_str = self.invoice.get("date", "")
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            self.lbl_inv_date.setText(dt.strftime("%d %b %Y"))
            self.lbl_inv_time.setText(dt.strftime("%I:%M %p"))
        except:
            self.lbl_inv_date.setText(dt_str)
            self.lbl_inv_time.setText("")
            
        biz_name = self.settings.get("business_name", "Bhumi Jewellers")
        self.lbl_inv_creator.setText(biz_name)

        # Status badge update
        status = self.invoice.get("payment_status", "paid").upper()
        self.lbl_status_badge.setText(status)
        if status == "PAID":
            self.lbl_status_badge.setStyleSheet("background-color: #198754; color: white; border-radius: 13px;")
        elif status == "PARTIAL":
            self.lbl_status_badge.setStyleSheet("background-color: #ffc107; color: black; border-radius: 13px;")
        else:
            self.lbl_status_badge.setStyleSheet("background-color: #dc3545; color: white; border-radius: 13px;")

        # 3. Load Products Table
        self.load_products_table()

        # 4. Update Summary Card
        gross = self.invoice.get("gross_total", 0.0)
        net = self.invoice.get("net_total", 0.0)
        paid = self.invoice.get("paid_amount", 0.0)
        pending = self.invoice.get("pending_amount", 0.0)
        discount = gross - net

        self.lbl_subtotal.setText(f"₹{gross:,.2f}")
        self.lbl_discount.setText(f"₹{discount:,.2f}")
        self.lbl_grand_total.setText(f"₹{net:,.2f}")
        self.lbl_paid_amount.setText(f"₹{paid:,.2f}")
        # 5. Record Balance Payment Box setup
        self.lbl_pay_remaining.setText(f"Remaining: ₹{pending:,.2f}")
        self.payment_amount_input.setText(f"{pending:.2f}")
        # Ensure fields are editable when there is a pending amount
        self.payment_amount_input.setReadOnly(False)
        self.payment_mode_combo.setEnabled(True)
        self.btn_add_payment.setEnabled(True)

        if pending <= 0:
            self.btn_add_payment.setEnabled(False)
            self.payment_amount_input.setEnabled(False)
            self.payment_mode_combo.setEnabled(False)
        else:
            self.btn_add_payment.setEnabled(True)
            self.payment_amount_input.setEnabled(True)
            self.payment_mode_combo.setEnabled(True)

        # 6. Load Payment History Table
        self.load_payment_history_table(net)

    def load_products_table(self):
        items = self.invoice.get("items", [])
        self.prod_table.setRowCount(len(items))
        
        for i, item in enumerate(items):
            # Sr No.
            self.prod_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.prod_table.item(i, 0).setTextAlignment(Qt.AlignCenter)
            
            # Product Name
            self.prod_table.setItem(i, 1, QTableWidgetItem(item["product_name"]))
            
            if self.editing_row_index == i:
                # Quantities line edit
                qty_edit = QLineEdit()
                qty_val = item["qty"]
                qty_edit.setText(f"{qty_val:.3f}" if not qty_val.is_integer() else f"{int(qty_val)}")
                qty_edit.setAlignment(Qt.AlignRight)
                qty_edit.setStyleSheet("padding: 2px; height: 24px;")
                self.prod_table.setCellWidget(i, 2, qty_edit)
                self.qty_edit_widget = qty_edit
                
                # Rate line edit
                rate_edit = QLineEdit()
                rate_edit.setText(f"{item['rate']:.2f}")
                rate_edit.setAlignment(Qt.AlignRight)
                rate_edit.setStyleSheet("padding: 2px; height: 24px;")
                self.prod_table.setCellWidget(i, 3, rate_edit)
                self.rate_edit_widget = rate_edit
                
                # Amount static during edit
                total = item["qty"] * item["rate"]
                self.prod_table.setItem(i, 4, QTableWidgetItem(f"₹{total:,.2f}"))
                self.prod_table.item(i, 4).setTextAlignment(Qt.AlignRight)
                
                # Actions Widget: Save & Cancel
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 2, 4, 2)
                actions_layout.setSpacing(4)
                
                save_btn = QPushButton("Save")
                save_btn.setObjectName("success_btn")
                save_btn.setStyleSheet("padding: 2px 8px; font-size: 11px; height: 20px;")
                save_btn.clicked.connect(lambda checked=False, it=item: self.save_row_edit(it))
                
                cancel_btn = QPushButton("Cancel")
                cancel_btn.setStyleSheet("padding: 2px 8px; font-size: 11px; height: 20px;")
                cancel_btn.clicked.connect(self.cancel_row_edit)
                
                actions_layout.addWidget(save_btn)
                actions_layout.addWidget(cancel_btn)
                self.prod_table.setCellWidget(i, 5, actions_widget)
            else:
                # Quantities display
                qty_val = item["qty"]
                qty_str = f"{qty_val:.3f}" if not qty_val.is_integer() else f"{int(qty_val)}"
                self.prod_table.setItem(i, 2, QTableWidgetItem(qty_str))
                self.prod_table.item(i, 2).setTextAlignment(Qt.AlignRight)
                
                # Rate display
                self.prod_table.setItem(i, 3, QTableWidgetItem(f"₹{item['rate']:,.2f}"))
                self.prod_table.item(i, 3).setTextAlignment(Qt.AlignRight)
                
                # Amount display
                total = item["qty"] * item["rate"]
                self.prod_table.setItem(i, 4, QTableWidgetItem(f"₹{total:,.2f}"))
                self.prod_table.item(i, 4).setTextAlignment(Qt.AlignRight)
                
                # Actions Widget: Edit & Delete
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 2, 4, 2)
                actions_layout.setSpacing(4)
                
                edit_btn = QPushButton("Edit")
                edit_btn.setStyleSheet("padding: 2px 8px; font-size: 11px; height: 20px;")
                edit_btn.clicked.connect(lambda checked=False, idx=i: self.start_row_edit(idx))
                
                delete_btn = QPushButton("Delete")
                delete_btn.setObjectName("danger_btn")
                delete_btn.setStyleSheet("padding: 2px 8px; font-size: 11px; height: 20px;")
                delete_btn.clicked.connect(lambda checked=False, it=item: self.delete_row_item(it))
                
                actions_layout.addWidget(edit_btn)
                actions_layout.addWidget(delete_btn)
                self.prod_table.setCellWidget(i, 5, actions_widget)

    def start_row_edit(self, row_idx):
        self.editing_row_index = row_idx
        self.load_products_table()

    def cancel_row_edit(self):
        self.editing_row_index = None
        self.qty_edit_widget = None
        self.rate_edit_widget = None
        self.load_products_table()

    def save_row_edit(self, item):
        qty_str = self.qty_edit_widget.text().strip()
        rate_str = self.rate_edit_widget.text().strip()
        
        if not qty_str or not rate_str:
            QMessageBox.warning(self, "Validation Error", "Quantity and Rate are required.")
            return

        try:
            qty = float(qty_str)
            rate = float(rate_str)
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Quantity and Rate must be valid numbers.")
            return

        if qty <= 0 or rate <= 0:
            QMessageBox.warning(self, "Validation Error", "Quantity and Rate must be greater than zero.")
            return

        try:
            self.db.update_invoice_item_qty_rate(item["id"], qty, rate)
            self.db.recalculate_invoice_totals(self.invoice["id"])
            
            # Sync parent window/view
            if self.parent_widget and hasattr(self.parent_widget, "refresh_all"):
                self.parent_widget.refresh_all()
                
            self.cancel_row_edit()
            self.refresh_ui()
            QMessageBox.information(self, "Success", "Product entry updated successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save item edits: {e}")

    def delete_row_item(self, item):
        if len(self.invoice.get("items", [])) <= 1:
            QMessageBox.warning(self, "Operation Prohibited", "An invoice must contain at least one item. If you want to clear/cancel this bill, please contact your store manager.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to remove '{item['product_name']}' from this bill?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.db.delete_invoice_item(item["id"])
                self.db.recalculate_invoice_totals(self.invoice["id"])
                
                # Sync parent window/view
                if self.parent_widget and hasattr(self.parent_widget, "refresh_all"):
                    self.parent_widget.refresh_all()
                    
                self.refresh_ui()
                QMessageBox.information(self, "Success", "Product deleted and invoice totals recalculated.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete item: {e}")

    def add_balance_payment(self):
        amt_str = self.payment_amount_input.text().strip()
        payment_mode = self.payment_mode_combo.currentText()
        
        if not amt_str:
            QMessageBox.warning(self, "Validation Error", "Please enter a payment amount.")
            return

        try:
            amount = float(amt_str)
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Payment amount must be a valid number.")
            return

        if amount <= 0:
            QMessageBox.warning(self, "Validation Error", "Payment amount must be greater than zero.")
            return

        pending = self.invoice.get("pending_amount", 0.0)
        if amount > pending:
            QMessageBox.warning(self, "Validation Error", "Payment amount cannot exceed the remaining balance.")
            return

        try:
            self.db.add_invoice_payment(self.invoice["id"], amount, payment_mode)

            # Sync parent window/view
            if self.parent_widget and hasattr(self.parent_widget, "refresh_all"):
                self.parent_widget.refresh_all()

            # Refresh UI to reflect new pending amount
            self.refresh_ui()
            # Clear the payment amount field after successful entry
            self.payment_amount_input.clear()
            QMessageBox.information(self, "Success", f"Recorded payment of ₹{amount:,.2f} via {payment_mode}.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to record payment: {e}")

    def load_payment_history_table(self, net_total):
        payments = self.db.get_invoice_payments(self.invoice["id"])
        self.history_table.setRowCount(len(payments))
        
        remaining_balance = net_total
        for i, pmt in enumerate(payments):
            # Parse Date & Time
            dt_str = pmt.get("payment_date", "")
            try:
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                date_str = dt.strftime("%d/%m")
                time_str = dt.strftime("%I:%M %p")
            except:
                date_str = dt_str
                time_str = ""
                
            remaining_balance -= pmt["amount"]
            
            self.history_table.setItem(i, 0, QTableWidgetItem(date_str))
            self.history_table.setItem(i, 1, QTableWidgetItem(time_str))
            self.history_table.setItem(i, 2, QTableWidgetItem(f"{pmt['amount']:,.2f}"))
            self.history_table.setItem(i, 3, QTableWidgetItem(pmt.get("payment_mode", "Cash")))
            self.history_table.setItem(i, 4, QTableWidgetItem(f"{remaining_balance:,.2f}"))
            
            # Text alignment
            for col in [0, 1, 3]:
                self.history_table.item(i, col).setTextAlignment(Qt.AlignCenter)
            for col in [2, 4]:
                self.history_table.item(i, col).setTextAlignment(Qt.AlignRight)

    def print_bill_action(self):
        try:
            PrintManager().print_invoice(self.invoice, self.settings)
            QMessageBox.information(self, "Success", "Invoice printed successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Failed to print invoice: {e}")

    def share_whatsapp_action(self):
        try:
            pdf_name = f"{self.invoice['bill_no'].replace('-', '_')}.pdf"
            pdf_path = os.path.abspath(os.path.join(PDF_DIR, pdf_name))
            
            # Generate temporary PDF inside PDF_DIR
            generate_invoice_pdf(self.invoice, self.settings, pdf_path)
            
            share_invoice_via_whatsapp(self.invoice, self.settings, pdf_path)
            QMessageBox.information(self, "Success", "WhatsApp share sequence initiated.")
        except Exception as e:
            QMessageBox.critical(self, "WhatsApp Share Error", f"Failed to generate share link: {e}")
