from pydantic import BaseModel

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
    amount: float
    product_id: int
    product_name: str

class OrderOut(BaseModel):
    id: int
    amount: float
    product_id: int
    product_name: str
    status: str

    class Config:
        from_attributes = True

