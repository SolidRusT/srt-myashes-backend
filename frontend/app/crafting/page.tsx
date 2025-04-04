'use client'

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import CraftingItemSearch from '@/components/crafting/CraftingItemSearch'
import MaterialsCalculator from '@/components/crafting/MaterialsCalculator'
import CraftingProfessionInfo from '@/components/crafting/CraftingProfessionInfo'

// Types
type CraftingMaterial = {
  item_id: string
  name: string
  amount: number
}

type Recipe = {
  recipe_id: string
  name: string
  result_item_id: string
  result_item_name: string
  result_amount: number
  result_quality?: string
  profession: string
  level: string
  materials: CraftingMaterial[]
  stations?: string[]
  duration?: string
  notes?: string
}

type BaseMaterial = {
  id: string
  name: string
  amount: number
}

type CraftingCalculation = {
  item_name: string
  amount: number
  recipe: Recipe
  required_materials: {
    id: string
    name: string
    amount: number
    is_craftable: boolean
    sub_materials: any[]
  }[]
  total_base_materials: BaseMaterial[]
  estimated_cost?: {
    currency: string
    amount: number
    breakdown: {
      item_name: string
      unit_price: number
      quantity: number
      total: number
    }[]
  }
}

export default function CraftingPage() {
  const searchParams = useSearchParams()
  
  // State
  const [loading, setLoading] = useState(false)
  const [selectedItem, setSelectedItem] = useState<string>('')
  const [quantity, setQuantity] = useState(1)
  const [calculationResult, setCalculationResult] = useState<CraftingCalculation | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [professions, setProfessions] = useState<{ id: string, name: string, type: string }[]>([])
  const [selectedProfession, setSelectedProfession] = useState<string | null>(null)
  
  // Load professions on mount
  useEffect(() => {
    const fetchProfessions = async () => {
      try {
        const response = await fetch('/api/v1/crafting/professions')
        if (!response.ok) throw new Error('Failed to fetch professions')
        
        const data = await response.json()
        setProfessions(data)
      } catch (error) {
        console.error('Error fetching professions:', error)
      }
    }
    
    fetchProfessions()
  }, [])
  
  // Check for item in URL params on mount
  useEffect(() => {
    const itemParam = searchParams.get('item')
    const qtyParam = searchParams.get('qty')
    
    if (itemParam) {
      setSelectedItem(itemParam)
      
      if (qtyParam && !isNaN(parseInt(qtyParam))) {
        setQuantity(parseInt(qtyParam))
      }
      
      // Auto-calculate if both params are present
      if (itemParam && qtyParam) {
        handleCalculate()
      }
    }
  }, [searchParams])
  
  // Calculate required materials
  const handleCalculate = async () => {
    if (!selectedItem) {
      setError('Please select an item to craft')
      return
    }
    
    if (quantity < 1) {
      setError('Quantity must be at least 1')
      return
    }
    
    setLoading(true)
    setError(null)
    
    try {
      // Make API call to get crafting calculation
      const response = await fetch(`/api/v1/crafting/calculate?item_name=${encodeURIComponent(selectedItem)}&amount=${quantity}`)
      
      if (!response.ok) {
        throw new Error(`Failed to calculate materials: ${response.statusText}`)
      }
      
      const data = await response.json()
      setCalculationResult(data)
      
    } catch (error) {
      console.error('Error calculating materials:', error)
      setError('Failed to calculate materials. Please try again.')
      setCalculationResult(null)
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-display font-bold mb-6 dark:text-white">Crafting Calculator</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left column: Calculator */}
        <div className="lg:col-span-2 space-y-8">
          {/* Item selection and calculation */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4 dark:text-white">Calculate Materials</h2>
            
            <div className="space-y-4">
              {/* Item selector */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Item to Craft
                </label>
                <CraftingItemSearch 
                  selectedItem={selectedItem}
                  onItemSelect={setSelectedItem}
                  profession={selectedProfession}
                />
              </div>
              
              {/* Quantity selector */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Quantity
                </label>
                <div className="flex">
                  <input
                    type="number"
                    min="1"
                    max="9999"
                    value={quantity}
                    onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
                    className="w-24 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-l-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
                  />
                  <button
                    onClick={handleCalculate}
                    disabled={loading || !selectedItem}
                    className={`flex items-center px-4 py-2 rounded-r-md transition-colors ${
                      loading || !selectedItem
                        ? 'bg-gray-300 dark:bg-gray-600 cursor-not-allowed'
                        : 'bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 text-white'
                    }`}
                  >
                    {loading ? <LoadingSpinner size="small" /> : 'Calculate'}
                  </button>
                </div>
                
                {error && (
                  <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>
                )}
              </div>
            </div>
          </div>
          
          {/* Calculation results */}
          {calculationResult && (
            <MaterialsCalculator calculation={calculationResult} />
          )}
        </div>
        
        {/* Right column: Professions */}
        <div className="space-y-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4 dark:text-white">Crafting Professions</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Filter by Profession
                </label>
                <select
                  value={selectedProfession || ''}
                  onChange={(e) => setSelectedProfession(e.target.value || null)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
                >
                  <option value="">All Professions</option>
                  {professions.map((profession) => (
                    <option key={profession.id} value={profession.name}>
                      {profession.name}
                    </option>
                  ))}
                </select>
              </div>
              
              {selectedProfession && (
                <CraftingProfessionInfo professionName={selectedProfession} />
              )}
              
              {!selectedProfession && (
                <div className="py-4 text-center text-gray-500 dark:text-gray-400">
                  <p>Select a profession to view details</p>
                </div>
              )}
            </div>
          </div>
          
          {/* Tips and tricks */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4 dark:text-white">Crafting Tips</h2>
            
            <div className="space-y-3 text-sm text-gray-700 dark:text-gray-300">
              <p>
                <span className="font-medium">Quality Matters:</span> Higher quality materials often result in better crafted items.
              </p>
              <p>
                <span className="font-medium">Material Sourcing:</span> Gathering your own materials is cheaper but takes time. The marketplace is faster but more expensive.
              </p>
              <p>
                <span className="font-medium">Crafting Stations:</span> Different crafting stations may provide bonuses to your crafting results.
              </p>
              <p>
                <span className="font-medium">Skill Leveling:</span> Craft lower-level items in bulk to efficiently level up your crafting skills.
              </p>
              <p>
                <span className="font-medium">Node Benefits:</span> Certain node types may provide bonuses to specific crafting professions.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
