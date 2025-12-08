import os
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from datetime import date, timedelta, datetime
from calendar import month_name

from app.database import SessionLocal
from app import models, schemas
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
import math

router = APIRouter(prefix="/admin", tags=["Admin"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _admin_credentials_from_env() -> tuple[str, str]:
    return (
        os.getenv("ADMIN_USERNAME", "admin"),
        os.getenv("ADMIN_PASSWORD", "changeme123"),
    )


def ensure_default_admin(db: Session) -> None:
    """Create a default admin user if none exists."""
    admin_username, admin_password = _admin_credentials_from_env()

    admin = (
        db.query(models.Admin)
        .filter(models.Admin.username == admin_username)
        .first()
    )
    if admin:
        return

    new_admin = models.Admin(
        username=admin_username,
        password_hash=hash_password(admin_password),
    )
    db.add(new_admin)
    db.commit()


def authenticate_admin(db: Session, username: str, password: str) -> models.Admin | None:
    admin_username, _ = _admin_credentials_from_env()
    admin_user = (
        db.query(models.Admin)
        .filter(models.Admin.username == username)
        .first()
    )
    if (
        not admin_user
        or username != admin_username
        or not verify_password(password, admin_user.password_hash)
    ):
        return None
    return admin_user


def require_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.Admin:
    ensure_default_admin(db)
    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    admin_user = (
        db.query(models.Admin)
        .filter(models.Admin.username == username)
        .first()
    )
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return admin_user


def _compute_regression(points: List[tuple[int, float]]) -> tuple[float, float, float]:
    """
    Simple linear regression on (x, y) pairs.
    Returns slope, intercept, r^2. If insufficient data, returns zeros.
    """
    n = len(points)
    if n < 2:
        return 0.0, 0.0, 0.0

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n

    ss_xx = sum((x - mean_x) ** 2 for x in xs)
    if ss_xx == 0:
        return 0.0, mean_y, 0.0

    ss_xy = sum((x - mean_x) * (y - mean_y) for x, y in points)
    slope = ss_xy / ss_xx
    intercept = mean_y - slope * mean_x

    # r^2
    ss_total = sum((y - mean_y) ** 2 for y in ys)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in points)
    r2 = 0.0 if ss_total == 0 else 1 - (ss_res / ss_total)

    return slope, intercept, r2


def _sum_between(revenue_map: dict[date, float], start: date, end: date) -> float:
    return sum(v for d, v in revenue_map.items() if start <= d <= end)


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    ensure_default_admin(db)
    admin_user = authenticate_admin(db, form_data.username, form_data.password)
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(admin_user.username)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/analytics", response_model=schemas.AdminAnalytics)
def get_analytics(
    db: Session = Depends(get_db),
    _: models.Admin = Depends(require_admin),
):
    total_orders = db.query(func.count(models.Order.id)).scalar() or 0
    paid_orders = (
        db.query(func.count(models.Order.id))
        .filter(models.Order.status == "paid")
        .scalar()
        or 0
    )
    pending_orders = (
        db.query(func.count(models.Order.id))
        .filter(models.Order.status == "pending")
        .scalar()
        or 0
    )

    revenue = (
        db.query(func.coalesce(func.sum(models.Order.amount), 0))
        .filter(models.Order.status == "paid")
        .scalar()
        or 0.0
    )

    average_ticket_size = round(revenue / paid_orders, 2) if paid_orders else 0.0

    top_products_query = (
        db.query(
            models.Product.id.label("product_id"),
            models.Product.name.label("product_name"),
            func.coalesce(func.sum(models.Order.quantity), 0).label("total_quantity"),
            func.coalesce(func.sum(models.Order.amount), 0).label("total_revenue"),
        )
        .join(models.Order, models.Order.product_id == models.Product.id)
        .filter(models.Order.status == "paid")
        .group_by(models.Product.id, models.Product.name)
        .order_by(func.sum(models.Order.amount).desc())
        .limit(5)
        .all()
    )

    top_products = [
        schemas.ProductSales(
            product_id=product.product_id,
            product_name=product.product_name,
            total_quantity=int(product.total_quantity or 0),
            total_revenue=float(product.total_revenue or 0.0),
        )
        for product in top_products_query
    ]

    # Category breakdown (paid orders)
    category_rows = (
        db.query(
            models.Product.category.label("category"),
            func.coalesce(func.sum(models.Order.quantity), 0).label("total_quantity"),
            func.coalesce(func.sum(models.Order.amount), 0).label("total_revenue"),
        )
        .join(models.Order, models.Order.product_id == models.Product.id)
        .filter(models.Order.status == "paid")
        .group_by(models.Product.category)
        .all()
    )

    category_breakdown = [
        schemas.CategoryBreakdown(
            category=row.category or "Uncategorized",
            total_quantity=int(row.total_quantity or 0),
            total_revenue=float(row.total_revenue or 0.0),
        )
        for row in category_rows
    ]

    # Revenue by date (paid orders)
    revenue_rows = (
        db.query(
            func.date(models.Order.created_at).label("dt"),
            func.coalesce(func.sum(models.Order.amount), 0).label("rev"),
        )
        .filter(models.Order.status == "paid")
        .group_by(func.date(models.Order.created_at))
        .order_by(func.date(models.Order.created_at))
        .all()
    )

    revenue_by_date = [
        schemas.DailyRevenue(date=row.dt, revenue=float(row.rev or 0.0))
        for row in revenue_rows
    ]

    return schemas.AdminAnalytics(
        total_orders=total_orders,
        paid_orders=paid_orders,
        pending_orders=pending_orders,
        total_revenue=float(revenue),
        average_ticket_size=average_ticket_size,
        top_products=top_products,
        category_breakdown=category_breakdown,
        revenue_by_date=revenue_by_date,
    )


@router.get("/analytics/advanced", response_model=schemas.AdvancedAnalytics)
def get_advanced_analytics(
    db: Session = Depends(get_db),
    _: models.Admin = Depends(require_admin),
):
    # Use revenue_by_date for regression (trend over time)
    rows = (
        db.query(
            func.date(models.Order.created_at).label("dt"),
            func.coalesce(func.sum(models.Order.amount), 0).label("rev"),
        )
        .filter(models.Order.status == "paid")
        .group_by(func.date(models.Order.created_at))
        .order_by(func.date(models.Order.created_at))
        .all()
    )

    # Ensure dates are date objects, not strings
    revenue_map: dict[date, float] = {}
    for row in rows:
        dt = row.dt
        if isinstance(dt, str):
            dt = datetime.strptime(dt, "%Y-%m-%d").date()
        elif isinstance(dt, datetime):
            dt = dt.date()
        elif not isinstance(dt, date):
            continue
        revenue_map[dt] = float(row.rev or 0.0)
    
    points = [(idx, float(row.rev or 0.0)) for idx, row in enumerate(rows)]
    slope, intercept, r2 = _compute_regression(points)

    sample_count = len(points)
    today = date.today()
    last_date = max(revenue_map.keys()) if revenue_map else today

    last_7_start = last_date - timedelta(days=6)
    prev_7_start = last_date - timedelta(days=13)
    prev_7_end = last_date - timedelta(days=7)
    last_30_start = last_date - timedelta(days=29)

    last_7 = _sum_between(revenue_map, last_7_start, last_date)
    prev_7 = _sum_between(revenue_map, prev_7_start, prev_7_end)
    last_30 = _sum_between(revenue_map, last_30_start, last_date)

    mom_growth_pct = 0.0
    if prev_7 > 0:
        mom_growth_pct = ((last_7 - prev_7) / prev_7) * 100

    # Forecast next 7 days using regression line over indexes
    forecast = []
    base_idx = sample_count
    for i in range(1, 8):
        next_idx = base_idx + i - 1
        y_pred = slope * next_idx + intercept
        forecast.append(
            schemas.ForecastPoint(
                date=last_date + timedelta(days=i),
                revenue=max(0.0, round(y_pred, 2)),
            )
        )

    # Forecast next month (30 days ahead)
    forecast_next_month = 0.0
    if sample_count >= 2:
        days_ahead = 30
        next_month_idx = base_idx + days_ahead - 1
        daily_pred = slope * next_month_idx + intercept
        forecast_next_month = max(0.0, round(daily_pred * 30, 2))

    # Monthly sales breakdown
    monthly_rows = (
        db.query(
            func.extract("year", models.Order.created_at).label("yr"),
            func.extract("month", models.Order.created_at).label("mo"),
            func.coalesce(func.sum(models.Order.amount), 0).label("rev"),
            func.count(models.Order.id).label("cnt"),
        )
        .filter(models.Order.status == "paid")
        .group_by(
            func.extract("year", models.Order.created_at),
            func.extract("month", models.Order.created_at),
        )
        .order_by(
            func.extract("year", models.Order.created_at),
            func.extract("month", models.Order.created_at),
        )
        .all()
    )

    monthly_sales = [
        schemas.MonthlySales(
            month=month_name[int(row.mo)],
            year=int(row.yr),
            total_revenue=float(row.rev or 0.0),
            total_orders=int(row.cnt or 0),
        )
        for row in monthly_rows
    ]

    # Hourly sales breakdown
    hourly_rows = (
        db.query(
            func.extract("hour", models.Order.created_at).label("hr"),
            func.coalesce(func.sum(models.Order.amount), 0).label("rev"),
            func.count(models.Order.id).label("cnt"),
        )
        .filter(models.Order.status == "paid")
        .group_by(func.extract("hour", models.Order.created_at))
        .order_by(func.extract("hour", models.Order.created_at))
        .all()
    )

    hourly_sales = [
        schemas.HourlySales(
            hour=int(row.hr),
            total_revenue=float(row.rev or 0.0),
            total_orders=int(row.cnt or 0),
        )
        for row in hourly_rows
    ]

    return schemas.AdvancedAnalytics(
        slope=slope,
        intercept=intercept,
        r2=r2,
        sample_count=sample_count,
        last_7d_revenue=round(last_7, 2),
        last_30d_revenue=round(last_30, 2),
        last_7d_avg=round(last_7 / 7, 2) if last_7 else 0.0,
        mom_growth_pct=round(mom_growth_pct, 2),
        forecast_next_7=forecast,
        forecast_next_month=forecast_next_month,
        monthly_sales=monthly_sales,
        hourly_sales=hourly_sales,
    )

