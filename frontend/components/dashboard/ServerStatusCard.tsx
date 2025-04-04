'use client'

type Server = {
  name: string
  status: string
  population?: string
}

interface ServerStatusCardProps {
  server: Server
}

export default function ServerStatusCard({ server }: ServerStatusCardProps) {
  // Helper function to get status indicator color
  const getStatusColor = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'online':
        return 'bg-green-500';
      case 'maintenance':
        return 'bg-yellow-500';
      case 'offline':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  }
  
  // Helper function to get population indicator
  const getPopulationIndicator = (population?: string) => {
    if (!population) return null
    
    let color = 'bg-gray-500'
    let width = 'w-1/4'
    
    switch (population.toLowerCase()) {
      case 'low':
        color = 'bg-green-500'
        width = 'w-1/4'
        break
      case 'medium':
        color = 'bg-yellow-500'
        width = 'w-2/4'
        break
      case 'high':
        color = 'bg-orange-500'
        width = 'w-3/4'
        break
      case 'full':
        color = 'bg-red-500'
        width = 'w-full'
        break
    }
    
    return (
      <div className="mt-2">
        <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">
          Population: {population}
        </div>
        <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div className={`h-full ${color} ${width}`}></div>
        </div>
      </div>
    )
  }
  
  return (
    <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800">
      <div className="flex justify-between items-center">
        <h3 className="font-medium dark:text-white">{server.name}</h3>
        <div className="flex items-center">
          <span className={`h-3 w-3 rounded-full ${getStatusColor(server.status)} mr-2`}></span>
          <span className="text-sm text-gray-600 dark:text-gray-400">{server.status}</span>
        </div>
      </div>
      
      {getPopulationIndicator(server.population)}
    </div>
  )
}
