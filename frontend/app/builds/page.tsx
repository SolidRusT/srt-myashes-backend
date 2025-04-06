'use client'

import { Suspense } from 'react'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import BuildPlannerContent from '@/components/builds/BuildPlannerContent'

export default function BuildPlannerPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-[calc(100vh-64px)]">
        <div className="text-center">
          <LoadingSpinner size="large" />
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading build planner...</p>
        </div>
      </div>
    }>
      <BuildPlannerContent />
    </Suspense>
  )
}
