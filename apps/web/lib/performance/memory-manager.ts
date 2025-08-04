/**
 * Memory Manager for Seiketsu AI Voice Engine
 * Manages memory efficiently for <50MB per session target
 */

interface MemoryConfig {
  maxSessionMemory: number // MB
  maxConversationHistory: number
  maxAudioBuffer: number // seconds
  gcThreshold: number // MB
  enableAutoCleanup: boolean
}

interface MemoryMetrics {
  heapUsed: number
  heapTotal: number
  audioBufferSize: number
  conversationSize: number
  componentCount: number
  lastGC: number
}

class MemoryManager {
  private config: MemoryConfig
  private metrics: MemoryMetrics = {
    heapUsed: 0,
    heapTotal: 0,
    audioBufferSize: 0,
    conversationSize: 0,
    componentCount: 0,
    lastGC: 0,
  }
  private cleanupTimers: Map<string, NodeJS.Timeout> = new Map()
  private audioBuffers: Map<string, AudioBuffer> = new Map()
  private conversationData: Map<string, any> = new Map()
  private componentRefs: WeakSet<any> = new WeakSet()

  constructor(config: Partial<MemoryConfig> = {}) {
    this.config = {
      maxSessionMemory: 50, // 50MB per session
      maxConversationHistory: 100, // 100 turns
      maxAudioBuffer: 30, // 30 seconds
      gcThreshold: 40, // 40MB triggers cleanup
      enableAutoCleanup: true,
      ...config,
    }

    if (this.config.enableAutoCleanup) {
      this.startMemoryMonitoring()
    }
  }

  /**
   * Start continuous memory monitoring
   */
  private startMemoryMonitoring(): void {
    const monitorInterval = setInterval(() => {
      this.updateMetrics()
      
      if (this.shouldTriggerCleanup()) {
        this.performAutomaticCleanup()
      }
    }, 5000) // Check every 5 seconds

    // Clean up on page unload
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => {
        clearInterval(monitorInterval)
        this.performFullCleanup()
      })
    }
  }

  /**
   * Update current memory metrics
   */
  private updateMetrics(): void {
    if (typeof window !== 'undefined' && (performance as any).memory) {
      const memory = (performance as any).memory
      this.metrics.heapUsed = memory.usedJSHeapSize / (1024 * 1024) // MB
      this.metrics.heapTotal = memory.totalJSHeapSize / (1024 * 1024) // MB
    }

    // Calculate audio buffer size
    let totalAudioSize = 0
    this.audioBuffers.forEach((buffer) => {
      totalAudioSize += buffer.length * buffer.numberOfChannels * 4 // 4 bytes per float32
    })
    this.metrics.audioBufferSize = totalAudioSize / (1024 * 1024) // MB

    // Calculate conversation data size
    let totalConversationSize = 0
    this.conversationData.forEach((data) => {
      totalConversationSize += JSON.stringify(data).length * 2 // UTF-16 encoding
    })
    this.metrics.conversationSize = totalConversationSize / (1024 * 1024) // MB
  }

  /**
   * Check if cleanup should be triggered
   */
  private shouldTriggerCleanup(): boolean {
    return (
      this.metrics.heapUsed > this.config.gcThreshold ||
      this.metrics.audioBufferSize > 10 || // 10MB audio buffer limit
      this.audioBuffers.size > 50 || // Too many buffers
      this.conversationData.size > this.config.maxConversationHistory
    )
  }

  /**
   * Perform automatic memory cleanup
   */
  private performAutomaticCleanup(): void {
    console.log('Performing automatic memory cleanup...')
    
    // Clean old audio buffers
    this.cleanupOldAudioBuffers()
    
    // Clean old conversation data
    this.cleanupOldConversations()
    
    // Force garbage collection if available
    if (typeof window !== 'undefined' && (window as any).gc) {
      (window as any).gc()
    }
    
    this.metrics.lastGC = Date.now()
    this.updateMetrics()
    
    console.log(`Memory cleanup completed. Heap used: ${this.metrics.heapUsed.toFixed(2)}MB`)
  }

  /**
   * Register audio buffer with automatic cleanup
   */
  registerAudioBuffer(id: string, buffer: AudioBuffer, ttl: number = 60000): void {
    // Remove existing buffer if it exists
    if (this.audioBuffers.has(id)) {
      this.audioBuffers.delete(id)
    }

    this.audioBuffers.set(id, buffer)

    // Set cleanup timer
    const timer = setTimeout(() => {
      this.audioBuffers.delete(id)
      this.cleanupTimers.delete(id)
      console.log(`Audio buffer ${id} auto-cleaned after ${ttl}ms`)
    }, ttl)

    this.cleanupTimers.set(id, timer)
  }

  /**
   * Get audio buffer with access tracking
   */
  getAudioBuffer(id: string): AudioBuffer | null {
    return this.audioBuffers.get(id) || null
  }

  /**
   * Remove audio buffer immediately
   */
  removeAudioBuffer(id: string): void {
    this.audioBuffers.delete(id)
    
    const timer = this.cleanupTimers.get(id)
    if (timer) {
      clearTimeout(timer)
      this.cleanupTimers.delete(id)
    }
  }

  /**
   * Clean up old audio buffers
   */
  private cleanupOldAudioBuffers(): void {
    const maxAge = this.config.maxAudioBuffer * 1000 // Convert to ms
    const now = Date.now()
    
    // Simple LRU-style cleanup (remove oldest 50% when threshold hit)
    if (this.audioBuffers.size > 20) {
      const entries = Array.from(this.audioBuffers.entries())
      const toRemove = entries.slice(0, Math.floor(entries.length / 2))
      
      toRemove.forEach(([id]) => {
        this.removeAudioBuffer(id)
      })
    }
  }

  /**
   * Register conversation data with memory-efficient storage
   */
  registerConversation(id: string, data: any): void {
    // Compress conversation data
    const compressedData = this.compressConversationData(data)
    this.conversationData.set(id, compressedData)
    
    // Auto-cleanup old conversations
    if (this.conversationData.size > this.config.maxConversationHistory) {
      const oldest = this.conversationData.keys().next().value
      this.conversationData.delete(oldest)
    }
  }

  /**
   * Compress conversation data to save memory
   */
  private compressConversationData(data: any): any {
    // Remove redundant fields and compress text
    const compressed = {
      id: data.id,
      timestamp: data.timestamp,
      summary: this.summarizeConversation(data),
      keyPoints: data.keyPoints || [],
      score: data.qualificationScore,
      // Remove full transcript, keep only summary
    }

    return compressed
  }

  /**
   * Create memory-efficient conversation summary
   */
  private summarizeConversation(conversation: any): string {
    if (!conversation.turns || conversation.turns.length === 0) {
      return 'Empty conversation'
    }

    // Extract key phrases and intents
    const keyPhrases = conversation.turns
      .filter((turn: any) => turn.speaker === 'lead')
      .map((turn: any) => turn.text)
      .join(' ')
      .split(' ')
      .filter((word: string) => word.length > 4)
      .slice(0, 20) // Keep only top 20 words

    return keyPhrases.join(' ')
  }

  /**
   * Clean up old conversation data
   */
  private cleanupOldConversations(): void {
    const maxConversations = this.config.maxConversationHistory
    
    if (this.conversationData.size > maxConversations) {
      const entries = Array.from(this.conversationData.entries())
      const toRemove = entries.slice(0, this.conversationData.size - maxConversations)
      
      toRemove.forEach(([id]) => {
        this.conversationData.delete(id)
      })
    }
  }

  /**
   * Register React component for memory tracking
   */
  registerComponent(component: any): void {
    this.componentRefs.add(component)
    this.metrics.componentCount++
  }

  /**
   * Create memory-efficient audio processing function
   */
  createOptimizedAudioProcessor(): (audioData: Float32Array) => Float32Array {
    // Pre-allocate buffers to avoid repeated allocation
    let processingBuffer: Float32Array | null = null
    let outputBuffer: Float32Array | null = null

    return (audioData: Float32Array): Float32Array => {
      // Reuse buffers if same size
      if (!processingBuffer || processingBuffer.length !== audioData.length) {
        processingBuffer = new Float32Array(audioData.length)
        outputBuffer = new Float32Array(audioData.length)
      }

      // Process in-place to minimize allocations
      processingBuffer.set(audioData)
      
      // Apply processing (example: simple gain)
      for (let i = 0; i < processingBuffer.length; i++) {
        outputBuffer![i] = processingBuffer[i] * 0.8
      }

      return outputBuffer!
    }
  }

  /**
   * Create memory-efficient event listener manager
   */
  createEventManager(): {
    addEventListener: (element: EventTarget, event: string, handler: EventListener) => void
    removeAllListeners: () => void
  } {
    const listeners: Array<{
      element: EventTarget
      event: string
      handler: EventListener
    }> = []

    return {
      addEventListener: (element: EventTarget, event: string, handler: EventListener) => {
        element.addEventListener(event, handler)
        listeners.push({ element, event, handler })
      },
      removeAllListeners: () => {
        listeners.forEach(({ element, event, handler }) => {
          element.removeEventListener(event, handler)
        })
        listeners.length = 0
      }
    }
  }

  /**
   * Get current memory metrics
   */
  getMetrics(): MemoryMetrics & { 
    isOptimal: boolean
    recommendations: string[]
  } {
    this.updateMetrics()
    
    const recommendations: string[] = []
    
    if (this.metrics.heapUsed > this.config.maxSessionMemory * 0.8) {
      recommendations.push('High memory usage detected - consider reducing conversation history')
    }
    
    if (this.metrics.audioBufferSize > 5) {
      recommendations.push('Large audio buffer detected - clean up old audio data')
    }
    
    if (this.audioBuffers.size > 30) {
      recommendations.push('Too many audio buffers - implement more aggressive cleanup')
    }

    return {
      ...this.metrics,
      isOptimal: this.metrics.heapUsed < this.config.maxSessionMemory * 0.7,
      recommendations
    }
  }

  /**
   * Force immediate cleanup
   */
  forceCleanup(): void {
    this.performAutomaticCleanup()
  }

  /**
   * Perform complete memory cleanup
   */
  performFullCleanup(): void {
    // Clear all timers
    this.cleanupTimers.forEach((timer) => clearTimeout(timer))
    this.cleanupTimers.clear()

    // Clear all data
    this.audioBuffers.clear()
    this.conversationData.clear()
    
    // Reset metrics
    this.metrics = {
      heapUsed: 0,
      heapTotal: 0,
      audioBufferSize: 0,
      conversationSize: 0,
      componentCount: 0,
      lastGC: Date.now(),
    }

    console.log('Full memory cleanup completed')
  }

  /**
   * Dispose of memory manager
   */
  dispose(): void {
    this.performFullCleanup()
  }
}

export { MemoryManager, type MemoryConfig, type MemoryMetrics }