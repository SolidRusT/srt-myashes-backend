'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { useSearchParams } from 'next/navigation'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import ServerStatusCard from '@/components/dashboard/ServerStatusCard'
import QuickChatCard from '@/components/dashboard/QuickChatCard'
import RecentBuildsCard from '@/components/dashboard/RecentBuildsCard'
import PopularResourcesCard from '@/components/dashboard/PopularResourcesCard'

type Server = {
  name: string
  status: string
  population?: string
}

export default function DashboardPage() {
  const searchParams = useSearchParams()
  
  // States
  const [loading, setLoading] = useState(true)
  const [servers, setServers] = useState<Server[]>([])
  const [recentBuilds, setRecentBuilds] = useState([])
  const [popularResources, setPopularResources] = useState([])
  
  // Fetch data on component mount
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      
      try {
        // Fetch server statuses
        const serversRes = await fetch('/api/v1/servers')
        const serversData = await serversRes.json()
        setServers(serversData.servers)
        
        // Fetch recent builds
        const buildsRes = await fetch('/api/v1/builds?limit=5')
        const buildsData = await buildsRes.json()
        setRecentBuilds(buildsData)
        
        // Fetch popular resources
        const resourcesRes = await fetch('/api/v1/resources/popular')
        const resourcesData = await resourcesRes.json()
        setPopularResources(resourcesData)
        
      } catch (error) {
        console.error('Error fetching dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchData()
  }, [])
  
  // Check if user was redirected from login
  useEffect(() => {
    const welcome = searchParams.get('welcome')
    if (welcome === 'true') {
      // Show welcome message or notification
      console.log('Welcome to the dashboard!')
    }
  }, [searchParams])
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-64px)]">
        <div className="text-center">
          <LoadingSpinner size="large" />
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-display font-bold mb-8 dark:text-white">Dashboard</h1>
      
      {/* Quick action buttons */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Link 
          href="/chat"
          className="flex flex-col items-center p-4 bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 text-white rounded-lg transition-colors text-center"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          <span>Ask Assistant</span>
        </Link>
        
        <Link 
          href="/builds/new"
          className="flex flex-col items-center p-4 bg-purple-600 hover:bg-purple-700 dark:bg-purple-700 dark:hover:bg-purple-800 text-white rounded-lg transition-colors text-center"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span>Create Build</span>
        </Link>
        
        <Link 
          href="/items"
          className="flex flex-col items-center p-4 bg-green-600 hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-800 text-white rounded-lg transition-colors text-center"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
          <span>Item Database</span>
        </Link>
        
        <Link 
          href="/crafting"
          className="flex flex-col items-center p-4 bg-yellow-600 hover:bg-yellow-700 dark:bg-yellow-700 dark:hover:bg-yellow-800 text-white rounded-lg transition-colors text-center"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
          <span>Crafting Planner</span>
        </Link>
      </div>
      
      {/* Main dashboard content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left column */}
        <div className="lg:col-span-2 space-y-8">
          {/* Server status section */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4 dark:text-white">Server Status</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {servers.map((server) => (
                <ServerStatusCard key={server.name} server={server} />
              ))}
            </div>
          </div>
          
          {/* Recent builds section */}
          <RecentBuildsCard builds={recentBuilds} />
        </div>
        
        {/* Right column */}
        <div className="space-y-8">
          {/* Quick chat section */}
          <QuickChatCard />
          
          {/* Popular resources section */}
          <PopularResourcesCard resources={popularResources} />
          
          {/* Community links section */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4 dark:text-white">Community Links</h2>
            <div className="space-y-3">
              <a
                href="https://discord.gg/myashes"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center p-3 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg hover:bg-indigo-200 dark:hover:bg-indigo-800/30 transition-colors"
              >
                <div className="w-8 h-8 flex items-center justify-center bg-indigo-500 text-white rounded-full mr-3">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/>
                  </svg>
                </div>
                <span className="text-indigo-900 dark:text-indigo-100">Join our Discord</span>
              </a>
              
              <a
                href="https://ashesofcreation.wiki"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-800/30 transition-colors"
              >
                <div className="w-8 h-8 flex items-center justify-center bg-blue-500 text-white rounded-full mr-3">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <span className="text-blue-900 dark:text-blue-100">Official Wiki</span>
              </a>
              
              <a
                href="https://ashescodex.com"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center p-3 bg-green-100 dark:bg-green-900/30 rounded-lg hover:bg-green-200 dark:hover:bg-green-800/30 transition-colors"
              >
                <div className="w-8 h-8 flex items-center justify-center bg-green-500 text-white rounded-full mr-3">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                  </svg>
                </div>
                <span className="text-green-900 dark:text-green-100">Ashes Codex</span>
              </a>
              
              <a
                href="https://ashesofcreation.com"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center p-3 bg-red-100 dark:bg-red-900/30 rounded-lg hover:bg-red-200 dark:hover:bg-red-800/30 transition-colors"
              >
                <div className="w-8 h-8 flex items-center justify-center bg-red-500 text-white rounded-full mr-3">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                  </svg>
                </div>
                <span className="text-red-900 dark:text-red-100">Official Website</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
