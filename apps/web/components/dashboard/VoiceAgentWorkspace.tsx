'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Mic, 
  MicOff, 
  Phone, 
  PhoneOff, 
  Volume2, 
  VolumeX,
  Play,
  Pause,
  Settings,
  AlertCircle,
  CheckCircle,
  Clock,
  Brain,
  Heart,
  Target,
  Zap,
  TrendingUp,
  Activity
} from 'lucide-react'

import { useEnterpriseVoice } from '../../lib/voice-ai/hooks/useEnterpriseVoice'

export function VoiceAgentWorkspace() {
  const [currentLead, setCurrentLead] = useState<string | null>('Lead: Jennifer Martinez - Property Inquiry')
  const [demoMode, setDemoMode] = useState(false)

  // Enterprise voice configuration
  const voiceConfig = {
    apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
    wsUrl: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
    agentId: 'enterprise-workspace-agent',
    enableEmotionDetection: true,
    enableRealTimeTranscription: true,
    audioSettings: {
      sampleRate: 16000,
      channels: 1,
      bitDepth: 16,
      noiseReduction: true,
      echoCancellation: true
    }
  }

  // Use enterprise voice hook
  const {
    voiceState,
    conversationState,
    connect,
    disconnect,
    toggleRecording,
    clearConversation,
    loadDemoScenario,
    getPerformanceScore,
    isPerformingWell
  } = useEnterpriseVoice({
    config: voiceConfig,
    autoConnect: false,
    enableMetricsTracking: true,
    onError: (error) => {
      // Handle voice errors silently in production
      if (process.env.NODE_ENV === 'development') {
        console.error('Voice error:', error)
      }
    },
    onMetricsUpdate: (metrics) => {
      // Update metrics silently in production
      if (process.env.NODE_ENV === 'development') {
        console.log('Metrics updated:', metrics)
      }
    }
  })

  const performanceScore = getPerformanceScore()

  const handleConnect = async () => {
    if (voiceState.isConnected) {
      disconnect()
    } else {
      await connect()
    }
  }

  const handleDemoScenario = async (scenarioType: string) => {
    const scenario = await loadDemoScenario(scenarioType)
    if (scenario) {
      setCurrentLead(`Demo: ${scenario.name}`)
      setDemoMode(true)
    }
  }

  const getStatusColor = () => {
    if (!voiceState.isConnected) return 'text-red-500'
    if (voiceState.isProcessing) return 'text-blue-500'
    if (voiceState.isRecording) return 'text-green-500'
    return 'text-yellow-500'
  }

  const getStatusText = () => {
    if (!voiceState.isInitialized) return 'Initializing...'
    if (!voiceState.isConnected) return 'Voice Agent Offline'
    if (voiceState.isProcessing) return 'AI Processing...'
    if (voiceState.isRecording) return 'Listening to Prospect'
    return 'Ready - Click to Start'
  }

  const getConnectionQuality = () => {
    if (!voiceState.isConnected) return 'poor'
    if (isPerformingWell()) return 'excellent'
    if (conversationState.metrics.responseTimeMs < 3000) return 'good'
    return 'poor'
  }

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold">Voice Agent Control</h2>
        <button className="p-2 text-muted-foreground hover:text-foreground">
          <Settings className="w-5 h-5" />
        </button>
      </div>

      {/* Main Voice Status */}
      <div className="bg-muted rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${getStatusColor()} animate-pulse`} />
            <span className="font-medium">{getStatusText()}</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <div className={`w-2 h-2 rounded-full ${
              getConnectionQuality() === 'excellent' ? 'bg-green-500' :
              getConnectionQuality() === 'good' ? 'bg-yellow-500' : 'bg-red-500'
            }`} />
            Connection {getConnectionQuality()}
          </div>
        </div>

        {/* Error Display */}
        {voiceState.error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 mb-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-500" />
              <span className="text-red-700 dark:text-red-300 text-sm">{voiceState.error}</span>
            </div>
          </div>
        )}

        {/* Current Conversation */}
        {currentLead && (
          <div className="bg-background rounded-lg p-4 mb-4">
            <p className="text-sm text-muted-foreground mb-1">
              {demoMode ? 'Demo Session' : 'Active Conversation'}
            </p>
            <p className="font-medium">{currentLead}</p>
            <div className="flex items-center gap-4 mt-3 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                <span>{conversationState.sessionId ? 'Active' : 'Ready'}</span>
              </div>
              {conversationState.turns.length > 0 && (
                <div className="flex items-center gap-1">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>{conversationState.turns.length} turns</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Real-time Context */}
        {(voiceState.currentEmotion || voiceState.currentIntent) && (
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 mb-4">
            <div className="flex items-center justify-between text-sm">
              {voiceState.currentEmotion && (
                <div className="flex items-center gap-2">
                  <Heart className="w-3 h-3 text-red-500" />
                  <span className="capitalize">{voiceState.currentEmotion}</span>
                </div>
              )}
              {voiceState.currentIntent && (
                <div className="flex items-center gap-2">
                  <Target className="w-3 h-3 text-blue-500" />
                  <span className="capitalize">{voiceState.currentIntent.replace(/_/g, ' ')}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Voice Controls */}
        <div className="flex items-center justify-center gap-4">
          <button
            onClick={toggleRecording}
            disabled={!voiceState.isConnected}
            className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
              voiceState.isRecording 
                ? 'bg-green-500 text-white shadow-lg shadow-green-500/25' 
                : 'bg-border text-muted-foreground hover:bg-accent disabled:bg-gray-200 disabled:cursor-not-allowed'
            }`}
          >
            {voiceState.isRecording ? <Mic className="w-6 h-6" /> : <MicOff className="w-6 h-6" />}
          </button>

          <button
            onClick={handleConnect}
            disabled={!voiceState.isInitialized}
            className={`w-16 h-16 rounded-full flex items-center justify-center transition-all ${
              voiceState.isConnected 
                ? 'bg-foreground text-background hover:bg-muted-foreground shadow-lg' 
                : 'bg-blue-500 text-white hover:bg-blue-600 shadow-lg disabled:bg-gray-200 disabled:cursor-not-allowed'
            }`}
          >
            {voiceState.isConnected ? <Phone className="w-8 h-8" /> : <PhoneOff className="w-8 h-8" />}
          </button>

          <button 
            onClick={() => setDemoMode(!demoMode)}
            className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
              demoMode ? 'bg-purple-500 text-white' : 'bg-border text-muted-foreground hover:bg-accent'
            }`}
          >
            <Brain className="w-6 h-6" />
          </button>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="space-y-4">
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Audio Level</span>
            <span className="text-xs text-muted-foreground">
              {voiceState.audioLevel > 0.1 ? 'Speaking' : 'Silent'}
            </span>
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-green-500"
              style={{ width: `${voiceState.audioLevel * 100}%` }}
              animate={{ width: `${voiceState.audioLevel * 100}%` }}
              transition={{ duration: 0.1 }}
            />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Response Time</span>
            <span className={`text-xs font-medium ${
              conversationState.metrics.responseTimeMs < 2000 ? 'text-green-600' : 'text-red-600'
            }`}>
              {conversationState.metrics.responseTimeMs}ms
            </span>
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div 
              className={`h-full ${
                conversationState.metrics.responseTimeMs < 1000 ? 'bg-green-500' :
                conversationState.metrics.responseTimeMs < 2000 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${Math.min(100, (2000 - conversationState.metrics.responseTimeMs) / 2000 * 100)}%` }}
            />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Performance Score</span>
            <span className={`text-xs font-medium ${
              performanceScore >= 90 ? 'text-green-600' :
              performanceScore >= 70 ? 'text-yellow-600' : 'text-red-600'
            }`}>
              {performanceScore.toFixed(0)}%
            </span>
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <motion.div
              className={`h-full ${
                performanceScore >= 90 ? 'bg-green-500' :
                performanceScore >= 70 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${performanceScore}%` }}
              animate={{ width: `${performanceScore}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        </div>
      </div>

      {/* Demo Scenarios */}
      <AnimatePresence>
        {demoMode && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4 space-y-2"
          >
            <h4 className="text-sm font-medium mb-2">Demo Scenarios</h4>
            <div className="grid grid-cols-1 gap-2">
              <button
                onClick={() => handleDemoScenario('first_time_buyer')}
                className="text-xs px-3 py-2 bg-blue-100 hover:bg-blue-200 rounded text-blue-800"
              >
                First-Time Buyer
              </button>
              <button
                onClick={() => handleDemoScenario('luxury_buyer')}
                className="text-xs px-3 py-2 bg-purple-100 hover:bg-purple-200 rounded text-purple-800"
              >
                Luxury Client
              </button>
              <button
                onClick={() => handleDemoScenario('investor')}
                className="text-xs px-3 py-2 bg-green-100 hover:bg-green-200 rounded text-green-800"
              >
                Real Estate Investor
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-3 mt-6">
        <button 
          onClick={clearConversation}
          className="btn btn-secondary text-sm"
          disabled={conversationState.turns.length === 0}
        >
          <Play className="w-4 h-4 mr-2" />
          Clear Chat
        </button>
        <button 
          onClick={() => window.open('/demo/voice-intelligence', '_blank')}
          className="btn btn-secondary text-sm"
        >
          <Activity className="w-4 h-4 mr-2" />
          Full Demo
        </button>
      </div>
    </div>
  )
}

export default VoiceAgentWorkspace