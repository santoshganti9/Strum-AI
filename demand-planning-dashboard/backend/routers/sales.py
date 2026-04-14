from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
from database import get_db
from models import SalesData as SalesDataModel, SKU as SKUModel
from schemas import SalesData, SalesDataCreate

router = APIRouter()

@router.get("/", response_model=List[SalesData])
def get_sales_data(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    item_id: Optional[str] = None,
    region: Optional[str] = None,
    weeks_back: Optional[int] = Query(None, ge=1, le=52),
    db: Session = Depends(get_db)
):
    """Get sales data with optional filtering"""
    query = db.query(SalesDataModel)
    
    if item_id:
        query = query.filter(SalesDataModel.item_id == item_id)
    if region:
        query = query.filter(SalesDataModel.region == region)
    if weeks_back:
        cutoff_date = datetime.now() - timedelta(weeks=weeks_back)
        query = query.filter(SalesDataModel.week_ending >= cutoff_date)
    
    sales_data = query.order_by(desc(SalesDataModel.week_ending)).offset(skip).limit(limit).all()
    return sales_data

@router.get("/summary")
def get_sales_summary(
    weeks_back: int = Query(4, ge=1, le=52),
    db: Session = Depends(get_db)
):
    """Get sales summary for the dashboard"""
    cutoff_date = datetime.now() - timedelta(weeks=weeks_back)
    
    # Total sales metrics
    total_metrics = db.query(
        func.sum(SalesDataModel.units_sold).label('total_units'),
        func.sum(SalesDataModel.revenue).label('total_revenue'),
        func.count(func.distinct(SalesDataModel.item_id)).label('active_skus')
    ).filter(SalesDataModel.week_ending >= cutoff_date).first()
    
    # Top performing SKUs
    top_skus = db.query(
        SalesDataModel.item_id,
        func.sum(SalesDataModel.units_sold).label('total_units'),
        func.sum(SalesDataModel.revenue).label('total_revenue')
    ).filter(
        SalesDataModel.week_ending >= cutoff_date
    ).group_by(
        SalesDataModel.item_id
    ).order_by(
        desc(func.sum(SalesDataModel.revenue))
    ).limit(10).all()
    
    return {
        "period_weeks": weeks_back,
        "total_units_sold": total_metrics.total_units or 0,
        "total_revenue": total_metrics.total_revenue or 0.0,
        "active_skus": total_metrics.active_skus or 0,
        "top_performing_skus": [
            {
                "item_id": sku.item_id,
                "total_units": sku.total_units,
                "total_revenue": sku.total_revenue
            } for sku in top_skus
        ]
    }

@router.get("/{item_id}/weekly", response_model=List[SalesData])
def get_weekly_sales(
    item_id: str,
    weeks_back: int = Query(12, ge=1, le=52),
    db: Session = Depends(get_db)
):
    """Get weekly sales data for a specific SKU"""
    # Verify SKU exists
    sku = db.query(SKUModel).filter(SKUModel.item_id == item_id).first()
    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")
    
    cutoff_date = datetime.now() - timedelta(weeks=weeks_back)
    
    sales_data = db.query(SalesDataModel).filter(
        SalesDataModel.item_id == item_id,
        SalesDataModel.week_ending >= cutoff_date
    ).order_by(desc(SalesDataModel.week_ending)).all()
    
    return sales_data

@router.post("/", response_model=SalesData)
def create_sales_data(sales_data: SalesDataCreate, db: Session = Depends(get_db)):
    """Create new sales data entry"""
    # Verify SKU exists
    sku = db.query(SKUModel).filter(SKUModel.item_id == sales_data.item_id).first()
    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")
    
    db_sales = SalesDataModel(**sales_data.dict())
    db.add(db_sales)
    db.commit()
    db.refresh(db_sales)
    return db_sales

@router.post("/bulk")
def create_bulk_sales_data(sales_data_list: List[SalesDataCreate], db: Session = Depends(get_db)):
    """Create multiple sales data entries"""
    created_count = 0
    errors = []
    
    for sales_data in sales_data_list:
        try:
            # Verify SKU exists
            sku = db.query(SKUModel).filter(SKUModel.item_id == sales_data.item_id).first()
            if not sku:
                errors.append(f"SKU {sales_data.item_id} not found")
                continue
            
            db_sales = SalesDataModel(**sales_data.dict())
            db.add(db_sales)
            created_count += 1
        except Exception as e:
            errors.append(f"Error creating sales data for {sales_data.item_id}: {str(e)}")
    
    db.commit()
    
    return {
        "created_count": created_count,
        "total_submitted": len(sales_data_list),
        "errors": errors
    }
