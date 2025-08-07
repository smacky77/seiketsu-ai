'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  TrendingUp,
  TrendingDown,
  Users,
  Phone,
  Star,
  DollarSign,
  Target,
  Clock,
  AlertTriangle,
  CheckCircle,
  Activity,
  BarChart3,
  PieChart,
  LineChart,
  Download,
  Filter,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
  Zap,
  Heart,
  Award,
  Bell
} from 'lucide-react'
import { SeiketsuAnalyticsDashboard } from '../../components/analytics/SeiketsuAnalyticsDashboard'
import { ClientAcquisitionTracker } from '../../components/analytics/ClientAcquisitionTracker'
import { BusinessPerformanceMetrics } from '../../components/analytics/BusinessPerformanceMetrics'
import { TechnicalPerformanceMonitor } from '../../components/analytics/TechnicalPerformanceMonitor'
import { RealTimeDataVisualization } from '../../components/analytics/RealTimeDataVisualization'
import { PredictiveAnalytics } from '../../components/analytics/PredictiveAnalytics'

// Interface definitions
interface DashboardMetrics {
  clientAcquisition: ClientAcquisitionMetrics
  clientSuccess: ClientSuccessMetrics
  businessPerformance: BusinessMetrics
  technicalPerformance: TechnicalMetrics
  realTimeData: RealTimeMetrics
}

interface ClientAcquisitionMetrics {
  leadGeneration: number
  demoConversion: number
  pilotEnrollment: number
  trialToPaid: number
  pipelineValue: number
  acquisitionCost: number
}

interface ClientSuccessMetrics {
  satisfactionScore: number
  uptime: number
  responseTime: number
  ticketResolution: number
  retention: number
  churn: number
}

interface BusinessMetrics {
  mrr: number
  revenuePerClient: number
  ltv: number
  profitability: number
  growth: number
}

interface TechnicalMetrics {
  apiResponseTime: number
  errorRate: number
  voiceQuality: number
  systemAvailability: number
  integrationSuccess: number
}

interface RealTimeMetrics {
  activeUsers: number
  currentCalls: number
  todayLeads: number
  systemLoad: number
  alerts: Alert[]
}

interface Alert {
  id: string
  type: 'warning' | 'error' | 'success' | 'info'
  message: string
  timestamp: Date
  resolved: boolean
}

export default function AnalyticsPage() {
  const [selectedTimeRange, setSelectedTimeRange] = useState<'today' | 'week' | 'month' | 'quarter'>('week')
  const [selectedView, setSelectedView] = useState<'executive' | 'detailed' | 'realtime' | 'predictive'>('executive')
  const [dashboardData, setDashboardData] = useState<DashboardMetrics | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(new Date())

  // Mock data - replace with real API calls
  useEffect(() => {
    const fetchDashboardData = async () => {
      setIsLoading(true)
      try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        setDashboardData({
          clientAcquisition: {
            leadGeneration: 847,
            demoConversion: 24.3,
            pilotEnrollment: 89.2,
            trialToPaid: 76.8,
            pipelineValue: 2847000,
            acquisitionCost: 890
          },
          clientSuccess: {
            satisfactionScore: 97.8,
            uptime: 99.97,
            responseTime: 1.2,
            ticketResolution: 4.3,
            retention: 94.2,
            churn: 5.8
          },
          businessPerformance: {
            mrr: 384000,
            revenuePerClient: 12800,
            ltv: 156000,
            profitability: 42.3,
            growth: 28.4
          },
          technicalPerformance: {
            apiResponseTime: 120,
            errorRate: 0.03,
            voiceQuality: 96.8,
            systemAvailability: 99.97,
            integrationSuccess: 98.2
          },
          realTimeData: {
            activeUsers: 247,
            currentCalls: 12,
            todayLeads: 34,
            systemLoad: 67.3,
            alerts: [
              {
                id: '1',
                type: 'success',
                message: 'New milestone: 1000+ qualified leads this month!',
                timestamp: new Date(),
                resolved: false
              },
              {
                id: '2',
                type: 'info',
                message: 'System maintenance scheduled for tonight 2-4 AM EST',
                timestamp: new Date(Date.now() - 1800000),
                resolved: false
              }
            ]
          }
        })
        setLastUpdated(new Date())
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchDashboardData()
    
    // Auto-refresh every 30 seconds for real-time data
    const interval = setInterval(() => {
      if (selectedView === 'realtime') {
        fetchDashboardData()
      }
    }, 30000)

    return () => clearInterval(interval)
  }, [selectedTimeRange, selectedView])

  const getMetricChangeColor = (change: number) => {
    if (change > 5) return 'text-green-500'
    if (change < -5) return 'text-red-500'
    return 'text-yellow-500'
  }

  const getMetricIcon = (change: number) => {
    if (change > 0) return <ArrowUpRight className="w-4 h-4 text-green-500" />
    if (change < 0) return <ArrowDownRight className="w-4 h-4 text-red-500" />
    return <ArrowUpRight className="w-4 h-4 text-gray-400" />
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num.toString()
  }

  const formatCurrency = (num: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(num)
  }

  if (isLoading || !dashboardData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center"
        >
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-cyan-400 mb-8"></div>
          <h2 className="text-2xl font-bold text-white mb-4">Loading Analytics Dashboard</h2>
          <p className="text-gray-400">Preparing real-time insights...</p>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white">
      {/* Header */}
      <div className="border-b border-gray-700 bg-gray-800/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <BarChart3 className="w-8 h-8 text-cyan-400" />
                <h1 className="text-2xl font-bold">Seiketsu AI Analytics</h1>
              </div>
              <div className="bg-green-500/20 text-green-400 px-3 py-1 rounded-full text-sm font-medium">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span>Live Data</span>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* Time Range Selector */}
              <select
                value={selectedTimeRange}
                onChange={(e) => setSelectedTimeRange(e.target.value as any)}
                className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400"
              >
                <option value="today">Today</option>
                <option value="week">This Week</option>
                <option value="month">This Month</option>
                <option value="quarter">This Quarter</option>
              </select>

              {/* View Selector */}
              <div className="flex bg-gray-700 rounded-lg p-1">
                {(['executive', 'detailed', 'realtime', 'predictive'] as const).map((view) => (
                  <button
                    key={view}
                    onClick={() => setSelectedView(view)}
                    className={`px-4 py-2 text-sm font-medium rounded-md capitalize transition-colors ${
                      selectedView === view
                        ? 'bg-cyan-500 text-white'
                        : 'text-gray-300 hover:text-white hover:bg-gray-600'
                    }`}
                  >
                    {view}
                  </button>
                ))}
              </div>

              {/* Actions */}
              <div className="flex items-center space-x-2">
                <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors">
                  <Filter className="w-5 h-5" />
                </button>
                <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors">
                  <Download className="w-5 h-5" />
                </button>
                <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors relative">
                  <Bell className="w-5 h-5" />
                  {dashboardData.realTimeData.alerts.length > 0 && (
                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></div>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Last Updated */}
          <div className="mt-2 text-xs text-gray-400">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <AnimatePresence mode="wait">
          {selectedView === 'executive' && (
            <motion.div
              key="executive"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-8"
            >
              {/* Executive Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <motion.div
                  whileHover={{ scale: 1.02 }}
                  className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 shadow-lg"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-green-100 text-sm font-medium">Client Satisfaction</p>
                      <p className="text-3xl font-bold text-white">{dashboardData.clientSuccess.satisfactionScore}%</p>
                      <div className="flex items-center mt-2">
                        {getMetricIcon(2.3)}
                        <span className="text-green-100 text-sm ml-1">+2.3% this week</span>
                      </div>
                    </div>
                    <div className="bg-green-400/20 p-3 rounded-lg">
                      <Heart className="w-8 h-8 text-green-100" />
                    </div>
                  </div>
                </motion.div>

                <motion.div
                  whileHover={{ scale: 1.02 }}
                  className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 shadow-lg"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-blue-100 text-sm font-medium">Monthly Revenue</p>
                      <p className="text-3xl font-bold text-white">{formatCurrency(dashboardData.businessPerformance.mrr)}</p>
                      <div className="flex items-center mt-2">
                        {getMetricIcon(28.4)}
                        <span className="text-blue-100 text-sm ml-1">+28.4% growth</span>
                      </div>
                    </div>
                    <div className="bg-blue-400/20 p-3 rounded-lg">
                      <DollarSign className="w-8 h-8 text-blue-100" />
                    </div>
                  </div>
                </motion.div>

                <motion.div
                  whileHover={{ scale: 1.02 }}
                  className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 shadow-lg"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-purple-100 text-sm font-medium">System Uptime</p>
                      <p className="text-3xl font-bold text-white">{dashboardData.clientSuccess.uptime}%</p>
                      <div className="flex items-center mt-2">
                        <CheckCircle className="w-4 h-4 text-purple-100" />
                        <span className="text-purple-100 text-sm ml-1">Excellent</span>
                      </div>
                    </div>
                    <div className="bg-purple-400/20 p-3 rounded-lg">
                      <Activity className="w-8 h-8 text-purple-100" />
                    </div>
                  </div>
                </motion.div>

                <motion.div
                  whileHover={{ scale: 1.02 }}
                  className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl p-6 shadow-lg"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-orange-100 text-sm font-medium">Pipeline Value</p>
                      <p className="text-3xl font-bold text-white">{formatCurrency(dashboardData.clientAcquisition.pipelineValue)}</p>
                      <div className="flex items-center mt-2">
                        {getMetricIcon(15.7)}
                        <span className="text-orange-100 text-sm ml-1">+15.7% this month</span>
                      </div>
                    </div>
                    <div className="bg-orange-400/20 p-3 rounded-lg">
                      <Target className="w-8 h-8 text-orange-100" />
                    </div>
                  </div>
                </motion.div>
              </div>

              {/* Main Dashboard Components */}
              <SeiketsuAnalyticsDashboard data={dashboardData} timeRange={selectedTimeRange} />
            </motion.div>
          )}

          {selectedView === 'detailed' && (
            <motion.div
              key="detailed"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-8"
            >
              <ClientAcquisitionTracker data={dashboardData.clientAcquisition} />
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <BusinessPerformanceMetrics data={dashboardData.businessPerformance} />
                <TechnicalPerformanceMonitor data={dashboardData.technicalPerformance} />
              </div>
            </motion.div>
          )}

          {selectedView === 'realtime' && (
            <motion.div
              key="realtime"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <RealTimeDataVisualization data={dashboardData.realTimeData} />
            </motion.div>
          )}

          {selectedView === 'predictive' && (
            <motion.div
              key="predictive"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <PredictiveAnalytics 
                clientData={dashboardData.clientAcquisition}
                businessData={dashboardData.businessPerformance}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}