'use client'

import { useState, useEffect } from 'react'
import { ExclamationTriangleIcon, InformationCircleIcon } from '@heroicons/react/24/outline'

interface Alert {
  item_id: string
  item_name: string
  alert_type: 'low_confidence' | 'high_variance'
  severity: 'high' | 'medium' | 'low'
  message: string
  confidence_score?: number
  variance?: number
  avg_predicted_units?: number
  forecast_count: number
  predicted_units?: number
}

interface ForecastAlertsProps {
  alerts: Alert[]
  loading?: boolean
  onAlertClick?: (alert: Alert) => void
}

const ForecastAlerts = ({ 
  alerts, 
  loading = false, 
  onAlertClick 
}: ForecastAlertsProps) => {
  const [filter, setFilter] = useState<'all' | 'high' | 'medium'>('all')
  const [sortBy, setSortBy] = useState<'severity' | 'confidence' | 'name'>('severity')

  // Filter and sort alerts
  const filteredAlerts = alerts
    .filter(alert => filter === 'all' || alert.severity === filter)
    .sort((a, b) => {
      switch (sortBy) {
        case 'severity':
          const severityOrder = { high: 0, medium: 1, low: 2 }
          return severityOrder[a.severity] - severityOrder[b.severity]
        case 'confidence':
          return (a.confidence_score || 0) - (b.confidence_score || 0)
        case 'name':
          return a.item_name.localeCompare(b.item_name)
        default:
          return 0
      }
    })

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
      case 'medium':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />
      default:
        return <InformationCircleIcon className="h-5 w-5 text-blue-500" />
    }
  }

  const getSeverityBadge = (severity: string) => {
    const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
    switch (severity) {
      case 'high':
        return `${baseClasses} bg-red-100 text-red-800`
      case 'medium':
        return `${baseClasses} bg-yellow-100 text-yellow-800`
      default:
        return `${baseClasses} bg-blue-100 text-blue-800`
    }
  }

  const getAlertTypeBadge = (alertType: string) => {
    switch (alertType) {
      case 'low_confidence':
        return 'bg-orange-100 text-orange-800'
      case 'high_variance':
        return 'bg-purple-100 text-purple-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg border p-6">
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Forecast Accuracy Alerts</h3>
            <p className="text-sm text-gray-600 mt-1">
              Items requiring attention based on forecast confidence and variance
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">
              {filteredAlerts.length} of {alerts.length} alerts
            </span>
          </div>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-4 mt-4">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Filter:</label>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as any)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Alerts</option>
              <option value="high">High Severity</option>
              <option value="medium">Medium Severity</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Sort by:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="severity">Severity</option>
              <option value="confidence">Confidence</option>
              <option value="name">Item Name</option>
            </select>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="divide-y divide-gray-200">
        {filteredAlerts.length === 0 ? (
          <div className="p-6 text-center">
            <InformationCircleIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h4 className="text-lg font-medium text-gray-900 mb-2">No alerts found</h4>
            <p className="text-gray-600">
              {filter === 'all' 
                ? "All forecasts are performing well!" 
                : `No ${filter} severity alerts at this time.`
              }
            </p>
          </div>
        ) : (
          filteredAlerts.map((alert, index) => (
            <div
              key={`${alert.item_id}-${alert.alert_type}-${index}`}
              className={`p-4 hover:bg-gray-50 transition-colors ${
                onAlertClick ? 'cursor-pointer' : ''
              }`}
              onClick={() => onAlertClick?.(alert)}
            >
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 mt-1">
                  {getSeverityIcon(alert.severity)}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="text-sm font-medium text-gray-900 truncate">
                      {alert.item_name}
                    </h4>
                    <span className="text-xs text-gray-500">({alert.item_id})</span>
                  </div>

                  <p className="text-sm text-gray-700 mb-2">{alert.message}</p>

                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <span className={getSeverityBadge(alert.severity)}>
                      {alert.severity.toUpperCase()}
                    </span>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getAlertTypeBadge(alert.alert_type)}`}>
                      {alert.alert_type.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-gray-600">
                    {alert.confidence_score !== undefined && (
                      <div>
                        <span className="font-medium">Confidence:</span>
                        <span className="ml-1">{(alert.confidence_score * 100).toFixed(1)}%</span>
                      </div>
                    )}
                    {alert.predicted_units !== undefined && (
                      <div>
                        <span className="font-medium">Predicted Units:</span>
                        <span className="ml-1">{alert.predicted_units.toLocaleString()}</span>
                      </div>
                    )}
                    {alert.avg_predicted_units !== undefined && (
                      <div>
                        <span className="font-medium">Avg Units:</span>
                        <span className="ml-1">{alert.avg_predicted_units.toLocaleString()}</span>
                      </div>
                    )}
                    <div>
                      <span className="font-medium">Forecasts:</span>
                      <span className="ml-1">{alert.forecast_count}</span>
                    </div>
                  </div>
                </div>

                {onAlertClick && (
                  <div className="flex-shrink-0">
                    <button className="text-gray-400 hover:text-gray-600">
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Summary Footer */}
      {alerts.length > 0 && (
        <div className="p-4 bg-gray-50 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-4">
              <span className="text-gray-600">
                High: <span className="font-medium text-red-600">
                  {alerts.filter(a => a.severity === 'high').length}
                </span>
              </span>
              <span className="text-gray-600">
                Medium: <span className="font-medium text-yellow-600">
                  {alerts.filter(a => a.severity === 'medium').length}
                </span>
              </span>
              <span className="text-gray-600">
                Low: <span className="font-medium text-blue-600">
                  {alerts.filter(a => a.severity === 'low').length}
                </span>
              </span>
            </div>
            <div className="text-gray-500">
              Last updated: {new Date().toLocaleTimeString()}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ForecastAlerts
