'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  MessageSquare,
  Phone,
  PhoneCall,
  Users,
  Clock,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Play,
  Pause,
  Download,
  Share,
  Star,
  AlertCircle,
  CheckCircle,
  Activity,
  Headphones,
  Monitor,
  Settings,
  Filter,
  Search,
  MoreVertical,
  ChevronUp,
  ChevronDown,
  Send,
  Paperclip,
  Smile
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { VoiceStatusIndicator, Waveform } from '@/components/ui/voice-status'
import { cn } from '@/lib/utils'

type CallStatus = 'incoming' | 'active' | 'on-hold' | 'ended' | 'missed'
type AgentStatus = 'available' | 'busy' | 'break' | 'offline'
type CallQuality = 'excellent' | 'good' | 'fair' | 'poor'
type MessageType = 'system' | 'agent' | 'lead' | 'note'

interface ActiveCall {
  id: string
  leadName: string
  leadPhone: string
  agentId: string
  agentName: string
  status: CallStatus
  startTime: Date
  duration: number
  quality: CallQuality
  sentiment: 'positive' | 'neutral' | 'negative'
  transcript: TranscriptEntry[]
  recording: boolean
  notes: string[]
}

interface TranscriptEntry {
  id: string
  timestamp: Date
  speaker: 'agent' | 'lead'
  content: string
  confidence: number
  sentiment?: 'positive' | 'neutral' | 'negative'
}

interface Agent {
  id: string
  name: string
  email: string
  status: AgentStatus
  currentCall?: string
  skillLevel: number
  totalCalls: number
  avgCallDuration: number
  conversionRate: number
  lastActivity: Date
}

interface TeamMessage {
  id: string
  type: MessageType
  author: string
  content: string
  timestamp: Date
  callId?: string
  priority?: 'low' | 'medium' | 'high'
}

interface RealTimeCommunicationHubProps {
  className?: string
  onCallAction?: (action: string, callId: string) => void
  onAgentStatusChange?: (agentId: string, status: AgentStatus) => void
}

// Mock data
const mockActiveCalls: ActiveCall[] = [
  {
    id: 'call-001',
    leadName: 'Jennifer Martinez',
    leadPhone: '+1 (555) 123-4567',
    agentId: 'agent-001',
    agentName: 'AI Agent Alpha',
    status: 'active',
    startTime: new Date(Date.now() - 245000),
    duration: 245,
    quality: 'excellent',
    sentiment: 'positive',
    recording: true,
    notes: ['Lead is very interested in downtown properties', 'Budget confirmed at $500K'],
    transcript: [
      {
        id: 'trans-001',
        timestamp: new Date(Date.now() - 180000),
        speaker: 'agent',
        content: 'Hello Jennifer, thank you for your interest in our downtown condo listing. I understand you\'re looking for a modern unit with amenities?',
        confidence: 0.95
      },
      {
        id: 'trans-002',
        timestamp: new Date(Date.now() - 165000),
        speaker: 'lead',
        content: 'Yes, that\'s right. I\'m particularly interested in units with a gym and rooftop access. What can you tell me about the building features?',
        confidence: 0.92,
        sentiment: 'positive'
      },
      {
        id: 'trans-003',
        timestamp: new Date(Date.now() - 150000),
        speaker: 'agent',
        content: 'Excellent! This building offers a state-of-the-art fitness center, rooftop pool, and panoramic city views. The unit I have in mind is on the 15th floor with floor-to-ceiling windows.',
        confidence: 0.97
      }
    ]
  },
  {
    id: 'call-002',
    leadName: 'Robert Chen',
    leadPhone: '+1 (555) 987-6543',
    agentId: 'agent-002',
    agentName: 'AI Agent Beta',
    status: 'on-hold',
    startTime: new Date(Date.now() - 180000),
    duration: 180,
    quality: 'good',
    sentiment: 'neutral',
    recording: true,
    notes: ['Needs to check with spouse', 'Interested in viewing schedule'],
    transcript: [
      {
        id: 'trans-004',
        timestamp: new Date(Date.now() - 120000),
        speaker: 'agent',
        content: 'I understand you\'d like to discuss this with your spouse. Would you prefer I hold while you consult, or shall we schedule a callback?',
        confidence: 0.93
      },
      {
        id: 'trans-005',
        timestamp: new Date(Date.now() - 110000),
        speaker: 'lead',
        content: 'Could you hold for just a moment? I\'d like to check her availability for a viewing this weekend.',
        confidence: 0.89,
        sentiment: 'neutral'
      }
    ]
  }
]

const mockAgents: Agent[] = [
  {
    id: 'agent-001',
    name: 'AI Agent Alpha',
    email: 'alpha@seiketsu.ai',
    status: 'busy',
    currentCall: 'call-001',
    skillLevel: 9.2,
    totalCalls: 1247,
    avgCallDuration: 4.8,
    conversionRate: 73,
    lastActivity: new Date()
  },
  {
    id: 'agent-002',
    name: 'AI Agent Beta',
    email: 'beta@seiketsu.ai',
    status: 'busy',
    currentCall: 'call-002',
    skillLevel: 8.7,
    totalCalls: 892,
    avgCallDuration: 5.2,
    conversionRate: 68,
    lastActivity: new Date()
  },
  {
    id: 'agent-003',
    name: 'AI Agent Gamma',
    email: 'gamma@seiketsu.ai',
    status: 'available',
    skillLevel: 8.9,
    totalCalls: 1056,
    avgCallDuration: 4.3,
    conversionRate: 71,
    lastActivity: new Date(Date.now() - 300000)
  }
]

const mockTeamMessages: TeamMessage[] = [
  {
    id: 'msg-001',
    type: 'system',
    author: 'System',
    content: 'New lead Jennifer Martinez assigned to AI Agent Alpha',
    timestamp: new Date(Date.now() - 245000),
    callId: 'call-001'
  },
  {
    id: 'msg-002',
    type: 'note',
    author: 'Supervisor',
    content: 'Great conversation flow on the downtown condo call. Lead seems highly qualified.',
    timestamp: new Date(Date.now() - 120000),
    callId: 'call-001',
    priority: 'medium'
  },
  {
    id: 'msg-003',
    type: 'system',
    author: 'System',
    content: 'Call quality degraded to "fair" on call with Robert Chen',
    timestamp: new Date(Date.now() - 60000),
    callId: 'call-002',
    priority: 'high'
  }
]

export function RealTimeCommunicationHub({
  className,
  onCallAction,
  onAgentStatusChange
}: RealTimeCommunicationHubProps) {
  const [activeCalls, setActiveCalls] = useState<ActiveCall[]>(mockActiveCalls)
  const [agents, setAgents] = useState<Agent[]>(mockAgents)
  const [teamMessages, setTeamMessages] = useState<TeamMessage[]>(mockTeamMessages)
  const [selectedCall, setSelectedCall] = useState<ActiveCall | null>(activeCalls[0])
  const [expandedTranscript, setExpandedTranscript] = useState(true)
  const [newMessage, setNewMessage] = useState('')
  const [messageFilter, setMessageFilter] = useState<MessageType[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [teamMessages])

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveCalls(prev => prev.map(call => ({
        ...call,
        duration: call.duration + 1
      })))
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const getCallStatusColor = (status: CallStatus) => {
    switch (status) {
      case 'active': return 'text-green-500'
      case 'on-hold': return 'text-yellow-500'
      case 'incoming': return 'text-blue-500'
      case 'ended': return 'text-gray-500'
      case 'missed': return 'text-red-500'
      default: return 'text-gray-500'
    }
  }

  const getAgentStatusColor = (status: AgentStatus) => {
    switch (status) {
      case 'available': return 'text-green-500'
      case 'busy': return 'text-blue-500'
      case 'break': return 'text-yellow-500'
      case 'offline': return 'text-gray-500'
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

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return 'text-green-600'
      case 'negative': return 'text-red-600'
      case 'neutral': return 'text-gray-600'
      default: return 'text-gray-600'
    }
  }

  const handleSendMessage = () => {
    if (!newMessage.trim()) return

    const message: TeamMessage = {
      id: `msg-${Date.now()}`,
      type: 'note',
      author: 'You',
      content: newMessage,
      timestamp: new Date(),
      callId: selectedCall?.id,
      priority: 'medium'
    }

    setTeamMessages(prev => [...prev, message])
    setNewMessage('')
  }

  const filteredMessages = teamMessages.filter(msg => 
    messageFilter.length === 0 || messageFilter.includes(msg.type)
  )

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Real-Time Communication Hub</h1>
          <p className="text-muted-foreground">
            {activeCalls.length} active calls • {agents.filter(a => a.status === 'available').length} agents available
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </Button>
          <Button variant="outline" size="sm">
            <Monitor className="w-4 h-4 mr-2" />
            Dashboard
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Active Calls Panel */}
        <div className="xl:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Active Calls ({activeCalls.length})</span>
                <Button variant="ghost" size="sm">
                  <Filter className="w-4 h-4" />
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {activeCalls.map((call) => (
                <motion.div
                  key={call.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={cn(
                    'p-4 border rounded-lg cursor-pointer transition-all',
                    selectedCall?.id === call.id ? 'border-primary bg-primary/5' : 'hover:bg-muted/50'
                  )}
                  onClick={() => setSelectedCall(call)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <VoiceStatusIndicator
                          status={call.status === 'active' ? 'speaking' : 
                                 call.status === 'on-hold' ? 'listening' : 'idle'}
                          size="sm"
                        />
                        <div>
                          <h4 className="font-semibold">{call.leadName}</h4>
                          <p className="text-sm text-muted-foreground">{call.leadPhone}</p>
                        </div>
                        <div className={cn(
                          'px-2 py-1 rounded text-xs font-medium',
                          call.status === 'active' ? 'bg-green-100 text-green-700' :
                          call.status === 'on-hold' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-gray-100 text-gray-700'
                        )}>
                          {call.status}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatDuration(call.duration)}
                        </div>
                        <div className="flex items-center gap-1">
                          <Activity className={getQualityColor(call.quality)} />
                          <span className={getQualityColor(call.quality)}>{call.quality}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <div className={cn(
                            'w-2 h-2 rounded-full',
                            getSentimentColor(call.sentiment)
                          )} />
                          <span className={getSentimentColor(call.sentiment)}>{call.sentiment}</span>
                        </div>
                        {call.recording && (
                          <div className="flex items-center gap-1 text-red-500">
                            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                            <span>Recording</span>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm">
                        <Headphones className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </CardContent>
          </Card>

          {/* Selected Call Details */}
          {selectedCall && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Call Details - {selectedCall.leadName}</span>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm">
                      <Download className="w-4 h-4 mr-2" />
                      Export
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setExpandedTranscript(!expandedTranscript)}
                    >
                      {expandedTranscript ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </Button>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div>
                    <p className="text-sm font-medium mb-1">Agent</p>
                    <p className="text-sm">{selectedCall.agentName}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium mb-1">Duration</p>
                    <p className="text-sm font-mono">{formatDuration(selectedCall.duration)}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium mb-1">Quality</p>
                    <p className={cn('text-sm font-medium', getQualityColor(selectedCall.quality))}>
                      {selectedCall.quality}
                    </p>
                  </div>
                </div>

                {/* Live Transcript */}
                <AnimatePresence>
                  {expandedTranscript && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium">Live Transcript</h4>
                        <div className="flex items-center gap-2">
                          <Waveform isActive={selectedCall.status === 'active'} bars={5} className="text-green-500" />
                          <span className="text-xs text-muted-foreground">Live</span>
                        </div>
                      </div>
                      
                      <div className="max-h-64 overflow-y-auto space-y-3 bg-muted/30 rounded-lg p-4">
                        {selectedCall.transcript.map((entry) => (
                          <motion.div
                            key={entry.id}
                            initial={{ opacity: 0, x: entry.speaker === 'agent' ? -20 : 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className={cn(
                              'p-3 rounded-lg',
                              entry.speaker === 'agent' 
                                ? 'bg-blue-50 border-l-4 border-blue-500' 
                                : 'bg-gray-50 border-l-4 border-gray-300'
                            )}
                          >
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs font-medium">
                                {entry.speaker === 'agent' ? 'AI Agent' : 'Lead'}
                              </span>
                              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                <span>{entry.timestamp.toLocaleTimeString()}</span>
                                <span>({Math.round(entry.confidence * 100)}%)</span>
                              </div>
                            </div>
                            <p className="text-sm">{entry.content}</p>
                          </motion.div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Sidebar */}
        <div className="space-y-4">
          {/* Agent Status */}
          <Card>
            <CardHeader>
              <CardTitle>Team Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {agents.map((agent) => (
                <div key={agent.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      'w-3 h-3 rounded-full',
                      getAgentStatusColor(agent.status)
                    )} />
                    <div>
                      <p className="font-medium text-sm">{agent.name}</p>
                      <p className="text-xs text-muted-foreground capitalize">{agent.status}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold">{agent.skillLevel}/10</p>
                    <p className="text-xs text-muted-foreground">{agent.conversionRate}%</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Team Chat */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Team Chat</span>
                <Button variant="ghost" size="sm">
                  <Filter className="w-4 h-4" />
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-64 overflow-y-auto mb-4">
                {filteredMessages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={cn(
                      'p-3 rounded-lg text-sm',
                      message.type === 'system' ? 'bg-blue-50 text-blue-800' :
                      message.type === 'note' ? 'bg-green-50 text-green-800' :
                      'bg-gray-50'
                    )}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-xs">{message.author}</span>
                      <span className="text-xs text-muted-foreground">
                        {message.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    <p>{message.content}</p>
                    {message.priority && (
                      <div className={cn(
                        'inline-block px-2 py-0.5 rounded text-xs mt-1',
                        message.priority === 'high' ? 'bg-red-100 text-red-700' :
                        message.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-gray-100 text-gray-700'
                      )}>
                        {message.priority} priority
                      </div>
                    )}
                  </motion.div>
                ))}
                <div ref={messagesEndRef} />
              </div>
              
              <div className="flex items-center gap-2">
                <Input
                  placeholder="Type a message..."
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  className="flex-1"
                />
                <Button size="sm" onClick={handleSendMessage}>
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default RealTimeCommunicationHub