/**
 * Performance Monitor for Seiketsu AI
 * Comprehensive performance tracking and optimization
 */

interface PerformanceConfig {
  enableRUM: boolean // Real User Monitoring
  enableWebVitals: boolean
  sampleRate: number
  reportingEndpoint?: string
  thresholds: {
    lcp: number // Largest Contentful Paint
    fid: number // First Input Delay
    cls: number // Cumulative Layout Shift
    voiceLatency: number
    memoryUsage: number
  }
}

interface PerformanceEntry {
  metric: string
  value: number
  timestamp: number
  page: string
  sessionId: string
  userId?: string
  metadata?: Record<string, any>
}

interface WebVitalsMetrics {
  lcp: number
  fid: number
  cls: number
  fcp: number // First Contentful Paint
  ttfb: number // Time to First Byte
}

interface VoiceMetrics {
  speechToTextLatency: number
  textToSpeechLatency: number
  processingLatency: number
  totalLatency: number
  audioQuality: number
  errorRate: number
}

interface SystemMetrics {
  memoryUsage: number
  cpuUsage: number
  networkLatency: number
  batteryLevel?: number
  connectionType: string
}

class PerformanceMonitor {
  private config: PerformanceConfig
  private sessionId: string
  private entries: PerformanceEntry[] = []
  private webVitals: Partial<WebVitalsMetrics> = {}
  private voiceMetrics: Partial<VoiceMetrics> = {}
  private systemMetrics: Partial<SystemMetrics> = {}
  private observers: Map<string, any> = new Map()
  private reportingTimer: NodeJS.Timeout | null = null

  constructor(config: Partial<PerformanceConfig> = {}) {
    this.config = {
      enableRUM: true,
      enableWebVitals: true,
      sampleRate: 1.0, // 100% sampling
      thresholds: {
        lcp: 2500, // 2.5s
        fid: 100, // 100ms
        cls: 0.1,
        voiceLatency: 180, // 180ms
        memoryUsage: 50, // 50MB
      },
      ...config,
    }

    this.sessionId = this.generateSessionId()

    if (typeof window !== 'undefined') {
      this.initializeMonitoring()
    }
  }

  /**
   * Initialize performance monitoring
   */
  private async initializeMonitoring(): Promise<void> {
    try {
      if (this.config.enableWebVitals) {
        await this.initializeWebVitals()
      }

      if (this.config.enableRUM) {
        this.initializeRUM()
      }

      this.startSystemMonitoring()
      this.startReporting()

      console.log('Performance monitoring initialized')
    } catch (error) {
      console.warn('Failed to initialize performance monitoring:', error)
    }
  }

  /**
   * Initialize Web Vitals monitoring
   */
  private async initializeWebVitals(): Promise<void> {
    try {
      // Dynamic import to avoid bundle bloat
      const { getCLS, getFID, getFCP, getLCP, getTTFB } = await import('web-vitals')

      getCLS((metric) => {
        this.webVitals.cls = metric.value
        this.recordMetric('web-vitals.cls', metric.value, {
          rating: this.getRating('cls', metric.value)
        })
      })

      getFID((metric) => {
        this.webVitals.fid = metric.value
        this.recordMetric('web-vitals.fid', metric.value, {
          rating: this.getRating('fid', metric.value)
        })
      })

      getFCP((metric) => {
        this.webVitals.fcp = metric.value
        this.recordMetric('web-vitals.fcp', metric.value)
      })

      getLCP((metric) => {
        this.webVitals.lcp = metric.value
        this.recordMetric('web-vitals.lcp', metric.value, {
          rating: this.getRating('lcp', metric.value)
        })
      })

      getTTFB((metric) => {
        this.webVitals.ttfb = metric.value
        this.recordMetric('web-vitals.ttfb', metric.value)
      })

    } catch (error) {
      console.warn('Web Vitals not available:', error)
    }
  }

  /**
   * Initialize Real User Monitoring
   */
  private initializeRUM(): void {
    // Navigation timing
    this.measureNavigationTiming()

    // Resource timing
    this.measureResourceTiming()

    // Long tasks (blocking main thread)
    this.observeLongTasks()

    // Layout shifts
    this.observeLayoutShifts()

    // Memory usage
    this.observeMemoryUsage()
  }

  /**
   * Measure navigation timing
   */
  private measureNavigationTiming(): void {
    if (!window.performance?.getEntriesByType) return

    const navigation = window.performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
    if (!navigation) return

    this.recordMetric('navigation.domContentLoaded', navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart)
    this.recordMetric('navigation.loadComplete', navigation.loadEventEnd - navigation.loadEventStart)
    this.recordMetric('navigation.domInteractive', navigation.domInteractive - navigation.navigationStart)
    this.recordMetric('navigation.redirect', navigation.redirectEnd - navigation.redirectStart)
    this.recordMetric('navigation.dns', navigation.domainLookupEnd - navigation.domainLookupStart)
    this.recordMetric('navigation.connect', navigation.connectEnd - navigation.connectStart)
    this.recordMetric('navigation.request', navigation.responseStart - navigation.requestStart)
    this.recordMetric('navigation.response', navigation.responseEnd - navigation.responseStart)
  }

  /**
   * Measure resource timing
   */
  private measureResourceTiming(): void {
    if (!window.performance?.getEntriesByType) return

    const resources = window.performance.getEntriesByType('resource') as PerformanceResourceTiming[]
    
    resources.forEach(resource => {
      const duration = resource.responseEnd - resource.startTime
      
      if (resource.name.includes('.js')) {
        this.recordMetric('resource.javascript', duration, { url: resource.name })
      } else if (resource.name.includes('.css')) {
        this.recordMetric('resource.css', duration, { url: resource.name })
      } else if (resource.name.match(/\.(jpg|jpeg|png|gif|webp|svg)$/)) {
        this.recordMetric('resource.image', duration, { url: resource.name })
      }
    })
  }

  /**
   * Observe long tasks that block main thread
   */
  private observeLongTasks(): void {
    try {
      const observer = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          this.recordMetric('longtask.duration', entry.duration, {
            startTime: entry.startTime,
            attribution: (entry as any).attribution
          })
        })
      })

      observer.observe({ entryTypes: ['longtask'] })
      this.observers.set('longtask', observer)
    } catch (error) {
      console.warn('Long task observer not supported:', error)
    }
  }

  /**
   * Observe layout shifts
   */
  private observeLayoutShifts(): void {
    try {
      const observer = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          const layoutShift = entry as any
          this.recordMetric('layout-shift.value', layoutShift.value, {
            hadRecentInput: layoutShift.hadRecentInput,
            sources: layoutShift.sources?.map((source: any) => ({
              node: source.node?.tagName,
              previousRect: source.previousRect,
              currentRect: source.currentRect
            }))
          })
        })
      })

      observer.observe({ entryTypes: ['layout-shift'] })
      this.observers.set('layout-shift', observer)
    } catch (error) {
      console.warn('Layout shift observer not supported:', error)
    }
  }

  /**
   * Observe memory usage
   */
  private observeMemoryUsage(): void {
    const measureMemory = () => {
      if ((performance as any).memory) {
        const memory = (performance as any).memory
        const used = memory.usedJSHeapSize / (1024 * 1024) // MB
        const total = memory.totalJSHeapSize / (1024 * 1024) // MB
        const limit = memory.jsHeapSizeLimit / (1024 * 1024) // MB

        this.systemMetrics.memoryUsage = used
        this.recordMetric('memory.used', used)
        this.recordMetric('memory.total', total)
        this.recordMetric('memory.limit', limit)

        // Alert if memory usage is high
        if (used > this.config.thresholds.memoryUsage) {
          this.recordMetric('memory.alert', used, {
            severity: 'warning',
            threshold: this.config.thresholds.memoryUsage
          })
        }
      }
    }

    // Measure every 10 seconds
    setInterval(measureMemory, 10000)
    measureMemory() // Initial measurement
  }

  /**
   * Start system monitoring
   */
  private startSystemMonitoring(): void {
    // Network information
    if ('connection' in navigator) {
      const connection = (navigator as any).connection
      this.systemMetrics.connectionType = connection.effectiveType || 'unknown'
      this.recordMetric('system.connection', 0, {
        effectiveType: connection.effectiveType,
        downlink: connection.downlink,
        rtt: connection.rtt
      })
    }

    // Battery information
    if ('getBattery' in navigator) {
      (navigator as any).getBattery().then((battery: any) => {
        this.systemMetrics.batteryLevel = battery.level * 100
        this.recordMetric('system.battery', battery.level * 100, {
          charging: battery.charging,
          chargingTime: battery.chargingTime,
          dischargingTime: battery.dischargingTime
        })
      })
    }
  }

  /**
   * Record voice-specific metrics
   */
  recordVoiceMetrics(metrics: Partial<VoiceMetrics>): void {
    this.voiceMetrics = { ...this.voiceMetrics, ...metrics }

    Object.entries(metrics).forEach(([key, value]) => {
      this.recordMetric(`voice.${key}`, value)

      // Check against thresholds
      if (key === 'totalLatency' && value > this.config.thresholds.voiceLatency) {
        this.recordMetric('voice.latency.alert', value, {
          severity: 'warning',
          threshold: this.config.thresholds.voiceLatency
        })
      }
    })
  }

  /**
   * Record custom metric
   */
  recordMetric(metric: string, value: number, metadata?: Record<string, any>): void {
    if (Math.random() > this.config.sampleRate) {
      return // Skip based on sample rate
    }

    const entry: PerformanceEntry = {
      metric,
      value,
      timestamp: Date.now(),
      page: window.location.pathname,
      sessionId: this.sessionId,
      metadata
    }

    this.entries.push(entry)

    // Limit entries to prevent memory issues
    if (this.entries.length > 1000) {
      this.entries = this.entries.slice(-500) // Keep latest 500
    }
  }

  /**
   * Start periodic reporting
   */
  private startReporting(): void {
    if (!this.config.reportingEndpoint) return

    this.reportingTimer = setInterval(() => {
      this.sendReport()
    }, 30000) // Report every 30 seconds
  }

  /**
   * Send performance report
   */
  private async sendReport(): Promise<void> {
    if (!this.config.reportingEndpoint || this.entries.length === 0) {
      return
    }

    const report = {
      sessionId: this.sessionId,
      timestamp: Date.now(),
      page: window.location.pathname,
      userAgent: navigator.userAgent,
      webVitals: this.webVitals,
      voiceMetrics: this.voiceMetrics,
      systemMetrics: this.systemMetrics,
      entries: this.entries.splice(0) // Send and clear entries
    }

    try {
      await fetch(this.config.reportingEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(report),
      })
    } catch (error) {
      console.warn('Failed to send performance report:', error)
      // Add entries back if sending failed
      this.entries.unshift(...report.entries)
    }
  }

  /**
   * Get Web Vitals rating
   */
  private getRating(metric: string, value: number): 'good' | 'needs-improvement' | 'poor' {
    const thresholds = {
      lcp: [2500, 4000],
      fid: [100, 300],
      cls: [0.1, 0.25],
    }

    const [good, poor] = thresholds[metric as keyof typeof thresholds] || [0, 0]
    
    if (value <= good) return 'good'
    if (value <= poor) return 'needs-improvement'
    return 'poor'
  }

  /**
   * Generate unique session ID
   */
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * Get current performance summary
   */
  getPerformanceSummary(): {
    webVitals: WebVitalsMetrics
    voiceMetrics: VoiceMetrics
    systemMetrics: SystemMetrics
    score: number
    recommendations: string[]
  } {
    const recommendations: string[] = []
    let score = 100

    // Web Vitals scoring
    if (this.webVitals.lcp && this.webVitals.lcp > this.config.thresholds.lcp) {
      score -= 15
      recommendations.push('Optimize Largest Contentful Paint - consider image optimization and lazy loading')
    }

    if (this.webVitals.fid && this.webVitals.fid > this.config.thresholds.fid) {
      score -= 10
      recommendations.push('Reduce First Input Delay - minimize JavaScript execution time')
    }

    if (this.webVitals.cls && this.webVitals.cls > this.config.thresholds.cls) {
      score -= 10
      recommendations.push('Minimize Cumulative Layout Shift - reserve space for dynamic content')
    }

    // Voice metrics scoring
    if (this.voiceMetrics.totalLatency && this.voiceMetrics.totalLatency > this.config.thresholds.voiceLatency) {
      score -= 20
      recommendations.push('Optimize voice response time - consider audio compression and processing optimization')
    }

    // Memory usage scoring
    if (this.systemMetrics.memoryUsage && this.systemMetrics.memoryUsage > this.config.thresholds.memoryUsage) {
      score -= 15
      recommendations.push('Reduce memory usage - implement cleanup and caching strategies')
    }

    return {
      webVitals: this.webVitals as WebVitalsMetrics,
      voiceMetrics: this.voiceMetrics as VoiceMetrics,
      systemMetrics: this.systemMetrics as SystemMetrics,
      score: Math.max(0, score),
      recommendations
    }
  }

  /**
   * Export performance data
   */
  exportData(): {
    entries: PerformanceEntry[]
    summary: ReturnType<typeof this.getPerformanceSummary>
  } {
    return {
      entries: [...this.entries],
      summary: this.getPerformanceSummary()
    }
  }

  /**
   * Cleanup and dispose
   */
  dispose(): void {
    this.observers.forEach(observer => {
      try {
        observer.disconnect()
      } catch (error) {
        console.warn('Error disconnecting observer:', error)
      }
    })
    this.observers.clear()

    if (this.reportingTimer) {
      clearInterval(this.reportingTimer)
      this.reportingTimer = null
    }

    // Send final report
    if (this.entries.length > 0) {
      this.sendReport()
    }
  }
}

// Singleton instance
export const performanceMonitor = new PerformanceMonitor()

// React hook for performance monitoring
export function usePerformanceMonitor() {
  const [metrics, setMetrics] = React.useState(performanceMonitor.getPerformanceSummary())

  React.useEffect(() => {
    const updateMetrics = () => {
      setMetrics(performanceMonitor.getPerformanceSummary())
    }

    const interval = setInterval(updateMetrics, 5000) // Update every 5 seconds

    return () => clearInterval(interval)
  }, [])

  return {
    metrics,
    recordMetric: performanceMonitor.recordMetric.bind(performanceMonitor),
    recordVoiceMetrics: performanceMonitor.recordVoiceMetrics.bind(performanceMonitor),
    exportData: performanceMonitor.exportData.bind(performanceMonitor)
  }
}

export { PerformanceMonitor, type PerformanceConfig, type WebVitalsMetrics, type VoiceMetrics }