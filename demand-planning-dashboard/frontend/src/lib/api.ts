import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Demand Planning API functions
export const demandPlanningAPI = {
  // Get historical sales data
  getHistoricalSales: (weeks: number = 13, itemId?: string) =>
    apiClient.get('/api/v1/demand-planning/historical-sales', {
      params: { weeks, item_id: itemId }
    }),

  // Get forecast data
  getForecastData: (weeks: number = 39, itemId?: string) =>
    apiClient.get('/api/v1/demand-planning/forecast-data', {
      params: { weeks, item_id: itemId }
    }),

  // Get combined timeline data
  getCombinedTimeline: (historicalWeeks: number = 13, forecastWeeks: number = 39, itemId?: string) =>
    apiClient.get('/api/v1/demand-planning/combined-timeline', {
      params: { 
        historical_weeks: historicalWeeks, 
        forecast_weeks: forecastWeeks, 
        item_id: itemId 
      }
    }),

  // Get forecast accuracy alerts
  getForecastAlerts: (confidenceThreshold: number = 0.3, limit: number = 20) =>
    apiClient.get('/api/v1/demand-planning/forecast-accuracy-alerts', {
      params: { confidence_threshold: confidenceThreshold, limit }
    }),

  // Get summary statistics
  getSummaryStats: () =>
    apiClient.get('/api/v1/demand-planning/summary-stats')
}

// SKU Detail API functions
export const skuDetailAPI = {
  // Get SKU details
  getSkuDetails: (itemId: string) =>
    apiClient.get(`/api/v1/sku-detail/sku/${itemId}`),

  // Get SKU timeline (52 weeks)
  getSkuTimeline: (itemId: string, historicalWeeks: number = 13, forecastWeeks: number = 39) =>
    apiClient.get(`/api/v1/sku-detail/sku/${itemId}/timeline`, {
      params: { historical_weeks: historicalWeeks, forecast_weeks: forecastWeeks }
    }),

  // Get previous year comparison
  getPreviousYearData: (itemId: string, weeks: number = 52) =>
    apiClient.get(`/api/v1/sku-detail/sku/${itemId}/previous-year`, {
      params: { weeks }
    }),

  // Get demand drivers
  getDemandDrivers: (itemId: string, weeks: number = 52) =>
    apiClient.get(`/api/v1/sku-detail/sku/${itemId}/demand-drivers`, {
      params: { weeks }
    }),

  // Search SKUs
  searchSkus: (query: string, limit: number = 20) =>
    apiClient.get('/api/v1/sku-detail/search', {
      params: { query, limit }
    })
}

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// API Types
export interface SKU {
  id: number
  item_id: string
  item_name: string
  category?: string
  subcategory?: string
  brand?: string
  unit_cost?: number
  unit_price?: number
  supplier?: string
  created_at: string
  updated_at?: string
}

export interface SalesData {
  id: number
  item_id: string
  week_ending: string
  units_sold: number
  revenue: number
  region?: string
  store_id?: string
  created_at: string
}

export interface Forecast {
  id: number
  item_id: string
  forecast_date: string
  forecast_period: string
  predicted_units?: number
  predicted_revenue?: number
  confidence_score?: number
  model_version?: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

// API Functions
export const skuApi = {
  getAll: (params?: { skip?: number; limit?: number; category?: string; brand?: string }) =>
    apiClient.get<SKU[]>('/api/v1/skus', { params }),
  
  getById: (itemId: string) =>
    apiClient.get<SKU>(`/api/v1/skus/${itemId}`),
  
  create: (sku: Omit<SKU, 'id' | 'created_at' | 'updated_at'>) =>
    apiClient.post<SKU>('/api/v1/skus', sku),
  
  update: (itemId: string, sku: Partial<SKU>) =>
    apiClient.put<SKU>(`/api/v1/skus/${itemId}`, sku),
  
  delete: (itemId: string) =>
    apiClient.delete(`/api/v1/skus/${itemId}`)
}

export const salesApi = {
  getAll: (params?: { 
    skip?: number; 
    limit?: number; 
    item_id?: string; 
    region?: string; 
    weeks_back?: number 
  }) =>
    apiClient.get<SalesData[]>('/api/v1/sales', { params }),
  
  getSummary: (weeksBack?: number) =>
    apiClient.get('/api/v1/sales/summary', { params: { weeks_back: weeksBack } }),
  
  getWeeklySales: (itemId: string, weeksBack?: number) =>
    apiClient.get<SalesData[]>(`/api/v1/sales/${itemId}/weekly`, { 
      params: { weeks_back: weeksBack } 
    }),
  
  create: (salesData: Omit<SalesData, 'id' | 'created_at'>) =>
    apiClient.post<SalesData>('/api/v1/sales', salesData),
  
  createBulk: (salesDataList: Omit<SalesData, 'id' | 'created_at'>[]) =>
    apiClient.post('/api/v1/sales/bulk', salesDataList)
}

export const forecastApi = {
  getAll: (params?: { 
    skip?: number; 
    limit?: number; 
    item_id?: string; 
    is_active?: boolean; 
    forecast_period?: string 
  }) =>
    apiClient.get<Forecast[]>('/api/v1/forecasts', { params }),
  
  getLatest: (itemId: string) =>
    apiClient.get<Forecast>(`/api/v1/forecasts/${itemId}/latest`),
  
  getHistory: (itemId: string, weeksBack?: number) =>
    apiClient.get<Forecast[]>(`/api/v1/forecasts/${itemId}/history`, { 
      params: { weeks_back: weeksBack } 
    }),
  
  getSummary: () =>
    apiClient.get('/api/v1/forecasts/summary'),
  
  create: (forecast: Omit<Forecast, 'id' | 'created_at' | 'updated_at'>) =>
    apiClient.post<Forecast>('/api/v1/forecasts', forecast),
  
  update: (forecastId: number, forecast: Partial<Forecast>) =>
    apiClient.put<Forecast>(`/api/v1/forecasts/${forecastId}`, forecast),
  
  delete: (forecastId: number) =>
    apiClient.delete(`/api/v1/forecasts/${forecastId}`)
}
