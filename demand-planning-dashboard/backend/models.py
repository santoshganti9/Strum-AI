from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class SKU(Base):
    __tablename__ = "skus"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(String(50), unique=True, index=True, nullable=False)
    item_name = Column(String(255), nullable=False)
    category = Column(String(100))
    subcategory = Column(String(100))
    brand = Column(String(100))
    unit_cost = Column(Float)
    unit_price = Column(Float)
    supplier = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    sales_data = relationship("SalesData", back_populates="sku")
    forecasts = relationship("Forecast", back_populates="sku")


class SalesData(Base):
    __tablename__ = "sales_data"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(String(50), ForeignKey("skus.item_id"), nullable=False)
    week_ending = Column(DateTime, nullable=False)
    units_sold = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    region = Column(String(100))
    store_id = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    sku = relationship("SKU", back_populates="sales_data")


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(String(50), ForeignKey("skus.item_id"), nullable=False)
    forecast_date = Column(DateTime, nullable=False)
    forecast_period = Column(String(20), nullable=False)  # 'weekly', 'monthly'
    predicted_units = Column(Integer)
    predicted_revenue = Column(Float)
    confidence_score = Column(Float)  # 0-1 confidence level
    model_version = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    sku = relationship("SKU", back_populates="forecasts")
