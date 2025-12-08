#!/usr/bin/env python3
"""
Script to delete all orders using SQLAlchemy (uses your models)
"""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal
from app import models

def clear_all_orders():
    db = SessionLocal()
    try:
        # Count orders before deletion
        count = db.query(models.Order).count()
        
        if count == 0:
            print("✅ No orders found in the database. Nothing to delete.")
            return
        
        print(f"⚠️  Found {count} order(s) in the database.")
        response = input("Are you sure you want to delete ALL orders? (yes/no): ")
        
        if response.lower() in ['yes', 'y']:
            # Delete all orders
            db.query(models.Order).delete()
            db.commit()
            print(f"✅ Successfully deleted {count} order(s) from the database.")
        else:
            print("❌ Operation cancelled. No orders were deleted.")
            db.rollback()
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_all_orders()

