/**
 * Bundle Optimizer for Seiketsu AI
 * Dynamic imports and code splitting for optimal loading
 */

interface BundleConfig {
  enableDynamicImports: boolean
  preloadCritical: boolean
  enableServiceWorker: boolean
  cacheStrategy: 'cache-first' | 'network-first' | 'stale-while-revalidate'
}

class BundleOptimizer {
  private config: BundleConfig
  private loadedModules: Map<string, any> = new Map()
  private loadingPromises: Map<string, Promise<any>> = new Map()

  constructor(config: Partial<BundleConfig> = {}) {
    this.config = {
      enableDynamicImports: true,
      preloadCritical: true,
      enableServiceWorker: true,
      cacheStrategy: 'stale-while-revalidate',
      ...config,
    }

    if (this.config.preloadCritical) {
      this.preloadCriticalModules()
    }
  }

  /**
   * Preload critical modules for instant access
   */
  private async preloadCriticalModules(): Promise<void> {
    const criticalModules = [
      'voice-engine',
      'audio-processor',
      'websocket-client',
    ]

    await Promise.all(
      criticalModules.map(module => this.preloadModule(module))
    )
  }

  /**
   * Preload a module without executing it
   */
  private async preloadModule(moduleName: string): Promise<void> {
    if (typeof window === 'undefined') return

    const moduleMap: Record<string, () => Promise<any>> = {
      'voice-engine': () => import('@/lib/voice-ai/engine/voice-engine'),
      'audio-processor': () => import('@/lib/voice-ai/utils/audio'),
      'websocket-client': () => import('@/lib/performance/websocket-optimizer'),
      'conversation-manager': () => import('@/lib/voice-ai/conversation/conversation-manager'),
      'lead-qualification': () => import('@/lib/voice-ai/qualification/lead-qualifier'),
    }

    const importFn = moduleMap[moduleName]
    if (importFn && !this.loadedModules.has(moduleName)) {
      try {
        // Use link preload for better browser optimization
        const link = document.createElement('link')
        link.rel = 'modulepreload'
        link.href = this.getModulePath(moduleName)
        document.head.appendChild(link)

        // Actually load the module
        const module = await importFn()
        this.loadedModules.set(moduleName, module)
      } catch (error) {
        console.warn(`Failed to preload module ${moduleName}:`, error)
      }
    }
  }

  /**
   * Get module path for preloading
   */
  private getModulePath(moduleName: string): string {
    // This would be generated during build time
    const paths: Record<string, string> = {
      'voice-engine': '/_next/static/chunks/voice-engine.js',
      'audio-processor': '/_next/static/chunks/audio-processor.js',
      'websocket-client': '/_next/static/chunks/websocket-client.js',
    }
    return paths[moduleName] || ''
  }

  /**
   * Dynamically import module with caching
   */
  async import<T = any>(moduleName: string): Promise<T> {
    // Return cached module if available
    if (this.loadedModules.has(moduleName)) {
      return this.loadedModules.get(moduleName)
    }

    // Return existing loading promise if in progress
    if (this.loadingPromises.has(moduleName)) {
      return this.loadingPromises.get(moduleName)
    }

    const moduleMap: Record<string, () => Promise<any>> = {
      'voice-engine': () => import('@/lib/voice-ai/engine/voice-engine'),
      'audio-processor': () => import('@/lib/voice-ai/utils/audio'),
      'websocket-client': () => import('@/lib/performance/websocket-optimizer'),
      'conversation-manager': () => import('@/lib/voice-ai/conversation/conversation-manager'),
      'lead-qualification': () => import('@/lib/voice-ai/qualification/lead-qualifier'),
      'analytics-dashboard': () => import('@/components/enterprise/analytics-dashboard'),
      'voice-control-center': () => import('@/components/enterprise/voice-agent-control-center'),
    }

    const importFn = moduleMap[moduleName]
    if (!importFn) {
      throw new Error(`Module ${moduleName} not found`)
    }

    // Create loading promise
    const loadingPromise = importFn()
      .then(module => {
        this.loadedModules.set(moduleName, module)
        this.loadingPromises.delete(moduleName)
        return module
      })
      .catch(error => {
        this.loadingPromises.delete(moduleName)
        throw error
      })

    this.loadingPromises.set(moduleName, loadingPromise)
    return loadingPromise
  }

  /**
   * Lazy load component with loading state
   */
  createLazyComponent<T = any>(
    moduleName: string, 
    componentName: string = 'default'
  ): React.ComponentType<T> {
    const LazyComponent = React.lazy(async () => {
      const module = await this.import(moduleName)
      return {
        default: module[componentName] || module.default || module
      }
    })

    // Return component with error boundary
    return (props: T) => (
      <React.Suspense 
        fallback={
          <div className="flex items-center justify-center p-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        }
      >
        <LazyComponent {...props} />
      </React.Suspense>
    )
  }

  /**
   * Prefetch modules based on user interaction
   */
  prefetchOnHover(moduleName: string): () => void {
    let timeoutId: NodeJS.Timeout

    return () => {
      // Debounce prefetch requests
      clearTimeout(timeoutId)
      timeoutId = setTimeout(() => {
        if (!this.loadedModules.has(moduleName) && !this.loadingPromises.has(moduleName)) {
          this.import(moduleName).catch(() => {
            // Silently handle prefetch failures
          })
        }
      }, 100) // 100ms debounce
    }
  }

  /**
   * Smart prefetch based on navigation patterns
   */
  smartPrefetch(currentRoute: string): void {
    const prefetchMap: Record<string, string[]> = {
      '/': ['voice-control-center', 'analytics-dashboard'],
      '/dashboard': ['conversation-manager', 'lead-qualification'],
      '/agents': ['voice-engine', 'audio-processor'],
      '/analytics': ['analytics-dashboard', 'conversation-manager'],
    }

    const modules = prefetchMap[currentRoute] || []
    modules.forEach(module => {
      // Prefetch with low priority
      setTimeout(() => {
        this.import(module).catch(() => {})
      }, 1000)
    })
  }

  /**
   * Bundle analysis and recommendations
   */
  async analyzeBundles(): Promise<{
    totalSize: number
    moduleCount: number
    recommendations: string[]
  }> {
    const recommendations: string[] = []
    
    // Analyze loaded modules
    const moduleCount = this.loadedModules.size
    const totalSize = await this.estimateBundleSize()

    if (totalSize > 2 * 1024 * 1024) { // 2MB
      recommendations.push('Consider splitting large modules further')
    }

    if (moduleCount > 50) {
      recommendations.push('Too many small modules - consider bundling related functionality')
    }

    if (this.loadingPromises.size > 10) {
      recommendations.push('Many concurrent imports - consider preloading critical modules')
    }

    return {
      totalSize,
      moduleCount,
      recommendations
    }
  }

  /**
   * Estimate bundle size (simplified)
   */
  private async estimateBundleSize(): Promise<number> {
    // This would integrate with webpack-bundle-analyzer in real implementation
    const moduleEstimates: Record<string, number> = {
      'voice-engine': 150 * 1024, // 150KB
      'audio-processor': 80 * 1024, // 80KB
      'websocket-client': 25 * 1024, // 25KB
      'conversation-manager': 60 * 1024, // 60KB
      'lead-qualification': 40 * 1024, // 40KB
      'analytics-dashboard': 120 * 1024, // 120KB
      'voice-control-center': 90 * 1024, // 90KB
    }

    let totalSize = 0
    this.loadedModules.forEach((_, moduleName) => {
      totalSize += moduleEstimates[moduleName] || 30 * 1024 // Default 30KB
    })

    return totalSize
  }

  /**
   * Register service worker for advanced caching
   */
  async registerServiceWorker(): Promise<void> {
    if (!this.config.enableServiceWorker || typeof window === 'undefined' || !navigator.serviceWorker) {
      return
    }

    try {
      const registration = await navigator.serviceWorker.register('/sw.js')
      
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New service worker available
              console.log('New version available - consider updating')
            }
          })
        }
      })

      console.log('Service Worker registered successfully')
    } catch (error) {
      console.warn('Service Worker registration failed:', error)
    }
  }

  /**
   * Clear module cache
   */
  clearCache(): void {
    this.loadedModules.clear()
    this.loadingPromises.clear()
  }

  /**
   * Get loading statistics
   */
  getStats(): {
    loadedModules: number
    loadingModules: number
    cacheHitRate: number
  } {
    const totalRequests = this.loadedModules.size + this.loadingPromises.size
    const cacheHitRate = totalRequests > 0 ? this.loadedModules.size / totalRequests : 0

    return {
      loadedModules: this.loadedModules.size,
      loadingModules: this.loadingPromises.size,
      cacheHitRate: Math.round(cacheHitRate * 100) / 100
    }
  }
}

// Singleton instance
export const bundleOptimizer = new BundleOptimizer()

// React integration
export function useDynamicImport<T = any>(moduleName: string) {
  const [module, setModule] = React.useState<T | null>(null)
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<Error | null>(null)

  React.useEffect(() => {
    let cancelled = false

    const loadModule = async () => {
      try {
        setLoading(true)
        setError(null)
        
        const imported = await bundleOptimizer.import<T>(moduleName)
        
        if (!cancelled) {
          setModule(imported)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error('Import failed'))
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadModule()

    return () => {
      cancelled = true
    }
  }, [moduleName])

  return { module, loading, error }
}

export { BundleOptimizer, type BundleConfig }