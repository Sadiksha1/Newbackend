import os
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session

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

    return schemas.AdminAnalytics(
        total_orders=total_orders,
        paid_orders=paid_orders,
        pending_orders=pending_orders,
        total_revenue=float(revenue),
        average_ticket_size=average_ticket_size,
        top_products=top_products,
    )

