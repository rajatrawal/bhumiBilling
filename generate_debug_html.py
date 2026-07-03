import os
from print_manager import A5InvoiceRenderer

# Dummy invoice data
invoice = {
    "bill_no": "TEST-001",
    "date": "2026-01-01 12:00:00",
    "mode": "retail",
    "customer_name": "John Doe",
    "customer_mobile": "1234567890",
    "items": [
        {"product_name": "Gold Ring", "qty": 1, "rate": 1500, "product_name": "Gold Ring"},
        {"product_name": "Silver Necklace", "qty": 2, "rate": 800, "product_name": "Silver Necklace"}
    ],
    "gross_total": 3100,
    "net_total": 3100,
    "paid_amount": 3100,
    "pending_amount": 0,
    "discount_type": "none",
    "discount_value": 0
}

settings = {
    "business_name": "Bhumi Jewellers",
    "business_address": "123 Street",
    "business_mobile": "9876543210",
    "gst_number": "",
    "footer_message": "Thank you for your purchase!"
}

html = A5InvoiceRenderer.render(invoice, settings)

output_path = os.path.abspath(os.path.join(os.getcwd(), "debug_test_invoice.html"))
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Debug HTML written to {output_path}, length={len(html)}")
