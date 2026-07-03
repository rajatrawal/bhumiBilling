#!/usr/bin/env python
import os, sys
# Ensure project root is in PYTHONPATH
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.append(project_root)

from print_manager import PrintManager

# Sample invoice data
invoice = {
    "bill_no": "TEST001",
    "date": "2026-06-22",
    "mode": "retail",
    "customer_name": "John Doe",
    "customer_mobile": "1234567890",
    "items": [
        {"product_name": "Item A", "qty": 1, "rate": 100},
        {"product_name": "Item B", "qty": 2, "rate": 150}
    ],
    "gross_total": 400,
    "net_total": 380,
    "paid_amount": 380,
    "pending_amount": 0,
    "business_name": "Bhumi",
    "business_address": "",
    "footer_message": "Thank you!"
}

# Sample settings
settings = {
    "printer_type_name": "NonExistentPrinter",  # force fallback to PDF
    "printer_type": "80mm",
    "PDF_DIR": os.path.join(project_root, "pdf_output")
}

try:
    result = PrintManager().print_invoice(invoice, settings)
    print("Print function returned:", result)
except Exception as e:
    print("Error during printing:", e)
