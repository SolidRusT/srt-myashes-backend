'use client'

import { useState } from 'react'

type Skill = {
  id: string
  name: string
  description: string
  level: number
  category: string
}

type BuildClass = {
  primary: string
  secondary: string
  classType: string
}

interface BuildSkillSectionProps {
  skills: Skill[]
  onSkillsChange: (skills: Skill[]) => void
  selectedClass: BuildClass | null
  level: number
}

export default function BuildSkillSection({
  skills,
  onSkillsChange,
  selectedClass,
  level
}: BuildSkillSectionProps) {
  const [newSkill, setNewSkill] = useState<Skill>({
    id: '',
    name: '',
    description: '',
    level: 1,
    category: 'Combat'
  })

  const handleAddSkill = () => {
    if (!newSkill.name) return
    
    const skill = {
      ...newSkill,
      id: `skill-${Date.now()}`
    }
    
    onSkillsChange([...skills, skill])
    
    // Reset form
    setNewSkill({
      id: '',
      name: '',
      description: '',
      level: 1,
      category: 'Combat'
    })
  }

  const handleRemoveSkill = (skillId: string) => {
    onSkillsChange(skills.filter(skill => skill.id !== skillId))
  }

  // If no class is selected, show a placeholder
  if (!selectedClass?.classType) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4 dark:text-white">Skills</h2>
        <div className="p-8 text-center text-gray-500 dark:text-gray-400 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg">
          Please select a class to manage skills
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4 dark:text-white">Skills</h2>
      
      {/* Skill list */}
      {skills.length > 0 ? (
        <div className="mb-6 space-y-3">
          {skills.map(skill => (
            <div 
              key={skill.id}
              className="flex justify-between items-start p-3 bg-gray-50 dark:bg-gray-700 rounded-md"
            >
              <div>
                <div className="flex items-center">
                  <span className="font-medium dark:text-white">{skill.name}</span>
                  <span className="ml-2 text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full">
                    {skill.category}
                  </span>
                  <span className="ml-2 text-xs px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded-full">
                    Level {skill.level}
                  </span>
                </div>
                <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
                  {skill.description}
                </p>
              </div>
              <button
                onClick={() => handleRemoveSkill(skill.id)}
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
          No skills added yet. Add skills below to complete your build.
        </div>
      )}
      
      {/* Skill form */}
      <div className="space-y-4 border-t border-gray-200 dark:border-gray-700 pt-4">
        <h3 className="text-lg font-medium dark:text-white">Add Skill</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Skill Name
            </label>
            <input
              type="text"
              value={newSkill.name}
              onChange={(e) => setNewSkill({...newSkill, name: e.target.value})}
              placeholder="Enter skill name"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Category
              </label>
              <select
                value={newSkill.category}
                onChange={(e) => setNewSkill({...newSkill, category: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
              >
                <option value="Combat">Combat</option>
                <option value="Utility">Utility</option>
                <option value="Ultimate">Ultimate</option>
                <option value="Passive">Passive</option>
                <option value="Class">Class Specific</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Skill Level
              </label>
              <select
                value={newSkill.level}
                onChange={(e) => setNewSkill({...newSkill, level: parseInt(e.target.value)})}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
              >
                {[...Array(Math.min(50, level))].map((_, i) => (
                  <option key={i + 1} value={i + 1}>
                    {i + 1}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Description
          </label>
          <textarea
            value={newSkill.description}
            onChange={(e) => setNewSkill({...newSkill, description: e.target.value})}
            placeholder="Describe what this skill does"
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
          />
        </div>
        
        <div className="flex justify-end">
          <button
            onClick={handleAddSkill}
            disabled={!newSkill.name}
            className={`px-4 py-2 rounded-md text-white ${
              !newSkill.name
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800'
            } transition-colors`}
          >
            Add Skill
          </button>
        </div>
      </div>
    </div>
  )
}
