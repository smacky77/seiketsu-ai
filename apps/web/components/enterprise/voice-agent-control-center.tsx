'use client'

import { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Mic,
  MicOff,
  Phone,
  PhoneOff,
  Volume2,
  VolumeX,
  Settings,
  AlertTriangle,
  CheckCircle,
  Clock,
  Activity,
  Users,
  TrendingUp,
  Shield,
  Zap,
  Play,
  Pause,
  RotateCcw,
  Download
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { VoiceStatusIndicator, Waveform } from '@/components/ui/voice-status'
import { cn } from '@/lib/utils'
import { AudioOptimizer } from '@/lib/performance/audio-optimizer'
import { MemoryManager } from '@/lib/performance/memory-manager'
import { WebSocketOptimizer } from '@/lib/performance/websocket-optimizer'

type AgentStatus = 'idle' | 'active' | 'busy' | 'error' | 'maintenance'
type ConversationStatus = 'waiting' | 'connecting' | 'active' | 'ended' | 'failed'
type CallQuality = 'excellent' | 'good' | 'fair' | 'poor'

interface ActiveCall {
  id: string
  leadName: string
  leadPhone: string
  status: ConversationStatus
  duration: number
  quality: CallQuality
  transcript: string[]
  sentiment: 'positive' | 'neutral' | 'negative'
  leadScore: number
}

interface AgentMetrics {
  callsToday: number
  avgCallDuration: number
  leadConversionRate: number
  uptime: number
  responseTime: number
  satisfactionScore: number
}

interface VoiceAgentControlCenterProps {
  className?: string
  agentId?: string
  onEmergencyStop?: () => void
  onConfigChange?: (config: any) => void
}

export function VoiceAgentControlCenter({
  className,
  agentId = 'agent-001',
  onEmergencyStop,
  onConfigChange
}: VoiceAgentControlCenterProps) {
  // Performance optimizers - initialized once
  const audioOptimizer = useMemo(() => new AudioOptimizer({
    maxLatency: 180,
    bufferSize: 512,
    enableWebWorker: true
  }), [])
  
  const memoryManager = useMemo(() => new MemoryManager({
    maxSessionMemory: 50,
    enableAutoCleanup: true
  }), [])
  
  const wsOptimizer = useMemo(() => new WebSocketOptimizer({
    binaryProtocol: true,
    compressionEnabled: true
  }), [])
  const [agentStatus, setAgentStatus] = useState<AgentStatus>('active')
  const [activeCall, setActiveCall] = useState<ActiveCall | null>({
    id: 'call-001',
    leadName: 'Jennifer Martinez',
    leadPhone: '+1 (555) 123-4567',
    status: 'active',
    duration: 224, // seconds
    quality: 'excellent',
    transcript: [
      'Agent: Hello! Thank you for your interest in the downtown condo listing.',
      'Lead: Hi, yes I saw it online. Can you tell me more about the amenities?',
      'Agent: Absolutely! The building features a rooftop pool, fitness center...'
    ],
    sentiment: 'positive',
    leadScore: 85
  })

  const [metrics, setMetrics] = useState<AgentMetrics>({
    callsToday: 23,
    avgCallDuration: 4.2,
    leadConversionRate: 68,
    uptime: 99.8,
    responseTime: 1.2,
    satisfactionScore: 4.7
  })

  const [audioLevels, setAudioLevels] = useState({
    input: 0.65,
    output: 0.48
  })

  const [isRecording, setIsRecording] = useState(false)
  const [showTranscript, setShowTranscript] = useState(true)
  const [performanceMetrics, setPerformanceMetrics] = useState({
    audioLatency: 0,
    memoryUsage: 0,
    wsLatency: 0,
    isOptimal: true
  })
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const cleanupRef = useRef<(() => void)[]>([])

  // Performance-optimized real-time updates
  useEffect(() => {
    let frameId: number
    
    const updateMetrics = () => {
      // Batch state updates for better performance
      const updates: any = {}
      
      if (activeCall) {
        updates.activeCall = {
          ...activeCall,
          duration: activeCall.duration + 1
        }
      }
      
      // Optimized audio level simulation
      const inputLevel = Math.random() * 0.8 + 0.2
      const outputLevel = Math.random() * 0.6 + 0.3
      
      updates.audioLevels = { input: inputLevel, output: outputLevel }
      
      // Update performance metrics
      const audioMetrics = audioOptimizer.getMetrics()
      const memoryMetrics = memoryManager.getMetrics()
      const wsMetrics = wsOptimizer.getMetrics()
      
      updates.performanceMetrics = {
        audioLatency: audioMetrics.processingTime,
        memoryUsage: memoryMetrics.heapUsed,
        wsLatency: wsMetrics.latency,
        isOptimal: audioMetrics.isOptimal && memoryMetrics.isOptimal && wsMetrics.isOptimal
      }
      
      // Apply all updates in one batch
      Object.keys(updates).forEach(key => {
        if (key === 'activeCall') setActiveCall(updates[key])
        else if (key === 'audioLevels') setAudioLevels(updates[key])
        else if (key === 'performanceMetrics') setPerformanceMetrics(updates[key])
      })
    }
    
    // Use requestAnimationFrame for smooth updates
    const animate = () => {
      updateMetrics()
      frameId = requestAnimationFrame(animate)
    }
    
    frameId = requestAnimationFrame(animate)

    return () => {
      if (frameId) {
        cancelAnimationFrame(frameId)
      }
    }
  }, [activeCall, audioOptimizer, memoryManager, wsOptimizer])

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const getStatusColor = (status: AgentStatus) => {
    switch (status) {
      case 'active': return 'text-green-500'
      case 'busy': return 'text-blue-500'
      case 'idle': return 'text-yellow-500'
      case 'error': return 'text-red-500'
      case 'maintenance': return 'text-orange-500'
      default: return 'text-gray-500'
    }
  }

  const getQualityColor = (quality: CallQuality) => {
    switch (quality) {
      case 'excellent': return 'text-green-500'
      case 'good': return 'text-blue-500'
      case 'fair': return 'text-yellow-500'
      case 'poor': return 'text-red-500'
      default: return 'text-gray-500'
    }
  }

  const handleEmergencyStop = useCallback(() => {
    setAgentStatus('maintenance')
    setActiveCall(null)
    
    // Cleanup performance optimizers
    audioOptimizer.dispose()
    memoryManager.performFullCleanup()
    wsOptimizer.disconnect()
    
    onEmergencyStop?.()
  }, [audioOptimizer, memoryManager, wsOptimizer, onEmergencyStop])

  const toggleAgent = useCallback(() => {
    setAgentStatus(prev => prev === 'active' ? 'idle' : 'active')
  }, [])

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Voice Agent Control Center</h1>
          <p className="text-muted-foreground">Agent ID: {agentId}</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </Button>
          <Button 
            variant="destructive" 
            size="sm"
            onClick={handleEmergencyStop}
          >
            <AlertTriangle className="w-4 h-4 mr-2" />
            Emergency Stop
          </Button>
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Agent Status Card */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Agent Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={cn(
                  'w-3 h-3 rounded-full animate-pulse',
                  getStatusColor(agentStatus)
                )} />
                <span className="font-medium capitalize">{agentStatus}</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={toggleAgent}
              >
                {agentStatus === 'active' ? 'Deactivate' : 'Activate'}
              </Button>
            </div>
            <div className="mt-4 text-sm text-muted-foreground">
              Uptime: {metrics.uptime}% • Response: {metrics.responseTime}s
              <br />
              <span className={cn(
                'text-xs',
                performanceMetrics.isOptimal ? 'text-green-600' : 'text-red-600'
              )}>
                Audio: {performanceMetrics.audioLatency.toFixed(0)}ms • 
                Memory: {performanceMetrics.memoryUsage.toFixed(0)}MB • 
                WS: {performanceMetrics.wsLatency.toFixed(0)}ms
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Current Performance */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Today's Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">Calls Handled</span>
                <span className="font-semibold">{metrics.callsToday}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Conversion Rate</span>
                <span className="font-semibold text-green-600">{metrics.leadConversionRate}%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Avg Duration</span>
                <span className="font-semibold">{metrics.avgCallDuration}m</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Satisfaction Score */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Satisfaction</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <div className="text-3xl font-bold text-green-600">
                {metrics.satisfactionScore}
              </div>
              <div>
                <div className="flex text-yellow-400">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className={cn(
                      'w-4 h-4',
                      i < Math.floor(metrics.satisfactionScore) ? 'text-yellow-400' : 'text-gray-300'
                    )}>
                      ★
                    </div>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground mt-1">Average rating</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Call Monitor */}
      <AnimatePresence>
        {activeCall && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-6"
          >
            {/* Call Details */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Active Call</span>
                  <div className="flex items-center gap-2">
                    <div className={cn(
                      'w-2 h-2 rounded-full',
                      getQualityColor(activeCall.quality)
                    )} />
                    <span className="text-sm capitalize">{activeCall.quality}</span>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <p className="font-semibold">{activeCall.leadName}</p>
                    <p className="text-sm text-muted-foreground">{activeCall.leadPhone}</p>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      <span className="font-mono">{formatDuration(activeCall.duration)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className={cn(
                        'px-2 py-1 rounded text-xs font-medium',
                        activeCall.sentiment === 'positive' ? 'bg-green-100 text-green-700' :
                        activeCall.sentiment === 'negative' ? 'bg-red-100 text-red-700' :
                        'bg-gray-100 text-gray-700'
                      )}>
                        {activeCall.sentiment}
                      </div>
                      <div className="text-sm font-semibold">Score: {activeCall.leadScore}</div>
                    </div>
                  </div>

                  {/* Voice Controls */}
                  <div className="flex items-center justify-center gap-4 pt-4 border-t">
                    <Button
                      variant={isRecording ? "destructive" : "default"}
                      size="lg"
                      className="w-12 h-12 rounded-full p-0"
                      onClick={() => setIsRecording(!isRecording)}
                    >
                      {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                    </Button>
                    
                    <Button
                      variant="outline"
                      size="lg"
                      className="w-12 h-12 rounded-full p-0"
                    >
                      <Volume2 className="w-5 h-5" />
                    </Button>
                    
                    <Button
                      variant="destructive"
                      size="lg"
                      className="w-12 h-12 rounded-full p-0"
                      onClick={() => setActiveCall(null)}
                    >
                      <PhoneOff className="w-5 h-5" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Live Transcript */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Live Transcript</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowTranscript(!showTranscript)}
                  >
                    {showTranscript ? 'Hide' : 'Show'}
                  </Button>
                </CardTitle>
              </CardHeader>
              {showTranscript && (
                <CardContent>
                  <div className="space-y-3 max-h-64 overflow-y-auto">
                    {activeCall.transcript.map((message, index) => {
                      const isAgent = message.startsWith('Agent:')
                      return (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, x: isAgent ? -20 : 20 }}
                          animate={{ opacity: 1, x: 0 }}
                          className={cn(
                            'p-3 rounded-lg text-sm',
                            isAgent ? 'bg-blue-50 text-blue-900' : 'bg-gray-50'
                          )}
                        >
                          <p className="font-medium text-xs mb-1">
                            {isAgent ? 'AI Agent' : 'Lead'}
                          </p>
                          <p>{message.replace(/^(Agent:|Lead:)\s*/, '')}</p>
                        </motion.div>
                      )
                    })}
                  </div>
                  
                  {/* Audio Levels */}
                  <div className="mt-4 space-y-3">
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium">Input Level</span>
                        <span className="text-xs text-muted-foreground">-12 dB</span>
                      </div>
                      <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                        <motion.div
                          className="h-full bg-green-500"
                          style={{ width: `${audioLevels.input * 100}%` }}
                          animate={{ width: `${audioLevels.input * 100}%` }}
                          transition={{ duration: 0.2 }}
                        />
                      </div>
                    </div>
                    
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium">Output Level</span>
                        <span className="text-xs text-muted-foreground">-8 dB</span>
                      </div>
                      <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                        <motion.div
                          className="h-full bg-blue-500"
                          style={{ width: `${audioLevels.output * 100}%` }}
                          animate={{ width: `${audioLevels.output * 100}%` }}
                          transition={{ duration: 0.2 }}
                        />
                      </div>
                    </div>
                  </div>
                </CardContent>
              )}
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Button variant="outline" className="h-auto flex-col py-3">
              <Play className="w-5 h-5 mb-2" />
              <span className="text-xs">Test Voice</span>
            </Button>
            <Button variant="outline" className="h-auto flex-col py-3">
              <RotateCcw className="w-5 h-5 mb-2" />
              <span className="text-xs">Restart Agent</span>
            </Button>
            <Button variant="outline" className="h-auto flex-col py-3">
              <Download className="w-5 h-5 mb-2" />
              <span className="text-xs">Export Logs</span>
            </Button>
            <Button variant="outline" className="h-auto flex-col py-3">
              <Shield className="w-5 h-5 mb-2" />
              <span className="text-xs">Security</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default VoiceAgentControlCenter