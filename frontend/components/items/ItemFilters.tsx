'use client'

import { useState } from 'react'

interface ItemFiltersProps {
  filters: {
    type: string
    quality: string
    level_min: string
    level_max: string
  }
  setFilters: (filters: any) => void
}

export default function ItemFilters({ filters, setFilters }: ItemFiltersProps) {
  const [expanded, setExpanded] = useState(false)
  
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>) => {
    const { name, value } = e.target
    
    setFilters({
      ...filters,
      [name]: value
    })
  }
  
  const itemTypes = [
    "Weapon",
    "Armor",
    "Accessory",
    "Crafting Material",
    "Gathering Resource",
    "Consumable",
    "Quest Item",
    "Tool",
    "Miscellaneous"
  ]
  
  const itemQualities = [
    "Common",
    "Uncommon",
    "Rare",
    "Epic",
    "Legendary",
    "Mythic"
  ]
  
  const clearFilters = () => {
    setFilters({
      type: '',
      quality: '',
      level_min: '',
      level_max: ''
    })
  }
  
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="flex items-center text-blue-600 dark:text-blue-400 hover:underline"
        >
          <span>{expanded ? 'Hide Filters' : 'Show Filters'}</span>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className={`ml-1 h-5 w-5 transition-transform ${expanded ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        
        {(filters.type || filters.quality || filters.level_min || filters.level_max) && (
          <button
            type="button"
            onClick={clearFilters}
            className="text-red-600 dark:text-red-400 hover:underline text-sm"
          >
            Clear Filters
          </button>
        )}
      </div>
      
      {expanded && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 pt-2 border-t border-gray-200 dark:border-gray-700">
          <div>
            <label htmlFor="type" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Item Type
            </label>
            <select
              id="type"
              name="type"
              value={filters.type}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
            >
              <option value="">All Types</option>
              {itemTypes.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label htmlFor="quality" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Quality
            </label>
            <select
              id="quality"
              name="quality"
              value={filters.quality}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
            >
              <option value="">All Qualities</option>
              {itemQualities.map((quality) => (
                <option key={quality} value={quality}>{quality}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label htmlFor="level_min" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Min Level
            </label>
            <input
              type="number"
              id="level_min"
              name="level_min"
              value={filters.level_min}
              onChange={handleChange}
              min="0"
              max="50"
              placeholder="0"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
            />
          </div>
          
          <div>
            <label htmlFor="level_max" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Max Level
            </label>
            <input
              type="number"
              id="level_max"
              name="level_max"
              value={filters.level_max}
              onChange={handleChange}
              min="0"
              max="50"
              placeholder="50"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
            />
          </div>
        </div>
      )}
    </div>
  )
}
