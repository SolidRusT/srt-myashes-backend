'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function QuickChatCard() {
  const router = useRouter()
  const [inputValue, setInputValue] = useState('')
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (inputValue.trim()) {
      // Redirect to chat page with query parameter
      router.push(`/chat?q=${encodeURIComponent(inputValue)}`)
    }
  }
  
  // Quick question suggestions
  const suggestions = [
    "Where can I find iron ore?",
    "Best class for solo PvE?",
    "How does node progression work?",
    "What materials do I need for a steel sword?"
  ]
  
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4 dark:text-white">Quick Chat</h2>
      
      <form onSubmit={handleSubmit} className="mb-4">
        <div className="flex">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask anything about Ashes of Creation..."
            className="flex-grow px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-l-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 text-white rounded-r-md transition-colors"
          >
            Ask
          </button>
        </div>
      </form>
      
      <div className="space-y-2">
        <p className="text-sm text-gray-600 dark:text-gray-400">Try asking:</p>
        <div className="grid grid-cols-1 gap-2">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => router.push(`/chat?q=${encodeURIComponent(suggestion)}`)}
              className="text-left text-sm p-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors text-gray-800 dark:text-gray-200"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
