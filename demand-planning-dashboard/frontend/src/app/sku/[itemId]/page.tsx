'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeftIcon, ChartBarIcon } from '@heroicons/react/24/outline'
import SkuTimelineChart from '@/components/SkuTimelineChart'
import DemandDriversPanel from '@/components/DemandDriversPanel'
import { skuDetailAPI } from '@/lib/api'

interface SkuDetails {
  sku_info: {
    item_id: string
    item_name: string
    category: string
    brand: string
    unit_cost: number | null
    supplier: string
    created_at: string | null
  }
  sales_summary: {
    total_units_sold: number
    total_revenue: number
    total_transactions: number
    avg_price: number
    first_sale_date: string | null
    last_sale_date: string | null
  }
  forecast_summary: {
    total_predicted_units: number
    total_predicted_revenue: number
    avg_confidence: number
    total_forecasts: number
  }
}

interface TimelineData {
  week_ending: string
  units: number
  revenue: number
  avg_unit_price: number
  cust_instock: number
  confidence_score?: number
  type: 'historical' | 'forecast'
}

interface PreviousYearData {
  week_ending: string
  original_week_ending: string
  units: number
  revenue: number
  type: 'previous_year'
}

interface DemandDriverData {
  week_ending: string
  avg_unit_price: number
  cust_instock: number
  units_sold: number | null
  type: 'historical' | 'projected'
}

export default function SkuDetailPage() {
  const params = useParams()
  const router = useRouter()
  const itemId = params.itemId as string

  const [skuDetails, setSkuDetails] = useState<SkuDetails | null>(null)
  const [timelineData, setTimelineData] = useState<TimelineData[]>([])
  const [previousYearData, setPreviousYearData] = useState<PreviousYearData[]>([])
  const [demandDriversData, setDemandDriversData] = useState<DemandDriverData[]>([])
  
  const [loading, setLoading] = useState(true)
  const [timelineLoading, setTimelineLoading] = useState(true)
  const [previousYearLoading, setPreviousYearLoading] = useState(true)
  const [demandDriversLoading, setDemandDriversLoading] = useState(true)
  
  const [showDemandDrivers, setShowDemandDrivers] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!itemId) return

    const fetchSkuData = async () => {
      try {
        // Fetch SKU details
        const detailsResponse = await skuDetailAPI.getSkuDetails(itemId)
        setSkuDetails(detailsResponse.data)
        setLoading(false)
      } catch (error) {
        console.error('Failed to fetch SKU details:', error)
        setError('Failed to load SKU details')
        setLoading(false)
      }
    }

    const fetchTimelineData = async () => {
      try {
        const response = await skuDetailAPI.getSkuTimeline(itemId, 13, 39)
        setTimelineData(response.data.timeline_data)
        setTimelineLoading(false)
      } catch (error) {
        console.error('Failed to fetch timeline data:', error)
        setTimelineLoading(false)
      }
    }

    const fetchPreviousYearData = async () => {
      try {
        const response = await skuDetailAPI.getPreviousYearData(itemId, 52)
        setPreviousYearData(response.data.previous_year_data)
        setPreviousYearLoading(false)
      } catch (error) {
        console.error('Failed to fetch previous year data:', error)
        setPreviousYearLoading(false)
      }
    }

    const fetchDemandDrivers = async () => {
      try {
        const response = await skuDetailAPI.getDemandDrivers(itemId, 52)
        setDemandDriversData(response.data.demand_drivers_data)
        setDemandDriversLoading(false)
      } catch (error) {
        console.error('Failed to fetch demand drivers:', error)
        setDemandDriversLoading(false)
      }
    }

    fetchSkuData()
    fetchTimelineData()
    fetchPreviousYearData()
    fetchDemandDrivers()
  }, [itemId])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error || !skuDetails) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">SKU Not Found</h1>
          <p className="text-gray-600 mb-4">{error || `SKU ${itemId} could not be found.`}</p>
          <button
            onClick={() => router.push('/')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center gap-4 mb-4">
              <button
                onClick={() => router.push('/')}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <ArrowLeftIcon className="h-5 w-5 text-gray-600" />
              </button>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  SKU Detail: Demand Planning Workbench
                </h1>
                <p className="mt-1 text-sm text-gray-600">
                  Comprehensive analysis for {skuDetails.sku_info.item_name} ({skuDetails.sku_info.item_id})
                </p>
              </div>
              <div className="ml-auto">
                <button
                  onClick={() => setShowDemandDrivers(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <ChartBarIcon className="h-5 w-5" />
                  Demand Drivers
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* SKU Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
                      <span className="text-white text-sm font-medium">📦</span>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Total Units Sold</dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {skuDetails.sales_summary.total_units_sold.toLocaleString()}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                      <span className="text-white text-sm font-medium">💰</span>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Total Revenue</dt>
                      <dd className="text-lg font-medium text-gray-900">
                        ${skuDetails.sales_summary.total_revenue.toLocaleString()}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-purple-500 rounded-md flex items-center justify-center">
                      <span className="text-white text-sm font-medium">📊</span>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Avg Price</dt>
                      <dd className="text-lg font-medium text-gray-900">
                        ${skuDetails.sales_summary.avg_price.toFixed(2)}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-orange-500 rounded-md flex items-center justify-center">
                      <span className="text-white text-sm font-medium">🔮</span>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Forecast Confidence</dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {(skuDetails.forecast_summary.avg_confidence * 100).toFixed(1)}%
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* SKU Information */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">SKU Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">Category</dt>
                <dd className="mt-1 text-sm text-gray-900">{skuDetails.sku_info.category || 'N/A'}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Brand</dt>
                <dd className="mt-1 text-sm text-gray-900">{skuDetails.sku_info.brand || 'N/A'}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Supplier</dt>
                <dd className="mt-1 text-sm text-gray-900">{skuDetails.sku_info.supplier || 'N/A'}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Unit Cost</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {skuDetails.sku_info.unit_cost ? `$${skuDetails.sku_info.unit_cost.toFixed(2)}` : 'N/A'}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Total Transactions</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {skuDetails.sales_summary.total_transactions.toLocaleString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Total Forecasts</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {skuDetails.forecast_summary.total_forecasts.toLocaleString()}
                </dd>
              </div>
            </div>
          </div>

          {/* 52-Week Timeline Chart */}
          <div className="bg-white shadow rounded-lg p-6">
            <SkuTimelineChart
              timelineData={timelineData}
              previousYearData={previousYearData}
              loading={timelineLoading || previousYearLoading}
              height={500}
              itemId={skuDetails.sku_info.item_id}
              itemName={skuDetails.sku_info.item_name}
            />
          </div>

          {/* Performance Summary */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Sales Performance</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">First Sale Date:</span>
                  <span className="text-sm font-medium text-gray-900">
                    {skuDetails.sales_summary.first_sale_date 
                      ? new Date(skuDetails.sales_summary.first_sale_date).toLocaleDateString()
                      : 'N/A'
                    }
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Last Sale Date:</span>
                  <span className="text-sm font-medium text-gray-900">
                    {skuDetails.sales_summary.last_sale_date 
                      ? new Date(skuDetails.sales_summary.last_sale_date).toLocaleDateString()
                      : 'N/A'
                    }
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Historical Weeks:</span>
                  <span className="text-sm font-medium text-gray-900">
                    {timelineData.filter(d => d.type === 'historical').length} weeks
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Forecast Performance</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Predicted Units:</span>
                  <span className="text-sm font-medium text-gray-900">
                    {skuDetails.forecast_summary.total_predicted_units.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Predicted Revenue:</span>
                  <span className="text-sm font-medium text-gray-900">
                    ${skuDetails.forecast_summary.total_predicted_revenue.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Forecast Weeks:</span>
                  <span className="text-sm font-medium text-gray-900">
                    {timelineData.filter(d => d.type === 'forecast').length} weeks
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Demand Drivers Side Panel */}
      <DemandDriversPanel
        isOpen={showDemandDrivers}
        onClose={() => setShowDemandDrivers(false)}
        demandDriversData={demandDriversData}
        loading={demandDriversLoading}
        itemId={skuDetails.sku_info.item_id}
        itemName={skuDetails.sku_info.item_name}
      />
    </div>
  )
}
