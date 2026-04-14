import { ReactNode } from 'react'
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/solid'

interface StatsCardProps {
  title: string
  value: string
  icon: ReactNode
  trend?: string
  trendDirection?: 'up' | 'down' | 'neutral'
}

export default function StatsCard({ 
  title, 
  value, 
  icon, 
  trend, 
  trendDirection = 'neutral' 
}: StatsCardProps) {
  const getTrendColor = () => {
    switch (trendDirection) {
      case 'up':
        return 'text-green-600'
      case 'down':
        return 'text-red-600'
      default:
        return 'text-gray-500'
    }
  }

  const getTrendIcon = () => {
    switch (trendDirection) {
      case 'up':
        return <ArrowUpIcon className="h-4 w-4" />
      case 'down':
        return <ArrowDownIcon className="h-4 w-4" />
      default:
        return null
    }
  }

  return (
    <div className="card">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <div className="p-3 bg-primary-50 rounded-lg">
            <div className="text-primary-600">
              {icon}
            </div>
          </div>
        </div>
        <div className="ml-4 flex-1">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
          {trend && (
            <div className={`flex items-center mt-1 ${getTrendColor()}`}>
              {getTrendIcon()}
              <span className="text-sm font-medium ml-1">{trend}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
