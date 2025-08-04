'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Building2,
  Users,
  Settings,
  Shield,
  CreditCard,
  Activity,
  Database,
  Key,
  Globe,
  Plus,
  Edit,
  Trash2,
  Eye,
  MoreHorizontal,
  Search,
  Filter,
  Download,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  DollarSign,
  Zap,
  Mail,
  Phone
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

type OrganizationStatus = 'active' | 'suspended' | 'trial' | 'expired'
type SubscriptionTier = 'starter' | 'professional' | 'enterprise' | 'custom'
type UserRole = 'owner' | 'admin' | 'manager' | 'agent' | 'viewer'

interface Organization {
  id: string
  name: string
  domain: string
  status: OrganizationStatus
  tier: SubscriptionTier
  users: OrganizationUser[]
  billing: BillingInfo
  usage: UsageMetrics
  settings: OrganizationSettings
  createdAt: Date
  lastActivity: Date
}

interface OrganizationUser {
  id: string
  name: string
  email: string
  role: UserRole
  status: 'active' | 'pending' | 'suspended'
  lastLogin: Date
  permissions: string[]
}

interface BillingInfo {
  subscriptionId: string
  currentPeriodStart: Date
  currentPeriodEnd: Date
  monthlyRevenue: number
  nextBillingDate: Date
  paymentMethod: string
  billingEmail: string
}

interface UsageMetrics {
  monthlyMinutes: number
  monthlyLeads: number
  apiCalls: number
  storage: number
  integrations: number
  limits: {
    minutes: number
    leads: number
    apiCalls: number
    storage: number
    integrations: number
  }
}

interface OrganizationSettings {
  allowedDomains: string[]
  ssoEnabled: boolean
  twoFactorRequired: boolean
  apiAccess: boolean
  webhooksEnabled: boolean
  customBranding: boolean
}

interface MultiTenantAdminProps {
  className?: string
  onOrganizationSelect?: (org: Organization) => void
  onUserAction?: (action: string, userId: string, orgId: string) => void
}

// Mock data
const mockOrganizations: Organization[] = [
  {
    id: 'org-001',
    name: 'Apex Real Estate',
    domain: 'apex-realestate.com',
    status: 'active',
    tier: 'enterprise',
    users: [
      {
        id: 'user-001',
        name: 'John Smith',
        email: 'john@apex-realestate.com',
        role: 'owner',
        status: 'active',
        lastLogin: new Date('2024-01-16'),
        permissions: ['all']
      },
      {
        id: 'user-002',
        name: 'Sarah Johnson',
        email: 'sarah@apex-realestate.com',
        role: 'admin',
        status: 'active',
        lastLogin: new Date('2024-01-15'),
        permissions: ['manage_agents', 'view_analytics']
      }
    ],
    billing: {
      subscriptionId: 'sub-001',
      currentPeriodStart: new Date('2024-01-01'),
      currentPeriodEnd: new Date('2024-01-31'),
      monthlyRevenue: 2499,
      nextBillingDate: new Date('2024-02-01'),
      paymentMethod: 'Credit Card ****1234',
      billingEmail: 'billing@apex-realestate.com'
    },
    usage: {
      monthlyMinutes: 8420,
      monthlyLeads: 156,
      apiCalls: 45680,
      storage: 2.4,
      integrations: 8,
      limits: {
        minutes: 10000,
        leads: 500,
        apiCalls: 100000,
        storage: 10,
        integrations: 20
      }
    },
    settings: {
      allowedDomains: ['apex-realestate.com'],
      ssoEnabled: true,
      twoFactorRequired: true,
      apiAccess: true,
      webhooksEnabled: true,
      customBranding: true
    },
    createdAt: new Date('2023-06-15'),
    lastActivity: new Date('2024-01-16')
  },
  {
    id: 'org-002',
    name: 'Metro Properties',
    domain: 'metroproperties.io',
    status: 'trial',
    tier: 'professional',
    users: [
      {
        id: 'user-003',
        name: 'Mike Davis',
        email: 'mike@metroproperties.io',
        role: 'owner',
        status: 'active',
        lastLogin: new Date('2024-01-14'),
        permissions: ['all']
      }
    ],
    billing: {
      subscriptionId: 'sub-002',
      currentPeriodStart: new Date('2024-01-08'),
      currentPeriodEnd: new Date('2024-01-22'),
      monthlyRevenue: 0,
      nextBillingDate: new Date('2024-01-22'),
      paymentMethod: 'Trial',
      billingEmail: 'mike@metroproperties.io'
    },
    usage: {
      monthlyMinutes: 245,
      monthlyLeads: 8,
      apiCalls: 1250,
      storage: 0.1,
      integrations: 2,
      limits: {
        minutes: 1000,
        leads: 50,
        apiCalls: 10000,
        storage: 1,
        integrations: 5
      }
    },
    settings: {
      allowedDomains: ['metroproperties.io'],
      ssoEnabled: false,
      twoFactorRequired: false,
      apiAccess: true,
      webhooksEnabled: false,
      customBranding: false
    },
    createdAt: new Date('2024-01-08'),
    lastActivity: new Date('2024-01-14')
  }
]

export function MultiTenantAdmin({
  className,
  onOrganizationSelect,
  onUserAction
}: MultiTenantAdminProps) {
  const [organizations, setOrganizations] = useState<Organization[]>(mockOrganizations)
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<OrganizationStatus[]>([])
  const [tierFilter, setTierFilter] = useState<SubscriptionTier[]>([])
  const [showFilters, setShowFilters] = useState(false)
  const [currentView, setCurrentView] = useState<'overview' | 'users' | 'billing'>('overview')

  const filteredOrganizations = organizations.filter(org => {
    const matchesSearch = org.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         org.domain.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter.length === 0 || statusFilter.includes(org.status)
    const matchesTier = tierFilter.length === 0 || tierFilter.includes(org.tier)
    
    return matchesSearch && matchesStatus && matchesTier
  })

  const getStatusColor = (status: OrganizationStatus) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-700'
      case 'trial': return 'bg-blue-100 text-blue-700'
      case 'suspended': return 'bg-red-100 text-red-700'
      case 'expired': return 'bg-gray-100 text-gray-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const getTierColor = (tier: SubscriptionTier) => {
    switch (tier) {
      case 'starter': return 'bg-gray-100 text-gray-700'
      case 'professional': return 'bg-blue-100 text-blue-700'
      case 'enterprise': return 'bg-purple-100 text-purple-700'
      case 'custom': return 'bg-orange-100 text-orange-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const getUsagePercentage = (used: number, limit: number): number => {
    return Math.min((used / limit) * 100, 100)
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(amount)
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes * k * k * k) / Math.log(k))
    return parseFloat((bytes * k * k * k / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  const totalRevenue = organizations.reduce((sum, org) => sum + org.billing.monthlyRevenue, 0)
  const activeOrgs = organizations.filter(org => org.status === 'active').length
  const trialOrgs = organizations.filter(org => org.status === 'trial').length

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Multi-Tenant Administration</h1>
          <p className="text-muted-foreground">
            {organizations.length} organizations, {formatCurrency(totalRevenue)}/month revenue
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button size="sm">
            <Plus className="w-4 h-4 mr-2" />
            Add Organization
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Organizations</p>
                <p className="text-2xl font-bold">{organizations.length}</p>
              </div>
              <Building2 className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Active Organizations</p>
                <p className="text-2xl font-bold text-green-600">{activeOrgs}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Trial Organizations</p>
                <p className="text-2xl font-bold text-blue-600">{trialOrgs}</p>
              </div>
              <Clock className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Monthly Revenue</p>
                <p className="text-2xl font-bold text-green-600">{formatCurrency(totalRevenue)}</p>
              </div>
              <DollarSign className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search organizations..."
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

      {/* Organization List */}
      <div className="space-y-4">
        {filteredOrganizations.map((org) => (
          <Card key={org.id} className="cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => {
                  setSelectedOrg(org)
                  onOrganizationSelect?.(org)
                }}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-xl font-semibold">{org.name}</h3>
                    <div className={cn(
                      'px-2 py-1 rounded-full text-xs font-medium',
                      getStatusColor(org.status)
                    )}>
                      {org.status}
                    </div>
                    <div className={cn(
                      'px-2 py-1 rounded-full text-xs font-medium',
                      getTierColor(org.tier)
                    )}>
                      {org.tier}
                    </div>
                  </div>
                  
                  <p className="text-muted-foreground mb-4">{org.domain}</p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {/* Users */}
                    <div>
                      <p className="text-sm font-medium mb-1">Users</p>
                      <div className="flex items-center gap-2">
                        <Users className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm">{org.users.length} active</span>
                      </div>
                    </div>

                    {/* Usage */}
                    <div>
                      <p className="text-sm font-medium mb-1">Voice Minutes</p>
                      <div className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span>{org.usage.monthlyMinutes.toLocaleString()}</span>
                          <span className="text-muted-foreground">
                            /{org.usage.limits.minutes.toLocaleString()}
                          </span>
                        </div>
                        <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-blue-500 transition-all duration-300"
                            style={{ 
                              width: `${getUsagePercentage(org.usage.monthlyMinutes, org.usage.limits.minutes)}%` 
                            }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Revenue */}
                    <div>
                      <p className="text-sm font-medium mb-1">Monthly Revenue</p>
                      <div className="flex items-center gap-2">
                        <DollarSign className="w-4 h-4 text-green-600" />
                        <span className="text-sm font-semibold text-green-600">
                          {formatCurrency(org.billing.monthlyRevenue)}
                        </span>
                      </div>
                    </div>

                    {/* Last Activity */}
                    <div>
                      <p className="text-sm font-medium mb-1">Last Activity</p>
                      <div className="flex items-center gap-2">
                        <Activity className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm">
                          {org.lastActivity.toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Quick Stats */}
                  <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Leads: </span>
                      <span className="font-medium">{org.usage.monthlyLeads}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">API Calls: </span>
                      <span className="font-medium">{org.usage.apiCalls.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Storage: </span>
                      <span className="font-medium">{formatBytes(org.usage.storage)}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Integrations: </span>
                      <span className="font-medium">{org.usage.integrations}</span>
                    </div>
                  </div>
                </div>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                      <MoreHorizontal className="w-4 h-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem>
                      <Eye className="w-4 h-4 mr-2" />
                      View Details
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Edit className="w-4 h-4 mr-2" />
                      Edit Organization
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Users className="w-4 h-4 mr-2" />
                      Manage Users
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <CreditCard className="w-4 h-4 mr-2" />
                      Billing Settings
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem>
                      <Settings className="w-4 h-4 mr-2" />
                      Organization Settings
                    </DropdownMenuItem>
                    <DropdownMenuItem className="text-red-600">
                      <AlertTriangle className="w-4 h-4 mr-2" />
                      Suspend Organization
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredOrganizations.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <Building2 className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No organizations found</h3>
            <p className="text-muted-foreground mb-4">
              Try adjusting your search criteria or add a new organization
            </p>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Add Organization
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default MultiTenantAdmin