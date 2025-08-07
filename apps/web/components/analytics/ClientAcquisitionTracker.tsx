'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import {
  TrendingUp,
  TrendingDown,
  Users,
  Target,
  DollarSign,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
  Eye,
  Phone,
  CheckCircle,
  Clock,
  Filter,
  Download
} from 'lucide-react'

interface ClientAcquisitionProps {
  data: {
    leadGeneration: number
    demoConversion: number
    pilotEnrollment: number
    trialToPaid: number
    pipelineValue: number
    acquisitionCost: number
  }
}

export function ClientAcquisitionTracker({ data }: ClientAcquisitionProps) {
  const [selectedMetric, setSelectedMetric] = useState<'pipeline' | 'conversion' | 'cost'>('pipeline')
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'quarter'>('month')

  // Mock historical data for charts
  const pipelineData = {
    week: [
      { date: 'Mon', leads: 45, demos: 12, trials: 8, customers: 3 },
      { date: 'Tue', leads: 52, demos: 15, trials: 11, customers: 4 },
      { date: 'Wed', leads: 48, demos: 13, trials: 9, customers: 5 },
      { date: 'Thu', leads: 61, demos: 18, trials: 14, customers: 6 },
      { date: 'Fri', leads: 55, demos: 16, trials: 12, customers: 4 },
      { date: 'Sat', leads: 38, demos: 10, trials: 7, customers: 2 },
      { date: 'Sun', leads: 41, demos: 11, trials: 8, customers: 3 }
    ],
    month: Array.from({ length: 30 }, (_, i) => ({
      date: `Day ${i + 1}`,
      leads: Math.floor(Math.random() * 50) + 30,
      demos: Math.floor(Math.random() * 20) + 8,
      trials: Math.floor(Math.random() * 15) + 5,
      customers: Math.floor(Math.random() * 8) + 2
    })),
    quarter: Array.from({ length: 12 }, (_, i) => ({
      date: `Week ${i + 1}`,
      leads: Math.floor(Math.random() * 300) + 200,
      demos: Math.floor(Math.random() * 100) + 50,
      trials: Math.floor(Math.random() * 60) + 30,
      customers: Math.floor(Math.random() * 30) + 15
    }))
  }

  const acquisitionMetrics = [
    {
      title: 'Lead Generation Rate',
      value: `${data.leadGeneration}`,
      unit: 'leads/day',
      change: '+18.2%',
      trend: 'up' as const,
      icon: Users,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/20'
    },
    {
      title: 'Demo Conversion Rate',
      value: `${data.demoConversion}%`,
      unit: 'of leads',
      change: '+5.4%',
      trend: 'up' as const,
      icon: Eye,
      color: 'text-green-400',
      bgColor: 'bg-green-500/20'
    },
    {
      title: 'Pilot Enrollment Rate',
      value: `${data.pilotEnrollment}%`,
      unit: 'of demos',
      change: '+12.8%',
      trend: 'up' as const,
      icon: Target,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/20'
    },
    {
      title: 'Trial-to-Paid Rate',
      value: `${data.trialToPaid}%`,
      unit: 'conversion',
      change: '+3.2%',
      trend: 'up' as const,
      icon: CheckCircle,
      color: 'text-orange-400',
      bgColor: 'bg-orange-500/20'
    },
    {
      title: 'Customer Acquisition Cost',
      value: `$${data.acquisitionCost}`,
      unit: 'per customer',
      change: '-8.1%',
      trend: 'down' as const,
      icon: DollarSign,
      color: 'text-cyan-400',
      bgColor: 'bg-cyan-500/20'
    },
    {
      title: 'Pipeline Value',
      value: `$${(data.pipelineValue / 1000000).toFixed(2)}M`,
      unit: 'total value',
      change: '+24.7%',
      trend: 'up' as const,
      icon: TrendingUp,
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-500/20'
    }
  ]

  const getTrendIcon = (trend: 'up' | 'down') => {
    return trend === 'up' 
      ? <ArrowUpRight className="w-4 h-4 text-green-400" />
      : <ArrowDownRight className="w-4 h-4 text-green-400" />
  }

  const currentData = pipelineData[timeRange]
  const maxValue = Math.max(...currentData.map(d => Math.max(d.leads, d.demos, d.trials, d.customers)))

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Client Acquisition Pipeline</h2>
          <p className="text-gray-400 mt-1">Track and optimize your client acquisition success</p>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-400"
          >
            <option value="week">This Week</option>
            <option value="month">This Month</option>
            <option value="quarter">This Quarter</option>
          </select>
          <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors">
            <Download className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {acquisitionMetrics.map((metric, index) => (
          <motion.div
            key={metric.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-gray-800 rounded-xl p-6 border border-gray-700 hover:border-gray-600 transition-colors"
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-lg ${metric.bgColor}`}>
                <metric.icon className={`w-6 h-6 ${metric.color}`} />
              </div>
              <div className="flex items-center space-x-2">
                {getTrendIcon(metric.trend)}
                <span className="text-green-400 text-sm font-medium">{metric.change}</span>
              </div>
            </div>
            
            <div>
              <p className="text-2xl font-bold text-white mb-1">{metric.value}</p>
              <p className="text-sm text-gray-400">{metric.unit}</p>
              <p className="text-sm font-medium text-gray-300 mt-2">{metric.title}</p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Conversion Funnel Visualization */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="bg-gray-800 rounded-xl p-6 border border-gray-700"
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold text-white">Acquisition Funnel</h3>
          <div className="text-sm text-gray-400">
            Overall conversion rate: <span className="text-white font-semibold">76.8%</span>
          </div>
        </div>

        <div className="space-y-4">
          {[
            { stage: 'Leads Generated', value: 3456, color: 'bg-blue-500', percentage: 100 },
            { stage: 'Demo Scheduled', value: 840, color: 'bg-green-500', percentage: 24.3 },
            { stage: 'Pilot Enrolled', value: 749, color: 'bg-purple-500', percentage: 89.2 },
            { stage: 'Trial Started', value: 575, color: 'bg-orange-500', percentage: 76.8 },
            { stage: 'Converted to Paid', value: 442, color: 'bg-cyan-500', percentage: 76.9 },
            { stage: '100% Satisfied', value: 432, color: 'bg-green-600', percentage: 97.7 }
          ].map((stage, index) => (
            <div key={stage.stage} className="relative">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-300 font-medium">{stage.stage}</span>
                <div className="text-right">
                  <span className="text-white font-bold text-lg">{stage.value.toLocaleString()}</span>
                  <span className="text-gray-400 text-sm ml-2">({stage.percentage.toFixed(1)}%)</span>
                </div>
              </div>
              <div className="relative">
                <div className="w-full bg-gray-700 rounded-full h-3">
                  <motion.div
                    className={`h-full rounded-full ${stage.color} relative overflow-hidden`}
                    initial={{ width: 0 }}
                    animate={{ width: `${stage.percentage}%` }}
                    transition={{ duration: 1, delay: index * 0.2 }}
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent to-white/20"></div>
                  </motion.div>
                </div>
              </div>
              {index < 5 && (
                <div className="flex justify-center mt-1">
                  <ArrowDownRight className="w-4 h-4 text-gray-500" />
                </div>
              )}
            </div>
          ))}
        </div>
      </motion.div>

      {/* Pipeline Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className="bg-gray-800 rounded-xl p-6 border border-gray-700"
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold text-white">Pipeline Performance Trends</h3>
          <div className="flex bg-gray-700 rounded-lg p-1">
            {(['pipeline', 'conversion', 'cost'] as const).map((metric) => (
              <button
                key={metric}
                onClick={() => setSelectedMetric(metric)}
                className={`px-4 py-2 text-sm font-medium rounded-md capitalize transition-colors ${
                  selectedMetric === metric
                    ? 'bg-cyan-500 text-white'
                    : 'text-gray-300 hover:text-white hover:bg-gray-600'
                }`}
              >
                {metric}
              </button>
            ))}
          </div>
        </div>

        {/* Chart Area */}
        <div className="h-64 bg-gray-900 rounded-lg p-4">
          <div className="h-full flex items-end space-x-2">
            {currentData.slice(0, 15).map((point, index) => {
              const height = selectedMetric === 'pipeline' 
                ? (point.leads / maxValue) * 100
                : selectedMetric === 'conversion'
                ? ((point.customers / point.leads) * 100 * 2) // Scale for visibility
                : (50 + Math.random() * 30) // Mock cost data

              return (
                <div key={index} className="flex-1 flex flex-col items-center">
                  <motion.div
                    className="w-full bg-gradient-to-t from-cyan-500 to-cyan-300 rounded-t-sm"
                    initial={{ height: 0 }}
                    animate={{ height: `${height}%` }}
                    transition={{ duration: 0.8, delay: index * 0.1 }}
                  />
                  <span className="text-xs text-gray-400 mt-2 transform -rotate-45">
                    {point.date}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center space-x-6 mt-4">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span className="text-sm text-gray-400">Leads</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-sm text-gray-400">Demos</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
            <span className="text-sm text-gray-400">Trials</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
            <span className="text-sm text-gray-400">Customers</span>
          </div>
        </div>
      </motion.div>

      {/* Action Items */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.0 }}
        className="bg-gradient-to-r from-green-500/10 to-blue-500/10 rounded-xl p-6 border border-green-500/20"
      >
        <h3 className="text-lg font-semibold text-white mb-4">Recommended Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-start space-x-3">
            <CheckCircle className="w-5 h-5 text-green-400 mt-0.5" />
            <div>
              <p className="text-white font-medium">Optimize Demo Conversion</p>
              <p className="text-sm text-gray-400">Demo conversion is below 30% - review demo quality and follow-up process</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <Target className="w-5 h-5 text-blue-400 mt-0.5" />
            <div>
              <p className="text-white font-medium">Scale Lead Generation</p>
              <p className="text-sm text-gray-400">Strong conversion rates indicate readiness to increase lead volume</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <Clock className="w-5 h-5 text-purple-400 mt-0.5" />
            <div>
              <p className="text-white font-medium">Reduce Time to Value</p>
              <p className="text-sm text-gray-400">Fast-track high-scoring leads to accelerate trial-to-paid conversion</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <DollarSign className="w-5 h-5 text-orange-400 mt-0.5" />
            <div>
              <p className="text-white font-medium">Monitor Acquisition Costs</p>
              <p className="text-sm text-gray-400">CAC trending down - good opportunity to increase marketing spend</p>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}