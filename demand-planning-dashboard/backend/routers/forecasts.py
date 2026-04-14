from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
from database import get_db
from models import Forecast as ForecastModel, SKU as SKUModel
from schemas import Forecast, ForecastCreate, ForecastUpdate

router = APIRouter()

@router.get("/", response_model=List[Forecast])
def get_forecasts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    item_id: Optional[str] = None,
    is_active: bool = Query(True),
    forecast_period: Optional[str] = Query(None, regex="^(weekly|monthly)$"),
    db: Session = Depends(get_db)
):
    """Get forecasts with optional filtering"""
    query = db.query(ForecastModel)
    
    if item_id:
        query = query.filter(ForecastModel.item_id == item_id)
    if is_active is not None:
        query = query.filter(ForecastModel.is_active == is_active)
    if forecast_period:
        query = query.filter(ForecastModel.forecast_period == forecast_period)
    
    forecasts = query.order_by(desc(ForecastModel.forecast_date)).offset(skip).limit(limit).all()
    return forecasts

@router.get("/{item_id}/latest", response_model=Forecast)
def get_latest_forecast(item_id: str, db: Session = Depends(get_db)):
    """Get the latest active forecast for a specific SKU"""
    # Verify SKU exists
    sku = db.query(SKUModel).filter(SKUModel.item_id == item_id).first()
    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")
    
    forecast = db.query(ForecastModel).filter(
        ForecastModel.item_id == item_id,
        ForecastModel.is_active == True
    ).order_by(desc(ForecastModel.created_at)).first()
    
    if not forecast:
        raise HTTPException(status_code=404, detail="No active forecast found for this SKU")
    
    return forecast

@router.get("/{item_id}/history", response_model=List[Forecast])
def get_forecast_history(
    item_id: str,
    weeks_back: int = Query(12, ge=1, le=52),
    db: Session = Depends(get_db)
):
    """Get forecast history for a specific SKU"""
    # Verify SKU exists
    sku = db.query(SKUModel).filter(SKUModel.item_id == item_id).first()
    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")
    
    cutoff_date = datetime.now() - timedelta(weeks=weeks_back)
    
    forecasts = db.query(ForecastModel).filter(
        ForecastModel.item_id == item_id,
        ForecastModel.forecast_date >= cutoff_date
    ).order_by(desc(ForecastModel.forecast_date)).all()
    
    return forecasts

@router.post("/", response_model=Forecast)
def create_forecast(forecast: ForecastCreate, db: Session = Depends(get_db)):
    """Create a new forecast"""
    # Verify SKU exists
    sku = db.query(SKUModel).filter(SKUModel.item_id == forecast.item_id).first()
    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")
    
    db_forecast = ForecastModel(**forecast.dict())
    db.add(db_forecast)
    db.commit()
    db.refresh(db_forecast)
    return db_forecast

@router.put("/{forecast_id}", response_model=Forecast)
def update_forecast(forecast_id: int, forecast_update: ForecastUpdate, db: Session = Depends(get_db)):
    """Update an existing forecast"""
    db_forecast = db.query(ForecastModel).filter(ForecastModel.id == forecast_id).first()
    if not db_forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")
    
    update_data = forecast_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_forecast, field, value)
    
    db.commit()
    db.refresh(db_forecast)
    return db_forecast

@router.delete("/{forecast_id}")
def delete_forecast(forecast_id: int, db: Session = Depends(get_db)):
    """Delete a forecast (soft delete by setting is_active to False)"""
    db_forecast = db.query(ForecastModel).filter(ForecastModel.id == forecast_id).first()
    if not db_forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")
    
    db_forecast.is_active = False
    db.commit()
    return {"message": "Forecast deactivated successfully"}

@router.get("/summary")
def get_forecast_summary(db: Session = Depends(get_db)):
    """Get forecast summary for the dashboard"""
    # Count active forecasts
    active_forecasts = db.query(ForecastModel).filter(ForecastModel.is_active == True).count()
    
    # Get forecasts by period
    weekly_forecasts = db.query(ForecastModel).filter(
        ForecastModel.is_active == True,
        ForecastModel.forecast_period == "weekly"
    ).count()
    
    monthly_forecasts = db.query(ForecastModel).filter(
        ForecastModel.is_active == True,
        ForecastModel.forecast_period == "monthly"
    ).count()
    
    # Get average confidence score
    avg_confidence = db.query(
        db.func.avg(ForecastModel.confidence_score)
    ).filter(ForecastModel.is_active == True).scalar()
    
    return {
        "active_forecasts": active_forecasts,
        "weekly_forecasts": weekly_forecasts,
        "monthly_forecasts": monthly_forecasts,
        "average_confidence": round(avg_confidence or 0, 2)
    }
