'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import { skuDetailAPI } from '@/lib/api'

interface SearchResult {
  item_id: string
  item_name: string
  category: string
  brand: string
  total_units_sold: number
  total_revenue: number
}

interface SkuSearchBarProps {
  placeholder?: string
  className?: string
}

const SkuSearchBar = ({ 
  placeholder = "Search SKUs by name or ID...", 
  className = "" 
}: SkuSearchBarProps) => {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const searchRef = useRef<HTMLDivElement>(null)
  const router = useRouter()

  // Debounced search
  useEffect(() => {
    if (query.length < 2) {
      setResults([])
      setIsOpen(false)
      return
    }

    const timeoutId = setTimeout(async () => {
      setLoading(true)
      try {
        const response = await skuDetailAPI.searchSkus(query, 10)
        setResults(response.data.results)
        setIsOpen(true)
      } catch (error) {
        console.error('Search failed:', error)
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 300)

    return () => clearTimeout(timeoutId)
  }, [query])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelectSku = (itemId: string) => {
    setQuery('')
    setIsOpen(false)
    router.push(`/sku/${itemId}`)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (results.length > 0) {
      handleSelectSku(results[0].item_id)
    }
  }

  return (
    <div ref={searchRef} className={`relative ${className}`}>
      <form onSubmit={handleSubmit}>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            placeholder={placeholder}
          />
          {loading && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            </div>
          )}
        </div>
      </form>

      {/* Search Results Dropdown */}
      {isOpen && (
        <div className="absolute z-50 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm">
          {results.length === 0 ? (
            <div className="px-4 py-2 text-gray-500">
              {loading ? 'Searching...' : 'No SKUs found'}
            </div>
          ) : (
            results.map((result) => (
              <button
                key={result.item_id}
                onClick={() => handleSelectSku(result.item_id)}
                className="w-full text-left px-4 py-2 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900 truncate">
                        {result.item_name}
                      </span>
                      <span className="text-xs text-gray-500">
                        ({result.item_id})
                      </span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {result.category && `${result.category} • `}
                      {result.brand && `${result.brand} • `}
                      {result.total_units_sold.toLocaleString()} units sold
                    </div>
                  </div>
                  <div className="text-xs text-gray-400">
                    ${result.total_revenue.toLocaleString()}
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  )
}

export default SkuSearchBar
