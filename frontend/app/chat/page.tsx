'use client'

import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'next/navigation'
import ReactMarkdown from 'react-markdown'
import { v4 as uuidv4 } from 'uuid'
import ChatInput from '@/components/chat/ChatInput'
import ChatMessage from '@/components/chat/ChatMessage'
import ServerSelector from '@/components/chat/ServerSelector'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import { useChatStore } from '@/stores/chatStore'
import { useServersStore } from '@/stores/serversStore'
import { Message, ContextDocument } from '@/types/chat'

export default function ChatPage() {
  const searchParams = useSearchParams()
  const chatContainerRef = useRef<HTMLDivElement>(null)
  const { messages, addMessage, setMessages, isLoading, setIsLoading } = useChatStore()
  const { selectedServer, servers } = useServersStore()
  const [initialQuery, setInitialQuery] = useState<string | null>(null)
  const [contextExpanded, setContextExpanded] = useState(false)
  const [contextDocuments, setContextDocuments] = useState<ContextDocument[]>([])
  
  useEffect(() => {
    // Check for query parameter and initialize chat
    const query = searchParams.get('q')
    if (query && messages.length === 0) {
      setInitialQuery(query)
    }
  }, [searchParams, messages.length])

  useEffect(() => {
    // Process initial query if present
    if (initialQuery) {
      handleSubmit(initialQuery)
      setInitialQuery(null)
    }
  }, [initialQuery])

  useEffect(() => {
    // Scroll to bottom when messages change
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [messages])

  const handleSubmit = async (content: string) => {
    // Skip empty messages
    if (!content.trim()) return

    // Add user message to chat
    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date()
    }
    addMessage(userMessage)
    setIsLoading(true)

    try {
      // Prepare the API request
      const apiMessages = messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }))
      
      apiMessages.push({
        role: 'user',
        content
      })

      // Call the API
      const response = await fetch('/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          messages: apiMessages,
          server: selectedServer || undefined,
          temperature: 0.7
        })
      })

      if (!response.ok) {
        throw new Error('Failed to get response from AI')
      }

      const data = await response.json()

      // Add assistant message to chat
      const assistantMessage: Message = {
        id: data.id || uuidv4(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date()
      }
      addMessage(assistantMessage)
      
      // Store context documents
      if (data.context_documents) {
        setContextDocuments(data.context_documents)
      }

    } catch (error) {
      console.error('Error:', error)
      
      // Add error message
      const errorMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      }
      addMessage(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const clearChat = () => {
    setMessages([])
    setContextDocuments([])
  }

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-6 flex flex-col h-full max-w-6xl">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-display font-bold dark:text-white">Ashes Assistant Chat</h1>
          <div className="flex items-center space-x-2">
            <ServerSelector />
            <button 
              onClick={clearChat}
              className="px-3 py-1 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 rounded-md text-sm font-medium transition-colors dark:text-white"
            >
              Clear Chat
            </button>
          </div>
        </div>

        <div className="flex-grow overflow-hidden flex">
          {/* Main chat area */}
          <div className="flex-grow overflow-hidden flex flex-col">
            <div 
              ref={chatContainerRef} 
              className="flex-grow overflow-y-auto p-4 space-y-4 mb-4 rounded-lg bg-white dark:bg-gray-800 shadow-sm"
            >
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center text-gray-500 dark:text-gray-400">
                  <div className="max-w-md">
                    <h2 className="text-xl font-semibold mb-2">Welcome to Ashes Assistant!</h2>
                    <p className="mb-6">Ask me anything about Ashes of Creation. I can help with items, locations, builds, crafting, and game mechanics.</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                      <button 
                        onClick={() => handleSubmit("Where can I find Western Larch wood?")}
                        className="p-2 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-left"
                      >
                        Where can I find Western Larch wood?
                      </button>
                      <button 
                        onClick={() => handleSubmit("What is the fastest way to level herbalism?")}
                        className="p-2 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-left"
                      >
                        What is the fastest way to level herbalism?
                      </button>
                      <button 
                        onClick={() => handleSubmit("Best tank class for PvE dungeons?")}
                        className="p-2 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-left"
                      >
                        Best tank class for PvE dungeons?
                      </button>
                      <button 
                        onClick={() => handleSubmit("How does the node system work?")}
                        className="p-2 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-left"
                      >
                        How does the node system work?
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((message) => (
                    <ChatMessage key={message.id} message={message} />
                  ))}
                  {isLoading && (
                    <div className="flex items-center px-4 py-2">
                      <LoadingSpinner />
                      <span className="ml-2 text-gray-500 dark:text-gray-400">Assistant is thinking...</span>
                    </div>
                  )}
                </div>
              )}
            </div>

            <ChatInput onSubmit={handleSubmit} isLoading={isLoading} />
          </div>
          
          {/* Context panel (only show when we have context) */}
          {contextDocuments.length > 0 && (
            <div className={`ml-4 w-80 rounded-lg bg-white dark:bg-gray-800 shadow-sm overflow-hidden flex flex-col transition-all ${contextExpanded ? 'flex' : 'hidden md:flex'}`}>
              <div className="p-3 bg-gray-100 dark:bg-gray-700 flex justify-between items-center">
                <h3 className="font-medium dark:text-white">Information Sources</h3>
                <button 
                  onClick={() => setContextExpanded(!contextExpanded)}
                  className="md:hidden text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                >
                  {contextExpanded ? 'Hide' : 'Show'}
                </button>
              </div>
              <div className="flex-grow overflow-y-auto p-3 text-sm">
                {contextDocuments.map((doc, index) => (
                  <div key={index} className="mb-4 pb-4 border-b border-gray-100 dark:border-gray-700 last:border-b-0">
                    <div className="font-medium mb-1 dark:text-white">{doc.source.split('/').pop() || doc.source}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                      Type: {doc.type} {doc.server && `| Server: ${doc.server}`}
                    </div>
                    <div className="text-gray-700 dark:text-gray-300 text-xs">
                      <ReactMarkdown>
                        {doc.text.length > 200 ? `${doc.text.substring(0, 200)}...` : doc.text}
                      </ReactMarkdown>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
