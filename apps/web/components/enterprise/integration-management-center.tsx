'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Database,
  Globe,
  Key,
  Settings,
  Check,
  X,
  AlertTriangle,
  RefreshCw,
  Plus,
  Edit,
  Trash2,
  Eye,
  EyeOff,
  Copy,
  ExternalLink,
  Activity,
  Clock,
  Shield,
  Zap,
  Home,
  Building,
  Mail,
  Phone,
  MessageSquare,
  Calendar,
  FileText,
  BarChart3,
  Users,
  CreditCard,
  Search,
  Filter,
  Download,
  Upload
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'

type IntegrationStatus = 'connected' | 'disconnected' | 'error' | 'syncing' | 'pending'
type IntegrationType = 'crm' | 'mls' | 'email' | 'sms' | 'calendar' | 'analytics' | 'storage' | 'payment' | 'webhook'

interface Integration {
  id: string
  name: string
  type: IntegrationType
  provider: string
  status: IntegrationStatus
  description: string
  icon: React.ComponentType<any>
  connected: boolean
  lastSync: Date
  syncFrequency: string
  recordsProcessed: number
  errorCount: number
  configuration: IntegrationConfig
  endpoints: IntegrationEndpoint[]
  webhooks: Webhook[]
}

interface IntegrationConfig {
  apiKey?: string
  apiSecret?: string
  baseUrl?: string
  username?: string
  password?: string
  organizationId?: string
  customFields: { [key: string]: any }
  rateLimits: {
    requestsPerMinute: number
    requestsPerDay: number
  }
}

interface IntegrationEndpoint {
  id: string
  name: string
  url: string
  method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  lastUsed: Date
  responseTime: number
  successRate: number
}

interface Webhook {
  id: string
  name: string
  url: string
  events: string[]
  secret: string
  active: boolean
  lastTriggered?: Date
  deliveryCount: number
  failureCount: number
}

interface DataMapping {
  id: string
  integrationId: string
  sourceField: string
  targetField: string
  transformation: string
  required: boolean
}

interface IntegrationManagementCenterProps {
  className?: string
  onIntegrationConnect?: (integration: Integration) => void
  onIntegrationDisconnect?: (integrationId: string) => void
  onConfigurationUpdate?: (integrationId: string, config: IntegrationConfig) => void
}

// Mock integrations data
const mockIntegrations: Integration[] = [
  {
    id: 'int-001',
    name: 'Salesforce CRM',
    type: 'crm',
    provider: 'Salesforce',
    status: 'connected',
    description: 'Sync leads, contacts, and opportunities with Salesforce CRM',
    icon: Database,
    connected: true,
    lastSync: new Date(Date.now() - 300000),
    syncFrequency: 'Every 5 minutes',
    recordsProcessed: 15847,
    errorCount: 2,
    configuration: {
      apiKey: 'sf_live_••••••••••••5678',
      baseUrl: 'https://yourorg.salesforce.com',
      organizationId: 'org_salesforce_123',
      customFields: {
        leadSource: 'Voice_Agent',
        customPrefix: 'SKTSU_'
      },
      rateLimits: {
        requestsPerMinute: 100,
        requestsPerDay: 15000
      }
    },
    endpoints: [
      {
        id: 'ep-001',
        name: 'Create Lead',
        url: '/services/data/v55.0/sobjects/Lead',
        method: 'POST',
        lastUsed: new Date(Date.now() - 120000),
        responseTime: 245,
        successRate: 99.8
      }
    ],
    webhooks: [
      {
        id: 'wh-001',
        name: 'Lead Status Updates',
        url: 'https://api.seiketsu.ai/webhooks/salesforce',
        events: ['lead.updated', 'opportunity.created'],
        secret: 'whsec_••••••••••••9876',
        active: true,
        lastTriggered: new Date(Date.now() - 600000),
        deliveryCount: 1247,
        failureCount: 3
      }
    ]
  },
  {
    id: 'int-002',
    name: 'MLS Integration',
    type: 'mls',
    provider: 'RETS/MLS',
    status: 'connected',
    description: 'Access property listings and market data from MLS',
    icon: Home,
    connected: true,
    lastSync: new Date(Date.now() - 180000),
    syncFrequency: 'Every 15 minutes',
    recordsProcessed: 45623,
    errorCount: 0,
    configuration: {
      username: 'seiketsu_mls_user',
      password: '••••••••••••',
      baseUrl: 'https://rets.regionalmls.com',
      customFields: {},
      rateLimits: {
        requestsPerMinute: 20,
        requestsPerDay: 2000
      }
    },
    endpoints: [
      {
        id: 'ep-002',
        name: 'Property Search',
        url: '/rets/search',
        method: 'GET',
        lastUsed: new Date(Date.now() - 180000),
        responseTime: 1250,
        successRate: 100.0
      }
    ],
    webhooks: []
  },
  {
    id: 'int-003',
    name: 'SendGrid Email',
    type: 'email',
    provider: 'SendGrid',
    status: 'connected',
    description: 'Send transactional emails and marketing campaigns',
    icon: Mail,
    connected: true,
    lastSync: new Date(Date.now() - 60000),
    syncFrequency: 'Real-time',
    recordsProcessed: 8934,
    errorCount: 1,
    configuration: {
      apiKey: 'SG.••••••••••••••••••••••••••••••••.••••••••••••••••••••••••••••••••••••••••••••••••',
      customFields: {
        fromName: 'Seiketsu AI',
        fromEmail: 'noreply@seiketsu.ai'
      },
      rateLimits: {
        requestsPerMinute: 600,
        requestsPerDay: 100000
      }
    },
    endpoints: [
      {
        id: 'ep-003',
        name: 'Send Email',
        url: '/v3/mail/send',
        method: 'POST',
        lastUsed: new Date(Date.now() - 60000),
        responseTime: 189,
        successRate: 99.9
      }
    ],
    webhooks: [
      {
        id: 'wh-002',
        name: 'Email Events',
        url: 'https://api.seiketsu.ai/webhooks/sendgrid',
        events: ['delivered', 'opened', 'clicked'],
        secret: 'whsec_••••••••••••1234',
        active: true,
        lastTriggered: new Date(Date.now() - 300000),
        deliveryCount: 2847,
        failureCount: 0
      }
    ]
  },
  {
    id: 'int-004',
    name: 'Google Calendar',
    type: 'calendar',
    provider: 'Google',
    status: 'error',
    description: 'Schedule appointments and manage agent calendars',
    icon: Calendar,
    connected: false,
    lastSync: new Date(Date.now() - 3600000),
    syncFrequency: 'Every 10 minutes',
    recordsProcessed: 0,
    errorCount: 15,
    configuration: {
      apiKey: 'AIza••••••••••••••••••••••••••••••••••••••••',
      customFields: {},
      rateLimits: {
        requestsPerMinute: 250,
        requestsPerDay: 10000
      }
    },
    endpoints: [
      {
        id: 'ep-004',
        name: 'Create Event',
        url: '/calendar/v3/calendars/primary/events',
        method: 'POST',
        lastUsed: new Date(Date.now() - 3600000),
        responseTime: 0,
        successRate: 0
      }
    ],
    webhooks: []
  }
]

export function IntegrationManagementCenter({
  className,
  onIntegrationConnect,
  onIntegrationDisconnect,
  onConfigurationUpdate
}: IntegrationManagementCenterProps) {
  const [integrations, setIntegrations] = useState<Integration[]>(mockIntegrations)
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<IntegrationStatus[]>([])
  const [typeFilter, setTypeFilter] = useState<IntegrationType[]>([])
  const [showFilters, setShowFilters] = useState(false)
  const [showSecrets, setShowSecrets] = useState<{ [key: string]: boolean }>({})

  const filteredIntegrations = integrations.filter(integration => {
    const matchesSearch = integration.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         integration.provider.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter.length === 0 || statusFilter.includes(integration.status)
    const matchesType = typeFilter.length === 0 || typeFilter.includes(integration.type)
    
    return matchesSearch && matchesStatus && matchesType
  })

  const getStatusColor = (status: IntegrationStatus) => {
    switch (status) {
      case 'connected': return 'bg-green-100 text-green-700'
      case 'syncing': return 'bg-blue-100 text-blue-700'
      case 'error': return 'bg-red-100 text-red-700'
      case 'disconnected': return 'bg-gray-100 text-gray-700'
      case 'pending': return 'bg-yellow-100 text-yellow-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const getStatusIcon = (status: IntegrationStatus) => {
    switch (status) {
      case 'connected': return <Check className="w-4 h-4" />
      case 'syncing': return <RefreshCw className="w-4 h-4 animate-spin" />
      case 'error': return <AlertTriangle className="w-4 h-4" />
      case 'disconnected': return <X className="w-4 h-4" />
      case 'pending': return <Clock className="w-4 h-4" />
      default: return <Activity className="w-4 h-4" />
    }
  }

  const getTypeIcon = (type: IntegrationType) => {
    switch (type) {
      case 'crm': return Database
      case 'mls': return Home
      case 'email': return Mail
      case 'sms': return MessageSquare
      case 'calendar': return Calendar
      case 'analytics': return BarChart3
      case 'storage': return FileText
      case 'payment': return CreditCard
      case 'webhook': return Globe
      default: return Activity
    }
  }

  const toggleSecretVisibility = (key: string) => {
    setShowSecrets(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    // Could add toast notification here
  }

  const formatRelativeTime = (date: Date) => {
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - date.getTime())
    const diffMinutes = Math.ceil(diffTime / (1000 * 60))
    
    if (diffMinutes < 60) return `${diffMinutes}m ago`
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`
    return `${Math.floor(diffMinutes / 1440)}d ago`
  }

  const connectedIntegrations = integrations.filter(i => i.status === 'connected').length
  const totalRecords = integrations.reduce((sum, i) => sum + i.recordsProcessed, 0)
  const totalErrors = integrations.reduce((sum, i) => sum + i.errorCount, 0)

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Integration Management Center</h1>
          <p className="text-muted-foreground">
            {connectedIntegrations}/{integrations.length} integrations connected
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export Config
          </Button>
          <Button variant="outline" size="sm">
            <Upload className="w-4 h-4 mr-2" />
            Import Config
          </Button>
          <Button size="sm">
            <Plus className="w-4 h-4 mr-2" />
            Add Integration
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Integrations</p>
                <p className="text-2xl font-bold">{integrations.length}</p>
              </div>
              <Globe className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Connected</p>
                <p className="text-2xl font-bold text-green-600">{connectedIntegrations}</p>
              </div>
              <Check className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Records Processed</p>
                <p className="text-2xl font-bold">{totalRecords.toLocaleString()}</p>
              </div>
              <Activity className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Errors</p>
                <p className="text-2xl font-bold text-red-600">{totalErrors}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search integrations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button
          variant="outline"
          onClick={() => setShowFilters(!showFilters)}
        >
          <Filter className="w-4 h-4 mr-2" />
          Filters
        </Button>
      </div>

      {/* Integration Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {filteredIntegrations.map((integration) => {
          const Icon = integration.icon
          const TypeIcon = getTypeIcon(integration.type)
          
          return (
            <motion.div
              key={integration.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="cursor-pointer"
              onClick={() => setSelectedIntegration(integration)}
            >
              <Card className={cn(
                'transition-all duration-200 hover:shadow-md',
                selectedIntegration?.id === integration.id && 'ring-2 ring-primary'
              )}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-muted rounded-lg">
                        <Icon className="w-6 h-6" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{integration.name}</CardTitle>
                        <p className="text-sm text-muted-foreground">{integration.provider}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className={cn(
                        'flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium',
                        getStatusColor(integration.status)
                      )}>
                        {getStatusIcon(integration.status)}
                        {integration.status}
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                            <Settings className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>
                            <Eye className="w-4 h-4 mr-2" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Edit className="w-4 h-4 mr-2" />
                            Edit Configuration
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <RefreshCw className="w-4 h-4 mr-2" />
                            Force Sync
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem>
                            <Key className="w-4 h-4 mr-2" />
                            API Keys
                          </DropdownMenuItem>
                          <DropdownMenuItem className="text-red-600">
                            <Trash2 className="w-4 h-4 mr-2" />
                            Remove Integration
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-muted-foreground">{integration.description}</p>
                  
                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="font-medium">{integration.recordsProcessed.toLocaleString()}</p>
                      <p className="text-muted-foreground">Records</p>
                    </div>
                    <div>
                      <p className="font-medium">{integration.errorCount}</p>
                      <p className="text-muted-foreground">Errors</p>
                    </div>
                    <div>
                      <p className="font-medium">{integration.syncFrequency}</p>
                      <p className="text-muted-foreground">Sync</p>
                    </div>
                  </div>

                  {/* Last Sync */}
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Last sync:</span>
                    <span>{formatRelativeTime(integration.lastSync)}</span>
                  </div>

                  {/* Rate Limits */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Rate Limit:</span>
                      <span>{integration.configuration.rateLimits.requestsPerMinute}/min</span>
                    </div>
                    <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-blue-500 transition-all duration-300"
                        style={{ width: '65%' }} // Mock usage percentage
                      />
                    </div>
                  </div>

                  {/* Endpoints Status */}
                  {integration.endpoints.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-sm font-medium">Endpoints ({integration.endpoints.length})</p>
                      {integration.endpoints.slice(0, 2).map((endpoint) => (
                        <div key={endpoint.id} className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">{endpoint.name}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-xs">{endpoint.responseTime}ms</span>
                            <div className={cn(
                              'w-2 h-2 rounded-full',
                              endpoint.successRate > 95 ? 'bg-green-500' :
                              endpoint.successRate > 90 ? 'bg-yellow-500' : 'bg-red-500'
                            )} />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Webhooks */}
                  {integration.webhooks.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-sm font-medium">Webhooks ({integration.webhooks.length})</p>
                      {integration.webhooks.slice(0, 1).map((webhook) => (
                        <div key={webhook.id} className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">{webhook.name}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-xs">{webhook.deliveryCount} delivered</span>
                            <div className={cn(
                              'w-2 h-2 rounded-full',
                              webhook.active ? 'bg-green-500' : 'bg-gray-500'
                            )} />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )
        })}
      </div>

      {/* Detailed Integration Panel */}
      <AnimatePresence>
        {selectedIntegration && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Configuration - {selectedIntegration.name}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedIntegration(null)}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* API Configuration */}
                <div>
                  <h4 className="font-semibold mb-3">API Configuration</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {Object.entries(selectedIntegration.configuration).map(([key, value]) => {
                      if (key === 'customFields' || key === 'rateLimits') return null
                      
                      const isSecret = key.includes('secret') || key.includes('password') || key.includes('key')
                      const displayValue = isSecret && !showSecrets[key] 
                        ? '••••••••••••••••' 
                        : value as string
                      
                      return (
                        <div key={key} className="space-y-2">
                          <label className="text-sm font-medium capitalize">
                            {key.replace(/([A-Z])/g, ' $1').toLowerCase()}
                          </label>
                          <div className="flex items-center gap-2">
                            <Input 
                              value={displayValue}
                              readOnly
                              className="font-mono text-sm"
                            />
                            {isSecret && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => toggleSecretVisibility(key)}
                              >
                                {showSecrets[key] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => copyToClipboard(value as string)}
                            >
                              <Copy className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>

                {/* Endpoints */}
                {selectedIntegration.endpoints.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-3">API Endpoints</h4>
                    <div className="space-y-3">
                      {selectedIntegration.endpoints.map((endpoint) => (
                        <div key={endpoint.id} className="p-4 border rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-3">
                              <span className={cn(
                                'px-2 py-1 rounded text-xs font-mono font-bold',
                                endpoint.method === 'GET' ? 'bg-blue-100 text-blue-700' :
                                endpoint.method === 'POST' ? 'bg-green-100 text-green-700' :
                                endpoint.method === 'PUT' ? 'bg-yellow-100 text-yellow-700' :
                                'bg-red-100 text-red-700'
                              )}>
                                {endpoint.method}
                              </span>
                              <span className="font-semibold">{endpoint.name}</span>
                            </div>
                            <div className="flex items-center gap-4 text-sm">
                              <span>Response: {endpoint.responseTime}ms</span>
                              <span>Success: {endpoint.successRate}%</span>
                              <span className="text-muted-foreground">
                                Last used: {formatRelativeTime(endpoint.lastUsed)}
                              </span>
                            </div>
                          </div>
                          <code className="text-sm text-muted-foreground">{endpoint.url}</code>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Webhooks */}
                {selectedIntegration.webhooks.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-3">Webhooks</h4>
                    <div className="space-y-3">
                      {selectedIntegration.webhooks.map((webhook) => (
                        <div key={webhook.id} className="p-4 border rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-3">
                              <div className={cn(
                                'w-3 h-3 rounded-full',
                                webhook.active ? 'bg-green-500' : 'bg-gray-500'
                              )} />
                              <span className="font-semibold">{webhook.name}</span>
                            </div>
                            <div className="flex items-center gap-4 text-sm">
                              <span>Delivered: {webhook.deliveryCount}</span>
                              <span>Failed: {webhook.failureCount}</span>
                              {webhook.lastTriggered && (
                                <span className="text-muted-foreground">
                                  Last: {formatRelativeTime(webhook.lastTriggered)}
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="space-y-2">
                            <code className="text-sm text-muted-foreground">{webhook.url}</code>
                            <div className="flex flex-wrap gap-1">
                              {webhook.events.map((event) => (
                                <span 
                                  key={event}
                                  className="px-2 py-0.5 bg-muted text-xs rounded"
                                >
                                  {event}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {filteredIntegrations.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <Globe className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No integrations found</h3>
            <p className="text-muted-foreground mb-4">
              Try adjusting your search criteria or add a new integration
            </p>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Add Integration
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default IntegrationManagementCenter