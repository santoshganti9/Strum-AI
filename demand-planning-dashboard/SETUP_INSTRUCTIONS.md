# Demand Planning Dashboard - Setup Instructions

## 🚀 Quick Start Guide

### Prerequisites
1. **Docker Desktop** - Install and start Docker Desktop
2. **Git** - For version control

### Step 1: Start Docker Desktop
Make sure Docker Desktop is running on your machine.

### Step 2: Start the Application
```bash
cd /Users/santoshganti/Documents/GitHub/Strum-AI/demand-planning-dashboard

# Start all services (PostgreSQL, Backend, Frontend)
docker-compose up -d

# Check if services are running
docker-compose ps
```

### Step 3: Import Your CSV Data
```bash
# Enter the backend container
docker-compose exec backend bash

# Run the data migration
python run_migration.py
```

### Step 4: Access the Application
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🔧 Alternative: Local Development Setup

If you prefer to run without Docker:

### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL (you'll need to install PostgreSQL locally)
# Update DATABASE_URL in .env file

# Run migrations and start server
python run_migration.py
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 📊 What's Included

### Database Schema
- **SKUs Table**: Product information and metadata
- **Sales Data Table**: Weekly sales performance by SKU
- **Forecasts Table**: AI-generated demand predictions

### API Endpoints
- **SKU Management**: CRUD operations for products
- **Sales Analytics**: Historical sales data and summaries
- **Forecast Management**: AI predictions and confidence scores

### Frontend Features
- **Dashboard Overview**: Key metrics and visualizations
- **SKU Management**: Product catalog interface
- **Sales Analytics**: Performance tracking
- **Forecast Review**: AI prediction analysis

## 🗂️ Your Data Structure

### Aggregated Data (aggregated_data.csv)
- **item_id**: Product identifier
- **timestamp**: Week ending date
- **units_sold**: Units sold that week
- **demand_drivers**: JSON with pricing and stock info

### Forecast Data (forecast_data.csv)
- **item_id**: Product identifier
- **forecasts**: JSON with prediction intervals
- **model_id**: AI model version
- **confidence_score**: Prediction confidence

## 🔍 Troubleshooting

### Docker Issues
```bash
# Check Docker is running
docker --version

# View logs
docker-compose logs

# Restart services
docker-compose down
docker-compose up -d
```

### Database Issues
```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

### Import Issues
```bash
# Check data files exist
ls -la backend/data/

# Run migration with verbose logging
docker-compose exec backend python run_migration.py
```

## 📈 Next Steps

1. **Verify Data Import**: Check the dashboard shows your data
2. **Customize Views**: Modify frontend components as needed
3. **Add Features**: Extend API endpoints for specific needs
4. **Deploy**: Use the Docker setup for production deployment

## 🎯 Key Features Ready for Use

✅ **Complete Database Schema** - SKUs, Sales, Forecasts
✅ **REST API** - Full CRUD operations with filtering
✅ **Modern Frontend** - React/TypeScript with Tailwind CSS
✅ **Data Migration** - CSV import utilities
✅ **Docker Setup** - Production-ready containerization
✅ **Documentation** - API docs and setup guides

Your Demand Planning Dashboard is ready to use! 🚀
