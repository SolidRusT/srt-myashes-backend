'use client'

import { useEffect } from 'react'
import { useServersStore } from '@/stores/serversStore'

export default function ServerSelector() {
  const { servers, selectedServer, selectServer } = useServersStore()
  
  // Fetch servers list from API (if needed)
  useEffect(() => {
    const fetchServers = async () => {
      try {
        console.log('Fetching servers list...');
        const response = await fetch('/api/v1/servers')
        if (response.ok) {
          const data = await response.json()
          console.log('Servers API response:', data);
          if (data.servers && Array.isArray(data.servers)) {
            // Extract server names from the response
            const serverNames = data.servers.map(server => server.name);
            useServersStore.getState().setServers(serverNames);
          }
        } else {
          console.error('Error fetching servers:', response.status, response.statusText);
        }
      } catch (error) {
        console.error('Error fetching servers:', error);
      }
    }
    
    // Only fetch if we have the default servers (could add a stale check too)
    if (servers.length <= 2) {
      fetchServers();
    }
  }, [servers.length])
  
  return (
    <div className="relative w-48">
      <select
        value={selectedServer || ''}
        onChange={(e) => selectServer(e.target.value || null)}
        className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 py-2 pl-3 pr-10 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
      >
        <option value="">All Servers</option>
        {servers.map((server) => (
          <option key={server} value={server}>
            {server}
          </option>
        ))}
      </select>
      <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700 dark:text-gray-300">
        <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </div>
    </div>
  )
}
