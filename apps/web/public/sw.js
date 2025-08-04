/**
 * Service Worker for Seiketsu AI Performance Optimization
 * Implements advanced caching strategies for optimal performance
 */

const CACHE_NAME = 'seiketsu-ai-v1.0.0'
const STATIC_CACHE = 'seiketsu-static-v1.0.0'
const DYNAMIC_CACHE = 'seiketsu-dynamic-v1.0.0'
const AUDIO_CACHE = 'seiketsu-audio-v1.0.0'

// Assets to cache immediately
const STATIC_ASSETS = [
  '/',
  '/dashboard',
  '/manifest.json',
  '/_next/static/css/app/layout.css',
  '/_next/static/chunks/webpack.js',
  '/_next/static/chunks/main.js',
  '/_next/static/chunks/pages/_app.js',
]

// Cache strategies by route pattern
const CACHE_STRATEGIES = {
  // Static assets - Cache First
  static: /\/_next\/static\//,
  
  // API calls - Network First with fallback
  api: /\/api\//,
  
  // Audio files - Cache First with long TTL
  audio: /\.(mp3|wav|ogg|webm|m4a)$/,
  
  // Images - Cache First with compression
  images: /\.(png|jpg|jpeg|gif|webp|svg|avif)$/,
  
  // Fonts - Cache First
  fonts: /\.(woff|woff2|eot|ttf|otf)$/,
  
  // Pages - Stale While Revalidate
  pages: /^https:\/\/seiketsu\.ai\//
}

// Install event - Cache static assets
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...')
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('Service Worker: Caching static assets')
        return cache.addAll(STATIC_ASSETS)
      })
      .then(() => {
        console.log('Service Worker: Installation complete')
        return self.skipWaiting()
      })
      .catch(error => {
        console.error('Service Worker: Installation failed', error)
      })
  )
})

// Activate event - Clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...')
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        const deletePromises = cacheNames
          .filter(cacheName => {
            return cacheName !== CACHE_NAME && 
                   cacheName !== STATIC_CACHE && 
                   cacheName !== DYNAMIC_CACHE &&
                   cacheName !== AUDIO_CACHE
          })
          .map(cacheName => {
            console.log('Service Worker: Deleting old cache', cacheName)
            return caches.delete(cacheName)
          })
        
        return Promise.all(deletePromises)
      })
      .then(() => {
        console.log('Service Worker: Activation complete')
        return self.clients.claim()
      })
  )
})

// Fetch event - Implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event
  const url = new URL(request.url)
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return
  }
  
  // Skip chrome-extension and other non-http requests
  if (!request.url.startsWith('http')) {
    return
  }
  
  // Apply appropriate caching strategy
  if (CACHE_STRATEGIES.static.test(request.url)) {
    event.respondWith(cacheFirst(request, STATIC_CACHE))
  } else if (CACHE_STRATEGIES.audio.test(request.url)) {
    event.respondWith(cacheFirstWithLongTTL(request, AUDIO_CACHE))
  } else if (CACHE_STRATEGIES.images.test(request.url)) {
    event.respondWith(cacheFirstWithCompression(request, STATIC_CACHE))
  } else if (CACHE_STRATEGIES.fonts.test(request.url)) {
    event.respondWith(cacheFirst(request, STATIC_CACHE))
  } else if (CACHE_STRATEGIES.api.test(request.url)) {
    event.respondWith(networkFirstWithFallback(request, DYNAMIC_CACHE))
  } else if (CACHE_STRATEGIES.pages.test(request.url)) {
    event.respondWith(staleWhileRevalidate(request, DYNAMIC_CACHE))
  } else {
    event.respondWith(networkFirstWithFallback(request, DYNAMIC_CACHE))
  }
})

// Cache First strategy - for static assets
async function cacheFirst(request, cacheName) {
  try {
    const cache = await caches.open(cacheName)
    const cachedResponse = await cache.match(request)
    
    if (cachedResponse) {
      // Serve from cache
      return cachedResponse
    }
    
    // Fetch from network and cache
    const networkResponse = await fetch(request)
    
    if (networkResponse.ok) {
      const responseClone = networkResponse.clone()
      cache.put(request, responseClone)
    }
    
    return networkResponse
  } catch (error) {
    console.error('Cache First failed:', error)
    return new Response('Service Unavailable', { status: 503 })
  }
}

// Cache First with Long TTL - for audio files
async function cacheFirstWithLongTTL(request, cacheName) {
  try {
    const cache = await caches.open(cacheName)
    const cachedResponse = await cache.match(request)
    
    if (cachedResponse) {
      // Check if cached response is still fresh (7 days)
      const cachedDate = new Date(cachedResponse.headers.get('date'))
      const maxAge = 7 * 24 * 60 * 60 * 1000 // 7 days in ms
      
      if (Date.now() - cachedDate.getTime() < maxAge) {
        return cachedResponse
      }
    }
    
    // Fetch fresh copy
    const networkResponse = await fetch(request)
    
    if (networkResponse.ok) {
      const responseClone = networkResponse.clone()
      
      // Add custom headers for long caching
      const modifiedResponse = new Response(responseClone.body, {
        status: responseClone.status,
        statusText: responseClone.statusText,
        headers: {
          ...Object.fromEntries(responseClone.headers.entries()),
          'Cache-Control': 'public, max-age=604800', // 7 days
          'date': new Date().toUTCString()
        }
      })
      
      cache.put(request, modifiedResponse.clone())
      return modifiedResponse
    }
    
    // Return cached version if network failed
    return cachedResponse || networkResponse
  } catch (error) {
    console.error('Cache First with Long TTL failed:', error)
    const cache = await caches.open(cacheName)
    return await cache.match(request) || new Response('Service Unavailable', { status: 503 })
  }
}

// Cache First with Compression - for images
async function cacheFirstWithCompression(request, cacheName) {
  try {
    const cache = await caches.open(cacheName)
    const cachedResponse = await cache.match(request)
    
    if (cachedResponse) {
      return cachedResponse
    }
    
    // Try to fetch WebP version first if browser supports it
    const acceptsWebP = request.headers.get('accept')?.includes('image/webp')
    let fetchRequest = request
    
    if (acceptsWebP && request.url.match(/\.(jpg|jpeg|png)$/)) {
      const webpUrl = request.url.replace(/\.(jpg|jpeg|png)$/, '.webp')
      fetchRequest = new Request(webpUrl, request)
    }
    
    const networkResponse = await fetch(fetchRequest)
    
    if (networkResponse.ok) {
      const responseClone = networkResponse.clone()
      cache.put(request, responseClone)
    }
    
    return networkResponse
  } catch (error) {
    console.error('Cache First with Compression failed:', error)
    return cacheFirst(request, cacheName) // Fallback to regular cache first
  }
}

// Network First with Fallback - for API calls
async function networkFirstWithFallback(request, cacheName) {
  try {
    // Try network first
    const networkResponse = await fetch(request)
    
    if (networkResponse.ok) {
      // Cache successful responses
      const cache = await caches.open(cacheName)
      const responseClone = networkResponse.clone()
      
      // Only cache GET requests and non-streaming responses
      if (request.method === 'GET' && !isStreamingResponse(networkResponse)) {
        cache.put(request, responseClone)
      }
      
      return networkResponse
    }
    
    throw new Error(`Network response not ok: ${networkResponse.status}`)
  } catch (error) {
    console.warn('Network First failed, trying cache:', error.message)
    
    // Fallback to cache
    const cache = await caches.open(cacheName)
    const cachedResponse = await cache.match(request)
    
    if (cachedResponse) {
      return cachedResponse
    }
    
    // Return offline page or error response
    return new Response(
      JSON.stringify({ error: 'Network unavailable', cached: false }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    )
  }
}

// Stale While Revalidate - for pages
async function staleWhileRevalidate(request, cacheName) {
  try {
    const cache = await caches.open(cacheName)
    const cachedResponse = await cache.match(request)
    
    // Start network request (don't await)
    const networkPromise = fetch(request)
      .then(networkResponse => {
        if (networkResponse.ok) {
          const responseClone = networkResponse.clone()
          cache.put(request, responseClone)
        }
        return networkResponse
      })
      .catch(error => {
        console.warn('Stale While Revalidate network update failed:', error)
      })
    
    // Return cached response immediately if available
    if (cachedResponse) {
      // Update cache in background
      networkPromise.catch(() => {}) // Prevent unhandled rejection
      return cachedResponse
    }
    
    // Wait for network if no cache
    return await networkPromise
  } catch (error) {
    console.error('Stale While Revalidate failed:', error)
    return new Response('Service Unavailable', { status: 503 })
  }
}

// Utility function to check if response is streaming
function isStreamingResponse(response) {
  const contentType = response.headers.get('content-type') || ''
  return contentType.includes('text/event-stream') || 
         contentType.includes('application/stream') ||
         response.headers.get('transfer-encoding') === 'chunked'
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(handleBackgroundSync())
  }
})

async function handleBackgroundSync() {
  try {
    // Handle any offline actions stored in IndexedDB
    console.log('Background sync triggered')
    
    // This would integrate with your offline action queue
    // For now, just log the event
  } catch (error) {
    console.error('Background sync failed:', error)
  }
}

// Push notification handling
self.addEventListener('push', (event) => {
  if (!event.data) return
  
  try {
    const data = event.data.json()
    const options = {
      body: data.body,
      icon: '/icon-192x192.png',
      badge: '/badge-72x72.png',
      tag: data.tag || 'default',
      data: data.data || {},
      actions: data.actions || [],
      requireInteraction: data.requireInteraction || false
    }
    
    event.waitUntil(
      self.registration.showNotification(data.title, options)
    )
  } catch (error) {
    console.error('Push notification failed:', error)
  }
})

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  
  const data = event.notification.data || {}
  const url = data.url || '/'
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then(clientList => {
        // Check if a window is already open
        for (const client of clientList) {
          if (client.url === url && 'focus' in client) {
            return client.focus()
          }
        }
        
        // Open new window
        if (clients.openWindow) {
          return clients.openWindow(url)
        }
      })
  )
})

// Message handling for communication with main thread
self.addEventListener('message', (event) => {
  const { type, data } = event.data
  
  switch (type) {
    case 'SKIP_WAITING':
      self.skipWaiting()
      break
      
    case 'CACHE_AUDIO':
      event.waitUntil(cacheAudioFile(data.url))
      break
      
    case 'CLEAR_CACHE':
      event.waitUntil(clearSpecificCache(data.cacheName))
      break
      
    case 'GET_CACHE_SIZE':
      event.waitUntil(getCacheSize().then(size => {
        event.ports[0]?.postMessage({ type: 'CACHE_SIZE', size })
      }))
      break
      
    default:
      console.warn('Unknown message type:', type)
  }
})

// Helper function to cache audio files
async function cacheAudioFile(url) {
  try {
    const cache = await caches.open(AUDIO_CACHE)
    const response = await fetch(url)
    
    if (response.ok) {
      await cache.put(url, response)
      console.log('Audio file cached:', url)
    }
  } catch (error) {
    console.error('Failed to cache audio file:', error)
  }
}

// Helper function to clear specific cache
async function clearSpecificCache(cacheName) {
  try {
    await caches.delete(cacheName)
    console.log('Cache cleared:', cacheName)
  } catch (error) {
    console.error('Failed to clear cache:', error)
  }
}

// Helper function to get total cache size
async function getCacheSize() {
  try {
    const cacheNames = await caches.keys()
    let totalSize = 0
    
    for (const cacheName of cacheNames) {
      const cache = await caches.open(cacheName)
      const keys = await cache.keys()
      
      for (const request of keys) {
        const response = await cache.match(request)
        if (response) {
          const blob = await response.blob()
          totalSize += blob.size
        }
      }
    }
    
    return totalSize
  } catch (error) {
    console.error('Failed to calculate cache size:', error)
    return 0
  }
}

console.log('Seiketsu AI Service Worker loaded successfully')