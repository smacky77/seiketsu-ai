'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  TrendingUp,
  TrendingDown,
  Users,
  Phone,
  Clock,
  DollarSign,
  Target,
  Award,
  Activity,
  BarChart3,
  PieChart,
  LineChart,
  Calendar,
  Download,
  Filter,
  RefreshCw,
  Settings,
  Eye,
  AlertCircle,
  CheckCircle,
  Star,
  Zap
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  LineChart as RechartsLineChart,
  BarChart as RechartsBarChart,
  PieChart as RechartsPieChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Line,
  Bar,
  Cell,
  Area,
  AreaChart
} from 'recharts'
import { cn } from '@/lib/utils'

interface MetricCard {
  title: string
  value: string | number
  change: number
  trend: 'up' | 'down' | 'neutral'
  icon: React.ComponentType<any>
  color: string
}

interface AnalyticsData {
  overview: MetricCard[]
  callVolume: any[]
  conversionFunnel: any[]
  agentPerformance: any[]
  leadSources: any[]
  revenueData: any[]
  customerSatisfaction: any[]
}

interface AnalyticsDashboardProps {
  className?: string
  timeRange?: 'day' | 'week' | 'month' | 'quarter' | 'year'
  onTimeRangeChange?: (range: string) => void
}

// Mock analytics data
const mockAnalyticsData: AnalyticsData = {
  overview: [
    {
      title: 'Total Calls',
      value: '2,847',
      change: 12.5,
      trend: 'up',
      icon: Phone,
      color: 'text-blue-600'
    },
    {
      title: 'Qualified Leads',
      value: '1,923',
      change: 8.2,
      trend: 'up',
      icon: Users,
      color: 'text-green-600'
    },
    {
      title: 'Conversion Rate',
      value: '67.5%',
      change: -2.1,
      trend: 'down',
      icon: Target,
      color: 'text-purple-600'
    },
    {
      title: 'Revenue Generated',
      value: '$284,500',
      change: 15.3,
      trend: 'up',
      icon: DollarSign,
      color: 'text-green-600'
    },
    {
      title: 'Avg Call Duration',
      value: '4.2 min',
      change: 0.8,
      trend: 'up',
      icon: Clock,
      color: 'text-orange-600'
    },
    {
      title: 'Customer Satisfaction',
      value: '4.8/5',
      change: 0.2,
      trend: 'up',
      icon: Star,
      color: 'text-yellow-600'
    }
  ],
  callVolume: [
    { name: 'Mon', calls: 420, leads: 280, conversions: 189 },
    { name: 'Tue', calls: 385, leads: 265, conversions: 178 },
    { name: 'Wed', calls: 445, leads: 298, conversions: 201 },
    { name: 'Thu', calls: 380, leads: 255, conversions: 172 },
    { name: 'Fri', calls: 465, leads: 315, conversions: 213 },
    { name: 'Sat', calls: 290, leads: 195, conversions: 132 },
    { name: 'Sun', calls: 245, leads: 165, conversions: 111 }
  ],
  conversionFunnel: [
    { stage: 'Initial Contact', count: 2847, percentage: 100 },
    { stage: 'Interest Shown', count: 2134, percentage: 75 },
    { stage: 'Qualified Lead', count: 1923, percentage: 67.5 },
    { stage: 'Appointment Set', count: 1156, percentage: 40.6 },
    { stage: 'Converted', count: 692, percentage: 24.3 }
  ],
  agentPerformance: [
    { name: 'AI Agent Alpha', calls: 1247, leads: 912, conversions: 665, rating: 4.9 },
    { name: 'AI Agent Beta', calls: 892, leads: 623, conversions: 421, rating: 4.7 },
    { name: 'AI Agent Gamma', calls: 1056, leads: 734, conversions: 489, rating: 4.8 },
    { name: 'AI Agent Delta', calls: 652, leads: 445, conversions: 298, rating: 4.6 }
  ],
  leadSources: [
    { name: 'Website', value: 35, count: 997, color: '#8884d8' },
    { name: 'Social Media', value: 25, count: 712, color: '#82ca9d' },
    { name: 'Referrals', value: 20, count: 569, color: '#ffc658' },
    { name: 'Phone Calls', value: 12, count: 342, color: '#ff7c7c' },
    { name: 'Email', value: 8, count: 228, color: '#8dd1e1' }
  ],
  revenueData: [
    { month: 'Jan', revenue: 125000, target: 120000 },
    { month: 'Feb', revenue: 145000, target: 140000 },
    { month: 'Mar', revenue: 165000, target: 160000 },
    { month: 'Apr', revenue: 185000, target: 180000 },
    { month: 'May', revenue: 205000, target: 200000 },
    { month: 'Jun', revenue: 225000, target: 220000 }
  ],
  customerSatisfaction: [
    { period: 'Week 1', satisfaction: 4.6, responses: 142 },
    { period: 'Week 2', satisfaction: 4.7, responses: 156 },
    { period: 'Week 3', satisfaction: 4.8, responses: 168 },
    { period: 'Week 4', satisfaction: 4.9, responses: 174 }
  ]
}

export function AnalyticsDashboard({
  className,
  timeRange = 'month',
  onTimeRangeChange
}: AnalyticsDashboardProps) {
  const [data, setData] = useState<AnalyticsData>(mockAnalyticsData)
  const [selectedTimeRange, setSelectedTimeRange] = useState(timeRange)
  const [isLoading, setIsLoading] = useState(false)

  const handleTimeRangeChange = (range: string) => {
    setSelectedTimeRange(range as any)
    onTimeRangeChange?.(range)
    // Simulate loading new data
    setIsLoading(true)
    setTimeout(() => setIsLoading(false), 1000)
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(value)
  }

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('en-US').format(value)
  }

  const getTrendIcon = (trend: 'up' | 'down' | 'neutral') => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-4 h-4 text-green-600" />
      case 'down': return <TrendingDown className="w-4 h-4 text-red-600" />
      default: return <Activity className="w-4 h-4 text-gray-600" />
    }
  }

  const getTrendColor = (trend: 'up' | 'down' | 'neutral', change: number) => {
    if (trend === 'neutral') return 'text-gray-600'
    return change > 0 ? 'text-green-600' : 'text-red-600'
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Analytics Dashboard</h1>
          <p className="text-muted-foreground">
            Enterprise insights and performance metrics
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 bg-muted rounded-lg p-1">
            {['day', 'week', 'month', 'quarter', 'year'].map((range) => (
              <Button
                key={range}
                variant={selectedTimeRange === range ? 'default' : 'ghost'}
                size="sm"
                className="capitalize"
                onClick={() => handleTimeRangeChange(range)}
              >
                {range}
              </Button>
            ))}
          </div>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button variant="outline" size="sm">
            <RefreshCw className={cn('w-4 h-4 mr-2', isLoading && 'animate-spin')} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Overview Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {data.overview.map((metric, index) => {
          const Icon = metric.icon
          return (
            <motion.div
              key={metric.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">{metric.title}</p>
                      <p className="text-2xl font-bold">{metric.value}</p>
                      <div className={cn(
                        'flex items-center gap-1 text-sm mt-1',
                        getTrendColor(metric.trend, metric.change)
                      )}>
                        {getTrendIcon(metric.trend)}
                        <span>{Math.abs(metric.change)}%</span>
                      </div>
                    </div>
                    <Icon className={cn('w-8 h-8', metric.color)} />
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )
        })}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Call Volume Trend */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <LineChart className="w-5 h-5" />
              Call Volume Trend
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={data.callVolume}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area 
                  type="monotone" 
                  dataKey="calls" 
                  stackId="1" 
                  stroke="#8884d8" 
                  fill="#8884d8" 
                  fillOpacity={0.3}
                />
                <Area 
                  type="monotone" 
                  dataKey="leads" 
                  stackId="1" 
                  stroke="#82ca9d" 
                  fill="#82ca9d" 
                  fillOpacity={0.3}
                />
                <Area 
                  type="monotone" 
                  dataKey="conversions" 
                  stackId="1" 
                  stroke="#ffc658" 
                  fill="#ffc658" 
                  fillOpacity={0.3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Lead Sources */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="w-5 h-5" />
              Lead Sources
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <RechartsPieChart>
                <Tooltip />
                <Legend />
                <Cell dataKey="value" nameKey="name">
                  {data.leadSources.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Cell>
              </RechartsPieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Agent Performance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Agent Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <RechartsBarChart data={data.agentPerformance}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="calls" fill="#8884d8" name="Total Calls" />
                <Bar dataKey="conversions" fill="#82ca9d" name="Conversions" />
              </RechartsBarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Revenue vs Target */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Revenue vs Target
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <RechartsLineChart data={data.revenueData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={(value) => `$${value / 1000}k`} />
                <Tooltip formatter={(value) => formatCurrency(value as number)} />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="revenue" 
                  stroke="#82ca9d" 
                  strokeWidth={3}
                  name="Actual Revenue"
                />
                <Line 
                  type="monotone" 
                  dataKey="target" 
                  stroke="#8884d8" 
                  strokeDasharray="5 5"
                  name="Target"
                />
              </RechartsLineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Conversion Funnel */}
        <Card>
          <CardHeader>
            <CardTitle>Conversion Funnel</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data.conversionFunnel.map((stage, index) => {
                const nextStage = data.conversionFunnel[index + 1]
                const dropOffRate = nextStage 
                  ? ((stage.count - nextStage.count) / stage.count * 100).toFixed(1)
                  : 0
                
                return (
                  <div key={stage.stage} className="relative">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">{stage.stage}</span>
                      <div className="flex items-center gap-4">
                        <span className="text-2xl font-bold">{formatNumber(stage.count)}</span>
                        <span className="text-sm text-muted-foreground">
                          {stage.percentage}%
                        </span>
                      </div>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-blue-500 to-green-500 transition-all duration-500"
                        style={{ width: `${stage.percentage}%` }}
                      />
                    </div>
                    {nextStage && (
                      <div className="text-xs text-red-600 mt-1">
                        {dropOffRate}% drop-off to next stage
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* Agent Leaderboard */}
        <Card>
          <CardHeader>
            <CardTitle>Agent Leaderboard</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data.agentPerformance
                .sort((a, b) => (b.conversions / b.calls) - (a.conversions / a.calls))
                .map((agent, index) => {
                  const conversionRate = (agent.conversions / agent.calls * 100).toFixed(1)
                  return (
                    <div key={agent.name} className="flex items-center gap-4 p-3 border rounded-lg">
                      <div className={cn(
                        'w-8 h-8 rounded-full flex items-center justify-center text-white font-bold',
                        index === 0 ? 'bg-yellow-500' :
                        index === 1 ? 'bg-gray-400' :
                        index === 2 ? 'bg-orange-500' :
                        'bg-blue-500'
                      )}>
                        {index + 1}
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold">{agent.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {formatNumber(agent.conversions)} conversions • {conversionRate}% rate
                        </p>
                      </div>
                      <div className="flex items-center gap-1">
                        <Star className="w-4 h-4 text-yellow-500" />
                        <span className="font-semibold">{agent.rating}</span>
                      </div>
                    </div>
                  )
                })
              }
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Customer Satisfaction Trend */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Star className="w-5 h-5" />
            Customer Satisfaction Trend
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <RechartsLineChart data={data.customerSatisfaction}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" />
              <YAxis domain={[4.0, 5.0]} />
              <Tooltip />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="satisfaction" 
                stroke="#ffc658" 
                strokeWidth={3}
                name="Avg Rating"
              />
            </RechartsLineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}

export default AnalyticsDashboard