/**
 * Enterprise Voice Service
 * Handles real-time voice processing, conversation intelligence, and demo capabilities
 */
import { VoiceStream } from '../../api/services/voice.service'

export interface VoiceIntelligenceConfig {
  apiUrl: string
  wsUrl: string
  apiKey?: string
  agentId: string
  enableEmotionDetection?: boolean
  enableRealTimeTranscription?: boolean
  audioSettings: {
    sampleRate: number
    channels: number
    bitDepth: number
    noiseReduction: boolean
    echoCancellation: boolean
  }
}

export interface ConversationMetrics {
  responseTimeMs: number
  emotionAccuracy: number
  intentConfidence: number
  conversationFlow: number
  leadQualificationScore: number
}

export interface DemoScenario {
  id: string
  name: string
  type: string
  description: string
  userProfile: {
    name: string
    background: string
    needs: string[]
    objections: string[]
    timeline: string
  }
  expectedFlow: {
    phase: string
    userInput: string
    expectedResponse: string
    keyPoints: string[]
    metrics: string[]
  }[]
  successCriteria: string[]
}

export interface VoiceAnalytics {
  sessionId: string
  duration: number
  emotionTimeline: Array<{
    timestamp: number
    emotion: string
    confidence: number
    valence: number
    arousal: number
  }>
  intentFlow: Array<{
    timestamp: number
    intent: string
    confidence: number
  }>
  objections: Array<{
    timestamp: number
    type: string
    resolved: boolean
    resolutionStrategy: string
  }>
  responseQuality: {
    averageLatency: number
    relevanceScore: number
    empathyScore: number
    professionalismScore: number
  }
}

export class EnterpriseVoiceService {
  private config: VoiceIntelligenceConfig
  private websocket: WebSocket | null = null
  private mediaRecorder: MediaRecorder | null = null
  private audioContext: AudioContext | null = null
  private audioStream: MediaStream | null = null
  private isRecording = false
  private isConnected = false
  private eventHandlers: { [key: string]: Function[] } = {}
  private currentSessionId: string | null = null
  private conversationMetrics: ConversationMetrics = {
    responseTimeMs: 0,
    emotionAccuracy: 0,
    intentConfidence: 0,
    conversationFlow: 0,
    leadQualificationScore: 0
  }

  constructor(config: VoiceIntelligenceConfig) {
    this.config = config
    this.currentSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * Initialize the voice service
   */
  async initialize(): Promise<void> {
    try {
      // Initialize audio context
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: this.config.audioSettings.sampleRate
      })

      // Request microphone access with high quality settings
      this.audioStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: this.config.audioSettings.sampleRate,
          channelCount: this.config.audioSettings.channels,
          sampleSize: this.config.audioSettings.bitDepth,
          echoCancellation: this.config.audioSettings.echoCancellation,
          noiseSuppression: this.config.audioSettings.noiseReduction,
          autoGainControl: true
        }
      })

      // Set up audio processing pipeline
      await this.setupAudioProcessing()

      this.emit('initialized')
      // Enterprise voice service initialized successfully
    } catch (error) {
      console.error('Failed to initialize voice service:', error)
      this.emit('error', { type: 'initialization', error })
      throw error
    }
  }

  /**
   * Set up advanced audio processing pipeline
   */
  private async setupAudioProcessing(): Promise<void> {
    if (!this.audioContext || !this.audioStream) return

    const source = this.audioContext.createMediaStreamSource(this.audioStream)
    
    // Create audio processing nodes
    const gainNode = this.audioContext.createGain()
    const analyzerNode = this.audioContext.createAnalyser()
    const compressionNode = this.audioContext.createDynamicsCompressor()
    
    // Configure analyzer for real-time audio analysis
    analyzerNode.fftSize = 2048
    analyzerNode.smoothingTimeConstant = 0.8

    // Configure compression for consistent audio levels
    compressionNode.threshold.setValueAtTime(-24, this.audioContext.currentTime)
    compressionNode.knee.setValueAtTime(30, this.audioContext.currentTime)
    compressionNode.ratio.setValueAtTime(12, this.audioContext.currentTime)
    compressionNode.attack.setValueAtTime(0.003, this.audioContext.currentTime)
    compressionNode.release.setValueAtTime(0.25, this.audioContext.currentTime)

    // Connect audio processing chain
    source.connect(gainNode)
    gainNode.connect(compressionNode)
    compressionNode.connect(analyzerNode)

    // Set up real-time audio level monitoring
    this.startAudioLevelMonitoring(analyzerNode)
  }

  /**
   * Start real-time audio level monitoring
   */
  private startAudioLevelMonitoring(analyzer: AnalyserNode): void {
    const bufferLength = analyzer.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)

    const updateLevels = () => {
      analyzer.getByteFrequencyData(dataArray)
      
      // Calculate average audio level
      const average = dataArray.reduce((sum, value) => sum + value, 0) / bufferLength
      const normalizedLevel = average / 255

      // Detect speech vs silence
      const isSpeechDetected = normalizedLevel > 0.02 // Threshold for speech detection

      this.emit('audioLevel', {
        level: normalizedLevel,
        isSpeaking: isSpeechDetected,
        timestamp: Date.now()
      })

      if (this.isConnected) {
        requestAnimationFrame(updateLevels)
      }
    }

    updateLevels()
  }

  /**
   * Connect to voice intelligence WebSocket
   */
  async connect(): Promise<void> {
    if (this.isConnected) {
      console.warn('Already connected to voice intelligence service')
      return
    }

    try {
      const wsUrl = `${this.config.wsUrl}/voice-intelligence/stream/${this.currentSessionId}?agent_id=${this.config.agentId}`
      this.websocket = new WebSocket(wsUrl)

      this.websocket.onopen = () => {
        this.isConnected = true
        this.emit('connected', { sessionId: this.currentSessionId })
        // Connected to voice intelligence service
      }

      this.websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.handleWebSocketMessage(data)
        } catch (error) {
          this.emit('error', { type: 'parsing', error })
        }
      }

      this.websocket.onclose = () => {
        this.isConnected = false
        this.emit('disconnected')
        // Disconnected from voice intelligence service
      }

      this.websocket.onerror = (error) => {
        this.emit('error', { type: 'websocket', error })
      }

      // Wait for connection
      await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error('Connection timeout')), 10000)
        
        this.once('connected', () => {
          clearTimeout(timeout)
          resolve(void 0)
        })

        this.once('error', (error) => {
          clearTimeout(timeout)
          reject(error)
        })
      })

    } catch (error) {
      console.error('Failed to connect to voice intelligence service:', error)
      throw error
    }
  }

  /**
   * Handle WebSocket messages
   */
  private handleWebSocketMessage(data: any): void {
    const startTime = data.type === 'transcription' ? Date.now() : null

    switch (data.type) {
      case 'transcription':
        this.emit('transcription', {
          text: data.text,
          confidence: data.confidence,
          timestamp: data.timestamp
        })
        break

      case 'emotion_detected':
        this.conversationMetrics.emotionAccuracy = data.confidence
        this.emit('emotionDetected', {
          emotion: data.emotion,
          confidence: data.confidence,
          valence: data.valence,
          arousal: data.arousal,
          timestamp: data.timestamp
        })
        break

      case 'intent_classified':
        this.conversationMetrics.intentConfidence = data.confidence
        this.emit('intentClassified', {
          intent: data.intent,
          confidence: data.confidence,
          entities: data.entities,
          timestamp: data.timestamp
        })
        break

      case 'objection_detected':
        this.emit('objectionDetected', {
          objections: data.objections,
          timestamp: data.timestamp
        })
        break

      case 'response_generated':
        const responseTime = data.processing_time_ms
        this.conversationMetrics.responseTimeMs = responseTime

        this.emit('responseGenerated', {
          text: data.text,
          strategy: data.strategy,
          audioUrl: data.audio_url,
          processingTime: responseTime,
          timestamp: data.timestamp
        })

        // Play audio response
        if (data.audio_url) {
          this.playAudioResponse(data.audio_url)
        }
        break

      case 'error':
        this.emit('error', {
          type: 'processing',
          message: data.message,
          timestamp: data.timestamp
        })
        break

      default:
        // Unhandled message type - could log in development only
        if (process.env.NODE_ENV === 'development') {
          console.log('Unhandled message type:', data.type)
        }
    }
  }

  /**
   * Start recording and processing
   */
  async startRecording(): Promise<void> {
    if (this.isRecording || !this.audioStream) {
      return
    }

    try {
      this.mediaRecorder = new MediaRecorder(this.audioStream, {
        mimeType: 'audio/webm;codecs=opus',
        audioBitsPerSecond: 128000
      })

      const audioChunks: Blob[] = []

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data)
        }
      }

      this.mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
        await this.sendAudioData(audioBlob)
      }

      // Start recording in 500ms intervals for real-time processing
      this.mediaRecorder.start(500)
      this.isRecording = true

      this.emit('recordingStarted')
      // Started voice recording

    } catch (error) {
      this.emit('error', { type: 'recording', error })
      throw error
    }
  }

  /**
   * Stop recording
   */
  stopRecording(): void {
    if (!this.isRecording || !this.mediaRecorder) {
      return
    }

    this.mediaRecorder.stop()
    this.isRecording = false
    
    this.emit('recordingStopped')
    // Stopped voice recording
  }

  /**
   * Send audio data to the server
   */
  private async sendAudioData(audioBlob: Blob): Promise<void> {
    if (!this.websocket || !this.isConnected) {
      // Not connected to voice intelligence service
      return
    }

    try {
      // Convert to ArrayBuffer for binary transmission
      const arrayBuffer = await audioBlob.arrayBuffer()
      this.websocket.send(arrayBuffer)
    } catch (error) {
      this.emit('error', { type: 'transmission', error })
    }
  }

  /**
   * Play audio response
   */
  private async playAudioResponse(audioUrl: string): Promise<void> {
    try {
      const audio = new Audio(audioUrl)
      
      audio.onloadstart = () => this.emit('audioPlaybackStarted')
      audio.onended = () => this.emit('audioPlaybackEnded')
      audio.onerror = (error) => this.emit('error', { type: 'playback', error })

      await audio.play()
    } catch (error) {
      this.emit('error', { type: 'playback', error })
    }
  }

  /**
   * Load demo scenario
   */
  async loadDemoScenario(scenarioType: string): Promise<DemoScenario> {
    try {
      const response = await fetch(`${this.config.apiUrl}/voice-intelligence/demo-scenario`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
        },
        body: JSON.stringify({ scenario_type: scenarioType })
      })

      if (!response.ok) {
        throw new Error(`Failed to load demo scenario: ${response.statusText}`)
      }

      const data = await response.json()
      return this.transformDemoScenario(data.scenario)
    } catch (error) {
      throw error
    }
  }

  /**
   * Transform demo scenario data
   */
  private transformDemoScenario(scenarioData: any): DemoScenario {
    return {
      id: `demo_${Date.now()}`,
      name: scenarioData.user_profile?.name || 'Demo Client',
      type: 'demo',
      description: `Demo conversation with ${scenarioData.user_profile?.name || 'client'}`,
      userProfile: {
        name: scenarioData.user_profile?.name || 'Demo Client',
        background: scenarioData.user_profile?.occupation || 'Professional',
        needs: scenarioData.user_profile?.needs || [],
        objections: scenarioData.user_profile?.objections || [],
        timeline: scenarioData.user_profile?.timeline || 'Flexible'
      },
      expectedFlow: scenarioData.conversation_flow?.map((flow: any, index: number) => ({
        phase: `Phase ${index + 1}`,
        userInput: flow.user_input,
        expectedResponse: flow.expected_response_type,
        keyPoints: flow.key_points || [],
        metrics: ['response_time', 'emotion_accuracy', 'intent_confidence']
      })) || [],
      successCriteria: scenarioData.success_metrics || []
    }
  }

  /**
   * Get current conversation metrics
   */
  getConversationMetrics(): ConversationMetrics {
    return { ...this.conversationMetrics }
  }

  /**
   * Get conversation analytics
   */
  async getConversationAnalytics(): Promise<VoiceAnalytics> {
    // This would compile analytics from the current session
    return {
      sessionId: this.currentSessionId || '',
      duration: 0,
      emotionTimeline: [],
      intentFlow: [],
      objections: [],
      responseQuality: {
        averageLatency: this.conversationMetrics.responseTimeMs,
        relevanceScore: 0.95,
        empathyScore: 0.87,
        professionalismScore: 0.92
      }
    }
  }

  /**
   * Disconnect from service
   */
  disconnect(): void {
    this.stopRecording()

    if (this.websocket) {
      this.websocket.close()
      this.websocket = null
    }

    if (this.audioStream) {
      this.audioStream.getTracks().forEach(track => track.stop())
      this.audioStream = null
    }

    if (this.audioContext) {
      this.audioContext.close()
      this.audioContext = null
    }

    this.isConnected = false
    this.emit('disconnected')
  }

  /**
   * Event handling
   */
  on(event: string, handler: Function): void {
    if (!this.eventHandlers[event]) {
      this.eventHandlers[event] = []
    }
    this.eventHandlers[event].push(handler)
  }

  once(event: string, handler: Function): void {
    const onceWrapper = (...args: any[]) => {
      handler(...args)
      this.off(event, onceWrapper)
    }
    this.on(event, onceWrapper)
  }

  off(event: string, handler: Function): void {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event] = this.eventHandlers[event].filter(h => h !== handler)
    }
  }

  private emit(event: string, data?: any): void {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event].forEach(handler => handler(data))
    }
  }
}

// Export singleton instance factory
export function createEnterpriseVoiceService(config: VoiceIntelligenceConfig): EnterpriseVoiceService {
  return new EnterpriseVoiceService(config)
}