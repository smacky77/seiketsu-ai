import { useCallback, useEffect, useRef, useState } from 'react'
import { useVoiceAIStore } from '../stores/voiceAIStore'
import { AudioProcessor } from '../services/AudioProcessor'
import { VoiceWebRTC } from '../services/VoiceWebRTC'
import { AIModelIntegration } from '../services/AIModelIntegration'
import { ConversationEngine } from '../services/ConversationEngine'
import type { 
  VoiceAIConfig, 
  AudioStreamConfig,
  VoiceActivityDetection,
  SpeechToTextResult,
  VoiceAIEvent
} from '../types'

interface UseVoiceEngineOptions {
  config: VoiceAIConfig
  autoStart?: boolean
  enableVAD?: boolean
  enableWebRTC?: boolean
}

interface VoiceEngineState {
  isInitialized: boolean
  isConnected: boolean
  isListening: boolean
  isSpeaking: boolean
  isProcessing: boolean
  audioLevel: number
  latency: {
    total: number
    stt: number
    processing: number
    tts: number
  }
  error: string | null
}

export function useVoiceEngine(options: UseVoiceEngineOptions) {
  const {
    initialize,
    connect,
    disconnect,
    setListening,
    setSpeaking,
    setProcessing,
    updateAudioLevels,
    recordLatency,
    setError,
    clearError
  } = useVoiceAIStore()

  const [state, setState] = useState<VoiceEngineState>({
    isInitialized: false,
    isConnected: false,
    isListening: false,
    isSpeaking: false,
    isProcessing: false,
    audioLevel: 0,
    latency: { total: 0, stt: 0, processing: 0, tts: 0 },
    error: null
  })

  // Service instances
  const audioProcessorRef = useRef<AudioProcessor | null>(null)
  const webRTCRef = useRef<VoiceWebRTC | null>(null)
  const aiModelRef = useRef<AIModelIntegration | null>(null)
  const conversationEngineRef = useRef<ConversationEngine | null>(null)
  
  // State tracking
  const isInitializedRef = useRef(false)
  const currentAudioBlobRef = useRef<Blob | null>(null)
  const recordingStartTimeRef = useRef<number>(0)

  // Initialize voice engine
  const initializeEngine = useCallback(async () => {
    if (isInitializedRef.current) return

    try {
      setState(prev => ({ ...prev, error: null }))
      clearError()

      // Initialize services
      audioProcessorRef.current = new AudioProcessor({
        sampleRate: options.config.realtime.audioSampleRate,
        channels: options.config.realtime.channels,
        bitDepth: options.config.realtime.bitDepth,
        bufferSize: 4096,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      })

      if (options.enableWebRTC) {
        webRTCRef.current = new VoiceWebRTC()
      }

      aiModelRef.current = new AIModelIntegration(options.config)
      conversationEngineRef.current = new ConversationEngine()

      // Set up event listeners
      setupEventListeners()

      // Initialize all services
      await audioProcessorRef.current.initialize()
      if (webRTCRef.current) {
        await webRTCRef.current.initialize()
      }
      await aiModelRef.current.initialize()

      // Initialize store
      await initialize(options.config)

      isInitializedRef.current = true
      setState(prev => ({ ...prev, isInitialized: true }))

      console.log('Voice engine initialized successfully')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to initialize voice engine'
      setState(prev => ({ ...prev, error: errorMessage }))
      setError({
        code: 'INITIALIZATION_ERROR',
        message: errorMessage,
        recoverable: true,
        timestamp: Date.now()
      })
      throw error
    }
  }, [options.config, options.enableWebRTC, initialize, setError, clearError])

  // Setup event listeners for all services
  const setupEventListeners = useCallback(() => {
    const handleVoiceAIEvent = (event: VoiceAIEvent) => {
      switch (event.type) {
        case 'voice_activity_start':
          if (options.enableVAD) {
            startListening()
          }
          break
        
        case 'voice_activity_end':
          if (options.enableVAD) {
            stopListening()
          }
          break
        
        case 'speech_recognized':
          handleSpeechRecognition(event.data as SpeechToTextResult)
          break
        
        case 'error':
          setState(prev => ({ ...prev, error: event.data.message }))
          break
      }
    }

    // Add listeners to all services
    audioProcessorRef.current?.addEventListener(handleVoiceAIEvent)
    webRTCRef.current?.addEventListener(handleVoiceAIEvent)
    aiModelRef.current?.addEventListener(handleVoiceAIEvent)
    conversationEngineRef.current?.addEventListener(handleVoiceAIEvent)
  }, [options.enableVAD])

  // Start listening for audio input
  const startListening = useCallback(async () => {
    if (!audioProcessorRef.current || state.isListening) return

    try {
      const mediaStream = await audioProcessorRef.current.startCapture()
      recordingStartTimeRef.current = Date.now()
      
      setState(prev => ({ ...prev, isListening: true }))
      setListening(true)
      
      console.log('Started listening')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to start listening'
      setState(prev => ({ ...prev, error: errorMessage }))
      setError({
        code: 'LISTEN_ERROR',
        message: errorMessage,
        recoverable: true,
        timestamp: Date.now()
      })
    }
  }, [state.isListening, setListening, setError])

  // Stop listening
  const stopListening = useCallback(async () => {
    if (!audioProcessorRef.current || !state.isListening) return

    try {
      audioProcessorRef.current.stopCapture()
      
      // Process recorded audio if available
      if (currentAudioBlobRef.current && aiModelRef.current) {
        setState(prev => ({ ...prev, isProcessing: true }))
        setProcessing(true)
        
        const sttStartTime = Date.now()
        const result = await aiModelRef.current.transcribeAudio(currentAudioBlobRef.current)
        const sttLatency = Date.now() - sttStartTime
        
        recordLatency('speechToText', sttLatency)
        setState(prev => ({ 
          ...prev, 
          latency: { ...prev.latency, stt: sttLatency }
        }))
        
        // Process with conversation engine
        if (conversationEngineRef.current && result.text.trim()) {
          const processingStartTime = Date.now()
          const response = await conversationEngineRef.current.processUserInput(result.text, result.confidence)
          const processingLatency = Date.now() - processingStartTime
          
          recordLatency('processing', processingLatency)
          setState(prev => ({ 
            ...prev, 
            latency: { ...prev.latency, processing: processingLatency }
          }))
          
          // Generate speech response
          if (response && aiModelRef.current) {
            await speakResponse(response)
          }
        }
      }
      
      setState(prev => ({ ...prev, isListening: false, isProcessing: false }))
      setListening(false)
      setProcessing(false)
      
      currentAudioBlobRef.current = null
      console.log('Stopped listening')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to stop listening'
      setState(prev => ({ ...prev, error: errorMessage, isListening: false, isProcessing: false }))
      setError({
        code: 'STOP_LISTEN_ERROR',
        message: errorMessage,
        recoverable: true,
        timestamp: Date.now()
      })
    }
  }, [state.isListening, setListening, setProcessing, recordLatency, setError])

  // Handle speech recognition results
  const handleSpeechRecognition = useCallback((result: SpeechToTextResult) => {
    if (result.isFinal && result.text.trim()) {
      console.log('Speech recognized:', result.text)
      // This will be processed in stopListening
    }
  }, [])

  // Speak a response
  const speakResponse = useCallback(async (text: string) => {
    if (!aiModelRef.current) return

    try {
      setState(prev => ({ ...prev, isSpeaking: true }))
      setSpeaking(true)
      
      const ttsStartTime = Date.now()
      const audioBuffer = await aiModelRef.current.synthesizeSpeech(text)
      const ttsLatency = Date.now() - ttsStartTime
      
      recordLatency('textToSpeech', ttsLatency)
      setState(prev => ({ 
        ...prev, 
        latency: { ...prev.latency, tts: ttsLatency }
      }))
      
      // Play the audio
      await aiModelRef.current.playAudio(audioBuffer)
      
      setState(prev => ({ ...prev, isSpeaking: false }))
      setSpeaking(false)
      
      console.log('Finished speaking')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to speak response'
      setState(prev => ({ ...prev, error: errorMessage, isSpeaking: false }))
      setSpeaking(false)
      setError({
        code: 'SPEAK_ERROR',
        message: errorMessage,
        recoverable: true,
        timestamp: Date.now()
      })
    }
  }, [setSpeaking, recordLatency, setError])

  // Connect to voice service
  const connectVoice = useCallback(async () => {
    if (!isInitializedRef.current) {
      await initializeEngine()
    }

    try {
      await connect()
      setState(prev => ({ ...prev, isConnected: true }))
      
      if (options.autoStart) {
        await startListening()
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to connect'
      setState(prev => ({ ...prev, error: errorMessage }))
      throw error
    }
  }, [connect, initializeEngine, options.autoStart, startListening])

  // Disconnect from voice service
  const disconnectVoice = useCallback(async () => {
    try {
      if (state.isListening) {
        await stopListening()
      }
      
      disconnect()
      setState(prev => ({ ...prev, isConnected: false, isListening: false, isSpeaking: false }))
    } catch (error) {
      console.error('Error disconnecting:', error)
    }
  }, [state.isListening, stopListening, disconnect])

  // Toggle listening state
  const toggleListening = useCallback(async () => {
    if (state.isListening) {
      await stopListening()
    } else {
      await startListening()
    }
  }, [state.isListening, startListening, stopListening])

  // Manual speech input (for testing)
  const processTextInput = useCallback(async (text: string) => {
    if (!conversationEngineRef.current) return

    try {
      setState(prev => ({ ...prev, isProcessing: true }))
      setProcessing(true)
      
      const response = await conversationEngineRef.current.processUserInput(text, 1.0)
      
      if (response) {
        await speakResponse(response)
      }
      
      setState(prev => ({ ...prev, isProcessing: false }))
      setProcessing(false)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to process text input'
      setState(prev => ({ ...prev, error: errorMessage, isProcessing: false }))
      setError({
        code: 'TEXT_PROCESS_ERROR',
        message: errorMessage,
        recoverable: true,
        timestamp: Date.now()
      })
    }
  }, [setProcessing, speakResponse, setError])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      audioProcessorRef.current?.destroy()
      webRTCRef.current?.destroy()
      aiModelRef.current?.destroy()
      conversationEngineRef.current?.destroy()
    }
  }, [])

  // Auto-initialize if enabled
  useEffect(() => {
    if (options.autoStart && !isInitializedRef.current) {
      initializeEngine()
    }
  }, [options.autoStart, initializeEngine])

  return {
    // State
    ...state,
    
    // Actions
    initialize: initializeEngine,
    connect: connectVoice,
    disconnect: disconnectVoice,
    startListening,
    stopListening,
    toggleListening,
    speak: speakResponse,
    processText: processTextInput,
    
    // Service references (for advanced usage)
    audioProcessor: audioProcessorRef.current,
    webRTC: webRTCRef.current,
    aiModel: aiModelRef.current,
    conversationEngine: conversationEngineRef.current
  }
}