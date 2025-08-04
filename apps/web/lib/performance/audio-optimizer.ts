/**
 * Audio Performance Optimizer for Seiketsu AI Voice Engine
 * Optimizes audio processing for <180ms response times
 */

interface AudioOptimizationConfig {
  maxLatency: number // Target max latency in ms
  bufferSize: number
  sampleRate: number
  compressionLevel: number
  enableWebWorker: boolean
  enableOffloadComputation: boolean
}

interface PerformanceMetrics {
  processingTime: number
  memoryUsage: number
  cpuUsage: number
  audioQuality: number
  bufferUnderruns: number
}

class AudioOptimizer {
  private config: AudioOptimizationConfig
  private audioContext: AudioContext | null = null
  private workletNode: AudioWorkletNode | null = null
  private worker: Worker | null = null
  private performanceMetrics: PerformanceMetrics = {
    processingTime: 0,
    memoryUsage: 0,
    cpuUsage: 0,
    audioQuality: 1.0,
    bufferUnderruns: 0,
  }

  constructor(config: Partial<AudioOptimizationConfig> = {}) {
    this.config = {
      maxLatency: 180, // 180ms target
      bufferSize: 512, // Small buffer for low latency
      sampleRate: 16000, // Optimized for speech
      compressionLevel: 0.7,
      enableWebWorker: true,
      enableOffloadComputation: true,
      ...config,
    }
  }

  async initialize(): Promise<void> {
    try {
      // Initialize with optimal settings for low latency
      this.audioContext = new AudioContext({
        latencyHint: 'interactive',
        sampleRate: this.config.sampleRate,
      })

      // Resume context if suspended
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume()
      }

      // Initialize Web Worker for offloading computation
      if (this.config.enableWebWorker && typeof Worker !== 'undefined') {
        await this.initializeWebWorker()
      }

      // Initialize Audio Worklet for real-time processing
      if (this.audioContext.audioWorklet) {
        await this.initializeAudioWorklet()
      }
    } catch (error) {
      console.error('Failed to initialize audio optimizer:', error)
      throw error
    }
  }

  private async initializeWebWorker(): Promise<void> {
    const workerCode = `
      // Audio processing worker for offloading computation
      let audioBuffer = []
      let isProcessing = false
      
      self.onmessage = function(e) {
        const { type, data } = e.data
        
        switch (type) {
          case 'PROCESS_AUDIO':
            if (!isProcessing) {
              isProcessing = true
              const processed = processAudioChunk(data.audioData, data.config)
              self.postMessage({
                type: 'AUDIO_PROCESSED',
                data: { processed, processingTime: performance.now() - data.startTime }
              })
              isProcessing = false
            }
            break
            
          case 'BATCH_PROCESS':
            batchProcessAudio(data.chunks, data.config)
            break
        }
      }
      
      function processAudioChunk(audioData, config) {
        // Optimized audio processing
        const processed = new Float32Array(audioData.length)
        
        // Apply noise gate for efficiency
        const noiseGate = config.noiseGate || 0.01
        
        for (let i = 0; i < audioData.length; i++) {
          let sample = audioData[i]
          
          // Noise gate
          if (Math.abs(sample) < noiseGate) {
            sample = 0
          }
          
          // Dynamic range compression
          if (config.compressionLevel > 0) {
            const threshold = 0.7
            if (Math.abs(sample) > threshold) {
              const ratio = config.compressionLevel
              const excess = Math.abs(sample) - threshold
              sample = Math.sign(sample) * (threshold + excess / ratio)
            }
          }
          
          processed[i] = sample
        }
        
        return processed
      }
      
      function batchProcessAudio(chunks, config) {
        const results = chunks.map(chunk => processAudioChunk(chunk, config))
        self.postMessage({
          type: 'BATCH_PROCESSED',
          data: { results }
        })
      }
    `

    const blob = new Blob([workerCode], { type: 'application/javascript' })
    this.worker = new Worker(URL.createObjectURL(blob))

    this.worker.onmessage = (e) => {
      const { type, data } = e.data
      
      if (type === 'AUDIO_PROCESSED') {
        this.performanceMetrics.processingTime = data.processingTime
      }
    }
  }

  private async initializeAudioWorklet(): Promise<void> {
    if (!this.audioContext) return

    const workletCode = `
      class OptimizedAudioProcessor extends AudioWorkletProcessor {
        constructor() {
          super()
          this.bufferSize = 512
          this.inputBuffer = new Float32Array(this.bufferSize)
          this.outputBuffer = new Float32Array(this.bufferSize)
          this.bufferIndex = 0
          this.lastProcessTime = 0
        }
        
        process(inputs, outputs, parameters) {
          const input = inputs[0]
          const output = outputs[0]
          
          if (input.length > 0 && output.length > 0) {
            const inputChannel = input[0]
            const outputChannel = output[0]
            
            const startTime = performance.now()
            
            // Optimized processing loop
            for (let i = 0; i < inputChannel.length; i++) {
              // Simple passthrough with minimal processing
              outputChannel[i] = inputChannel[i] * 0.8 // Slight attenuation
            }
            
            const processingTime = performance.now() - startTime
            
            // Report performance metrics
            if (processingTime > 5) { // Only report if processing takes >5ms
              this.port.postMessage({
                type: 'PERFORMANCE_UPDATE',
                processingTime,
                bufferSize: inputChannel.length
              })
            }
          }
          
          return true
        }
      }
      
      registerProcessor('optimized-audio-processor', OptimizedAudioProcessor)
    `

    const blob = new Blob([workletCode], { type: 'application/javascript' })
    const workletURL = URL.createObjectURL(blob)

    try {
      await this.audioContext.audioWorklet.addModule(workletURL)
      this.workletNode = new AudioWorkletNode(this.audioContext, 'optimized-audio-processor')
      
      this.workletNode.port.onmessage = (e) => {
        if (e.data.type === 'PERFORMANCE_UPDATE') {
          this.updatePerformanceMetrics({
            processingTime: e.data.processingTime
          })
        }
      }
    } catch (error) {
      console.warn('Audio worklet initialization failed, falling back to script processor:', error)
    } finally {
      URL.revokeObjectURL(workletURL)
    }
  }

  /**
   * Process audio with optimizations for minimum latency
   */
  async processAudioForLowLatency(audioData: Float32Array): Promise<{
    processed: Float32Array
    latency: number
    quality: number
  }> {
    const startTime = performance.now()

    let processed: Float32Array

    // Use Web Worker for heavy processing if available
    if (this.worker && audioData.length > 1024) {
      processed = await this.processWithWorker(audioData)
    } else {
      // Inline processing for small chunks (minimal latency)
      processed = this.processInline(audioData)
    }

    const latency = performance.now() - startTime
    const quality = this.calculateAudioQuality(processed)

    // Update metrics
    this.updatePerformanceMetrics({
      processingTime: latency,
      audioQuality: quality
    })

    return { processed, latency, quality }
  }

  private processInline(audioData: Float32Array): Float32Array {
    const processed = new Float32Array(audioData.length)
    const noiseGate = 0.01
    const compressionRatio = this.config.compressionLevel

    // Optimized single-pass processing
    for (let i = 0; i < audioData.length; i++) {
      let sample = audioData[i]

      // Noise gate for efficiency
      if (Math.abs(sample) < noiseGate) {
        sample = 0
      } else {
        // Dynamic compression
        const threshold = 0.7
        if (Math.abs(sample) > threshold) {
          const excess = Math.abs(sample) - threshold
          sample = Math.sign(sample) * (threshold + excess / compressionRatio)
        }
      }

      processed[i] = sample
    }

    return processed
  }

  private async processWithWorker(audioData: Float32Array): Promise<Float32Array> {
    return new Promise((resolve) => {
      if (!this.worker) {
        resolve(this.processInline(audioData))
        return
      }

      const handleMessage = (e: MessageEvent) => {
        if (e.data.type === 'AUDIO_PROCESSED') {
          this.worker!.removeEventListener('message', handleMessage)
          resolve(e.data.data.processed)
        }
      }

      this.worker.addEventListener('message', handleMessage)
      this.worker.postMessage({
        type: 'PROCESS_AUDIO',
        data: {
          audioData,
          config: this.config,
          startTime: performance.now()
        }
      })
    })
  }

  /**
   * Optimize audio buffer size based on current performance
   */
  optimizeBufferSize(): number {
    const { processingTime, bufferUnderruns } = this.performanceMetrics
    let optimalSize = this.config.bufferSize

    // Increase buffer size if we're experiencing underruns
    if (bufferUnderruns > 3) {
      optimalSize = Math.min(optimalSize * 2, 2048)
    }

    // Decrease buffer size if processing is consistently fast
    if (processingTime < this.config.maxLatency * 0.3) {
      optimalSize = Math.max(optimalSize / 2, 256)
    }

    // Ensure buffer size is power of 2
    optimalSize = Math.pow(2, Math.round(Math.log2(optimalSize)))

    this.config.bufferSize = optimalSize
    return optimalSize
  }

  /**
   * Create optimized media stream constraints
   */
  getOptimizedConstraints(): MediaStreamConstraints {
    return {
      audio: {
        sampleRate: this.config.sampleRate,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        latency: this.config.maxLatency / 1000, // Convert to seconds
        // @ts-ignore - experimental constraint
        googEchoCancellation: true,
        googAutoGainControl: true,
        googNoiseSuppression: true,
        googHighpassFilter: true,
        googTypingNoiseDetection: true,
      }
    }
  }

  private calculateAudioQuality(audioData: Float32Array): number {
    let sum = 0
    let peakCount = 0
    const threshold = 0.95

    for (let i = 0; i < audioData.length; i++) {
      sum += audioData[i] * audioData[i]
      if (Math.abs(audioData[i]) > threshold) {
        peakCount++
      }
    }

    const rms = Math.sqrt(sum / audioData.length)
    const peakRatio = peakCount / audioData.length

    // Quality score (0-1): good RMS level with minimal clipping
    let quality = Math.min(rms * 5, 1.0) // Boost low levels
    quality -= peakRatio * 2 // Penalize clipping
    quality = Math.max(0, Math.min(1, quality))

    return quality
  }

  private updatePerformanceMetrics(updates: Partial<PerformanceMetrics>): void {
    this.performanceMetrics = { ...this.performanceMetrics, ...updates }
  }

  /**
   * Get current performance metrics
   */
  getMetrics(): PerformanceMetrics & { isOptimal: boolean } {
    return {
      ...this.performanceMetrics,
      isOptimal: this.performanceMetrics.processingTime < this.config.maxLatency &&
                this.performanceMetrics.audioQuality > 0.8 &&
                this.performanceMetrics.bufferUnderruns < 2
    }
  }

  /**
   * Memory cleanup
   */
  dispose(): void {
    if (this.worker) {
      this.worker.terminate()
      this.worker = null
    }

    if (this.workletNode) {
      this.workletNode.disconnect()
      this.workletNode = null
    }

    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close()
      this.audioContext = null
    }
  }
}

export { AudioOptimizer, type AudioOptimizationConfig, type PerformanceMetrics }