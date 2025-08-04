import type { 
  AudioStreamConfig, 
  VoiceActivityDetection, 
  AudioVisualization,
  VoiceAIEventListener,
  VoiceAIEvent
} from '../types'

export class AudioProcessor extends EventTarget {
  private audioContext: AudioContext | null = null
  private mediaStream: MediaStream | null = null
  private sourceNode: MediaStreamAudioSourceNode | null = null
  private analyserNode: AnalyserNode | null = null
  private gainNode: GainNode | null = null
  private processorNode: ScriptProcessorNode | null = null
  
  private config: AudioStreamConfig
  private isProcessing = false
  private vadBuffer: Float32Array = new Float32Array(0)
  private vadThreshold = 0.01
  private vadFrameSize = 1024
  private listeners: VoiceAIEventListener[] = []
  
  // Audio analysis buffers
  private frequencyData: Uint8Array = new Uint8Array(0)
  private timeDomainData: Uint8Array = new Uint8Array(0)
  
  // Voice activity detection state
  private isVoiceActive = false
  private voiceStartTime = 0
  private silenceStartTime = 0
  private minVoiceDuration = 300 // ms
  private minSilenceDuration = 500 // ms

  constructor(config: AudioStreamConfig) {
    super()
    this.config = {
      sampleRate: 44100,
      channels: 1,
      bitDepth: 16,
      bufferSize: 4096,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
      ...config
    }
  }

  async initialize(): Promise<void> {
    try {
      // Initialize AudioContext
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: this.config.sampleRate
      })

      // Resume context if suspended
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume()
      }

      console.log('AudioProcessor initialized:', {
        sampleRate: this.audioContext.sampleRate,
        state: this.audioContext.state
      })
    } catch (error) {
      throw new Error(`Failed to initialize AudioContext: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  async startCapture(): Promise<MediaStream> {
    if (!this.audioContext) {
      throw new Error('AudioProcessor not initialized')
    }

    try {
      // Get user media with constraints
      const constraints: MediaStreamConstraints = {
        audio: {
          sampleRate: this.config.sampleRate,
          channelCount: this.config.channels,
          echoCancellation: this.config.echoCancellation,
          noiseSuppression: this.config.noiseSuppression,
          autoGainControl: this.config.autoGainControl
        }
      }

      this.mediaStream = await navigator.mediaDevices.getUserMedia(constraints)
      
      // Create audio processing chain
      this.setupAudioProcessing()
      
      this.isProcessing = true
      console.log('Audio capture started')
      
      return this.mediaStream
    } catch (error) {
      throw new Error(`Failed to start audio capture: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  stopCapture(): void {
    this.isProcessing = false
    
    // Stop media stream
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop())
      this.mediaStream = null
    }

    // Cleanup audio nodes
    if (this.processorNode) {
      this.processorNode.disconnect()
      this.processorNode = null
    }
    
    if (this.sourceNode) {
      this.sourceNode.disconnect()
      this.sourceNode = null
    }
    
    if (this.analyserNode) {
      this.analyserNode.disconnect()
      this.analyserNode = null
    }
    
    if (this.gainNode) {
      this.gainNode.disconnect()
      this.gainNode = null
    }

    console.log('Audio capture stopped')
  }

  private setupAudioProcessing(): void {
    if (!this.audioContext || !this.mediaStream) return

    // Create source node from media stream
    this.sourceNode = this.audioContext.createMediaStreamSource(this.mediaStream)
    
    // Create analyser for frequency analysis
    this.analyserNode = this.audioContext.createAnalyser()
    this.analyserNode.fftSize = 2048
    this.analyserNode.smoothingTimeConstant = 0.3
    
    // Create gain node for volume control
    this.gainNode = this.audioContext.createGain()
    this.gainNode.gain.value = 1.0
    
    // Create processor for real-time audio processing
    this.processorNode = this.audioContext.createScriptProcessor(
      this.config.bufferSize, 
      this.config.channels, 
      this.config.channels
    )
    
    // Initialize analysis buffers
    this.frequencyData = new Uint8Array(this.analyserNode.frequencyBinCount)
    this.timeDomainData = new Uint8Array(this.analyserNode.frequencyBinCount)
    this.vadBuffer = new Float32Array(this.vadFrameSize)
    
    // Set up audio processing callback
    this.processorNode.onaudioprocess = (event) => {
      this.processAudioFrame(event)
    }
    
    // Connect audio processing chain
    this.sourceNode
      .connect(this.gainNode)
      .connect(this.analyserNode)
      .connect(this.processorNode)
    
    // Connect to destination for monitoring (optional)
    // this.processorNode.connect(this.audioContext.destination)
  }

  private processAudioFrame(event: AudioProcessingEvent): void {
    if (!this.analyserNode || !this.isProcessing) return

    const inputBuffer = event.inputBuffer
    const inputData = inputBuffer.getChannelData(0)
    const currentTime = Date.now()
    
    // Update analysis data
    this.analyserNode.getByteFrequencyData(this.frequencyData)
    this.analyserNode.getByteTimeDomainData(this.timeDomainData)
    
    // Calculate audio level (RMS)
    let sum = 0
    for (let i = 0; i < inputData.length; i++) {
      sum += inputData[i] * inputData[i]
    }
    const rms = Math.sqrt(sum / inputData.length)
    const volume = Math.min(1, Math.max(0, rms * 10)) // Normalize to 0-1
    
    // Voice Activity Detection
    const vadResult = this.detectVoiceActivity(inputData, currentTime)
    
    // Create visualization data
    const visualization: AudioVisualization = {
      frequencyData: new Uint8Array(this.frequencyData),
      timeDomainData: new Uint8Array(this.timeDomainData),
      volume,
      pitch: this.detectPitch(this.timeDomainData)
    }
    
    // Emit events
    this.emitEvent({
      type: 'audio_processed',
      data: { visualization, vad: vadResult }
    })
    
    // Emit VAD events
    if (vadResult.isActive !== this.isVoiceActive) {
      if (vadResult.isActive) {
        this.emitEvent({ type: 'voice_activity_start', data: vadResult })
      } else {
        this.emitEvent({ type: 'voice_activity_end', data: vadResult })
      }
      this.isVoiceActive = vadResult.isActive
    }
  }

  private detectVoiceActivity(audioData: Float32Array, timestamp: number): VoiceActivityDetection {
    // Calculate energy
    let energy = 0
    for (let i = 0; i < audioData.length; i++) {
      energy += audioData[i] * audioData[i]
    }
    energy /= audioData.length
    
    // Simple threshold-based VAD
    const isActive = energy > this.vadThreshold
    const confidence = Math.min(1, energy / (this.vadThreshold * 3))
    
    // Apply temporal smoothing
    const now = timestamp
    let finalIsActive = isActive
    
    if (isActive && !this.isVoiceActive) {
      // Voice started - check minimum duration
      if (this.voiceStartTime === 0) {
        this.voiceStartTime = now
        finalIsActive = false // Wait for minimum duration
      } else if (now - this.voiceStartTime >= this.minVoiceDuration) {
        finalIsActive = true
      } else {
        finalIsActive = false
      }
    } else if (!isActive && this.isVoiceActive) {
      // Voice ended - check minimum silence duration
      if (this.silenceStartTime === 0) {
        this.silenceStartTime = now
        finalIsActive = true // Continue voice activity
      } else if (now - this.silenceStartTime >= this.minSilenceDuration) {
        finalIsActive = false
        this.voiceStartTime = 0
        this.silenceStartTime = 0
      } else {
        finalIsActive = true
      }
    } else if (isActive) {
      // Reset silence timer if voice continues
      this.silenceStartTime = 0
    }
    
    return {
      isActive: finalIsActive,
      confidence,
      energy,
      timestamp
    }
  }

  private detectPitch(timeDomainData: Uint8Array): number | undefined {
    // Simple autocorrelation pitch detection
    const correlations: number[] = []
    const minPeriod = Math.floor(this.config.sampleRate / 800) // 800 Hz max
    const maxPeriod = Math.floor(this.config.sampleRate / 80)  // 80 Hz min
    
    for (let period = minPeriod; period < maxPeriod; period++) {
      let correlation = 0
      for (let i = 0; i < timeDomainData.length - period; i++) {
        correlation += (timeDomainData[i] - 128) * (timeDomainData[i + period] - 128)
      }
      correlations.push(correlation)
    }
    
    // Find peak correlation
    let maxCorrelation = 0
    let bestPeriod = 0
    for (let i = 0; i < correlations.length; i++) {
      if (correlations[i] > maxCorrelation) {
        maxCorrelation = correlations[i]
        bestPeriod = i + minPeriod
      }
    }
    
    if (maxCorrelation > 0.3) {
      return this.config.sampleRate / bestPeriod
    }
    
    return undefined
  }

  // Volume control
  setVolume(volume: number): void {
    if (this.gainNode) {
      this.gainNode.gain.value = Math.max(0, Math.min(2, volume))
    }
  }

  getVolume(): number {
    return this.gainNode?.gain.value || 1
  }

  // Mute control
  setMuted(muted: boolean): void {
    if (this.mediaStream) {
      this.mediaStream.getAudioTracks().forEach(track => {
        track.enabled = !muted
      })
    }
  }

  isMuted(): boolean {
    if (this.mediaStream) {
      return this.mediaStream.getAudioTracks().some(track => !track.enabled)
    }
    return false
  }

  // Event management
  addEventListener(listener: VoiceAIEventListener): void {
    this.listeners.push(listener)
  }

  removeEventListener(listener: VoiceAIEventListener): void {
    const index = this.listeners.indexOf(listener)
    if (index > -1) {
      this.listeners.splice(index, 1)
    }
  }

  private emitEvent(event: VoiceAIEvent): void {
    this.listeners.forEach(listener => {
      try {
        listener(event)
      } catch (error) {
        console.error('Error in audio event listener:', error)
      }
    })
  }

  // Cleanup
  destroy(): void {
    this.stopCapture()
    
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close()
    }
    
    this.listeners = []
    console.log('AudioProcessor destroyed')
  }

  // Getters
  get isActive(): boolean {
    return this.isProcessing
  }

  get currentVisualization(): AudioVisualization | null {
    if (!this.analyserNode || !this.isProcessing) return null
    
    return {
      frequencyData: new Uint8Array(this.frequencyData),
      timeDomainData: new Uint8Array(this.timeDomainData),
      volume: this.getVolume()
    }
  }

  get audioContext(): AudioContext | null {
    return this.audioContext
  }

  get mediaStream(): MediaStream | null {
    return this.mediaStream
  }
}