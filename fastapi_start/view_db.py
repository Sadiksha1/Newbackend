#!/usr/bin/env python3
"""
Script to view database contents
Run this script to see all products and orders in the database
"""
import sqlite3
from pathlib import Path

# Database path
db_path = Path(__file__).parent / "products.db"

if not db_path.exists():
    print("❌ Database file not found! Make sure the server has been run at least once.")
    exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 60)
print("DATABASE CONTENTS")
print("=" * 60)

# View Products
print("\n📦 PRODUCTS TABLE:")
print("-" * 60)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
if cursor.fetchone():
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    if products:
        # Get column names
        cursor.execute("PRAGMA table_info(products)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Columns: {', '.join(columns)}")
        print()
        for product in products:
            print(f"  ID: {product[0]}, Name: {product[1]}, Price: {product[2]}, Category: {product[3]}, Image: {product[4]}")
    else:
        print("  (No products found)")
else:
    print("  (Products table does not exist)")

# View Orders
print("\n🛒 ORDERS TABLE:")
print("-" * 60)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
if cursor.fetchone():
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    if orders:
        # Get column names
        cursor.execute("PRAGMA table_info(orders)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Columns: {', '.join(columns)}")
        print()
        for order in orders:
            print(f"  ID: {order[0]}, Amount: {order[1]}, Product ID: {order[2]}, Product Name: {order[3]}, Status: {order[4]}")
    else:
        print("  (No orders found)")
else:
    print("  (Orders table does not exist)")

print("\n" + "=" * 60)
conn.close()

