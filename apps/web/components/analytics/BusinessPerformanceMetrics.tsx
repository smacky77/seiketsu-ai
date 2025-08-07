'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Users,
  Target,
  Clock,
  Percent,
  BarChart3,
  PieChart,
  ArrowUpRight,
  ArrowDownRight,
  Calendar,
  Award
} from 'lucide-react'

interface BusinessMetricsProps {
  data: {
    mrr: number
    revenuePerClient: number
    ltv: number
    profitability: number
    growth: number
  }
}

export function BusinessPerformanceMetrics({ data }: BusinessMetricsProps) {
  const [selectedPeriod, setSelectedPeriod] = useState<'month' | 'quarter' | 'year'>('month')
  const [focusMetric, setFocusMetric] = useState<'revenue' | 'growth' | 'profitability'>('revenue')

  // Mock historical data
  const revenueHistory = {
    month: [
      { period: 'Jan', mrr: 320000, growth: 15.2, clients: 25 },
      { period: 'Feb', mrr: 342000, growth: 18.8, clients: 27 },
      { period: 'Mar', mrr: 361000, growth: 22.1, clients: 28 },
      { period: 'Apr', mrr: 384000, growth: 28.4, clients: 30 }
    ],
    quarter: [
      { period: 'Q1', mrr: 341000, growth: 18.7, clients: 27 },
      { period: 'Q2', mrr: 384000, growth: 28.4, clients: 30 },
      { period: 'Q3', mrr: 445000, growth: 35.2, clients: 35 },
      { period: 'Q4', mrr: 520000, growth: 42.1, clients: 41 }
    ],
    year: [
      { period: '2022', mrr: 180000, growth: 8.5, clients: 14 },
      { period: '2023', mrr: 295000, growth: 24.3, clients: 23 },
      { period: '2024', mrr: 384000, growth: 28.4, clients: 30 }
    ]
  }

  const businessKPIs = [
    {
      title: 'Monthly Recurring Revenue',
      value: `$${(data.mrr / 1000).toFixed(0)}K`,
      change: '+28.4%',
      trend: 'up' as const,
      icon: DollarSign,
      color: 'text-green-400',
      bgColor: 'bg-green-500/20',
      target: '$400K',
      targetProgress: (data.mrr / 400000) * 100
    },
    {
      title: 'Average Revenue Per Client',
      value: `$${(data.revenuePerClient / 1000).toFixed(1)}K`,
      change: '+12.8%',
      trend: 'up' as const,
      icon: Users,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/20',
      target: '$15K',
      targetProgress: (data.revenuePerClient / 15000) * 100
    },
    {
      title: 'Customer Lifetime Value',
      value: `$${(data.ltv / 1000).toFixed(0)}K`,
      change: '+18.7%',
      trend: 'up' as const,
      icon: Target,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/20',
      target: '$200K',
      targetProgress: (data.ltv / 200000) * 100
    },
    {
      title: 'Profit Margin',
      value: `${data.profitability.toFixed(1)}%`,
      change: '+5.2%',
      trend: 'up' as const,
      icon: Percent,
      color: 'text-orange-400',
      bgColor: 'bg-orange-500/20',
      target: '45%',
      targetProgress: (data.profitability / 45) * 100
    },
    {
      title: 'Growth Rate',
      value: `${data.growth.toFixed(1)}%`,
      change: '+8.1%',
      trend: 'up' as const,
      icon: TrendingUp,
      color: 'text-cyan-400',
      bgColor: 'bg-cyan-500/20',
      target: '35%',
      targetProgress: (data.growth / 35) * 100
    }
  ]

  const revenueBreakdown = [
    { source: 'Enterprise Plans', amount: 156000, percentage: 40.6, color: 'bg-blue-500' },
    { source: 'Professional Plans', amount: 115200, percentage: 30.0, color: 'bg-green-500' },
    { source: 'Starter Plans', amount: 69120, percentage: 18.0, color: 'bg-purple-500' },
    { source: 'Add-on Services', amount: 26880, percentage: 7.0, color: 'bg-orange-500' },
    { source: 'Custom Solutions', amount: 16800, percentage: 4.4, color: 'bg-cyan-500' }
  ]

  const profitabilityMetrics = [
    { metric: 'Gross Margin', value: 78.2, benchmark: 75.0, status: 'above' },
    { metric: 'Operating Margin', value: 42.3, benchmark: 40.0, status: 'above' },
    { metric: 'EBITDA Margin', value: 45.8, benchmark: 42.0, status: 'above' },
    { metric: 'Net Margin', value: 32.1, benchmark: 30.0, status: 'above' }
  ]

  const getTrendIcon = (trend: 'up' | 'down') => {
    return trend === 'up' 
      ? <ArrowUpRight className="w-4 h-4 text-green-400" />
      : <ArrowDownRight className="w-4 h-4 text-red-400" />
  }

  const currentHistory = revenueHistory[selectedPeriod]
  const maxValue = Math.max(...currentHistory.map(h => h.mrr))

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Business Performance</h2>
          <p className="text-gray-400 mt-1">Revenue metrics and profitability analysis</p>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value as any)}
            className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-400"
          >
            <option value="month">Monthly</option>
            <option value="quarter">Quarterly</option>
            <option value="year">Yearly</option>
          </select>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
        {businessKPIs.map((kpi, index) => (
          <motion.div
            key={kpi.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-gray-800 rounded-xl p-6 border border-gray-700 hover:border-gray-600 transition-colors"
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-lg ${kpi.bgColor}`}>
                <kpi.icon className={`w-6 h-6 ${kpi.color}`} />
              </div>
              <div className="flex items-center space-x-2">
                {getTrendIcon(kpi.trend)}
                <span className="text-green-400 text-sm font-medium">{kpi.change}</span>
              </div>
            </div>
            
            <div className="space-y-2">
              <p className="text-2xl font-bold text-white">{kpi.value}</p>
              <p className="text-sm text-gray-400">{kpi.title}</p>
              
              {/* Progress to target */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs text-gray-400">
                  <span>Target: {kpi.target}</span>
                  <span>{Math.min(kpi.targetProgress, 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-1.5">
                  <motion.div
                    className={`h-full rounded-full ${
                      kpi.targetProgress >= 100 ? 'bg-green-500' : 
                      kpi.targetProgress >= 80 ? 'bg-blue-500' : 'bg-orange-500'
                    }`}
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(kpi.targetProgress, 100)}%` }}
                    transition={{ duration: 1, delay: index * 0.1 }}
                  />
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Revenue Trend Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="bg-gray-800 rounded-xl p-6 border border-gray-700"
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold text-white">Revenue Growth Trend</h3>
          <div className="flex bg-gray-700 rounded-lg p-1">
            {(['revenue', 'growth', 'profitability'] as const).map((metric) => (
              <button
                key={metric}
                onClick={() => setFocusMetric(metric)}
                className={`px-4 py-2 text-sm font-medium rounded-md capitalize transition-colors ${
                  focusMetric === metric
                    ? 'bg-cyan-500 text-white'
                    : 'text-gray-300 hover:text-white hover:bg-gray-600'
                }`}
              >
                {metric}
              </button>
            ))}
          </div>
        </div>

        <div className="h-64 bg-gray-900 rounded-lg p-4">
          <div className="h-full flex items-end justify-between space-x-4">
            {currentHistory.map((point, index) => {
              const height = focusMetric === 'revenue'
                ? (point.mrr / maxValue) * 100
                : focusMetric === 'growth'
                ? (point.growth / 50) * 100 // Scale for visibility
                : ((point.mrr * 0.4) / maxValue) * 100 // Mock profitability

              return (
                <div key={index} className="flex-1 flex flex-col items-center">
                  <div className="w-full flex flex-col items-center space-y-2">
                    <motion.div
                      className="w-12 bg-gradient-to-t from-green-500 to-green-300 rounded-t-lg"
                      initial={{ height: 0 }}
                      animate={{ height: `${height * 2}px` }}
                      transition={{ duration: 0.8, delay: index * 0.2 }}
                    />
                    <div className="text-center">
                      <p className="text-white font-semibold text-sm">
                        {focusMetric === 'revenue' 
                          ? `$${(point.mrr / 1000).toFixed(0)}K`
                          : focusMetric === 'growth'
                          ? `${point.growth.toFixed(1)}%`
                          : `${(point.mrr * 0.4 / 1000).toFixed(0)}K`
                        }
                      </p>
                      <p className="text-gray-400 text-xs">{point.period}</p>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Revenue Breakdown */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.7 }}
          className="bg-gray-800 rounded-xl p-6 border border-gray-700"
        >
          <h3 className="text-xl font-semibold text-white mb-6">Revenue Breakdown</h3>
          
          <div className="space-y-4">
            {revenueBreakdown.map((source, index) => (
              <div key={source.source} className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-gray-300 font-medium">{source.source}</span>
                  <div className="text-right">
                    <span className="text-white font-bold">${(source.amount / 1000).toFixed(0)}K</span>
                    <span className="text-gray-400 text-sm ml-2">({source.percentage}%)</span>
                  </div>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <motion.div
                    className={`h-full rounded-full ${source.color}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${source.percentage}%` }}
                    transition={{ duration: 1, delay: index * 0.1 }}
                  />
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Profitability Metrics */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.9 }}
          className="bg-gray-800 rounded-xl p-6 border border-gray-700"
        >
          <h3 className="text-xl font-semibold text-white mb-6">Profitability Analysis</h3>
          
          <div className="space-y-6">
            {profitabilityMetrics.map((metric, index) => (
              <div key={metric.metric} className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-gray-300 font-medium">{metric.metric}</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-white font-bold">{metric.value.toFixed(1)}%</span>
                    <div className={`flex items-center space-x-1 ${
                      metric.status === 'above' ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {metric.status === 'above' ? (
                        <ArrowUpRight className="w-4 h-4" />
                      ) : (
                        <ArrowDownRight className="w-4 h-4" />
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2 text-xs text-gray-400">
                  <span>Benchmark: {metric.benchmark.toFixed(1)}%</span>
                  <span className={metric.status === 'above' ? 'text-green-400' : 'text-red-400'}>
                    ({metric.status === 'above' ? '+' : ''}{(metric.value - metric.benchmark).toFixed(1)}%)
                  </span>
                </div>
                <div className="relative w-full bg-gray-700 rounded-full h-2">
                  <motion.div
                    className={`h-full rounded-full ${
                      metric.status === 'above' ? 'bg-green-500' : 'bg-red-500'
                    }`}
                    initial={{ width: 0 }}
                    animate={{ width: `${(metric.value / (metric.benchmark * 1.5)) * 100}%` }}
                    transition={{ duration: 1, delay: index * 0.1 }}
                  />
                  <div 
                    className="absolute top-0 h-full w-0.5 bg-yellow-400"
                    style={{ left: `${(metric.benchmark / (metric.benchmark * 1.5)) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Financial Insights */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.1 }}
        className="bg-gradient-to-r from-blue-500/10 to-green-500/10 rounded-xl p-6 border border-blue-500/20"
      >
        <div className="flex items-center space-x-3 mb-4">
          <Award className="w-6 h-6 text-yellow-400" />
          <h3 className="text-lg font-semibold text-white">Financial Performance Insights</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <TrendingUp className="w-5 h-5 text-green-400 mt-0.5" />
              <div>
                <p className="text-white font-medium">Strong Revenue Growth</p>
                <p className="text-sm text-gray-400">28.4% MoM growth exceeds industry average of 15%</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <Target className="w-5 h-5 text-blue-400 mt-0.5" />
              <div>
                <p className="text-white font-medium">Healthy Unit Economics</p>
                <p className="text-sm text-gray-400">LTV:CAC ratio of 175:1 indicates sustainable growth</p>
              </div>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <Percent className="w-5 h-5 text-purple-400 mt-0.5" />
              <div>
                <p className="text-white font-medium">Excellent Margins</p>
                <p className="text-sm text-gray-400">42.3% profit margin well above SaaS benchmark of 30%</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <DollarSign className="w-5 h-5 text-orange-400 mt-0.5" />
              <div>
                <p className="text-white font-medium">Expansion Revenue</p>
                <p className="text-sm text-gray-400">18% of revenue from existing client expansion</p>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}