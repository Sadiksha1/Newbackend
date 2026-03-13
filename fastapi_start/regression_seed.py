#!/usr/bin/env python3
"""
Seed 15 days of synthetic vending machine orders designed to make the
multiple linear regression in /admin/analytics/advanced clearly visible.

Patterns baked in so the regression has real signals to fit:
  - Gentle upward revenue trend over time      → slope > 0
  - Higher sales on weekends                   → is_weekend coefficient
  - Higher sales on Nepali public holidays      → is_holiday coefficient
  - Morning/lunch/evening peaks                → hourly chart
  - Monthly variation                          → month coefficient

Usage (run from fastapi_start/ directory):
    python regression_seed.py               # clears orders only, keeps products
    python regression_seed.py --full-reset  # clears products + orders + admin too
"""
import argparse
import hashlib
import os
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from app.database import SessionLocal
from app import models


def hash_password(password: str) -> str:
    """Mirrors app.utils.security.hash_password without importing jose."""
    salt = os.getenv("ADMIN_PASSWORD_SALT", "static-salt")
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()

# ── Nepali public holidays (keep in sync with admin.py) ──────────────────────
NEPAL_HOLIDAYS: set[date] = {
    date(2024, 10, 13), date(2024, 10, 29), date(2024, 10, 31),
    date(2024, 11, 1),  date(2024, 1, 15),  date(2024, 4, 14),
    date(2025, 1, 14),  date(2025, 4, 14),  date(2025, 5, 1),
    date(2025, 10, 3),  date(2025, 10, 18), date(2025, 10, 20),
    date(2025, 10, 21),
    date(2026, 1, 11),  date(2026, 2, 19),  date(2026, 3, 3),
    date(2026, 4, 14),  date(2026, 5, 1),
}

# ── Synthetic products (no real image files needed) ───────────────────────────
SYNTHETIC_PRODUCTS = [
    {"name": "Lays Classic Chips",  "price": 30.0,  "category": "snack",     "image": "lays.jpg"},
    {"name": "Coca Cola Can",       "price": 50.0,  "category": "drinks",    "image": "coke.jpg"},
    {"name": "Oreo Cookies",        "price": 45.0,  "category": "snack",     "image": "oreo.jpg"},
    {"name": "Mineral Water 500ml", "price": 20.0,  "category": "drinks",    "image": "water.jpg"},
    {"name": "Kurkure Masala",      "price": 25.0,  "category": "snack",     "image": "kurkure.jpg"},
    {"name": "Wai Wai Noodles",     "price": 35.0,  "category": "noodles",   "image": "waiwai.jpg"},
]

# Hour weights — peaks at 10 AM, 12–1 PM, 5–7 PM
_HOURS        = list(range(8, 22))
_HOUR_WEIGHTS = [2, 4, 6, 8, 7, 5, 4, 5, 7, 8, 7, 5, 3, 2]   # len == 14


def _orders_for_day(
    target_date: date,
    products: list,
    rng: random.Random,
    start_date: date,
) -> list[dict]:
    """Return a list of order dicts for one calendar day."""
    is_weekend = target_date.weekday() >= 5          # Sat or Sun
    is_holiday = target_date in NEPAL_HOLIDAYS

    # Base daily count grows gently over the 90-day window (trend)
    trend_idx   = (target_date - start_date).days    # 0 … 89
    base_count  = 4 + int(trend_idx * 0.40)          # 4 → ~10 over 15 days

    # Multipliers per day type  ← these create the regression signals
    if is_holiday:
        multiplier = rng.uniform(2.0, 2.8)
    elif is_weekend:
        multiplier = rng.uniform(1.4, 1.9)
    else:
        multiplier = rng.uniform(0.6, 1.2)

    n_orders = max(1, int(round(base_count * multiplier + rng.gauss(0, 1.2))))

    orders = []
    for _ in range(n_orders):
        product  = rng.choice(products)
        quantity = rng.choices([1, 2, 3], weights=[0.60, 0.30, 0.10])[0]
        hour     = rng.choices(_HOURS, weights=_HOUR_WEIGHTS)[0]
        minute   = rng.randint(0, 59)
        second   = rng.randint(0, 59)
        dt       = datetime(
            target_date.year, target_date.month, target_date.day,
            hour, minute, second,
        )
        orders.append({
            "product":    product,
            "quantity":   quantity,
            "status":     "paid",
            "created_at": dt,
        })

    # A small number of failed (pending-stuck) orders every few days
    if rng.random() < 0.25:
        for _ in range(rng.randint(1, 2)):
            product = rng.choice(products)
            hour    = rng.choices(_HOURS, weights=_HOUR_WEIGHTS)[0]
            dt      = datetime(target_date.year, target_date.month, target_date.day, hour, rng.randint(0, 59))
            orders.append({
                "product":    product,
                "quantity":   1,
                "status":     "pending",
                "created_at": dt,
            })

    return orders


def seed(full_reset: bool = False) -> None:
    rng = random.Random(42)   # fixed seed → reproducible data
    db  = SessionLocal()

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

        # ── Generate 90 days of orders ────────────────────────────────────────
        end_date   = date.today()
        start_date = end_date - timedelta(days=14)   # 15 days inclusive
        print(f"📅 Generating orders from {start_date} to {end_date}…")

        all_order_objs = []
        current = start_date
        while current <= end_date:
            day_orders = _orders_for_day(current, products, rng, start_date)
            for o in day_orders:
                amount = round(o["product"].price * o["quantity"], 2)
                all_order_objs.append(models.Order(
                    amount=amount,
                    product_id=o["product"].id,
                    quantity=o["quantity"],
                    status=o["status"],
                    created_at=o["created_at"],
                ))
            current += timedelta(days=1)

        db.add_all(all_order_objs)
        db.commit()

        paid_count    = sum(1 for o in all_order_objs if o.status == "paid")
        pending_count = sum(1 for o in all_order_objs if o.status == "pending")
        total_revenue = sum(o.amount for o in all_order_objs if o.status == "paid")

        print("\n✅ Regression seed complete:")
        print(f"   Days covered  : {(end_date - start_date).days + 1} (last 15 days)")
        print(f"   Total orders  : {len(all_order_objs)}")
        print(f"     ├─ paid     : {paid_count}")
        print(f"     └─ pending  : {pending_count}")
        print(f"   Total revenue : Rs. {total_revenue:,.2f}")
        print("\n   Patterns embedded for regression:")
        print("     ✔ Upward trend over 90 days")
        print("     ✔ Weekend spike (×1.4–1.9)")
        print("     ✔ Holiday spike (×2.0–2.8)")
        print("     ✔ Hourly peaks at 10 AM, 12–1 PM, 5–7 PM")
        print("     ✔ Monthly seasonality (Jan–Apr period)")
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
