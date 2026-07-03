import os
import logging
import tempfile
from datetime import datetime
from typing import Optional

# Local PDF generator using ReportLab (implemented in pdf_generator_a5.py)
from pdf_generator_a5 import generate_invoice_pdf

logger = logging.getLogger("BhumiBilling.PrintManager")

class PDFPrintManager:
    """Utility to send a PDF file to the default printer on Windows.

    It uses the OS integration `os.startfile` with the "print" operation, which
    opens the associated PDF viewer and triggers the print dialog silently.
    """

    @staticmethod
    def print_pdf(pdf_path: str, printer_name: Optional[str] = None) -> bool:
        """Print the given PDF file.

        Args:
            pdf_path: Absolute path to the PDF file.
            printer_name: Currently unused – Windows `startfile` prints to the
                default system printer. Future enhancements could select a
                specific printer via QPrinter.
        Returns:
            True if the command was successfully launched.
        """
        # Use the robust Windows printer helper – prints without opening a viewer
        from pdf_printer_win import print_pdf_direct
        print_pdf_direct(pdf_path, printer_name)
        return True        

class PrintManager:
    """Facade for printing an A5 invoice using the PDF‑first workflow."""

    @staticmethod
    def get_default_printer_name() -> str:
        """Placeholder for future printer‑selection logic.
        Currently the OS default printer is used via `os.startfile`.
        """
        # No explicit API to query default printer without Qt; return empty.
        return ""

    @staticmethod
    def get_installed_printers() -> list:
        """Placeholder – returns empty list as printer enumeration is not used.
        """
        return []

    def print_invoice(self, invoice: dict, settings: dict, printer_name: str = None) -> bool:
        """Generate a temporary A5 PDF invoice and send it to the printer.

        Steps:
        1. Render PDF via `generate_invoice_pdf`.
        2. Call `PDFPrintManager.print_pdf` to print.
        3. Delete the temporary PDF file.
        """
        try:
            # Determine temporary directory within the project.
            temp_dir = os.path.join(os.getcwd(), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_path = os.path.join(temp_dir, f"invoice_{timestamp}.pdf")

            # Generate PDF.
            generate_invoice_pdf(invoice, settings, pdf_path)

            # Print PDF.
            PDFPrintManager.print_pdf(pdf_path, printer_name)

            # Cleanup – remove the temporary PDF after a short delay.
            # NOTE: Deleting the file immediately can cause 'file not found' errors because the
            # OS launches the PDF viewer asynchronously. The removal is therefore disabled.
            # try:
            #     os.remove(pdf_path)
            #     logger.debug(f"Temporary PDF removed: {pdf_path}")
            # except Exception as cleanup_err:
            #     logger.warning(f"Could not delete temporary PDF {pdf_path}: {cleanup_err}")

            return True
        except Exception as e:
            logger.error(f"Printing failed: {e}")
            raise RuntimeError(f"Printer error: {e}")
