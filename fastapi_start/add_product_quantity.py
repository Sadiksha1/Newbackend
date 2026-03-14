#!/usr/bin/env python3
"""
One-off helper script to add a `quantity` column to the `products` table.

- Works against the local SQLite database `products.db`
- Adds: quantity INTEGER NOT NULL DEFAULT 1
- Safe to run multiple times (no-op if the column already exists)
"""

import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).parent / "products.db"


def main() -> None:
  if not DB_PATH.exists():
    print(f"❌ Database not found at {DB_PATH}. Start the backend once so it can be created.")
    return

  conn = sqlite3.connect(str(DB_PATH))
  try:
    cur = conn.cursor()

    # Check existing columns
    cur.execute("PRAGMA table_info(products)")
    cols = [row[1] for row in cur.fetchall()]
    if "quantity" in cols:
      print("✅ Column `quantity` already exists on `products` table. Nothing to do.")
      return

    print("➕ Adding `quantity` column to `products` table…")
    cur.execute("ALTER TABLE products ADD COLUMN quantity INTEGER NOT NULL DEFAULT 1")
    conn.commit()
    print("✅ Column `quantity` added and existing rows initialised to 1.")
  finally:
    conn.close()


if __name__ == "__main__":
  main()

