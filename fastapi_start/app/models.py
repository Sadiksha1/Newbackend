from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    category = Column(String, nullable=True)
    image = Column(String, nullable=True)

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String, default="PENDING", nullable=False)  # PENDING, PAID, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product")
    payment = relationship("Payment", back_populates="order", uselist=False)

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, index=True)  # UUID string
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    amount = Column(Float, nullable=False)
    status = Column(String, default="PENDING", nullable=False)  # PENDING, PAID, FAILED
    qr_filename = Column(String, nullable=True)
    invoice_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="payment")
    product = relationship("Product")
