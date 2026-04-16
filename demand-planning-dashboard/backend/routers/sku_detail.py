from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from datetime import timedelta, date
from typing import Optional, List
import json
import logging

from database import get_db
from models import SKU, SalesData, Forecast

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Anchor date: latest date in historical data (2025-04-20)
ANCHOR_DATE = date(2025, 4, 20)

router = APIRouter(tags=["sku-detail"])

@router.get("/sku/{item_id}")
def get_sku_details(
    item_id: str = Path(..., description="SKU Item ID"),
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific SKU
    """
    try:
        # Get SKU basic info
        sku = db.query(SKU).filter(SKU.item_id == item_id).first()
        if not sku:
            raise HTTPException(status_code=404, detail=f"SKU {item_id} not found")
        
        # Get sales summary
        sales_summary = db.query(
            func.sum(SalesData.units_sold).label('total_units_sold'),
            func.sum(SalesData.revenue).label('total_revenue'),
            func.count(SalesData.id).label('total_transactions'),
            func.min(SalesData.week_ending).label('first_sale_date'),
            func.max(SalesData.week_ending).label('last_sale_date')
        ).filter(SalesData.item_id == item_id).first()
        
        # Get forecast summary
        forecast_summary = db.query(
            func.sum(Forecast.predicted_units).label('total_predicted_units'),
            func.sum(Forecast.predicted_revenue).label('total_predicted_revenue'),
            func.avg(Forecast.confidence_score).label('avg_confidence'),
            func.count(Forecast.id).label('total_forecasts')
        ).filter(
            Forecast.item_id == item_id,
            Forecast.is_active == True
        ).first()
        
        return {
            "sku_info": {
                "item_id": sku.item_id,
                "item_name": sku.item_name,
                "category": sku.category,
                "brand": sku.brand,
                "unit_cost": float(sku.unit_cost) if sku.unit_cost else None,
                "supplier": sku.supplier,
                "created_at": sku.created_at.isoformat() if sku.created_at else None
            },
            "sales_summary": {
                "total_units_sold": int(sales_summary.total_units_sold or 0),
                "total_revenue": float(sales_summary.total_revenue or 0),
                "total_transactions": int(sales_summary.total_transactions or 0),
                "avg_price": float((sales_summary.total_revenue or 0) / (sales_summary.total_units_sold or 1)),
                "first_sale_date": sales_summary.first_sale_date.isoformat() if sales_summary.first_sale_date else None,
                "last_sale_date": sales_summary.last_sale_date.isoformat() if sales_summary.last_sale_date else None
            },
            "forecast_summary": {
                "total_predicted_units": int(forecast_summary.total_predicted_units or 0),
                "total_predicted_revenue": float(forecast_summary.total_predicted_revenue or 0),
                "avg_confidence": float(forecast_summary.avg_confidence or 0),
                "total_forecasts": int(forecast_summary.total_forecasts or 0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching SKU details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching SKU details: {str(e)}")

@router.get("/sku/{item_id}/timeline")
def get_sku_timeline(
    item_id: str = Path(..., description="SKU Item ID"),
    historical_weeks: int = Query(13, description="Number of historical weeks"),
    forecast_weeks: int = Query(39, description="Number of forecast weeks"),
    db: Session = Depends(get_db)
):
    """
    Get 52-week timeline for a specific SKU (13 weeks historical + 39 weeks forecast)
    """
    try:
        # Verify SKU exists
        sku = db.query(SKU).filter(SKU.item_id == item_id).first()
        if not sku:
            raise HTTPException(status_code=404, detail=f"SKU {item_id} not found")

        current_date = ANCHOR_DATE

        # Get historical data
        historical_start = current_date - timedelta(weeks=historical_weeks)
        historical_data = (
            db.query(
                SalesData.week_ending,
                func.sum(SalesData.units_sold).label("units_sold"),
                func.sum(SalesData.revenue).label("revenue"),
            )
            .filter(
                SalesData.item_id == item_id,
                SalesData.week_ending >= historical_start,
                SalesData.week_ending <= current_date,
            )
            .group_by(SalesData.week_ending)
            .order_by(SalesData.week_ending)
            .all()
        )

        # Get forecast data
        forecast_end = current_date + timedelta(weeks=forecast_weeks)
        forecast_data = (
            db.query(
                Forecast.forecast_date,
                func.sum(Forecast.predicted_units).label("predicted_units"),
                func.sum(Forecast.predicted_revenue).label("predicted_revenue"),
                func.avg(Forecast.confidence_score).label("confidence_score"),
            )
            .filter(
                Forecast.item_id == item_id,
                Forecast.forecast_date > current_date,
                Forecast.forecast_date <= forecast_end,
                Forecast.is_active == True,
            )
            .group_by(Forecast.forecast_date)
            .order_by(Forecast.forecast_date)
            .all()
        )

        # Format historical data
        timeline_data = []
        for record in historical_data:
            timeline_data.append(
                {
                    "week_ending": record.week_ending.isoformat(),
                    "units": int(record.units_sold or 0),
                    "revenue": float(record.revenue or 0),
                    "type": "historical",
                }
            )

        # Format forecast data
        for record in forecast_data:
            timeline_data.append(
                {
                    "week_ending": record.forecast_date.isoformat(),
                    "units": int(record.predicted_units or 0),
                    "revenue": float(record.predicted_revenue or 0),
                    "confidence_score": float(record.confidence_score or 0.5),
                    "type": "forecast",
                }
            )

        return {
            "item_id": item_id,
            "item_name": sku.item_name,
            "timeline_data": timeline_data,
            "period_summary": {
                "historical_weeks": historical_weeks,
                "forecast_weeks": forecast_weeks,
                "total_weeks": len(timeline_data),
                "historical_records": len(
                    [d for d in timeline_data if d["type"] == "historical"]
                ),
                "forecast_records": len(
                    [d for d in timeline_data if d["type"] == "forecast"]
                ),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching SKU timeline: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error fetching SKU timeline: {str(e)}"
        )


@router.get("/sku/{item_id}/previous-year")
def get_sku_previous_year(
    item_id: str = Path(..., description="SKU Item ID"),
    weeks: int = Query(52, description="Number of weeks to compare"),
    db: Session = Depends(get_db),
):
    """
    Get previous year same week actuals for comparison
    """
    try:
        # Verify SKU exists
        sku = db.query(SKU).filter(SKU.item_id == item_id).first()
        if not sku:
            raise HTTPException(status_code=404, detail=f"SKU {item_id} not found")

        current_date = ANCHOR_DATE

        # Get previous year data (52 weeks ago to current week last year)
        previous_year_start = current_date - timedelta(weeks=weeks + 52)
        previous_year_end = current_date - timedelta(weeks=52)

        previous_year_data = (
            db.query(
                SalesData.week_ending,
                func.sum(SalesData.units_sold).label("units_sold"),
                func.sum(SalesData.revenue).label("revenue"),
            )
            .filter(
                SalesData.item_id == item_id,
                SalesData.week_ending >= previous_year_start,
                SalesData.week_ending <= previous_year_end,
            )
            .group_by(SalesData.week_ending)
            .order_by(SalesData.week_ending)
            .all()
        )

        # Format data with adjusted dates (shift by 52 weeks to align with current year)
        comparison_data = []
        for record in previous_year_data:
            adjusted_date = record.week_ending + timedelta(weeks=52)
            comparison_data.append(
                {
                    "week_ending": adjusted_date.isoformat(),
                    "original_week_ending": record.week_ending.isoformat(),
                    "units": int(record.units_sold or 0),
                    "revenue": float(record.revenue or 0),
                    "type": "previous_year",
                }
            )

        return {
            "item_id": item_id,
            "item_name": sku.item_name,
            "previous_year_data": comparison_data,
            "comparison_period": {
                "previous_year_start": previous_year_start.isoformat(),
                "previous_year_end": previous_year_end.isoformat(),
                "total_records": len(comparison_data),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching previous year data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error fetching previous year data: {str(e)}"
        )


@router.get("/sku/{item_id}/demand-drivers")
def get_sku_demand_drivers(
    item_id: str = Path(..., description="SKU Item ID"),
    weeks: int = Query(52, description="Number of weeks of demand driver data"),
    db: Session = Depends(get_db),
):
    """
    Get demand drivers (avg_unit_price, cust_instock) for a specific SKU
    """
    try:
        # Verify SKU exists
        sku = db.query(SKU).filter(SKU.item_id == item_id).first()
        if not sku:
            raise HTTPException(status_code=404, detail=f"SKU {item_id} not found")

        current_date = ANCHOR_DATE
        
        # Get historical demand drivers
        historical_start = current_date - timedelta(weeks=weeks//2)  # Half historical
        historical_data = (
            db.query(
                SalesData.week_ending,
                func.sum(SalesData.units_sold).label("units_sold"),
                func.sum(SalesData.revenue).label("revenue"),
            )
            .filter(
                SalesData.item_id == item_id,
                SalesData.week_ending >= historical_start,
                SalesData.week_ending <= current_date,
            )
            .group_by(SalesData.week_ending)
            .order_by(SalesData.week_ending)
            .all()
        )
        
        # Format demand drivers data
        demand_drivers_data = []
        
        # Historical data
        for record in historical_data:
            demand_drivers_data.append(
                {
                    "week_ending": record.week_ending.isoformat(),
                    "units_sold": int(record.units_sold or 0),
                    "revenue": float(record.revenue or 0),
                    "type": "historical",
                }
            )

        return {
            "item_id": item_id,
            "item_name": sku.item_name,
            "demand_drivers_data": demand_drivers_data,
            "summary": {
                "total_weeks": len(demand_drivers_data),
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching demand drivers: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching demand drivers: {str(e)}")

@router.get("/search")
def search_skus(
    query: str = Query(..., description="Search query for SKU name or ID"),
    limit: int = Query(20, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Search for SKUs by name or ID
    """
    try:
        # Search in both item_id and item_name
        search_results = db.query(SKU).filter(
            (SKU.item_id.ilike(f"%{query}%")) |
            (SKU.item_name.ilike(f"%{query}%"))
        ).limit(limit).all()
        
        results = []
        for sku in search_results:
            # Get basic sales stats for each SKU
            sales_stats = db.query(
                func.sum(SalesData.units_sold).label('total_units'),
                func.sum(SalesData.revenue).label('total_revenue')
            ).filter(SalesData.item_id == sku.item_id).first()
            
            results.append({
                "item_id": sku.item_id,
                "item_name": sku.item_name,
                "category": sku.category,
                "brand": sku.brand,
                "total_units_sold": int(sales_stats.total_units or 0),
                "total_revenue": float(sales_stats.total_revenue or 0)
            })
        
        return {
            "query": query,
            "results": results,
            "total_found": len(results),
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error searching SKUs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error searching SKUs: {str(e)}")
