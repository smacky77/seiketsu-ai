'use client'

import { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search,
  Filter,
  MoreHorizontal,
  Phone,
  Mail,
  Calendar,
  User,
  Star,
  TrendingUp,
  Clock,
  MessageSquare,
  Eye,
  Edit,
  Trash2,
  Plus,
  Download,
  RefreshCw,
  Tag,
  MapPin,
  DollarSign
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

type LeadStatus = 'new' | 'contacted' | 'qualified' | 'appointment' | 'converted' | 'lost'
type LeadSource = 'website' | 'phone' | 'referral' | 'social' | 'advertisement' | 'other'
type Priority = 'low' | 'medium' | 'high' | 'urgent'

interface Lead {
  id: string
  name: string
  email: string
  phone: string
  status: LeadStatus
  source: LeadSource
  priority: Priority
  score: number
  lastContact: Date
  nextFollowUp?: Date
  propertyInterest: string
  budget: number
  location: string
  notes: string
  conversationHistory: ConversationEntry[]
  tags: string[]
  assignedAgent?: string
  createdAt: Date
}

interface ConversationEntry {
  id: string
  timestamp: Date
  type: 'call' | 'email' | 'sms' | 'meeting' | 'note'
  content: string
  duration?: number
  outcome?: string
  sentiment: 'positive' | 'neutral' | 'negative'
}

interface LeadFilters {
  status: LeadStatus[]
  source: LeadSource[]
  priority: Priority[]
  dateRange: 'today' | 'week' | 'month' | 'quarter' | 'custom'
  minScore: number
  maxScore: number
  search: string
}

interface LeadManagementSystemProps {
  className?: string
  onLeadSelect?: (lead: Lead) => void
  onLeadUpdate?: (lead: Lead) => void
  onLeadDelete?: (leadId: string) => void
}

// Mock data
const mockLeads: Lead[] = [
  {
    id: 'lead-001',
    name: 'Jennifer Martinez',
    email: 'jennifer@email.com',
    phone: '+1 (555) 123-4567',
    status: 'qualified',
    source: 'website',
    priority: 'high',
    score: 85,
    lastContact: new Date('2024-01-15'),
    nextFollowUp: new Date('2024-01-17'),
    propertyInterest: 'Downtown Condo - $450K',
    budget: 500000,
    location: 'Downtown',
    notes: 'Very interested in modern amenities. Prefers high-floor units.',
    conversationHistory: [
      {
        id: 'conv-001',
        timestamp: new Date('2024-01-15'),
        type: 'call',
        content: 'Initial inquiry about downtown properties',
        duration: 420,
        sentiment: 'positive'
      }
    ],
    tags: ['qualified', 'high-value', 'urgent'],
    assignedAgent: 'Agent Smith',
    createdAt: new Date('2024-01-10')
  },
  {
    id: 'lead-002',
    name: 'Robert Chen',
    email: 'robert.chen@email.com',
    phone: '+1 (555) 987-6543',
    status: 'appointment',
    source: 'referral',
    priority: 'medium',
    score: 72,
    lastContact: new Date('2024-01-14'),
    nextFollowUp: new Date('2024-01-18'),
    propertyInterest: 'Suburban House - $650K',
    budget: 700000,
    location: 'Westside',
    notes: 'Looking for family home with good schools nearby.',
    conversationHistory: [
      {
        id: 'conv-002',
        timestamp: new Date('2024-01-14'),
        type: 'email',
        content: 'Sent property recommendations',
        sentiment: 'neutral'
      }
    ],
    tags: ['family', 'schools'],
    assignedAgent: 'Agent Johnson',
    createdAt: new Date('2024-01-12')
  },
  {
    id: 'lead-003',
    name: 'Sarah Williams',
    email: 'sarah.w@email.com',
    phone: '+1 (555) 456-7890',
    status: 'new',
    source: 'social',
    priority: 'low',
    score: 45,
    lastContact: new Date('2024-01-16'),
    propertyInterest: 'Starter Home - $300K',
    budget: 350000,
    location: 'Eastside',
    notes: 'First-time buyer, needs education on process.',
    conversationHistory: [],
    tags: ['first-time'],
    createdAt: new Date('2024-01-16')
  }
]

export function LeadManagementSystem({
  className,
  onLeadSelect,
  onLeadUpdate,
  onLeadDelete
}: LeadManagementSystemProps) {
  const [leads, setLeads] = useState<Lead[]>(mockLeads)
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null)
  const [filters, setFilters] = useState<LeadFilters>({
    status: [],
    source: [],
    priority: [],
    dateRange: 'month',
    minScore: 0,
    maxScore: 100,
    search: ''
  })
  const [showFilters, setShowFilters] = useState(false)
  const [sortBy, setSortBy] = useState<keyof Lead>('lastContact')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  const filteredLeads = useMemo(() => {
    return leads
      .filter(lead => {
        // Search filter
        if (filters.search) {
          const searchTerm = filters.search.toLowerCase()
          if (!lead.name.toLowerCase().includes(searchTerm) &&
              !lead.email.toLowerCase().includes(searchTerm) &&
              !lead.phone.includes(searchTerm)) {
            return false
          }
        }

        // Status filter
        if (filters.status.length > 0 && !filters.status.includes(lead.status)) {
          return false
        }

        // Source filter
        if (filters.source.length > 0 && !filters.source.includes(lead.source)) {
          return false
        }

        // Priority filter
        if (filters.priority.length > 0 && !filters.priority.includes(lead.priority)) {
          return false
        }

        // Score filter
        if (lead.score < filters.minScore || lead.score > filters.maxScore) {
          return false
        }

        return true
      })
      .sort((a, b) => {
        const aValue = a[sortBy as keyof typeof a]
        const bValue = b[sortBy as keyof typeof b]
        
        if (aValue && bValue && aValue < bValue) return sortOrder === 'asc' ? -1 : 1
        if (aValue && bValue && aValue > bValue) return sortOrder === 'asc' ? 1 : -1
        return 0
      })
  }, [leads, filters, sortBy, sortOrder])

  const getStatusColor = (status: LeadStatus) => {
    switch (status) {
      case 'new': return 'bg-blue-100 text-blue-700'
      case 'contacted': return 'bg-yellow-100 text-yellow-700'
      case 'qualified': return 'bg-green-100 text-green-700'
      case 'appointment': return 'bg-purple-100 text-purple-700'
      case 'converted': return 'bg-emerald-100 text-emerald-700'
      case 'lost': return 'bg-red-100 text-red-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const getPriorityColor = (priority: Priority) => {
    switch (priority) {
      case 'urgent': return 'text-red-500'
      case 'high': return 'text-orange-500'
      case 'medium': return 'text-yellow-500'
      case 'low': return 'text-gray-500'
      default: return 'text-gray-500'
    }
  }

  const handleLeadClick = (lead: Lead) => {
    setSelectedLead(lead)
    onLeadSelect?.(lead)
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(amount)
  }

  const formatRelativeTime = (date: Date) => {
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - date.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays} days ago`
    if (diffDays < 30) return `${Math.ceil(diffDays / 7)} weeks ago`
    return `${Math.ceil(diffDays / 30)} months ago`
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Lead Management</h1>
          <p className="text-muted-foreground">
            {filteredLeads.length} of {leads.length} leads
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
            Add Lead
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search leads by name, email, or phone..."
            value={filters.search}
            onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
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

      {/* Filter Panel */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border rounded-lg p-4 bg-card"
          >
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Status</label>
                <div className="space-y-1">
                  {['new', 'contacted', 'qualified', 'appointment', 'converted', 'lost'].map(status => (
                    <label key={status} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={filters.status.includes(status as LeadStatus)}
                        onChange={(e) => {
                          const newStatus = filters.status.filter(s => s !== status)
                          if (e.target.checked) newStatus.push(status as LeadStatus)
                          setFilters(prev => ({ ...prev, status: newStatus }))
                        }}
                        className="rounded"
                      />
                      <span className="text-sm capitalize">{status}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Source</label>
                <div className="space-y-1">
                  {['website', 'phone', 'referral', 'social', 'advertisement', 'other'].map(source => (
                    <label key={source} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={filters.source.includes(source as LeadSource)}
                        onChange={(e) => {
                          const newSource = filters.source.filter(s => s !== source)
                          if (e.target.checked) newSource.push(source as LeadSource)
                          setFilters(prev => ({ ...prev, source: newSource }))
                        }}
                        className="rounded"
                      />
                      <span className="text-sm capitalize">{source}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Priority</label>
                <div className="space-y-1">
                  {['low', 'medium', 'high', 'urgent'].map(priority => (
                    <label key={priority} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={filters.priority.includes(priority as Priority)}
                        onChange={(e) => {
                          const newPriority = filters.priority.filter(p => p !== priority)
                          if (e.target.checked) newPriority.push(priority as Priority)
                          setFilters(prev => ({ ...prev, priority: newPriority }))
                        }}
                        className="rounded"
                      />
                      <span className="text-sm capitalize">{priority}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Lead Score</label>
                <div className="space-y-2">
                  <Input
                    type="number"
                    placeholder="Min score"
                    value={filters.minScore}
                    onChange={(e) => setFilters(prev => ({ ...prev, minScore: parseInt(e.target.value) || 0 }))}
                  />
                  <Input
                    type="number"
                    placeholder="Max score"
                    value={filters.maxScore}
                    onChange={(e) => setFilters(prev => ({ ...prev, maxScore: parseInt(e.target.value) || 100 }))}
                  />
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Lead Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        <AnimatePresence>
          {filteredLeads.map((lead) => (
            <motion.div
              key={lead.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              whileHover={{ scale: 1.02 }}
              className="cursor-pointer"
              onClick={() => handleLeadClick(lead)}
            >
              <Card className={cn(
                'transition-all duration-200 hover:shadow-md',
                selectedLead?.id === lead.id && 'ring-2 ring-primary'
              )}>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg">{lead.name}</CardTitle>
                      <p className="text-sm text-muted-foreground">{lead.email}</p>
                      <p className="text-sm text-muted-foreground">{lead.phone}</p>
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
                          Edit Lead
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Phone className="w-4 h-4 mr-2" />
                          Call Lead
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Mail className="w-4 h-4 mr-2" />
                          Send Email
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem className="text-red-600">
                          <Trash2 className="w-4 h-4 mr-2" />
                          Delete Lead
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {/* Status and Score */}
                  <div className="flex items-center justify-between">
                    <div className={cn(
                      'px-2 py-1 rounded-full text-xs font-medium',
                      getStatusColor(lead.status)
                    )}>
                      {lead.status}
                    </div>
                    <div className="flex items-center gap-2">
                      <Star className={cn(
                        'w-4 h-4',
                        getPriorityColor(lead.priority)
                      )} />
                      <span className="text-sm font-semibold">{lead.score}</span>
                    </div>
                  </div>

                  {/* Property Interest */}
                  <div>
                    <p className="text-sm font-medium">{lead.propertyInterest}</p>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground mt-1">
                      <div className="flex items-center gap-1">
                        <DollarSign className="w-3 h-3" />
                        {formatCurrency(lead.budget)}
                      </div>
                      <div className="flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        {lead.location}
                      </div>
                    </div>
                  </div>

                  {/* Tags */}
                  {lead.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {lead.tags.slice(0, 3).map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 bg-muted text-xs rounded"
                        >
                          {tag}
                        </span>
                      ))}
                      {lead.tags.length > 3 && (
                        <span className="px-2 py-0.5 bg-muted text-xs rounded">
                          +{lead.tags.length - 3}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Last Contact */}
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Last contact: {formatRelativeTime(lead.lastContact)}
                    </div>
                    {lead.conversationHistory.length > 0 && (
                      <div className="flex items-center gap-1">
                        <MessageSquare className="w-3 h-3" />
                        {lead.conversationHistory.length}
                      </div>
                    )}
                  </div>

                  {/* Next Follow-up */}
                  {lead.nextFollowUp && (
                    <div className="flex items-center gap-1 text-xs text-blue-600">
                      <Calendar className="w-3 h-3" />
                      Follow-up: {lead.nextFollowUp.toLocaleDateString()}
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {filteredLeads.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <User className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No leads found</h3>
            <p className="text-muted-foreground mb-4">
              Try adjusting your search criteria or filters
            </p>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Add New Lead
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default LeadManagementSystem