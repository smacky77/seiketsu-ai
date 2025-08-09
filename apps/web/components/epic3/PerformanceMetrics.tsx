'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  TrendingUp, 
  TrendingDown, 
  BarChart3, 
  LineChart, 
  Activity,
  Clock,
  Users,
  Target,
  Zap,
  Database,
  Network,
  Server
} from 'lucide-react'

interface PerformanceMetric {
  metric: string
  current: number
  previous: number
  unit: string
  trend: 'up' | 'down' | 'stable'
  target?: number
}

interface APIEndpointMetric {
  endpoint: string
  requests: number
  avgResponseTime: number
  errorRate: number
  throughput: number
}

export function PerformanceMetrics() {
  const [timeframe, setTimeframe] = useState('24h')
  const [metricType, setMetricType] = useState('overview')
  
  const performanceMetrics: PerformanceMetric[] = [
    {
      metric: 'Average Response Time',
      current: 147,
      previous: 162,
      unit: 'ms',
      trend: 'down',
      target: 200
    },
    {
      metric: 'Requests per Second',
      current: 342,
      previous: 298,
      unit: 'req/s',
      trend: 'up',
      target: 500
    },
    {
      metric: 'Error Rate',
      current: 0.12,
      previous: 0.18,
      unit: '%',
      trend: 'down',
      target: 1.0
    },
    {
      metric: 'Database Query Time',
      current: 23,
      previous: 29,
      unit: 'ms',
      trend: 'down',
      target: 50
    },
    {
      metric: 'Memory Usage',
      current: 67.8,
      previous: 71.2,
      unit: '%',
      trend: 'down',
      target: 80
    },
    {
      metric: 'CPU Utilization',
      current: 34.2,
      previous: 31.8,
      unit: '%',
      trend: 'up',
      target: 70
    }
  ]

  const apiEndpointMetrics: APIEndpointMetric[] = [
    {
      endpoint: '/api/v1/market-analysis',
      requests: 5673,
      avgResponseTime: 234,
      errorRate: 0.08,
      throughput: 23.4
    },
    {
      endpoint: '/api/v1/property-predictions',
      requests: 3421,
      avgResponseTime: 187,
      errorRate: 0.12,
      throughput: 14.2
    },
    {
      endpoint: '/api/v1/communication/send',
      requests: 8934,
      avgResponseTime: 89,
      errorRate: 0.05,
      throughput: 37.2
    },
    {
      endpoint: '/api/v1/scheduling/availability',
      requests: 2156,
      avgResponseTime: 156,
      errorRate: 0.23,
      throughput: 9.0
    },
    {
      endpoint: '/api/v1/scheduling/book',
      requests: 1789,
      avgResponseTime: 312,
      errorRate: 0.34,
      throughput: 7.4
    }
  ]

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-3 w-3 text-green-600" />
      case 'down':
        return <TrendingDown className="h-3 w-3 text-red-600" />
      default:
        return <Activity className="h-3 w-3 text-slate-600" />
    }
  }

  const getTrendColor = (trend: string, isGoodTrend: boolean = true) => {
    if (trend === 'stable') return 'text-slate-600'
    
    const isPositive = (trend === 'up' && isGoodTrend) || (trend === 'down' && !isGoodTrend)
    return isPositive ? 'text-green-600' : 'text-red-600'
  }

  const getPerformanceStatus = (current: number, target?: number) => {
    if (!target) return 'unknown'
    const percentage = (current / target) * 100
    if (percentage <= 70) return 'excellent'
    if (percentage <= 85) return 'good'
    if (percentage <= 95) return 'fair'
    return 'poor'
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'excellent':
        return 'text-green-600'
      case 'good':
        return 'text-blue-600'
      case 'fair':
        return 'text-yellow-600'
      case 'poor':
        return 'text-red-600'
      default:
        return 'text-slate-600'
    }
  }

  return (
    <div className="space-y-6">
      {/* Performance Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {performanceMetrics.map((metric, index) => {
          const isErrorMetric = metric.metric.toLowerCase().includes('error')
          const isGoodTrend = !isErrorMetric
          const change = Math.abs(metric.current - metric.previous)
          const changePercentage = ((change / metric.previous) * 100).toFixed(1)
          const status = getPerformanceStatus(metric.current, metric.target)

          return (
            <Card key={index} className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-slate-200 flex items-center justify-between">
                  {metric.metric}
                  {metric.target && (
                    <span className={`text-xs px-2 py-1 rounded ${getStatusColor(status)}`}>
                      {status}
                    </span>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-white mb-1">
                  {metric.current.toFixed(metric.unit === '%' ? 1 : 0)}{metric.unit}
                </div>
                <div className={`flex items-center text-sm ${getTrendColor(metric.trend, isGoodTrend)}`}>
                  {getTrendIcon(metric.trend)}
                  <span className="ml-1">
                    {changePercentage}% vs {timeframe}
                  </span>
                </div>
                {metric.target && (
                  <div className="mt-2">
                    <div className="w-full bg-slate-700 rounded-full h-1.5">
                      <div 
                        className={`h-1.5 rounded-full ${getStatusColor(status).replace('text', 'bg')}`}
                        style={{ 
                          width: `${Math.min((metric.current / metric.target) * 100, 100)}%` 
                        }}
                      ></div>
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      Target: {metric.target}{metric.unit}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Detailed Performance Tabs */}
      <Tabs defaultValue="api" className="w-full">
        <TabsList className="grid w-full grid-cols-4 bg-slate-800 border border-slate-700">
          <TabsTrigger value="api" className="text-slate-200">API Performance</TabsTrigger>
          <TabsTrigger value="infrastructure" className="text-slate-200">Infrastructure</TabsTrigger>
          <TabsTrigger value="user" className="text-slate-200">User Experience</TabsTrigger>
          <TabsTrigger value="trends" className="text-slate-200">Historical Trends</TabsTrigger>
        </TabsList>

        <TabsContent value="api" className="space-y-4">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Server className="h-5 w-5" />
                API Endpoint Performance
              </CardTitle>
              <CardDescription className="text-slate-400">
                Performance metrics for Epic 3 API endpoints
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left py-2 text-slate-300">Endpoint</th>
                      <th className="text-right py-2 text-slate-300">Requests</th>
                      <th className="text-right py-2 text-slate-300">Avg Response</th>
                      <th className="text-right py-2 text-slate-300">Error Rate</th>
                      <th className="text-right py-2 text-slate-300">Throughput</th>
                    </tr>
                  </thead>
                  <tbody>
                    {apiEndpointMetrics.map((endpoint, index) => (
                      <tr key={index} className="border-b border-slate-700/50">
                        <td className="py-3 text-white font-mono text-xs">
                          {endpoint.endpoint}
                        </td>
                        <td className="py-3 text-right text-slate-200">
                          {endpoint.requests.toLocaleString()}
                        </td>
                        <td className="py-3 text-right text-slate-200">
                          <span className={endpoint.avgResponseTime > 200 ? 'text-yellow-400' : 'text-green-400'}>
                            {endpoint.avgResponseTime}ms
                          </span>
                        </td>
                        <td className="py-3 text-right">
                          <span className={endpoint.errorRate > 0.2 ? 'text-red-400' : 'text-green-400'}>
                            {endpoint.errorRate.toFixed(2)}%
                          </span>
                        </td>
                        <td className="py-3 text-right text-slate-200">
                          {endpoint.throughput} req/s
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="infrastructure" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  Database Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-300">Connection Pool</span>
                    <span className="text-white font-medium">47/100 active</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-300">Query Cache Hit Rate</span>
                    <span className="text-green-400 font-medium">94.2%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-300">Slow Query Count</span>
                    <span className="text-yellow-400 font-medium">3</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-300">Deadlocks</span>
                    <span className="text-green-400 font-medium">0</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Network className="h-5 w-5" />
                  Network & CDN
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-300">CDN Cache Hit Rate</span>
                    <span className="text-green-400 font-medium">97.8%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-300">Bandwidth Usage</span>
                    <span className="text-white font-medium">234 MB/s</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-300">Origin Requests</span>
                    <span className="text-white font-medium">1,247/min</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-300">Edge Locations</span>
                    <span className="text-green-400 font-medium">12/12 healthy</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="user" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-slate-200">Page Load Time</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-white">1.8s</div>
                <div className="flex items-center text-sm text-green-400">
                  <TrendingDown className="h-3 w-3 mr-1" />
                  12% faster
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-slate-200">Time to Interactive</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-white">2.4s</div>
                <div className="flex items-center text-sm text-green-400">
                  <TrendingDown className="h-3 w-3 mr-1" />
                  8% faster
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-slate-200">Bounce Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-white">23.4%</div>
                <div className="flex items-center text-sm text-green-400">
                  <TrendingDown className="h-3 w-3 mr-1" />
                  5% lower
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Core Web Vitals</CardTitle>
              <CardDescription className="text-slate-400">
                Google's user experience metrics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-4 bg-green-900/20 rounded-lg border border-green-700">
                  <div className="text-green-400 font-medium">Largest Contentful Paint</div>
                  <div className="text-2xl font-bold text-white mt-2">1.2s</div>
                  <div className="text-sm text-green-400">Good</div>
                </div>
                <div className="text-center p-4 bg-green-900/20 rounded-lg border border-green-700">
                  <div className="text-green-400 font-medium">First Input Delay</div>
                  <div className="text-2xl font-bold text-white mt-2">45ms</div>
                  <div className="text-sm text-green-400">Good</div>
                </div>
                <div className="text-center p-4 bg-yellow-900/20 rounded-lg border border-yellow-700">
                  <div className="text-yellow-400 font-medium">Cumulative Layout Shift</div>
                  <div className="text-2xl font-bold text-white mt-2">0.12</div>
                  <div className="text-sm text-yellow-400">Needs Improvement</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trends" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <LineChart className="h-5 w-5" />
                  Performance Trends (7 days)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-48 bg-gradient-to-t from-blue-900/20 to-slate-700/20 rounded-lg border border-slate-600 flex items-center justify-center">
                  <div className="text-center space-y-2">
                    <BarChart3 className="h-12 w-12 text-blue-400 mx-auto" />
                    <p className="text-sm text-slate-300">Response time trend chart</p>
                    <p className="text-xs text-slate-400">7-day moving average</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  SLA Compliance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-300">Uptime SLA (99.9%)</span>
                    <span className="text-green-400 font-medium">99.97%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-300">Response Time SLA (&lt;200ms)</span>
                    <span className="text-green-400 font-medium">98.3%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-300">Error Rate SLA (&lt;0.1%)</span>
                    <span className="text-yellow-400 font-medium">85.2%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-300">Overall SLA Score</span>
                    <span className="text-green-400 font-medium text-xl">94.5%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}