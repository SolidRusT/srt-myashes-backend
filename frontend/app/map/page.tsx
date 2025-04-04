'use client'

import { useState, useEffect, useRef } from 'react'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import ResourceFilters from '@/components/map/ResourceFilters'
import LocationCard from '@/components/map/LocationCard'
import MapControls from '@/components/map/MapControls'
import MapLegend from '@/components/map/MapLegend'

// Types
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

type ResourceType = {
  id: string
  name: string
  color: string
  icon: string
}

export default function MapPage() {
  // State
  const [loading, setLoading] = useState(true)
  const [locations, setLocations] = useState<ResourceLocation[]>([])
  const [filteredLocations, setFilteredLocations] = useState<ResourceLocation[]>([])
  const [selectedLocation, setSelectedLocation] = useState<ResourceLocation | null>(null)
  const [zoom, setZoom] = useState(1)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [resourceTypes, setResourceTypes] = useState<ResourceType[]>([])
  const [filters, setFilters] = useState({
    types: [] as string[],
    zone: '',
    searchQuery: ''
  })
  
  // Refs
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const isDragging = useRef(false)
  const startDragPos = useRef({ x: 0, y: 0 })
  
  // Resource type definitions with colors and icons
  const defaultResourceTypes: ResourceType[] = [
    { id: 'mining', name: 'Mining', color: '#B6B6B6', icon: 'pickaxe' },
    { id: 'lumber', name: 'Lumber', color: '#6B8E23', icon: 'axe' },
    { id: 'hunting', name: 'Hunting', color: '#8B4513', icon: 'bow' },
    { id: 'harvesting', name: 'Harvesting', color: '#9ACD32', icon: 'sickle' },
    { id: 'fishing', name: 'Fishing', color: '#4169E1', icon: 'fishing-rod' },
    { id: 'quest', name: 'Quest', color: '#FFD700', icon: 'scroll' },
    { id: 'dungeon', name: 'Dungeon', color: '#8A2BE2', icon: 'dungeon' },
    { id: 'settlement', name: 'Settlement', color: '#FF6347', icon: 'house' }
  ]
  
  // Load locations and resource types
  useEffect(() => {
    const fetchLocations = async () => {
      setLoading(true)
      
      try {
        // Fetch resource locations
        const response = await fetch('/api/v1/locations/points-of-interest')
        
        if (!response.ok) {
          throw new Error('Failed to fetch location data')
        }
        
        const data = await response.json()
        setLocations(data)
        setFilteredLocations(data)
        
        // Set default resource types
        setResourceTypes(defaultResourceTypes)
        
      } catch (error) {
        console.error('Error fetching locations:', error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchLocations()
  }, [])
  
  // Apply filters when they change
  useEffect(() => {
    if (locations.length === 0) return
    
    let filtered = [...locations]
    
    // Filter by type
    if (filters.types.length > 0) {
      filtered = filtered.filter(location => 
        filters.types.includes(location.type)
      )
    }
    
    // Filter by zone
    if (filters.zone) {
      filtered = filtered.filter(location => 
        location.zone.toLowerCase().includes(filters.zone.toLowerCase())
      )
    }
    
    // Filter by search query
    if (filters.searchQuery) {
      const query = filters.searchQuery.toLowerCase()
      filtered = filtered.filter(location => 
        location.name.toLowerCase().includes(query) || 
        location.description?.toLowerCase().includes(query)
      )
    }
    
    setFilteredLocations(filtered)
  }, [filters, locations])
  
  // Map drag handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return // Only left mouse button
    
    isDragging.current = true
    startDragPos.current = { 
      x: e.clientX - position.x, 
      y: e.clientY - position.y 
    }
    
    // Change cursor
    if (mapContainerRef.current) {
      mapContainerRef.current.style.cursor = 'grabbing'
    }
  }
  
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging.current) return
    
    const newX = e.clientX - startDragPos.current.x
    const newY = e.clientY - startDragPos.current.y
    
    setPosition({ x: newX, y: newY })
  }
  
  const handleMouseUp = () => {
    isDragging.current = false
    
    // Reset cursor
    if (mapContainerRef.current) {
      mapContainerRef.current.style.cursor = 'grab'
    }
  }
  
  // Zoom handlers
  const handleZoomIn = () => {
    setZoom(prevZoom => Math.min(prevZoom + 0.2, 3))
  }
  
  const handleZoomOut = () => {
    setZoom(prevZoom => Math.max(prevZoom - 0.2, 0.5))
  }
  
  const handleResetZoom = () => {
    setZoom(1)
    setPosition({ x: 0, y: 0 })
  }
  
  // Handle pin click
  const handlePinClick = (location: ResourceLocation) => {
    setSelectedLocation(location)
  }
  
  // Get color for location type
  const getLocationColor = (type: string): string => {
    const resourceType = resourceTypes.find(t => t.name.toLowerCase() === type.toLowerCase())
    return resourceType?.color || '#999999'
  }
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-64px)]">
        <div className="text-center">
          <LoadingSpinner size="large" />
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading map...</p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="flex flex-col h-[calc(100vh-64px)]">
      <div className="py-4 px-6 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <h1 className="text-2xl font-display font-bold dark:text-white">Resource Map</h1>
        <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">
          Find resource nodes, dungeons, and points of interest across Verra
        </p>
      </div>
      
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div className="w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <ResourceFilters 
              filters={filters}
              setFilters={setFilters}
              resourceTypes={resourceTypes}
            />
          </div>
          
          <div className="flex-1 overflow-y-auto p-4">
            <h2 className="text-lg font-semibold mb-3 dark:text-white">
              Locations ({filteredLocations.length})
            </h2>
            
            {filteredLocations.length > 0 ? (
              <div className="space-y-3">
                {filteredLocations.map(location => (
                  <LocationCard
                    key={location.id}
                    location={location}
                    isSelected={selectedLocation?.id === location.id}
                    onClick={() => handlePinClick(location)}
                    color={getLocationColor(location.type)}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <p>No locations match your filters</p>
                <button 
                  onClick={() => setFilters({ types: [], zone: '', searchQuery: '' })}
                  className="mt-2 text-blue-600 dark:text-blue-400 hover:underline"
                >
                  Clear filters
                </button>
              </div>
            )}
          </div>
        </div>
        
        {/* Map area */}
        <div className="flex-1 relative bg-gray-100 dark:bg-gray-900 overflow-hidden">
          {/* Map container */}
          <div 
            ref={mapContainerRef}
            className="absolute inset-0 cursor-grab"
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          >
            {/* Map image */}
            <div 
              className="absolute"
              style={{ 
                transform: `translate(${position.x}px, ${position.y}px) scale(${zoom})`,
                transformOrigin: 'center',
                transition: 'transform 0.1s ease-out'
              }}
            >
              <div className="relative">
                <img 
                  src="/images/ashes-map.jpg" 
                  alt="Ashes of Creation Map" 
                  className="max-w-none"
                  draggable={false}
                />
                
                {/* Location pins */}
                {filteredLocations.map(location => (
                  <div
                    key={location.id}
                    className={`absolute w-6 h-6 -ml-3 -mt-3 rounded-full flex items-center justify-center cursor-pointer ${
                      selectedLocation?.id === location.id 
                        ? 'z-20 ring-2 ring-white ring-opacity-70'
                        : 'z-10'
                    }`}
                    style={{
                      left: `${location.coordinates.x}%`,
                      top: `${location.coordinates.y}%`,
                      backgroundColor: getLocationColor(location.type)
                    }}
                    onClick={() => handlePinClick(location)}
                  >
                    <span className="flex h-2 w-2 relative">
                      {selectedLocation?.id === location.id && (
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                      )}
                    </span>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Selected location details */}
            {selectedLocation && (
              <div 
                className="absolute z-30 bottom-4 left-1/2 transform -translate-x-1/2 w-96 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4"
                onClick={(e) => e.stopPropagation()}
              >
                <button 
                  className="absolute right-2 top-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  onClick={() => setSelectedLocation(null)}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
                
                <div className="flex items-start">
                  <div 
                    className="w-8 h-8 rounded-full mr-3 flex-shrink-0 flex items-center justify-center"
                    style={{ backgroundColor: getLocationColor(selectedLocation.type) }}
                  >
                    <span className="text-white text-xs">
                      {selectedLocation.type.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  
                  <div>
                    <h3 className="font-medium text-lg dark:text-white">{selectedLocation.name}</h3>
                    <div className="flex text-sm text-gray-600 dark:text-gray-400">
                      <span className="mr-2">{selectedLocation.type}</span>
                      <span className="mx-1">•</span>
                      <span>{selectedLocation.zone}</span>
                    </div>
                    
                    {selectedLocation.description && (
                      <p className="mt-2 text-sm text-gray-700 dark:text-gray-300">
                        {selectedLocation.description}
                      </p>
                    )}
                    
                    <div className="mt-2 text-xs text-gray-500 dark:text-gray-500">
                      Coordinates: {selectedLocation.coordinates.x.toFixed(1)}%, {selectedLocation.coordinates.y.toFixed(1)}%
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
          
          {/* Map controls */}
          <MapControls
            onZoomIn={handleZoomIn}
            onZoomOut={handleZoomOut}
            onReset={handleResetZoom}
            currentZoom={zoom}
          />
          
          {/* Map legend */}
          <MapLegend resourceTypes={resourceTypes} />
        </div>
      </div>
    </div>
  )
}
