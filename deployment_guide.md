# Deployment Guide & Operations Manual - Bhumi Billing

Bhumi Billing is a high-speed, keyboard-first desktop billing application built for jewellery retail/wholesale businesses. This guide contains instructions on installation, database setup, thermal printer configurations, and packaging.

---

## 1. Directory Structure

```
g:\bhumi billing\
├── main.py                # Main Application entrypoint
├── config.py              # Configurations, paths and constants
├── db_manager.py          # SQLite database connection & CRUD operations
├── pdf_generator.py       # ReportLab PDF invoice generator (A4 layout)
├── print_manager.py       # Direct thermal printer spooling manager
├── build.bat              # Standalone PyInstaller compile automation script
├── deployment_guide.md    # This Operations manual
│
├── utils/
│   ├── whatsapp.py        # WhatsApp URL launcher & clipboard helper
│   └── backup.py          # Automatic daily database snapshot backup task
│
└── ui/
    ├── __init__.py        # Package constructor
    ├── styles.py          # QSS stylesheets (Light & Dark theme styling)
    ├── main_window.py     # Main tab navigator and keyboard router
    ├── billing_widget.py  # Ultra-fast billing workspace widget
    ├── product_widget.py  # Product directory editor
    ├── customer_widget.py # Customer directory editor & inline dialog
    └── settings_widget.py # Print & Business settings panel
```

Once launched, the application automatically creates a data folder (`data/`) containing:
- `bhumi_billing.db`: Active SQLite database file.
- `bhumi_billing.log`: Application logging records.
- `invoices/`: Archive copies of generated PDF invoices.
- `backups/`: Automated daily and static copies of database (`backup.db`).

---

## 2. Dependencies & System Setup

### Prerequisites
- **Python**: Version 3.8 to 3.11 (for maximum compatibility with PySide6 and ReportLab on older Windows 7 / 10 architectures).
- **Windows System Drivers**: Ensure correct printer spool drivers (e.g. POS-58 or POS-80) are installed and print tests pass from Windows Control Panel.

### Step-by-Step Installation
1. Clone or copy project directory structure.
2. Open terminal in the directory and set up virtual environment:
   ```cmd
   python -m venv venv
   ```
3. Activate virtual environment:
   ```cmd
   venv\Scripts\activate
   ```
4. Install package dependencies:
   ```cmd
   pip install PySide6 reportlab pyinstaller
   ```
5. Launch the application:
   ```cmd
   python main.py
   ```

---

## 3. Keyboard Shortcut Reference Map

| Shortcut Key | Mode / Context | Action Description |
| :--- | :--- | :--- |
| **`F1`** | Universal | Opens shortcut help dialog |
| **`F2`** | Universal | Switch focus directly to Billing Workspace Product Search field |
| **`F3`** | Billing | Toggle billing mode (Retail Rate <-> Wholesale Rate) |
| **`F4`** | Billing | Populate product search with the last billed item details |
| **`F6`** | Billing | Shift keyboard focus directly to discount input box |
| **`F7`** | Daily Tally | Settle outstanding balance for the selected customer invoice |
| **`F8`** | Universal | Switch focus directly to Daily Tally & Cash book tab |
| **`F9` / `Ctrl+P`** | Billing | Save transaction to database, spools thermal receipt, resets layout |
| **`F10`** | Universal | Go to Products Catalog Editor tab |
| **`F11`** | Universal | Go to Customers Directory tab |
| **`F12`** | Universal | Go to Settings & Profile configuration tab |
| **`Ctrl+S`** | Billing | Save invoice details to DB without pushing to print queue |
| **`Ctrl+N`** | Billing | Inline popup to create a new customer without losing focus |
| **`Ctrl+M`** | Billing | Move keyboard focus straight to Customer search bar |
| **`Ctrl+D`** | Billing | Cycle Payment Status through states: `PAID` -> `PENDING` -> `PARTIAL` |
| **`Ctrl+W`** | Billing | Format WhatsApp text receipt, copy PDF path, launch sharing URL |
| **`DEL`** | Billing Table | Delete currently highlighted row item from active invoice list |

---

## 4. Printer Configuration

1. In Windows, go to **Settings > Devices > Printers & Scanners** and verify your POS Printer is listed. Note its name exactly (e.g., `POS-80` or `XP-80`).
2. Launch Bhumi Billing and go to the **Settings (F12)** tab.
3. Locate **System Target Printer** under "Receipt & Printer Setup".
4. Select the matching printer from the dropdown. (The app queries and displays all available system printer names automatically).
5. Choose **Thermal Template Size** (select `80mm` or `58mm` depending on roll size).
6. Click **Save Settings**.
7. Future billing checkouts using **F9 / Ctrl+P** will now skip all standard popups and print directly to that thermal device.

---

## 5. Standalone Compiling (EXE Build)

To build a standalone executable (`BhumiBilling.exe`) for Windows deployment:
1. Run the automated script:
   ```cmd
   build.bat
   ```
   Or run PyInstaller manually:
   ```cmd
   pyinstaller --noconsole --onefile --clean --name="BhumiBilling" main.py
   ```
2. The standalone package will compile and save inside the `dist/` folder.
3. Distribute `dist/BhumiBilling.exe` to client machines. They do **not** need Python installed.

---

## 6. Safety, Crash Recovery & Backups

### Real-Time Crash Recovery
If power outages occur or Windows closes unexpectedly:
- The app updates a `draft_invoice` table in SQLite on every keystroke.
- When the app is launched again, it alerts the user to restore the exact state of the uncompleted checkout.

### Automated Backups
- On the first launch of every new calendar day, the system checkpoints SQLite and copies the DB file into `data/backups/bhumi_billing_backup_YYYYMMDD.db`.
- A static duplicate `data/backups/backup.db` is also overwritten daily.
- To restore a backup, copy the backup `.db` file into `data/` and rename it to `bhumi_billing.db`.
