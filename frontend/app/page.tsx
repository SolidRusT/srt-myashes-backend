'use client'

import { useState } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'

export default function Home() {
  const router = useRouter()
  const [searchQuery, setSearchQuery] = useState('')

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      router.push(`/chat?q=${encodeURIComponent(searchQuery)}`)
    }
  }

  return (
    <div className="flex flex-col min-h-[calc(100vh-64px)]">
      {/* Hero Section */}
      <section className="relative flex items-center justify-center py-20 px-4 md:py-32 overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0 z-0">
          <Image
            src="/images/ashes-hero-bg.jpg"
            alt="Ashes of Creation"
            fill
            priority
            className="object-cover"
            quality={90}
          />
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm"></div>
        </div>

        {/* Content */}
        <div className="relative z-10 max-w-5xl mx-auto text-center">
          <motion.h1 
            className="text-4xl md:text-6xl font-display font-bold text-white mb-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            Your Ultimate <span className="text-ashes-gold">Ashes of Creation</span> Assistant
          </motion.h1>
          
          <motion.p 
            className="text-xl md:text-2xl text-gray-200 mb-8 max-w-3xl mx-auto"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            Get answers to all your questions, plan your character builds, and master the world of Verra.
          </motion.p>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <form onSubmit={handleSearch} className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-8">
              <input
                type="text"
                placeholder="Ask anything about Ashes of Creation..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full sm:w-96 px-4 py-3 rounded-lg bg-white/10 backdrop-blur-md border border-white/20 text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-ashes-gold"
              />
              <button
                type="submit"
                className="px-6 py-3 bg-ashes-gold hover:bg-yellow-500 text-black font-semibold rounded-lg transition-colors w-full sm:w-auto"
              >
                Ask Now
              </button>
            </form>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 px-4 bg-white dark:bg-gray-900">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-display font-bold text-center mb-12 dark:text-white">
            Everything You Need to Conquer Verra
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <motion.div 
              className="game-card p-6"
              whileHover={{ y: -10 }}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              viewport={{ once: true }}
            >
              <div className="h-12 w-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-blue-600 dark:text-blue-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold mb-2 dark:text-white">AI-Powered Assistant</h3>
              <p className="text-gray-600 dark:text-gray-300">
                Get instant answers to your questions about items, locations, crafting recipes, and gameplay mechanics.
              </p>
              <Link href="/chat" className="mt-4 inline-block text-blue-600 dark:text-blue-400 font-medium hover:underline">
                Start Chatting →
              </Link>
            </motion.div>

            {/* Feature 2 */}
            <motion.div 
              className="game-card p-6"
              whileHover={{ y: -10 }}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              viewport={{ once: true }}
            >
              <div className="h-12 w-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-purple-600 dark:text-purple-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold mb-2 dark:text-white">Character Build Planner</h3>
              <p className="text-gray-600 dark:text-gray-300">
                Create optimized character builds with our interactive planner. Experiment with different classes, skills, and gear.
              </p>
              <Link href="/builds" className="mt-4 inline-block text-purple-600 dark:text-purple-400 font-medium hover:underline">
                Plan Your Build →
              </Link>
            </motion.div>

            {/* Feature 3 */}
            <motion.div 
              className="game-card p-6"
              whileHover={{ y: -10 }}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              viewport={{ once: true }}
            >
              <div className="h-12 w-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-green-600 dark:text-green-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                </svg>
              </div>
              <h3 className="text-xl font-bold mb-2 dark:text-white">Crafting Calculator</h3>
              <p className="text-gray-600 dark:text-gray-300">
                Calculate required materials for any crafting project. Optimize your gathering routes and track your progress.
              </p>
              <Link href="/crafting" className="mt-4 inline-block text-green-600 dark:text-green-400 font-medium hover:underline">
                Start Crafting →
              </Link>
            </motion.div>

            {/* Feature 4 */}
            <motion.div 
              className="game-card p-6"
              whileHover={{ y: -10 }}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              viewport={{ once: true }}
            >
              <div className="h-12 w-12 bg-red-100 dark:bg-red-900 rounded-lg flex items-center justify-center mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-red-600 dark:text-red-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold mb-2 dark:text-white">Interactive World Map</h3>
              <p className="text-gray-600 dark:text-gray-300">
                Explore Verra with our detailed map. Find resource nodes, dungeons, cities, and other points of interest.
              </p>
              <Link href="/map" className="mt-4 inline-block text-red-600 dark:text-red-400 font-medium hover:underline">
                Explore Map →
              </Link>
            </motion.div>

            {/* Feature 5 */}
            <motion.div 
              className="game-card p-6"
              whileHover={{ y: -10 }}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              viewport={{ once: true }}
            >
              <div className="h-12 w-12 bg-yellow-100 dark:bg-yellow-900 rounded-lg flex items-center justify-center mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-yellow-600 dark:text-yellow-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold mb-2 dark:text-white">Economy Tracker</h3>
              <p className="text-gray-600 dark:text-gray-300">
                Stay updated on item values and market trends. Make smarter decisions for trading and investments.
              </p>
              <Link href="/economy" className="mt-4 inline-block text-yellow-600 dark:text-yellow-400 font-medium hover:underline">
                Check Prices →
              </Link>
            </motion.div>

            {/* Feature 6 */}
            <motion.div 
              className="game-card p-6"
              whileHover={{ y: -10 }}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.5 }}
              viewport={{ once: true }}
            >
              <div className="h-12 w-12 bg-indigo-100 dark:bg-indigo-900 rounded-lg flex items-center justify-center mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-indigo-600 dark:text-indigo-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold mb-2 dark:text-white">Discord Integration</h3>
              <p className="text-gray-600 dark:text-gray-300">
                Access all features directly from Discord. Get quick answers and share information with your guild.
              </p>
              <a href="https://discord.gg/myashes" target="_blank" rel="noopener noreferrer" className="mt-4 inline-block text-indigo-600 dark:text-indigo-400 font-medium hover:underline">
                Join Discord →
              </a>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Call to Action */}
      <section className="py-16 px-4 bg-ashes-dark text-white">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-display font-bold mb-6">Ready to Enhance Your Ashes of Creation Experience?</h2>
          <p className="text-xl text-gray-300 mb-8">
            Join thousands of players who are already using MyAshes.ai to get ahead in the game.
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <Link href="/chat" className="px-8 py-3 bg-ashes-gold hover:bg-yellow-500 text-black font-semibold rounded-lg transition-colors">
              Get Started
            </Link>
            <Link href="/about" className="px-8 py-3 bg-transparent hover:bg-white/10 border border-white rounded-lg font-semibold transition-colors">
              Learn More
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
