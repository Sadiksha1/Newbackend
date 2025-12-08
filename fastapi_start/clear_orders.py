#!/usr/bin/env python3
"""
Script to delete all orders from the database
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

# Check how many orders exist
cursor.execute("SELECT COUNT(*) FROM orders")
count = cursor.fetchone()[0]

if count == 0:
    print("✅ No orders found in the database. Nothing to delete.")
    conn.close()
    exit(0)

print(f"⚠️  Found {count} order(s) in the database.")
response = input("Are you sure you want to delete ALL orders? (yes/no): ")

if response.lower() in ['yes', 'y']:
    cursor.execute("DELETE FROM orders")
    conn.commit()
    print(f"✅ Successfully deleted {count} order(s) from the database.")
else:
    print("❌ Operation cancelled. No orders were deleted.")

conn.close()

