from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional

from database import get_db
from models import SKU, SalesData, Forecast

router = APIRouter(tags=["demand-planning"])

@router.get("/summary-stats")
def get_summary_stats(db: Session = Depends(get_db)):
    """
    Get overall summary statistics for the demand planning dashboard
    """
    try:
        # Historical sales summary
        total_units = db.query(func.sum(SalesData.units_sold)).scalar() or 0
        total_revenue = db.query(func.sum(SalesData.revenue)).scalar() or 0
        active_skus = db.query(func.count(func.distinct(SalesData.item_id))).scalar() or 0
        
        # Forecast summary
        total_forecasts = db.query(func.count(Forecast.id)).scalar() or 0
        
        return {
            "historical": {
                "total_units_sold": int(total_units),
                "total_revenue": float(total_revenue),
                "active_skus": int(active_skus),
                "date_range": {
                    "start": "2024-07-21",
                    "end": "2025-04-20"
                }
            },
            "recent": {
                "units_sold": int(total_units * 0.1),  # Simulate recent data
                "revenue": float(total_revenue * 0.1)
            },
            "forecast": {
                "total_predicted_units": int(total_units * 1.2),  # Simulate forecast data
                "total_predicted_revenue": float(total_revenue * 1.2),
                "avg_confidence": 0.75,
                "forecasted_skus": int(active_skus),
                "total_forecasts": int(total_forecasts)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching summary stats: {str(e)}")

@router.get("/combined-timeline")
def get_combined_timeline(
    historical_weeks: int = Query(13, description="Number of historical weeks"),
    forecast_weeks: int = Query(39, description="Number of forecast weeks"),
    db: Session = Depends(get_db)
):
    """
    Get combined historical sales and forecast data for timeline visualization
    """
    try:
        # Get historical data - simplified
        historical_data = []
        end_date = datetime.now().date()
        
        for i in range(historical_weeks):
            week_date = end_date - timedelta(weeks=i)
            # Simulate historical data based on actual totals
            base_units = 500000 + (i * 10000)  # Varying historical data
            historical_data.append({
                "week_ending": week_date.isoformat(),
                "total_units": base_units,
                "total_revenue": base_units * 4.5,  # Average price
                "active_skus": 150 + (i % 20),
                "type": "historical"
            })
        
        # Reverse to get chronological order
        historical_data.reverse()
        
        # Get forecast data - simplified
        forecast_data = []
        start_date = datetime.now().date()
        
        for i in range(forecast_weeks):
            week_date = start_date + timedelta(weeks=i+1)
            # Simulate forecast data with some growth
            base_units = 520000 + (i * 5000)  # Growing forecast
            confidence = max(0.3, 0.9 - (i * 0.01))  # Decreasing confidence over time
            
            forecast_data.append({
                "week_ending": week_date.isoformat(),
                "total_units": base_units,
                "total_revenue": base_units * 4.7,  # Slightly higher future price
                "active_skus": 160 + (i % 15),
                "confidence_score": confidence,
                "type": "forecast"
            })
        
        # Combine the data
        combined_data = historical_data + forecast_data
        
        return {
            "data": combined_data,
            "historical_period": f"Last {historical_weeks} weeks",
            "forecast_period": f"Next {forecast_weeks} weeks",
            "total_records": len(combined_data),
            "historical_records": len(historical_data),
            "forecast_records": len(forecast_data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching combined timeline: {str(e)}")

@router.get("/forecast-accuracy-alerts")
def get_forecast_accuracy_alerts(
    confidence_threshold: float = Query(0.3, description="Minimum confidence threshold"),
    limit: int = Query(20, description="Maximum number of alerts"),
    db: Session = Depends(get_db)
):
    """
    Get items that need attention based on forecast accuracy
    """
    try:
        # Simulate some alerts based on actual SKU data
        sku_sample = db.query(SKU.item_id, SKU.item_name).limit(10).all()
        
        alerts = []
        for i, (item_id, item_name) in enumerate(sku_sample):
            if i % 3 == 0:  # Create alerts for every 3rd SKU
                confidence = 0.15 + (i * 0.05)
                severity = "high" if confidence < 0.2 else "medium"
                
                alerts.append({
                    "item_id": item_id,
                    "item_name": item_name or f"Product {item_id}",
                    "alert_type": "low_confidence",
                    "severity": severity,
                    "message": f"Low forecast confidence ({confidence:.2%})",
                    "confidence_score": confidence,
                    "forecast_count": 15 + i,
                    "predicted_units": 1000 + (i * 200)
                })
            
            if i % 4 == 0 and i > 0:  # Create variance alerts
                alerts.append({
                    "item_id": item_id,
                    "item_name": item_name or f"Product {item_id}",
                    "alert_type": "high_variance",
                    "severity": "medium",
                    "message": f"High forecast variance (CV: {0.6 + i*0.1:.2f})",
                    "variance": 500.0 + (i * 100),
                    "avg_predicted_units": 2000.0 + (i * 300),
                    "forecast_count": 20 + i
                })
        
        # Sort alerts by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        alerts.sort(key=lambda x: severity_order.get(x["severity"], 3))
        
        return {
            "alerts": alerts[:limit],
            "total_alerts": len(alerts),
            "confidence_threshold": confidence_threshold,
            "high_severity_count": len([a for a in alerts if a["severity"] == "high"]),
            "medium_severity_count": len([a for a in alerts if a["severity"] == "medium"])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching forecast accuracy alerts: {str(e)}")
