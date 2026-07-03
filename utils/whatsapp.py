import urllib.parse
import webbrowser
from PySide6.QtGui import QGuiApplication

def clean_mobile_number(number_str):
    """Normalize phone numbers for WhatsApp integration (must include country code without symbols)."""
    if not number_str:
        return ""
    # Strip symbols
    cleaned = "".join(c for c in number_str if c.isdigit())
    # Add Indian country code default if not present and starts with 10 digits
    if len(cleaned) == 10:
        cleaned = "91" + cleaned
    return cleaned

def share_invoice_via_whatsapp(invoice, settings, pdf_path):
    """
    Formulate invoice text receipt, copy file path to system clipboard,
    and open wa.me URL launcher.
    """
    biz_name = settings.get("business_name", "Bhumi Jewellers")
    bill_no = invoice.get("bill_no", "")
    net_total = float(invoice.get("net_total", 0.0))
    payment_status = invoice.get("payment_status", "paid").upper()
    
    # Clean recipient number
    cust_mobile = clean_mobile_number(invoice.get("customer_mobile", ""))
    
    # Formulate friendly WhatsApp receipt text
    msg = (
        f"*Invoice from {biz_name}*\n"
        f"---------------------------\n"
        f"*Bill No:* {bill_no}\n"
        f"*Date:* {invoice.get('date', '')}\n"
        f"*Net Total:* ₹{net_total:,.2f}\n"
        f"*Status:* {payment_status}\n"
        f"---------------------------\n"
        f"Your invoice PDF has been saved at:\n"
        f"`{pdf_path}`\n\n"
        f"Please reply if you have any questions. Thank you!"
    )
    
    # Copy PDF path and text description to clipboard for fast paste/drag-drop
    clipboard = QGuiApplication.clipboard()
    # Copy file path as text
    clipboard.setText(pdf_path)
    
    # URL encode message
    encoded_msg = urllib.parse.quote(msg)
    
    # Launch browser scheme
    if cust_mobile:
        wa_url = f"https://wa.me/{cust_mobile}?text={encoded_msg}"
    else:
        wa_url = f"https://web.whatsapp.com/send?text={encoded_msg}"
        
    webbrowser.open(wa_url)
    return True
