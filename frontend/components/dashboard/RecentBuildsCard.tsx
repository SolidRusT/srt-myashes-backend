'use client'

import Link from 'next/link'

// Types
type BuildClass = {
  primary: string
  secondary: string
  classType: string
}

type Build = {
  id: string
  name: string
  race: string
  classes: BuildClass
  level: number
  created_at: string
  user_id?: string
}

interface RecentBuildsCardProps {
  builds: Build[]
}

export default function RecentBuildsCard({ builds }: RecentBuildsCardProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold dark:text-white">Recent Character Builds</h2>
        <Link
          href="/builds"
          className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
        >
          View All
        </Link>
      </div>
      
      {builds && builds.length > 0 ? (
        <div className="space-y-4">
          {builds.map((build) => (
            <Link
              key={build.id}
              href={`/builds/${build.id}`}
              className="block p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="font-medium dark:text-white">{build.name}</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {build.race} {build.classes.classType} (Level {build.level})
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-xs text-gray-500 dark:text-gray-500">
                    {new Date(build.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="py-8 text-center text-gray-500 dark:text-gray-400">
          <p>No builds have been created yet.</p>
          <Link
            href="/builds/new"
            className="mt-4 inline-block px-4 py-2 bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 text-white rounded-md transition-colors"
          >
            Create a Build
          </Link>
        </div>
      )}
    </div>
  )
}
