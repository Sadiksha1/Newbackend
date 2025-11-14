from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    name: str
    price: float
    category: Optional[str] = None
    image: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductOut(ProductBase):
    id: int
    model_config = {"from_attributes": True}

class OrderCreate(BaseModel):
    product_id: int
    quantity: int = 1

class OrderOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    total_amount: float
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}

class PaymentCreate(BaseModel):
    amount: float
    product_id: Optional[int] = None
    order_id: Optional[int] = None

class PaymentOut(BaseModel):
    id: str
    order_id: Optional[int]
    product_id: Optional[int]
    amount: float
    status: str
    qr_code_url: Optional[str] = None
    invoice_number: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class PaymentStatusOut(BaseModel):
    payment_id: str
    status: str
