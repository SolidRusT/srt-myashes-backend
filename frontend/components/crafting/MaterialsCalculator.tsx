'use client'

import Link from 'next/link'
import { useState } from 'react'

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

type RequiredMaterial = {
  id: string
  name: string
  amount: number
  is_craftable: boolean
  sub_materials: any[]
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
  required_materials: RequiredMaterial[]
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

interface MaterialsCalculatorProps {
  calculation: CraftingCalculation
}

export default function MaterialsCalculator({ calculation }: MaterialsCalculatorProps) {
  const [showDetails, setShowDetails] = useState(false)
  
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold dark:text-white">Crafting Requirements</h2>
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
        >
          {showDetails ? 'Hide Details' : 'Show Details'}
        </button>
      </div>
      
      {/* Recipe overview */}
      <div className="p-4 mb-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-medium dark:text-white">
            {calculation.item_name} x{calculation.amount}
          </h3>
          <span className="text-sm px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full">
            {calculation.recipe.profession} ({calculation.recipe.level})
          </span>
        </div>
        
        {calculation.recipe.stations && calculation.recipe.stations.length > 0 && (
          <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
            <span className="font-medium">Required Station:</span> {calculation.recipe.stations.join(', ')}
          </p>
        )}
        
        {calculation.recipe.duration && (
          <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
            <span className="font-medium">Crafting Time:</span> {calculation.recipe.duration}
          </p>
        )}
        
        {calculation.recipe.notes && (
          <p className="text-sm text-gray-600 dark:text-gray-300">
            <span className="font-medium">Notes:</span> {calculation.recipe.notes}
          </p>
        )}
      </div>
      
      {/* Recipe details */}
      {showDetails && (
        <div className="mb-4 border-b border-gray-200 dark:border-gray-700 pb-4">
          <h3 className="text-md font-medium mb-2 dark:text-white">Recipe Details</h3>
          <div className="pl-4 border-l-2 border-blue-300 dark:border-blue-800">
            <p className="text-sm text-gray-600 dark:text-gray-300">
              <span className="font-medium">Output:</span> {calculation.recipe.result_item_name} x{calculation.recipe.result_amount}
              {calculation.recipe.result_quality && ` (${calculation.recipe.result_quality})`}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              <span className="font-medium">Base Materials:</span> {calculation.recipe.materials.length}
            </p>
            {calculation.required_materials.some(m => m.is_craftable) && (
              <p className="text-sm text-gray-600 dark:text-gray-300">
                <span className="font-medium">Sub-recipes:</span> {calculation.required_materials.filter(m => m.is_craftable).length}
              </p>
            )}
          </div>
        </div>
      )}
      
      {/* Required materials */}
      <h3 className="text-md font-medium mb-3 dark:text-white">Required Materials</h3>
      <div className="mb-6 divide-y divide-gray-200 dark:divide-gray-700">
        {calculation.required_materials.map((material) => (
          <div key={material.id} className="py-3 flex justify-between items-center">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-md mr-3 flex-shrink-0"></div>
              <div>
                <div className="font-medium dark:text-white">{material.name}</div>
                {material.is_craftable && (
                  <div className="text-xs text-blue-600 dark:text-blue-400">
                    <Link href={`/crafting?item=${encodeURIComponent(material.name)}`}>
                      Craftable
                    </Link>
                  </div>
                )}
              </div>
            </div>
            <div className="text-gray-700 dark:text-gray-300 font-medium">
              {material.amount}
            </div>
          </div>
        ))}
      </div>
      
      {/* Total base materials */}
      <h3 className="text-md font-medium mb-3 dark:text-white">Total Base Materials</h3>
      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {calculation.total_base_materials.map((material) => (
            <div key={material.id} className="flex justify-between items-center">
              <span className="text-gray-700 dark:text-gray-300">{material.name}</span>
              <span className="font-medium dark:text-white">{material.amount}</span>
            </div>
          ))}
        </div>
      </div>
      
      {/* Estimated cost */}
      {calculation.estimated_cost && (
        <div className="mt-6">
          <h3 className="text-md font-medium mb-3 dark:text-white">Estimated Cost</h3>
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <div className="flex justify-between items-center mb-3">
              <span className="text-gray-700 dark:text-gray-300">Total Cost</span>
              <span className="text-lg font-bold dark:text-white">
                {calculation.estimated_cost.amount} {calculation.estimated_cost.currency}
              </span>
            </div>
            
            {showDetails && calculation.estimated_cost.breakdown && (
              <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-600">
                <h4 className="text-sm font-medium mb-2 dark:text-white">Cost Breakdown</h4>
                <div className="space-y-1 text-sm">
                  {calculation.estimated_cost.breakdown.map((item, index) => (
                    <div key={index} className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">
                        {item.item_name} ({item.quantity} x {item.unit_price})
                      </span>
                      <span className="text-gray-800 dark:text-gray-200">{item.total}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Export/Save buttons */}
      <div className="mt-6 flex gap-3">
        <button className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-800 text-white rounded-md transition-colors text-sm">
          Save Shopping List
        </button>
        <button className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 text-white rounded-md transition-colors text-sm">
          Export
        </button>
      </div>
    </div>
  )
}
