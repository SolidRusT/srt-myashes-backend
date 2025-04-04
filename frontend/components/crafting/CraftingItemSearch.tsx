'use client'

import { useState, useEffect, useRef } from 'react'
import LoadingSpinner from '@/components/common/LoadingSpinner'

interface CraftingItemSearchProps {
  selectedItem: string
  onItemSelect: (itemName: string) => void
  profession: string | null
}

export default function CraftingItemSearch({ selectedItem, onItemSelect, profession }: CraftingItemSearchProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [searchResults, setSearchResults] = useState<{name: string, profession: string}[]>([])
  const [loading, setLoading] = useState(false)
  const [showResults, setShowResults] = useState(false)
  const resultsRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  
  // Update search term when selected item changes
  useEffect(() => {
    setSearchTerm(selectedItem)
  }, [selectedItem])
  
  // Search for items
  useEffect(() => {
    const delayDebounceFn = setTimeout(async () => {
      if (searchTerm.length < 2) {
        setSearchResults([])
        return
      }
      
      setLoading(true)
      
      try {
        // Prepare query parameters
        const params = new URLSearchParams({
          query: searchTerm,
        })
        
        if (profession) {
          params.append('profession', profession)
        }
        
        // Fetch items
        const response = await fetch(`/api/v1/crafting/recipes?${params.toString()}`)
        
        if (!response.ok) {
          throw new Error('Failed to fetch items')
        }
        
        const data = await response.json()
        
        // Extract unique item names and professions
        const results = data.map((recipe: any) => ({
          name: recipe.result_item_name,
          profession: recipe.profession
        }))
        
        setSearchResults(results)
        setShowResults(true)
      } catch (error) {
        console.error('Error searching items:', error)
        setSearchResults([])
      } finally {
        setLoading(false)
      }
    }, 300)
    
    return () => clearTimeout(delayDebounceFn)
  }, [searchTerm, profession])
  
  // Handle outside click to close results
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (resultsRef.current && !resultsRef.current.contains(event.target as Node) && 
          inputRef.current && !inputRef.current.contains(event.target as Node)) {
        setShowResults(false)
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])
  
  // Handle item selection
  const handleSelectItem = (itemName: string) => {
    onItemSelect(itemName)
    setShowResults(false)
  }
  
  return (
    <div className="relative">
      <div className="flex">
        <input
          ref={inputRef}
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onFocus={() => searchTerm.length >= 2 && setShowResults(true)}
          placeholder="Search for items to craft..."
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
        />
        {loading && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <LoadingSpinner size="small" />
          </div>
        )}
      </div>
      
      {/* Search results dropdown */}
      {showResults && searchResults.length > 0 && (
        <div 
          ref={resultsRef}
          className="absolute z-10 mt-1 w-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-lg max-h-60 overflow-y-auto"
        >
          <ul className="py-1">
            {searchResults.map((result, index) => (
              <li key={index}>
                <button
                  type="button"
                  onClick={() => handleSelectItem(result.name)}
                  className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  <span className="font-medium dark:text-white">{result.name}</span>
                  <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">
                    {result.profession}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {/* No results message */}
      {showResults && searchTerm.length >= 2 && searchResults.length === 0 && !loading && (
        <div className="absolute z-10 mt-1 w-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-lg p-4 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            No craftable items found. Try a different search term.
          </p>
        </div>
      )}
    </div>
  )
}
