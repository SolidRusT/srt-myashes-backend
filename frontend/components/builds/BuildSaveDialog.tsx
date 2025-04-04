'use client'

import LoadingSpinner from '@/components/common/LoadingSpinner'

interface BuildSaveDialogProps {
  isOpen: boolean
  onClose: () => void
  onSave: () => void
  buildName: string
  onBuildNameChange: (name: string) => void
  isSaving: boolean
}

export default function BuildSaveDialog({
  isOpen,
  onClose,
  onSave,
  buildName,
  onBuildNameChange,
  isSaving
}: BuildSaveDialogProps) {
  if (!isOpen) return null
  
  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div 
          className="fixed inset-0 transition-opacity" 
          onClick={onClose}
        >
          <div className="absolute inset-0 bg-black opacity-50"></div>
        </div>
        
        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <div className="px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="sm:flex sm:items-start">
              <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 dark:bg-blue-900 sm:mx-0 sm:h-10 sm:w-10">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-blue-600 dark:text-blue-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                </svg>
              </div>
              <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                  Save Build
                </h3>
                <div className="mt-2">
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Your build will be saved and can be shared with the community. Please give it a descriptive name.
                  </p>
                  
                  <div className="mt-4">
                    <label htmlFor="buildName" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Build Name *
                    </label>
                    <input
                      type="text"
                      id="buildName"
                      value={buildName}
                      onChange={(e) => onBuildNameChange(e.target.value)}
                      placeholder="Enter a descriptive name for your build"
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600"
                      required
                    />
                    {!buildName && (
                      <p className="mt-1 text-xs text-red-500">
                        Build name is required
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              onClick={onSave}
              disabled={!buildName || isSaving}
              className={`w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 text-base font-medium text-white sm:ml-3 sm:w-auto sm:text-sm ${
                !buildName || isSaving
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800'
              } transition-colors`}
            >
              {isSaving ? <LoadingSpinner size="small" /> : 'Save Build'}
            </button>
            <button
              type="button"
              onClick={onClose}
              disabled={isSaving}
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 dark:border-gray-600 shadow-sm px-4 py-2 bg-white dark:bg-gray-800 text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
