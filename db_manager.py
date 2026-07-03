import sqlite3
import os
import shutil
from datetime import datetime
from config import DB_PATH, BACKUP_DIR, DEFAULT_SETTINGS

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        """Get database connection with WAL mode enabled and foreign keys enforced."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def init_db(self):
        """Create tables and initialize standard settings / defaults if empty."""
        with self.get_connection() as conn:
            # 1. Settings Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # 2. Products Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    retail_rate REAL DEFAULT 0.0,
                    wholesale_rate REAL DEFAULT 0.0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_products_code ON products(code);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);")

            # 3. Customers Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    mobile TEXT,
                    address TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_customers_mobile ON customers(mobile);")

            # 4. Invoices Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bill_no TEXT UNIQUE NOT NULL,
                    date TEXT NOT NULL,
                    customer_id INTEGER,
                    mode TEXT CHECK(mode IN ('retail', 'wholesale')) DEFAULT 'retail',
                    discount_type TEXT CHECK(discount_type IN ('percentage', 'amount', 'none')) DEFAULT 'none',
                    discount_value REAL DEFAULT 0.0,
                    gross_total REAL DEFAULT 0.0,
                    net_total REAL DEFAULT 0.0,
                    payment_status TEXT CHECK(payment_status IN ('paid', 'pending', 'partial')) DEFAULT 'paid',
                    paid_amount REAL DEFAULT 0.0,
                    pending_amount REAL DEFAULT 0.0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(customer_id) REFERENCES customers(id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_invoices_bill_no ON invoices(bill_no);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(date);")

            # 5. Invoice Items Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS invoice_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    product_id INTEGER,
                    product_code TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    qty REAL DEFAULT 1.0,
                    rate REAL DEFAULT 0.0,
                    total REAL DEFAULT 0.0,
                    FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
                )
            """)

            # 6. Cash Book Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cash_book (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    type TEXT CHECK(type IN ('opening', 'sale', 'expense')) NOT NULL,
                    description TEXT,
                    amount REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 7. Draft Table (For crash recovery)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS draft_invoice (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    customer_id INTEGER,
                    mode TEXT DEFAULT 'retail',
                    discount_type TEXT DEFAULT 'none',
                    discount_value REAL DEFAULT 0.0,
                    payment_status TEXT DEFAULT 'paid',
                    paid_amount REAL DEFAULT 0.0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS draft_invoice_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    product_code TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    qty REAL DEFAULT 1.0,
                    rate REAL DEFAULT 0.0
                )
            """)

            # 8. Invoice Payments Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS invoice_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    payment_date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    payment_mode TEXT CHECK(payment_mode IN ('Cash', 'UPI', 'Card', 'Other')) DEFAULT 'Cash',
                    remaining REAL DEFAULT 0.0,
                    FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
                )
            """)

            # Seed default settings if not exists
            for key, val in DEFAULT_SETTINGS.items():
                conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, str(val)))

            # Seed a default customer if customers table is completely empty
            cursor = conn.execute("SELECT COUNT(*) FROM customers")
            if cursor.fetchone()[0] == 0:
                conn.execute(
                    "INSERT INTO customers (name, mobile, address, notes) VALUES (?, ?, ?, ?)",
                    (DEFAULT_SETTINGS["default_customer_name"],
                     DEFAULT_SETTINGS["default_customer_mobile"],
                     DEFAULT_SETTINGS["default_customer_address"],
                     "System Created default customer")
                )

            # Seed default product samples if empty
            cursor = conn.execute("SELECT COUNT(*) FROM products")
            if cursor.fetchone()[0] == 0:
                samples = [
                    ("101", "Nath Gold", 15000.00, 14200.00, "Traditional Maharashtrian Nose Ring"),
                    ("110", "Kolhapuri Saaj", 45000.00, 43000.00, "Traditional gold necklace"),
                    ("15", "Earrings Silver", 1500.00, 1300.00, "Sterling silver earrings"),
                    ("12", "Gold Tops", 8000.00, 7600.00, "Daily wear gold studs"),
                    ("22", "Tanmani", 55000.00, 52000.00, "Pearl and gold pendant set")
                ]
                conn.executemany(
                    "INSERT INTO products (code, name, retail_rate, wholesale_rate, notes) VALUES (?, ?, ?, ?, ?)",
                    samples
                )

            # Run backward compatibility migration for existing invoices
            cursor = conn.execute("SELECT id, date, paid_amount, net_total FROM invoices")
            invoices_list = cursor.fetchall()
            for inv in invoices_list:
                inv_id = inv["id"]
                exists = conn.execute("SELECT COUNT(*) FROM invoice_payments WHERE invoice_id = ?", (inv_id,)).fetchone()[0]
                if exists == 0 and inv["paid_amount"] > 0:
                    remaining = max(0.0, inv["net_total"] - inv["paid_amount"])
                    conn.execute("""
                        INSERT INTO invoice_payments (invoice_id, payment_date, amount, payment_mode, remaining)
                        VALUES (?, ?, ?, 'Cash', ?)
                    """, (inv_id, inv["date"], inv["paid_amount"], remaining))

            conn.commit()

    # ==========================================
    # SETTINGS CRUD
    # ==========================================
    def get_setting(self, key, default=None):
        with self.get_connection() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else default

    def get_all_settings(self):
        with self.get_connection() as conn:
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
            return {row["key"]: row["value"] for row in rows}

    def save_settings(self, settings_dict):
        with self.get_connection() as conn:
            for key, val in settings_dict.items():
                conn.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    (key, str(val))
                )
            conn.commit()

    # ==========================================
    # PRODUCT CRUD
    # ==========================================
    def add_product(self, code, name, retail_rate, wholesale_rate, notes=""):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO products (code, name, retail_rate, wholesale_rate, notes) VALUES (?, ?, ?, ?, ?)",
                (code.strip(), name.strip(), float(retail_rate), float(wholesale_rate), notes.strip())
            )
            conn.commit()

    def update_product(self, product_id, code, name, retail_rate, wholesale_rate, notes=""):
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE products SET code = ?, name = ?, retail_rate = ?, wholesale_rate = ?, notes = ? WHERE id = ?",
                (code.strip(), name.strip(), float(retail_rate), float(wholesale_rate), notes.strip(), product_id)
            )
            conn.commit()

    def delete_product(self, product_id):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()

    def search_products(self, query):
        """Search products by code (exact prefix) or name (fuzzy/contains)."""
        query = query.strip()
        if not query:
            return []
        with self.get_connection() as conn:
            # First, check for exact product code prefix match
            rows = conn.execute(
                "SELECT * FROM products WHERE code LIKE ? ORDER BY LENGTH(code) ASC LIMIT 20",
                (f"{query}%",)
            ).fetchall()
            
            # If no matches or few matches, append containing-name matches
            if len(rows) < 10:
                name_rows = conn.execute(
                    "SELECT * FROM products WHERE name LIKE ? AND code NOT LIKE ? ORDER BY name ASC LIMIT 20",
                    (f"%{query}%", f"{query}%")
                ).fetchall()
                rows = list(rows) + list(name_rows)
            return [dict(r) for r in rows[:20]]

    def get_product_by_code(self, code):
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM products WHERE code = ?", (code.strip(),)).fetchone()
            return dict(row) if row else None

    def get_all_products(self):
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM products ORDER BY code ASC").fetchall()
            return [dict(r) for r in rows]

    # ==========================================
    # CUSTOMER CRUD
    # ==========================================
    def add_customer(self, name, mobile, address, notes=""):
        with self.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO customers (name, mobile, address, notes) VALUES (?, ?, ?, ?)",
                (name.strip(), mobile.strip(), address.strip(), notes.strip())
            )
            conn.commit()
            return cursor.lastrowid

    def update_customer(self, customer_id, name, mobile, address, notes=""):
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE customers SET name = ?, mobile = ?, address = ?, notes = ? WHERE id = ?",
                (name.strip(), mobile.strip(), address.strip(), notes.strip(), customer_id)
            )
            conn.commit()

    def delete_customer(self, customer_id):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
            conn.commit()

    def search_customers(self, query):
        query = query.strip()
        if not query:
            return []
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM customers WHERE name LIKE ? OR mobile LIKE ? ORDER BY name ASC LIMIT 20",
                (f"%{query}%", f"%{query}%")
            ).fetchall()
            return [dict(r) for r in rows]

    def get_all_customers(self):
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM customers ORDER BY name ASC").fetchall()
            return [dict(r) for r in rows]

    # ==========================================
    # BILLING / INVOICE LOGIC
    # ==========================================
    def generate_next_bill_number(self):
        """Generates sequential BAJ-YYYY-XXXX invoice numbers."""
        current_year = datetime.now().strftime("%Y")
        prefix = f"BAJ-{current_year}-"
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT bill_no FROM invoices WHERE bill_no LIKE ? ORDER BY bill_no DESC LIMIT 1",
                (f"{prefix}%",)
            ).fetchone()
            
            if row:
                last_bill = row["bill_no"]
                try:
                    last_serial = int(last_bill.split("-")[-1])
                    next_serial = last_serial + 1
                except (ValueError, IndexError):
                    next_serial = 1
            else:
                next_serial = 1
            
            return f"{prefix}{next_serial:04d}"

    def save_invoice(self, bill_no, customer_id, mode, discount_type, discount_value,
                     gross_total, net_total, payment_status, paid_amount, pending_amount,
                     notes, items, payment_mode="Cash"):
        """Saves a completed invoice and its itemized lines inside a single transaction."""
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.get_connection() as conn:
            try:
                # Use Transaction
                conn.execute("BEGIN TRANSACTION")
                
                # Check for duplicate bill_no
                dup = conn.execute("SELECT id FROM invoices WHERE bill_no = ?", (bill_no,)).fetchone()
                if dup:
                    # Regenerate fresh bill number if duplicate occurs (due to concurrency)
                    bill_no = self.generate_next_bill_number()

                cursor = conn.execute("""
                    INSERT INTO invoices (
                        bill_no, date, customer_id, mode, discount_type, discount_value,
                        gross_total, net_total, payment_status, paid_amount, pending_amount, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    bill_no, date_str, customer_id, mode, discount_type, float(discount_value),
                    float(gross_total), float(net_total), payment_status, float(paid_amount),
                    float(pending_amount), notes
                ))
                
                invoice_id = cursor.lastrowid
                
                # Insert items
                for item in items:
                    conn.execute("""
                        INSERT INTO invoice_items (
                            invoice_id, product_id, product_code, product_name, qty, rate, total
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        invoice_id, item.get("product_id"), item["product_code"], item["product_name"],
                        float(item["qty"]), float(item["rate"]), float(item["qty"]) * float(item["rate"])
                    ))
                
                # Log transaction to invoice_payments if payment is made
                if float(paid_amount) > 0:
                    conn.execute("""
                        INSERT INTO invoice_payments (invoice_id, payment_date, amount, payment_mode, remaining)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        invoice_id,
                        date_str,
                        float(paid_amount),
                        payment_mode,
                        float(pending_amount)
                    ))
                
                # Clear active draft upon successful save
                conn.execute("DELETE FROM draft_invoice")
                conn.execute("DELETE FROM draft_invoice_items")
                
                conn.commit()
                return bill_no, invoice_id
            except Exception as e:
                conn.rollback()
                raise e

    def get_recent_products(self):
        """Retrieve details of the last 20 unique billed products for F4 Recents view."""
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT p.id, p.code, p.name, p.retail_rate, p.wholesale_rate, p.notes
                FROM invoice_items ii
                JOIN products p ON ii.product_id = p.id
                GROUP BY p.id
                ORDER BY MAX(ii.id) DESC
                LIMIT 20
            """).fetchall()
            return [dict(r) for r in rows]

    def get_invoice_by_bill_no(self, bill_no):
        with self.get_connection() as conn:
            inv_row = conn.execute("""
                SELECT i.*, c.name as customer_name, c.mobile as customer_mobile, c.address as customer_address
                FROM invoices i
                LEFT JOIN customers c ON i.customer_id = c.id
                WHERE i.bill_no = ?
            """, (bill_no,)).fetchone()
            
            if not inv_row:
                return None
                
            items_rows = conn.execute("""
                SELECT * FROM invoice_items WHERE invoice_id = ?
            """, (inv_row["id"],)).fetchall()
            
            invoice = dict(inv_row)
            invoice["items"] = [dict(r) for r in items_rows]
            return invoice

    def get_all_invoices(self, customer_id=None, pending_only=False, start_date=None, end_date=None):
        """Queries invoices with dynamic filter matching."""
        query_str = """
            SELECT i.*, c.name as customer_name, c.mobile as customer_mobile 
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            WHERE 1=1
        """
        params = []
        
        if customer_id:
            query_str += " AND i.customer_id = ?"
            params.append(customer_id)
            
        if pending_only:
            query_str += " AND i.payment_status IN ('pending', 'partial')"
            
        if start_date:
            query_str += " AND date(i.date) >= date(?)"
            params.append(start_date)
            
        if end_date:
            query_str += " AND date(i.date) <= date(?)"
            params.append(end_date)
            
        query_str += " ORDER BY i.id DESC"
        
        with self.get_connection() as conn:
            rows = conn.execute(query_str, params).fetchall()
            return [dict(r) for r in rows]

    def update_invoice_payment(self, invoice_id, paid_amount, pending_amount, payment_status, payment_mode="Cash"):
        """Update outstanding invoice payment tracker and log to invoice_payments."""
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.get_connection() as conn:
            conn.execute("BEGIN TRANSACTION")
            try:
                # Get existing payment values
                old_row = conn.execute("SELECT bill_no, paid_amount FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
                if not old_row:
                    raise ValueError("Invoice not found")
                
                old_paid = old_row["paid_amount"]
                diff = float(paid_amount) - old_paid
                
                conn.execute("""
                    UPDATE invoices 
                    SET paid_amount = ?, pending_amount = ?, payment_status = ?
                    WHERE id = ?
                """, (float(paid_amount), float(pending_amount), payment_status, invoice_id))
                
                # Log adjustment to invoice_payments if positive change
                if diff > 0:
                    conn.execute("""
                        INSERT INTO invoice_payments (invoice_id, payment_date, amount, payment_mode, remaining)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        invoice_id,
                        date_str,
                        diff,
                        payment_mode,
                        float(pending_amount)
                    ))
                
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e

    def add_invoice_payment(self, invoice_id, amount, payment_mode="Cash"):
        """Record a new payment for an invoice and update invoice outstanding totals."""
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.get_connection() as conn:
            conn.execute("BEGIN TRANSACTION")
            try:
                # Get current invoice totals
                inv = conn.execute("SELECT net_total, paid_amount, pending_amount FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
                if not inv:
                    raise ValueError("Invoice not found")
                
                new_paid = inv["paid_amount"] + float(amount)
                new_pending = max(0.0, inv["net_total"] - new_paid)
                new_status = "paid" if new_pending == 0 else "partial"
                
                # Update invoice record
                conn.execute("""
                    UPDATE invoices 
                    SET paid_amount = ?, pending_amount = ?, payment_status = ?
                    WHERE id = ?
                """, (new_paid, new_pending, new_status, invoice_id))
                
                # Insert payment record
                conn.execute("""
                    INSERT INTO invoice_payments (invoice_id, payment_date, amount, payment_mode, remaining)
                    VALUES (?, ?, ?, ?, ?)
                """, (invoice_id, date_str, float(amount), payment_mode, new_pending))
                
                conn.commit()
                return new_paid, new_pending, new_status
            except Exception as e:
                conn.rollback()
                raise e

    def get_invoice_payments(self, invoice_id):
        """Fetch payment history for an invoice."""
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM invoice_payments 
                WHERE invoice_id = ? 
                ORDER BY id ASC
            """, (invoice_id,)).fetchall()
            return [dict(r) for r in rows]

    def update_invoice_item_qty_rate(self, item_id, new_qty, new_rate):
        """Update an invoice item's quantity, rate, and total."""
        with self.get_connection() as conn:
            conn.execute("BEGIN TRANSACTION")
            try:
                total = float(new_qty) * float(new_rate)
                conn.execute("""
                    UPDATE invoice_items 
                    SET qty = ?, rate = ?, total = ?
                    WHERE id = ?
                """, (float(new_qty), float(new_rate), total, item_id))
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e

    def delete_invoice_item(self, item_id):
        """Delete an invoice item."""
        with self.get_connection() as conn:
            conn.execute("BEGIN TRANSACTION")
            try:
                conn.execute("DELETE FROM invoice_items WHERE id = ?", (item_id,))
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e

    def recalculate_invoice_totals(self, invoice_id):
        """Recompute all gross, net, paid, and pending values for the invoice."""
        with self.get_connection() as conn:
            conn.execute("BEGIN TRANSACTION")
            try:
                # 1. Sum gross total from items
                gross_row = conn.execute("SELECT SUM(total) FROM invoice_items WHERE invoice_id = ?", (invoice_id,)).fetchone()
                gross = gross_row[0] if gross_row[0] is not None else 0.0
                
                # 2. Get invoice details
                inv = conn.execute("SELECT discount_type, discount_value FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
                if not inv:
                    raise ValueError("Invoice not found")
                
                disc_type = inv["discount_type"]
                disc_val = inv["discount_value"]
                
                # 3. Calculate discount amount
                if disc_type == "percentage":
                    disc_amt = (disc_val / 100.0) * gross
                elif disc_type == "amount":
                    disc_amt = min(disc_val, gross)
                else:
                    disc_amt = 0.0
                    
                net = max(0.0, gross - disc_amt)
                
                # 4. Sum total payments made
                pmt_row = conn.execute("SELECT SUM(amount) FROM invoice_payments WHERE invoice_id = ?", (invoice_id,)).fetchone()
                total_paid = pmt_row[0] if pmt_row[0] is not None else 0.0
                
                # Cap paid amount to new net total if payments exceed it
                paid = min(net, total_paid)
                pending = max(0.0, net - paid)
                status = "paid" if pending == 0 else ("partial" if paid > 0 else "pending")
                
                # 5. Update invoice
                conn.execute("""
                    UPDATE invoices 
                    SET gross_total = ?, net_total = ?, paid_amount = ?, pending_amount = ?, payment_status = ?
                    WHERE id = ?
                """, (gross, net, paid, pending, status, invoice_id))
                
                conn.commit()
                return {
                    "gross_total": gross,
                    "net_total": net,
                    "paid_amount": paid,
                    "pending_amount": pending,
                    "payment_status": status
                }
            except Exception as e:
                conn.rollback()
                raise e

    # ==========================================
    # DRAFT RECOVERY LOGIC (Real-time autosave)
    # ==========================================
    def save_draft(self, customer_id, mode, discount_type, discount_value, payment_status, paid_amount, items):
        with self.get_connection() as conn:
            conn.execute("BEGIN TRANSACTION")
            try:
                # Clear previous draft
                conn.execute("DELETE FROM draft_invoice")
                conn.execute("DELETE FROM draft_invoice_items")
                
                # Insert main draft info
                conn.execute("""
                    INSERT INTO draft_invoice (id, customer_id, mode, discount_type, discount_value, payment_status, paid_amount, updated_at)
                    VALUES (1, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (customer_id, mode, discount_type, float(discount_value), payment_status, float(paid_amount)))
                
                # Insert draft items
                for item in items:
                    conn.execute("""
                        INSERT INTO draft_invoice_items (product_id, product_code, product_name, qty, rate)
                        VALUES (?, ?, ?, ?, ?)
                    """, (item.get("product_id"), item["product_code"], item["product_name"], float(item["qty"]), float(item["rate"])))
                
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e

    def load_draft(self):
        with self.get_connection() as conn:
            draft_row = conn.execute("SELECT * FROM draft_invoice WHERE id = 1").fetchone()
            if not draft_row:
                return None
                
            items_rows = conn.execute("SELECT * FROM draft_invoice_items").fetchall()
            
            draft = dict(draft_row)
            draft["items"] = [dict(r) for r in items_rows]
            return draft

    def clear_draft(self):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM draft_invoice")
            conn.execute("DELETE FROM draft_invoice_items")
            conn.commit()

    # ==========================================
    # CASH BOOK OPERATIONS
    # ==========================================
    def add_cash_entry(self, entry_type, description, amount, date_str=None):
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO cash_book (date, type, description, amount)
                VALUES (?, ?, ?, ?)
            """, (date_str, entry_type, description.strip(), float(amount)))
            conn.commit()

    def get_cash_book_entries(self, date_str):
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM cash_book WHERE date = ? ORDER BY id ASC", (date_str,)).fetchall()
            return [dict(r) for r in rows]

    def delete_cash_entry(self, entry_id):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM cash_book WHERE id = ?", (entry_id,))
            conn.commit()

    def get_daily_tally(self, date_str):
        """Fetches cash stats and summary details for daily reporting."""
        with self.get_connection() as conn:
            # 1. Total Bills Today
            bills_count = conn.execute(
                "SELECT COUNT(*) FROM invoices WHERE date(date) = date(?)",
                (date_str,)
            ).fetchone()[0]
            
            # 2. Sum Gross & Net Sales
            totals = conn.execute("""
                SELECT IFNULL(SUM(gross_total), 0) as gross, 
                       IFNULL(SUM(net_total), 0) as net,
                       IFNULL(SUM(paid_amount), 0) as paid,
                       IFNULL(SUM(pending_amount), 0) as pending
                FROM invoices WHERE date(date) = date(?)
            """, (date_str,)).fetchone()
            
            # 3. Cash Book summary
            opening_cash = conn.execute("""
                SELECT IFNULL(SUM(amount), 0) FROM cash_book 
                WHERE date = ? AND type = 'opening'
            """, (date_str,)).fetchone()[0]
            
            sales_cash = conn.execute("""
                SELECT IFNULL(SUM(amount), 0) FROM cash_book 
                WHERE date = ? AND type = 'sale'
            """, (date_str,)).fetchone()[0]
            
            expense_cash = conn.execute("""
                SELECT IFNULL(SUM(amount), 0) FROM cash_book 
                WHERE date = ? AND type = 'expense'
            """, (date_str,)).fetchone()[0]
            
            closing_cash = opening_cash + sales_cash - expense_cash
            
            # 4. Total Outstanding Amount across all history
            total_outstanding = conn.execute("""
                SELECT IFNULL(SUM(pending_amount), 0) FROM invoices
            """).fetchone()[0]

            return {
                "date": date_str,
                "bills_count": bills_count,
                "gross_sales": totals["gross"],
                "net_sales": totals["net"],
                "discount_given": totals["gross"] - totals["net"],
                "paid_amount": totals["paid"],
                "pending_amount": totals["pending"],
                "outstanding_amount": total_outstanding,
                "opening_cash": opening_cash,
                "sales_cash": sales_cash,
                "expense_cash": expense_cash,
                "closing_cash": closing_cash
            }

    # ==========================================
    # BACKUP / RESTORE MANAGEMENT
    # ==========================================
    def backup_database(self):
        """Creates a timestamped backup copy inside backup folder and maintains static backup.db."""
        date_stamp = datetime.now().strftime("%Y%m%d")
        backup_file = os.path.join(BACKUP_DIR, f"bhumi_billing_backup_{date_stamp}.db")
        static_backup_file = os.path.join(BACKUP_DIR, "backup.db")
        
        # Safe checkpoint before copying
        with self.get_connection() as conn:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            
        # Copy file
        shutil.copy2(self.db_path, backup_file)
        shutil.copy2(self.db_path, static_backup_file)
        return backup_file

    def restore_database(self, backup_file_path):
        """Overwrites active database with target backup."""
        if not os.path.exists(backup_file_path):
            raise FileNotFoundError(f"Backup file not found at {backup_file_path}")
            
        # Close all SQLite connections before restoring
        # We assume clean swap since it's desktop app
        shutil.copy2(backup_file_path, self.db_path)
        # Re-initialize to ensure journal modes and integrity
        self.init_db()
