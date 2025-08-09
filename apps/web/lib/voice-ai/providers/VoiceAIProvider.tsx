'use client'

import React, { createContext, useContext, useEffect, useRef, useState } from 'react'
import { useVoiceAIStore } from '../stores/voiceAIStore'
import { AudioProcessor } from '../services/AudioProcessor'
import { VoiceWebRTC } from '../services/VoiceWebRTC'
import { AIModelIntegration } from '../services/AIModelIntegration'
import { ConversationEngine } from '../services/ConversationEngine'
import type { 
  VoiceAIConfig, 
  VoiceAIEvent, 
  VoiceAIError,
  VoiceAgent,
  LeadProfile
} from '../types'

interface VoiceAIContextValue {
  // State
  isInitialized: boolean
  isConnected: boolean
  isListening: boolean
  isSpeaking: boolean
  isProcessing: boolean
  currentAgent: VoiceAgent | null
  currentLead: LeadProfile | null
  error: VoiceAIError | null
  
  // Services
  audioProcessor: AudioProcessor | null
  webRTC: VoiceWebRTC | null
  aiModel: AIModelIntegration | null
  conversationEngine: ConversationEngine | null
  
  // Actions
  initialize: (config: VoiceAIConfig) => Promise<void>
  shutdown: () => void
  startListening: () => Promise<void>
  stopListening: () => Promise<void>
  speak: (text: string) => Promise<void>
  processText: (text: string) => Promise<string>
  
  // Event handling
  addEventListener: (listener: (event: VoiceAIEvent) => void) => void
  removeEventListener: (listener: (event: VoiceAIEvent) => void) => void
}

const VoiceAIContext = createContext<VoiceAIContextValue | null>(null)

interface VoiceAIProviderProps {
  children: React.ReactNode
  config?: Partial<VoiceAIConfig>
  autoInitialize?: boolean
  onError?: (error: VoiceAIError) => void
  onEvent?: (event: VoiceAIEvent) => void
}

export function VoiceAIProvider({ 
  children, 
  config = {},
  autoInitialize = false,
  onError,
  onEvent
}: VoiceAIProviderProps) {
  const store = useVoiceAIStore()
  const [isInitialized, setIsInitialized] = useState(false)
  
  // Service instances
  const audioProcessorRef = useRef<AudioProcessor | null>(null)
  const webRTCRef = useRef<VoiceWebRTC | null>(null)
  const aiModelRef = useRef<AIModelIntegration | null>(null)
  const conversationEngineRef = useRef<ConversationEngine | null>(null)
  
  // Event listeners
  const eventListenersRef = useRef<Set<(event: VoiceAIEvent) => void>>(new Set())
  
  // Default configuration
  const defaultConfig: VoiceAIConfig = {
    elevenlabs: {
      apiKey: process.env.NEXT_PUBLIC_ELEVENLABS_API_KEY || '',
      voiceId: process.env.NEXT_PUBLIC_ELEVENLABS_VOICE_ID || 'default',
      modelId: 'eleven_monolingual_v1',
      stability: 0.5,
      similarityBoost: 0.7
    },
    openai: {
      apiKey: process.env.NEXT_PUBLIC_OPENAI_API_KEY || '',
      model: 'gpt-4',
      temperature: 0.7,
      maxTokens: 150
    },
    realtime: {
      maxLatency: 180,
      audioSampleRate: 16000,
      channels: 1,
      bitDepth: 16
    },
    features: {
      wakeWordDetection: false,
      voiceBiometrics: false,
      emotionDetection: true,
      backgroundNoiseSupression: true
    }
  }
  
  const mergedConfig = { ...defaultConfig, ...config }

  // Initialize voice AI services
  const initialize = async (customConfig?: VoiceAIConfig) => {
    if (isInitialized) return
    
    const finalConfig = customConfig || mergedConfig
    
    try {
      setIsInitialized(false)
      
      // Validate required configuration
      if (!finalConfig.elevenlabs.apiKey && !finalConfig.openai.apiKey) {
        throw new Error('At least one AI service API key is required')
      }
      
      // Initialize services
      audioProcessorRef.current = new AudioProcessor({
        sampleRate: finalConfig.realtime.audioSampleRate,
        channels: finalConfig.realtime.channels,
        bitDepth: finalConfig.realtime.bitDepth,
        bufferSize: 4096,
        echoCancellation: true,
        noiseSuppression: finalConfig.features.backgroundNoiseSupression,
        autoGainControl: true
      })
      
      webRTCRef.current = new VoiceWebRTC()
      aiModelRef.current = new AIModelIntegration(finalConfig)
      conversationEngineRef.current = new ConversationEngine()
      
      // Set up event forwarding
      setupEventForwarding()
      
      // Initialize all services
      await audioProcessorRef.current.initialize()
      await webRTCRef.current.initialize()
      await aiModelRef.current.initialize()
      
      // Initialize store
      await store.initialize(finalConfig)
      
      setIsInitialized(true)
      
      console.log('VoiceAI initialized successfully')
      
      // Emit initialization event
      emitEvent({
        type: 'initialized',
        data: { config: finalConfig }
      })
      
    } catch (error) {
      const voiceError: VoiceAIError = {
        code: 'INITIALIZATION_ERROR',
        message: error instanceof Error ? error.message : 'Failed to initialize VoiceAI',
        recoverable: true,
        timestamp: Date.now()
      }
      
      handleError(voiceError)
      throw error
    }
  }

  // Shutdown voice AI services
  const shutdown = () => {
    try {
      // Stop any active processes
      if (store.isListening) {
        stopListening()
      }
      
      // Destroy services
      audioProcessorRef.current?.destroy()
      webRTCRef.current?.destroy()
      aiModelRef.current?.destroy()
      conversationEngineRef.current?.destroy()
      
      // Clear references
      audioProcessorRef.current = null
      webRTCRef.current = null
      aiModelRef.current = null
      conversationEngineRef.current = null
      
      // Reset store
      store.shutdown()
      setIsInitialized(false)
      
      console.log('VoiceAI shutdown complete')
      
    } catch (error) {
      console.error('Error during shutdown:', error)
    }
  }

  // Start listening for voice input
  const startListening = async () => {
    if (!audioProcessorRef.current || !isInitialized) {
      throw new Error('VoiceAI not initialized')
    }
    
    try {
      const mediaStream = await audioProcessorRef.current.startCapture()
      store.setListening(true)
      
      emitEvent({
        type: 'listening_started',
        data: { mediaStream }
      })
      
    } catch (error) {
      const voiceError: VoiceAIError = {
        code: 'LISTEN_ERROR',
        message: error instanceof Error ? error.message : 'Failed to start listening',
        recoverable: true,
        timestamp: Date.now()
      }
      
      handleError(voiceError)
      throw error
    }
  }

  // Stop listening
  const stopListening = async () => {
    if (!audioProcessorRef.current) return
    
    try {
      audioProcessorRef.current.stopCapture()
      store.setListening(false)
      
      emitEvent({
        type: 'listening_stopped',
        data: {}
      })
      
    } catch (error) {
      console.error('Error stopping listening:', error)
    }
  }

  // Speak text using TTS
  const speak = async (text: string) => {
    if (!aiModelRef.current || !isInitialized) {
      throw new Error('VoiceAI not initialized')
    }
    
    try {
      store.setSpeaking(true)
      
      const audioBuffer = await aiModelRef.current.synthesizeSpeech(text)
      await aiModelRef.current.playAudio(audioBuffer)
      
      store.setSpeaking(false)
      
      emitEvent({
        type: 'speech_synthesized',
        data: { text, audioBuffer }
      })
      
    } catch (error) {
      store.setSpeaking(false)
      
      const voiceError: VoiceAIError = {
        code: 'TTS_ERROR',
        message: error instanceof Error ? error.message : 'Failed to synthesize speech',
        recoverable: true,
        timestamp: Date.now()
      }
      
      handleError(voiceError)
      throw error
    }
  }

  // Process text input through conversation engine
  const processText = async (text: string): Promise<string> => {
    if (!conversationEngineRef.current || !isInitialized) {
      throw new Error('VoiceAI not initialized')
    }
    
    try {
      store.setProcessing(true)
      
      const response = await conversationEngineRef.current.processUserInput(text)
      
      store.setProcessing(false)
      
      emitEvent({
        type: 'text_processed',
        data: { input: text, response }
      })
      
      return response
      
    } catch (error) {
      store.setProcessing(false)
      
      const voiceError: VoiceAIError = {
        code: 'PROCESSING_ERROR',
        message: error instanceof Error ? error.message : 'Failed to process text',
        recoverable: true,
        timestamp: Date.now()
      }
      
      handleError(voiceError)
      throw error
    }
  }

  // Event management
  const addEventListener = (listener: (event: VoiceAIEvent) => void) => {
    eventListenersRef.current.add(listener)
  }

  const removeEventListener = (listener: (event: VoiceAIEvent) => void) => {
    eventListenersRef.current.delete(listener)
  }

  // Setup event forwarding from services
  const setupEventForwarding = () => {
    const forwardEvent = (event: VoiceAIEvent) => {
      emitEvent(event)
    }
    
    audioProcessorRef.current?.addVoiceAIEventListener(forwardEvent)
    webRTCRef.current?.addVoiceAIEventListener(forwardEvent)
    aiModelRef.current?.addVoiceAIEventListener(forwardEvent)
    conversationEngineRef.current?.addVoiceAIEventListener(forwardEvent)
  }

  // Emit event to all listeners
  const emitEvent = (event: VoiceAIEvent) => {
    // Call external handler if provided
    onEvent?.(event)
    
    // Call all registered listeners
    eventListenersRef.current.forEach(listener => {
      try {
        listener(event)
      } catch (error) {
        console.error('Error in event listener:', error)
      }
    })
  }

  // Handle errors
  const handleError = (error: VoiceAIError) => {
    store.setError(error)
    onError?.(error)
    
    emitEvent({
      type: 'error',
      data: error
    })
  }

  // Auto-initialize if enabled
  useEffect(() => {
    if (autoInitialize && !isInitialized) {
      initialize().catch(error => {
        console.error('Auto-initialization failed:', error)
      })
    }
  }, [autoInitialize])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      shutdown()
    }
  }, [])

  // Subscribe to store errors
  useEffect(() => {
    // Since we're using the hook directly, we can access the error from the store
    if (store.error) {
      onError?.(store.error)
    }
  }, [onError, store.error])

  const contextValue: VoiceAIContextValue = {
    // State
    isInitialized,
    isConnected: store.isConnected,
    isListening: store.isListening,
    isSpeaking: store.isSpeaking,
    isProcessing: store.isProcessing,
    currentAgent: store.activeAgent || null,
    currentLead: store.currentLead || null,
    error: store.error || null,
    
    // Services
    audioProcessor: audioProcessorRef.current,
    webRTC: webRTCRef.current,
    aiModel: aiModelRef.current,
    conversationEngine: conversationEngineRef.current,
    
    // Actions
    initialize,
    shutdown,
    startListening,
    stopListening,
    speak,
    processText,
    
    // Event handling
    addEventListener,
    removeEventListener
  }

  return (
    <VoiceAIContext.Provider value={contextValue}>
      {children}
    </VoiceAIContext.Provider>
  )
}

// Hook to use VoiceAI context
export function useVoiceAI(): VoiceAIContextValue {
  const context = useContext(VoiceAIContext)
  
  if (!context) {
    throw new Error('useVoiceAI must be used within a VoiceAIProvider')
  }
  
  return context
}

// Higher-order component for VoiceAI integration
interface WithVoiceAIProps {
  voiceAI: VoiceAIContextValue
}

export function withVoiceAI<P extends object>(
  Component: React.ComponentType<P & WithVoiceAIProps>
): React.ComponentType<P> {
  return function WithVoiceAIComponent(props: P) {
    const voiceAI = useVoiceAI()
    
    return <Component {...props} voiceAI={voiceAI} />
  }
}

// Error boundary for VoiceAI components
interface VoiceAIErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class VoiceAIErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ComponentType<{ error: Error }> },
  VoiceAIErrorBoundaryState
> {
  constructor(props: { children: React.ReactNode; fallback?: React.ComponentType<{ error: Error }> }) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): VoiceAIErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('VoiceAI Error Boundary caught an error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback
        return <FallbackComponent error={this.state.error} />
      }
      
      return (
        <div className="voice-ai-error p-4 bg-red-50 border border-red-200 rounded-lg">
          <h3 className="text-red-800 font-semibold">Voice AI Error</h3>
          <p className="text-red-600 text-sm mt-1">
            {this.state.error.message}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200"
          >
            Try Again
          </button>
        </div>
      )
    }

    return this.props.children
  }
}