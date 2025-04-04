'use client'

import { useState } from 'react'

type Equipment = {
  id: string
  name: string
  slot: string
  quality: string
  stats: Record<string, any>
}

interface BuildEquipmentSectionProps {
  equipment: Equipment[]
  onEquipmentChange: (equipment: Equipment[]) => void
}

export default function BuildEquipmentSection({
  equipment,
  onEquipmentChange
}: BuildEquipmentSectionProps) {
  const [newEquipment, setNewEquipment] = useState<Equipment>({
    id: '',
    name: '',
    slot: 'Weapon',
    quality: 'Common',
    stats: {}
  })
  const [newStatName, setNewStatName] = useState('')
  const [newStatValue, setNewStatValue] = useState('')

  const handleAddEquipment = () => {
    if (!newEquipment.name) return
    
    const item = {
      ...newEquipment,
      id: `equipment-${Date.now()}`
    }
    
    onEquipmentChange([...equipment, item])
    
    // Reset form
    setNewEquipment({
      id: '',
      name: '',
      slot: 'Weapon',
      quality: 'Common',
      stats: {}
    })
    setNewStatName('')
    setNewStatValue('')
  }

  const handleRemoveEquipment = (equipmentId: string) => {
    onEquipmentChange(equipment.filter(item => item.id !== equipmentId))
  }

  const handleAddStat = () => {
    if (!newStatName || !newStatValue) return
    
    setNewEquipment({
      ...newEquipment,
      stats: {
        ...newEquipment.stats,
        [newStatName]: newStatValue
      }
    })
    
    setNewStatName('')
    setNewStatValue('')
  }

  const handleRemoveStat = (statName: string) => {
    const newStats = { ...newEquipment.stats }
    delete newStats[statName]
    
    setNewEquipment({
      ...newEquipment,
      stats: newStats
    })
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4 dark:text-white">Equipment</h2>
      
      {/* Equipment list */}
      {equipment.length > 0 ? (
        <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          {equipment.map(item => (
            <div 
              key={item.id}
              className="flex justify-between items-start p-3 bg-gray-50 dark:bg-gray-700 rounded-md"
            >
              <div>
                <div className="flex items-center">
                  <span className={`font-medium ${getQualityClass(item.quality)}`}>
                    {item.name}
                  </span>
                  <span className="ml-2 text-xs px-2 py-1 bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-200 rounded-full">
                    {item.slot}
                  </span>
                </div>
                {Object.keys(item.stats).length > 0 && (
                  <ul className="mt-1 space-y-1">
                    {Object.entries(item.stats).map(([name, value]) => (
                      <li key={name} className="text-xs text-gray-600 dark:text-gray-300">
                        {name}: {value}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <button
                onClick={() => handleRemoveEquipment(item.id)}
                className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="mb-6 p-4 text-center text-gray-500 dark:text-gray-400 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg">
          No equipment added yet. Add equipment below to complete your build.
        </div>
      )}
      
      {/* Equipment form */}
      <div className="space-y-4 border-t border-gray-200 dark:border-gray-700 pt-4">
        <h3 className="text-lg font-medium dark:text-white">Add Equipment</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Item Name
            </label>
            <input
              type="text"
              value={newEquipment.name}
              onChange={(e) => setNewEquipment({...newEquipment, name: e.target.value})}
              placeholder="Enter item name"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Slot
            </label>
            <select
              value={newEquipment.slot}
              onChange={(e) => setNewEquipment({...newEquipment, slot: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
            >
              <option value="Weapon">Weapon</option>
              <option value="Off-hand">Off-hand</option>
              <option value="Head">Head</option>
              <option value="Chest">Chest</option>
              <option value="Hands">Hands</option>
              <option value="Legs">Legs</option>
              <option value="Feet">Feet</option>
              <option value="Neck">Neck</option>
              <option value="Ring">Ring</option>
              <option value="Earring">Earring</option>
              <option value="Trinket">Trinket</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Quality
            </label>
            <select
              value={newEquipment.quality}
              onChange={(e) => setNewEquipment({...newEquipment, quality: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
            >
              <option value="Common">Common</option>
              <option value="Uncommon">Uncommon</option>
              <option value="Rare">Rare</option>
              <option value="Epic">Epic</option>
              <option value="Legendary">Legendary</option>
              <option value="Mythic">Mythic</option>
            </select>
          </div>
        </div>
        
        {/* Stats section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Stats
          </label>
          
          {/* Current stats */}
          {Object.keys(newEquipment.stats).length > 0 && (
            <div className="mb-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Current Stats</h4>
              <div className="space-y-2">
                {Object.entries(newEquipment.stats).map(([name, value]) => (
                  <div key={name} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-300">
                      {name}: {value}
                    </span>
                    <button
                      onClick={() => handleRemoveStat(name)}
                      className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Add new stat */}
          <div className="flex space-x-2">
            <input
              type="text"
              value={newStatName}
              onChange={(e) => setNewStatName(e.target.value)}
              placeholder="Stat name (e.g. Strength)"
              className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
            />
            <input
              type="text"
              value={newStatValue}
              onChange={(e) => setNewStatValue(e.target.value)}
              placeholder="Value (e.g. +10)"
              className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
            />
            <button
              onClick={handleAddStat}
              disabled={!newStatName || !newStatValue}
              className={`px-4 py-2 rounded-md text-white ${
                !newStatName || !newStatValue
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-green-600 hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-800'
              } transition-colors`}
            >
              Add Stat
            </button>
          </div>
        </div>
        
        <div className="flex justify-end">
          <button
            onClick={handleAddEquipment}
            disabled={!newEquipment.name}
            className={`px-4 py-2 rounded-md text-white ${
              !newEquipment.name
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800'
            } transition-colors`}
          >
            Add Equipment
          </button>
        </div>
      </div>
    </div>
  )
}

// Helper function to get CSS class based on item quality
function getQualityClass(quality: string): string {
  switch (quality.toLowerCase()) {
    case 'common':
      return 'text-gray-200 dark:text-gray-300';
    case 'uncommon':
      return 'text-green-400';
    case 'rare':
      return 'text-blue-400';
    case 'epic':
      return 'text-purple-400';
    case 'legendary':
      return 'text-yellow-400';
    case 'mythic':
      return 'text-red-400';
    default:
      return 'text-gray-800 dark:text-white';
  }
}
