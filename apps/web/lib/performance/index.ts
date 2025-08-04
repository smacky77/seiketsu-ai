/**
 * Performance Optimization Suite for Seiketsu AI
 * Centralized exports for all performance optimization modules
 */

// Core optimizers
export { AudioOptimizer, type AudioOptimizationConfig, type PerformanceMetrics } from './audio-optimizer'
export { MemoryManager, type MemoryConfig, type MemoryMetrics } from './memory-manager'
export { WebSocketOptimizer, type WebSocketConfig, type ConnectionMetrics } from './websocket-optimizer'
export { BundleOptimizer, bundleOptimizer, useDynamicImport, type BundleConfig } from './bundle-optimizer'
export { 
  PerformanceMonitor, 
  performanceMonitor, 
  usePerformanceMonitor,
  type PerformanceConfig,
  type WebVitalsMetrics,
  type VoiceMetrics 
} from './performance-monitor'

// Performance suite class for unified management
class PerformanceSuite {
  private audioOptimizer: AudioOptimizer
  private memoryManager: MemoryManager
  private wsOptimizer: WebSocketOptimizer
  private monitor: PerformanceMonitor
  private isInitialized = false

  constructor() {
    this.audioOptimizer = new AudioOptimizer({
      maxLatency: 180,
      bufferSize: 512,
      enableWebWorker: true,
      enableOffloadComputation: true
    })

    this.memoryManager = new MemoryManager({
      maxSessionMemory: 50,
      maxConversationHistory: 100,
      enableAutoCleanup: true
    })

    this.wsOptimizer = new WebSocketOptimizer({
      binaryProtocol: true,
      compressionEnabled: true,
      maxReconnectAttempts: 5
    })

    this.monitor = new PerformanceMonitor({
      enableRUM: true,
      enableWebVitals: true,
      sampleRate: 1.0
    })
  }

  /**
   * Initialize all performance optimizers
   */
  async initialize(config?: {
    audioConfig?: Partial<AudioOptimizationConfig>
    memoryConfig?: Partial<MemoryConfig>
    wsConfig?: Partial<WebSocketConfig>
    monitorConfig?: Partial<PerformanceConfig>
  }): Promise<void> {
    if (this.isInitialized) return

    try {
      // Initialize audio optimizer
      await this.audioOptimizer.initialize()

      // Initialize WebSocket if URL provided
      if (config?.wsConfig?.url) {
        await this.wsOptimizer.connect(config.wsConfig.url)
      }

      // Register service worker for bundle optimization
      await bundleOptimizer.registerServiceWorker()

      this.isInitialized = true
      console.log('Seiketsu AI Performance Suite initialized successfully')
    } catch (error) {
      console.error('Failed to initialize Performance Suite:', error)
      throw error
    }
  }

  /**
   * Get unified performance metrics
   */
  getMetrics(): {
    audio: ReturnType<AudioOptimizer['getMetrics']>
    memory: ReturnType<MemoryManager['getMetrics']>
    websocket: ReturnType<WebSocketOptimizer['getMetrics']>
    overall: ReturnType<PerformanceMonitor['getPerformanceSummary']>
    bundleStats: ReturnType<typeof bundleOptimizer.getStats>
  } {
    return {
      audio: this.audioOptimizer.getMetrics(),
      memory: this.memoryManager.getMetrics(),
      websocket: this.wsOptimizer.getMetrics(),
      overall: this.monitor.getPerformanceSummary(),
      bundleStats: bundleOptimizer.getStats()
    }
  }

  /**
   * Force performance optimization
   */
  optimize(): void {
    // Optimize buffer sizes
    this.audioOptimizer.optimizeBufferSize()

    // Force memory cleanup
    this.memoryManager.forceCleanup()

    // Clear bundle cache if needed
    const stats = bundleOptimizer.getStats()
    if (stats.cacheHitRate < 0.7) {
      bundleOptimizer.clearCache()
    }
  }

  /**
   * Get performance recommendations
   */
  getRecommendations(): string[] {
    const recommendations: string[] = []
    const metrics = this.getMetrics()

    if (!metrics.audio.isOptimal) {
      recommendations.push('Audio processing is not optimal - consider reducing buffer size or enabling Web Workers')
    }

    if (!metrics.memory.isOptimal) {
      recommendations.push('Memory usage is high - enable automatic cleanup and reduce conversation history')
    }

    if (!metrics.websocket.isOptimal) {
      recommendations.push('WebSocket performance is degraded - check network connection and enable compression')
    }

    if (metrics.overall.score < 80) {
      recommendations.push('Overall performance score is low - review Web Vitals and voice metrics')
    }

    if (metrics.bundleStats.cacheHitRate < 0.8) {
      recommendations.push('Bundle cache hit rate is low - consider preloading critical modules')
    }

    return recommendations
  }

  /**
   * Export comprehensive performance report
   */
  exportReport(): {
    timestamp: number
    metrics: ReturnType<typeof this.getMetrics>
    recommendations: string[]
    isHealthy: boolean
  } {
    const metrics = this.getMetrics()
    const recommendations = this.getRecommendations()

    const isHealthy = (
      metrics.audio.isOptimal &&
      metrics.memory.isOptimal &&
      metrics.websocket.isOptimal &&
      metrics.overall.score > 75
    )

    return {
      timestamp: Date.now(),
      metrics,
      recommendations,
      isHealthy
    }
  }

  /**
   * Cleanup all optimizers
   */
  dispose(): void {
    this.audioOptimizer.dispose()
    this.memoryManager.dispose()
    this.wsOptimizer.disconnect()
    this.monitor.dispose()
    this.isInitialized = false
  }

  // Getters for individual optimizers
  get audio() { return this.audioOptimizer }
  get memory() { return this.memoryManager }
  get websocket() { return this.wsOptimizer }
  get monitor() { return this.monitor }
}

// Singleton instance
export const performanceSuite = new PerformanceSuite()

// React hook for unified performance management
export function usePerformanceSuite() {
  const [metrics, setMetrics] = React.useState(performanceSuite.getMetrics())
  const [isInitialized, setIsInitialized] = React.useState(false)

  React.useEffect(() => {
    const initializeSuite = async () => {
      try {
        await performanceSuite.initialize()
        setIsInitialized(true)
      } catch (error) {
        console.error('Failed to initialize performance suite:', error)
      }
    }

    initializeSuite()

    // Update metrics periodically
    const interval = setInterval(() => {
      setMetrics(performanceSuite.getMetrics())
    }, 5000)

    return () => {
      clearInterval(interval)
      performanceSuite.dispose()
    }
  }, [])

  return {
    metrics,
    isInitialized,
    optimize: performanceSuite.optimize.bind(performanceSuite),
    getRecommendations: performanceSuite.getRecommendations.bind(performanceSuite),
    exportReport: performanceSuite.exportReport.bind(performanceSuite)
  }
}

// Utility functions
export const performanceUtils = {
  /**
   * Measure function execution time
   */
  measureTime: <T>(fn: () => T, label?: string): T => {
    const start = performance.now()
    const result = fn()
    const duration = performance.now() - start
    
    if (label) {
      console.log(`${label}: ${duration.toFixed(2)}ms`)
    }
    
    performanceMonitor.recordMetric('function.execution', duration, { label })
    return result
  },

  /**
   * Measure async function execution time
   */
  measureTimeAsync: async <T>(fn: () => Promise<T>, label?: string): Promise<T> => {
    const start = performance.now()
    const result = await fn()
    const duration = performance.now() - start
    
    if (label) {
      console.log(`${label}: ${duration.toFixed(2)}ms`)
    }
    
    performanceMonitor.recordMetric('function.execution.async', duration, { label })
    return result
  },

  /**
   * Create performance-optimized debounced function
   */
  debounce: <T extends (...args: any[]) => any>(
    fn: T,
    delay: number
  ): (...args: Parameters<T>) => void => {
    let timeoutId: NodeJS.Timeout
    
    return (...args: Parameters<T>) => {
      clearTimeout(timeoutId)
      timeoutId = setTimeout(() => fn(...args), delay)
    }
  },

  /**
   * Create performance-optimized throttled function
   */
  throttle: <T extends (...args: any[]) => any>(
    fn: T,
    delay: number
  ): (...args: Parameters<T>) => void => {
    let lastCall = 0
    
    return (...args: Parameters<T>) => {
      const now = Date.now()
      if (now - lastCall >= delay) {
        lastCall = now
        fn(...args)
      }
    }
  }
}

export default performanceSuite