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


def print_table(table_name: str, label: str, formatter=None):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if not cursor.fetchone():
        print(f"\n{label} table does not exist")
        return

    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]

    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    print(f"\n{label}")
    print("-" * 60)
    print(f"Columns: {', '.join(columns)}")

    if not rows:
        print("  (No rows found)")
        return

    for row in rows:
        data = dict(zip(columns, row))
        if formatter:
            print(formatter(data))
        else:
            print(f"  {data}")


print("=" * 60)
print("DATABASE CONTENTS")
print("=" * 60)

print_table(
    "products",
    "📦 PRODUCTS TABLE:",
    formatter=lambda d: f"  ID: {d.get('id')}, Name: {d.get('name')}, Price: {d.get('price')}, Category: {d.get('category')}, Image: {d.get('image')}",
)

print_table(
    "orders",
    "🛒 ORDERS TABLE:",
    formatter=lambda d: (
        "  ID: {id}, Amount: {amount}, Product ID: {product_id}, "
        "Quantity: {quantity}, Status: {status}, Created: {created_at}"
    ).format(
        id=d.get("id"),
        amount=d.get("amount"),
        product_id=d.get("product_id"),
        quantity=d.get("quantity"),
        status=d.get("status"),
        created_at=d.get("created_at"),
    ),
)

print_table(
    "admins",
    "👤 ADMINS TABLE:",
    formatter=lambda d: f"  ID: {d.get('id')}, Username: {d.get('username')}, Created: {d.get('created_at')}",
)

print("\n" + "=" * 60)
conn.close()

