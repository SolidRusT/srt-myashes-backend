'use client'

import { useState, useRef, useEffect } from 'react'

interface ChatInputProps {
  onSubmit: (message: string) => void
  isLoading: boolean
}

export default function ChatInput({ onSubmit, isLoading }: ChatInputProps) {
  const [message, setMessage] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Adjust textarea height based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [message])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim() && !isLoading) {
      onSubmit(message)
      setMessage('')
      
      // Reset height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter without Shift
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div className="flex items-end border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden bg-white dark:bg-gray-700 shadow-sm">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything about Ashes of Creation..."
          className="flex-grow px-4 py-3 max-h-[200px] min-h-[56px] resize-none focus:outline-none bg-transparent text-gray-800 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
          disabled={isLoading}
          rows={1}
        />
        <button
          type="submit"
          className={`px-4 py-3 text-white font-medium rounded-r-lg transition-colors ${
            isLoading || !message.trim()
              ? 'bg-gray-400 dark:bg-gray-600 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800'
          }`}
          disabled={isLoading || !message.trim()}
        >
          {isLoading ? (
            <div className="w-6 h-6 flex items-center justify-center">
              <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
            </div>
          ) : (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="w-6 h-6"
            >
              <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
            </svg>
          )}
        </button>
      </div>
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
        Press Enter to send, Shift+Enter for a new line
      </p>
    </form>
  )
}
