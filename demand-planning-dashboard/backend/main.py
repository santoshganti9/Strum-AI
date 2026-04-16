from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from database import engine
from models import Base

from routers import (
    demand_planning,
    forecasts,
    sales,
    sku_detail_simple as sku_detail,
    skus,
)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Demand Planning Dashboard API",
    description="API for retail supply chain demand planning and forecasting",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Demand Planning Dashboard API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "demand-planning-api"}


app.include_router(skus.router, prefix="/api/v1/skus", tags=["SKUs"])
app.include_router(forecasts.router, prefix="/api/v1/forecasts", tags=["Forecasts"])
app.include_router(sales.router, prefix="/api/v1/sales", tags=["Sales"])
app.include_router(
    demand_planning.router, prefix="/api/v1/demand-planning", tags=["Demand Planning"]
)
app.include_router(sku_detail.router, prefix="/api/v1/sku-detail", tags=["SKU Detail"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
