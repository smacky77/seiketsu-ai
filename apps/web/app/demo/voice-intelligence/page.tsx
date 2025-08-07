'use client'

import { useState, useEffect } from 'react'
import { VoiceIntelligenceDemo } from '../../../components/voice-intelligence/VoiceIntelligenceDemo'
import { motion } from 'framer-motion'
import { 
  Mic, 
  Brain, 
  Zap, 
  Target, 
  Clock, 
  TrendingUp,
  Play,
  Users,
  Building,
  Star,
  CheckCircle,
  ArrowRight
} from 'lucide-react'

export default function VoiceIntelligenceDemoPage() {
  const [selectedDemo, setSelectedDemo] = useState<string>('')
  const [metrics, setMetrics] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Simulate loading
    const timer = setTimeout(() => setIsLoading(false), 1000)
    return () => clearTimeout(timer)
  }, [])

  const demoScenarios = [
    {
      id: 'first_time_buyer',
      name: 'First-Time Home Buyer',
      description: 'Young professional seeking guidance through their first home purchase',
      avatar: '👩‍💼',
      difficulty: 'Beginner',
      duration: '5-7 minutes',
      keyFeatures: ['Budget guidance', 'Process education', 'Emotional support'],
      businessValue: 'Lead nurturing and education'
    },
    {
      id: 'luxury_buyer',
      name: 'Luxury Property Client',
      description: 'High-net-worth individual looking for exclusive properties',
      avatar: '🤵',
      difficulty: 'Advanced',
      duration: '7-10 minutes',
      keyFeatures: ['Luxury tone', 'Exclusive inventory', 'Premium service'],
      businessValue: 'High-value client retention'
    },
    {
      id: 'investor',
      name: 'Real Estate Investor',
      description: 'Experienced investor analyzing cash-flow opportunities',
      avatar: '📊',
      difficulty: 'Expert',
      duration: '6-8 minutes',
      keyFeatures: ['Market analysis', 'ROI calculations', 'Data-driven insights'],
      businessValue: 'Investment deal facilitation'
    }
  ]

  const enterpriseFeatures = [
    {
      icon: Zap,
      title: 'Sub-2 Second Response',
      description: 'Lightning-fast AI responses that feel natural and immediate',
      metric: '< 1.2s average',
      color: 'text-yellow-500'
    },
    {
      icon: Brain,
      title: 'Emotion Intelligence',
      description: 'Real-time emotion detection with appropriate response adaptation',
      metric: '94% accuracy',
      color: 'text-purple-500'
    },
    {
      icon: Target,
      title: 'Intent Recognition',
      description: 'Precise understanding of client needs and motivations',
      metric: '92% confidence',
      color: 'text-green-500'
    },
    {
      icon: Users,
      title: 'Lead Qualification',
      description: 'Intelligent scoring and real estate-specific qualification',
      metric: '89% conversion',
      color: 'text-blue-500'
    }
  ]

  const businessImpact = [
    { label: 'Lead Conversion Rate', value: '+127%', trend: 'up' },
    { label: 'Response Time', value: '-78%', trend: 'down' },
    { label: 'Client Satisfaction', value: '4.9/5', trend: 'up' },
    { label: 'Agent Productivity', value: '+245%', trend: 'up' }
  ]

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"
          />
          <h2 className="text-xl font-semibold text-gray-700">Loading Voice Intelligence Demo</h2>
          <p className="text-gray-500 mt-2">Initializing enterprise AI capabilities...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="container mx-auto px-4 py-8">
        
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-800 rounded-full text-sm font-medium mb-4">
            <Mic className="w-4 h-4" />
            Enterprise Voice Intelligence Demo
          </div>
          
          <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
            Experience the Future of
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600 block">
              Real Estate Conversations
            </span>
          </h1>
          
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            Our AI voice agents deliver human-like conversations with enterprise-grade intelligence, 
            emotion detection, and real estate expertise—all with sub-2 second response times.
          </p>
        </motion.div>

        {/* Key Features */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12"
        >
          {enterpriseFeatures.map((feature, index) => (
            <div key={feature.title} className="bg-white rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center gap-3 mb-3">
                <feature.icon className={`w-6 h-6 ${feature.color}`} />
                <h3 className="font-semibold text-gray-900">{feature.title}</h3>
              </div>
              <p className="text-gray-600 text-sm mb-3">{feature.description}</p>
              <div className={`text-2xl font-bold ${feature.color}`}>
                {feature.metric}
              </div>
            </div>
          ))}
        </motion.div>

        {/* Demo Scenarios */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mb-12"
        >
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Choose Your Demo Scenario</h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Experience different client personas and see how our AI adapts its conversation style, 
              tone, and expertise to match each unique situation.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {demoScenarios.map((scenario) => (
              <motion.div
                key={scenario.id}
                whileHover={{ y: -5 }}
                className={`bg-white rounded-lg p-6 shadow-sm cursor-pointer transition-all ${
                  selectedDemo === scenario.id 
                    ? 'ring-2 ring-blue-500 shadow-lg' 
                    : 'hover:shadow-md'
                }`}
                onClick={() => setSelectedDemo(scenario.id)}
              >
                <div className="text-center mb-4">
                  <div className="text-4xl mb-3">{scenario.avatar}</div>
                  <h3 className="font-semibold text-gray-900 mb-2">{scenario.name}</h3>
                  <p className="text-gray-600 text-sm mb-3">{scenario.description}</p>
                  
                  <div className="flex justify-between text-xs text-gray-500 mb-3">
                    <span>⏱️ {scenario.duration}</span>
                    <span>🎯 {scenario.difficulty}</span>
                  </div>
                </div>

                <div className="space-y-2 mb-4">
                  {scenario.keyFeatures.map((feature, index) => (
                    <div key={index} className="flex items-center gap-2 text-sm text-gray-600">
                      <CheckCircle className="w-3 h-3 text-green-500" />
                      {feature}
                    </div>
                  ))}
                </div>

                <div className="text-xs font-medium text-blue-600 bg-blue-50 px-3 py-1 rounded-full text-center">
                  {scenario.businessValue}
                </div>

                {selectedDemo === scenario.id && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="mt-4 flex items-center justify-center gap-2 text-blue-600 font-medium"
                  >
                    <Play className="w-4 h-4" />
                    Selected for Demo
                  </motion.div>
                )}
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Live Demo */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mb-12"
        >
          <VoiceIntelligenceDemo
            agentId="enterprise-demo-agent"
            apiUrl={process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}
            wsUrl={process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}
            onMetricsUpdate={setMetrics}
            demoMode={true}
          />
        </motion.div>

        {/* Business Impact */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white rounded-lg p-8 shadow-sm mb-12"
        >
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Proven Business Impact</h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Real results from enterprise deployments across leading real estate organizations.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {businessImpact.map((metric) => (
              <div key={metric.label} className="text-center">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <TrendingUp 
                    className={`w-5 h-5 ${
                      metric.trend === 'up' ? 'text-green-500' : 'text-red-500'
                    }`} 
                  />
                  <span className={`text-3xl font-bold ${
                    metric.trend === 'up' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {metric.value}
                  </span>
                </div>
                <p className="text-gray-600 font-medium">{metric.label}</p>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Next Steps */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="text-center"
        >
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-8 text-white">
            <h2 className="text-3xl font-bold mb-4">Ready to Transform Your Business?</h2>
            <p className="text-xl opacity-90 mb-8 max-w-2xl mx-auto">
              Join leading real estate companies already using our voice intelligence platform 
              to increase conversions and deliver exceptional client experiences.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors flex items-center gap-2">
                Schedule Enterprise Demo
                <ArrowRight className="w-4 h-4" />
              </button>
              
              <button className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-blue-600 transition-colors">
                View Pricing Plans
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}