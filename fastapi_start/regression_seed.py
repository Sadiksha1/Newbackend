#!/usr/bin/env python3
"""
Full reset: delete everything (orders, products, admins), then re-insert:
  - Admin: admin / changeme123
  - Current products (from DB before delete), same ids
  - Current orders (from DB before delete), unchanged

Usage (run from fastapi_start/ directory):
    python regression_seed.py
"""
import hashlib
import os
from datetime import datetime

from app.database import SessionLocal
from app import models

# Fixed admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "changeme123"


def hash_password(password: str) -> str:
    """Mirrors app.utils.security.hash_password without importing jose."""
    salt = os.getenv("ADMIN_PASSWORD_SALT", "static-salt")
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()


def seed() -> None:
    db = SessionLocal()

    try:
        # ── 1. Fetch current products and orders (before delete) ─────────────
        print("📥 Fetching current products and orders…")
        products_rows = db.query(models.Product).order_by(models.Product.id).all()
        orders_rows = db.query(models.Order).order_by(models.Order.id).all()

        products_data = [
            {
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "category": p.category,
                "image": p.image,
                "quantity": getattr(p, "quantity", 1) or 1,
            }
            for p in products_rows
        ]
        orders_data = [
            {
                "id": o.id,
                "amount": o.amount,
                "product_id": o.product_id,
                "quantity": o.quantity,
                "status": o.status,
                "created_at": o.created_at,
            }
            for o in orders_rows
        ]

        n_products = len(products_data)
        n_orders = len(orders_data)
        print(f"   Products: {n_products}, Orders: {n_orders}")

        # ── 2. Delete everything (orders, products, admins) ───────────────────
        print("🗑  Deleting all orders…")
        db.query(models.Order).delete()
        print("🗑  Deleting all products…")
        db.query(models.Product).delete()
        print("🗑  Deleting all admins…")
        db.query(models.Admin).delete()
        db.commit()

        # ── 3. Insert admin (admin / changeme123) ─────────────────────────────
        print("👤 Creating admin (admin / changeme123)…")
        db.add(
            models.Admin(
                username=ADMIN_USERNAME,
                password_hash=hash_password(ADMIN_PASSWORD),
            )
        )
        db.commit()
        print("   ✅ Admin created.")

        # ── 4. Re-insert products with same ids, quantity = 1 ─────────────────
        if products_data:
            print("📦 Re-inserting products (quantity set to 1)…")
            for p in products_data:
                db.add(
                    models.Product(
                        id=p["id"],
                        name=p["name"],
                        price=p["price"],
                        category=p["category"],
                        image=p["image"],
                        quantity=1,
                    )
                )
            db.commit()
            print(f"   ✅ {len(products_data)} products re-inserted.")
        else:
            print("   ⚠ No products to re-insert (DB was empty).")

        # ── 5. Re-insert orders unchanged ────────────────────────────────────
        if orders_data:
            print("📅 Re-inserting orders (unchanged)…")
            for o in orders_data:
                db.add(
                    models.Order(
                        id=o["id"],
                        amount=o["amount"],
                        product_id=o["product_id"],
                        quantity=o["quantity"],
                        status=o["status"],
                        created_at=o["created_at"],
                    )
                )
            db.commit()
            print(f"   ✅ {len(orders_data)} orders re-inserted.")
        else:
            print("   ⚠ No orders to re-insert (DB had none).")

        print("\n✅ Full reset complete. Admin: admin / changeme123")
        print("   Products and orders restored as before.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
