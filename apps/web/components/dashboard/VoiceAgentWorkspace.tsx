'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
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
  Clock
} from 'lucide-react'

interface VoiceStatus {
  isActive: boolean
  isListening: boolean
  isSpeaking: boolean
  connectionQuality: 'excellent' | 'good' | 'poor'
  currentConversation: string | null
}

export function VoiceAgentWorkspace() {
  const [voiceStatus, setVoiceStatus] = useState<VoiceStatus>({
    isActive: true,
    isListening: false,
    isSpeaking: false,
    connectionQuality: 'excellent',
    currentConversation: 'Lead: Jennifer Martinez - Property Inquiry'
  })

  const [audioLevel, setAudioLevel] = useState(0.3)

  const toggleVoiceAgent = () => {
    setVoiceStatus(prev => ({ ...prev, isActive: !prev.isActive }))
  }

  const toggleListening = () => {
    setVoiceStatus(prev => ({ ...prev, isListening: !prev.isListening }))
  }

  const getStatusColor = () => {
    if (!voiceStatus.isActive) return 'text-red-500'
    if (voiceStatus.isSpeaking) return 'text-blue-500'
    if (voiceStatus.isListening) return 'text-green-500'
    return 'text-yellow-500'
  }

  const getStatusText = () => {
    if (!voiceStatus.isActive) return 'Voice Agent Offline'
    if (voiceStatus.isSpeaking) return 'AI Speaking...'
    if (voiceStatus.isListening) return 'Listening to Prospect'
    return 'Ready - Waiting for Call'
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
              voiceStatus.connectionQuality === 'excellent' ? 'bg-green-500' :
              voiceStatus.connectionQuality === 'good' ? 'bg-yellow-500' : 'bg-red-500'
            }`} />
            Connection {voiceStatus.connectionQuality}
          </div>
        </div>

        {/* Current Conversation */}
        {voiceStatus.currentConversation && (
          <div className="bg-background rounded-lg p-4 mb-4">
            <p className="text-sm text-muted-foreground mb-1">Active Conversation</p>
            <p className="font-medium">{voiceStatus.currentConversation}</p>
            <div className="flex items-center gap-4 mt-3 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                <span>00:03:42</span>
              </div>
              <div className="flex items-center gap-1">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>Lead Qualified</span>
              </div>
            </div>
          </div>
        )}

        {/* Voice Controls */}
        <div className="flex items-center justify-center gap-4">
          <button
            onClick={toggleListening}
            className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
              voiceStatus.isListening 
                ? 'bg-green-500 text-white shadow-lg shadow-green-500/25' 
                : 'bg-border text-muted-foreground hover:bg-accent'
            }`}
          >
            {voiceStatus.isListening ? <Mic className="w-6 h-6" /> : <MicOff className="w-6 h-6" />}
          </button>

          <button
            onClick={toggleVoiceAgent}
            className={`w-16 h-16 rounded-full flex items-center justify-center transition-all ${
              voiceStatus.isActive 
                ? 'bg-foreground text-background hover:bg-muted-foreground shadow-lg' 
                : 'bg-red-500 text-white hover:bg-red-600 shadow-lg shadow-red-500/25'
            }`}
          >
            {voiceStatus.isActive ? <Phone className="w-8 h-8" /> : <PhoneOff className="w-8 h-8" />}
          </button>

          <button className="w-12 h-12 rounded-full bg-border text-muted-foreground hover:bg-accent flex items-center justify-center">
            <Volume2 className="w-6 h-6" />
          </button>
        </div>
      </div>

      {/* Audio Levels */}
      <div className="space-y-4">
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Input Level</span>
            <span className="text-xs text-muted-foreground">-12 dB</span>
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-green-500"
              style={{ width: `${audioLevel * 100}%` }}
              animate={{ width: [`${audioLevel * 100}%`, `${(audioLevel + 0.1) * 100}%`, `${audioLevel * 100}%`] }}
              transition={{ duration: 0.5, repeat: Infinity }}
            />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Output Level</span>
            <span className="text-xs text-muted-foreground">-8 dB</span>
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-blue-500"
              style={{ width: '60%' }}
              animate={{ width: ['60%', '70%', '60%'] }}
              transition={{ duration: 0.7, repeat: Infinity }}
            />
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-3 mt-6">
        <button className="btn btn-secondary text-sm">
          <Play className="w-4 h-4 mr-2" />
          Test Voice
        </button>
        <button className="btn btn-secondary text-sm">
          <AlertCircle className="w-4 h-4 mr-2" />
          Emergency Stop
        </button>
      </div>
    </div>
  )
}