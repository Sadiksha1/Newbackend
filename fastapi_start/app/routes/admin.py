import os
import numpy as np
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

router = APIRouter(prefix="/admin", tags=["Admin"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login")

# ---------------------------------------------------------------------------
# Nepali public holidays (Gregorian equivalents)
# Dashain/Tihar shift yearly — append new entries each year as needed.
# ---------------------------------------------------------------------------
NEPAL_HOLIDAYS: set[date] = {
    # --- 2024 ---
    date(2024, 1, 11),   # Prithvi Jayanti
    date(2024, 1, 15),   # Maghe Sankranti
    date(2024, 2, 19),   # National Democracy Day
    date(2024, 3, 8),    # International Women's Day
    date(2024, 3, 25),   # Holi
    date(2024, 4, 14),   # Nepali New Year (Baisakh 1)
    date(2024, 5, 1),    # Labour Day
    date(2024, 5, 23),   # Buddha Jayanti
    date(2024, 8, 19),   # Janai Purnima
    date(2024, 8, 26),   # Krishna Janmashtami
    date(2024, 9, 7),    # Indra Jatra
    date(2024, 10, 2),   # Ghatasthapana (Dashain starts)
    date(2024, 10, 10),  # Fulpati
    date(2024, 10, 11),  # Maha Ashtami
    date(2024, 10, 12),  # Maha Nawami
    date(2024, 10, 13),  # Vijaya Dashami
    date(2024, 10, 29),  # Laxmi Puja (Tihar)
    date(2024, 10, 31),  # Mha Puja
    date(2024, 11, 1),   # Bhai Tika
    date(2024, 12, 25),  # Christmas
    date(2024, 12, 28),  # Udhauli Parwa

    # --- 2025 ---
    date(2025, 1, 11),   # Prithvi Jayanti
    date(2025, 1, 14),   # Maghe Sankranti
    date(2025, 2, 19),   # National Democracy Day
    date(2025, 3, 14),   # Holi
    date(2025, 4, 14),   # Nepali New Year
    date(2025, 5, 1),    # Labour Day
    date(2025, 5, 12),   # Buddha Jayanti
    date(2025, 8, 9),    # Janai Purnima
    date(2025, 8, 16),   # Krishna Janmashtami
    date(2025, 9, 22),   # Ghatasthapana (Dashain starts)
    date(2025, 9, 30),   # Fulpati
    date(2025, 10, 1),   # Maha Ashtami
    date(2025, 10, 2),   # Maha Nawami
    date(2025, 10, 3),   # Vijaya Dashami
    date(2025, 10, 18),  # Laxmi Puja (Tihar)
    date(2025, 10, 20),  # Mha Puja
    date(2025, 10, 21),  # Bhai Tika
    date(2025, 12, 25),  # Christmas
    date(2025, 12, 28),  # Udhauli Parwa

    # --- 2026 ---
    date(2026, 1, 11),   # Prithvi Jayanti
    date(2026, 1, 15),   # Maghe Sankranti
    date(2026, 2, 19),   # National Democracy Day
    date(2026, 3, 3),    # Holi
    date(2026, 4, 14),   # Nepali New Year
    date(2026, 5, 1),    # Labour Day
    date(2026, 5, 31),   # Buddha Jayanti
    date(2026, 7, 29),   # Janai Purnima
    date(2026, 8, 5),    # Krishna Janmashtami
    date(2026, 10, 11),  # Ghatasthapana (Dashain starts)
    date(2026, 10, 19),  # Fulpati
    date(2026, 10, 20),  # Maha Ashtami
    date(2026, 10, 21),  # Maha Nawami
    date(2026, 10, 22),  # Vijaya Dashami
    date(2026, 11, 7),   # Laxmi Puja (Tihar)
    date(2026, 11, 9),   # Mha Puja
    date(2026, 11, 10),  # Bhai Tika
    date(2026, 12, 25),  # Christmas
}


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
    admin_username, admin_password = _admin_credentials_from_env()
    admin = db.query(models.Admin).filter(models.Admin.username == admin_username).first()
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
    admin_user = db.query(models.Admin).filter(models.Admin.username == username).first()
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
    admin_user = db.query(models.Admin).filter(models.Admin.username == username).first()
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return admin_user


# ---------------------------------------------------------------------------
# Simple linear regression — kept for backwards-compat slope/intercept fields
# ---------------------------------------------------------------------------
def _compute_regression(points: List[tuple[int, float]]) -> tuple[float, float, float]:
    """Simple linear regression on (index, revenue) pairs. Returns slope, intercept, r²."""
    n = len(points)
    if n < 2:
        return 0.0, 0.0, 0.0

    X = np.array([[1.0, float(x)] for x, _ in points])
    y = np.array([float(rev) for _, rev in points])

    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    intercept, slope = float(beta[0]), float(beta[1])

    y_pred   = X @ beta
    ss_res   = np.sum((y - y_pred) ** 2)
    ss_total = np.sum((y - y.mean()) ** 2)
    r2       = 0.0 if ss_total == 0 else float(1 - ss_res / ss_total)

    return slope, intercept, r2


# ---------------------------------------------------------------------------
# Multiple linear regression via numpy OLS
# ---------------------------------------------------------------------------
def _compute_regression_multi(
    points: List[tuple[List[float], float]]
) -> tuple[List[float], float, float]:
    """
    Multiple linear regression using numpy OLS: β = (XᵀX)⁻¹ Xᵀy
    Each point: ([feature0, feature1, ...], revenue)
    Returns (coefficients, intercept, r²)
    """
    if len(points) < 2:
        return [], 0.0, 0.0

    # X shape: (n, k+1) — first col is bias/intercept term
    X = np.array([[1.0] + features for features, _ in points], dtype=float)
    y = np.array([rev for _, rev in points], dtype=float)

    # lstsq is more numerically stable than manual matrix inversion
    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)

    intercept    = float(beta[0])
    coefficients = beta[1:].tolist()

    y_pred   = X @ beta
    ss_res   = np.sum((y - y_pred) ** 2)
    ss_total = np.sum((y - y.mean()) ** 2)
    r2       = 0.0 if ss_total == 0 else float(1 - ss_res / ss_total)

    return coefficients, intercept, r2


def _sum_between(revenue_map: dict[date, float], start: date, end: date) -> float:
    return sum(v for d, v in revenue_map.items() if start <= d <= end)


# ---------------------------------------------------------------------------
# Feature extraction — add/remove features here, everything else auto-adapts
# ---------------------------------------------------------------------------
def _extract_features(dt: date, num_orders: int = 0, total_qty: int = 0) -> List[float]:
    """
    Feature vector for one day — calendar/time signals only.

    num_orders and total_qty are accepted but intentionally excluded:
    both are highly correlated with revenue by definition (revenue = price x qty),
    which inflates R² without improving genuine out-of-sample forecasts.
    Using only knowable-in-advance features keeps forecasting honest.

    Index  Name            Description
    -----  --------------  -----------------------------------------------
      0    day_index       overall time trend (filled in by caller)
      1    day_of_week     0=Mon … 6=Sun
      2    is_weekend      1 if Sat/Sun, else 0
      3    month           1–12, captures seasonality
      4    is_holiday      1 if Nepali public holiday, else 0
    """
    return [
        0.0,                                         # 0: day_index (filled by caller)
        float(dt.weekday()),                         # 1: day_of_week
        1.0 if dt.weekday() >= 5 else 0.0,          # 2: is_weekend
        float(dt.month),                             # 3: month
        1.0 if dt in NEPAL_HOLIDAYS else 0.0,        # 4: is_holiday
    ]


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
        .scalar() or 0
    )
    pending_orders = (
        db.query(func.count(models.Order.id))
        .filter(models.Order.status == "pending")
        .scalar() or 0
    )
    revenue = (
        db.query(func.coalesce(func.sum(models.Order.amount), 0))
        .filter(models.Order.status == "paid")
        .scalar() or 0.0
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
            product_id=p.product_id,
            product_name=p.product_name,
            total_quantity=int(p.total_quantity or 0),
            total_revenue=float(p.total_revenue or 0.0),
        )
        for p in top_products_query
    ]

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
    rows = (
        db.query(
            func.date(models.Order.created_at).label("dt"),
            func.coalesce(func.sum(models.Order.amount), 0).label("rev"),
            func.count(models.Order.id).label("num_orders"),
            func.coalesce(func.sum(models.Order.quantity), 0).label("total_qty"),
        )
        .filter(models.Order.status == "paid")
        .group_by(func.date(models.Order.created_at))
        .order_by(func.date(models.Order.created_at))
        .all()
    )

    # Build revenue_map for window sum calculations
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

    # Build multi-feature points
    multi_points: List[tuple[List[float], float]] = []
    for idx, row in enumerate(rows):
        dt = row.dt
        if isinstance(dt, str):
            dt = datetime.strptime(dt, "%Y-%m-%d").date()
        elif isinstance(dt, datetime):
            dt = dt.date()

        features    = _extract_features(dt)
        features[0] = float(idx)  # fill day_index
        multi_points.append((features, float(row.rev or 0.0)))

    # Multi-feature regression (numpy)
    coefficients, intercept, r2 = _compute_regression_multi(multi_points)

    # Simple regression kept for backwards-compat slope/intercept schema fields
    simple_points = [(idx, rev) for idx, (_, rev) in enumerate(multi_points)]
    slope, simple_intercept, _ = _compute_regression(simple_points)

    sample_count = len(multi_points)
    today        = date.today()
    last_date    = max(revenue_map.keys()) if revenue_map else today

    # Window calculations
    last_7_start  = last_date - timedelta(days=6)
    prev_7_start  = last_date - timedelta(days=13)
    prev_7_end    = last_date - timedelta(days=7)
    last_30_start = last_date - timedelta(days=29)

    last_7  = _sum_between(revenue_map, last_7_start, last_date)
    prev_7  = _sum_between(revenue_map, prev_7_start, prev_7_end)
    last_30 = _sum_between(revenue_map, last_30_start, last_date)

    mom_growth_pct = 0.0
    if prev_7 > 0:
        mom_growth_pct = ((last_7 - prev_7) / prev_7) * 100

    # Forecast next 7 days — only calendar features needed (all knowable in advance)
    forecast = []
    for i in range(1, 8):
        future_date     = last_date + timedelta(days=i)
        future_features = _extract_features(future_date)
        future_features[0] = float(sample_count + i - 1)
        y_pred = intercept + sum(c * f for c, f in zip(coefficients, future_features))
        forecast.append(
            schemas.ForecastPoint(
                date=future_date,
                revenue=max(0.0, round(y_pred, 2)),
            )
        )

    # Forecast next 30 days (sum of daily predictions)
    forecast_next_month = 0.0
    if sample_count >= 2:
        for i in range(1, 31):
            future_date     = last_date + timedelta(days=i)
            future_features = _extract_features(future_date)
            future_features[0] = float(sample_count + i - 1)
            y_pred = intercept + sum(c * f for c, f in zip(coefficients, future_features))
            forecast_next_month += max(0.0, y_pred)
        forecast_next_month = round(forecast_next_month, 2)

    # Monthly breakdown
    monthly_rows = (
        db.query(
            func.extract("year",  models.Order.created_at).label("yr"),
            func.extract("month", models.Order.created_at).label("mo"),
            func.coalesce(func.sum(models.Order.amount), 0).label("rev"),
            func.count(models.Order.id).label("cnt"),
        )
        .filter(models.Order.status == "paid")
        .group_by(
            func.extract("year",  models.Order.created_at),
            func.extract("month", models.Order.created_at),
        )
        .order_by(
            func.extract("year",  models.Order.created_at),
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

    # Hourly breakdown
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

    feature_names = [
        "day_index",
        "day_of_week",
        "is_weekend",
        "month",
        "is_holiday",
    ]

    return schemas.AdvancedAnalytics(
        slope=slope,
        intercept=simple_intercept,
        r2=r2,
        sample_count=sample_count,
        multi_intercept=round(intercept, 4),
        coefficients=[round(c, 4) for c in coefficients],
        feature_names=feature_names,
        last_7d_revenue=round(last_7, 2),
        last_30d_revenue=round(last_30, 2),
        last_7d_avg=round(last_7 / 7, 2) if last_7 else 0.0,
        mom_growth_pct=round(mom_growth_pct, 2),
        forecast_next_7=forecast,
        forecast_next_month=forecast_next_month,
        monthly_sales=monthly_sales,
        hourly_sales=hourly_sales,
    )