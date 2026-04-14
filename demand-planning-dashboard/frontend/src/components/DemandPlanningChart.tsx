'use client'

import { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Brush,
  ReferenceLine
} from 'recharts'
import { format, parseISO } from 'date-fns'

interface TimelineData {
  week_ending: string
  total_units: number
  total_revenue: number
  active_skus: number
  confidence_score?: number
  type: 'historical' | 'forecast'
}

interface DemandPlanningChartProps {
  data: TimelineData[]
  loading?: boolean
  height?: number
}

const DemandPlanningChart = ({ 
  data, 
  loading = false, 
  height = 400 
}: DemandPlanningChartProps) => {
  const [selectedMetric, setSelectedMetric] = useState<'units' | 'revenue'>('units')
  const [showConfidence, setShowConfidence] = useState(true)

  // Process data for chart
  const chartData = data.map((item, index) => ({
    ...item,
    date: format(parseISO(item.week_ending), 'MMM dd'),
    fullDate: item.week_ending,
    index,
    // Split data by type for different styling
    historicalUnits: item.type === 'historical' ? item.total_units : null,
    forecastUnits: item.type === 'forecast' ? item.total_units : null,
    historicalRevenue: item.type === 'historical' ? item.total_revenue : null,
    forecastRevenue: item.type === 'forecast' ? item.total_revenue : null,
    confidence: item.confidence_score ? item.confidence_score * 100 : null
  }))

  // Find the boundary between historical and forecast data
  const boundaryIndex = chartData.findIndex(item => item.type === 'forecast')

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900">{`Week ending: ${format(parseISO(data.fullDate), 'MMM dd, yyyy')}`}</p>
          <p className="text-sm text-gray-600 mb-2">{`Type: ${data.type}`}</p>
          
          {selectedMetric === 'units' ? (
            <p className="text-blue-600">{`Units: ${data.total_units.toLocaleString()}`}</p>
          ) : (
            <p className="text-green-600">{`Revenue: $${data.total_revenue.toLocaleString()}`}</p>
          )}
          
          <p className="text-purple-600">{`Active SKUs: ${data.active_skus}`}</p>
          
          {data.type === 'forecast' && data.confidence && (
            <p className="text-orange-600">{`Confidence: ${data.confidence.toFixed(1)}%`}</p>
          )}
        </div>
      )
    }
    return null
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Chart Controls */}
      <div className="flex flex-wrap items-center gap-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">Metric:</label>
          <select
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value as 'units' | 'revenue')}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="units">Units Sold</option>
            <option value="revenue">Revenue</option>
          </select>
        </div>
        
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="showConfidence"
            checked={showConfidence}
            onChange={(e) => setShowConfidence(e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <label htmlFor="showConfidence" className="text-sm font-medium text-gray-700">
            Show Confidence Score
          </label>
        </div>

        <div className="flex items-center gap-4 ml-auto">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span className="text-sm text-gray-600">Historical</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-sm text-gray-600">Forecast</span>
          </div>
          {showConfidence && (
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
              <span className="text-sm text-gray-600">Confidence %</span>
            </div>
          )}
        </div>
      </div>

      {/* Chart */}
      <div className="bg-white p-4 rounded-lg border">
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="date" 
              stroke="#666"
              fontSize={12}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis 
              stroke="#666"
              fontSize={12}
              tickFormatter={(value) => 
                selectedMetric === 'revenue' 
                  ? `$${(value / 1000).toFixed(0)}K`
                  : value.toLocaleString()
              }
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />

            {/* Reference line to separate historical from forecast */}
            {boundaryIndex > 0 && (
              <ReferenceLine 
                x={chartData[boundaryIndex - 1]?.date} 
                stroke="#ff6b6b" 
                strokeDasharray="5 5"
                label={{ value: "Today", position: "top" }}
              />
            )}

            {/* Historical data line */}
            <Line
              type="monotone"
              dataKey={selectedMetric === 'units' ? 'historicalUnits' : 'historicalRevenue'}
              stroke="#3b82f6"
              strokeWidth={3}
              dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
              connectNulls={false}
              name={`Historical ${selectedMetric === 'units' ? 'Units' : 'Revenue'}`}
            />

            {/* Forecast data line */}
            <Line
              type="monotone"
              dataKey={selectedMetric === 'units' ? 'forecastUnits' : 'forecastRevenue'}
              stroke="#10b981"
              strokeWidth={3}
              strokeDasharray="8 4"
              dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
              connectNulls={false}
              name={`Forecast ${selectedMetric === 'units' ? 'Units' : 'Revenue'}`}
            />

            {/* Confidence score line (right axis) */}
            {showConfidence && (
              <Line
                type="monotone"
                dataKey="confidence"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={{ fill: '#f59e0b', strokeWidth: 1, r: 3 }}
                connectNulls={false}
                name="Confidence %"
                yAxisId="confidence"
              />
            )}

            {/* Secondary Y-axis for confidence */}
            {showConfidence && (
              <YAxis 
                yAxisId="confidence"
                orientation="right"
                stroke="#f59e0b"
                fontSize={12}
                domain={[0, 100]}
                tickFormatter={(value) => `${value}%`}
              />
            )}

            {/* Brush for zooming */}
            <Brush 
              dataKey="date" 
              height={30} 
              stroke="#8884d8"
              fill="#f0f0f0"
              startIndex={Math.max(0, chartData.length - 20)} // Show last 20 weeks by default
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Chart Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div className="bg-blue-50 p-3 rounded-lg">
          <div className="font-semibold text-blue-900">Historical Period</div>
          <div className="text-blue-700">
            {chartData.filter(d => d.type === 'historical').length} weeks of data
          </div>
        </div>
        <div className="bg-green-50 p-3 rounded-lg">
          <div className="font-semibold text-green-900">Forecast Period</div>
          <div className="text-green-700">
            {chartData.filter(d => d.type === 'forecast').length} weeks projected
          </div>
        </div>
        <div className="bg-orange-50 p-3 rounded-lg">
          <div className="font-semibold text-orange-900">Avg Confidence</div>
          <div className="text-orange-700">
            {chartData.filter(d => d.confidence).length > 0 
              ? `${(chartData.filter(d => d.confidence).reduce((sum, d) => sum + (d.confidence || 0), 0) / chartData.filter(d => d.confidence).length).toFixed(1)}%`
              : 'N/A'
            }
          </div>
        </div>
      </div>
    </div>
  )
}

export default DemandPlanningChart
