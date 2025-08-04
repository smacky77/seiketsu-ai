'use client'

import { motion } from 'framer-motion'
import { 
  Users, 
  UserCheck, 
  UserPlus, 
  UserX, 
  TrendingUp,
  Clock,
  DollarSign,
  Target,
  Filter,
  MoreHorizontal
} from 'lucide-react'

interface PipelineStage {
  name: string
  count: number
  value: number
  change: {
    count: number
    percentage: number
    trend: 'up' | 'down' | 'stable'
  }
  color: string
  icon: any
}

const pipelineStages: PipelineStage[] = [
  {
    name: 'New Leads',
    count: 127,
    value: 2540000,
    change: { count: 12, percentage: 10.4, trend: 'up' },
    color: 'bg-blue-500',
    icon: Users
  },
  {
    name: 'Qualified',
    count: 89,
    value: 1780000,
    change: { count: 8, percentage: 9.9, trend: 'up' },
    color: 'bg-yellow-500',
    icon: UserCheck
  },
  {
    name: 'In Progress',
    count: 45,
    value: 900000,
    change: { count: -3, percentage: -6.2, trend: 'down' },
    color: 'bg-purple-500',
    icon: UserPlus
  },
  {
    name: 'Closed Won',
    count: 23,
    value: 460000,
    change: { count: 5, percentage: 27.8, trend: 'up' },
    color: 'bg-green-500',
    icon: Target
  },
  {
    name: 'Closed Lost',
    count: 15,
    value: 300000,
    change: { count: -2, percentage: -11.8, trend: 'down' },
    color: 'bg-red-500',
    icon: UserX
  }
]

const recentActivity = [
  {
    id: 1,
    type: 'qualified',
    lead: 'Jennifer Martinez',
    agent: 'Sarah Johnson',
    value: '$450K',
    time: '5 minutes ago'
  },
  {
    id: 2,
    type: 'closed_won',
    lead: 'Robert Chen',
    agent: 'Michael Chen',
    value: '$750K',
    time: '1 hour ago'
  },
  {
    id: 3,
    type: 'new_lead',
    lead: 'Amanda Foster',
    agent: 'Emily Rodriguez',
    value: '$320K',
    time: '2 hours ago'
  },
  {
    id: 4,
    type: 'in_progress',
    lead: 'Thomas Wilson',
    agent: 'David Park',
    value: '$580K',
    time: '3 hours ago'
  }
]

const getActivityIcon = (type: string) => {
  switch (type) {
    case 'qualified':
      return <UserCheck className="w-4 h-4 text-yellow-500" />
    case 'closed_won':
      return <Target className="w-4 h-4 text-green-500" />
    case 'new_lead':
      return <Users className="w-4 h-4 text-blue-500" />
    case 'in_progress':
      return <UserPlus className="w-4 h-4 text-purple-500" />
    default:
      return <Clock className="w-4 h-4 text-gray-500" />
  }
}

const getActivityLabel = (type: string) => {
  switch (type) {
    case 'qualified':
      return 'Lead Qualified'
    case 'closed_won':
      return 'Deal Closed'
    case 'new_lead':
      return 'New Lead'
    case 'in_progress':
      return 'In Progress'
    default:
      return 'Activity'
  }
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

export function LeadPipelineView() {
  const totalValue = pipelineStages.reduce((sum, stage) => sum + stage.value, 0)
  const totalCount = pipelineStages.reduce((sum, stage) => sum + stage.count, 0)

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold">Lead Pipeline</h2>
          <p className="text-sm text-muted-foreground">
            {totalCount} leads • {formatCurrency(totalValue)} total value
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn btn-secondary text-sm">
            <Filter className="w-4 h-4 mr-1" />
            Filter
          </button>
          <button className="p-2 text-muted-foreground hover:text-foreground">
            <MoreHorizontal className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Pipeline Stages */}
      <div className="space-y-4 mb-6">
        {pipelineStages.map((stage, index) => (
          <motion.div
            key={stage.name}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-muted rounded-lg p-4"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 ${stage.color} rounded-lg flex items-center justify-center`}>
                  <stage.icon className="w-5 h-5 text-white" />
                </div>
                <div>
                  <div className="font-medium">{stage.name}</div>
                  <div className="text-sm text-muted-foreground">
                    {formatCurrency(stage.value)} potential value
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold">{stage.count}</div>
                <div className={`text-sm flex items-center gap-1 ${
                  stage.change.trend === 'up' ? 'text-green-600' : 
                  stage.change.trend === 'down' ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {stage.change.trend === 'up' && <TrendingUp className="w-3 h-3" />}
                  {stage.change.trend === 'down' && <TrendingUp className="w-3 h-3 rotate-180" />}
                  {stage.change.count > 0 ? '+' : ''}{stage.change.count}
                </div>
              </div>
            </div>

            {/* Progress bar showing percentage of total pipeline */}
            <div className="h-2 bg-background rounded-full overflow-hidden">
              <div
                className={`h-full ${stage.color} transition-all duration-500`}
                style={{ width: `${(stage.count / totalCount) * 100}%` }}
              />
            </div>
            <div className="flex justify-between items-center mt-2 text-xs text-muted-foreground">
              <span>{((stage.count / totalCount) * 100).toFixed(1)}% of total pipeline</span>
              <span>
                {stage.change.percentage > 0 ? '+' : ''}{stage.change.percentage.toFixed(1)}% vs last month
              </span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Recent Activity */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium">Recent Activity</h3>
          <button className="text-sm text-muted-foreground hover:text-foreground">
            View all
          </button>
        </div>
        
        <div className="space-y-3">
          {recentActivity.map((activity, index) => (
            <motion.div
              key={activity.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="flex items-center gap-3 p-3 bg-background rounded-lg border border-border"
            >
              {getActivityIcon(activity.type)}
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm">{getActivityLabel(activity.type)}</span>
                  <span className="text-muted-foreground">•</span>
                  <span className="text-sm text-muted-foreground">{activity.lead}</span>
                </div>
                <div className="text-xs text-muted-foreground">
                  by {activity.agent} • {activity.time}
                </div>
              </div>
              <div className="text-sm font-medium text-green-600">
                {activity.value}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}