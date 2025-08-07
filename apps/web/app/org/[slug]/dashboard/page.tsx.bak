"use client"

import * as React from "react"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts'
import { Phone, Users, TrendingUp, MessageSquare, PhoneCall, User, Clock, CheckCircle } from "lucide-react"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { VoiceStatusIndicator, VoiceControls } from "@/components/ui/voice-status"
import { DataTable } from "@/components/ui/data-table"
import { ProtectedAppLayout } from "@/components/layout/app-layout"
import { useVoiceStore } from "@/lib/stores/voice-store"
import { useLeadsStore } from "@/lib/stores/leads-store"
import { useOrganizationContext } from "@/components/layout/organization-switcher"
import { formatCurrency, formatNumber, formatPercentage } from "@/lib/utils"
import type { Lead, VoiceAgent, DashboardMetrics } from "@/types"

// Mock data for demonstration
const mockMetrics: DashboardMetrics = {
  totalLeads: 1247,
  qualifiedLeads: 892,
  conversionRate: 0.715,
  averageResponseTime: 2.3,
  activeAgents: 3,
  totalCallTime: 45600, // seconds
  revenueGenerated: 125000,
  appointmentsScheduled: 234
}

const mockRecentCalls = [
  { time: '2m ago', lead: 'Sarah Johnson', duration: '4:32', outcome: 'Qualified', agent: 'Alex' },
  { time: '5m ago', lead: 'Mike Chen', duration: '2:15', outcome: 'Follow-up', agent: 'Alex' },
  { time: '8m ago', lead: 'Lisa Rodriguez', duration: '6:45', outcome: 'Qualified', agent: 'Emma' },
  { time: '12m ago', lead: 'David Kim', duration: '3:20', outcome: 'Not Interested', agent: 'Alex' },
  { time: '15m ago', lead: 'Anna Wilson', duration: '5:10', outcome: 'Qualified', agent: 'Emma' },
]

const mockPerformanceData = [
  { name: 'Mon', calls: 45, qualified: 32, appointments: 18 },
  { name: 'Tue', calls: 52, qualified: 38, appointments: 22 },
  { name: 'Wed', calls: 48, qualified: 35, appointments: 19 },
  { name: 'Thu', calls: 61, qualified: 44, appointments: 28 },
  { name: 'Fri', calls: 55, qualified: 41, appointments: 25 },
  { name: 'Sat', calls: 38, qualified: 25, appointments: 15 },
  { name: 'Sun', calls: 31, qualified: 20, appointments: 12 },
]

const mockAgentData = [
  { name: 'Alex Rodriguez', status: 'active', calls: 156, qualified: 112, conversion: 0.72 },
  { name: 'Emma Thompson', status: 'active', calls: 143, qualified: 98, conversion: 0.69 },
  { name: 'David Kim', status: 'idle', calls: 89, qualified: 67, conversion: 0.75 },
]

export default function DashboardPage() {
  const { agents, isRecording, connectionStatus, startRecording, stopRecording } = useVoiceStore()
  const { getLeadStats } = useLeadsStore()
  const { organization, isAdmin } = useOrganizationContext()
  
  const leadStats = getLeadStats()
  const activeAgentsCount = agents.filter(agent => agent.status === 'active').length

  const handleToggleRecording = () => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  const MetricCard = ({ 
    title, 
    value, 
    description, 
    icon: Icon, 
    trend, 
    format = 'number'
  }: {
    title: string
    value: number
    description: string
    icon: React.ComponentType<{ className?: string }>
    trend?: number
    format?: 'number' | 'currency' | 'percentage' | 'duration'
  }) => {
    const formatValue = (val: number) => {
      switch (format) {
        case 'currency':
          return formatCurrency(val)
        case 'percentage':
          return formatPercentage(val)
        case 'duration':
          return `${Math.floor(val / 3600)}h ${Math.floor((val % 3600) / 60)}m`
        default:
          return formatNumber(val)
      }
    }

    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
          <Icon className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatValue(value)}</div>
          <div className="flex items-center space-x-2 text-xs text-muted-foreground">
            <span>{description}</span>
            {trend !== undefined && (
              <span className={trend > 0 ? "text-green-600" : trend < 0 ? "text-red-600" : ""}>
                {trend > 0 ? '+' : ''}{formatPercentage(trend)} from last week
              </span>
            )}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <ProtectedAppLayout>
      <div className="container-fluid section-spacing">
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back to {organization?.name}. Here's what's happening with your voice agents.
          </p>
        </div>

        {/* Metrics Grid */}
        <div className="dashboard-grid dashboard-grid-4 mb-8">
          <MetricCard
            title="Total Leads"
            value={mockMetrics.totalLeads}
            description="New leads this month"
            icon={Users}
            trend={12.5}
          />
          <MetricCard
            title="Qualified Leads"
            value={mockMetrics.qualifiedLeads}
            description="Ready for follow-up"
            icon={CheckCircle}
            trend={8.2}
          />
          <MetricCard
            title="Conversion Rate"
            value={mockMetrics.conversionRate}
            description="Leads to appointments"
            icon={TrendingUp}
            trend={3.1}
            format="percentage"
          />
          <MetricCard
            title="Revenue Generated"
            value={mockMetrics.revenueGenerated}
            description="From converted leads"
            icon={TrendingUp}
            trend={15.7}
            format="currency"
          />
        </div>

        {/* Voice Agents Status */}
        <div className="dashboard-grid dashboard-grid-2 mb-8">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Phone className="h-5 w-5" />
                <span>Active Voice Agents</span>
              </CardTitle>
              <CardDescription>
                Real-time status of your voice agents
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {mockAgentData.map((agent, index) => (
                <div key={agent.name} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <VoiceStatusIndicator 
                      status={agent.status === 'active' ? 'listening' : 'idle'} 
                      size="sm" 
                    />
                    <div>
                      <p className="font-medium">{agent.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {agent.calls} calls • {formatPercentage(agent.conversion)} conversion
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">{agent.qualified} qualified</p>
                    <p className="text-xs text-muted-foreground capitalize">{agent.status}</p>
                  </div>
                </div>
              ))}
              
              {isAdmin && (
                <div className="pt-4 border-t">
                  <VoiceControls
                    isRecording={isRecording}
                    onToggleRecording={handleToggleRecording}
                    disabled={connectionStatus !== 'connected'}
                  />
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Calls</CardTitle>
              <CardDescription>
                Latest voice agent interactions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockRecentCalls.map((call, index) => (
                  <div key={index} className="flex items-center justify-between py-2 border-b last:border-0">
                    <div className="flex items-center space-x-3">
                      <div className="w-2 h-2 bg-green-500 rounded-full" />
                      <div>
                        <p className="font-medium text-sm">{call.lead}</p>
                        <p className="text-xs text-muted-foreground">
                          {call.agent} • {call.time}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm">{call.duration}</p>
                      <p className={`text-xs ${
                        call.outcome === 'Qualified' ? 'text-green-600' :
                        call.outcome === 'Follow-up' ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {call.outcome}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
              <Button variant="outline" className="w-full mt-4">
                View All Calls
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Performance Charts */}
        <div className="dashboard-grid dashboard-grid-2 mb-8">
          <Card>
            <CardHeader>
              <CardTitle>Weekly Performance</CardTitle>
              <CardDescription>
                Calls, qualifications, and appointments over the past week
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={mockPerformanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="calls" fill="#3b82f6" name="Total Calls" />
                  <Bar dataKey="qualified" fill="#10b981" name="Qualified" />
                  <Bar dataKey="appointments" fill="#f59e0b" name="Appointments" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Conversion Trends</CardTitle>
              <CardDescription>
                Lead qualification and conversion rates over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={mockPerformanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="qualified" 
                    stroke="#10b981" 
                    strokeWidth={2}
                    name="Qualified Leads"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="appointments" 
                    stroke="#f59e0b" 
                    strokeWidth={2}
                    name="Appointments"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>
              Common tasks and shortcuts for managing your voice agents
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Button variant="outline" className="h-20 flex-col space-y-2">
                <Phone className="h-6 w-6" />
                <span>Start Call</span>
              </Button>
              <Button variant="outline" className="h-20 flex-col space-y-2">
                <Users className="h-6 w-6" />
                <span>View Leads</span>
              </Button>
              <Button variant="outline" className="h-20 flex-col space-y-2">
                <MessageSquare className="h-6 w-6" />
                <span>Conversations</span>
              </Button>
              <Button variant="outline" className="h-20 flex-col space-y-2">
                <BarChart className="h-6 w-6" />
                <span>Analytics</span>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </ProtectedAppLayout>
  )
}