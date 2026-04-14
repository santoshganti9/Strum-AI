# Demand Planning Dashboard

We take the provided datasets (`aggregated_data.csv` and `forecast_data.csv`), load them into a local database, serve them through a backend API, and visualize them in a two-page Next.js dashboard.

## Assessment Requirements Mapped

- **Frontend**: Next.js 14 (React + TypeScript)
- **Backend**: Python FastAPI
- **Database**: PostgreSQL (local, via Docker)
- **Submission artifact**: GitHub repo with setup + design notes in README

## Data Used

- `aggregated_data.csv` (historical weekly actuals)
- `forecast_data.csv` (40-week model forecasts + percentiles + projected drivers)

Implementation note: dashboard APIs use the latest available inference context and combine **last 13 historical weeks** with **next 39 forecast weeks** for the primary views.

## Architecture

- **Frontend**: Next.js App Router + Tailwind CSS
- **Backend**: FastAPI + SQLAlchemy
- **Database**: PostgreSQL 15
- **Runtime**: Docker Compose (frontend + backend + database)

## Project Structure

```text
demand-planning-dashboard/
├── backend/
│   ├── main.py                  # FastAPI app + router registration
│   ├── models.py                # SQLAlchemy schema
│   ├── data_migration.py        # CSV parsing + load logic
│   ├── run_migration.py         # Migration runner script
│   ├── database.py              # DB connection/session config
│   ├── requirements.txt
│   └── routers/
│       ├── demand_planning_simple.py
│       ├── sku_detail_simple.py
│       ├── skus.py
│       ├── sales.py
│       └── forecasts.py
├── frontend/
│   ├── src/app/page.tsx         # Demand Planning Home
│   ├── src/app/sku/[itemId]/page.tsx  # SKU Detail Workbench
│   └── src/components/
└── docker-compose.yml
```

## Database Schema Design

To keep query access straightforward and performant for dashboard use-cases, the data is split into three main relational tables:

1. `skus`
   - Master SKU identity and product metadata (`item_id`, name/category/brand, pricing fields)
2. `sales_data`
   - Historical weekly actuals (`item_id`, `week_ending`, `units_sold`, derived `revenue`)
3. `forecasts`
   - Forecasted weekly points (`item_id`, `forecast_date`, `predicted_units`, confidence metadata)

### JSON Normalization Strategy

- `aggregated_data.demand_drivers` is parsed during migration; `avg_unit_price` is used to enrich SKU and compute revenue.
- `forecast_data.forecasts` array is flattened into one row per forecast week.
- Forecast confidence-related fields are derived and stored per weekly forecast record for easy API filtering and alerting.

## Backend API

Base URL: `http://localhost:8000`

### Utility Endpoints

- `GET /` — API metadata
- `GET /health` — health check
- `GET /docs` — Swagger UI

### Demand Planning Endpoints (`/api/v1/demand-planning`)

Endpoints used by the Home dashboard:

- `GET /summary-stats`
  - Returns historical totals, recent snapshot, and forecast summary blocks.
- `GET /combined-timeline?historical_weeks=13&forecast_weeks=39`
  - Returns timeline array with `type` = `historical | forecast`.
- `GET /forecast-accuracy-alerts?confidence_threshold=0.3&limit=20`
  - Returns ranked alert cards (`low_confidence`, `high_variance`) with severity.

### SKU Detail Endpoints (`/api/v1/sku-detail`)

Endpoints used by the SKU workbench:

- `GET /sku/{item_id}`
  - SKU metadata + `sales_summary` + `forecast_summary`.
- `GET /sku/{item_id}/timeline?historical_weeks=13&forecast_weeks=39`
  - Returns continuous weekly timeline payload for the 52-week chart.
- `GET /sku/{item_id}/previous-year?weeks=52`
  - Returns previous-year same-week series for overlay comparison.
- `GET /sku/{item_id}/demand-drivers?weeks=52`
  - Returns driver series (`avg_unit_price`, `cust_instock`) tagged as `historical | projected`.
- `GET /search?query=<sku_or_name>&limit=20`
  - Search endpoint powering SKU typeahead.

### Core CRUD Endpoints

Also implemented for data-level access:

#### SKUs (`/api/v1/skus`)
- `GET /?skip=0&limit=100&category=&brand=`
- `GET /{item_id}`
- `POST /`
- `PUT /{item_id}`
- `DELETE /{item_id}`

#### Sales (`/api/v1/sales`)
- `GET /?skip=0&limit=100&item_id=&region=&weeks_back=`
- `GET /summary?weeks_back=4`
- `GET /{item_id}/weekly?weeks_back=12`
- `POST /`
- `POST /bulk`

#### Forecasts (`/api/v1/forecasts`)
- `GET /?skip=0&limit=100&item_id=&is_active=true&forecast_period=weekly`
- `GET /{item_id}/latest`
- `GET /{item_id}/history?weeks_back=12`
- `GET /summary`
- `POST /`
- `PUT /{forecast_id}`
- `DELETE /{forecast_id}` (soft delete)

### Example Response Shapes

`GET /api/v1/demand-planning/summary-stats`

```json
{
  "historical": {
    "total_units_sold": 25842,
    "total_revenue": 1250000.0,
    "active_skus": 166,
    "date_range": { "start": "2024-07-21", "end": "2025-04-20" }
  },
  "recent": { "units_sold": 2584, "revenue": 125000.0 },
  "forecast": {
    "total_predicted_units": 31010,
    "total_predicted_revenue": 1500000.0,
    "avg_confidence": 0.75,
    "forecasted_skus": 166,
    "total_forecasts": 84480
  }
}
```

`GET /api/v1/sku-detail/sku/{item_id}/timeline?historical_weeks=13&forecast_weeks=39`

```json
{
  "item_id": "CUST_003_ITEM_0243",
  "timeline_data": [
    { "week_ending": "2025-01-26", "units": 820, "revenue": 3712.0, "type": "historical" },
    { "week_ending": "2025-04-27", "units": 845, "revenue": 3981.0, "confidence_score": 0.72, "type": "forecast" }
  ],
  "period_summary": {
    "historical_weeks": 13,
    "forecast_weeks": 39,
    "total_weeks": 52,
    "anchor_week_ending": "2025-04-20"
  }
}
```

## Frontend Pages

### 1) Demand Planning Home

- Aggregated trend chart: historical units sold (13 weeks) + forecast (39 weeks)
- Forecast attention alerts (confidence/variance driven)
- Search/navigation into SKU-level workbench

### 2) SKU Detail: Demand Planning Workbench

- 52-week timeline (13 historical + 39 forecast)
- Optional previous-year same-week comparison line
- Demand drivers side panel with:
  - `avg_unit_price` over time
  - `cust_instock` over time
  - historical + projected values

## Setup Instructions

## Prerequisites

- Docker + Docker Compose
- (Optional local dev) Python 3.11+
- (Optional local dev) Node.js 18+

## 1) Start services

From project root (`demand-planning-dashboard`):

```bash
docker-compose up -d --build
```

Services:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5435`

## 2) Place dataset files

Copy the two assessment CSVs into:

`backend/data/`

Expected files:
- `backend/data/aggregated_data.csv`
- `backend/data/forecast_data.csv`

## 3) Run data migration

```bash
docker-compose exec backend python run_migration.py
```

This will:
- create SKU records from unique `item_id`
- load historical weekly actuals
- flatten and load forecast weekly rows

## 4) Open the app

- Home page: `http://localhost:3000`
- Click an alert card or use search to open SKU Workbench

## Local Development (Without Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql://postgres:password123@localhost:5435/demand_planning"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
export NEXT_PUBLIC_API_URL="http://localhost:8000"
npm run dev
```

## Technical Notes

- **Backend framework**: FastAPI with SQLAlchemy session-per-request pattern via `Depends(get_db)`.
- **Relational model**: `skus` is the parent entity; `sales_data` and `forecasts` reference SKU via `item_id`.
- **CSV migration flow**:
  - Parse `aggregated_data.csv` and create missing SKUs.
  - Derive `revenue = units_sold * avg_unit_price` from demand-driver payload.
  - Parse `forecast_data.csv` and flatten each `forecasts` JSON array into one DB row per forecast week.
- **Time-series alignment**: SKU timeline APIs anchor on latest available actual week (fallback to latest forecast week) and return a continuous weekly index for chart stability.
- **CORS**: configured for local frontend origins on ports `3000` and `3001`.
- **Validation**: request bounds enforced through FastAPI query constraints (e.g., pagination and week-range limits on CRUD endpoints).

## Reviewer Checklist

- [x] Local DB setup (PostgreSQL)
- [x] CSV ingestion pipeline
- [x] REST API for dashboard and SKU views
- [x] Two-page frontend consuming backend APIs
- [x] README with setup + schema/API notes

## Assumptions & Notes

- The dashboard uses the most recent available inference context for forecast-facing views.
- Historical and projected driver values are exposed through dedicated SKU detail APIs for side-panel visualization.
- Authentication is out of scope.
