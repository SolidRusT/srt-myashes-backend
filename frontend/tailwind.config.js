/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f5f7ff',
          100: '#ebefff',
          200: '#d6ddff',
          300: '#b6c1ff',
          400: '#8f9bff',
          500: '#6b77ff',
          600: '#5a63f7',
          700: '#4a4ee6',
          800: '#3e40b9',
          900: '#343a93',
          950: '#1e2051',
        },
        secondary: {
          50: '#fef2f4',
          100: '#fde6e9',
          200: '#fad0d9',
          300: '#f7aabb',
          400: '#f27b94',
          500: '#e84c70',
          600: '#d62f5c',
          700: '#b1214a',
          800: '#931f41',
          900: '#7c1e3a',
          950: '#450b1c',
        },
        ashes: {
          dark: '#1F2028',
          light: '#F8F9FA',
          gold: '#F4B942',
          red: '#BF4052',
          blue: '#2B80C5',
          green: '#4CAF50',
          purple: '#7E57C2',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
        serif: ['Lora', 'ui-serif', 'Georgia'],
        mono: ['Fira Code', 'ui-monospace', 'SFMono-Regular'],
        display: ['Cinzel', 'serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
