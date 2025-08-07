/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: false,
  },
  eslint: {
    ignoreDuringBuilds: false,
  },
  // Performance optimizations
  compress: true,
  poweredByHeader: false,
  generateEtags: false,
  
  // Bundle optimization
  swcMinify: true,
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production' ? {
      exclude: ['error', 'warn']
    } : false,
  },
  // PWA Configuration
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
        ],
      },
    ]
  },
  // Multi-tenant routing support
  async rewrites() {
    return [
      {
        source: '/org/:org/dashboard/:path*',
        destination: '/dashboard/:path*?org=:org',
      },
      {
        source: '/org/:org/agents/:path*',
        destination: '/agents/:path*?org=:org',
      },
      {
        source: '/org/:org/leads/:path*',
        destination: '/leads/:path*?org=:org',
      },
      {
        source: '/org/:org/analytics/:path*',
        destination: '/analytics/:path*?org=:org',
      },
    ]
  },
  // Image optimization for enterprise
  images: {
    domains: ['localhost', 'seiketsu.ai'],
    formats: ['image/webp', 'image/avif'],
  },
  // Webpack optimizations
  webpack: (config, { isServer, dev }) => {
    if (!isServer) {
      config.resolve.fallback.fs = false
    }
    
    // Performance optimizations
    if (!dev) {
      // Enable webpack 5 optimizations
      config.optimization = {
        ...config.optimization,
        moduleIds: 'deterministic',
        chunkIds: 'deterministic',
        mangleExports: 'deterministic',
        usedExports: true,
        sideEffects: false,
        splitChunks: {
          chunks: 'all',
          cacheGroups: {
            vendor: {
              test: /[\\/]node_modules[\\/]/,
              name: 'vendors',
              chunks: 'all',
              priority: 10,
              reuseExistingChunk: true,
            },
            voice: {
              test: /[\\/](voice|audio)[\\/]/,
              name: 'voice-engine',
              chunks: 'all',
              priority: 20,
              reuseExistingChunk: true,
            },
            common: {
              name: 'common',
              minChunks: 2,
              chunks: 'all',
              priority: 5,
              reuseExistingChunk: true,
            },
          },
        },
      }
      
      // Tree shaking optimization
      config.resolve.alias = {
        ...config.resolve.alias,
        'lodash': 'lodash-es',
      }
    }
    
    // Audio/Voice specific optimizations
    config.resolve.alias = {
      ...config.resolve.alias,
      '@voice': '/lib/voice-ai',
    }
    
    return config
  },
}

module.exports = nextConfig