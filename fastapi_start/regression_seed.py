#!/usr/bin/env python3
"""
Seed a fixed 14‑day window of **deterministic** orders and revenue so that
the regression in /admin/analytics/advanced runs on the exact dataset used
in the analysis report (Dec 28, 2024 – Jan 10, 2025).

Each day has a specified:
  - date
  - number of paid orders (n)
  - total daily revenue y_i (NPR)

Usage (run from fastapi_start/ directory):
    python regression_seed.py               # clears orders only, keeps products
    python regression_seed.py --full-reset  # clears products + orders + admin too
"""
import argparse
import hashlib
import os
from datetime import date, datetime

from app.database import SessionLocal
from app import models


def hash_password(password: str) -> str:
    """Mirrors app.utils.security.hash_password without importing jose."""
    salt = os.getenv("ADMIN_PASSWORD_SALT", "static-salt")
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()

# ── Synthetic products (no real image files needed) ───────────────────────────
SYNTHETIC_PRODUCTS = [
    {"name": "Lays Classic Chips",  "price": 30.0,  "category": "snack",     "image": "lays.jpg"},
    {"name": "Coca Cola Can",       "price": 50.0,  "category": "drinks",    "image": "coke.jpg"},
    {"name": "Oreo Cookies",        "price": 45.0,  "category": "snack",     "image": "oreo.jpg"},
    {"name": "Mineral Water 500ml", "price": 20.0,  "category": "drinks",    "image": "water.jpg"},
    {"name": "Kurkure Masala",      "price": 25.0,  "category": "snack",     "image": "kurkure.jpg"},
    {"name": "Wai Wai Noodles",     "price": 35.0,  "category": "noodles",   "image": "waiwai.jpg"},
]

# ── Fixed daily regression dataset (Dec 28, 2024 – Jan 10, 2025) ──────────────
# Matches the report screenshot: i, Date, Day, Holiday, Orders(n), Revenue y_i
DAY_DATA = [
    # i,        date,               orders, revenue_y_i
    (0, date(2024, 12, 28), 20,  710.00),  # Saturday, YES — Udhauli
    (1, date(2024, 12, 29), 15,  960.00),  # Sunday
    (2, date(2024, 12, 30), 15, 1220.00),  # Monday
    (3, date(2024, 12, 31), 14,  860.00),  # Tuesday
    (4, date(2025, 1, 1),   12,  765.00),  # Wednesday
    (5, date(2025, 1, 2),   13,  560.00),  # Thursday
    (6, date(2025, 1, 3),   13,  480.00),  # Friday
    (7, date(2025, 1, 4),   18, 1285.00),  # Saturday
    (8, date(2025, 1, 5),   14,  970.00),  # Sunday
    (9, date(2025, 1, 6),    9,  670.00),  # Monday
    (10, date(2025, 1, 7),  11,  615.00),  # Tuesday
    (11, date(2025, 1, 8),  13,  635.00),  # Wednesday
    (12, date(2025, 1, 9),  15,  915.00),  # Thursday
    (13, date(2025, 1, 10), 10,  825.00),  # Friday
]


def seed(full_reset: bool = False) -> None:
    db = SessionLocal()

    try:
        # ── Clear data ────────────────────────────────────────────────────────
        print("🗑  Clearing existing orders…")
        db.query(models.Order).delete()

        if full_reset:
            print("🗑  Full reset: clearing products and admins…")
            db.query(models.Product).delete()
            db.query(models.Admin).delete()

        db.commit()

        # ── Ensure admin exists ───────────────────────────────────────────────
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "changeme123")
        if not db.query(models.Admin).filter(models.Admin.username == admin_username).first():
            db.add(models.Admin(
                username=admin_username,
                password_hash=hash_password(admin_password),
            ))
            db.commit()
            print(f"✅ Admin '{admin_username}' created.")
        else:
            print(f"ℹ  Admin '{admin_username}' already exists, skipped.")

        # ── Ensure products exist ─────────────────────────────────────────────
        products = db.query(models.Product).all()
        if not products:
            print("📦 No products found — creating synthetic products…")
            for p in SYNTHETIC_PRODUCTS:
                db.add(models.Product(**p))
            db.commit()
            products = db.query(models.Product).all()
            print(f"✅ {len(products)} products created.")
        else:
            print(f"ℹ  Using {len(products)} existing products.")

        # ── Generate fixed 14 days of orders ──────────────────────────────────
        print("📅 Inserting fixed regression dataset (Dec 28, 2024 – Jan 10, 2025)…")

        all_order_objs = []
        for _, day_date, n_orders, total_revenue in DAY_DATA:
            if n_orders <= 0:
                continue

            # Split total daily revenue evenly across n_orders.
            # Use all but last order with floor, and adjust last for rounding.
            base_amount = round(total_revenue / n_orders, 2)
            accumulated = 0.0

            for idx in range(n_orders):
                if idx == n_orders - 1:
                    amount = round(total_revenue - accumulated, 2)
                else:
                    amount = base_amount
                    accumulated += amount

                product = products[idx % len(products)]

                # Spread orders across the day: 10:00, 10:30, 11:00, ...
                hour   = 10 + (idx % 10)
                minute = (idx * 30) % 60

                created_at = datetime(
                    day_date.year,
                    day_date.month,
                    day_date.day,
                    hour,
                    minute,
                    0,
                )

                all_order_objs.append(
                    models.Order(
                        amount=amount,
                        product_id=product.id,
                        quantity=1,
                        status="paid",
                        created_at=created_at,
                    )
                )

        db.add_all(all_order_objs)
        db.commit()

        paid_count    = sum(1 for o in all_order_objs if o.status == "paid")
        pending_count = sum(1 for o in all_order_objs if o.status == "pending")
        total_revenue = sum(o.amount for o in all_order_objs if o.status == "paid")

        print("\n✅ Regression seed complete:")
        print(f"   Days covered  : {len(DAY_DATA)} (Dec 28, 2024 – Jan 10, 2025)")
        print(f"   Total orders  : {len(all_order_objs)}")
        print(f"     ├─ paid     : {paid_count}")
        print(f"     └─ pending  : {pending_count}")
        print(f"   Total revenue : Rs. {total_revenue:,.2f}")
        print("\n   Visit /admin/analytics/advanced after logging in to see results.")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed synthetic regression data.")
    parser.add_argument(
        "--full-reset",
        action="store_true",
        help="Also clear products and admin (default: keep them, only replace orders).",
    )
    args = parser.parse_args()
    seed(full_reset=args.full_reset)
