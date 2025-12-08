#!/usr/bin/env python3
"""
Seed the local SQLite DB with sample products and orders for analytics/testing.

Usage:
  python seed_data.py            # uses default sample data

Requires the app dependencies and an initialized database (alembic upgrade head).
"""
import os
from datetime import datetime, timedelta
from pathlib import Path

from app.database import SessionLocal
from app import models
from app.utils.security import hash_password

PHOTOS_DIR = Path(__file__).parent / "photos"

def seed():
    db = SessionLocal()
    try:
        # Start fresh
        db.query(models.Order).delete()
        db.query(models.Product).delete()
        db.query(models.Admin).delete()
        db.commit()

        # Seed admin from env or defaults
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "changeme123")
        admin = models.Admin(
            username=admin_username,
            password_hash=hash_password(admin_password),
        )
        db.add(admin)
        db.commit()

        # Build products only for images that actually exist
        if not PHOTOS_DIR.exists():
            print(f"❌ Photos folder not found at {PHOTOS_DIR}. Create it and add images first.")
            return

        image_files = sorted([f for f in os.listdir(PHOTOS_DIR) if f.lower().endswith((".png", ".jpg", ".jpeg"))])
        if not image_files:
            print(f"❌ No images found in {PHOTOS_DIR}. Add .png/.jpg files to seed products.")
            return

        products = []
        for idx, filename in enumerate(image_files, start=1):
            name_base = Path(filename).stem
            product_name = name_base.capitalize()
            price = 5 * idx  # simple deterministic integer pricing: 5,10,15,...
            products.append(
                models.Product(
                    name=product_name,
                    price=price,
                    category="snack",
                    image=filename,
                )
            )

        db.add_all(products)
        db.commit()
        for p in products:
            db.refresh(p)

        # Orders with varied dates and times for testing analytics
        now = datetime.utcnow()
        sample_orders = []
        
        if products:
            # Create orders across different months (last 3 months)
            months_back = [2, 1, 0]  # 2 months ago, 1 month ago, current month
            categories_list = ["snack", "chocolate", "noodle", "juice", "biscuit", "soap"]
            
            # Update product categories for variety
            for idx, product in enumerate(products):
                product.category = categories_list[idx % len(categories_list)]
            db.commit()
            
            # Paid orders across different dates and times
            order_idx = 0
            for month_offset in months_back:
                base_date = now - timedelta(days=30 * month_offset)
                
                # Create orders for different days in each month
                for day_offset in range(0, 15, 2):  # Every 2 days
                    order_date = base_date - timedelta(days=day_offset)
                    
                    # Create orders at different hours (8 AM to 10 PM)
                    for hour in [8, 10, 12, 14, 16, 18, 20, 22]:
                        if order_idx >= len(products):
                            break
                        
                        product = products[order_idx % len(products)]
                        order_datetime = order_date.replace(hour=hour, minute=30, second=0, microsecond=0)
                        
                        sample_orders.append(
                            {
                                "product": product,
                                "quantity": (order_idx % 3) + 1,
                                "status": "paid",
                                "created_at": order_datetime,
                            }
                        )
                        order_idx += 1
                        
                        if order_idx >= 50:  # Limit total orders
                            break
                    if order_idx >= 50:
                        break
                if order_idx >= 50:
                    break
            
            # Add some recent pending orders
            for i in range(min(5, len(products))):
                sample_orders.append(
                    {
                        "product": products[i],
                        "quantity": 1,
                        "status": "pending",
                        "created_at": now - timedelta(minutes=30 - i * 10),
                    }
                )

        orders = []
        for o in sample_orders:
            amount = round(o["product"].price * o["quantity"], 2)
            orders.append(
                models.Order(
                    amount=amount,
                    product_id=o["product"].id,
                    quantity=o["quantity"],
                    status=o["status"],
                    created_at=o["created_at"],
                )
            )
        db.add_all(orders)
        db.commit()

        print("✅ Seed complete:")
        print(f"  Products: {len(products)}")
        print(f"  Orders:   {len(orders)} (paid: {sum(1 for o in orders if o.status=='paid')}, pending: {sum(1 for o in orders if o.status=='pending')})")
        print("  Admins:   will auto-create on first /admin/analytics call using env ADMIN_USERNAME/ADMIN_PASSWORD")

    finally:
        db.close()


if __name__ == "__main__":
    seed()

