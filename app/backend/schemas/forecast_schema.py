from pydantic import BaseModel, Field
from typing import Optional, List


# ─── Forecast ────────────────────────────────────────────────────────────────

class ForecastInput(BaseModel):
    category_name: str
    market: str
    periods: int = Field(30, ge=1, le=365)
    order_month: Optional[int] = Field(None, ge=1, le=12)
    order_year: Optional[int] = Field(None, ge=2000, le=2100)


class ForecastPoint(BaseModel):
    date: str
    predicted_sales: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None


class ForecastResponse(BaseModel):
    category_name: str
    market: str
    periods: int
    forecast: List[ForecastPoint]
    model_version: str = "0.1.0"


# ─── Supplier ─────────────────────────────────────────────────────────────────

class SupplierInput(BaseModel):
    department_name: str
    category_name: str
    order_item_quantity: int = Field(..., ge=1)
    order_item_product_price: float = Field(..., ge=0)
    market: str
    shipping_mode: str
    order_region: str


class SupplierScore(BaseModel):
    supplier_id: Optional[str] = None
    department_name: str
    score: float = Field(..., ge=0.0, le=1.0)
    predicted_delay_risk: float
    recommendation: str


class SupplierResponse(BaseModel):
    recommendations: List[SupplierScore]
    model_version: str = "0.1.0"