/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  images: {
    domains: ['ashesofcreation.com', 'ashesofcreation.wiki', 'ashescodex.com'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/:path*` : 'http://backend:8000/:path*',
      },
    ]
  },
}

module.exports = nextConfig
