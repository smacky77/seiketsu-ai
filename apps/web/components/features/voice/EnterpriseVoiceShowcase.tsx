'use client'

import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Mic, 
  Brain, 
  Zap, 
  Target, 
  Clock, 
  TrendingUp,
  Heart,
  MessageCircle,
  CheckCircle,
  Play,
  Pause,
  Volume2,
  Activity,
  Eye,
  Sparkles
} from 'lucide-react'

interface ShowcaseMetric {
  label: string
  value: string
  change: string
  trend: 'up' | 'down' | 'stable'
  icon: React.ElementType
  color: string
}

interface VoiceCapability {
  title: string
  description: string
  icon: React.ElementType
  demo: string
  color: string
  metrics: string[]
}

export function EnterpriseVoiceShowcase() {
  const [activeDemo, setActiveDemo] = useState<string>('')
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentMetrics, setCurrentMetrics] = useState<ShowcaseMetric[]>([
    {
      label: 'Response Time',
      value: '1.2s',
      change: '-67%',
      trend: 'down',
      icon: Clock,
      color: 'text-green-600'
    },
    {
      label: 'Emotion Accuracy',
      value: '94.2%',
      change: '+12%',
      trend: 'up',
      icon: Heart,
      color: 'text-purple-600'
    },
    {
      label: 'Intent Recognition',
      value: '91.8%',
      change: '+8%',
      trend: 'up',
      icon: Target,
      color: 'text-blue-600'
    },
    {
      label: 'Lead Conversion',
      value: '127%',
      change: '+127%',
      trend: 'up',
      icon: TrendingUp,
      color: 'text-orange-600'
    }
  ])

  const voiceCapabilities: VoiceCapability[] = [
    {
      title: 'Sub-2 Second Response',
      description: 'Lightning-fast AI processing that feels natural and immediate',
      icon: Zap,
      demo: 'response_time',
      color: 'bg-yellow-500',
      metrics: ['< 2s target', '1.2s average', '0.8s fastest']
    },
    {
      title: 'Emotion Intelligence',
      description: 'Real-time emotion detection with appropriate response adaptation',
      icon: Heart,
      demo: 'emotion_detection',
      color: 'bg-purple-500',
      metrics: ['94% accuracy', '7 emotions', 'Real-time adaptation']
    },
    {
      title: 'Context Awareness',
      description: 'Deep understanding of real estate context and client needs',
      icon: Brain,
      demo: 'context_awareness',
      color: 'bg-blue-500',
      metrics: ['Memory retention', 'Multi-turn context', 'Domain expertise']
    },
    {
      title: 'Natural Conversation',
      description: 'Human-like dialogue flow with interruption handling',
      icon: MessageCircle,
      demo: 'natural_conversation',
      color: 'bg-green-500',
      metrics: ['Interruption handling', 'Natural flow', 'Active listening']
    }
  ]

  const demoScenarios = [
    {
      id: 'first_time_buyer',
      name: 'First-Time Buyer',
      description: 'Nervous client needs guidance',
      emotion: 'anxiety',
      response: 'Empathetic, educational tone'
    },
    {
      id: 'luxury_client',
      name: 'Luxury Client', 
      description: 'High-end property inquiry',
      emotion: 'confident',
      response: 'Authoritative, premium service'
    },
    {
      id: 'urgent_investor',
      name: 'Urgent Investor',
      description: 'Time-sensitive deal analysis',
      emotion: 'urgency',
      response: 'Data-driven, efficient'
    }
  ]

  // Simulate real-time metrics updates
  useEffect(() => {
    if (isPlaying) {
      const interval = setInterval(() => {
        setCurrentMetrics(prev => prev.map(metric => ({
          ...metric,
          value: generateRandomMetricValue(metric.label)
        })))
      }, 2000)

      return () => clearInterval(interval)
    }
  }, [isPlaying])

  const generateRandomMetricValue = (label: string): string => {
    switch (label) {
      case 'Response Time':
        return `${(Math.random() * 0.8 + 0.8).toFixed(1)}s`
      case 'Emotion Accuracy':
        return `${(Math.random() * 5 + 92).toFixed(1)}%`
      case 'Intent Recognition':
        return `${(Math.random() * 4 + 89).toFixed(1)}%`
      case 'Lead Conversion':
        return `${(Math.random() * 20 + 120).toFixed(0)}%`
      default:
        return `${Math.random() * 100}%`
    }
  }

  const startDemo = (demoType: string) => {
    setActiveDemo(demoType)
    setIsPlaying(true)
    
    // Simulate demo duration
    setTimeout(() => {
      setIsPlaying(false)
      setActiveDemo('')
    }, 10000)
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8">
      
      {/* Header */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-800 rounded-full text-sm font-medium mb-4">
          <Sparkles className="w-4 h-4" />
          Enterprise Voice Intelligence
        </div>
        
        <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
          Voice Conversations
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600 block">
            Indistinguishable from Human
          </span>
        </h1>
        
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Experience enterprise-grade voice AI that understands emotion, context, and intent 
          with sub-2 second response times and human-like conversation flow.
        </p>
      </div>

      {/* Live Metrics Dashboard */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12">
        {currentMetrics.map((metric) => (
          <motion.div
            key={metric.label}
            className="bg-white rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow"
            whileHover={{ y: -2 }}
          >
            <div className="flex items-center justify-between mb-3">
              <metric.icon className={`w-6 h-6 ${metric.color}`} />
              <span className={`text-sm font-medium ${
                metric.trend === 'up' ? 'text-green-600' : 
                metric.trend === 'down' ? 'text-red-600' : 'text-gray-600'
              }`}>
                {metric.change}
              </span>
            </div>
            
            <div className="text-2xl font-bold text-gray-900 mb-1">
              {metric.value}
            </div>
            
            <div className="text-sm text-gray-600">
              {metric.label}
            </div>
            
            {isPlaying && (
              <motion.div
                className="mt-2 h-1 bg-gray-200 rounded-full overflow-hidden"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <motion.div
                  className={`h-full bg-gradient-to-r from-blue-500 to-purple-500`}
                  animate={{ width: ['0%', '100%'] }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
              </motion.div>
            )}
          </motion.div>
        ))}
      </div>

      {/* Voice Capabilities */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        {voiceCapabilities.map((capability) => (
          <motion.div
            key={capability.title}
            className={`bg-white rounded-lg p-6 shadow-sm hover:shadow-lg transition-all cursor-pointer ${
              activeDemo === capability.demo ? 'ring-2 ring-blue-500 shadow-lg' : ''
            }`}
            whileHover={{ y: -5 }}
            onClick={() => startDemo(capability.demo)}
          >
            <div className={`w-12 h-12 rounded-lg ${capability.color} flex items-center justify-center mb-4`}>
              <capability.icon className="w-6 h-6 text-white" />
            </div>
            
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {capability.title}
            </h3>
            
            <p className="text-gray-600 mb-4">
              {capability.description}
            </p>
            
            <div className="space-y-1">
              {capability.metrics.map((metric, index) => (
                <div key={index} className="flex items-center gap-2 text-sm text-gray-500">
                  <CheckCircle className="w-3 h-3 text-green-500" />
                  {metric}
                </div>
              ))}
            </div>
            
            {activeDemo === capability.demo && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 flex items-center gap-2 text-blue-600 font-medium"
              >
                <Activity className="w-4 h-4 animate-pulse" />
                Demo Active
              </motion.div>
            )}
          </motion.div>
        ))}
      </div>

      {/* Interactive Demo Scenarios */}
      <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-2xl p-8">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Experience Different Client Scenarios
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            See how our AI adapts its personality, tone, and approach based on client emotion and context.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {demoScenarios.map((scenario) => (
            <motion.div
              key={scenario.id}
              className={`bg-white rounded-lg p-6 shadow-sm cursor-pointer transition-all ${
                activeDemo === scenario.id ? 'ring-2 ring-purple-500 shadow-lg' : 'hover:shadow-md'
              }`}
              whileHover={{ scale: 1.02 }}
              onClick={() => startDemo(scenario.id)}
            >
              <div className="text-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {scenario.name}
                </h3>
                <p className="text-gray-600 text-sm mb-3">
                  {scenario.description}
                </p>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Detected Emotion:</span>
                  <span className="font-medium capitalize">{scenario.emotion}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">AI Response:</span>
                  <span className="font-medium">{scenario.response}</span>
                </div>
              </div>

              {activeDemo === scenario.id && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="mt-4 p-3 bg-purple-50 rounded-lg"
                >
                  <div className="flex items-center gap-2 text-purple-600">
                    <Volume2 className="w-4 h-4 animate-pulse" />
                    <span className="text-sm font-medium">AI Responding...</span>
                  </div>
                </motion.div>
              )}
            </motion.div>
          ))}
        </div>

        {/* Demo Controls */}
        <div className="flex items-center justify-center gap-4">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all ${
              isPlaying 
                ? 'bg-red-500 text-white hover:bg-red-600' 
                : 'bg-blue-500 text-white hover:bg-blue-600'
            }`}
          >
            {isPlaying ? (
              <>
                <Pause className="w-4 h-4" />
                Stop Demo
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Start Live Demo
              </>
            )}
          </button>
          
          <button
            onClick={() => window.open('/demo/voice-intelligence', '_blank')}
            className="flex items-center gap-2 px-6 py-3 border border-gray-300 rounded-lg font-medium hover:bg-gray-50 transition-all"
          >
            <Eye className="w-4 h-4" />
            Full Interactive Demo
          </button>
        </div>
      </div>

      {/* Performance Visualization */}
      <AnimatePresence>
        {isPlaying && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-white rounded-lg p-8 shadow-lg border-2 border-blue-500"
          >
            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                Live Performance Monitoring
              </h3>
              <p className="text-gray-600">
                Real-time metrics during voice conversation processing
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Processing Pipeline */}
              <div className="space-y-4">
                <h4 className="font-semibold text-gray-900">Processing Pipeline</h4>
                {[
                  { stage: 'Speech Recognition', time: '245ms', status: 'complete' },
                  { stage: 'Emotion Detection', time: '120ms', status: 'complete' },
                  { stage: 'Intent Classification', time: '89ms', status: 'processing' },
                  { stage: 'Response Generation', time: '420ms', status: 'pending' },
                  { stage: 'Voice Synthesis', time: '185ms', status: 'pending' }
                ].map((item, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${
                      item.status === 'complete' ? 'bg-green-500' :
                      item.status === 'processing' ? 'bg-blue-500 animate-pulse' :
                      'bg-gray-300'
                    }`} />
                    <span className="text-sm text-gray-700">{item.stage}</span>
                    <span className="text-xs text-gray-500 ml-auto">{item.time}</span>
                  </div>
                ))}
              </div>

              {/* Audio Quality */}
              <div className="space-y-4">
                <h4 className="font-semibold text-gray-900">Audio Quality</h4>
                {[
                  { metric: 'Clarity Score', value: 94, unit: '%' },
                  { metric: 'Noise Level', value: 12, unit: 'dB' },
                  { metric: 'Voice Activity', value: 87, unit: '%' }
                ].map((item, index) => (
                  <div key={index} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-700">{item.metric}</span>
                      <span className="font-medium">{item.value}{item.unit}</span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <motion.div
                        className="h-full bg-gradient-to-r from-green-400 to-green-600"
                        animate={{ width: `${item.value}%` }}
                        transition={{ duration: 1 }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Conversation Insights */}
              <div className="space-y-4">
                <h4 className="font-semibold text-gray-900">Conversation Insights</h4>
                <div className="space-y-3">
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <div className="text-sm font-medium text-blue-900">Current Emotion</div>
                    <div className="text-blue-700">Interested & Engaged</div>
                  </div>
                  <div className="p-3 bg-green-50 rounded-lg">
                    <div className="text-sm font-medium text-green-900">Intent Detected</div>
                    <div className="text-green-700">Schedule Property Viewing</div>
                  </div>
                  <div className="p-3 bg-purple-50 rounded-lg">
                    <div className="text-sm font-medium text-purple-900">Qualification Score</div>
                    <div className="text-purple-700">High Potential Lead</div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}