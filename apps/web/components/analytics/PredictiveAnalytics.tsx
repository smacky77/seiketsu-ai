'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import {
  TrendingUp,
  TrendingDown,
  Brain,
  Target,
  Calendar,
  AlertCircle,
  CheckCircle,
  DollarSign,
  Users,
  BarChart3,
  LineChart,
  PieChart,
  Lightbulb,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  Zap
} from 'lucide-react'

interface PredictiveAnalyticsProps {
  clientData: {
    leadGeneration: number
    demoConversion: number
    pilotEnrollment: number
    trialToPaid: number
    pipelineValue: number
    acquisitionCost: number
  }
  businessData: {
    mrr: number
    revenuePerClient: number
    ltv: number
    profitability: number
    growth: number
  }
}

export function PredictiveAnalytics({ clientData, businessData }: PredictiveAnalyticsProps) {
  const [predictionHorizon, setPredictionHorizon] = useState<'30d' | '90d' | '1y'>('90d')
  const [selectedModel, setSelectedModel] = useState<'revenue' | 'growth' | 'churn' | 'satisfaction'>('revenue')

  // Generate predictive insights based on current data
  const generatePredictions = () => {
    const currentMRR = businessData.mrr
    const currentGrowth = businessData.growth / 100
    const currentChurn = 0.058 // 5.8% from mock data
    
    const predictions = {
      '30d': {
        revenue: currentMRR * (1 + currentGrowth / 12),
        newClients: Math.round(clientData.leadGeneration * 0.3),
        churnRisk: 3.2,
        satisfaction: 97.8
      },
      '90d': {
        revenue: currentMRR * Math.pow(1 + currentGrowth / 12, 3),
        newClients: Math.round(clientData.leadGeneration * 0.9),
        churnRisk: 8.7,
        satisfaction: 96.9
      },
      '1y': {
        revenue: currentMRR * Math.pow(1 + currentGrowth / 12, 12),
        newClients: Math.round(clientData.leadGeneration * 3.6),
        churnRisk: 18.4,
        satisfaction: 95.8
      }
    }
    
    return predictions[predictionHorizon]
  }

  const predictions = generatePredictions()

  const predictiveMetrics = [
    {
      title: 'Predicted Revenue',
      currentValue: `$${(businessData.mrr / 1000).toFixed(0)}K`,
      predictedValue: `$${(predictions.revenue / 1000).toFixed(0)}K`,
      change: ((predictions.revenue - businessData.mrr) / businessData.mrr * 100).toFixed(1),
      confidence: 87,
      icon: DollarSign,
      color: 'text-green-400',
      trend: 'up'
    },
    {
      title: 'New Clients Forecast',
      currentValue: '30',
      predictedValue: predictions.newClients.toString(),
      change: ((predictions.newClients - 30) / 30 * 100).toFixed(1),
      confidence: 82,
      icon: Users,
      color: 'text-blue-400',
      trend: predictions.newClients > 30 ? 'up' : 'down'
    },
    {
      title: 'Churn Risk',
      currentValue: '5.8%',
      predictedValue: `${predictions.churnRisk.toFixed(1)}%`,
      change: ((predictions.churnRisk - 5.8) / 5.8 * 100).toFixed(1),
      confidence: 79,
      icon: AlertCircle,
      color: predictions.churnRisk > 10 ? 'text-red-400' : predictions.churnRisk > 7 ? 'text-yellow-400' : 'text-green-400',
      trend: predictions.churnRisk > 5.8 ? 'up' : 'down'
    },
    {
      title: 'Satisfaction Score',
      currentValue: '97.8%',
      predictedValue: `${predictions.satisfaction.toFixed(1)}%`,
      change: ((predictions.satisfaction - 97.8) / 97.8 * 100).toFixed(1),
      confidence: 91,
      icon: CheckCircle,
      color: 'text-purple-400',
      trend: predictions.satisfaction > 97.8 ? 'up' : 'down'
    }
  ]

  const scenarioAnalysis = [
    {
      scenario: 'Optimistic Growth',
      probability: 25,
      description: 'Market expansion + product improvements',
      impact: {
        revenue: '+45%',
        clients: '+38%',
        satisfaction: '+2.1%'
      },
      color: 'bg-green-500'
    },
    {
      scenario: 'Expected Growth', 
      probability: 50,
      description: 'Current trends continue',
      impact: {
        revenue: '+28%',
        clients: '+22%',
        satisfaction: '+0.8%'
      },
      color: 'bg-blue-500'
    },
    {
      scenario: 'Conservative Growth',
      probability: 20,
      description: 'Market challenges + competition',
      impact: {
        revenue: '+15%',
        clients: '+12%',
        satisfaction: '-0.5%'
      },
      color: 'bg-yellow-500'
    },
    {
      scenario: 'Risk Scenario',
      probability: 5,
      description: 'Economic downturn + tech issues',
      impact: {
        revenue: '-5%',
        clients: '-8%',
        satisfaction: '-2.1%'
      },
      color: 'bg-red-500'
    }
  ]

  const mlInsights = [
    {
      title: 'Lead Quality Improvement',
      insight: 'ML model identifies optimal lead scoring parameters',
      impact: '+23% conversion rate',
      confidence: 89,
      timeframe: '2 weeks',
      icon: Target
    },
    {
      title: 'Optimal Pricing Strategy',
      insight: 'Price elasticity analysis suggests tiered pricing opportunity',
      impact: '+18% revenue per client',
      confidence: 76,
      timeframe: '1 month',
      icon: DollarSign
    },
    {
      title: 'Churn Prevention',
      insight: 'Early warning system identifies at-risk clients',
      impact: '-34% churn rate',
      confidence: 84,
      timeframe: '6 weeks',
      icon: AlertCircle
    },
    {
      title: 'Capacity Planning',
      insight: 'Predictive load balancing optimizes resource allocation',
      impact: '+27% system efficiency',
      confidence: 92,
      timeframe: '3 weeks',
      icon: Zap
    }
  ]

  const riskFactors = [
    {
      risk: 'Market Saturation',
      probability: 'Medium',
      impact: 'High',
      mitigation: 'Expand to new markets, develop new features',
      urgency: 'monitor'
    },
    {
      risk: 'Competitive Pressure',
      probability: 'High',
      impact: 'Medium', 
      mitigation: 'Strengthen unique value proposition',
      urgency: 'action'
    },
    {
      risk: 'Technical Scalability',
      probability: 'Low',
      impact: 'High',
      mitigation: 'Infrastructure investment, performance optimization',
      urgency: 'monitor'
    },
    {
      risk: 'Economic Downturn',
      probability: 'Medium',
      impact: 'High',
      mitigation: 'Diversify client base, flexible pricing',
      urgency: 'prepare'
    }
  ]

  const getTrendIcon = (trend: string) => {
    return trend === 'up' 
      ? <ArrowUpRight className="w-4 h-4 text-green-400" />
      : <ArrowDownRight className="w-4 h-4 text-red-400" />
  }

  const getRiskColor = (urgency: string) => {
    switch (urgency) {
      case 'action': return 'border-red-500/50 bg-red-500/10'
      case 'prepare': return 'border-yellow-500/50 bg-yellow-500/10'
      default: return 'border-blue-500/50 bg-blue-500/10'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 85) return 'text-green-400'
    if (confidence >= 75) return 'text-yellow-400'
    return 'text-red-400'
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center space-x-3">
            <Brain className="w-8 h-8 text-cyan-400" />
            <span>Predictive Analytics</span>
          </h2>
          <p className="text-gray-400 mt-1">AI-powered insights and future performance predictions</p>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={predictionHorizon}
            onChange={(e) => setPredictionHorizon(e.target.value as any)}
            className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-400"
          >
            <option value="30d">30 Days</option>
            <option value="90d">90 Days</option>
            <option value="1y">1 Year</option>
          </select>
          <div className="flex bg-gray-700 rounded-lg p-1">
            {(['revenue', 'growth', 'churn', 'satisfaction'] as const).map((model) => (
              <button
                key={model}
                onClick={() => setSelectedModel(model)}
                className={`px-3 py-1 text-sm font-medium rounded-md capitalize transition-colors ${
                  selectedModel === model
                    ? 'bg-cyan-500 text-white'
                    : 'text-gray-300 hover:text-white hover:bg-gray-600'
                }`}
              >
                {model}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Prediction Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {predictiveMetrics.map((metric, index) => (
          <motion.div
            key={metric.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-gray-800 rounded-xl p-6 border border-gray-700 relative overflow-hidden"
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-lg bg-gray-700`}>
                <metric.icon className={`w-6 h-6 ${metric.color}`} />
              </div>
              <div className="text-right">
                <div className="flex items-center space-x-1">
                  {getTrendIcon(metric.trend)}
                  <span className={metric.trend === 'up' ? 'text-green-400' : 'text-red-400'}>
                    {Math.abs(parseFloat(metric.change))}%
                  </span>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-400">Current</p>
                <p className="text-xl font-bold text-white">{metric.currentValue}</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Predicted ({predictionHorizon})</p>
                <p className="text-2xl font-bold text-cyan-400">{metric.predictedValue}</p>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">{metric.title}</span>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 rounded-full bg-cyan-400"></div>
                  <span className={`font-medium ${getConfidenceColor(metric.confidence)}`}>
                    {metric.confidence}%
                  </span>
                </div>
              </div>
            </div>

            {/* Confidence indicator */}
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-700">
              <motion.div
                className="h-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500"
                initial={{ width: 0 }}
                animate={{ width: `${metric.confidence}%` }}
                transition={{ duration: 1, delay: index * 0.1 }}
              />
            </div>
          </motion.div>
        ))}
      </div>

      {/* Scenario Analysis */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-gray-800 rounded-xl p-6 border border-gray-700"
      >
        <h3 className="text-xl font-semibold text-white mb-6">Scenario Analysis</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {scenarioAnalysis.map((scenario, index) => (
            <motion.div
              key={scenario.scenario}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              className="bg-gray-900 rounded-lg p-4 border border-gray-700"
            >
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-white font-medium">{scenario.scenario}</h4>
                <div className="text-right">
                  <span className="text-2xl font-bold text-white">{scenario.probability}%</span>
                  <p className="text-xs text-gray-400">probability</p>
                </div>
              </div>
              
              <p className="text-sm text-gray-400 mb-4">{scenario.description}</p>
              
              <div className="space-y-2">
                {Object.entries(scenario.impact).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-sm">
                    <span className="text-gray-300 capitalize">{key}</span>
                    <span className={`font-medium ${
                      value.startsWith('+') ? 'text-green-400' : 
                      value.startsWith('-') ? 'text-red-400' : 'text-gray-300'
                    }`}>
                      {value}
                    </span>
                  </div>
                ))}
              </div>
              
              <div className="mt-3 w-full bg-gray-700 rounded-full h-2">
                <div
                  className={`h-full rounded-full ${scenario.color}`}
                  style={{ width: `${scenario.probability}%` }}
                />
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* ML-Powered Insights */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="bg-gray-800 rounded-xl p-6 border border-gray-700"
      >
        <div className="flex items-center space-x-3 mb-6">
          <Lightbulb className="w-6 h-6 text-yellow-400" />
          <h3 className="text-xl font-semibold text-white">AI-Powered Recommendations</h3>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {mlInsights.map((insight, index) => (
            <motion.div
              key={insight.title}
              initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-lg p-5 border border-blue-500/20"
            >
              <div className="flex items-start space-x-4">
                <div className="p-3 bg-blue-500/20 rounded-lg">
                  <insight.icon className="w-6 h-6 text-blue-400" />
                </div>
                <div className="flex-1">
                  <h4 className="text-white font-semibold mb-2">{insight.title}</h4>
                  <p className="text-gray-400 text-sm mb-3">{insight.insight}</p>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-green-400 font-semibold">{insight.impact}</span>
                      <p className="text-xs text-gray-500">Expected impact</p>
                    </div>
                    <div className="text-right">
                      <span className={`font-medium ${getConfidenceColor(insight.confidence)}`}>
                        {insight.confidence}%
                      </span>
                      <p className="text-xs text-gray-500">Confidence</p>
                    </div>
                    <div className="text-right">
                      <span className="text-cyan-400 font-medium">{insight.timeframe}</span>
                      <p className="text-xs text-gray-500">Implementation</p>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Risk Assessment */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className="bg-gray-800 rounded-xl p-6 border border-gray-700"
      >
        <h3 className="text-xl font-semibold text-white mb-6">Risk Assessment & Mitigation</h3>
        
        <div className="space-y-4">
          {riskFactors.map((risk, index) => (
            <motion.div
              key={risk.risk}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`p-4 rounded-lg border ${getRiskColor(risk.urgency)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h4 className="text-white font-medium">{risk.risk}</h4>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        risk.probability === 'High' ? 'bg-red-500/20 text-red-400' :
                        risk.probability === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-green-500/20 text-green-400'
                      }`}>
                        {risk.probability} Probability
                      </span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        risk.impact === 'High' ? 'bg-red-500/20 text-red-400' :
                        risk.impact === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-green-500/20 text-green-400'
                      }`}>
                        {risk.impact} Impact
                      </span>
                    </div>
                  </div>
                  <p className="text-gray-400 text-sm mb-2">{risk.mitigation}</p>
                </div>
                <div className={`px-3 py-1 rounded-full text-xs font-medium ml-4 ${
                  risk.urgency === 'action' ? 'bg-red-500/20 text-red-400' :
                  risk.urgency === 'prepare' ? 'bg-yellow-500/20 text-yellow-400' :
                  'bg-blue-500/20 text-blue-400'
                }`}>
                  {risk.urgency.toUpperCase()}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Future Opportunities */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.0 }}
        className="bg-gradient-to-r from-green-500/10 to-blue-500/10 rounded-xl p-6 border border-green-500/20"
      >
        <div className="flex items-center space-x-3 mb-4">
          <Target className="w-6 h-6 text-green-400" />
          <h3 className="text-lg font-semibold text-white">Strategic Opportunities</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <TrendingUp className="w-5 h-5 text-green-400 mt-0.5" />
              <div>
                <p className="text-white font-medium">Market Expansion</p>
                <p className="text-sm text-gray-400">International markets show 340% growth potential</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <Users className="w-5 h-5 text-blue-400 mt-0.5" />
              <div>
                <p className="text-white font-medium">Enterprise Segment</p>
                <p className="text-sm text-gray-400">Fortune 500 companies represent $2.3M opportunity</p>
              </div>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <Zap className="w-5 h-5 text-purple-400 mt-0.5" />
              <div>
                <p className="text-white font-medium">AI Enhancement</p>
                <p className="text-sm text-gray-400">Advanced ML could increase efficiency by 45%</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <BarChart3 className="w-5 h-5 text-orange-400 mt-0.5" />
              <div>
                <p className="text-white font-medium">Product Integration</p>
                <p className="text-sm text-gray-400">CRM partnerships could unlock 28% revenue growth</p>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}