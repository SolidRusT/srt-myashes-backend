'use client'

import { Suspense } from 'react'
import LoadingSpinner from '@/components/common/LoadingSpinner'

function CraftingContent() {
  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-6">Crafting Calculator</h1>
      <p className="text-gray-500 dark:text-gray-400">
        This feature is under development. Check back soon!
      </p>
    </div>
  )
}

export default function CraftingPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-[calc(100vh-64px)]">
        <div className="text-center">
          <LoadingSpinner size="large" />
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading crafting calculator...</p>
        </div>
      </div>
    }>
      <CraftingContent />
    </Suspense>
  )
}
