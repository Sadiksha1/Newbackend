from datetime import datetime, date
from pydantic import BaseModel, Field

class ProductBase(BaseModel):
    name: str
    price: float
    category: str
    image: str
    quantity: int = 1


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


class CategoryBreakdown(BaseModel):
    category: str
    total_quantity: int
    total_revenue: float


class DailyRevenue(BaseModel):
    date: date
    revenue: float


class ForecastPoint(BaseModel):
    date: date
    revenue: float


class MonthlySales(BaseModel):
    month: str
    year: int
    total_revenue: float
    total_orders: int


class HourlySales(BaseModel):
    hour: int
    total_revenue: float
    total_orders: int


class ForecastPoint(BaseModel):
    date: date
    revenue: float


class AdvancedAnalytics(BaseModel):
    # Simple 1-D trend regression (backward compat)
    slope: float
    intercept: float
    # Multi-feature OLS regression
    r2: float
    sample_count: int
    multi_intercept: float
    coefficients: list[float]
    feature_names: list[str]
    # Rolling window KPIs
    last_7d_revenue: float
    last_30d_revenue: float
    last_7d_avg: float
    mom_growth_pct: float
    # Forecasts
    forecast_next_7: list[ForecastPoint]
    forecast_next_month: float
    # Breakdowns
    monthly_sales: list[MonthlySales]
    hourly_sales: list[HourlySales]


class AdminAnalytics(BaseModel):
    total_orders: int
    paid_orders: int
    pending_orders: int
    total_revenue: float
    average_ticket_size: float
    top_products: list[ProductSales]
    category_breakdown: list[CategoryBreakdown]
    revenue_by_date: list[DailyRevenue]

