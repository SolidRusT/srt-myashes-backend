'use client'

import { useState } from 'react'
import Image from 'next/image'

type Archetype = {
  id: string
  name: string
  description: string
}

type ClassInfo = {
  id: string
  name: string
  primary: string
  secondary: string
  description: string
}

type BuildClass = {
  primary: string
  secondary: string
  classType: string
}

interface BuildClassSelectorProps {
  archetypes: Archetype[]
  classes: ClassInfo[]
  selectedClass: BuildClass | null
  onSelectClass: (buildClass: BuildClass | null) => void
}

export default function BuildClassSelector({
  archetypes,
  classes,
  selectedClass,
  onSelectClass
}: BuildClassSelectorProps) {
  const [primaryArchetype, setPrimaryArchetype] = useState<string | null>(
    selectedClass?.primary || null
  )
  const [secondaryArchetype, setSecondaryArchetype] = useState<string | null>(
    selectedClass?.secondary || null
  )

  const handlePrimarySelect = (archetypeName: string) => {
    setPrimaryArchetype(archetypeName)
    
    // If we also have a secondary, find the resulting class
    if (secondaryArchetype) {
      const resultingClass = classes.find(
        c => c.primary === archetypeName && c.secondary === secondaryArchetype
      )
      
      if (resultingClass) {
        onSelectClass({
          primary: archetypeName,
          secondary: secondaryArchetype,
          classType: resultingClass.name
        })
      } else {
        // If no valid class combination, reset secondary
        setSecondaryArchetype(null)
        onSelectClass({
          primary: archetypeName,
          secondary: '',
          classType: ''
        })
      }
    } else {
      onSelectClass({
        primary: archetypeName,
        secondary: '',
        classType: ''
      })
    }
  }

  const handleSecondarySelect = (archetypeName: string) => {
    setSecondaryArchetype(archetypeName)
    
    // If we have a primary, find the resulting class
    if (primaryArchetype) {
      const resultingClass = classes.find(
        c => c.primary === primaryArchetype && c.secondary === archetypeName
      )
      
      if (resultingClass) {
        onSelectClass({
          primary: primaryArchetype,
          secondary: archetypeName,
          classType: resultingClass.name
        })
      } else {
        // This shouldn't normally happen but just in case
        onSelectClass({
          primary: primaryArchetype,
          secondary: archetypeName,
          classType: ''
        })
      }
    }
  }

  // Get the selected class details
  const selectedClassDetails = selectedClass?.classType
    ? classes.find(c => c.name === selectedClass.classType)
    : null

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Primary Archetype
        </label>
        <div className="grid grid-cols-2 gap-2">
          {archetypes.map(archetype => (
            <button
              key={archetype.id}
              onClick={() => handlePrimarySelect(archetype.name)}
              className={`p-2 rounded-md text-sm text-left ${
                primaryArchetype === archetype.name
                  ? 'bg-blue-100 dark:bg-blue-900 border-2 border-blue-500 dark:border-blue-600'
                  : 'bg-gray-100 dark:bg-gray-700 border-2 border-transparent hover:border-gray-300 dark:hover:border-gray-600'
              }`}
            >
              {archetype.name}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Secondary Archetype
        </label>
        <div className="grid grid-cols-2 gap-2">
          {archetypes.map(archetype => (
            <button
              key={archetype.id}
              onClick={() => handleSecondarySelect(archetype.name)}
              disabled={!primaryArchetype}
              className={`p-2 rounded-md text-sm text-left ${
                !primaryArchetype
                  ? 'opacity-50 cursor-not-allowed bg-gray-100 dark:bg-gray-700'
                  : secondaryArchetype === archetype.name
                  ? 'bg-blue-100 dark:bg-blue-900 border-2 border-blue-500 dark:border-blue-600'
                  : 'bg-gray-100 dark:bg-gray-700 border-2 border-transparent hover:border-gray-300 dark:hover:border-gray-600'
              }`}
            >
              {archetype.name}
            </button>
          ))}
        </div>
      </div>

      {selectedClassDetails && (
        <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
              <span className="text-blue-600 dark:text-blue-300 font-semibold">{selectedClassDetails.name.charAt(0)}</span>
            </div>
            <div>
              <h3 className="font-semibold dark:text-white">{selectedClassDetails.name}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {selectedClassDetails.primary} + {selectedClassDetails.secondary}
              </p>
            </div>
          </div>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
            {selectedClassDetails.description || 
              `The ${selectedClassDetails.name} combines the powers of ${selectedClassDetails.primary} and ${selectedClassDetails.secondary}.`}
          </p>
        </div>
      )}
    </div>
  )
}
