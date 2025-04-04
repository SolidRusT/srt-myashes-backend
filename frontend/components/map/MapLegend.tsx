'use client'

import { useState } from 'react'

type ResourceType = {
  id: string
  name: string
  color: string
  icon: string
}

interface MapLegendProps {
  resourceTypes: ResourceType[]
}

export default function MapLegend({ resourceTypes }: MapLegendProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  
  return (
    <div className={`absolute bottom-4 left-4 z-20 bg-white dark:bg-gray-800 rounded-lg shadow-md transition-all overflow-hidden ${
      isExpanded ? 'max-h-80' : 'max-h-10'
    }`}>
      <div 
        className="px-4 py-2 cursor-pointer flex items-center justify-between border-b border-gray-200 dark:border-gray-700"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className="font-medium text-sm dark:text-white">Map Legend</span>
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          className={`h-4 w-4 text-gray-600 dark:text-gray-400 transition-transform ${
            isExpanded ? 'transform rotate-180' : ''
          }`} 
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
      
      <div className="p-3">
        <div className="grid grid-cols-2 gap-x-6 gap-y-2">
          {resourceTypes.map(type => (
            <div key={type.id} className="flex items-center">
              <span 
                className="w-3 h-3 rounded-full mr-2"
                style={{ backgroundColor: type.color }}
              ></span>
              <span className="text-xs text-gray-700 dark:text-gray-300">{type.name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
