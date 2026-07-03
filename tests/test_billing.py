import unittest
import os
import shutil
import tempfile
from db_manager import DatabaseManager
from ui.billing_widget import BillingWidget
from PySide6.QtWidgets import QApplication

class TestBhumiBilling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a single QApplication instance for Qt-related class instantiation tests if needed
        # We check if QApplication instance already exists to avoid crashes
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication([])

    def setUp(self):
        # Create temp database for testing
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_bhumi.db")
        self.db = DatabaseManager(self.db_path)

    def tearDown(self):
        # Clean up temp files
        shutil.rmtree(self.test_dir)

    def test_database_initialization(self):
        """Verify standard settings and default items are seeded correctly."""
        settings = self.db.get_all_settings()
        self.assertEqual(settings.get("business_name"), "Bhumi Jewellers")
        self.assertEqual(settings.get("theme"), "dark")

        products = self.db.get_all_products()
        self.assertTrue(len(products) >= 5) # Seeds 5 sample products
        self.assertEqual(products[0]["code"], "101")
        self.assertEqual(products[0]["name"], "Nath Gold")

        customers = self.db.get_all_customers()
        self.assertEqual(len(customers), 1) # Walk-in Customer seeded
        self.assertEqual(customers[0]["name"], "Walk-in Customer")

    def test_bill_number_generation(self):
        """Verify auto sequential bill numbers increment correctly."""
        bill1 = self.db.generate_next_bill_number()
        self.assertTrue(bill1.startswith("BAJ-2026-"))
        self.assertTrue(bill1.endswith("0001"))

        # Save an invoice
        items = [{"product_id": 1, "product_code": "101", "product_name": "Nath Gold", "qty": 1.0, "rate": 15000.0}]
        self.db.save_invoice(bill1, 1, "retail", "none", 0.0, 15000.0, 15000.0, "paid", 15000.0, 0.0, "", items)

        bill2 = self.db.generate_next_bill_number()
        self.assertTrue(bill2.endswith("0002"))

    def test_single_line_parsing(self):
        """Verify parsing of expressions for ultra-fast single-line billing."""
        # Create dummy widget to test parsing logic
        widget = BillingWidget(self.db)
        
        # Test Case 1: Name and Qty and Rate
        res = widget.parse_single_line_expression("e 2 120")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "e")
        self.assertEqual(res[1], 2.0)
        self.assertEqual(res[2], 120.0)

        # Test Case 2: Multi-word query, Qty, Rate
        res = widget.parse_single_line_expression("gold top earrings 5 8000")
        self.assertEqual(res[0], "gold top earrings")
        self.assertEqual(res[1], 5.0)
        self.assertEqual(res[2], 8000.0)

        # Test Case 3: Code and Qty
        res = widget.parse_single_line_expression("110 3")
        self.assertEqual(res[0], "110")
        self.assertEqual(res[1], 3.0)
        self.assertIsNone(res[2])

        # Test Case 4: Pure Code (No qty or rate)
        res = widget.parse_single_line_expression("101")
        self.assertEqual(res[0], "101")
        self.assertEqual(res[1], 1.0)
        self.assertIsNone(res[2])

        # Test Case 5: Decimal Qty (Weight based)
        res = widget.parse_single_line_expression("110 2.450 55000")
        self.assertEqual(res[0], "110")
        self.assertEqual(res[1], 2.450)
        self.assertEqual(res[2], 55000.0)

    def test_add_item_merge_logic(self):
        """Verify products only merge if both code and rate match."""
        widget = BillingWidget(self.db)
        
        product = {
            "id": 1,
            "code": "101",
            "name": "Nath Gold",
            "retail_rate": 15000.0,
            "wholesale_rate": 14200.0
        }
        
        # 1. Add product with rate 10
        widget.add_item_to_bill(product, qty=1.0, rate=10.0)
        self.assertEqual(len(widget.active_items), 1)
        self.assertEqual(widget.active_items[0]["qty"], 1.0)
        self.assertEqual(widget.active_items[0]["rate"], 10.0)
        
        # 2. Add same product with same rate -> should merge
        widget.add_item_to_bill(product, qty=1.0, rate=10.0)
        self.assertEqual(len(widget.active_items), 1)
        self.assertEqual(widget.active_items[0]["qty"], 2.0)
        self.assertEqual(widget.active_items[0]["rate"], 10.0)
        
        # 3. Add same product with different rate -> should not merge, should create new row
        widget.add_item_to_bill(product, qty=1.0, rate=11.0)
        self.assertEqual(len(widget.active_items), 2)
        
        # Row 1 (merged)
        self.assertEqual(widget.active_items[0]["product_code"], "101")
        self.assertEqual(widget.active_items[0]["qty"], 2.0)
        self.assertEqual(widget.active_items[0]["rate"], 10.0)
        
        # Row 2 (new)
        self.assertEqual(widget.active_items[1]["product_code"], "101")
        self.assertEqual(widget.active_items[1]["qty"], 1.0)
        self.assertEqual(widget.active_items[1]["rate"], 11.0)

    def test_retroactive_payments_migration(self):
        """Verify pre-existing paid invoices are migrated to invoice_payments."""
        # 1. Manually insert invoice without payment records
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO invoices (bill_no, date, customer_id, gross_total, net_total, paid_amount, pending_amount, payment_status)
                VALUES ('TEST-MIG-1', '2026-06-20 10:00:00', 1, 1000.0, 1000.0, 400.0, 600.0, 'partial')
            """)
            conn.commit()

        # 2. Re-initialize database manager (triggers the migration logic)
        migrator_db = DatabaseManager(self.db_path)
        
        # 3. Retrieve payments and check
        with migrator_db.get_connection() as conn:
            inv = conn.execute("SELECT id FROM invoices WHERE bill_no = 'TEST-MIG-1'").fetchone()
            inv_id = inv["id"]
        
        payments = migrator_db.get_invoice_payments(inv_id)
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments[0]["amount"], 400.0)
        self.assertEqual(payments[0]["payment_mode"], "Cash")
        self.assertEqual(payments[0]["remaining"], 600.0)

    def test_invoice_items_edit_and_recalculation(self):
        """Verify editing and deleting invoice items recalculates invoice totals correctly."""
        # 1. Create invoice with 2 items
        items = [
            {"product_id": 1, "product_code": "101", "product_name": "Necklace", "qty": 2.0, "rate": 1000.0},
            {"product_id": 2, "product_code": "110", "product_name": "Earrings", "qty": 1.0, "rate": 500.0}
        ]
        bill_no = self.db.generate_next_bill_number()
        final_bill_no, inv_id = self.db.save_invoice(
            bill_no, 1, "retail", "none", 0.0, 2500.0, 2500.0, "partial", 1000.0, 1500.0, "", items, "Cash"
        )
        
        # Verify initial invoice state
        inv = self.db.get_invoice_by_bill_no(final_bill_no)
        self.assertEqual(inv["gross_total"], 2500.0)
        self.assertEqual(inv["net_total"], 2500.0)
        self.assertEqual(inv["paid_amount"], 1000.0)
        self.assertEqual(inv["pending_amount"], 1500.0)
        self.assertEqual(inv["payment_status"], "partial")
        
        # 2. Modify Necklace quantity from 2 -> 3 (total becomes 3*1000 = 3000)
        # Total gross becomes 3000 + 500 = 3500.
        necklace_item = [item for item in inv["items"] if item["product_name"] == "Necklace"][0]
        self.db.update_invoice_item_qty_rate(necklace_item["id"], 3.0, 1000.0)
        
        # Recalculate invoice totals
        res = self.db.recalculate_invoice_totals(inv_id)
        self.assertEqual(res["gross_total"], 3500.0)
        self.assertEqual(res["net_total"], 3500.0)
        self.assertEqual(res["paid_amount"], 1000.0)
        self.assertEqual(res["pending_amount"], 2500.0)
        
        # 3. Delete earrings row (gross becomes 3000)
        earrings_item = [item for item in inv["items"] if item["product_name"] == "Earrings"][0]
        self.db.delete_invoice_item(earrings_item["id"])
        
        res = self.db.recalculate_invoice_totals(inv_id)
        self.assertEqual(res["gross_total"], 3000.0)
        self.assertEqual(res["net_total"], 3000.0)
        self.assertEqual(res["pending_amount"], 2000.0)

    def test_balance_payment_and_overpayment_protection(self):
        """Verify adding balance payments behaves correctly and prevents overpayment."""
        items = [{"product_id": 1, "product_code": "101", "product_name": "Necklace", "qty": 1.0, "rate": 1000.0}]
        bill_no = self.db.generate_next_bill_number()
        final_bill_no, inv_id = self.db.save_invoice(
            bill_no, 1, "retail", "none", 0.0, 1000.0, 1000.0, "partial", 400.0, 600.0, "", items, "Cash"
        )
        
        # Add payment of 200
        new_paid, new_pending, new_status = self.db.add_invoice_payment(inv_id, 200.0, "UPI")
        self.assertEqual(new_paid, 600.0)
        self.assertEqual(new_pending, 400.0)
        self.assertEqual(new_status, "partial")
        
        # Verify payments history
        payments = self.db.get_invoice_payments(inv_id)
        self.assertEqual(len(payments), 2) # Initial payment of 400 + UPI payment of 200
        self.assertEqual(payments[1]["amount"], 200.0)
        self.assertEqual(payments[1]["payment_mode"], "UPI")
        self.assertEqual(payments[1]["remaining"], 400.0)
        
        # Add final payment of 400
        new_paid, new_pending, new_status = self.db.add_invoice_payment(inv_id, 400.0, "Card")
        self.assertEqual(new_paid, 1000.0)
        self.assertEqual(new_pending, 0.0)
        self.assertEqual(new_status, "paid")

if __name__ == "__main__":
    unittest.main()
