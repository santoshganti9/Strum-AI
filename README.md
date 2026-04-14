# Demand Planning Dashboard

A comprehensive retail supply chain demand planning dashboard built with PostgreSQL, FastAPI, and Next.js TypeScript. This system enables retail supply chain teams to monitor weekly sales performance and review AI-generated forecasts at a SKU level.

## 🏗️ Architecture

- **Database**: PostgreSQL 15
- **Backend**: Python FastAPI with SQLAlchemy ORM
- **Frontend**: Next.js 14 with TypeScript and Tailwind CSS
- **Containerization**: Docker & Docker Compose

## 📁 Project Structure

```
demand-planning-dashboard/
├── backend/                    # FastAPI Backend
│   ├── routers/               # API route handlers
│   │   ├── skus.py           # SKU management endpoints
│   │   ├── sales.py          # Sales data endpoints
│   │   └── forecasts.py      # Forecast endpoints
│   ├── main.py               # FastAPI application entry point
│   ├── database.py           # Database configuration
│   ├── models.py             # SQLAlchemy models
│   ├── schemas.py            # Pydantic schemas
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile           # Backend container config
│   └── .env.example         # Environment variables template
├── frontend/                  # Next.js Frontend
│   ├── src/
│   │   ├── app/              # Next.js 14 app directory
│   │   ├── components/       # React components
│   │   └── lib/              # Utilities and API client
│   ├── package.json          # Node.js dependencies
│   ├── tailwind.config.js    # Tailwind CSS configuration
│   ├── tsconfig.json         # TypeScript configuration
│   └── Dockerfile           # Frontend container config
└── docker-compose.yml        # Multi-service orchestration
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### 1. Clone and Setup

```bash
cd /Users/santoshganti/Documents/GitHub/Strum-AI/demand-planning-dashboard
```

### 2. Environment Configuration

Create environment files:

```bash
# Backend environment
cp backend/.env.example backend/.env

# Update backend/.env with your settings if needed
```

### 3. Start with Docker Compose

```bash
# Start all services (PostgreSQL, Backend, Frontend)
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Access the Application

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432 (postgres/password123)

## 🔧 Development Setup

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://postgres:password123@localhost:5432/demand_planning"

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
export NEXT_PUBLIC_API_URL="http://localhost:8000"

# Run development server
npm run dev
```

## 📊 Database Schema

### Core Tables

1. **SKUs** - Product information and metadata
2. **Sales Data** - Weekly sales performance by SKU
3. **Forecasts** - AI-generated demand predictions

### Key Relationships

- SKUs have many Sales Data records
- SKUs have many Forecasts
- Sales Data links to SKUs via item_id
- Forecasts link to SKUs via item_id

## 🔌 API Endpoints

### SKU Management
- `GET /api/v1/skus` - List all SKUs with filtering
- `GET /api/v1/skus/{item_id}` - Get SKU details with sales/forecasts
- `POST /api/v1/skus` - Create new SKU
- `PUT /api/v1/skus/{item_id}` - Update SKU
- `DELETE /api/v1/skus/{item_id}` - Delete SKU

### Sales Data
- `GET /api/v1/sales` - List sales data with filtering
- `GET /api/v1/sales/summary` - Dashboard summary metrics
- `GET /api/v1/sales/{item_id}/weekly` - Weekly sales for specific SKU
- `POST /api/v1/sales` - Create sales record
- `POST /api/v1/sales/bulk` - Bulk import sales data

### Forecasts
- `GET /api/v1/forecasts` - List forecasts with filtering
- `GET /api/v1/forecasts/{item_id}/latest` - Latest forecast for SKU
- `GET /api/v1/forecasts/{item_id}/history` - Forecast history
- `GET /api/v1/forecasts/summary` - Forecast summary metrics
- `POST /api/v1/forecasts` - Create forecast
- `PUT /api/v1/forecasts/{id}` - Update forecast

## 📈 Features

### Dashboard Overview
- Total units sold and revenue metrics
- Active SKU count
- Active forecast count
- Weekly sales trend visualization
- Top performing SKUs table

### SKU Management
- Complete CRUD operations
- Category and brand filtering
- Supplier information tracking
- Cost and pricing data

### Sales Analytics
- Weekly sales performance tracking
- Regional sales breakdown
- Historical trend analysis
- Revenue and unit metrics

### Demand Forecasting
- AI-generated predictions
- Confidence scoring
- Multiple forecast periods (weekly/monthly)
- Forecast accuracy tracking

## 🔄 Data Migration

After setup, you'll be ready to import your CSV files:

1. **SKU Data CSV** - Product catalog information
2. **Sales Data CSV** - Historical sales performance

The system provides bulk import endpoints for efficient data migration.

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation and serialization
- **Alembic**: Database migrations
- **PostgreSQL**: Primary database
- **Uvicorn**: ASGI server

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **Heroicons**: Icon library
- **Axios**: HTTP client
- **Recharts**: Chart library (ready for implementation)

### DevOps
- **Docker**: Containerization
- **Docker Compose**: Multi-service orchestration
- **PostgreSQL**: Database service

## 🔒 Security Considerations

- Environment variables for sensitive configuration
- CORS configuration for frontend-backend communication
- Input validation with Pydantic schemas
- SQL injection prevention with SQLAlchemy ORM

## 📝 Next Steps

1. **Import CSV Data**: Use the bulk import endpoints to load your historical data
2. **Implement Charts**: Enhance the dashboard with Recharts visualizations
3. **Add Authentication**: Implement user authentication and authorization
4. **Forecast Models**: Integrate ML models for demand prediction
5. **Real-time Updates**: Add WebSocket support for live data updates

## 🤝 Contributing

1. Follow the existing code structure and patterns
2. Add tests for new features
3. Update documentation for API changes
4. Use TypeScript for all frontend code
5. Follow Python PEP 8 for backend code

## 📞 Support

For issues and questions:
1. Check the API documentation at http://localhost:8000/docs
2. Review the application logs: `docker-compose logs`
3. Verify database connectivity and migrations

---

**Ready for CSV data import and further development!** 🚀
