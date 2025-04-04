'use client'

import { useState } from 'react'

type ResourceType = {
  id: string
  name: string
  color: string
  icon: string
}

interface ResourceFiltersProps {
  filters: {
    types: string[]
    zone: string
    searchQuery: string
  }
  setFilters: (filters: any) => void
  resourceTypes: ResourceType[]
}

export default function ResourceFilters({ filters, setFilters, resourceTypes }: ResourceFiltersProps) {
  const [expanded, setExpanded] = useState(false)
  
  // Toggle resource type filter
  const toggleTypeFilter = (typeName: string) => {
    const currentTypes = [...filters.types]
    
    if (currentTypes.includes(typeName)) {
      // Remove from filters
      setFilters({
        ...filters,
        types: currentTypes.filter(t => t !== typeName)
      })
    } else {
      // Add to filters
      setFilters({
        ...filters,
        types: [...currentTypes, typeName]
      })
    }
  }
  
  // Update zone filter
  const handleZoneChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFilters({
      ...filters,
      zone: e.target.value
    })
  }
  
  // Update search query
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilters({
      ...filters,
      searchQuery: e.target.value
    })
  }
  
  // Clear all filters
  const clearFilters = () => {
    setFilters({
      types: [],
      zone: '',
      searchQuery: ''
    })
  }
  
  // Zone options (hardcoded for now, would come from API in real implementation)
  const zoneOptions = [
    "Riverlands",
    "Tropical Jungle",
    "Desert",
    "Forest",
    "Mountains",
    "Plains",
    "Swamp",
    "Tundra",
    "Underground"
  ]
  
  return (
    <div className="space-y-4">
      {/* Search input */}
      <div>
        <label htmlFor="search" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Search
        </label>
        <input
          id="search"
          type="text"
          placeholder="Search resources..."
          value={filters.searchQuery}
          onChange={handleSearchChange}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
        />
      </div>
      
      {/* Zone selector */}
      <div>
        <label htmlFor="zone" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Zone
        </label>
        <select
          id="zone"
          value={filters.zone}
          onChange={handleZoneChange}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
        >
          <option value="">All Zones</option>
          {zoneOptions.map(zone => (
            <option key={zone} value={zone}>{zone}</option>
          ))}
        </select>
      </div>
      
      {/* Resource type filters */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Resource Types
          </label>
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            {expanded ? 'Collapse' : 'Expand'}
          </button>
        </div>
        
        <div className={`grid grid-cols-2 gap-2 ${expanded ? '' : 'max-h-24 overflow-y-auto'}`}>
          {resourceTypes.map(type => (
            <label
              key={type.id}
              className="flex items-center space-x-2 cursor-pointer py-1"
            >
              <input
                type="checkbox"
                checked={filters.types.includes(type.name)}
                onChange={() => toggleTypeFilter(type.name)}
                className="rounded border-gray-300 text-blue-600 dark:text-blue-400 dark:bg-gray-700 focus:ring-blue-500 dark:focus:ring-blue-600"
              />
              <div className="flex items-center">
                <span
                  className="w-3 h-3 rounded-full mr-1"
                  style={{ backgroundColor: type.color }}
                ></span>
                <span className="text-sm text-gray-700 dark:text-gray-300">{type.name}</span>
              </div>
            </label>
          ))}
        </div>
      </div>
      
      {/* Clear filters button (shown only when filters are active) */}
      {(filters.types.length > 0 || filters.zone || filters.searchQuery) && (
        <div className="pt-2">
          <button
            type="button"
            onClick={clearFilters}
            className="w-full px-3 py-2 text-sm text-red-600 dark:text-red-400 border border-red-200 dark:border-red-900 rounded-md hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
          >
            Clear Filters
          </button>
        </div>
      )}
    </div>
  )
}
