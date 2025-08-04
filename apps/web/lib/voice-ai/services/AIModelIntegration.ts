import type { 
  VoiceAIConfig,
  SpeechToTextResult,
  TextToSpeechRequest,
  EmotionDetection,
  VoiceAIEventListener,
  VoiceAIEvent,
  VoiceAIError
} from '../types'

interface STTProvider {
  name: string
  transcribe(audioBlob: Blob): Promise<SpeechToTextResult>
  transcribeStream?(audioStream: MediaStream): AsyncGenerator<SpeechToTextResult>
}

interface TTSProvider {
  name: string
  synthesize(request: TextToSpeechRequest): Promise<AudioBuffer>
  getVoices?(): Promise<Voice[]>
}

interface Voice {
  id: string
  name: string
  language: string
  gender: 'male' | 'female' | 'neutral'
  style?: string
}

export class AIModelIntegration {
  private config: VoiceAIConfig
  private listeners: VoiceAIEventListener[] = []
  private sttProvider: STTProvider
  private ttsProvider: TTSProvider
  private audioContext: AudioContext | null = null
  
  // Performance tracking
  private metrics = {
    sttLatency: [] as number[],
    ttsLatency: [] as number[],
    sttAccuracy: [] as number[],
    errorCount: 0
  }

  constructor(config: VoiceAIConfig) {
    this.config = config
    this.sttProvider = new OpenAISTTProvider(config.openai)
    this.ttsProvider = new ElevenLabsTTSProvider(config.elevenlabs)
  }

  async initialize(): Promise<void> {
    try {
      // Initialize audio context
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume()
      }
      
      console.log('AI Model Integration initialized')
    } catch (error) {
      throw new Error(`Failed to initialize AI models: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  // Speech-to-Text methods
  async transcribeAudio(audioBlob: Blob): Promise<SpeechToTextResult> {
    const startTime = Date.now()
    
    try {
      const result = await this.sttProvider.transcribe(audioBlob)
      
      // Track latency
      const latency = Date.now() - startTime
      this.metrics.sttLatency.push(latency)
      this.keepMetricsSize()
      
      this.emitEvent({
        type: 'speech_recognized',
        data: result
      })
      
      return result
    } catch (error) {
      this.handleError('STT_ERROR', `Speech recognition failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
      throw error
    }
  }

  async *transcribeStream(audioStream: MediaStream): AsyncGenerator<SpeechToTextResult> {
    if (!this.sttProvider.transcribeStream) {
      throw new Error('Streaming transcription not supported by current provider')
    }

    try {
      for await (const result of this.sttProvider.transcribeStream(audioStream)) {
        this.emitEvent({
          type: 'speech_recognized',
          data: result
        })
        yield result
      }
    } catch (error) {
      this.handleError('STT_STREAM_ERROR', `Streaming transcription failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
      throw error
    }
  }

  // Text-to-Speech methods
  async synthesizeSpeech(text: string, options: Partial<TextToSpeechRequest> = {}): Promise<AudioBuffer> {
    const startTime = Date.now()
    
    try {
      const request: TextToSpeechRequest = {
        text,
        voiceId: this.config.elevenlabs.voiceId,
        modelId: this.config.elevenlabs.modelId,
        voiceSettings: {
          stability: this.config.elevenlabs.stability || 0.5,
          similarityBoost: this.config.elevenlabs.similarityBoost || 0.7,
          style: this.config.elevenlabs.style
        },
        outputFormat: 'wav',
        ...options
      }
      
      const audioBuffer = await this.ttsProvider.synthesize(request)
      
      // Track latency
      const latency = Date.now() - startTime
      this.metrics.ttsLatency.push(latency)
      this.keepMetricsSize()
      
      return audioBuffer
    } catch (error) {
      this.handleError('TTS_ERROR', `Speech synthesis failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
      throw error
    }
  }

  async playAudio(audioBuffer: AudioBuffer): Promise<void> {
    if (!this.audioContext) {
      throw new Error('Audio context not initialized')
    }

    return new Promise((resolve, reject) => {
      try {
        const source = this.audioContext!.createBufferSource()
        source.buffer = audioBuffer
        source.connect(this.audioContext!.destination)
        
        source.onended = () => resolve()
        source.onerror = (error) => reject(error)
        
        source.start()
      } catch (error) {
        reject(error)
      }
    })
  }

  // Voice and emotion analysis
  async analyzeEmotion(audioBlob: Blob): Promise<EmotionDetection> {
    // Placeholder for emotion detection - would integrate with actual service
    // For now, return mock data based on audio characteristics
    
    try {
      // This would typically call an emotion detection API
      const mockEmotion: EmotionDetection = {
        emotion: 'neutral',
        confidence: 0.7,
        arousal: 0.5,
        valence: 0.0,
        timestamp: Date.now()
      }
      
      this.emitEvent({
        type: 'emotion_detected',
        data: mockEmotion
      })
      
      return mockEmotion
    } catch (error) {
      this.handleError('EMOTION_ERROR', `Emotion analysis failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
      throw error
    }
  }

  // Utility methods
  async getAvailableVoices(): Promise<Voice[]> {
    if (this.ttsProvider.getVoices) {
      return await this.ttsProvider.getVoices()
    }
    return []
  }

  // Performance metrics
  getPerformanceMetrics() {
    const avgSTTLatency = this.metrics.sttLatency.length > 0 
      ? this.metrics.sttLatency.reduce((a, b) => a + b, 0) / this.metrics.sttLatency.length 
      : 0
    
    const avgTTSLatency = this.metrics.ttsLatency.length > 0
      ? this.metrics.ttsLatency.reduce((a, b) => a + b, 0) / this.metrics.ttsLatency.length
      : 0
    
    return {
      averageSTTLatency: avgSTTLatency,
      averageTTSLatency: avgTTSLatency,
      totalLatency: avgSTTLatency + avgTTSLatency,
      errorRate: this.metrics.errorCount / (this.metrics.sttLatency.length + this.metrics.ttsLatency.length + this.metrics.errorCount)
    }
  }

  private keepMetricsSize(): void {
    const maxSize = 100
    if (this.metrics.sttLatency.length > maxSize) {
      this.metrics.sttLatency = this.metrics.sttLatency.slice(-maxSize)
    }
    if (this.metrics.ttsLatency.length > maxSize) {
      this.metrics.ttsLatency = this.metrics.ttsLatency.slice(-maxSize)
    }
  }

  private handleError(code: string, message: string): void {
    this.metrics.errorCount++
    
    const error: VoiceAIError = {
      code,
      message,
      recoverable: true,
      timestamp: Date.now()
    }
    
    this.emitEvent({
      type: 'error',
      data: error
    })
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
        console.error('Error in AI model event listener:', error)
      }
    })
  }

  // Cleanup
  destroy(): void {
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close()
    }
    this.listeners = []
  }
}

// OpenAI Speech-to-Text Provider
class OpenAISTTProvider implements STTProvider {
  name = 'OpenAI Whisper'
  private config: VoiceAIConfig['openai']

  constructor(config: VoiceAIConfig['openai']) {
    this.config = config
  }

  async transcribe(audioBlob: Blob): Promise<SpeechToTextResult> {
    try {
      // Convert blob to the format expected by OpenAI
      const formData = new FormData()
      formData.append('file', audioBlob, 'audio.wav')
      formData.append('model', 'whisper-1')
      formData.append('response_format', 'verbose_json')
      formData.append('timestamp_granularities[]', 'word')

      const response = await fetch('https://api.openai.com/v1/audio/transcriptions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`
        },
        body: formData
      })

      if (!response.ok) {
        throw new Error(`OpenAI API error: ${response.status}`)
      }

      const data = await response.json()
      
      return {
        text: data.text,
        confidence: data.confidence || 0.9,
        isFinal: true,
        timestamp: Date.now(),
        alternatives: data.alternatives?.map((alt: any) => ({
          text: alt.text,
          confidence: alt.confidence || 0.5
        }))
      }
    } catch (error) {
      throw new Error(`OpenAI transcription failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }
}

// ElevenLabs Text-to-Speech Provider
class ElevenLabsTTSProvider implements TTSProvider {
  name = 'ElevenLabs'
  private config: VoiceAIConfig['elevenlabs']

  constructor(config: VoiceAIConfig['elevenlabs']) {
    this.config = config
  }

  async synthesize(request: TextToSpeechRequest): Promise<AudioBuffer> {
    try {
      const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${request.voiceId}`, {
        method: 'POST',
        headers: {
          'Accept': 'audio/mpeg',
          'Content-Type': 'application/json',
          'xi-api-key': this.config.apiKey
        },
        body: JSON.stringify({
          text: request.text,
          model_id: request.modelId || 'eleven_monolingual_v1',
          voice_settings: request.voiceSettings
        })
      })

      if (!response.ok) {
        throw new Error(`ElevenLabs API error: ${response.status}`)
      }

      const audioData = await response.arrayBuffer()
      
      // Convert to AudioBuffer
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      const audioBuffer = await audioContext.decodeAudioData(audioData)
      
      return audioBuffer
    } catch (error) {
      throw new Error(`ElevenLabs synthesis failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  async getVoices(): Promise<Voice[]> {
    try {
      const response = await fetch('https://api.elevenlabs.io/v1/voices', {
        headers: {
          'xi-api-key': this.config.apiKey
        }
      })

      if (!response.ok) {
        throw new Error(`ElevenLabs API error: ${response.status}`)
      }

      const data = await response.json()
      
      return data.voices.map((voice: any) => ({
        id: voice.voice_id,
        name: voice.name,
        language: voice.labels?.language || 'en',
        gender: voice.labels?.gender || 'neutral',
        style: voice.labels?.accent
      }))
    } catch (error) {
      console.error('Failed to fetch voices:', error)
      return []
    }
  }
}