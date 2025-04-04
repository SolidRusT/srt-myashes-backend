'use client'

type ResourceLocation = {
  id: string
  name: string
  type: string
  coordinates: {
    x: number
    y: number
    z?: number
  }
  zone: string
  description?: string
}

interface LocationCardProps {
  location: ResourceLocation
  isSelected: boolean
  onClick: () => void
  color: string
}

export default function LocationCard({ location, isSelected, onClick, color }: LocationCardProps) {
  return (
    <div
      className={`p-3 rounded-lg cursor-pointer transition-colors ${
        isSelected
          ? 'bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800'
          : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
      }`}
      onClick={onClick}
    >
      <div className="flex items-start">
        <div 
          className="w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center mr-3 mt-0.5"
          style={{ backgroundColor: color }}
        >
          <span className="text-white text-xs">
            {location.type.charAt(0).toUpperCase()}
          </span>
        </div>
        
        <div>
          <h3 className="font-medium dark:text-white">{location.name}</h3>
          <div className="flex text-xs text-gray-600 dark:text-gray-400">
            <span className="mr-2">{location.type}</span>
            <span className="mx-1">•</span>
            <span>{location.zone}</span>
          </div>
          
          {location.description && (
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-500 line-clamp-1">
              {location.description}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
