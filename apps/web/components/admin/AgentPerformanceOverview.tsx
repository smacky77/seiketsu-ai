'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  User, 
  TrendingUp, 
  TrendingDown, 
  Phone, 
  Target, 
  Clock,
  Star,
  MoreVertical,
  Filter,
  Search
} from 'lucide-react'

interface Agent {
  id: string
  name: string
  avatar: string
  status: 'online' | 'busy' | 'offline'
  calls: {
    today: number
    trend: 'up' | 'down' | 'stable'
    change: number
  }
  conversion: {
    rate: number
    trend: 'up' | 'down' | 'stable'
    change: number
  }
  avgCallTime: string
  rating: number
  totalLeads: number
}

const mockAgents: Agent[] = [
  {
    id: '1',
    name: 'Sarah Johnson',
    avatar: 'SJ',
    status: 'online',
    calls: { today: 23, trend: 'up', change: 15 },
    conversion: { rate: 42.3, trend: 'up', change: 5.2 },
    avgCallTime: '4:32',
    rating: 4.9,
    totalLeads: 156
  },
  {
    id: '2',
    name: 'Michael Chen',
    avatar: 'MC',
    status: 'busy',
    calls: { today: 18, trend: 'stable', change: 0 },
    conversion: { rate: 38.7, trend: 'down', change: -2.1 },
    avgCallTime: '5:15',
    rating: 4.7,
    totalLeads: 134
  },
  {
    id: '3',
    name: 'Emily Rodriguez',
    avatar: 'ER',
    status: 'online',
    calls: { today: 31, trend: 'up', change: 22 },
    conversion: { rate: 45.8, trend: 'up', change: 8.3 },
    avgCallTime: '3:48',
    rating: 4.8,
    totalLeads: 189
  },
  {
    id: '4',
    name: 'David Park',
    avatar: 'DP',
    status: 'offline',
    calls: { today: 12, trend: 'down', change: -8 },
    conversion: { rate: 29.1, trend: 'down', change: -4.5 },
    avgCallTime: '6:02',
    rating: 4.4,
    totalLeads: 98
  },
  {
    id: '5',
    name: 'Jessica Taylor',
    avatar: 'JT',
    status: 'online',
    calls: { today: 27, trend: 'up', change: 12 },
    conversion: { rate: 41.2, trend: 'stable', change: 0.8 },
    avgCallTime: '4:55',
    rating: 4.6,
    totalLeads: 167
  }
]

const getStatusColor = (status: string) => {
  switch (status) {
    case 'online':
      return 'bg-green-500'
    case 'busy':
      return 'bg-yellow-500'
    case 'offline':
      return 'bg-gray-400'
    default:
      return 'bg-gray-400'
  }
}

const getTrendIcon = (trend: string, size = 4) => {
  if (trend === 'up') return <TrendingUp className={`w-${size} h-${size} text-green-500`} />
  if (trend === 'down') return <TrendingDown className={`w-${size} h-${size} text-red-500`} />
  return null
}

export function AgentPerformanceOverview() {
  const [sortBy, setSortBy] = useState<'calls' | 'conversion' | 'rating'>('conversion')
  const [filterStatus, setFilterStatus] = useState<'all' | 'online' | 'busy' | 'offline'>('all')

  const filteredAgents = mockAgents
    .filter(agent => filterStatus === 'all' || agent.status === filterStatus)
    .sort((a, b) => {
      switch (sortBy) {
        case 'calls':
          return b.calls.today - a.calls.today
        case 'conversion':
          return b.conversion.rate - a.conversion.rate
        case 'rating':
          return b.rating - a.rating
        default:
          return 0
      }
    })

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold">Agent Performance</h2>
          <p className="text-sm text-muted-foreground">Real-time agent activity and metrics</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="text-sm bg-muted border border-border rounded px-3 py-1"
          >
            <option value="conversion">Sort by Conversion</option>
            <option value="calls">Sort by Calls</option>
            <option value="rating">Sort by Rating</option>
          </select>
          <button className="btn btn-secondary text-sm">
            <Filter className="w-4 h-4 mr-1" />
            Filter
          </button>
        </div>
      </div>

      {/* Performance Summary */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-muted rounded-lg p-4">
          <div className="flex items-center gap-2 mb-1">
            <User className="w-4 h-4 text-blue-500" />
            <span className="text-sm font-medium">Active Agents</span>
          </div>
          <div className="text-xl font-bold">
            {mockAgents.filter(a => a.status !== 'offline').length}
          </div>
          <div className="text-xs text-muted-foreground">
            of {mockAgents.length} total
          </div>
        </div>

        <div className="bg-muted rounded-lg p-4">
          <div className="flex items-center gap-2 mb-1">
            <Phone className="w-4 h-4 text-green-500" />
            <span className="text-sm font-medium">Total Calls</span>
          </div>
          <div className="text-xl font-bold">
            {mockAgents.reduce((sum, agent) => sum + agent.calls.today, 0)}
          </div>
          <div className="text-xs text-muted-foreground">today</div>
        </div>

        <div className="bg-muted rounded-lg p-4">
          <div className="flex items-center gap-2 mb-1">
            <Target className="w-4 h-4 text-purple-500" />
            <span className="text-sm font-medium">Avg Conversion</span>
          </div>
          <div className="text-xl font-bold">
            {(mockAgents.reduce((sum, agent) => sum + agent.conversion.rate, 0) / mockAgents.length).toFixed(1)}%
          </div>
          <div className="text-xs text-muted-foreground">across all agents</div>
        </div>
      </div>

      {/* Agent List */}
      <div className="space-y-3">
        {filteredAgents.map((agent, index) => (
          <motion.div
            key={agent.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="bg-muted rounded-lg p-4 hover:bg-accent transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {/* Agent Avatar */}
                <div className="relative">
                  <div className="w-10 h-10 bg-background rounded-full flex items-center justify-center border border-border">
                    <span className="text-sm font-medium">{agent.avatar}</span>
                  </div>
                  <div className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-white ${getStatusColor(agent.status)}`} />
                </div>

                {/* Agent Info */}
                <div>
                  <div className="font-medium">{agent.name}</div>
                  <div className="flex items-center gap-3 text-sm text-muted-foreground">
                    <span className="capitalize">{agent.status}</span>
                    <span>•</span>
                    <div className="flex items-center gap-1">
                      <Star className="w-3 h-3 text-yellow-500 fill-current" />
                      <span>{agent.rating}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Performance Metrics */}
              <div className="flex items-center gap-6 text-sm">
                <div className="text-center">
                  <div className="flex items-center gap-1 mb-1">
                    <span className="font-medium">{agent.calls.today}</span>
                    {getTrendIcon(agent.calls.trend, 3)}
                  </div>
                  <div className="text-xs text-muted-foreground">Calls</div>
                </div>

                <div className="text-center">
                  <div className="flex items-center gap-1 mb-1">
                    <span className="font-medium">{agent.conversion.rate}%</span>
                    {getTrendIcon(agent.conversion.trend, 3)}
                  </div>
                  <div className="text-xs text-muted-foreground">Conversion</div>
                </div>

                <div className="text-center">
                  <div className="font-medium mb-1">{agent.avgCallTime}</div>
                  <div className="text-xs text-muted-foreground">Avg Time</div>
                </div>

                <div className="text-center">
                  <div className="font-medium mb-1">{agent.totalLeads}</div>
                  <div className="text-xs text-muted-foreground">Total Leads</div>
                </div>

                <button className="p-1 text-muted-foreground hover:text-foreground">
                  <MoreVertical className="w-4 h-4" />
                </button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* View All Button */}
      <div className="mt-6 text-center">
        <button className="btn btn-secondary">
          View All Agents
        </button>
      </div>
    </div>
  )
}