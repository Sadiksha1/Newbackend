from datetime import datetime
from pydantic import BaseModel, Field

class ProductBase(BaseModel):
    name: str
    price: float
    category: str
    image: str

class ProductCreate(ProductBase):
    pass

class ProductOut(ProductBase):
    id: int
    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    product_id: int = Field(..., gt=0, example=1)
    quantity: int = Field(1, gt=0, le=50, example=2)

class OrderOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    amount: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ProductSales(BaseModel):
    product_id: int
    product_name: str
    total_quantity: int
    total_revenue: float


class AdminAnalytics(BaseModel):
    total_orders: int
    paid_orders: int
    pending_orders: int
    total_revenue: float
    average_ticket_size: float
    top_products: list[ProductSales]

