'use client'

import Link from 'next/link'

// Types
type Resource = {
  id: string
  name: string
  type: string
  locations: Array<{zone: string, coordinates?: string}>
  level?: string
}

interface PopularResourcesCardProps {
  resources: Resource[]
}

export default function PopularResourcesCard({ resources = [] }: PopularResourcesCardProps) {
  // If no resources passed, show some defaults
  const defaultResources = [
    { id: 'iron-ore', name: 'Iron Ore', type: 'Mining Resource', locations: [{ zone: 'Riverlands' }] },
    { id: 'oak-wood', name: 'Oak Wood', type: 'Lumber Resource', locations: [{ zone: 'Riverlands' }] },
    { id: 'cotton', name: 'Cotton', type: 'Harvesting Resource', locations: [{ zone: 'Grasslands' }] },
    { id: 'silver-ore', name: 'Silver Ore', type: 'Mining Resource', locations: [{ zone: 'Highlands' }] },
    { id: 'herbs', name: 'Medicinal Herbs', type: 'Gathering Resource', locations: [{ zone: 'Forest' }] }
  ]
  
  const displayResources = resources.length > 0 ? resources : defaultResources
  
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold dark:text-white">Popular Resources</h2>
        <Link
          href="/locations/resources"
          className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
        >
          View All
        </Link>
      </div>
      
      <div className="space-y-3">
        {displayResources.map((resource) => (
          <Link
            key={resource.id}
            href={`/locations/resources/${resource.id}`}
            className="flex justify-between items-center p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-md transition-colors"
          >
            <div>
              <span className="font-medium dark:text-white">{resource.name}</span>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {resource.type}
              </div>
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-300 text-right">
              {resource.locations && resource.locations[0]?.zone}
              {resource.locations && resource.locations.length > 1 && ' +'}
            </div>
          </Link>
        ))}
      </div>
      
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <Link
          href="/map"
          className="inline-block w-full px-4 py-2 bg-green-600 hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-800 text-white rounded-md transition-colors text-center"
        >
          Open Resource Map
        </Link>
      </div>
    </div>
  )
}
