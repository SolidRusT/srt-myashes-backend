'use client'

import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="bg-gray-100 dark:bg-gray-800/50 border-t border-gray-200 dark:border-gray-700">
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row md:justify-between">
          <div className="mb-6 md:mb-0">
            <h2 className="text-xl font-display font-bold text-gray-900 dark:text-white mb-4">MyAshes.ai</h2>
            <p className="text-gray-600 dark:text-gray-300 max-w-md">
              The ultimate AI-powered assistant for Ashes of Creation. Get answers, plan builds, and optimize your gameplay.
            </p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-3 gap-8">
            <div>
              <h3 className="text-sm font-semibold text-gray-400 dark:text-gray-300 uppercase tracking-wider mb-4">Features</h3>
              <ul className="space-y-3">
                <li>
                  <Link href="/chat" className="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400">
                    AI Assistant
                  </Link>
                </li>
                <li>
                  <Link href="/builds" className="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400">
                    Build Planner
                  </Link>
                </li>
                <li>
                  <Link href="/crafting" className="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400">
                    Crafting Calculator
                  </Link>
                </li>
                <li>
                  <Link href="/map" className="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400">
                    Interactive Map
                  </Link>
                </li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-sm font-semibold text-gray-400 dark:text-gray-300 uppercase tracking-wider mb-4">Resources</h3>
              <ul className="space-y-3">
                <li>
                  <a 
                    href="https://ashesofcreation.wiki" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                  >
                    Official Wiki
                  </a>
                </li>
                <li>
                  <a 
                    href="https://ashesofcreation.com" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                  >
                    Official Website
                  </a>
                </li>
                <li>
                  <a 
                    href="https://ashescodex.com" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                  >
                    Ashes Codex
                  </a>
                </li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-sm font-semibold text-gray-400 dark:text-gray-300 uppercase tracking-wider mb-4">Connect</h3>
              <ul className="space-y-3">
                <li>
                  <a 
                    href="https://discord.gg/myashes" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                  >
                    Discord
                  </a>
                </li>
                <li>
                  <Link href="/contact" className="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400">
                    Contact Us
                  </Link>
                </li>
                <li>
                  <Link href="/about" className="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400">
                    About
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>
        
        <div className="mt-8 border-t border-gray-200 dark:border-gray-700 pt-8 flex flex-col md:flex-row justify-between items-center">
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            &copy; {new Date().getFullYear()} MyAshes.ai. All rights reserved.
          </p>
          <div className="mt-4 md:mt-0 flex space-x-6">
            <Link href="/privacy" className="text-gray-500 dark:text-gray-400 text-sm hover:text-gray-700 dark:hover:text-gray-300">
              Privacy Policy
            </Link>
            <Link href="/terms" className="text-gray-500 dark:text-gray-400 text-sm hover:text-gray-700 dark:hover:text-gray-300">
              Terms of Service
            </Link>
          </div>
        </div>
        
        <div className="mt-6 text-center text-xs text-gray-500 dark:text-gray-400">
          <p>
            MyAshes.ai is a fan project and is not affiliated with Intrepid Studios. Ashes of Creation™ is a registered trademark of Intrepid Studios Inc.
          </p>
        </div>
      </div>
    </footer>
  )
}
