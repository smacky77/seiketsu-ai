'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Bell, 
  Settings,
  X,
  Filter,
  Search,
  AlertCircle,
  Info,
  Zap,
  Mail,
  MessageSquare,
  Phone
} from 'lucide-react'

interface Alert {
  id: string
  title: string
  description: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  status: 'active' | 'acknowledged' | 'resolved'
  service: string
  timestamp: Date
  acknowledged_by?: string
  resolved_at?: Date
  tags: string[]
}

interface IncidentResponse {
  id: string
  title: string
  status: 'investigating' | 'identified' | 'monitoring' | 'resolved'
  priority: 'p1' | 'p2' | 'p3' | 'p4'
  created_at: Date
  assigned_to: string
  affected_services: string[]
  estimated_resolution?: Date
}

interface NotificationRule {
  id: string
  name: string
  conditions: string
  channels: ('email' | 'sms' | 'slack' | 'webhook')[]
  active: boolean
  recipients: string[]
}

export function AlertManagementPanel() {
  const [selectedAlerts, setSelectedAlerts] = useState<string[]>([])
  const [filterSeverity, setFilterSeverity] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState('')

  const alerts: Alert[] = [
    {
      id: '1',
      title: 'High Memory Usage on Market Intelligence Service',
      description: 'Memory usage exceeded 85% threshold for 5 minutes',
      severity: 'high',
      status: 'active',
      service: 'market-intelligence-api',
      timestamp: new Date(Date.now() - 300000),
      tags: ['performance', 'memory', 'threshold']
    },
    {
      id: '2',
      title: 'Scheduling API Response Time Degraded',
      description: 'Average response time increased to 340ms (threshold: 200ms)',
      severity: 'medium',
      status: 'acknowledged',
      service: 'scheduling-api',
      timestamp: new Date(Date.now() - 900000),
      acknowledged_by: 'john.doe@seiketsu.ai',
      tags: ['performance', 'latency', 'api']
    },
    {
      id: '3',
      title: 'Failed Communication Workflow',
      description: 'Email campaign "New Listing Alerts" failed to send to 47 recipients',
      severity: 'medium',
      status: 'active',
      service: 'communication-service',
      timestamp: new Date(Date.now() - 600000),
      tags: ['communication', 'email', 'failure']
    },
    {
      id: '4',
      title: 'Database Connection Pool Exhausted',
      description: 'All 100 database connections are in use, new requests queuing',
      severity: 'critical',
      status: 'active',
      service: 'database-cluster',
      timestamp: new Date(Date.now() - 180000),
      tags: ['database', 'connections', 'critical']
    },
    {
      id: '5',
      title: 'Property Prediction Model Accuracy Drop',
      description: 'Model accuracy dropped to 76% (threshold: 80%)',
      severity: 'low',
      status: 'resolved',
      service: 'ai-prediction-engine',
      timestamp: new Date(Date.now() - 1800000),
      resolved_at: new Date(Date.now() - 300000),
      tags: ['ai', 'accuracy', 'model']
    }
  ]

  const incidents: IncidentResponse[] = [
    {
      id: 'inc-001',
      title: 'Market Analysis Service Performance Degradation',
      status: 'investigating',
      priority: 'p2',
      created_at: new Date(Date.now() - 1200000),
      assigned_to: 'DevOps Team',
      affected_services: ['market-intelligence-api', 'property-predictions'],
      estimated_resolution: new Date(Date.now() + 3600000)
    },
    {
      id: 'inc-002',
      title: 'Email Delivery Service Outage',
      status: 'identified',
      priority: 'p1',
      created_at: new Date(Date.now() - 900000),
      assigned_to: 'Platform Team',
      affected_services: ['communication-service', 'email-automation']
    }
  ]

  const notificationRules: NotificationRule[] = [
    {
      id: '1',
      name: 'Critical System Alerts',
      conditions: 'severity:critical OR service:database-cluster',
      channels: ['email', 'sms', 'slack'],
      active: true,
      recipients: ['ops-team@seiketsu.ai', '+1-555-0199']
    },
    {
      id: '2',
      name: 'Performance Degradation',
      conditions: 'tags:performance AND status:active',
      channels: ['email', 'slack'],
      active: true,
      recipients: ['dev-team@seiketsu.ai']
    },
    {
      id: '3',
      name: 'Communication Service Issues',
      conditions: 'service:communication-service',
      channels: ['email'],
      active: false,
      recipients: ['marketing@seiketsu.ai']
    }
  ]

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-600 bg-red-100 border-red-200'
      case 'high':
        return 'text-orange-600 bg-orange-100 border-orange-200'
      case 'medium':
        return 'text-yellow-600 bg-yellow-100 border-yellow-200'
      case 'low':
        return 'text-blue-600 bg-blue-100 border-blue-200'
      case 'info':
        return 'text-slate-600 bg-slate-100 border-slate-200'
      default:
        return 'text-slate-600 bg-slate-100 border-slate-200'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <AlertTriangle className="h-4 w-4" />
      case 'high':
        return <AlertCircle className="h-4 w-4" />
      case 'medium':
        return <Clock className="h-4 w-4" />
      case 'low':
        return <Info className="h-4 w-4" />
      case 'info':
        return <Info className="h-4 w-4" />
      default:
        return <Bell className="h-4 w-4" />
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <AlertTriangle className="h-4 w-4 text-red-600" />
      case 'acknowledged':
        return <Clock className="h-4 w-4 text-yellow-600" />
      case 'resolved':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      default:
        return <Bell className="h-4 w-4 text-slate-600" />
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'p1':
        return 'bg-red-600 text-white'
      case 'p2':
        return 'bg-orange-600 text-white'
      case 'p3':
        return 'bg-yellow-600 text-white'
      case 'p4':
        return 'bg-blue-600 text-white'
      default:
        return 'bg-slate-600 text-white'
    }
  }

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'email':
        return <Mail className="h-4 w-4" />
      case 'sms':
        return <MessageSquare className="h-4 w-4" />
      case 'slack':
        return <MessageSquare className="h-4 w-4" />
      case 'webhook':
        return <Zap className="h-4 w-4" />
      default:
        return <Bell className="h-4 w-4" />
    }
  }

  const filteredAlerts = alerts.filter(alert => {
    const matchesSearch = alert.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         alert.service.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesSeverity = filterSeverity === 'all' || alert.severity === filterSeverity
    return matchesSearch && matchesSeverity
  })

  const toggleAlertSelection = (alertId: string) => {
    setSelectedAlerts(prev => 
      prev.includes(alertId) 
        ? prev.filter(id => id !== alertId)
        : [...prev, alertId]
    )
  }

  const acknowledgeSelected = () => {
    console.log('Acknowledging alerts:', selectedAlerts)
    setSelectedAlerts([])
  }

  const resolveSelected = () => {
    console.log('Resolving alerts:', selectedAlerts)
    setSelectedAlerts([])
  }

  return (
    <div className="space-y-6">
      {/* Alert Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-8 w-8 text-red-500" />
              <div>
                <div className="text-2xl font-bold text-white">2</div>
                <div className="text-sm text-slate-400">Critical</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-8 w-8 text-orange-500" />
              <div>
                <div className="text-2xl font-bold text-white">3</div>
                <div className="text-sm text-slate-400">High</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Clock className="h-8 w-8 text-yellow-500" />
              <div>
                <div className="text-2xl font-bold text-white">5</div>
                <div className="text-sm text-slate-400">Medium</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Info className="h-8 w-8 text-blue-500" />
              <div>
                <div className="text-2xl font-bold text-white">7</div>
                <div className="text-sm text-slate-400">Low</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-8 w-8 text-green-500" />
              <div>
                <div className="text-2xl font-bold text-white">23</div>
                <div className="text-sm text-slate-400">Resolved Today</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Alert Management Tabs */}
      <Tabs defaultValue="alerts" className="w-full">
        <TabsList className="grid w-full grid-cols-3 bg-slate-800 border border-slate-700">
          <TabsTrigger value="alerts" className="text-slate-200">Active Alerts</TabsTrigger>
          <TabsTrigger value="incidents" className="text-slate-200">Incident Response</TabsTrigger>
          <TabsTrigger value="notifications" className="text-slate-200">Notification Rules</TabsTrigger>
        </TabsList>

        <TabsContent value="alerts" className="space-y-4">
          {/* Alert Controls */}
          <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
            <div className="flex gap-2">
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-3 text-slate-400" />
                <Input
                  placeholder="Search alerts..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9 bg-slate-800 border-slate-700 text-slate-200"
                />
              </div>
              <select
                value={filterSeverity}
                onChange={(e) => setFilterSeverity(e.target.value)}
                className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-slate-200"
              >
                <option value="all">All Severities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            
            {selectedAlerts.length > 0 && (
              <div className="flex gap-2">
                <Button onClick={acknowledgeSelected} size="sm" variant="outline">
                  <Clock className="h-4 w-4 mr-2" />
                  Acknowledge ({selectedAlerts.length})
                </Button>
                <Button onClick={resolveSelected} size="sm" variant="outline">
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Resolve ({selectedAlerts.length})
                </Button>
              </div>
            )}
          </div>

          {/* Alert List */}
          <div className="space-y-2">
            {filteredAlerts.map((alert) => (
              <Card key={alert.id} className={`bg-slate-800 border-slate-700 cursor-pointer transition-all ${
                selectedAlerts.includes(alert.id) ? 'ring-2 ring-blue-600' : ''
              }`}>
                <CardContent className="p-4">
                  <div className="flex items-start gap-4">
                    <input
                      type="checkbox"
                      checked={selectedAlerts.includes(alert.id)}
                      onChange={() => toggleAlertSelection(alert.id)}
                      className="mt-1"
                    />
                    
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded border ${getSeverityColor(alert.severity)}`}>
                            {getSeverityIcon(alert.severity)}
                            {alert.severity.toUpperCase()}
                          </span>
                          {getStatusIcon(alert.status)}
                          <span className="text-slate-400 text-sm">{alert.service}</span>
                        </div>
                        <span className="text-slate-400 text-sm">
                          {Math.floor((Date.now() - alert.timestamp.getTime()) / 60000)}m ago
                        </span>
                      </div>
                      
                      <h3 className="text-white font-medium mb-1">{alert.title}</h3>
                      <p className="text-slate-400 text-sm mb-2">{alert.description}</p>
                      
                      <div className="flex items-center gap-2 flex-wrap">
                        {alert.tags.map((tag, index) => (
                          <span key={index} className="text-xs bg-slate-700 text-slate-300 px-2 py-1 rounded">
                            {tag}
                          </span>
                        ))}
                      </div>

                      {alert.acknowledged_by && (
                        <div className="mt-2 text-xs text-slate-400">
                          Acknowledged by {alert.acknowledged_by}
                        </div>
                      )}
                    </div>

                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost">
                        <Settings className="h-4 w-4" />
                      </Button>
                      <Button size="sm" variant="ghost">
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="incidents" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold text-white">Active Incidents</h3>
            <Button>
              <AlertTriangle className="h-4 w-4 mr-2" />
              Create Incident
            </Button>
          </div>

          <div className="space-y-4">
            {incidents.map((incident) => (
              <Card key={incident.id} className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-white flex items-center gap-2">
                        <span className={`px-2 py-1 text-xs rounded ${getPriorityColor(incident.priority)}`}>
                          {incident.priority.toUpperCase()}
                        </span>
                        {incident.title}
                      </CardTitle>
                      <CardDescription className="text-slate-400">
                        Created {Math.floor((Date.now() - incident.created_at.getTime()) / 60000)}m ago • Assigned to {incident.assigned_to}
                      </CardDescription>
                    </div>
                    <span className="text-sm bg-blue-900/20 text-blue-400 px-2 py-1 rounded">
                      {incident.status}
                    </span>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <div className="text-sm text-slate-400 mb-1">Affected Services</div>
                      <div className="flex gap-2 flex-wrap">
                        {incident.affected_services.map((service, index) => (
                          <span key={index} className="text-xs bg-red-900/20 text-red-400 px-2 py-1 rounded border border-red-700">
                            {service}
                          </span>
                        ))}
                      </div>
                    </div>
                    {incident.estimated_resolution && (
                      <div>
                        <div className="text-sm text-slate-400 mb-1">Estimated Resolution</div>
                        <div className="text-sm text-white">
                          {incident.estimated_resolution.toLocaleString()}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold text-white">Notification Rules</h3>
            <Button>
              <Bell className="h-4 w-4 mr-2" />
              Create Rule
            </Button>
          </div>

          <div className="space-y-4">
            {notificationRules.map((rule) => (
              <Card key={rule.id} className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-white flex items-center gap-2">
                      {rule.active ? (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      ) : (
                        <X className="h-5 w-5 text-slate-600" />
                      )}
                      {rule.name}
                    </CardTitle>
                    <Button size="sm" variant="ghost">
                      <Settings className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <div className="text-sm text-slate-400 mb-1">Conditions</div>
                      <div className="text-sm font-mono bg-slate-700 p-2 rounded text-slate-200">
                        {rule.conditions}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400 mb-1">Notification Channels</div>
                      <div className="flex gap-2">
                        {rule.channels.map((channel, index) => (
                          <span key={index} className="inline-flex items-center gap-1 text-xs bg-blue-900/20 text-blue-400 px-2 py-1 rounded">
                            {getChannelIcon(channel)}
                            {channel}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400 mb-1">Recipients ({rule.recipients.length})</div>
                      <div className="text-sm text-slate-300">
                        {rule.recipients.slice(0, 2).join(', ')}
                        {rule.recipients.length > 2 && ` +${rule.recipients.length - 2} more`}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}