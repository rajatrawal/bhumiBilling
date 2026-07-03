# Reset Products Script
"""
This script clears the existing products table (preserving other data) and populates it with a predefined list of product names.
Each product is assigned a sequential code starting from "1" and default retail and wholesale rates of 0.0.
"""

import sys
import os

# Ensure the project root is in the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from db_manager import DatabaseManager

# List of product names to add (as provided by the user)
PRODUCT_NAMES = [
    "AD Necklace",
    "Angathi",
    "Bajuband",
    "Bali",
    "Bangles",
    "Bormal",
    "Bracelet",
    "Bugadi",
    "Chain",
    "Chinchpeti",
    "Chitak",
    "Combo Set",
    "Crystal Pot",
    "Damaru MS",
    "Forming MS (A)",
    "Forming MS (F)",
    "Golden Necklace",
    "Jhumka",
    "Jondhale Pot",
    "Kaanchain",
    "Kada",
    "Kolhapuri Saaj",
    "Laxmihar",
    "Micro MS",
    "Mohanmala",
    "Mugvat",
    "Nath",
    "Pendant",
    "Pohe Haar",
    "Pot",
    "Ranihar",
    "Ringa",
    "Short MS",
    "Tanmani",
    "Thushi",
    "Tops",
    "Vati",
]

def reset_and_populate():
    db = DatabaseManager()
    # Clear existing products
    with db.get_connection() as conn:
        conn.execute("DELETE FROM products")
        conn.commit()
    # Insert new products with sequential codes
    for idx, name in enumerate(PRODUCT_NAMES, start=1):
        code = str(idx)
        db.add_product(code=code, name=name, retail_rate=0.0, wholesale_rate=0.0, notes="")
    print(f"Inserted {len(PRODUCT_NAMES)} products into the database.")

if __name__ == "__main__":
    reset_and_populate()
