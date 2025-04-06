'use client'

import { Suspense } from 'react'
import ChatContent from '@/components/chat/ChatContent'
import LoadingSpinner from '@/components/common/LoadingSpinner'

export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-[calc(100vh-64px)] bg-gray-50 dark:bg-gray-900">
        <div className="flex flex-col items-center">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-gray-500 dark:text-gray-400">Loading chat interface...</p>
        </div>
      </div>
    }>
      <ChatContent />
    </Suspense>
  )
}
