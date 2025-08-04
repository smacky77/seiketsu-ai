'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  BarChart3, 
  TrendingUp, 
  TrendingDown,
  Phone,
  Users,
  Star,
  Target,
  Clock,
  ArrowUp,
  ArrowDown,
  MoreHorizontal
} from 'lucide-react'

interface MetricData {
  label: string
  value: string
  change: number
  trend: 'up' | 'down' | 'neutral'
  icon: React.ReactNode
  color: string
}

interface DailyGoal {
  label: string
  current: number
  target: number
  unit: string
}

export function PerformanceMetrics() {
  const [timeRange, setTimeRange] = useState<'today' | 'week' | 'month'>('today')

  const metrics: MetricData[] = [
    {
      label: 'Calls Handled',
      value: '23',
      change: 12,
      trend: 'up',
      icon: <Phone className="w-4 h-4" />,
      color: 'text-blue-500'
    },
    {
      label: 'Leads Qualified',
      value: '8',
      change: 25,
      trend: 'up',
      icon: <Users className="w-4 h-4" />,
      color: 'text-green-500'
    },
    {
      label: 'Avg Call Duration',
      value: '4:32',
      change: -8,
      trend: 'down',
      icon: <Clock className="w-4 h-4" />,
      color: 'text-yellow-500'
    },
    {
      label: 'Quality Score',
      value: '94%',
      change: 3,
      trend: 'up',
      icon: <Star className="w-4 h-4" />,
      color: 'text-purple-500'
    }
  ]

  const dailyGoals: DailyGoal[] = [
    { label: 'Calls', current: 23, target: 30, unit: 'calls' },
    { label: 'Qualified Leads', current: 8, target: 10, unit: 'leads' },
    { label: 'Appointments', current: 3, target: 5, unit: 'meetings' }
  ]

  const getTrendIcon = (trend: string) => {
    if (trend === 'up') return <ArrowUp className="w-3 h-3 text-green-500" />
    if (trend === 'down') return <ArrowDown className="w-3 h-3 text-red-500" />
    return null
  }

  const getTrendColor = (trend: string, change: number) => {
    if (trend === 'up') return 'text-green-500'
    if (trend === 'down') return 'text-red-500'
    return 'text-muted-foreground'
  }

  const getProgressColor = (current: number, target: number) => {
    const percentage = (current / target) * 100
    if (percentage >= 100) return 'bg-green-500'
    if (percentage >= 80) return 'bg-blue-500'
    if (percentage >= 60) return 'bg-yellow-500'
    return 'bg-muted-foreground'
  }

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold">Performance</h2>
        <div className="flex items-center gap-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="text-sm bg-muted border-0 rounded-lg px-3 py-1 focus:outline-none focus:ring-2 focus:ring-foreground"
          >
            <option value="today">Today</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
          </select>
          <button className="p-1 text-muted-foreground hover:text-foreground">
            <MoreHorizontal className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 gap-4 mb-6">
        {metrics.map((metric, index) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="p-4 bg-muted rounded-lg"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg bg-background ${metric.color}`}>
                  {metric.icon}
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{metric.label}</p>
                  <p className="text-lg font-semibold">{metric.value}</p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                {getTrendIcon(metric.trend)}
                <span className={`text-sm font-medium ${getTrendColor(metric.trend, metric.change)}`}>
                  {Math.abs(metric.change)}%
                </span>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Daily Goals */}
      <div className="mb-6">
        <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
          <Target className="w-4 h-4" />
          Daily Goals
        </h3>
        <div className="space-y-4">
          {dailyGoals.map((goal, index) => {
            const percentage = Math.min((goal.current / goal.target) * 100, 100)
            return (
              <motion.div
                key={goal.label}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">{goal.label}</span>
                  <span className="text-sm text-muted-foreground">
                    {goal.current} / {goal.target} {goal.unit}
                  </span>
                </div>
                <div className="w-full bg-background rounded-full h-2">
                  <motion.div
                    className={`h-full rounded-full ${getProgressColor(goal.current, goal.target)}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ duration: 0.8, delay: index * 0.1 }}
                  />
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  {percentage >= 100 ? 'Goal achieved!' : `${Math.round(percentage)}% complete`}
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-3 bg-muted rounded-lg text-center">
          <div className="text-lg font-bold text-green-500">94%</div>
          <div className="text-xs text-muted-foreground">Success Rate</div>
        </div>
        <div className="p-3 bg-muted rounded-lg text-center">
          <div className="text-lg font-bold text-blue-500">2.3x</div>
          <div className="text-xs text-muted-foreground">Efficiency Gain</div>
        </div>
      </div>

      {/* Performance Insight */}
      <div className="mt-6 p-4 bg-accent rounded-lg">
        <div className="flex items-start gap-3">
          <TrendingUp className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-foreground">
              Outstanding Performance Today
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              You're 25% above your weekly average for lead qualification. 
              Keep up the great work!
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}