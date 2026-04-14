from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# SKU Schemas
class SKUBase(BaseModel):
    item_id: str = Field(..., description="Unique item identifier")
    item_name: str = Field(..., description="Product name")
    category: Optional[str] = None
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    unit_cost: Optional[float] = None
    unit_price: Optional[float] = None
    supplier: Optional[str] = None

class SKUCreate(SKUBase):
    pass

class SKUUpdate(BaseModel):
    item_name: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    unit_cost: Optional[float] = None
    unit_price: Optional[float] = None
    supplier: Optional[str] = None

class SKU(SKUBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Sales Data Schemas
class SalesDataBase(BaseModel):
    item_id: str
    week_ending: datetime
    units_sold: int = 0
    revenue: float = 0.0
    region: Optional[str] = None
    store_id: Optional[str] = None

class SalesDataCreate(SalesDataBase):
    pass

class SalesData(SalesDataBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Forecast Schemas
class ForecastBase(BaseModel):
    item_id: str
    forecast_date: datetime
    forecast_period: str = Field(..., description="weekly or monthly")
    predicted_units: Optional[int] = None
    predicted_revenue: Optional[float] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    model_version: Optional[str] = None
    is_active: bool = True

class ForecastCreate(ForecastBase):
    pass

class ForecastUpdate(BaseModel):
    predicted_units: Optional[int] = None
    predicted_revenue: Optional[float] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    model_version: Optional[str] = None
    is_active: Optional[bool] = None

class Forecast(ForecastBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Response Schemas
class SKUWithSales(SKU):
    sales_data: List[SalesData] = []
    forecasts: List[Forecast] = []

class DashboardSummary(BaseModel):
    total_skus: int
    total_weekly_sales: int
    total_revenue: float
    active_forecasts: int
    top_performing_skus: List[SKU]
