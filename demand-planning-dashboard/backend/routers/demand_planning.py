from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import timedelta, date
from typing import List, Optional
import pandas as pd
import logging

from database import get_db
from models import SKU, SalesData, Forecast

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Anchor date: latest date in historical data (2025-04-20)
ANCHOR_DATE = date(2025, 4, 20)

router = APIRouter(tags=["demand-planning"])


@router.get("/historical-sales")
def get_historical_sales(
    weeks: int = Query(13, description="Number of weeks of historical data"),
    item_id: Optional[str] = Query(None, description="Filter by specific SKU"),
    db: Session = Depends(get_db),
):
    """
    Get aggregated historical sales data for the last N weeks
    """
    try:
        # Calculate the date range
        end_date = ANCHOR_DATE
        start_date = end_date - timedelta(weeks=weeks)

        # Base query
        query = db.query(
            SalesData.week_ending,
            func.sum(SalesData.units_sold).label("total_units"),
            func.sum(SalesData.revenue).label("total_revenue"),
            func.count(func.distinct(SalesData.item_id)).label("active_skus"),
        ).filter(SalesData.week_ending >= start_date, SalesData.week_ending <= end_date)

        # Filter by item_id if provided
        if item_id:
            query = query.filter(SalesData.item_id == item_id)

        # Group by week and order by date
        results = (
            query.group_by(SalesData.week_ending).order_by(SalesData.week_ending).all()
        )

        # Format the response
        historical_data = []
        for result in results:
            historical_data.append(
                {
                    "week_ending": result.week_ending.isoformat(),
                    "total_units": result.total_units or 0,
                    "total_revenue": float(result.total_revenue or 0),
                    "active_skus": result.active_skus or 0,
                    "type": "historical",
                }
            )

        return {
            "data": historical_data,
            "period": f"Last {weeks} weeks",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_records": len(historical_data),
        }

    except Exception as e:
        logger.error(f"Error fetching historical sales: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error fetching historical sales: {str(e)}"
        )


@router.get("/forecast-data")
def get_forecast_data(
    weeks: int = Query(39, description="Number of weeks of forecast data"),
    item_id: Optional[str] = Query(None, description="Filter by specific SKU"),
    db: Session = Depends(get_db),
):
    """
    Get aggregated forecast data for the next N weeks
    """
    try:
        # Calculate the date range for forecasts
        start_date = ANCHOR_DATE
        end_date = start_date + timedelta(weeks=weeks)

        # Base query for active forecasts
        query = db.query(
            Forecast.forecast_date,
            func.sum(Forecast.predicted_units).label("total_predicted_units"),
            func.sum(Forecast.predicted_revenue).label("total_predicted_revenue"),
            func.avg(Forecast.confidence_score).label("avg_confidence"),
            func.count(func.distinct(Forecast.item_id)).label("forecasted_skus"),
        ).filter(
            Forecast.forecast_date >= start_date,
            Forecast.forecast_date <= end_date,
            Forecast.is_active == True,
        )

        # Filter by item_id if provided
        if item_id:
            query = query.filter(Forecast.item_id == item_id)

        # Group by forecast date and order by date
        results = (
            query.group_by(Forecast.forecast_date)
            .order_by(Forecast.forecast_date)
            .all()
        )

        # Format the response
        forecast_data = []
        for result in results:
            forecast_data.append(
                {
                    "week_ending": result.forecast_date.isoformat(),
                    "total_units": result.total_predicted_units or 0,
                    "total_revenue": float(result.total_predicted_revenue or 0),
                    "active_skus": result.forecasted_skus or 0,
                    "confidence_score": float(result.avg_confidence or 0.5),
                    "type": "forecast",
                }
            )

        return {
            "data": forecast_data,
            "period": f"Next {weeks} weeks",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_records": len(forecast_data),
        }

    except Exception as e:
        logger.error(f"Error fetching forecast data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error fetching forecast data: {str(e)}"
        )


@router.get("/combined-timeline")
def get_combined_timeline(
    historical_weeks: int = Query(13, description="Number of historical weeks"),
    forecast_weeks: int = Query(39, description="Number of forecast weeks"),
    item_id: Optional[str] = Query(None, description="Filter by specific SKU"),
    db: Session = Depends(get_db),
):
    """
    Get combined historical sales and forecast data for timeline visualization
    """
    try:
        # Get historical data
        historical_response = get_historical_sales(historical_weeks, item_id, db)
        historical_data = historical_response["data"]

        # Get forecast data
        forecast_response = get_forecast_data(forecast_weeks, item_id, db)
        forecast_data = forecast_response["data"]

        # Combine the data
        combined_data = historical_data + forecast_data

        # Sort by date
        combined_data.sort(key=lambda x: x["week_ending"])

        return {
            "data": combined_data,
            "historical_period": f"Last {historical_weeks} weeks",
            "forecast_period": f"Next {forecast_weeks} weeks",
            "total_records": len(combined_data),
            "historical_records": len(historical_data),
            "forecast_records": len(forecast_data),
        }

    except Exception as e:
        logger.error(f"Error fetching combined timeline: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error fetching combined timeline: {str(e)}"
        )


@router.get("/forecast-accuracy-alerts")
def get_forecast_accuracy_alerts(
    confidence_threshold: float = Query(
        0.3, description="Minimum confidence threshold"
    ),
    limit: int = Query(20, description="Maximum number of alerts"),
    db: Session = Depends(get_db),
):
    """
    Get items that need attention based on forecast accuracy
    """
    try:
        # Find SKUs with low confidence forecasts
        low_confidence_query = (
            db.query(
                Forecast.item_id,
                SKU.item_name,
                func.avg(Forecast.confidence_score).label("avg_confidence"),
                func.count(Forecast.id).label("forecast_count"),
                func.sum(Forecast.predicted_units).label("total_predicted_units"),
            )
            .join(SKU, Forecast.item_id == SKU.item_id)
            .filter(
                Forecast.is_active == True,
                Forecast.forecast_date >= ANCHOR_DATE,
            )
            .group_by(Forecast.item_id, SKU.item_name)
            .having(func.avg(Forecast.confidence_score) < confidence_threshold)
            .order_by(func.avg(Forecast.confidence_score).asc())
            .limit(limit)
        )

        low_confidence_results = low_confidence_query.all()

        # Find SKUs with high variance in forecasts
        variance_query = (
            db.query(
                Forecast.item_id,
                SKU.item_name,
                func.stddev(Forecast.predicted_units).label("units_variance"),
                func.avg(Forecast.predicted_units).label("avg_predicted_units"),
                func.count(Forecast.id).label("forecast_count"),
            )
            .join(SKU, Forecast.item_id == SKU.item_id)
            .filter(
                Forecast.is_active == True,
                Forecast.forecast_date >= ANCHOR_DATE,
            )
            .group_by(Forecast.item_id, SKU.item_name)
            .having(
                func.count(Forecast.id)
                > 5  # Only consider SKUs with multiple forecasts
            )
            .order_by(func.stddev(Forecast.predicted_units).desc())
            .limit(limit)
        )

        variance_results = variance_query.all()

        # Format alerts
        alerts = []

        # Low confidence alerts
        for result in low_confidence_results:
            alerts.append(
                {
                    "item_id": result.item_id,
                    "item_name": result.item_name,
                    "alert_type": "low_confidence",
                    "severity": "high" if result.avg_confidence < 0.2 else "medium",
                    "message": f"Low forecast confidence ({result.avg_confidence:.2%})",
                    "confidence_score": float(result.avg_confidence),
                    "forecast_count": result.forecast_count,
                    "predicted_units": result.total_predicted_units or 0,
                }
            )

        # High variance alerts
        for result in variance_results:
            if result.units_variance and result.avg_predicted_units:
                coefficient_of_variation = (
                    result.units_variance / result.avg_predicted_units
                )
                if coefficient_of_variation > 0.5:  # High variance threshold
                    alerts.append(
                        {
                            "item_id": result.item_id,
                            "item_name": result.item_name,
                            "alert_type": "high_variance",
                            "severity": "medium",
                            "message": f"High forecast variance (CV: {coefficient_of_variation:.2f})",
                            "variance": float(result.units_variance),
                            "avg_predicted_units": float(result.avg_predicted_units),
                            "forecast_count": result.forecast_count,
                        }
                    )

        # Sort alerts by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        alerts.sort(key=lambda x: severity_order.get(x["severity"], 3))

        return {
            "alerts": alerts[:limit],
            "total_alerts": len(alerts),
            "confidence_threshold": confidence_threshold,
            "high_severity_count": len([a for a in alerts if a["severity"] == "high"]),
            "medium_severity_count": len(
                [a for a in alerts if a["severity"] == "medium"]
            ),
        }

    except Exception as e:
        logger.error(
            f"Error fetching forecast accuracy alerts: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Error fetching forecast accuracy alerts: {str(e)}"
        )


@router.get("/summary-stats")
def get_summary_stats(db: Session = Depends(get_db)):
    """
    Get overall summary statistics for the demand planning dashboard
    """
    try:
        # Get current date for calculations
        current_date = ANCHOR_DATE
        last_week = current_date - timedelta(days=7)

        # Historical sales summary
        historical_stats = db.query(
            func.sum(SalesData.units_sold).label("total_units_sold"),
            func.sum(SalesData.revenue).label("total_revenue"),
            func.count(func.distinct(SalesData.item_id)).label("active_skus"),
            func.min(SalesData.week_ending).label("earliest_date"),
            func.max(SalesData.week_ending).label("latest_date"),
        ).first()

        # Recent sales (last week)
        recent_stats = (
            db.query(
                func.sum(SalesData.units_sold).label("recent_units"),
                func.sum(SalesData.revenue).label("recent_revenue"),
            )
            .filter(SalesData.week_ending >= last_week)
            .first()
        )

        # Forecast summary
        forecast_stats = (
            db.query(
                func.sum(Forecast.predicted_units).label("total_predicted_units"),
                func.sum(Forecast.predicted_revenue).label("total_predicted_revenue"),
                func.avg(Forecast.confidence_score).label("avg_confidence"),
                func.count(func.distinct(Forecast.item_id)).label("forecasted_skus"),
                func.count(Forecast.id).label("total_forecasts"),
            )
            .filter(Forecast.is_active == True, Forecast.forecast_date >= current_date)
            .first()
        )

        return {
            "historical": {
                "total_units_sold": historical_stats.total_units_sold or 0,
                "total_revenue": float(historical_stats.total_revenue or 0),
                "active_skus": historical_stats.active_skus or 0,
                "date_range": {
                    "start": historical_stats.earliest_date.isoformat()
                    if historical_stats.earliest_date
                    else None,
                    "end": historical_stats.latest_date.isoformat()
                    if historical_stats.latest_date
                    else None,
                },
            },
            "recent": {
                "units_sold": recent_stats.recent_units or 0,
                "revenue": float(recent_stats.recent_revenue or 0),
            },
            "forecast": {
                "total_predicted_units": forecast_stats.total_predicted_units or 0,
                "total_predicted_revenue": float(
                    forecast_stats.total_predicted_revenue or 0
                ),
                "avg_confidence": float(forecast_stats.avg_confidence or 0),
                "forecasted_skus": forecast_stats.forecasted_skus or 0,
                "total_forecasts": forecast_stats.total_forecasts or 0,
            },
        }

    except Exception as e:
        logger.error(f"Error fetching summary stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error fetching summary stats: {str(e)}"
        )
