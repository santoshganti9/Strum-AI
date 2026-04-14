from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional

from database import get_db
from models import SKU, SalesData, Forecast

router = APIRouter(tags=["sku-detail"])


def _get_anchor_datetime_for_sku(db: Session, item_id: str) -> Optional[datetime]:
    latest_actual = (
        db.query(func.max(SalesData.week_ending))
        .filter(SalesData.item_id == item_id)
        .scalar()
    )
    if latest_actual is not None:
        return latest_actual

    latest_forecast = (
        db.query(func.max(Forecast.forecast_date))
        .filter(Forecast.item_id == item_id)
        .scalar()
    )
    return latest_forecast


@router.get("/sku/{item_id}")
def get_sku_details(
    item_id: str = Path(..., description="SKU Item ID"), db: Session = Depends(get_db)
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
        sales_summary = (
            db.query(
                func.sum(SalesData.units_sold).label("total_units_sold"),
                func.sum(SalesData.revenue).label("total_revenue"),
                func.count(SalesData.id).label("total_transactions"),
                func.min(SalesData.week_ending).label("first_sale_date"),
                func.max(SalesData.week_ending).label("last_sale_date"),
            )
            .filter(SalesData.item_id == item_id)
            .first()
        )

        # Get forecast summary
        forecast_summary = (
            db.query(
                func.sum(Forecast.predicted_units).label("total_predicted_units"),
                func.sum(Forecast.predicted_revenue).label("total_predicted_revenue"),
                func.avg(Forecast.confidence_score).label("avg_confidence"),
                func.count(Forecast.id).label("total_forecasts"),
            )
            .filter(Forecast.item_id == item_id)
            .first()
        )

        return {
            "sku_info": {
                "item_id": sku.item_id,
                "item_name": sku.item_name,
                "category": sku.category,
                "brand": sku.brand,
                "unit_cost": float(sku.unit_cost) if sku.unit_cost else None,
                "supplier": sku.supplier,
                "created_at": sku.created_at.isoformat() if sku.created_at else None,
            },
            "sales_summary": {
                "total_units_sold": int(sales_summary.total_units_sold or 0),
                "total_revenue": float(sales_summary.total_revenue or 0),
                "total_transactions": int(sales_summary.total_transactions or 0),
                "avg_price": float(
                    (sales_summary.total_revenue or 0)
                    / (sales_summary.total_units_sold or 1)
                ),
                "first_sale_date": sales_summary.first_sale_date.isoformat()
                if sales_summary.first_sale_date
                else None,
                "last_sale_date": sales_summary.last_sale_date.isoformat()
                if sales_summary.last_sale_date
                else None,
            },
            "forecast_summary": {
                "total_predicted_units": int(
                    forecast_summary.total_predicted_units or 0
                ),
                "total_predicted_revenue": float(
                    forecast_summary.total_predicted_revenue or 0
                ),
                "avg_confidence": float(forecast_summary.avg_confidence or 0),
                "total_forecasts": int(forecast_summary.total_forecasts or 0),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching SKU details: {str(e)}"
        )


@router.get("/sku/{item_id}/timeline")
def get_sku_timeline(
    item_id: str = Path(..., description="SKU Item ID"),
    historical_weeks: int = Query(13, description="Number of historical weeks"),
    forecast_weeks: int = Query(39, description="Number of forecast weeks"),
    db: Session = Depends(get_db),
):
    """
    Get 52-week timeline for a specific SKU (13 weeks historical + 39 weeks forecast)
    """
    try:
        # Verify SKU exists
        sku = db.query(SKU).filter(SKU.item_id == item_id).first()
        if not sku:
            raise HTTPException(status_code=404, detail=f"SKU {item_id} not found")

        anchor_dt = _get_anchor_datetime_for_sku(db, item_id)
        if anchor_dt is None:
            return {
                "item_id": item_id,
                "item_name": sku.item_name,
                "timeline_data": [],
                "period_summary": {
                    "historical_weeks": historical_weeks,
                    "forecast_weeks": forecast_weeks,
                    "total_weeks": 0,
                    "historical_records": 0,
                    "forecast_records": 0,
                    "anchor_week_ending": None,
                },
            }

        # Build a continuous weekly index: (historical_weeks including anchor) + forecast_weeks
        historical_start = anchor_dt - timedelta(weeks=historical_weeks - 1)
        forecast_end = anchor_dt + timedelta(weeks=forecast_weeks)

        # Get historical aggregates within the historical window
        historical_data = (
            db.query(
                SalesData.week_ending,
                func.sum(SalesData.units_sold).label("units_sold"),
                func.sum(SalesData.revenue).label("revenue"),
            )
            .filter(
                SalesData.item_id == item_id,
                SalesData.week_ending >= historical_start,
                SalesData.week_ending <= anchor_dt,
            )
            .group_by(SalesData.week_ending)
            .order_by(SalesData.week_ending)
            .all()
        )

        # Get forecast data
        forecast_data = (
            db.query(
                Forecast.forecast_date,
                func.sum(Forecast.predicted_units).label("predicted_units"),
                func.sum(Forecast.predicted_revenue).label("predicted_revenue"),
                func.avg(Forecast.confidence_score).label("confidence_score"),
            )
            .filter(
                Forecast.item_id == item_id,
                Forecast.forecast_date > anchor_dt,
                Forecast.forecast_date <= forecast_end,
            )
            .group_by(Forecast.forecast_date)
            .order_by(Forecast.forecast_date)
            .all()
        )

        # Index results by date (YYYY-MM-DD) so we can fill missing weeks.
        historical_by_day: dict[str, dict] = {}
        for record in historical_data:
            key = record.week_ending.date().isoformat()
            units = int(record.units_sold or 0)
            revenue = float(record.revenue or 0)
            avg_price = (revenue / units) if units > 0 else 0.0
            historical_by_day[key] = {
                "units": units,
                "revenue": revenue,
                "avg_unit_price": float(avg_price),
            }

        forecast_by_day: dict[str, dict] = {}
        for record in forecast_data:
            key = record.forecast_date.date().isoformat()
            units = int(record.predicted_units or 0)
            revenue = float(record.predicted_revenue or 0)
            avg_price = (revenue / units) if units > 0 else 0.0
            forecast_by_day[key] = {
                "units": units,
                "revenue": revenue,
                "avg_unit_price": float(avg_price),
                "confidence_score": float(record.confidence_score or 0.5),
            }

        # Build the final continuous timeline
        timeline_data = []
        total_weeks = historical_weeks + forecast_weeks
        for i in range(total_weeks):
            week_dt = historical_start + timedelta(weeks=i)
            week_key = week_dt.date().isoformat()

            if week_dt <= anchor_dt:
                row = historical_by_day.get(week_key, None)
                timeline_data.append(
                    {
                        "week_ending": week_key,
                        "units": int(row["units"]) if row else 0,
                        "revenue": float(row["revenue"]) if row else 0.0,
                        "avg_unit_price": float(row["avg_unit_price"]) if row else 0.0,
                        "cust_instock": 0.8,
                        "type": "historical",
                    }
                )
            else:
                row = forecast_by_day.get(week_key, None)
                timeline_data.append(
                    {
                        "week_ending": week_key,
                        "units": int(row["units"]) if row else 0,
                        "revenue": float(row["revenue"]) if row else 0.0,
                        "avg_unit_price": float(row["avg_unit_price"]) if row else 0.0,
                        "cust_instock": 0.85,
                        "confidence_score": float(row["confidence_score"])
                        if row
                        else 0.5,
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
                "anchor_week_ending": anchor_dt.date().isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching SKU timeline: {str(e)}"
        )


@router.get("/sku/{item_id}/previous-year")
def get_sku_previous_year(
    item_id: str = Path(..., description="SKU Item ID"),
    weeks: int = Query(52, description="Number of weeks to compare"),
    historical_weeks: int = Query(
        13, description="Number of historical weeks for alignment"
    ),
    forecast_weeks: int = Query(
        39, description="Number of forecast weeks for alignment"
    ),
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

        anchor_dt = _get_anchor_datetime_for_sku(db, item_id)
        if anchor_dt is None:
            return {
                "item_id": item_id,
                "item_name": sku.item_name,
                "previous_year_data": [],
                "comparison_period": {
                    "previous_year_start": None,
                    "previous_year_end": None,
                    "total_records": 0,
                    "anchor_week_ending": None,
                },
            }

        # Align previous-year to the same window as the main 52-week timeline.
        current_start = anchor_dt - timedelta(weeks=historical_weeks - 1)
        current_end = anchor_dt + timedelta(weeks=forecast_weeks)
        previous_year_start = current_start - timedelta(weeks=52)
        previous_year_end = current_end - timedelta(weeks=52)

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

        # Index by original week ending day, then shift +52 weeks so keys match the current window.
        by_original_day: dict[str, dict] = {}
        for record in previous_year_data:
            original_key = record.week_ending.date().isoformat()
            by_original_day[original_key] = {
                "units": int(record.units_sold or 0),
                "revenue": float(record.revenue or 0),
            }

        comparison_data = []
        total_weeks = historical_weeks + forecast_weeks
        for i in range(total_weeks):
            current_week_dt = current_start + timedelta(weeks=i)
            prev_week_dt = current_week_dt - timedelta(weeks=52)
            prev_key = prev_week_dt.date().isoformat()
            row = by_original_day.get(prev_key, None)

            comparison_data.append(
                {
                    "week_ending": current_week_dt.date().isoformat(),
                    "original_week_ending": prev_key,
                    "units": int(row["units"]) if row else 0,
                    "revenue": float(row["revenue"]) if row else 0.0,
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
                "anchor_week_ending": anchor_dt.date().isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching previous year data: {str(e)}"
        )


@router.get("/sku/{item_id}/demand-drivers")
def get_sku_demand_drivers(
    item_id: str = Path(..., description="SKU Item ID"),
    weeks: int = Query(52, description="Number of weeks of demand driver data"),
    historical_weeks: int = Query(
        13, description="Number of historical weeks for alignment"
    ),
    forecast_weeks: int = Query(
        39, description="Number of forecast weeks for alignment"
    ),
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

        anchor_dt = _get_anchor_datetime_for_sku(db, item_id)
        if anchor_dt is None:
            return {
                "item_id": item_id,
                "item_name": sku.item_name,
                "demand_drivers_data": [],
                "summary": {
                    "total_weeks": 0,
                    "historical_weeks": 0,
                    "projected_weeks": 0,
                    "anchor_week_ending": None,
                },
            }

        # Get historical sales data to calculate price trends within the aligned historical window
        historical_start = anchor_dt - timedelta(weeks=historical_weeks - 1)
        historical_data = (
            db.query(
                SalesData.week_ending,
                func.sum(SalesData.units_sold).label("units_sold"),
                func.sum(SalesData.revenue).label("revenue"),
            )
            .filter(
                SalesData.item_id == item_id,
                SalesData.week_ending >= historical_start,
                SalesData.week_ending <= anchor_dt,
            )
            .group_by(SalesData.week_ending)
            .order_by(SalesData.week_ending)
            .all()
        )

        # Format demand drivers data
        demand_drivers_data = []

        # Historical data with calculated prices
        for record in historical_data:
            avg_price = (
                (record.revenue / record.units_sold) if record.units_sold > 0 else 10.0
            )
            demand_drivers_data.append(
                {
                    "week_ending": record.week_ending.isoformat(),
                    "avg_unit_price": float(avg_price),
                    "cust_instock": 0.8
                    + (
                        0.1 * (len(demand_drivers_data) % 3 - 1)
                    ),  # Simulate stock variation
                    "units_sold": int(record.units_sold or 0),
                    "type": "historical",
                }
            )

        # Simulate future demand drivers aligned to the forecast window
        remaining_forecast_weeks = forecast_weeks
        if remaining_forecast_weeks > 0:
            base_price = (
                demand_drivers_data[-1]["avg_unit_price"]
                if demand_drivers_data
                else 0.0
            )

            for i in range(remaining_forecast_weeks):
                future_date = anchor_dt + timedelta(weeks=i + 1)
                # Simulate price trends and stock planning
                price_trend = base_price * (1 + 0.002 * i)  # Slight price increase
                stock_target = max(
                    0.7, 0.85 + (0.05 * ((i % 4) - 2))
                )  # Cyclical stock planning

                demand_drivers_data.append(
                    {
                        "week_ending": future_date.isoformat(),
                        "avg_unit_price": round(price_trend, 2),
                        "cust_instock": round(stock_target, 3),
                        "units_sold": None,  # No actual sales for future
                        "type": "projected",
                    }
                )

        return {
            "item_id": item_id,
            "item_name": sku.item_name,
            "demand_drivers_data": demand_drivers_data,
            "summary": {
                "total_weeks": len(demand_drivers_data),
                "historical_weeks": len(
                    [d for d in demand_drivers_data if d["type"] == "historical"]
                ),
                "projected_weeks": len(
                    [d for d in demand_drivers_data if d["type"] == "projected"]
                ),
                "avg_price_range": {
                    "min": min(
                        [
                            d["avg_unit_price"]
                            for d in demand_drivers_data
                            if d["avg_unit_price"] > 0
                        ]
                    ),
                    "max": max(
                        [
                            d["avg_unit_price"]
                            for d in demand_drivers_data
                            if d["avg_unit_price"] > 0
                        ]
                    ),
                },
                "stock_range": {
                    "min": min(
                        [
                            d["cust_instock"]
                            for d in demand_drivers_data
                            if d["cust_instock"] > 0
                        ]
                    ),
                    "max": max(
                        [
                            d["cust_instock"]
                            for d in demand_drivers_data
                            if d["cust_instock"] > 0
                        ]
                    ),
                },
                "anchor_week_ending": anchor_dt.date().isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching demand drivers: {str(e)}"
        )


@router.get("/search")
def search_skus(
    query: str = Query(..., description="Search query for SKU name or ID"),
    limit: int = Query(20, description="Maximum number of results"),
    db: Session = Depends(get_db),
):
    """
    Search for SKUs by name or ID
    """
    try:
        # Search in both item_id and item_name
        search_results = (
            db.query(SKU)
            .filter(
                (SKU.item_id.ilike(f"%{query}%")) | (SKU.item_name.ilike(f"%{query}%"))
            )
            .limit(limit)
            .all()
        )

        results = []
        for sku in search_results:
            # Get basic sales stats for each SKU
            sales_stats = (
                db.query(
                    func.sum(SalesData.units_sold).label("total_units"),
                    func.sum(SalesData.revenue).label("total_revenue"),
                )
                .filter(SalesData.item_id == sku.item_id)
                .first()
            )

            results.append(
                {
                    "item_id": sku.item_id,
                    "item_name": sku.item_name,
                    "category": sku.category,
                    "brand": sku.brand,
                    "total_units_sold": int(sales_stats.total_units or 0),
                    "total_revenue": float(sales_stats.total_revenue or 0),
                }
            )

        return {
            "query": query,
            "results": results,
            "total_found": len(results),
            "limit": limit,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching SKUs: {str(e)}")
