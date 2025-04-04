'use client'

import Link from 'next/link'
import Image from 'next/image'

type Item = {
  id: string
  name: string
  quality: string
  type: string
  subtype?: string
  description?: string
  stats?: Array<{name: string, value: any}>
  level?: number
  sources?: Array<{type: string, details: string}>
  locations?: Array<{zone: string, coordinates?: string, notes?: string}>
  recipe?: {
    recipe_id: string
    materials: Array<{item_id: string, name: string, amount: number}>
    skill: string
    skill_level: string
  }
  used_in?: string[]
  icon_url?: string
}

interface ItemCardProps {
  item: Item
}

export default function ItemCard({ item }: ItemCardProps) {
  // Helper function to get CSS class based on item quality
  const getQualityClass = (quality: string): string => {
    switch (quality.toLowerCase()) {
      case 'common':
        return 'text-gray-200 dark:text-gray-300 border-gray-300 dark:border-gray-600';
      case 'uncommon':
        return 'text-green-500 border-green-500';
      case 'rare':
        return 'text-blue-500 border-blue-500';
      case 'epic':
        return 'text-purple-500 border-purple-500';
      case 'legendary':
        return 'text-yellow-500 border-yellow-500';
      case 'mythic':
        return 'text-red-500 border-red-500';
      default:
        return 'text-gray-800 dark:text-white border-gray-300 dark:border-gray-600';
    }
  }
  
  const qualityClass = getQualityClass(item.quality)
  
  // Placeholder image if no icon is available
  const placeholderIcon = `/images/item-icons/${item.type?.toLowerCase() || 'misc'}.png`
  
  return (
    <Link href={`/items/${item.id}`}>
      <div className={`game-card card-hover-effect border-l-4 ${qualityClass}`}>
        <div className="flex p-4">
          <div className="flex-shrink-0 mr-4">
            <div className="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded-md overflow-hidden relative">
              <Image
                src={item.icon_url || placeholderIcon}
                alt={item.name}
                fill
                className="object-cover"
                onError={(e) => {
                  // Fallback if the main image fails
                  const target = e.target as HTMLImageElement;
                  target.src = '/images/item-icons/misc.png';
                }}
              />
            </div>
          </div>
          
          <div className="flex-grow">
            <h3 className={`font-medium mb-1 ${qualityClass}`}>{item.name}</h3>
            
            <div className="flex items-center text-xs text-gray-600 dark:text-gray-400 mb-2">
              <span className="mr-2">{item.type}</span>
              {item.subtype && (
                <>
                  <span className="mx-1">•</span>
                  <span>{item.subtype}</span>
                </>
              )}
              {item.level && (
                <>
                  <span className="mx-1">•</span>
                  <span>Level {item.level}</span>
                </>
              )}
            </div>
            
            {item.description && (
              <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                {item.description}
              </p>
            )}
          </div>
        </div>
        
        {/* Stats preview (if available) */}
        {item.stats && item.stats.length > 0 && (
          <div className="px-4 pb-3 pt-0 border-t border-gray-100 dark:border-gray-700 text-xs">
            <div className="grid grid-cols-2 gap-1">
              {item.stats.slice(0, 4).map((stat, index) => (
                <div key={index} className="text-gray-600 dark:text-gray-400">
                  {stat.name}: {stat.value}
                </div>
              ))}
              {item.stats.length > 4 && (
                <div className="text-gray-500 dark:text-gray-500">
                  +{item.stats.length - 4} more...
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </Link>
  )
}
