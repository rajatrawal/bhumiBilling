import os
import time
import logging
import subprocess
import win32print

logger = logging.getLogger("BhumiBilling.PDFPrinter")


def get_default_printer():
    """Return the default Windows printer."""
    return win32print.GetDefaultPrinter()


def print_pdf_direct(pdf_path, printer_name=None, wait_seconds=10):
    """
    Print a PDF file silently using SumatraPDF.

    Args:
        pdf_path (str): Absolute path to PDF file.
        printer_name (str): Printer name. If None, default printer is used.
        wait_seconds (int): Optional wait after print command.

    Raises:
        FileNotFoundError: If PDF or SumatraPDF does not exist.
        Exception: If printing fails.
    """

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if printer_name is None:
        printer_name = get_default_printer()

    # Path to SumatraPDF.exe
    # Place SumatraPDF.exe in the same folder as this file
    sumatra_path = r"C:\Users\Rajat\AppData\Local\SumatraPDF\SumatraPDF.exe"
    if not os.path.exists(sumatra_path):
        raise FileNotFoundError(
            f"SumatraPDF.exe not found: {sumatra_path}"
        )

    logger.info(
        f"Printing '{pdf_path}' to '{printer_name}' using SumatraPDF"
    )

    try:
        cmd = [
            sumatra_path,
            "-print-to",
            printer_name,
            "-silent",
            pdf_path
        ]

        logger.info(f"Executing: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logger.error(
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )
            raise Exception(
                f"SumatraPDF exited with code "
                f"{result.returncode}"
            )

        logger.info("Print command sent successfully.")

        if wait_seconds:
            time.sleep(wait_seconds)

    except Exception as e:
        logger.exception("PDF printing failed")
        raise Exception(f"Failed to print PDF: {e}")


if __name__ == "__main__":
    pdf_file = r"C:\Bills\invoice.pdf"

    print_pdf_direct(pdf_file)

    # OR
    # print_pdf_direct(
    #     pdf_file,
    #     "Samsung SCX-3400 Series"
    # )