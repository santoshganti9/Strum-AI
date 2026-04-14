'use client'

import { useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts'
import { format, parseISO } from 'date-fns'
import { XMarkIcon, ChartBarIcon } from '@heroicons/react/24/outline'

interface DemandDriverData {
  week_ending: string
  avg_unit_price: number
  cust_instock: number
  units_sold: number | null
  type: 'historical' | 'projected'
}

interface DemandDriversPanelProps {
  isOpen: boolean
  onClose: () => void
  demandDriversData: DemandDriverData[]
  loading?: boolean
  itemId: string
  itemName: string
}

const DemandDriversPanel = ({
  isOpen,
  onClose,
  demandDriversData,
  loading = false,
  itemId,
  itemName
}: DemandDriversPanelProps) => {
  const [selectedDriver, setSelectedDriver] = useState<'price' | 'stock' | 'both'>('both')

  // Process data for chart
  const chartData = demandDriversData.map(item => ({
    ...item,
    date: format(parseISO(item.week_ending), 'MMM dd'),
    fullDate: item.week_ending,
    // Split data by type for different styling
    historicalPrice: item.type === 'historical' ? item.avg_unit_price : null,
    projectedPrice: item.type === 'projected' ? item.avg_unit_price : null,
    historicalStock: item.type === 'historical' ? item.cust_instock * 100 : null, // Convert to percentage
    projectedStock: item.type === 'projected' ? item.cust_instock * 100 : null,
    stockPercentage: item.cust_instock * 100
  }))

  // Find the boundary between historical and projected data
  const boundaryIndex = chartData.findIndex(item => item.type === 'projected')

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg text-sm">
          <p className="font-semibold text-gray-900">{`Week: ${format(parseISO(data.fullDate), 'MMM dd, yyyy')}`}</p>
          <p className="text-xs text-gray-600 mb-2">{`Type: ${data.type}`}</p>
          
          <p className="text-blue-600">{`Avg Unit Price: $${data.avg_unit_price.toFixed(2)}`}</p>
          <p className="text-green-600">{`Customer In-Stock: ${data.stockPercentage.toFixed(1)}%`}</p>
          
          {data.units_sold !== null && (
            <p className="text-purple-600">{`Units Sold: ${data.units_sold.toLocaleString()}`}</p>
          )}
        </div>
      )
    }
    return null
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-xl border-l border-gray-200 z-50 flex flex-col">
      {/* Panel Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <ChartBarIcon className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Demand Drivers</h3>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-100 rounded-full transition-colors"
        >
          <XMarkIcon className="h-5 w-5 text-gray-500" />
        </button>
      </div>

      {/* SKU Info */}
      <div className="p-4 bg-gray-50 border-b border-gray-200">
        <h4 className="font-medium text-gray-900">{itemName}</h4>
        <p className="text-sm text-gray-600">{itemId}</p>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          {/* Controls */}
          <div className="p-4 border-b border-gray-200">
            <label className="block text-sm font-medium text-gray-700 mb-2">Display:</label>
            <select
              value={selectedDriver}
              onChange={(e) => setSelectedDriver(e.target.value as 'price' | 'stock' | 'both')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="both">Both Drivers</option>
              <option value="price">Price Only</option>
              <option value="stock">Stock Level Only</option>
            </select>
          </div>

          {/* Chart */}
          <div className="p-4">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis 
                  dataKey="date" 
                  stroke="#666"
                  fontSize={10}
                  angle={-45}
                  textAnchor="end"
                  height={50}
                />
                
                {/* Left Y-axis for price */}
                {(selectedDriver === 'price' || selectedDriver === 'both') && (
                  <YAxis 
                    yAxisId="price"
                    stroke="#3b82f6"
                    fontSize={10}
                    tickFormatter={(value) => `$${value.toFixed(1)}`}
                  />
                )}
                
                {/* Right Y-axis for stock percentage */}
                {(selectedDriver === 'stock' || selectedDriver === 'both') && (
                  <YAxis 
                    yAxisId="stock"
                    orientation="right"
                    stroke="#10b981"
                    fontSize={10}
                    domain={[0, 100]}
                    tickFormatter={(value) => `${value}%`}
                  />
                )}
                
                <Tooltip content={<CustomTooltip />} />
                <Legend fontSize={10} />

                {/* Reference line to separate historical from projected */}
                {boundaryIndex > 0 && (
                  <ReferenceLine 
                    x={chartData[boundaryIndex - 1]?.date} 
                    stroke="#ff6b6b" 
                    strokeDasharray="3 3"
                    strokeWidth={1}
                  />
                )}

                {/* Price lines */}
                {(selectedDriver === 'price' || selectedDriver === 'both') && (
                  <>
                    <Line
                      yAxisId="price"
                      type="monotone"
                      dataKey="historicalPrice"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={{ fill: '#3b82f6', strokeWidth: 1, r: 2 }}
                      connectNulls={false}
                      name="Historical Price"
                    />
                    <Line
                      yAxisId="price"
                      type="monotone"
                      dataKey="projectedPrice"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      strokeDasharray="4 2"
                      dot={{ fill: '#3b82f6', strokeWidth: 1, r: 2 }}
                      connectNulls={false}
                      name="Projected Price"
                    />
                  </>
                )}

                {/* Stock level lines */}
                {(selectedDriver === 'stock' || selectedDriver === 'both') && (
                  <>
                    <Line
                      yAxisId="stock"
                      type="monotone"
                      dataKey="historicalStock"
                      stroke="#10b981"
                      strokeWidth={2}
                      dot={{ fill: '#10b981', strokeWidth: 1, r: 2 }}
                      connectNulls={false}
                      name="Historical Stock %"
                    />
                    <Line
                      yAxisId="stock"
                      type="monotone"
                      dataKey="projectedStock"
                      stroke="#10b981"
                      strokeWidth={2}
                      strokeDasharray="4 2"
                      dot={{ fill: '#10b981', strokeWidth: 1, r: 2 }}
                      connectNulls={false}
                      name="Projected Stock %"
                    />
                  </>
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Summary Stats */}
          <div className="p-4 border-t border-gray-200">
            <h5 className="font-medium text-gray-900 mb-3">Summary Statistics</h5>
            
            <div className="space-y-3">
              {/* Price Stats */}
              <div className="bg-blue-50 p-3 rounded-lg">
                <div className="text-sm font-medium text-blue-900">Average Unit Price</div>
                <div className="text-xs text-blue-700 mt-1">
                  Current: ${chartData[chartData.length - 1]?.avg_unit_price.toFixed(2) || 'N/A'}
                </div>
                <div className="text-xs text-blue-700">
                  Range: ${Math.min(...chartData.map(d => d.avg_unit_price)).toFixed(2)} - 
                  ${Math.max(...chartData.map(d => d.avg_unit_price)).toFixed(2)}
                </div>
              </div>

              {/* Stock Stats */}
              <div className="bg-green-50 p-3 rounded-lg">
                <div className="text-sm font-medium text-green-900">Customer In-Stock</div>
                <div className="text-xs text-green-700 mt-1">
                  Current: {chartData[chartData.length - 1]?.stockPercentage.toFixed(1) || 'N/A'}%
                </div>
                <div className="text-xs text-green-700">
                  Range: {Math.min(...chartData.map(d => d.stockPercentage)).toFixed(1)}% - 
                  {Math.max(...chartData.map(d => d.stockPercentage)).toFixed(1)}%
                </div>
              </div>

              {/* Data Coverage */}
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-sm font-medium text-gray-900">Data Coverage</div>
                <div className="text-xs text-gray-700 mt-1">
                  Historical: {chartData.filter(d => d.type === 'historical').length} weeks
                </div>
                <div className="text-xs text-gray-700">
                  Projected: {chartData.filter(d => d.type === 'projected').length} weeks
                </div>
              </div>
            </div>
          </div>

          {/* Legend */}
          <div className="p-4 border-t border-gray-200 bg-gray-50">
            <h5 className="font-medium text-gray-900 mb-2 text-sm">Legend</h5>
            <div className="space-y-1 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-3 h-0.5 bg-blue-500"></div>
                <span className="text-gray-600">Average Unit Price ($)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-0.5 bg-green-500"></div>
                <span className="text-gray-600">Customer In-Stock (%)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-0.5 bg-gray-400 border-dashed border-t"></div>
                <span className="text-gray-600">Projected Values</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DemandDriversPanel
