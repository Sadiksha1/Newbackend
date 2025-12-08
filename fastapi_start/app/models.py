from sqlalchemy import Column, Integer, String, Float, ForeignKey
from .database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Float)
    category = Column(String)
    image = Column(String)

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float)
    product_id = Column(Integer, ForeignKey("products.id"))
    product_name = Column(String)
    status = Column(String, default="pending")