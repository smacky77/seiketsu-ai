/**
 * WebSocket Optimizer for Seiketsu AI Voice Engine
 * Optimizes real-time communication for <100ms message latency
 */

interface WebSocketConfig {
  url: string
  maxReconnectAttempts: number
  reconnectDelay: number
  heartbeatInterval: number
  messageTimeout: number
  binaryProtocol: boolean
  compressionEnabled: boolean
}

interface ConnectionMetrics {
  latency: number
  messagesSent: number
  messagesReceived: number
  reconnectCount: number
  errorCount: number
  bytesTransferred: number
  connectionUptime: number
}

interface QueuedMessage {
  id: string
  data: any
  timestamp: number
  priority: 'high' | 'normal' | 'low'
  retryCount: number
}

class WebSocketOptimizer {
  private config: WebSocketConfig
  private ws: WebSocket | null = null
  private connectionState: 'disconnected' | 'connecting' | 'connected' | 'error' = 'disconnected'
  private messageQueue: QueuedMessage[] = []
  private pendingMessages: Map<string, { resolve: Function; reject: Function; timestamp: number }> = new Map()
  private heartbeatTimer: NodeJS.Timeout | null = null
  private reconnectTimer: NodeJS.Timeout | null = null
  private metrics: ConnectionMetrics = {
    latency: 0,
    messagesSent: 0,
    messagesReceived: 0,
    reconnectCount: 0,
    errorCount: 0,
    bytesTransferred: 0,
    connectionUptime: 0,
  }
  private connectionStartTime: number = 0
  private eventListeners: Map<string, Function[]> = new Map()

  constructor(config: Partial<WebSocketConfig> = {}) {
    this.config = {
      url: '',
      maxReconnectAttempts: 5,
      reconnectDelay: 1000,
      heartbeatInterval: 30000, // 30 seconds
      messageTimeout: 10000, // 10 seconds
      binaryProtocol: true,
      compressionEnabled: true,
      ...config,
    }
  }

  /**
   * Connect to WebSocket with optimization
   */
  async connect(url?: string): Promise<void> {
    if (this.connectionState === 'connected') {
      return
    }

    const connectUrl = url || this.config.url
    if (!connectUrl) {
      throw new Error('WebSocket URL is required')
    }

    this.connectionState = 'connecting'
    this.connectionStartTime = Date.now()

    return new Promise((resolve, reject) => {
      try {
        // Create WebSocket with optimized protocols
        const protocols = []
        if (this.config.binaryProtocol) {
          protocols.push('binary')
        }
        if (this.config.compressionEnabled) {
          protocols.push('permessage-deflate')
        }

        this.ws = new WebSocket(connectUrl, protocols)
        
        // Optimize buffer sizes
        if (this.ws.binaryType !== undefined) {
          this.ws.binaryType = 'arraybuffer'
        }

        this.ws.onopen = () => {
          this.connectionState = 'connected'
          this.metrics.connectionUptime = Date.now()
          this.startHeartbeat()
          this.processQueuedMessages()
          this.emit('connected')
          resolve()
        }

        this.ws.onmessage = (event) => {
          this.handleMessage(event)
        }

        this.ws.onclose = (event) => {
          this.handleDisconnection(event)
        }

        this.ws.onerror = (error) => {
          this.metrics.errorCount++
          this.connectionState = 'error'
          this.emit('error', error)
          reject(error)
        }

        // Connection timeout
        setTimeout(() => {
          if (this.connectionState === 'connecting') {
            this.ws?.close()
            reject(new Error('Connection timeout'))
          }
        }, 10000) // 10 second timeout

      } catch (error) {
        this.connectionState = 'error'
        reject(error)
      }
    })
  }

  /**
   * Send message with optimization and reliability
   */
  async sendMessage(data: any, priority: 'high' | 'normal' | 'low' = 'normal'): Promise<any> {
    const messageId = this.generateMessageId()
    const message: QueuedMessage = {
      id: messageId,
      data,
      timestamp: Date.now(),
      priority,
      retryCount: 0,
    }

    if (this.connectionState !== 'connected') {
      // Queue message for later
      this.queueMessage(message)
      throw new Error('WebSocket not connected - message queued')
    }

    return this.sendMessageInternal(message)
  }

  /**
   * Send audio data with optimized binary protocol
   */
  async sendAudioData(audioBuffer: Float32Array): Promise<void> {
    if (this.connectionState !== 'connected') {
      throw new Error('WebSocket not connected')
    }

    const startTime = performance.now()

    // Optimize audio data for transmission
    const optimizedData = this.optimizeAudioForTransmission(audioBuffer)
    
    // Send as binary data for efficiency
    const message = {
      type: 'audio',
      timestamp: Date.now(),
      data: optimizedData,
    }

    const binaryData = this.serializeBinaryMessage(message)
    
    try {
      this.ws!.send(binaryData)
      this.metrics.messagesSent++
      this.metrics.bytesTransferred += binaryData.byteLength
      
      // Record latency for audio messages
      const latency = performance.now() - startTime
      this.updateLatencyMetric(latency)
      
    } catch (error) {
      this.metrics.errorCount++
      throw error
    }
  }

  /**
   * Optimize audio data for WebSocket transmission
   */
  private optimizeAudioForTransmission(audioBuffer: Float32Array): ArrayBuffer {
    // Convert Float32 to Int16 for smaller payload (50% size reduction)
    const int16Buffer = new Int16Array(audioBuffer.length)
    
    for (let i = 0; i < audioBuffer.length; i++) {
      // Convert float (-1 to 1) to int16 (-32768 to 32767)
      int16Buffer[i] = Math.max(-32768, Math.min(32767, audioBuffer[i] * 32767))
    }

    return int16Buffer.buffer
  }

  /**
   * Serialize message to binary format
   */
  private serializeBinaryMessage(message: any): ArrayBuffer {
    const jsonString = JSON.stringify(message)
    const encoder = new TextEncoder()
    return encoder.encode(jsonString).buffer
  }

  /**
   * Internal message sending with retry logic
   */
  private async sendMessageInternal(message: QueuedMessage): Promise<any> {
    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        this.pendingMessages.delete(message.id)
        reject(new Error('Message timeout'))
      }, this.config.messageTimeout)

      this.pendingMessages.set(message.id, {
        resolve: (response: any) => {
          clearTimeout(timeoutId)
          resolve(response)
        },
        reject: (error: any) => {
          clearTimeout(timeoutId)
          reject(error)
        },
        timestamp: Date.now(),
      })

      try {
        const payload = {
          id: message.id,
          ...message.data,
          timestamp: message.timestamp,
        }

        const data = this.config.binaryProtocol
          ? this.serializeBinaryMessage(payload)
          : JSON.stringify(payload)

        this.ws!.send(data)
        this.metrics.messagesSent++
        
        if (data instanceof ArrayBuffer) {
          this.metrics.bytesTransferred += data.byteLength
        } else {
          this.metrics.bytesTransferred += new Blob([data]).size
        }

      } catch (error) {
        clearTimeout(timeoutId)
        this.pendingMessages.delete(message.id)
        this.metrics.errorCount++
        reject(error)
      }
    })
  }

  /**
   * Handle incoming messages with latency tracking
   */
  private handleMessage(event: MessageEvent): void {
    const receiveTime = Date.now()
    this.metrics.messagesReceived++

    try {
      let data: any

      if (event.data instanceof ArrayBuffer) {
        // Binary message
        const decoder = new TextDecoder()
        const jsonString = decoder.decode(event.data)
        data = JSON.parse(jsonString)
        this.metrics.bytesTransferred += event.data.byteLength
      } else {
        // Text message
        data = JSON.parse(event.data)
        this.metrics.bytesTransferred += new Blob([event.data]).size
      }

      // Calculate round-trip latency
      if (data.timestamp) {
        const latency = receiveTime - data.timestamp
        this.updateLatencyMetric(latency)
      }

      // Handle response to pending message
      if (data.id && this.pendingMessages.has(data.id)) {
        const pending = this.pendingMessages.get(data.id)!
        this.pendingMessages.delete(data.id)
        pending.resolve(data)
        return
      }

      // Handle different message types
      switch (data.type) {
        case 'pong':
          // Heartbeat response - already handled latency
          break
        
        case 'audio':
          this.emit('audio', this.parseAudioMessage(data))
          break
        
        case 'transcription':
          this.emit('transcription', data)
          break
        
        case 'error':
          this.emit('error', new Error(data.message))
          break
        
        default:
          this.emit('message', data)
      }

    } catch (error) {
      this.metrics.errorCount++
      this.emit('error', error)
    }
  }

  /**
   * Parse incoming audio message
   */
  private parseAudioMessage(data: any): Float32Array {
    if (data.data instanceof ArrayBuffer) {
      // Convert Int16 back to Float32
      const int16Array = new Int16Array(data.data)
      const float32Array = new Float32Array(int16Array.length)
      
      for (let i = 0; i < int16Array.length; i++) {
        float32Array[i] = int16Array[i] / 32767
      }
      
      return float32Array
    }
    
    return new Float32Array(data.data)
  }

  /**
   * Update latency metrics with smoothing
   */
  private updateLatencyMetric(newLatency: number): void {
    // Exponential moving average for smooth latency tracking
    const alpha = 0.3
    this.metrics.latency = this.metrics.latency === 0
      ? newLatency
      : alpha * newLatency + (1 - alpha) * this.metrics.latency
  }

  /**
   * Queue message when not connected
   */
  private queueMessage(message: QueuedMessage): void {
    // Insert based on priority
    let insertIndex = this.messageQueue.length
    
    for (let i = 0; i < this.messageQueue.length; i++) {
      const queuedMessage = this.messageQueue[i]
      
      if (this.getPriorityValue(message.priority) > this.getPriorityValue(queuedMessage.priority)) {
        insertIndex = i
        break
      }
    }
    
    this.messageQueue.splice(insertIndex, 0, message)
    
    // Limit queue size
    if (this.messageQueue.length > 100) {
      this.messageQueue = this.messageQueue.slice(0, 100)
    }
  }

  /**
   * Get numeric priority value for sorting
   */
  private getPriorityValue(priority: string): number {
    switch (priority) {
      case 'high': return 3
      case 'normal': return 2
      case 'low': return 1
      default: return 0
    }
  }

  /**
   * Process queued messages after connection
   */
  private async processQueuedMessages(): Promise<void> {
    const queue = [...this.messageQueue]
    this.messageQueue = []

    for (const message of queue) {
      try {
        await this.sendMessageInternal(message)
      } catch (error) {
        console.warn('Failed to send queued message:', error)
        
        // Retry high priority messages
        if (message.priority === 'high' && message.retryCount < 3) {
          message.retryCount++
          this.queueMessage(message)
        }
      }
    }
  }

  /**
   * Start heartbeat to maintain connection
   */
  private startHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
    }

    this.heartbeatTimer = setInterval(() => {
      if (this.connectionState === 'connected') {
        const pingMessage = {
          type: 'ping',
          timestamp: Date.now(),
        }
        
        try {
          this.ws!.send(JSON.stringify(pingMessage))
        } catch (error) {
          console.warn('Heartbeat failed:', error)
        }
      }
    }, this.config.heartbeatInterval)
  }

  /**
   * Handle connection loss and reconnection
   */
  private handleDisconnection(event: CloseEvent): void {
    this.connectionState = 'disconnected'
    this.stopHeartbeat()
    
    // Clear pending messages
    this.pendingMessages.forEach(({ reject }) => {
      reject(new Error('Connection lost'))
    })
    this.pendingMessages.clear()

    this.emit('disconnected', event)

    // Auto-reconnect if not a clean close
    if (event.code !== 1000 && this.metrics.reconnectCount < this.config.maxReconnectAttempts) {
      this.scheduleReconnect()
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }

    const delay = this.config.reconnectDelay * Math.pow(2, this.metrics.reconnectCount)

    this.reconnectTimer = setTimeout(async () => {
      try {
        this.metrics.reconnectCount++
        await this.connect()
        console.log(`WebSocket reconnected after ${this.metrics.reconnectCount} attempts`)
      } catch (error) {
        console.warn('Reconnection failed:', error)
        
        if (this.metrics.reconnectCount < this.config.maxReconnectAttempts) {
          this.scheduleReconnect()
        } else {
          this.emit('maxReconnectAttemptsReached')
        }
      }
    }, delay)
  }

  /**
   * Stop heartbeat timer
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * Generate unique message ID
   */
  private generateMessageId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * Event emitter functionality
   */
  on(event: string, callback: Function): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, [])
    }
    this.eventListeners.get(event)!.push(callback)
  }

  private emit(event: string, ...args: any[]): void {
    const listeners = this.eventListeners.get(event)
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(...args)
        } catch (error) {
          console.error('Event listener error:', error)
        }
      })
    }
  }

  /**
   * Get connection metrics
   */
  getMetrics(): ConnectionMetrics & { isOptimal: boolean } {
    if (this.connectionState === 'connected') {
      this.metrics.connectionUptime = Date.now() - this.metrics.connectionUptime
    }

    return {
      ...this.metrics,
      isOptimal: this.metrics.latency < 100 && // <100ms latency
                this.metrics.errorCount < 5 && // Low error count
                this.connectionState === 'connected'
    }
  }

  /**
   * Disconnect and cleanup
   */
  disconnect(): void {
    this.stopHeartbeat()
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.ws) {
      this.ws.close(1000, 'Client disconnecting')
      this.ws = null
    }

    this.connectionState = 'disconnected'
    this.messageQueue = []
    this.pendingMessages.clear()
    this.eventListeners.clear()
  }
}

export { WebSocketOptimizer, type WebSocketConfig, type ConnectionMetrics }