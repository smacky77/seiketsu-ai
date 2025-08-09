'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  Activity, 
  Server, 
  Database, 
  Cpu, 
  HardDrive,
  Network,
  Zap,
  AlertTriangle,
  CheckCircle,
  Clock
} from 'lucide-react'

interface SystemMetric {
  name: string
  value: number
  unit: string
  status: 'healthy' | 'warning' | 'critical'
  threshold: number
  icon: React.ComponentType<any>
}

interface ServiceHealth {
  name: string
  status: 'online' | 'degraded' | 'offline'
  responseTime: number
  uptime: number
  lastCheck: Date
}

export function SystemMonitoringDashboard() {
  const [currentTime, setCurrentTime] = useState(new Date())
  const [autoRefresh, setAutoRefresh] = useState(true)

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  const systemMetrics: SystemMetric[] = [
    {
      name: 'CPU Usage',
      value: 34.2,
      unit: '%',
      status: 'healthy',
      threshold: 80,
      icon: Cpu
    },
    {
      name: 'Memory Usage',
      value: 67.8,
      unit: '%', 
      status: 'warning',
      threshold: 85,
      icon: Database
    },
    {
      name: 'Disk Usage',
      value: 45.3,
      unit: '%',
      status: 'healthy',
      threshold: 90,
      icon: HardDrive
    },
    {
      name: 'Network I/O',
      value: 123.5,
      unit: 'MB/s',
      status: 'healthy',
      threshold: 500,
      icon: Network
    }
  ]

  const serviceHealth: ServiceHealth[] = [
    {
      name: 'Market Intelligence API',
      status: 'online',
      responseTime: 145,
      uptime: 99.8,
      lastCheck: new Date(Date.now() - 30000)
    },
    {
      name: 'Communication Service',
      status: 'online',
      responseTime: 89,
      uptime: 100,
      lastCheck: new Date(Date.now() - 30000)
    },
    {
      name: 'Scheduling System',
      status: 'degraded',
      responseTime: 340,
      uptime: 97.2,
      lastCheck: new Date(Date.now() - 30000)
    },
    {
      name: 'Database Cluster',
      status: 'online',
      responseTime: 23,
      uptime: 99.9,
      lastCheck: new Date(Date.now() - 30000)
    },
    {
      name: 'Authentication Service',
      status: 'online',
      responseTime: 67,
      uptime: 99.7,
      lastCheck: new Date(Date.now() - 30000)
    }
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'online':
        return 'text-green-600'
      case 'warning':
      case 'degraded':
        return 'text-yellow-600'
      case 'critical':
      case 'offline':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'online':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'warning':
      case 'degraded':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />
      case 'critical':
      case 'offline':
        return <AlertTriangle className="h-4 w-4 text-red-600" />
      default:
        return <Activity className="h-4 w-4 text-gray-600" />
    }
  }

  const getProgressColor = (value: number, threshold: number, status: string) => {
    if (status === 'critical') return 'bg-red-600'
    if (status === 'warning') return 'bg-yellow-600'
    return 'bg-green-600'
  }

  return (
    <div className="space-y-6">
      {/* Real-time Status Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-green-600" />
            <span className="text-sm font-medium text-white">System Status: All Systems Operational</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Clock className="h-4 w-4" />
            Last updated: {currentTime.toLocaleTimeString()}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
            className="bg-slate-800 border-slate-700 text-slate-200"
          >
            {autoRefresh ? 'Pause' : 'Resume'} Auto-refresh
          </Button>
          <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
            <Activity className="h-4 w-4 mr-2" />
            Refresh Now
          </Button>
        </div>
      </div>

      {/* System Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {systemMetrics.map((metric, index) => {
          const Icon = metric.icon
          const progressPercentage = (metric.value / metric.threshold) * 100
          
          return (
            <Card key={index} className="bg-slate-800 border-slate-700">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-slate-200">
                  {metric.name}
                </CardTitle>
                <Icon className="h-4 w-4 text-slate-400" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-white">
                  {metric.value.toFixed(1)}{metric.unit}
                </div>
                <div className="mt-2">
                  <div className="w-full bg-slate-700 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-500 ${getProgressColor(metric.value, metric.threshold, metric.status)}`}
                      style={{ width: `${Math.min(progressPercentage, 100)}%` }}
                    ></div>
                  </div>
                </div>
                <div className={`flex items-center mt-2 text-sm ${getStatusColor(metric.status)}`}>
                  {getStatusIcon(metric.status)}
                  <span className="ml-1 capitalize">{metric.status}</span>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Service Health Status */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Server className="h-5 w-5" />
            Service Health Monitor
          </CardTitle>
          <CardDescription className="text-slate-400">
            Real-time status of all Epic 3 microservices
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {serviceHealth.map((service, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg">
                <div className="flex items-center gap-3">
                  {getStatusIcon(service.status)}
                  <div>
                    <div className="font-medium text-white">{service.name}</div>
                    <div className="text-sm text-slate-400">
                      Last checked {Math.floor((Date.now() - service.lastCheck.getTime()) / 1000)}s ago
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="text-slate-400">Response Time</div>
                      <div className="font-medium text-white">{service.responseTime}ms</div>
                    </div>
                    <div>
                      <div className="text-slate-400">Uptime</div>
                      <div className="font-medium text-white">{service.uptime}%</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Performance Trends */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Response Time Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48 bg-gradient-to-t from-blue-900/20 to-slate-700/20 rounded-lg border border-slate-600 flex items-center justify-center">
              <div className="text-center space-y-2">
                <Zap className="h-12 w-12 text-blue-400 mx-auto" />
                <p className="text-sm text-slate-300">Real-time performance chart</p>
                <p className="text-xs text-slate-400">Average response: 147ms</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Resource Utilization</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48 bg-gradient-to-t from-green-900/20 to-slate-700/20 rounded-lg border border-slate-600 flex items-center justify-center">
              <div className="text-center space-y-2">
                <Database className="h-12 w-12 text-green-400 mx-auto" />
                <p className="text-sm text-slate-300">Resource usage over time</p>
                <p className="text-xs text-slate-400">Avg utilization: 52%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}