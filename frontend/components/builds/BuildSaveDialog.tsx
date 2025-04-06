'use client'

// Placeholder component - implement actual functionality as needed
export default function BuildSaveDialog({ isOpen, onClose, onSave, buildName, onBuildNameChange, isSaving }: any) {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-semibold mb-4 dark:text-white">Save Build</h2>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Build Name
          </label>
          <input
            type="text"
            value={buildName}
            onChange={(e) => onBuildNameChange(e.target.value)}
            placeholder="Enter build name"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md"
          />
        </div>
        
        <div className="flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 bg-gray-200 dark:bg-gray-700 rounded-md"
          >
            Cancel
          </button>
          <button
            onClick={onSave}
            className="px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 rounded-md"
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : 'Save Build'}
          </button>
        </div>
      </div>
    </div>
  )
}
