from datetime import datetime
from print_manager import PrintManager
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QFormLayout, QDateEdit, 
                             QGroupBox, QInputDialog, QComboBox)
from PySide6.QtCore import Qt, QDate

class TallyWidget(QWidget):
    """
    Daily tally widget displaying daily summaries, recording cash book items (Sales, Expenses, Opening),
    and searching outstanding invoices.
    """
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.init_ui()
        self.refresh_all()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Top Bar: Date selection & Refresh
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("<b>Select Date:</b>"))
        
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.dateChanged.connect(self.refresh_all)
        top_bar.addWidget(self.date_picker)
        
        refresh_btn = QPushButton("Refresh Data")
        refresh_btn.clicked.connect(self.refresh_all)
        top_bar.addWidget(refresh_btn)
        top_bar.addStretch()
        
        layout.addLayout(top_bar)

        # Stats Cards Layout
        self.stats_group = QGroupBox("Daily Summary Overview")
        stats_layout = QHBoxLayout(self.stats_group)
        
        self.lbl_bills = QLabel("Bills: 0")
        self.lbl_sales = QLabel("Net Sales: ₹0.00")
        self.lbl_discount = QLabel("Discounts: ₹0.00")
        self.lbl_paid = QLabel("Paid Recd: ₹0.00")
        self.lbl_pending = QLabel("Pending: ₹0.00")
        
        for lbl in [self.lbl_bills, self.lbl_sales, self.lbl_discount, self.lbl_paid, self.lbl_pending]:
            lbl.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
            stats_layout.addWidget(lbl)
            
        layout.addWidget(self.stats_group)

        # 1. Bills List
        bills_box = QGroupBox("Daily Invoices")
        bills_layout = QVBoxLayout(bills_box)
        
        self.bills_table = QTableWidget()
        self.bills_table.setColumnCount(6)
        self.bills_table.setHorizontalHeaderLabels(["Bill No", "Customer", "Total", "Paid", "Pending", "Status"])
        self.bills_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.bills_table.setSelectionMode(QTableWidget.SingleSelection)
        self.bills_table.doubleClicked.connect(self.on_bill_double_clicked)
        
        h_bills = self.bills_table.horizontalHeader()
        h_bills.setSectionResizeMode(QHeaderView.ResizeToContents)
        h_bills.setSectionResizeMode(1, QHeaderView.Stretch)
        
        bills_layout.addWidget(self.bills_table)
        
        # Settle Bill Button
        settle_btn = QPushButton("Settle Pending Balance (F7)")
        settle_btn.setObjectName("success_btn")
        settle_btn.clicked.connect(self.settle_invoice_payment)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(settle_btn)
        # Print Bill Button
        print_btn = QPushButton("Print Bill (Ctrl+P)")
        print_btn.setObjectName("primary_btn")
        print_btn.clicked.connect(self.print_selected_invoice)
        btn_layout.addWidget(print_btn)
        bills_layout.addLayout(btn_layout)
        
        layout.addWidget(bills_box)

    def get_selected_date_str(self):
        return self.date_picker.date().toString("yyyy-MM-dd")

    def refresh_all(self):
        date_str = self.get_selected_date_str()
        
        # 1. Load Stats
        tally = self.db.get_daily_tally(date_str)
        self.lbl_bills.setText(f"Bills: {tally['bills_count']}")
        self.lbl_sales.setText(f"Net Sales: ₹{tally['net_sales']:,.2f}")
        self.lbl_discount.setText(f"Discounts: ₹{tally['discount_given']:,.2f}")
        self.lbl_paid.setText(f"Paid Recd: ₹{tally['paid_amount']:,.2f}")
        self.lbl_pending.setText(f"Pending: ₹{tally['pending_amount']:,.2f}")
        
        # 2. Load Invoices Table
        invoices = self.db.get_all_invoices(start_date=date_str, end_date=date_str)
        self.bills_table.setRowCount(len(invoices))
        for i, inv in enumerate(invoices):
            self.bills_table.setItem(i, 0, QTableWidgetItem(inv["bill_no"]))
            self.bills_table.setItem(i, 1, QTableWidgetItem(inv["customer_name"] or "Walk-in"))
            self.bills_table.setItem(i, 2, QTableWidgetItem(f"{inv['net_total']:,.2f}"))
            self.bills_table.setItem(i, 3, QTableWidgetItem(f"{inv['paid_amount']:,.2f}"))
            self.bills_table.setItem(i, 4, QTableWidgetItem(f"{inv['pending_amount']:,.2f}"))
            
            # Status styling
            status = inv["payment_status"].upper()
            status_item = QTableWidgetItem(status)
            if status == "PAID":
                status_item.setForeground(Qt.green)
            elif status == "PARTIAL":
                status_item.setForeground(Qt.yellow)
            else:
                status_item.setForeground(Qt.red)
                
            self.bills_table.setItem(i, 5, status_item)

    def settle_invoice_payment(self):
        """Allows recording partial/full payments on outstanding bills directly from the list."""
        selected_ranges = self.bills_table.selectedRanges()
        if not selected_ranges:
            QMessageBox.information(self, "Notice", "Select an invoice row from the Daily Invoices list.")
            return
            
        row = selected_ranges[0].topRow()
        bill_no = self.bills_table.item(row, 0).text()
        
        invoice = self.db.get_invoice_by_bill_no(bill_no)
        if not invoice:
            return
            
        if invoice["payment_status"] == "paid":
            QMessageBox.information(self, "Notice", f"Invoice {bill_no} is already fully paid.")
            return

        # Settle input dialog
        pending_amt = invoice["pending_amount"]
        text, ok = QInputDialog.getText(
            self, "Record Payment Settlement",
            f"Bill {bill_no} outstanding: ₹{pending_amt:,.2f}\n"
            f"Enter amount received (₹):",
            QLineEdit.Normal, f"{pending_amt:.2f}"
        )
        
        if ok and text:
            try:
                recv_amt = float(text.strip())
                if recv_amt <= 0:
                    QMessageBox.warning(self, "Error", "Payment amount must be greater than zero.")
                    return
                if recv_amt > pending_amt:
                    QMessageBox.warning(self, "Error", f"Received amount (₹{recv_amt}) cannot exceed pending balance (₹{pending_amt}).")
                    return
                    
                new_paid = invoice["paid_amount"] + recv_amt
                new_pending = pending_amt - recv_amt
                new_status = "paid" if new_pending == 0 else "partial"
                
                self.db.update_invoice_payment(invoice["id"], new_paid, new_pending, new_status)
                self.refresh_all()
                QMessageBox.information(self, "Success", "Payment updated successfully.")
            except ValueError:
                QMessageBox.warning(self, "Error", "Invalid numeric payment entry.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Database error: {e}")


    def print_selected_invoice(self):
        """Print the currently selected invoice from the bills table."""
        selected_ranges = self.bills_table.selectedRanges()
        if not selected_ranges:
            QMessageBox.information(self, "Notice", "Select an invoice row to print.")
            return
        row = selected_ranges[0].topRow()
        bill_no_item = self.bills_table.item(row, 0)
        if not bill_no_item:
            QMessageBox.warning(self, "Error", "Unable to retrieve Bill No.")
            return
        bill_no = bill_no_item.text()
        invoice = self.db.get_invoice_by_bill_no(bill_no)
        if not invoice:
            QMessageBox.warning(self, "Error", f"Invoice {bill_no} not found.")
            return
        settings = self.db.get_all_settings()
        try:
            PrintManager().print_invoice(invoice, settings)
            QMessageBox.information(self, "Success", f"Invoice {bill_no} printed successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Failed to print invoice {bill_no}: {e}")
        
    def on_bill_double_clicked(self, index):
        """Open the premium invoice details modal dialog."""
        row = index.row()
        bill_no = self.bills_table.item(row, 0).text()
        from ui.bill_details_dialog import BillDetailsDialog
        dialog = BillDetailsDialog(self.db, bill_no, self)
        dialog.exec()
