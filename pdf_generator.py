from print_manager import A5InvoiceRenderer
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtGui import QTextDocument
from PySide6.QtCore import QSizeF, QMarginsF
from PySide6.QtGui import QPageLayout, QPageSize
import os

def generate_invoice_pdf(invoice, settings, output_path):
    """PDF generation is deprecated in A5‑only mode.

    This function is retained for compatibility but will raise an error if called.
    """
    raise NotImplementedError("PDF generation is not supported in the A5‑only configuration.")

    """Generate A5 PDF invoice using shared HTML renderer.
    Uses Qt's QPrinter in PdfFormat to ensure rendering matches on‑screen print.
    """
    html = A5InvoiceRenderer.render(invoice, settings)
    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(output_path)
    printer.setPageSize(QPageSize(QPageSize.A5))
    printer.setPageOrientation(QPageLayout.Portrait)
    printer.setFullPage(True)
    printer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)
    doc = QTextDocument()
    doc.setDocumentMargin(0)
    doc.setHtml(html)
    printable_rect = printer.pageRect(QPrinter.DevicePixel)
    doc.setPageSize(QSizeF(printable_rect.width(), printable_rect.height()))
    doc.print_(printer)
