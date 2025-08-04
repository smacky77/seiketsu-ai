'use client'

import { motion } from 'framer-motion'
import { 
  Users, 
  Phone, 
  TrendingUp, 
  AlertTriangle,
  CheckCircle,
  Clock,
  DollarSign,
  Target,
  Activity,
  BarChart3,
  PieChart,
  Filter
} from 'lucide-react'
import { SystemHealthMonitor } from './SystemHealthMonitor'
import { AgentPerformanceOverview } from './AgentPerformanceOverview'
import { LeadPipelineView } from './LeadPipelineView'

interface MetricCard {
  title: string
  value: string
  change: string
  trend: 'up' | 'down' | 'stable'
  icon: any
  color: 'green' | 'blue' | 'yellow' | 'red' | 'gray'
}

const metrics: MetricCard[] = [
  {
    title: 'Total Agents',
    value: '25',
    change: '+3 this month',
    trend: 'up',
    icon: Users,
    color: 'blue'
  },
  {
    title: 'Active Conversations',
    value: '12',
    change: '+8 since yesterday',
    trend: 'up',
    icon: Phone,
    color: 'green'
  },
  {
    title: 'Lead Conversion Rate',
    value: '34.2%',
    change: '+2.4% vs last month',
    trend: 'up',
    icon: Target,
    color: 'green'
  },
  {
    title: 'Monthly Revenue',
    value: '$28,450',
    change: '+15.3% vs last month',
    trend: 'up',
    icon: DollarSign,
    color: 'green'
  },
  {
    title: 'System Uptime',
    value: '99.97%',
    change: 'Last 30 days',
    trend: 'stable',
    icon: Activity,
    color: 'green'
  },
  {
    title: 'Avg Response Time',
    value: '1.2s',
    change: '-0.3s vs last week',
    trend: 'up',
    icon: Clock,
    color: 'green'
  }
]

const recentAlerts = [
  {
    id: 1,
    type: 'warning',
    message: 'Agent Sarah Johnson exceeded daily call limit',
    time: '2 minutes ago',
    action: 'Adjust limits'
  },
  {
    id: 2,
    type: 'info',
    message: 'New integration request from Zillow API',
    time: '15 minutes ago',
    action: 'Review'
  },
  {
    id: 3,
    type: 'success',
    message: 'System backup completed successfully',
    time: '1 hour ago',
    action: 'View details'
  }
]

function MetricCardComponent({ metric }: { metric: MetricCard }) {
  const getColorClasses = (color: string) => {
    switch (color) {
      case 'green':
        return 'bg-green-50 text-green-600 border-green-200'
      case 'blue':
        return 'bg-blue-50 text-blue-600 border-blue-200'
      case 'yellow':
        return 'bg-yellow-50 text-yellow-600 border-yellow-200'
      case 'red':
        return 'bg-red-50 text-red-600 border-red-200'
      default:
        return 'bg-muted text-muted-foreground border-border'
    }
  }

  const getTrendIcon = () => {
    if (metric.trend === 'up') return <TrendingUp className="w-4 h-4 text-green-500" />
    if (metric.trend === 'down') return <TrendingUp className="w-4 h-4 text-red-500 rotate-180" />
    return <div className="w-4 h-4" />
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <div className={`w-12 h-12 rounded-lg border flex items-center justify-center ${getColorClasses(metric.color)}`}>
          <metric.icon className="w-6 h-6" />
        </div>
        {getTrendIcon()}
      </div>
      <div className="space-y-1">
        <h3 className="text-2xl font-bold">{metric.value}</h3>
        <p className="text-sm font-medium text-muted-foreground">{metric.title}</p>
        <p className="text-xs text-muted-foreground">{metric.change}</p>
      </div>
    </motion.div>
  )
}

export function SystemOverviewDashboard() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">System Overview</h1>
          <p className="text-muted-foreground">Monitor your agency's performance and system health</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="btn btn-secondary">
            <Filter className="w-4 h-4 mr-2" />
            Filters
          </button>
          <button className="btn btn-secondary">
            <BarChart3 className="w-4 h-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
        {metrics.map((metric, index) => (
          <MetricCardComponent key={metric.title} metric={metric} />
        ))}
      </div>

      {/* Main Dashboard Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System Health Monitor - Takes 2 columns */}
        <div className="lg:col-span-2">
          <SystemHealthMonitor />
        </div>

        {/* Recent Alerts */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold">Recent Alerts</h2>
            <button className="text-sm text-muted-foreground hover:text-foreground">
              View all
            </button>
          </div>
          
          <div className="space-y-4">
            {recentAlerts.map((alert) => (
              <div key={alert.id} className="flex items-start gap-3 p-3 rounded-lg bg-muted">
                <div className="flex-shrink-0 mt-1">
                  {alert.type === 'warning' && (
                    <AlertTriangle className="w-4 h-4 text-yellow-500" />
                  )}
                  {alert.type === 'info' && (
                    <Clock className="w-4 h-4 text-blue-500" />
                  )}
                  {alert.type === 'success' && (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground">{alert.message}</p>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-xs text-muted-foreground">{alert.time}</span>
                    <button className="text-xs text-blue-600 hover:text-blue-700 font-medium">
                      {alert.action}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Secondary Dashboard Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Performance Overview */}
        <AgentPerformanceOverview />
        
        {/* Lead Pipeline View */}
        <LeadPipelineView />
      </div>
    </div>
  )
}