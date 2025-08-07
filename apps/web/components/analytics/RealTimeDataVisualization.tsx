'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Activity,
  Users,
  Phone,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  Target,
  Zap,
  Bell,
  RefreshCw,
  Maximize2,
  Minimize2,
  Eye,
  EyeOff
} from 'lucide-react'

interface RealTimeDataProps {
  data: {
    activeUsers: number
    currentCalls: number
    todayLeads: number
    systemLoad: number
    alerts: Array<{
      id: string
      type: 'warning' | 'error' | 'success' | 'info'
      message: string
      timestamp: Date
      resolved: boolean
    }>
  }
}

export function RealTimeDataVisualization({ data }: RealTimeDataProps) {
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [showAlerts, setShowAlerts] = useState(true)
  const [liveMetrics, setLiveMetrics] = useState({
    callsPerMinute: 15,
    averageCallDuration: 4.2,
    leadQualificationRate: 68.5,
    systemResponseTime: 125,
    voiceQuality: 96.8,
    customerSatisfaction: 97.2
  })

  const [activityData, setActivityData] = useState<Array<{
    timestamp: string
    calls: number
    leads: number
    users: number
  }>>([])

  // Simulate real-time data updates
  useEffect(() => {
    const generateDataPoint = () => ({
      timestamp: new Date().toLocaleTimeString(),
      calls: Math.floor(Math.random() * 20) + 10,
      leads: Math.floor(Math.random() * 8) + 2,
      users: data.activeUsers + Math.floor((Math.random() - 0.5) * 20)
    })

    // Initialize with some data points
    const initialData = Array.from({ length: 20 }, () => generateDataPoint())
    setActivityData(initialData)

    const interval = setInterval(() => {
      setActivityData(prev => {
        const newData = [...prev.slice(1), generateDataPoint()]
        return newData
      })

      // Update live metrics
      setLiveMetrics(prev => ({
        callsPerMinute: Math.max(5, prev.callsPerMinute + (Math.random() - 0.5) * 3),
        averageCallDuration: Math.max(2, prev.averageCallDuration + (Math.random() - 0.5) * 0.5),
        leadQualificationRate: Math.max(50, Math.min(90, prev.leadQualificationRate + (Math.random() - 0.5) * 5)),
        systemResponseTime: Math.max(80, prev.systemResponseTime + (Math.random() - 0.5) * 20),
        voiceQuality: Math.max(90, Math.min(100, prev.voiceQuality + (Math.random() - 0.5) * 2)),
        customerSatisfaction: Math.max(90, Math.min(100, prev.customerSatisfaction + (Math.random() - 0.5) * 1))
      }))
    }, 2000)

    return () => clearInterval(interval)
  }, [data.activeUsers])

  const realTimeKPIs = [
    {
      title: 'Active Users',
      value: data.activeUsers,
      unit: 'users',
      icon: Users,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/20',
      trend: '+12'
    },
    {
      title: 'Current Calls',
      value: data.currentCalls,
      unit: 'active',
      icon: Phone,
      color: 'text-green-400',
      bgColor: 'bg-green-500/20',
      trend: '+3'
    },
    {
      title: 'Today Leads',
      value: data.todayLeads,
      unit: 'qualified',
      icon: Target,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/20',
      trend: '+8'
    },
    {
      title: 'System Load',
      value: `${data.systemLoad.toFixed(1)}%`,
      unit: 'capacity',
      icon: Activity,
      color: data.systemLoad > 80 ? 'text-red-400' : data.systemLoad > 60 ? 'text-yellow-400' : 'text-green-400',
      bgColor: data.systemLoad > 80 ? 'bg-red-500/20' : data.systemLoad > 60 ? 'bg-yellow-500/20' : 'bg-green-500/20',
      trend: data.systemLoad > 70 ? '+5%' : '-2%'
    }
  ]

  const liveMetricCards = [
    {
      title: 'Calls/Minute',
      value: liveMetrics.callsPerMinute.toFixed(1),
      status: liveMetrics.callsPerMinute > 12 ? 'high' : 'normal',
      icon: Phone
    },
    {
      title: 'Avg Call Duration',
      value: `${liveMetrics.averageCallDuration.toFixed(1)}m`,
      status: liveMetrics.averageCallDuration > 5 ? 'high' : 'normal',
      icon: Clock
    },
    {
      title: 'Qualification Rate',
      value: `${liveMetrics.leadQualificationRate.toFixed(1)}%`,
      status: liveMetrics.leadQualificationRate > 70 ? 'high' : 'normal',
      icon: Target
    },
    {
      title: 'Response Time',
      value: `${liveMetrics.systemResponseTime.toFixed(0)}ms`,
      status: liveMetrics.systemResponseTime < 150 ? 'high' : 'normal',
      icon: Zap
    },
    {
      title: 'Voice Quality',
      value: `${liveMetrics.voiceQuality.toFixed(1)}%`,
      status: liveMetrics.voiceQuality > 96 ? 'high' : 'normal',
      icon: CheckCircle
    },
    {
      title: 'Satisfaction',
      value: `${liveMetrics.customerSatisfaction.toFixed(1)}%`,
      status: liveMetrics.customerSatisfaction > 95 ? 'high' : 'normal',
      icon: TrendingUp
    }
  ]

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'error': return <AlertTriangle className="w-4 h-4 text-red-400" />
      case 'warning': return <AlertTriangle className="w-4 h-4 text-yellow-400" />
      case 'success': return <CheckCircle className="w-4 h-4 text-green-400" />
      default: return <Bell className="w-4 h-4 text-blue-400" />
    }
  }

  const getAlertColor = (type: string) => {
    switch (type) {
      case 'error': return 'border-red-500/50 bg-red-500/10'
      case 'warning': return 'border-yellow-500/50 bg-yellow-500/10'
      case 'success': return 'border-green-500/50 bg-green-500/10'
      default: return 'border-blue-500/50 bg-blue-500/10'
    }
  }

  const maxValue = Math.max(...activityData.map(d => Math.max(d.calls, d.leads, d.users / 10)))

  return (
    <div className={`space-y-8 ${isFullscreen ? 'fixed inset-0 bg-gray-900 z-50 p-8 overflow-y-auto' : ''}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Real-Time Dashboard</h2>
          <p className="text-gray-400 mt-1">Live system metrics and activity monitoring</p>
        </div>
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setShowAlerts(!showAlerts)}
            className="flex items-center space-x-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
          >
            {showAlerts ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            <span className="text-sm">Alerts</span>
          </button>
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
          <div className="flex items-center space-x-2 px-3 py-2 bg-green-500/20 rounded-lg">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-green-400 text-sm font-medium">LIVE</span>
          </div>
        </div>
      </div>

      {/* Main KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        {realTimeKPIs.map((kpi, index) => (
          <motion.div
            key={kpi.title}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.1 }}
            className="bg-gray-800 rounded-xl p-6 border border-gray-700 relative overflow-hidden"
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-lg ${kpi.bgColor}`}>
                <kpi.icon className={`w-6 h-6 ${kpi.color}`} />
              </div>
              <div className="text-right">
                <span className="text-xs text-gray-400">{kpi.trend}</span>
              </div>
            </div>
            
            <div>
              <p className="text-3xl font-bold text-white mb-1">
                {typeof kpi.value === 'number' ? kpi.value.toLocaleString() : kpi.value}
              </p>
              <p className="text-sm text-gray-400">{kpi.title}</p>
              <p className="text-xs text-gray-500 mt-1">{kpi.unit}</p>
            </div>

            {/* Animated background */}
            <div className="absolute inset-0 opacity-5">
              <div className="w-full h-full bg-gradient-to-br from-transparent to-current animate-pulse"></div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Live Activity Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-gray-800 rounded-xl p-6 border border-gray-700"
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold text-white">Live Activity Stream</h3>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                <span className="text-gray-400">Calls</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="text-gray-400">Leads</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                <span className="text-gray-400">Users</span>
              </div>
            </div>
          </div>
        </div>

        <div className="h-64 bg-gray-900 rounded-lg p-4 relative overflow-hidden">
          <div className="h-full flex items-end space-x-1">
            <AnimatePresence>
              {activityData.slice(-15).map((point, index) => (
                <motion.div
                  key={`${point.timestamp}-${index}`}
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex-1 flex flex-col items-center space-y-1"
                >
                  <motion.div
                    className="w-full bg-blue-500 rounded-t-sm"
                    style={{ height: `${(point.calls / maxValue) * 180}px` }}
                  />
                  <motion.div
                    className="w-full bg-green-500"
                    style={{ height: `${(point.leads / maxValue) * 180}px` }}
                  />
                  <motion.div
                    className="w-full bg-purple-500 rounded-b-sm"
                    style={{ height: `${(point.users / 10 / maxValue) * 180}px` }}
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      </motion.div>

      {/* Live Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {liveMetricCards.map((metric, index) => (
          <motion.div
            key={metric.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 + index * 0.1 }}
            className={`bg-gray-800 rounded-xl p-4 border transition-all duration-300 ${
              metric.status === 'high' 
                ? 'border-green-500/50 bg-green-500/5' 
                : 'border-gray-700'
            }`}
          >
            <div className="flex items-center space-x-3">
              <div className={`p-2 rounded-lg ${
                metric.status === 'high' ? 'bg-green-500/20' : 'bg-gray-700'
              }`}>
                <metric.icon className={`w-4 h-4 ${
                  metric.status === 'high' ? 'text-green-400' : 'text-gray-400'
                }`} />
              </div>
              <div>
                <p className="text-white font-bold text-lg">{metric.value}</p>
                <p className="text-gray-400 text-xs">{metric.title}</p>
              </div>
            </div>
            {metric.status === 'high' && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute top-2 right-2 w-2 h-2 bg-green-400 rounded-full animate-pulse"
              />
            )}
          </motion.div>
        ))}
      </div>

      {/* Real-time Alerts */}
      <AnimatePresence>
        {showAlerts && data.alerts.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-gray-800 rounded-xl p-6 border border-gray-700"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">System Alerts</h3>
              <div className="text-sm text-gray-400">
                {data.alerts.filter(a => !a.resolved).length} active
              </div>
            </div>

            <div className="space-y-3">
              {data.alerts.slice(0, 5).map((alert) => (
                <motion.div
                  key={alert.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={`p-4 rounded-lg border ${getAlertColor(alert.type)}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      {getAlertIcon(alert.type)}
                      <div>
                        <p className="text-white font-medium">{alert.message}</p>
                        <p className="text-gray-400 text-sm mt-1">
                          {alert.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                    {!alert.resolved && (
                      <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                        alert.type === 'error' ? 'bg-red-500/20 text-red-400' :
                        alert.type === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                        alert.type === 'success' ? 'bg-green-500/20 text-green-400' :
                        'bg-blue-500/20 text-blue-400'
                      }`}>
                        {alert.type}
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Real-time Status Summary */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.0 }}
        className="bg-gradient-to-r from-blue-500/10 to-green-500/10 rounded-xl p-6 border border-blue-500/20"
      >
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-white mb-2">System Status</h3>
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span className="text-green-400">All systems operational</span>
              </div>
              <div className="flex items-center space-x-2">
                <Activity className="w-4 h-4 text-blue-400" />
                <span className="text-blue-400">{data.systemLoad.toFixed(1)}% system load</span>
              </div>
              <div className="flex items-center space-x-2">
                <Users className="w-4 h-4 text-purple-400" />
                <span className="text-purple-400">{data.activeUsers} active users</span>
              </div>
            </div>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-green-400">99.97%</p>
            <p className="text-sm text-gray-400">Uptime Today</p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}