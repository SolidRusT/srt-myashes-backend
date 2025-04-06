'use client'

import { Suspense } from 'react'
import LoadingSpinner from '@/components/common/LoadingSpinner'

function ItemsContent() {
  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-6">Item Database</h1>
      <p className="text-gray-500 dark:text-gray-400">
        Browse all items in Ashes of Creation
      </p>
    </div>
  )
}

export default function ItemsPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-[calc(100vh-64px)]">
        <div className="text-center">
          <LoadingSpinner size="large" />
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading item database...</p>
        </div>
      </div>
    }>
      <ItemsContent />
    </Suspense>
  )
}
