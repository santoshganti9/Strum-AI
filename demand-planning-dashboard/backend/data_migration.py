import pandas as pd
import json
from database import SessionLocal
from models import SKU, SalesData, Forecast
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataMigration:
    def __init__(self):
        self.db = SessionLocal()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

    def import_aggregated_data_csv(
        self, csv_file_path: str = "data/aggregated_data.csv"
    ) -> dict:
        """
        Import sales data from aggregated_data.csv
        Columns: item_id, timestamp, units_sold, demand_drivers
        """
        try:
            df = pd.read_csv(csv_file_path)
            logger.info(f"Loading aggregated data from {csv_file_path}")
            logger.info(f"Total rows: {len(df)}")

            # First, create SKUs from unique item_ids
            unique_items = df["item_id"].unique()
            logger.info(f"Found {len(unique_items)} unique SKUs")

            sku_created_count = 0
            for item_id in unique_items:
                existing_sku = self.db.query(SKU).filter(SKU.item_id == item_id).first()
                if not existing_sku:
                    # Extract item name from item_id (remove CUST_003_)
                    item_name = (
                        item_id.replace("CUST_003_", "").replace("_", " ").title()
                    )

                    # Parse demand drivers from first occurrence to get pricing info
                    first_row = df[df["item_id"] == item_id].iloc[0]
                    try:
                        demand_drivers = json.loads(first_row["demand_drivers"])
                        unit_price = demand_drivers.get("avg_unit_price", None)
                    except Exception:
                        unit_price = None

                    new_sku = SKU(
                        item_id=item_id,
                        item_name=item_name,
                        category="Retail Product",
                        unit_price=unit_price,
                    )
                    self.db.add(new_sku)
                    sku_created_count += 1

            self.db.commit()
            logger.info(f"Created {sku_created_count} new SKUs")

            # Now import sales data
            sales_created_count = 0
            errors = []

            for index, row in df.iterrows():
                try:
                    # Parse demand drivers to get additional info
                    try:
                        demand_drivers = json.loads(row["demand_drivers"])
                        avg_unit_price = demand_drivers.get("avg_unit_price", 0)
                        revenue = float(row["units_sold"]) * avg_unit_price
                    except Exception:
                        revenue = 0.0

                    # Convert timestamp to datetime
                    week_ending = pd.to_datetime(row["timestamp"])

                    sales_data = SalesData(
                        item_id=row["item_id"],
                        week_ending=week_ending,
                        units_sold=int(row["units_sold"]),
                        revenue=revenue,
                        region="Default Region",
                    )

                    self.db.add(sales_data)
                    sales_created_count += 1

                    # Commit in batches of 1000
                    if sales_created_count % 1000 == 0:
                        self.db.commit()
                        logger.info(f"Processed {sales_created_count} sales records...")

                except Exception as e:
                    error_msg = f"Row {index + 1}: {str(e)}"
                    errors.append(error_msg)
                    if len(errors) < 10:  # Only log first 10 errors
                        logger.error(error_msg)

            self.db.commit()

            result = {
                "skus_created": sku_created_count,
                "sales_created": sales_created_count,
                "total_processed": len(df),
                "errors": len(errors),
            }

            logger.info(f"Aggregated data import completed: {result}")
            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"Aggregated data import failed: {str(e)}")
            raise

    def import_forecast_data_csv(
        self, csv_file_path: str = "data/forecast_data.csv"
    ) -> dict:
        """
        Import forecast data from forecast_data.csv
        Columns: client_id, inference_id, model_id, created_at, inference_date, run_id, item_id, forecasts, demand_drivers, auto_features
        """
        try:
            df = pd.read_csv(csv_file_path)
            logger.info(f"Loading forecast data from {csv_file_path}")
            logger.info(f"Total rows: {len(df)}")

            forecast_created_count = 0
            errors = []

            for index, row in df.iterrows():
                try:
                    # Parse the forecasts JSON
                    forecasts_json = json.loads(row["forecasts"])
                    model_id = row["model_id"]

                    # Process each forecast timestamp
                    for forecast_entry in forecasts_json:
                        forecast_date = pd.to_datetime(forecast_entry["timestamp"])
                        values = forecast_entry["values"]

                        # Use mean as predicted units and calculate revenue
                        predicted_units = int(values.get("mean", 0))

                        # Get unit price from SKU to calculate predicted revenue
                        sku = (
                            self.db.query(SKU)
                            .filter(SKU.item_id == row["item_id"])
                            .first()
                        )
                        if sku and sku.unit_price:
                            predicted_revenue = predicted_units * sku.unit_price
                        else:
                            predicted_revenue = None

                        # Calculate confidence score from p50 vs mean
                        p50 = values.get("p50", values.get("mean", 0))
                        mean = values.get("mean", 0)
                        if mean > 0 and p50 is not None:
                            confidence_score = min(1.0, p50 / mean)
                        else:
                            confidence_score = 0.5

                        forecast = Forecast(
                            item_id=row["item_id"],
                            forecast_date=forecast_date,
                            forecast_period="weekly",
                            predicted_units=predicted_units,
                            predicted_revenue=predicted_revenue,
                            confidence_score=confidence_score,
                            model_version=str(model_id),
                            is_active=True,
                        )

                        self.db.add(forecast)
                        forecast_created_count += 1

                    # Commit in batches of 100 (since each row creates multiple forecasts)
                    if (index + 1) % 100 == 0:
                        self.db.commit()
                        logger.info(
                            f"Processed {index + 1} forecast rows, created {forecast_created_count} forecasts..."
                        )

                except Exception as e:
                    error_msg = f"Row {index + 1}: {str(e)}"
                    errors.append(error_msg)
                    if len(errors) < 10:  # Only log first 10 errors
                        logger.error(error_msg)

            self.db.commit()

            result = {
                "forecasts_created": forecast_created_count,
                "total_processed": len(df),
                "errors": len(errors),
            }

            logger.info(f"Forecast data import completed: {result}")
            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"Forecast data import failed: {str(e)}")
            raise

    def import_all_data(self):
        """Import both aggregated data and forecast data"""
        logger.info("Starting complete data migration...")

        # Import aggregated data first (creates SKUs and sales data)
        aggregated_result = self.import_aggregated_data_csv()

        # Then import forecast data
        forecast_result = self.import_forecast_data_csv()

        total_result = {
            "aggregated_data": aggregated_result,
            "forecast_data": forecast_result,
        }

        logger.info("Complete data migration finished!")
        logger.info(f"Final results: {total_result}")

        return total_result


def main():
    """Run the data migration"""
    with DataMigration() as migration:
        return migration.import_all_data()


if __name__ == "__main__":
    main()
