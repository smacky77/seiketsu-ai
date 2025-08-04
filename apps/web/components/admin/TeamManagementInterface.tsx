'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Plus, 
  Search, 
  Filter, 
  MoreVertical,
  User,
  Shield,
  Settings,
  Mail,
  Phone,
  Calendar,
  TrendingUp,
  TrendingDown,
  Award,
  Edit,
  Trash2,
  Eye,
  UserPlus
} from 'lucide-react'
import { UserPermissionManager } from './UserPermissionManager'

interface Agent {
  id: string
  name: string
  email: string
  phone: string
  avatar: string
  role: 'agent' | 'senior_agent' | 'team_lead' | 'manager'
  status: 'active' | 'inactive' | 'pending'
  dateJoined: string
  lastActive: string
  performance: {
    callsToday: number
    callsThisMonth: number
    conversionRate: number
    avgCallTime: string
    satisfactionScore: number
    leadsGenerated: number
  }
  permissions: string[]
  territory: string
  supervisor?: string
}

const mockAgents: Agent[] = [
  {
    id: '1',
    name: 'Sarah Johnson',
    email: 'sarah.johnson@email.com',
    phone: '+1 (555) 123-4567',
    avatar: 'SJ',
    role: 'team_lead',
    status: 'active',
    dateJoined: '2024-01-15',
    lastActive: '5 minutes ago',
    performance: {
      callsToday: 23,
      callsThisMonth: 456,
      conversionRate: 42.3,
      avgCallTime: '4:32',
      satisfactionScore: 4.9,
      leadsGenerated: 89
    },
    permissions: ['view_all_leads', 'manage_team', 'access_reports', 'voice_config'],
    territory: 'North District'
  },
  {
    id: '2',
    name: 'Michael Chen',
    email: 'michael.chen@email.com',
    phone: '+1 (555) 234-5678',
    avatar: 'MC',
    role: 'senior_agent',
    status: 'active',
    dateJoined: '2024-02-03',
    lastActive: '2 hours ago',
    performance: {
      callsToday: 18,
      callsThisMonth: 378,
      conversionRate: 38.7,
      avgCallTime: '5:15',
      satisfactionScore: 4.7,
      leadsGenerated: 67
    },
    permissions: ['view_own_leads', 'access_basic_reports', 'voice_config'],
    territory: 'Downtown'
  },
  {
    id: '3',
    name: 'Emily Rodriguez',
    email: 'emily.rodriguez@email.com',
    phone: '+1 (555) 345-6789',
    avatar: 'ER',
    role: 'agent',
    status: 'active',
    dateJoined: '2024-03-10',
    lastActive: '1 hour ago',
    performance: {
      callsToday: 31,
      callsThisMonth: 523,
      conversionRate: 45.8,
      avgCallTime: '3:48',
      satisfactionScore: 4.8,
      leadsGenerated: 102
    },
    permissions: ['view_own_leads', 'voice_config'],
    territory: 'South District'
  },
  {
    id: '4',
    name: 'David Park',
    email: 'david.park@email.com',
    phone: '+1 (555) 456-7890',
    avatar: 'DP',
    role: 'agent',
    status: 'inactive',
    dateJoined: '2024-01-28',
    lastActive: '3 days ago',
    performance: {
      callsToday: 0,
      callsThisMonth: 234,
      conversionRate: 29.1,
      avgCallTime: '6:02',
      satisfactionScore: 4.4,
      leadsGenerated: 45
    },
    permissions: ['view_own_leads'],
    territory: 'East District'
  }
]

const getRoleColor = (role: string) => {
  switch (role) {
    case 'manager':
      return 'bg-purple-100 text-purple-800 border-purple-200'
    case 'team_lead':
      return 'bg-blue-100 text-blue-800 border-blue-200'
    case 'senior_agent':
      return 'bg-green-100 text-green-800 border-green-200'
    case 'agent':
      return 'bg-gray-100 text-gray-800 border-gray-200'
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200'
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'active':
      return 'bg-green-500'
    case 'inactive':
      return 'bg-gray-400'
    case 'pending':
      return 'bg-yellow-500'
    default:
      return 'bg-gray-400'
  }
}

export function TeamManagementInterface() {
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [showPermissions, setShowPermissions] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterRole, setFilterRole] = useState<string>('all')
  const [filterStatus, setFilterStatus] = useState<string>('all')

  const filteredAgents = mockAgents.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         agent.email.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesRole = filterRole === 'all' || agent.role === filterRole
    const matchesStatus = filterStatus === 'all' || agent.status === filterStatus
    return matchesSearch && matchesRole && matchesStatus
  })

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Team Management</h1>
          <p className="text-muted-foreground">
            Manage your agents, roles, and permissions
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => setShowPermissions(!showPermissions)}
            className="btn btn-secondary"
          >
            <Shield className="w-4 h-4 mr-2" />
            Permissions
          </button>
          <button className="btn btn-primary">
            <UserPlus className="w-4 h-4 mr-2" />
            Add Agent
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="card p-6">
        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search agents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-muted border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
            />
          </div>
          
          <select
            value={filterRole}
            onChange={(e) => setFilterRole(e.target.value)}
            className="px-3 py-2 bg-muted border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
          >
            <option value="all">All Roles</option>
            <option value="manager">Manager</option>
            <option value="team_lead">Team Lead</option>
            <option value="senior_agent">Senior Agent</option>
            <option value="agent">Agent</option>
          </select>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 bg-muted border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="pending">Pending</option>
          </select>

          <button className="btn btn-secondary">
            <Filter className="w-4 h-4 mr-2" />
            More Filters
          </button>
        </div>
      </div>

      {/* Team Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-2">
            <User className="w-5 h-5 text-blue-500" />
            <span className="font-medium">Total Agents</span>
          </div>
          <div className="text-2xl font-bold">{mockAgents.length}</div>
          <div className="text-sm text-muted-foreground">
            {mockAgents.filter(a => a.status === 'active').length} active
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp className="w-5 h-5 text-green-500" />
            <span className="font-medium">Avg Performance</span>
          </div>
          <div className="text-2xl font-bold">
            {(mockAgents.reduce((sum, agent) => sum + agent.performance.conversionRate, 0) / mockAgents.length).toFixed(1)}%
          </div>
          <div className="text-sm text-muted-foreground">conversion rate</div>
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-3 mb-2">
            <Phone className="w-5 h-5 text-purple-500" />
            <span className="font-medium">Calls Today</span>
          </div>
          <div className="text-2xl font-bold">
            {mockAgents.reduce((sum, agent) => sum + agent.performance.callsToday, 0)}
          </div>
          <div className="text-sm text-muted-foreground">across all agents</div>
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-3 mb-2">
            <Award className="w-5 h-5 text-yellow-500" />
            <span className="font-medium">Top Performer</span>
          </div>
          <div className="text-lg font-bold">Emily Rodriguez</div>
          <div className="text-sm text-muted-foreground">45.8% conversion</div>
        </div>
      </div>

      {/* Agents Table */}
      <div className="card">
        <div className="p-6 border-b border-border">
          <h2 className="text-lg font-semibold">Team Members</h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left p-4 font-medium text-muted-foreground">Agent</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Role</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Performance</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Territory</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Last Active</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredAgents.map((agent, index) => (
                <motion.tr
                  key={agent.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="border-b border-border hover:bg-muted/50"
                >
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="relative">
                        <div className="w-10 h-10 bg-muted rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium">{agent.avatar}</span>
                        </div>
                        <div className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-white ${getStatusColor(agent.status)}`} />
                      </div>
                      <div>
                        <div className="font-medium">{agent.name}</div>
                        <div className="text-sm text-muted-foreground">{agent.email}</div>
                      </div>
                    </div>
                  </td>
                  
                  <td className="p-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getRoleColor(agent.role)}`}>
                      {agent.role.replace('_', ' ')}
                    </span>
                  </td>
                  
                  <td className="p-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{agent.performance.conversionRate}%</span>
                        {agent.performance.conversionRate > 40 ? (
                          <TrendingUp className="w-3 h-3 text-green-500" />
                        ) : (
                          <TrendingDown className="w-3 h-3 text-red-500" />
                        )}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {agent.performance.callsToday} calls today
                      </div>
                    </div>
                  </td>
                  
                  <td className="p-4">
                    <span className="text-sm">{agent.territory}</span>
                  </td>
                  
                  <td className="p-4">
                    <span className="text-sm text-muted-foreground">{agent.lastActive}</span>
                  </td>
                  
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => setSelectedAgent(agent)}
                        className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg">
                        <Edit className="w-4 h-4" />
                      </button>
                      <button className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg">
                        <MoreVertical className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Permission Manager Modal/Panel */}
      {showPermissions && (
        <UserPermissionManager 
          onClose={() => setShowPermissions(false)}
        />
      )}

      {/* Agent Detail Modal */}
      {selectedAgent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-card rounded-lg shadow-lg max-w-2xl w-full max-h-[90vh] overflow-auto"
          >
            <div className="p-6 border-b border-border">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Agent Details</h2>
                <button 
                  onClick={() => setSelectedAgent(null)}
                  className="p-2 text-muted-foreground hover:text-foreground rounded-lg"
                >
                  ×
                </button>
              </div>
            </div>
            
            <div className="p-6 space-y-6">
              {/* Agent Info */}
              <div className="flex items-start gap-4">
                <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center">
                  <span className="text-lg font-medium">{selectedAgent.avatar}</span>
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-semibold">{selectedAgent.name}</h3>
                  <p className="text-muted-foreground">{selectedAgent.email}</p>
                  <p className="text-muted-foreground">{selectedAgent.phone}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getRoleColor(selectedAgent.role)}`}>
                      {selectedAgent.role.replace('_', ' ')}
                    </span>
                    <div className={`w-2 h-2 rounded-full ${getStatusColor(selectedAgent.status)}`} />
                    <span className="text-sm text-muted-foreground capitalize">{selectedAgent.status}</span>
                  </div>
                </div>
              </div>

              {/* Performance Metrics */}
              <div>
                <h4 className="font-medium mb-3">Performance Metrics</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-muted rounded-lg p-4">
                    <div className="text-sm text-muted-foreground">Conversion Rate</div>
                    <div className="text-2xl font-bold">{selectedAgent.performance.conversionRate}%</div>
                  </div>
                  <div className="bg-muted rounded-lg p-4">
                    <div className="text-sm text-muted-foreground">Calls This Month</div>
                    <div className="text-2xl font-bold">{selectedAgent.performance.callsThisMonth}</div>
                  </div>
                  <div className="bg-muted rounded-lg p-4">
                    <div className="text-sm text-muted-foreground">Avg Call Time</div>
                    <div className="text-2xl font-bold">{selectedAgent.performance.avgCallTime}</div>
                  </div>
                  <div className="bg-muted rounded-lg p-4">
                    <div className="text-sm text-muted-foreground">Satisfaction Score</div>
                    <div className="text-2xl font-bold">{selectedAgent.performance.satisfactionScore}</div>
                  </div>
                </div>
              </div>

              {/* Permissions */}
              <div>
                <h4 className="font-medium mb-3">Permissions</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedAgent.permissions.map((permission) => (
                    <span
                      key={permission}
                      className="inline-flex items-center px-3 py-1 rounded-full text-xs bg-accent text-accent-foreground"
                    >
                      {permission.replace('_', ' ')}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}