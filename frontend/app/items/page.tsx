'use client'

import { useState, useEffect } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import ItemCard from '@/components/items/ItemCard'
import ItemFilters from '@/components/items/ItemFilters'
import Pagination from '@/components/common/Pagination'

// Types
type ItemSource = {
  type: string
  details: string
}

type ItemLocation = {
  zone: string
  coordinates?: string
  notes?: string
}

type ItemStat = {
  name: string
  value: any
}

type CraftingMaterial = {
  item_id: string
  name: string
  amount: number
}

type CraftingRecipe = {
  recipe_id: string
  materials: CraftingMaterial[]
  skill: string
  skill_level: string
}

type Item = {
  id: string
  name: string
  quality: string
  type: string
  subtype?: string
  description?: string
  stats?: ItemStat[]
  level?: number
  sources?: ItemSource[]
  locations?: ItemLocation[]
  recipe?: CraftingRecipe
  used_in?: string[]
  icon_url?: string
}

type ItemSearchResult = {
  items: Item[]
  total: number
  page: number
  page_size: number
}

export default function ItemsPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  
  // States
  const [loading, setLoading] = useState(true)
  const [searchResults, setSearchResults] = useState<ItemSearchResult | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [filters, setFilters] = useState({
    type: '',
    quality: '',
    level_min: '',
    level_max: ''
  })
  const [page, setPage] = useState(1)
  
  // Handle search form submission
  const handleSearch = (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    
    const params = new URLSearchParams()
    if (searchQuery) params.set('q', searchQuery)
    if (filters.type) params.set('type', filters.type)
    if (filters.quality) params.set('quality', filters.quality)
    if (filters.level_min) params.set('level_min', filters.level_min)
    if (filters.level_max) params.set('level_max', filters.level_max)
    params.set('page', page.toString())
    
    router.push(`/items?${params.toString()}`)
    
    fetchItems(searchQuery, filters, page)
  }
  
  // Fetch items based on search params
  const fetchItems = async (query: string, itemFilters: any, currentPage: number) => {
    setLoading(true)
    
    try {
      const queryParams = new URLSearchParams()
      if (query) queryParams.set('query', query)
      if (itemFilters.type) queryParams.set('type', itemFilters.type)
      if (itemFilters.quality) queryParams.set('quality', itemFilters.quality)
      if (itemFilters.level_min) queryParams.set('level_min', itemFilters.level_min)
      if (itemFilters.level_max) queryParams.set('level_max', itemFilters.level_max)
      queryParams.set('page', currentPage.toString())
      
      const response = await fetch(`/api/v1/items?${queryParams.toString()}`)
      
      if (!response.ok) {
        throw new Error('Failed to fetch items')
      }
      
      const data = await response.json()
      setSearchResults(data)
      
    } catch (error) {
      console.error('Error fetching items:', error)
    } finally {
      setLoading(false)
    }
  }
  
  // Extract search parameters from URL
  useEffect(() => {
    const query = searchParams.get('q') || ''
    const type = searchParams.get('type') || ''
    const quality = searchParams.get('quality') || ''
    const level_min = searchParams.get('level_min') || ''
    const level_max = searchParams.get('level_max') || ''
    const currentPage = parseInt(searchParams.get('page') || '1')
    
    setSearchQuery(query)
    setFilters({
      type,
      quality,
      level_min,
      level_max
    })
    setPage(currentPage)
    
    fetchItems(query, { type, quality, level_min, level_max }, currentPage)
  }, [searchParams])
  
  // Handle pagination
  const handlePageChange = (newPage: number) => {
    setPage(newPage)
    
    const params = new URLSearchParams(searchParams.toString())
    params.set('page', newPage.toString())
    
    router.push(`/items?${params.toString()}`)
  }
  
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-display font-bold dark:text-white">Item Database</h1>
        <Link
          href="/items/random"
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 text-white rounded-md transition-colors"
        >
          Random Item
        </Link>
      </div>
      
      {/* Search and filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-8">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="flex gap-4 flex-col sm:flex-row">
            <div className="flex-grow">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search for items..."
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
              />
            </div>
            <button
              type="submit"
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 text-white rounded-md transition-colors"
            >
              Search
            </button>
          </div>
          
          <ItemFilters filters={filters} setFilters={setFilters} />
        </form>
      </div>
      
      {/* Results */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4 dark:text-white">
          {loading ? 'Searching...' : searchResults ? 
            `Found ${searchResults.total} items` : 
            'Search for items above'}
        </h2>
        
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <LoadingSpinner size="large" />
          </div>
        ) : searchResults && searchResults.items.length > 0 ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {searchResults.items.map((item) => (
                <ItemCard key={item.id} item={item} />
              ))}
            </div>
            
            {/* Pagination */}
            {searchResults.total > searchResults.page_size && (
              <div className="mt-8">
                <Pagination
                  currentPage={page}
                  totalPages={Math.ceil(searchResults.total / searchResults.page_size)}
                  onPageChange={handlePageChange}
                />
              </div>
            )}
          </>
        ) : searchResults ? (
          <div className="py-8 text-center text-gray-500 dark:text-gray-400">
            <p>No items found matching your criteria.</p>
            <p className="mt-2">Try adjusting your search terms or filters.</p>
          </div>
        ) : null}
      </div>
    </div>
  )
}
