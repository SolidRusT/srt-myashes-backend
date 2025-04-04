'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import LoadingSpinner from '@/components/common/LoadingSpinner'

// Types
type Profession = {
  id: string
  name: string
  type: string
  description: string
  tiers: Array<{name: string, description: string}>
  recipes?: string[]
}

interface CraftingProfessionInfoProps {
  professionName: string
}

export default function CraftingProfessionInfo({ professionName }: CraftingProfessionInfoProps) {
  const [profession, setProfession] = useState<Profession | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Fetch profession details
  useEffect(() => {
    const fetchProfession = async () => {
      setLoading(true)
      setError(null)
      
      try {
        // Make API call to get profession info
        const response = await fetch(`/api/v1/crafting/professions?name=${encodeURIComponent(professionName)}`)
        
        if (!response.ok) {
          throw new Error('Failed to fetch profession data')
        }
        
        const data = await response.json()
        
        // If we got an array, find the matching profession
        if (Array.isArray(data)) {
          const matchingProfession = data.find(p => 
            p.name.toLowerCase() === professionName.toLowerCase()
          )
          
          if (matchingProfession) {
            setProfession(matchingProfession)
          } else {
            setError('Profession not found')
          }
        } else {
          // If we got a single object, use it
          setProfession(data)
        }
        
      } catch (error) {
        console.error('Error fetching profession:', error)
        setError('Failed to load profession data')
      } finally {
        setLoading(false)
      }
    }
    
    if (professionName) {
      fetchProfession()
    }
  }, [professionName])
  
  if (loading) {
    return (
      <div className="py-8 text-center">
        <LoadingSpinner />
        <p className="mt-2 text-gray-500 dark:text-gray-400">Loading profession data...</p>
      </div>
    )
  }
  
  if (error || !profession) {
    return (
      <div className="py-8 text-center text-red-500">
        <p>{error || 'Failed to load profession data'}</p>
      </div>
    )
  }
  
  return (
    <div className="space-y-4">
      <div>
        <h3 className="font-medium mb-1 dark:text-white">{profession.name}</h3>
        <div className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full inline-block">
          {profession.type}
        </div>
        <p className="mt-2 text-sm text-gray-700 dark:text-gray-300">
          {profession.description}
        </p>
      </div>
      
      <div>
        <h4 className="text-sm font-medium mb-2 dark:text-white">Progression Tiers</h4>
        <div className="space-y-3">
          {profession.tiers.map((tier, index) => (
            <div 
              key={index}
              className={`p-3 border-l-2 ${
                index === 0 
                  ? 'border-blue-500 dark:border-blue-400' 
                  : 'border-gray-300 dark:border-gray-600'
              } ${
                index !== profession.tiers.length - 1
                  ? 'border-b border-gray-200 dark:border-gray-700'
                  : ''
              }`}
            >
              <h5 className="text-sm font-medium dark:text-white">
                {tier.name}
              </h5>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                {tier.description}
              </p>
            </div>
          ))}
        </div>
      </div>
      
      <div className="pt-2">
        <Link 
          href={`/crafting/progression/${profession.name}`}
          className="block w-full py-2 px-4 text-center text-sm bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 text-white rounded-md transition-colors"
        >
          View Leveling Guide
        </Link>
      </div>
    </div>
  )
}
