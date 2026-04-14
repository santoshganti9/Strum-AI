#!/usr/bin/env python3
"""
Script to run data migration for the Demand Planning Dashboard
"""

import sys
import os
from data_migration import DataMigration

def main():
    print("🚀 Starting Demand Planning Dashboard Data Migration")
    print("=" * 60)
    
    try:
        with DataMigration() as migration:
            print("📊 Importing aggregated sales data...")
            aggregated_result = migration.import_aggregated_data_csv()
            
            print(f"✅ Aggregated data import completed:")
            print(f"   - SKUs created: {aggregated_result['skus_created']}")
            print(f"   - Sales records created: {aggregated_result['sales_created']}")
            print(f"   - Total rows processed: {aggregated_result['total_processed']}")
            print(f"   - Errors: {aggregated_result['errors']}")
            print()
            
            print("🔮 Importing forecast data...")
            forecast_result = migration.import_forecast_data_csv()
            
            print(f"✅ Forecast data import completed:")
            print(f"   - Forecasts created: {forecast_result['forecasts_created']}")
            print(f"   - Total rows processed: {forecast_result['total_processed']}")
            print(f"   - Errors: {forecast_result['errors']}")
            print()
            
            print("🎉 Data migration completed successfully!")
            print("=" * 60)
            print("📈 Your Demand Planning Dashboard is ready!")
            print("   - Frontend: http://localhost:3000")
            print("   - Backend API: http://localhost:8000")
            print("   - API Docs: http://localhost:8000/docs")
            
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
