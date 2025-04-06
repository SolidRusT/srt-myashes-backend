'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Image from 'next/image'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import BuildClassSelector from '@/components/builds/BuildClassSelector'
import BuildRaceSelector from '@/components/builds/BuildRaceSelector'
import BuildSkillSection from '@/components/builds/BuildSkillSection'
import BuildEquipmentSection from '@/components/builds/BuildEquipmentSection'
import BuildSaveDialog from '@/components/builds/BuildSaveDialog'

// Types
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

type Race = {
  id: string
  name: string
  description: string
  racial_traits: Array<{name: string, description: string}>
}

type BuildClass = {
  primary: string
  secondary: string
  classType: string
}

type Equipment = {
  id: string
  name: string
  slot: string
  quality: string
  stats: Record<string, any>
}

type Skill = {
  id: string
  name: string
  description: string
  level: number
  category: string
}

export default function BuildPlannerContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  
  // States
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [archetypes, setArchetypes] = useState<Archetype[]>([])
  const [classes, setClasses] = useState<ClassInfo[]>([])
  const [races, setRaces] = useState<Race[]>([])
  const [isSaveDialogOpen, setIsSaveDialogOpen] = useState(false)
  
  // Build state
  const [selectedRace, setSelectedRace] = useState<string | null>(null)
  const [selectedClass, setSelectedClass] = useState<BuildClass | null>(null)
  const [level, setLevel] = useState(1)
  const [skills, setSkills] = useState<Skill[]>([])
  const [equipment, setEquipment] = useState<Equipment[]>([])
  const [buildName, setBuildName] = useState('')
  const [buildDescription, setBuildDescription] = useState('')
  
  // Load data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        
        // Fetch archetypes
        const archetypesRes = await fetch('/api/v1/builds/archetypes')
        const archetypesData = await archetypesRes.json()
        setArchetypes(archetypesData)
        
        // Fetch classes
        const classesRes = await fetch('/api/v1/builds/classes')
        const classesData = await classesRes.json()
        setClasses(classesData)
        
        // Fetch races
        const racesRes = await fetch('/api/v1/builds/races')
        const racesData = await racesRes.json()
        setRaces(racesData)
        
        // Check if editing existing build
        const buildId = searchParams.get('id')
        if (buildId) {
          await loadBuild(buildId)
        }
        
      } catch (error) {
        console.error('Error loading build data:', error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchData()
  }, [searchParams])
  
  // Load existing build
  const loadBuild = async (buildId: string) => {
    try {
      const res = await fetch(`/api/v1/builds/${buildId}`)
      
      if (!res.ok) {
        throw new Error('Failed to load build')
      }
      
      const buildData = await res.json()
      
      // Populate form with build data
      setSelectedRace(buildData.race)
      setSelectedClass(buildData.classes)
      setLevel(buildData.level)
      setSkills(buildData.skills)
      setEquipment(buildData.equipment)
      setBuildName(buildData.name)
      setBuildDescription(buildData.description)
      
    } catch (error) {
      console.error('Error loading build:', error)
    }
  }
  
  // Save build
  const saveBuild = async () => {
    if (!selectedRace || !selectedClass) {
      alert('Please select a race and class before saving')
      return
    }
    
    if (!buildName) {
      alert('Please enter a name for your build')
      return
    }
    
    try {
      setSaving(true)
      
      const buildData = {
        name: buildName,
        description: buildDescription,
        race: selectedRace,
        classes: selectedClass,
        level,
        skills,
        equipment,
        is_public: true,
        tags: []
      }
      
      // Check if editing or creating
      const buildId = searchParams.get('id')
      
      let res
      if (buildId) {
        // Update existing build
        res = await fetch(`/api/v1/builds/${buildId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(buildData)
        })
      } else {
        // Create new build
        res = await fetch('/api/v1/builds', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(buildData)
        })
      }
      
      if (!res.ok) {
        throw new Error('Failed to save build')
      }
      
      const savedBuild = await res.json()
      
      // Redirect to build view page
      router.push(`/builds/${savedBuild.id}`)
      
    } catch (error) {
      console.error('Error saving build:', error)
      alert('Failed to save build. Please try again.')
    } finally {
      setSaving(false)
      setIsSaveDialogOpen(false)
    }
  }
  
  const handleLevelChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newLevel = parseInt(e.target.value)
    if (newLevel >= 1 && newLevel <= 50) {
      setLevel(newLevel)
    }
  }
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-64px)]">
        <div className="text-center">
          <LoadingSpinner size="large" />
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading build planner...</p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-display font-bold dark:text-white">Character Build Planner</h1>
        <div className="flex space-x-4">
          <button
            onClick={() => router.push('/builds')}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 bg-gray-200 dark:bg-gray-700 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            Browse Builds
          </button>
          <button
            onClick={() => setIsSaveDialogOpen(true)}
            className="px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 rounded-md transition-colors"
            disabled={saving}
          >
            {saving ? <LoadingSpinner size="small" /> : 'Save Build'}
          </button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Race & Class */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4 dark:text-white">Character Basics</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Character Name
                </label>
                <input
                  type="text"
                  value={buildName}
                  onChange={(e) => setBuildName(e.target.value)}
                  placeholder="Enter build name"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Level
                </label>
                <div className="flex items-center">
                  <input
                    type="range"
                    min="1"
                    max="50"
                    value={level}
                    onChange={handleLevelChange}
                    className="w-full"
                  />
                  <span className="ml-2 font-medium">{level}</span>
                </div>
              </div>
              
              <BuildRaceSelector
                races={races}
                selectedRace={selectedRace}
                onSelectRace={setSelectedRace}
              />
              
              <BuildClassSelector
                archetypes={archetypes}
                classes={classes}
                selectedClass={selectedClass}
                onSelectClass={setSelectedClass}
              />
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4 dark:text-white">Build Description</h2>
            <textarea
              value={buildDescription}
              onChange={(e) => setBuildDescription(e.target.value)}
              placeholder="Describe your build, its strengths, playstyle, etc."
              rows={6}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
            />
          </div>
        </div>
        
        {/* Right Column: Skills & Equipment */}
        <div className="lg:col-span-2 space-y-6">
          <BuildSkillSection 
            skills={skills}
            onSkillsChange={setSkills}
            selectedClass={selectedClass}
            level={level}
          />
          
          <BuildEquipmentSection
            equipment={equipment}
            onEquipmentChange={setEquipment}
          />
        </div>
      </div>
      
      {/* Save Dialog */}
      <BuildSaveDialog
        isOpen={isSaveDialogOpen}
        onClose={() => setIsSaveDialogOpen(false)}
        onSave={saveBuild}
        buildName={buildName}
        onBuildNameChange={setBuildName}
        isSaving={saving}
      />
    </div>
  )
}
