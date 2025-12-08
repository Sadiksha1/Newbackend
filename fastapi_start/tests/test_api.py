import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app import models
from app.database import Base
from app.routes import payment, product, admin as admin_route
from app.utils.security import hash_password, create_access_token


# Use test-specific admin credentials
TEST_ADMIN_USERNAME = "admin_test"
TEST_ADMIN_PASSWORD = "secret123"
os.environ["ADMIN_USERNAME"] = TEST_ADMIN_USERNAME
os.environ["ADMIN_PASSWORD"] = TEST_ADMIN_PASSWORD
os.environ["ADMIN_PASSWORD_SALT"] = "testsalt"


# In-memory SQLite for tests
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override dependencies to use the test database
app.dependency_overrides[payment.get_db] = override_get_db
app.dependency_overrides[product.get_db] = override_get_db
app.dependency_overrides[admin_route.get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_order_flow():
    # Seed product
    with TestingSessionLocal() as db:
        product_obj = models.Product(name="Soda", price=2.5, category="drink", image="soda.png")
        db.add(product_obj)
        db.commit()
        db.refresh(product_obj)
        product_id = product_obj.id

    # Create order
    resp = client.post("/payment/create-order", json={"product_id": product_id, "quantity": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert data["quantity"] == 2
    assert data["amount"] == pytest.approx(5.0)
    assert data["status"] == "pending"

    order_id = data["id"]

    # Mark as paid
    pay_resp = client.get(f"/payment/scan/{order_id}")
    assert pay_resp.status_code == 200

    # Verify status endpoint
    status_resp = client.get(f"/payment/status/{order_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "paid"


def test_admin_analytics_requires_auth():
    resp = client.get("/admin/analytics")
    assert resp.status_code == 401


def test_admin_analytics_returns_totals():
    # Seed product and orders
    with TestingSessionLocal() as db:
        product_obj = models.Product(name="Chips", price=3.0, category="snack", image="chips.png")
        db.add(product_obj)
        db.commit()
        db.refresh(product_obj)

        paid_order = models.Order(
            amount=6.0,
            product_id=product_obj.id,
            quantity=2,
            status="paid",
        )
        pending_order = models.Order(
            amount=3.0,
            product_id=product_obj.id,
            quantity=1,
            status="pending",
        )
        db.add_all([paid_order, pending_order])

        # Ensure admin exists with test credentials
        admin_user = models.Admin(
            username=TEST_ADMIN_USERNAME,
            password_hash=hash_password(TEST_ADMIN_PASSWORD),
        )
        db.add(admin_user)
        db.commit()

    # Get token
    token_resp = client.post(
        "/admin/login",
        data={"username": TEST_ADMIN_USERNAME, "password": TEST_ADMIN_PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert token_resp.status_code == 200
    access_token = token_resp.json()["access_token"]

    resp = client.get("/admin/analytics", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_orders"] == 2
    assert data["paid_orders"] == 1
    assert data["pending_orders"] == 1
    assert data["total_revenue"] == pytest.approx(6.0)
    assert data["average_ticket_size"] == pytest.approx(6.0)

    # Top products aggregation
    assert data["top_products"]
    top_product = data["top_products"][0]
    assert top_product["product_id"] == product_obj.id
    assert top_product["total_quantity"] == 2
    assert top_product["total_revenue"] == pytest.approx(6.0)

