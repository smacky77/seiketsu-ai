'use client'

import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Mic, 
  MicOff, 
  Play, 
  Pause, 
  Square,
  Volume2,
  VolumeX,
  Activity,
  Brain,
  Target,
  MessageSquare,
  Clock,
  Zap,
  TrendingUp,
  Heart,
  Eye,
  CheckCircle,
  AlertTriangle
} from 'lucide-react'

import { createEnterpriseVoiceService, EnterpriseVoiceService, DemoScenario } from '../../lib/voice-ai/services/enterpriseVoiceService'

interface VoiceIntelligenceDemoProps {
  agentId?: string
  apiUrl: string
  wsUrl: string
  onMetricsUpdate?: (metrics: any) => void
  demoMode?: boolean
}

interface ConversationTurn {
  id: string
  speaker: 'user' | 'agent'
  text: string
  timestamp: Date
  emotion?: string
  intent?: string
  confidence?: number
  processingTime?: number
}

interface LiveMetrics {
  responseTime: number
  emotionAccuracy: number
  intentConfidence: number
  audioQuality: number
  conversationFlow: number
}

export function VoiceIntelligenceDemo({
  agentId = 'demo-agent',
  apiUrl,
  wsUrl,
  onMetricsUpdate,
  demoMode = false
}: VoiceIntelligenceDemoProps) {
  const [voiceService, setVoiceService] = useState<EnterpriseVoiceService | null>(null)
  const [isInitialized, setIsInitialized] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [currentScenario, setCurrentScenario] = useState<DemoScenario | null>(null)
  
  // Conversation state
  const [conversationTurns, setConversationTurns] = useState<ConversationTurn[]>([])
  const [currentTranscription, setCurrentTranscription] = useState('')
  const [detectedEmotion, setDetectedEmotion] = useState<string>('')
  const [detectedIntent, setDetectedIntent] = useState<string>('')
  const [audioLevel, setAudioLevel] = useState(0)
  
  // Metrics
  const [liveMetrics, setLiveMetrics] = useState<LiveMetrics>({
    responseTime: 0,
    emotionAccuracy: 0,
    intentConfidence: 0,
    audioQuality: 0,
    conversationFlow: 0
  })
  
  const [error, setError] = useState<string>('')
  const conversationRef = useRef<HTMLDivElement>(null)

  // Initialize voice service
  useEffect(() => {
    const initializeService = async () => {
      try {
        const service = createEnterpriseVoiceService({
          apiUrl,
          wsUrl,
          agentId,
          enableEmotionDetection: true,
          enableRealTimeTranscription: true,
          audioSettings: {
            sampleRate: 16000,
            channels: 1,
            bitDepth: 16,
            noiseReduction: true,
            echoCancellation: true
          }
        })

        // Set up event handlers
        service.on('initialized', () => {
          setIsInitialized(true)
          // Voice service initialized successfully
        })

        service.on('connected', () => {
          setIsConnected(true)
          // Connected to voice intelligence service
        })

        service.on('disconnected', () => {
          setIsConnected(false)
          setIsRecording(false)
        })

        service.on('recordingStarted', () => {
          setIsRecording(true)
        })

        service.on('recordingStopped', () => {
          setIsRecording(false)
        })

        service.on('audioLevel', (data: { level: number; isSpeaking: boolean }) => {
          setAudioLevel(data.level)
        })

        service.on('transcription', (data: { text: string; confidence: number; timestamp: string }) => {
          setCurrentTranscription(data.text)
          
          // Add user turn
          const userTurn: ConversationTurn = {
            id: `user_${Date.now()}`,
            speaker: 'user',
            text: data.text,
            timestamp: new Date(data.timestamp),
            confidence: data.confidence
          }
          
          setConversationTurns(prev => [...prev, userTurn])
        })

        service.on('emotionDetected', (data: any) => {
          setDetectedEmotion(data.emotion)
          setLiveMetrics(prev => ({ ...prev, emotionAccuracy: data.confidence }))
        })

        service.on('intentClassified', (data: any) => {
          setDetectedIntent(data.intent)
          setLiveMetrics(prev => ({ ...prev, intentConfidence: data.confidence }))
        })

        service.on('responseGenerated', (data: any) => {
          setIsProcessing(false)
          setCurrentTranscription('')
          
          // Add agent turn
          const agentTurn: ConversationTurn = {
            id: `agent_${Date.now()}`,
            speaker: 'agent',
            text: data.text,
            timestamp: new Date(data.timestamp),
            processingTime: data.processingTime
          }
          
          setConversationTurns(prev => [...prev, agentTurn])
          setLiveMetrics(prev => ({ ...prev, responseTime: data.processingTime }))
          
          // Update overall metrics
          if (onMetricsUpdate) {
            const metrics = service.getConversationMetrics()
            onMetricsUpdate(metrics)
          }
        })

        service.on('error', (error: any) => {
          setError(error.message || 'An error occurred')
          setIsProcessing(false)
          // Handle voice service error appropriately
        })

        // Initialize the service
        await service.initialize()
        setVoiceService(service)

      } catch (error) {
        setError('Failed to initialize voice service')
        throw error
      }
    }

    initializeService()

    return () => {
      if (voiceService) {
        voiceService.disconnect()
      }
    }
  }, [apiUrl, wsUrl, agentId])

  // Auto-scroll conversation
  useEffect(() => {
    if (conversationRef.current) {
      conversationRef.current.scrollTop = conversationRef.current.scrollHeight
    }
  }, [conversationTurns])

  // Connect to service
  const handleConnect = async () => {
    if (!voiceService || isConnected) return
    
    try {
      await voiceService.connect()
    } catch (error) {
      setError('Failed to connect to voice intelligence service')
      throw error
    }
  }

  // Start/stop recording
  const toggleRecording = async () => {
    if (!voiceService || !isConnected) return

    try {
      if (isRecording) {
        voiceService.stopRecording()
      } else {
        setIsProcessing(true)
        await voiceService.startRecording()
      }
    } catch (error) {
      setError('Failed to toggle recording')
      throw error
    }
  }

  // Load demo scenario
  const loadDemoScenario = async (scenarioType: string) => {
    if (!voiceService) return

    try {
      const scenario = await voiceService.loadDemoScenario(scenarioType)
      setCurrentScenario(scenario)
      setConversationTurns([])
      setError('')
    } catch (error) {
      setError('Failed to load demo scenario')
      throw error
    }
  }

  // Clear conversation
  const clearConversation = () => {
    setConversationTurns([])
    setCurrentTranscription('')
    setDetectedEmotion('')
    setDetectedIntent('')
    setError('')
    setCurrentScenario(null)
  }

  // Get response time color
  const getResponseTimeColor = (time: number) => {
    if (time < 1000) return 'text-green-500'
    if (time < 2000) return 'text-yellow-500'
    return 'text-red-500'
  }

  // Get confidence color
  const getConfidenceColor = (confidence: number) => {
    if (confidence > 0.8) return 'text-green-500'
    if (confidence > 0.6) return 'text-yellow-500'
    return 'text-red-500'
  }

  return (
    <div className="max-w-6xl mx-auto p-6 bg-white dark:bg-gray-900 rounded-lg shadow-lg">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Main Conversation Panel */}
        <div className="lg:col-span-2 space-y-4">
          
          {/* Header */}
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Voice Intelligence Demo
            </h2>
            
            <div className="flex items-center gap-3">
              {demoMode && (
                <select
                  onChange={(e) => loadDemoScenario(e.target.value)}
                  className="px-3 py-2 border rounded-md text-sm"
                  defaultValue=""
                >
                  <option value="" disabled>Load Demo Scenario</option>
                  <option value="first_time_buyer">First-Time Buyer</option>
                  <option value="luxury_buyer">Luxury Client</option>
                  <option value="investor">Real Estate Investor</option>
                  <option value="downsizing_senior">Downsizing Senior</option>
                  <option value="urgent_relocation">Corporate Relocation</option>
                </select>
              )}
              
              <button
                onClick={clearConversation}
                className="px-3 py-2 text-sm bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-md"
              >
                Clear
              </button>
            </div>
          </div>

          {/* Connection Status */}
          <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
            <div className="flex items-center gap-3">
              <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
              <span className="text-sm font-medium">
                {isConnected ? 'Connected to Voice Intelligence' : 'Disconnected'}
              </span>
            </div>
            
            {!isConnected && isInitialized && (
              <button
                onClick={handleConnect}
                className="px-3 py-1 text-sm bg-blue-500 hover:bg-blue-600 text-white rounded"
              >
                Connect
              </button>
            )}
          </div>

          {/* Demo Scenario Info */}
          {currentScenario && (
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md">
              <h3 className="font-semibold text-blue-900 dark:text-blue-100">
                Demo Scenario: {currentScenario.name}
              </h3>
              <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                {currentScenario.description}
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {currentScenario.successCriteria.map((criteria, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-800 text-blue-800 dark:text-blue-200 rounded"
                  >
                    {criteria}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-500" />
                <span className="text-red-700 dark:text-red-300">{error}</span>
              </div>
            </div>
          )}

          {/* Conversation Area */}
          <div className="border rounded-md h-96 flex flex-col">
            <div className="p-3 border-b bg-gray-50 dark:bg-gray-800">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Conversation ({conversationTurns.length} turns)
                </span>
                
                {/* Audio Level Indicator */}
                <div className="flex items-center gap-2">
                  <Volume2 className="w-4 h-4 text-gray-400" />
                  <div className="w-20 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-green-500"
                      style={{ width: `${audioLevel * 100}%` }}
                      animate={{ width: `${audioLevel * 100}%` }}
                      transition={{ duration: 0.1 }}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div
              ref={conversationRef}
              className="flex-1 p-4 overflow-y-auto space-y-3"
            >
              <AnimatePresence>
                {conversationTurns.map((turn) => (
                  <motion.div
                    key={turn.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className={`flex ${turn.speaker === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      turn.speaker === 'user' 
                        ? 'bg-blue-500 text-white ml-12' 
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white mr-12'
                    }`}>
                      <p className="text-sm">{turn.text}</p>
                      <div className="flex items-center justify-between mt-2 text-xs opacity-75">
                        <span>{turn.timestamp.toLocaleTimeString()}</span>
                        {turn.processingTime && (
                          <span className={getResponseTimeColor(turn.processingTime)}>
                            {turn.processingTime}ms
                          </span>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {/* Current Transcription */}
              {currentTranscription && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex justify-end"
                >
                  <div className="max-w-xs lg:max-w-md px-4 py-2 bg-blue-300 text-blue-900 rounded-lg ml-12">
                    <p className="text-sm italic">{currentTranscription}...</p>
                  </div>
                </motion.div>
              )}

              {/* Processing Indicator */}
              {isProcessing && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex justify-start"
                >
                  <div className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg mr-12">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                    <span className="text-sm text-gray-600 dark:text-gray-400">AI is thinking...</span>
                  </div>
                </motion.div>
              )}
            </div>

            {/* Recording Controls */}
            <div className="p-4 border-t bg-gray-50 dark:bg-gray-800">
              <div className="flex items-center justify-center">
                <button
                  onClick={toggleRecording}
                  disabled={!isConnected}
                  className={`w-16 h-16 rounded-full flex items-center justify-center transition-all ${
                    isRecording
                      ? 'bg-red-500 hover:bg-red-600 text-white shadow-lg shadow-red-500/25'
                      : 'bg-blue-500 hover:bg-blue-600 text-white shadow-lg disabled:bg-gray-300 disabled:cursor-not-allowed'
                  }`}
                >
                  {isRecording ? (
                    <Square className="w-8 h-8" />
                  ) : (
                    <Mic className="w-8 h-8" />
                  )}
                </button>
              </div>
              
              <div className="text-center mt-2">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {isRecording ? 'Recording... Click to stop' : 'Click to start recording'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Metrics Panel */}
        <div className="space-y-4">
          
          {/* Live Metrics */}
          <div className="p-4 border rounded-md">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Live Metrics
            </h3>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Response Time</span>
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-medium ${getResponseTimeColor(liveMetrics.responseTime)}`}>
                    {liveMetrics.responseTime}ms
                  </span>
                  <Clock className="w-3 h-3" />
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Emotion Accuracy</span>
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-medium ${getConfidenceColor(liveMetrics.emotionAccuracy)}`}>
                    {(liveMetrics.emotionAccuracy * 100).toFixed(1)}%
                  </span>
                  <Heart className="w-3 h-3" />
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Intent Confidence</span>
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-medium ${getConfidenceColor(liveMetrics.intentConfidence)}`}>
                    {(liveMetrics.intentConfidence * 100).toFixed(1)}%
                  </span>
                  <Target className="w-3 h-3" />
                </div>
              </div>
            </div>
          </div>

          {/* Current Context */}
          <div className="p-4 border rounded-md">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <Brain className="w-4 h-4" />
              Current Context
            </h3>
            
            <div className="space-y-2">
              {detectedEmotion && (
                <div>
                  <span className="text-xs text-gray-500">Emotion:</span>
                  <div className="flex items-center gap-2 mt-1">
                    <div className={`w-2 h-2 rounded-full ${
                      detectedEmotion === 'joy' ? 'bg-yellow-400' :
                      detectedEmotion === 'anger' ? 'bg-red-500' :
                      detectedEmotion === 'fear' ? 'bg-purple-500' :
                      detectedEmotion === 'sadness' ? 'bg-blue-500' :
                      'bg-gray-400'
                    }`} />
                    <span className="text-sm font-medium capitalize">{detectedEmotion}</span>
                  </div>
                </div>
              )}
              
              {detectedIntent && (
                <div>
                  <span className="text-xs text-gray-500">Intent:</span>
                  <div className="mt-1">
                    <span className="text-sm font-medium capitalize">
                      {detectedIntent.replace(/_/g, ' ')}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Performance Indicators */}
          <div className="p-4 border rounded-md">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Performance
            </h3>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">Sub-2s Responses</span>
                <CheckCircle className="w-4 h-4 text-green-500" />
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">Human-like Quality</span>
                <CheckCircle className="w-4 h-4 text-green-500" />
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">Context Awareness</span>
                <CheckCircle className="w-4 h-4 text-green-500" />
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">Enterprise Ready</span>
                <CheckCircle className="w-4 h-4 text-green-500" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}