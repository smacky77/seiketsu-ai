/**
 * Enterprise Voice Hook
 * React hook for enterprise voice intelligence functionality
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import { EnterpriseVoiceService, VoiceIntelligenceConfig, ConversationMetrics, VoiceAnalytics } from '../services/enterpriseVoiceService'

export interface UseEnterpriseVoiceOptions {
  config: VoiceIntelligenceConfig
  autoConnect?: boolean
  enableMetricsTracking?: boolean
  onError?: (error: any) => void
  onMetricsUpdate?: (metrics: ConversationMetrics) => void
}

export interface VoiceState {
  isInitialized: boolean
  isConnected: boolean
  isRecording: boolean
  isProcessing: boolean
  audioLevel: number
  currentEmotion?: string
  currentIntent?: string
  error?: string
}

export interface ConversationState {
  sessionId?: string
  turns: Array<{
    id: string
    speaker: 'user' | 'agent'
    text: string
    timestamp: Date
    emotion?: string
    intent?: string
    confidence?: number
    processingTime?: number
  }>
  metrics: ConversationMetrics
  analytics?: VoiceAnalytics
}

export function useEnterpriseVoice(options: UseEnterpriseVoiceOptions) {
  const { config, autoConnect = false, enableMetricsTracking = true, onError, onMetricsUpdate } = options

  // State
  const [voiceState, setVoiceState] = useState<VoiceState>({
    isInitialized: false,
    isConnected: false,
    isRecording: false,
    isProcessing: false,
    audioLevel: 0
  })

  const [conversationState, setConversationState] = useState<ConversationState>({
    turns: [],
    metrics: {
      responseTimeMs: 0,
      emotionAccuracy: 0,
      intentConfidence: 0,
      conversationFlow: 0,
      leadQualificationScore: 0
    }
  })

  // Refs
  const voiceServiceRef = useRef<EnterpriseVoiceService | null>(null)
  const metricsIntervalRef = useRef<NodeJS.Timeout>()

  // Initialize voice service
  useEffect(() => {
    const initializeVoiceService = async () => {
      try {
        const service = new EnterpriseVoiceService(config)
        voiceServiceRef.current = service

        // Set up event handlers
        service.on('initialized', () => {
          setVoiceState(prev => ({ ...prev, isInitialized: true, error: undefined }))
        })

        service.on('connected', (data: { sessionId: string }) => {
          setVoiceState(prev => ({ ...prev, isConnected: true, error: undefined }))
          setConversationState(prev => ({ ...prev, sessionId: data.sessionId }))
        })

        service.on('disconnected', () => {
          setVoiceState(prev => ({ 
            ...prev, 
            isConnected: false, 
            isRecording: false, 
            isProcessing: false 
          }))
        })

        service.on('recordingStarted', () => {
          setVoiceState(prev => ({ ...prev, isRecording: true }))
        })

        service.on('recordingStopped', () => {
          setVoiceState(prev => ({ ...prev, isRecording: false }))
        })

        service.on('audioLevel', (data: { level: number; isSpeaking: boolean }) => {
          setVoiceState(prev => ({ ...prev, audioLevel: data.level }))
        })

        service.on('transcription', (data: { text: string; confidence: number; timestamp: string }) => {
          const turn = {
            id: `user_${Date.now()}`,
            speaker: 'user' as const,
            text: data.text,
            timestamp: new Date(data.timestamp),
            confidence: data.confidence
          }

          setConversationState(prev => ({
            ...prev,
            turns: [...prev.turns, turn]
          }))

          setVoiceState(prev => ({ ...prev, isProcessing: true }))
        })

        service.on('emotionDetected', (data: any) => {
          setVoiceState(prev => ({ ...prev, currentEmotion: data.emotion }))
          
          if (enableMetricsTracking) {
            setConversationState(prev => ({
              ...prev,
              metrics: { ...prev.metrics, emotionAccuracy: data.confidence }
            }))
          }
        })

        service.on('intentClassified', (data: any) => {
          setVoiceState(prev => ({ ...prev, currentIntent: data.intent }))
          
          if (enableMetricsTracking) {
            setConversationState(prev => ({
              ...prev,
              metrics: { ...prev.metrics, intentConfidence: data.confidence }
            }))
          }
        })

        service.on('responseGenerated', (data: any) => {
          const turn = {
            id: `agent_${Date.now()}`,
            speaker: 'agent' as const,
            text: data.text,
            timestamp: new Date(data.timestamp),
            processingTime: data.processingTime
          }

          setConversationState(prev => ({
            ...prev,
            turns: [...prev.turns, turn],
            metrics: { 
              ...prev.metrics, 
              responseTimeMs: data.processingTime 
            }
          }))

          setVoiceState(prev => ({ ...prev, isProcessing: false }))

          // Call metrics callback
          if (onMetricsUpdate && enableMetricsTracking) {
            onMetricsUpdate(conversationState.metrics)
          }
        })

        service.on('error', (error: any) => {
          const errorMessage = error.message || 'An error occurred'
          setVoiceState(prev => ({ ...prev, error: errorMessage, isProcessing: false }))
          
          if (onError) {
            onError(error)
          }
        })

        // Initialize the service
        await service.initialize()

        // Auto-connect if requested
        if (autoConnect) {
          await service.connect()
        }

      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to initialize voice service'
        setVoiceState(prev => ({ ...prev, error: errorMessage }))
        
        if (onError) {
          onError(error)
        }
      }
    }

    initializeVoiceService()

    // Cleanup
    return () => {
      if (voiceServiceRef.current) {
        voiceServiceRef.current.disconnect()
      }
      if (metricsIntervalRef.current) {
        clearInterval(metricsIntervalRef.current)
      }
    }
  }, [config, autoConnect, enableMetricsTracking, onError, onMetricsUpdate])

  // Start metrics tracking
  useEffect(() => {
    if (enableMetricsTracking && voiceState.isConnected) {
      metricsIntervalRef.current = setInterval(() => {
        if (voiceServiceRef.current) {
          const metrics = voiceServiceRef.current.getConversationMetrics()
          setConversationState(prev => ({ ...prev, metrics }))
          
          if (onMetricsUpdate) {
            onMetricsUpdate(metrics)
          }
        }
      }, 1000) // Update metrics every second

      return () => {
        if (metricsIntervalRef.current) {
          clearInterval(metricsIntervalRef.current)
        }
      }
    }
  }, [enableMetricsTracking, voiceState.isConnected, onMetricsUpdate])

  // Actions
  const connect = useCallback(async () => {
    if (!voiceServiceRef.current || voiceState.isConnected) return
    
    try {
      await voiceServiceRef.current.connect()
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to connect'
      setVoiceState(prev => ({ ...prev, error: errorMessage }))
      
      if (onError) {
        onError(error)
      }
    }
  }, [voiceState.isConnected, onError])

  const disconnect = useCallback(() => {
    if (voiceServiceRef.current) {
      voiceServiceRef.current.disconnect()
    }
  }, [])

  const startRecording = useCallback(async () => {
    if (!voiceServiceRef.current || !voiceState.isConnected || voiceState.isRecording) return

    try {
      await voiceServiceRef.current.startRecording()
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to start recording'
      setVoiceState(prev => ({ ...prev, error: errorMessage }))
      
      if (onError) {
        onError(error)
      }
    }
  }, [voiceState.isConnected, voiceState.isRecording, onError])

  const stopRecording = useCallback(() => {
    if (voiceServiceRef.current && voiceState.isRecording) {
      voiceServiceRef.current.stopRecording()
    }
  }, [voiceState.isRecording])

  const toggleRecording = useCallback(async () => {
    if (voiceState.isRecording) {
      stopRecording()
    } else {
      await startRecording()
    }
  }, [voiceState.isRecording, startRecording, stopRecording])

  const clearConversation = useCallback(() => {
    setConversationState({
      turns: [],
      metrics: {
        responseTimeMs: 0,
        emotionAccuracy: 0,
        intentConfidence: 0,
        conversationFlow: 0,
        leadQualificationScore: 0
      }
    })
    
    setVoiceState(prev => ({ 
      ...prev, 
      currentEmotion: undefined, 
      currentIntent: undefined,
      error: undefined 
    }))
  }, [])

  const loadDemoScenario = useCallback(async (scenarioType: string) => {
    if (!voiceServiceRef.current) return null

    try {
      const scenario = await voiceServiceRef.current.loadDemoScenario(scenarioType)
      clearConversation()
      return scenario
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load demo scenario'
      setVoiceState(prev => ({ ...prev, error: errorMessage }))
      
      if (onError) {
        onError(error)
      }
      return null
    }
  }, [clearConversation, onError])

  const getAnalytics = useCallback(async () => {
    if (!voiceServiceRef.current) return null

    try {
      const analytics = await voiceServiceRef.current.getConversationAnalytics()
      setConversationState(prev => ({ ...prev, analytics }))
      return analytics
    } catch (error) {
      if (onError) {
        onError(error)
      }
      return null
    }
  }, [onError])

  const clearError = useCallback(() => {
    setVoiceState(prev => ({ ...prev, error: undefined }))
  }, [])

  // Performance utilities
  const getPerformanceScore = useCallback(() => {
    const { metrics } = conversationState
    
    // Calculate composite performance score (0-100)
    let score = 100
    
    // Response time penalty
    if (metrics.responseTimeMs > 2000) {
      score -= Math.min(30, (metrics.responseTimeMs - 2000) / 100)
    }
    
    // Accuracy bonuses
    score += (metrics.emotionAccuracy - 0.5) * 20
    score += (metrics.intentConfidence - 0.5) * 20
    
    return Math.max(0, Math.min(100, score))
  }, [conversationState.metrics])

  const isPerformingWell = useCallback(() => {
    const score = getPerformanceScore()
    return score >= 80 && conversationState.metrics.responseTimeMs < 2000
  }, [getPerformanceScore, conversationState.metrics.responseTimeMs])

  return {
    // State
    voiceState,
    conversationState,
    
    // Actions
    connect,
    disconnect,
    startRecording,
    stopRecording,
    toggleRecording,
    clearConversation,
    loadDemoScenario,
    getAnalytics,
    clearError,
    
    // Utilities
    getPerformanceScore,
    isPerformingWell,
    
    // Service reference (for advanced usage)
    voiceService: voiceServiceRef.current
  }
}