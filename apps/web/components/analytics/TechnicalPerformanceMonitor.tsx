'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Activity,
  Zap,
  Shield,
  Server,
  Phone,
  AlertTriangle,
  CheckCircle,
  Clock,
  Wifi,
  Database,
  Cpu,
  HardDrive,
  Network,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw
} from 'lucide-react'

interface TechnicalMetricsProps {
  data: {
    apiResponseTime: number
    errorRate: number
    voiceQuality: number
    systemAvailability: number
    integrationSuccess: number
  }
}

export function TechnicalPerformanceMonitor({ data }: TechnicalMetricsProps) {
  const [refreshing, setRefreshing] = useState(false)
  const [realTimeMetrics, setRealTimeMetrics] = useState({
    currentLoad: 67.3,
    activeCalls: 142,
    queueDepth: 8,
    processingLatency: 85
  })

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setRealTimeMetrics(prev => ({
        currentLoad: Math.max(10, Math.min(95, prev.currentLoad + (Math.random() - 0.5) * 10)),
        activeCalls: Math.max(0, prev.activeCalls + Math.floor((Math.random() - 0.5) * 20)),
        queueDepth: Math.max(0, Math.min(50, prev.queueDepth + Math.floor((Math.random() - 0.5) * 5))),
        processingLatency: Math.max(50, Math.min(200, prev.processingLatency + (Math.random() - 0.5) * 30))
      }))
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  const performanceMetrics = [
    {
      title: 'API Response Time',
      value: `${data.apiResponseTime}ms`,
      status: data.apiResponseTime < 150 ? 'excellent' : data.apiResponseTime < 300 ? 'good' : 'warning',
      trend: 'down',
      change: '-23%',
      icon: Zap,
      target: '<200ms',
      description: 'Average API endpoint response time'
    },
    {
      title: 'System Uptime',
      value: `${data.systemAvailability}%`,
      status: data.systemAvailability > 99.9 ? 'excellent' : data.systemAvailability > 99.5 ? 'good' : 'warning',
      trend: 'up',
      change: '+0.02%',
      icon: Activity,
      target: '>99.9%',
      description: 'System availability over last 30 days'
    },
    {
      title: 'Error Rate',
      value: `${data.errorRate}%`,
      status: data.errorRate < 0.1 ? 'excellent' : data.errorRate < 0.5 ? 'good' : 'error',
      trend: 'down',
      change: '-45%',
      icon: AlertTriangle,
      target: '<0.1%',
      description: 'API and system error rate'
    },
    {
      title: 'Voice Quality Score',
      value: `${data.voiceQuality}%`,
      status: data.voiceQuality > 95 ? 'excellent' : data.voiceQuality > 90 ? 'good' : 'warning',
      trend: 'up',
      change: '+2.1%',
      icon: Phone,
      target: '>95%',
      description: 'Voice synthesis and recognition quality'
    },
    {
      title: 'Integration Success Rate',
      value: `${data.integrationSuccess}%`,
      status: data.integrationSuccess > 98 ? 'excellent' : data.integrationSuccess > 95 ? 'good' : 'warning',
      trend: 'up',
      change: '+1.8%',
      icon: Network,
      target: '>98%',
      description: 'Third-party API integration reliability'
    }
  ]

  const systemHealth = [
    {
      component: 'Voice Processing Engine',
      status: 'healthy',
      load: 72,
      responseTime: 45,
      lastCheck: '30s ago'
    },
    {
      component: 'Database Cluster',
      status: 'healthy', 
      load: 58,
      responseTime: 12,
      lastCheck: '1m ago'
    },
    {
      component: 'API Gateway',
      status: 'healthy',
      load: 41,
      responseTime: 23,
      lastCheck: '15s ago'
    },
    {
      component: 'ML Inference Service',
      status: 'warning',
      load: 89,
      responseTime: 156,
      lastCheck: '45s ago'
    },
    {
      component: 'Message Queue',
      status: 'healthy',
      load: 34,
      responseTime: 8,
      lastCheck: '20s ago'
    }
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'excellent': return 'text-green-400 bg-green-500/20'
      case 'good': return 'text-blue-400 bg-blue-500/20'
      case 'warning': return 'text-yellow-400 bg-yellow-500/20'
      case 'error': return 'text-red-400 bg-red-500/20'
      default: return 'text-gray-400 bg-gray-500/20'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="w-4 h-4 text-green-400" />
      case 'warning': return <AlertTriangle className="w-4 h-4 text-yellow-400" />
      case 'error': return <AlertTriangle className="w-4 h-4 text-red-400" />
      default: return <Activity className="w-4 h-4 text-gray-400" />
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    // Simulate refresh delay
    await new Promise(resolve => setTimeout(resolve, 1500))
    setRefreshing(false)
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Technical Performance</h2>
          <p className="text-gray-400 mt-1">System health and performance monitoring</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center space-x-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 text-gray-300 ${refreshing ? 'animate-spin' : ''}`} />
          <span className="text-gray-300 text-sm">Refresh</span>
        </button>
      </div>

      {/* Real-time Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-gray-800 rounded-xl p-4 border border-gray-700"
        >
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <Cpu className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-white font-bold text-xl">{realTimeMetrics.currentLoad.toFixed(1)}%</p>
              <p className="text-gray-400 text-sm">System Load</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="bg-gray-800 rounded-xl p-4 border border-gray-700"
        >
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-500/20 rounded-lg">
              <Phone className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <p className="text-white font-bold text-xl">{realTimeMetrics.activeCalls}</p>
              <p className="text-gray-400 text-sm">Active Calls</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="bg-gray-800 rounded-xl p-4 border border-gray-700"
        >
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <Clock className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <p className="text-white font-bold text-xl">{realTimeMetrics.queueDepth}</p>
              <p className="text-gray-400 text-sm">Queue Depth</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
          className="bg-gray-800 rounded-xl p-4 border border-gray-700"
        >
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-orange-500/20 rounded-lg">
              <Zap className="w-5 h-5 text-orange-400" />
            </div>
            <div>
              <p className="text-white font-bold text-xl">{realTimeMetrics.processingLatency.toFixed(0)}ms</p>
              <p className="text-gray-400 text-sm">Processing Latency</p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Performance Metrics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {performanceMetrics.map((metric, index) => (
          <motion.div
            key={metric.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-gray-800 rounded-xl p-6 border border-gray-700"
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-lg ${getStatusColor(metric.status).split(' ')[1]}`}>
                <metric.icon className={`w-6 h-6 ${getStatusColor(metric.status).split(' ')[0]}`} />
              </div>
              <div className="flex items-center space-x-2">
                {metric.trend === 'up' ? (
                  <ArrowUpRight className="w-4 h-4 text-green-400" />
                ) : (
                  <ArrowDownRight className="w-4 h-4 text-green-400" />
                )}
                <span className="text-green-400 text-sm font-medium">{metric.change}</span>
              </div>
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-3xl font-bold text-white">{metric.value}</p>
                <p className="text-sm text-gray-400">{metric.description}</p>
              </div>

              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Target: {metric.target}</span>
                <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(metric.status)}`}>
                  {metric.status}
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* System Health Overview */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="bg-gray-800 rounded-xl p-6 border border-gray-700"
      >
        <h3 className="text-xl font-semibold text-white mb-6">System Component Health</h3>
        
        <div className="space-y-4">
          {systemHealth.map((component, index) => (
            <motion.div
              key={component.component}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center justify-between p-4 bg-gray-900 rounded-lg"
            >
              <div className="flex items-center space-x-4">
                {getStatusIcon(component.status)}
                <div>
                  <p className="text-white font-medium">{component.component}</p>
                  <p className="text-gray-400 text-sm">Last checked: {component.lastCheck}</p>
                </div>
              </div>

              <div className="flex items-center space-x-8 text-sm">
                <div className="text-center">
                  <p className="text-gray-400">Load</p>
                  <div className="flex items-center space-x-2 mt-1">
                    <div className="w-16 bg-gray-700 rounded-full h-2">
                      <div
                        className={`h-full rounded-full ${
                          component.load > 80 ? 'bg-red-500' :
                          component.load > 60 ? 'bg-yellow-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${component.load}%` }}
                      />
                    </div>
                    <span className="text-white font-medium w-8">{component.load}%</span>
                  </div>
                </div>

                <div className="text-center">
                  <p className="text-gray-400">Response</p>
                  <p className={`font-medium mt-1 ${
                    component.responseTime > 100 ? 'text-red-400' :
                    component.responseTime > 50 ? 'text-yellow-400' : 'text-green-400'
                  }`}>
                    {component.responseTime}ms
                  </p>
                </div>

                <div className="text-center">
                  <p className="text-gray-400">Status</p>
                  <div className={`px-2 py-1 rounded-full text-xs font-medium mt-1 ${
                    component.status === 'healthy' ? 'bg-green-500/20 text-green-400' :
                    component.status === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-red-500/20 text-red-400'
                  }`}>
                    {component.status}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Performance Insights */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className="bg-gradient-to-r from-green-500/10 to-blue-500/10 rounded-xl p-6 border border-green-500/20"
      >
        <div className="flex items-center space-x-3 mb-4">
          <Shield className="w-6 h-6 text-green-400" />
          <h3 className="text-lg font-semibold text-white">Performance Insights & Recommendations</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <CheckCircle className="w-5 h-5 text-green-400 mt-0.5" />
              <div>
                <p className="text-white font-medium">Excellent Response Times</p>
                <p className="text-sm text-gray-400">API response time 23% below target - system performing optimally</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <TrendingUp className="w-5 h-5 text-blue-400 mt-0.5" />
              <div>
                <p className="text-white font-medium">Voice Quality Improving</p>
                <p className="text-sm text-gray-400">2.1% improvement in voice synthesis quality this week</p>
              </div>
            </div>
          </div>
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="w-5 h-5 text-yellow-400 mt-0.5" />
              <div>
                <p className="text-white font-medium">ML Service Under Load</p>
                <p className="text-sm text-gray-400">Consider scaling ML inference service - currently at 89% capacity</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <Zap className="w-5 h-5 text-purple-400 mt-0.5" />
              <div>
                <p className="text-white font-medium">Integration Reliability</p>
                <p className="text-sm text-gray-400">Third-party API success rate above 98% - excellent reliability</p>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}