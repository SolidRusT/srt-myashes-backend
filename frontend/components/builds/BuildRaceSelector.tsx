'use client'

import { useState } from 'react'
import Image from 'next/image'

type Race = {
  id: string
  name: string
  description: string
  racial_traits: Array<{name: string, description: string}>
}

interface BuildRaceSelectorProps {
  races: Race[]
  selectedRace: string | null
  onSelectRace: (raceName: string) => void
}

export default function BuildRaceSelector({
  races,
  selectedRace,
  onSelectRace
}: BuildRaceSelectorProps) {
  const [showDetails, setShowDetails] = useState<string | null>(null)

  const handleRaceSelect = (raceName: string) => {
    onSelectRace(raceName)
  }

  const toggleDetails = (raceName: string) => {
    setShowDetails(showDetails === raceName ? null : raceName)
  }

  // Get the selected race details
  const selectedRaceDetails = selectedRace
    ? races.find(r => r.name === selectedRace)
    : null

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        Race
      </label>
      <div className="grid grid-cols-2 gap-2">
        {races.map(race => (
          <button
            key={race.id}
            onClick={() => handleRaceSelect(race.name)}
            className={`p-2 rounded-md text-sm text-left ${
              selectedRace === race.name
                ? 'bg-blue-100 dark:bg-blue-900 border-2 border-blue-500 dark:border-blue-600'
                : 'bg-gray-100 dark:bg-gray-700 border-2 border-transparent hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            <div className="flex justify-between items-center">
              <span>{race.name}</span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  toggleDetails(race.name)
                }}
                className="ml-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </button>
            </div>
          </button>
        ))}
      </div>

      {showDetails && (
        <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          {races
            .filter(r => r.name === showDetails)
            .map(race => (
              <div key={race.id}>
                <h3 className="font-semibold dark:text-white">{race.name}</h3>
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                  {race.description}
                </p>
                {race.racial_traits && race.racial_traits.length > 0 && (
                  <div className="mt-3">
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Racial Traits</h4>
                    <ul className="mt-1 space-y-1">
                      {race.racial_traits.map((trait, index) => (
                        <li key={index} className="text-sm text-gray-600 dark:text-gray-300">
                          <span className="font-medium">{trait.name}</span>: {trait.description}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <button
                  type="button"
                  onClick={() => setShowDetails(null)}
                  className="mt-3 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                >
                  Close
                </button>
              </div>
            ))}
        </div>
      )}

      {selectedRaceDetails && !showDetails && (
        <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold dark:text-white">{selectedRaceDetails.name}</h3>
            <button
              type="button"
              onClick={() => toggleDetails(selectedRaceDetails.name)}
              className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
            >
              View Details
            </button>
          </div>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-300 line-clamp-2">
            {selectedRaceDetails.description}
          </p>
        </div>
      )}
    </div>
  )
}
