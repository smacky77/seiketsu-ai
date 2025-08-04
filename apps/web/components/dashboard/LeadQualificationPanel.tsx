'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  TrendingUp, 
  User, 
  DollarSign, 
  Calendar,
  MapPin,
  Star,
  AlertTriangle,
  CheckCircle,
  Clock,
  ArrowRight
} from 'lucide-react'

interface LeadData {
  id: string
  name: string
  score: number
  budget: string
  timeline: string
  location: string
  propertyType: string
  priority: 'hot' | 'warm' | 'cold'
  status: 'new' | 'contacted' | 'qualified' | 'appointment'
  lastActivity: string
  insights: string[]
}

export function LeadQualificationPanel() {
  const [selectedLead, setSelectedLead] = useState<string | null>('1')
  
  const leads: LeadData[] = [
    {
      id: '1',
      name: 'Jennifer Martinez',
      score: 85,
      budget: '$400K - $500K',
      timeline: 'Within 30 days',
      location: 'Downtown area',
      propertyType: '2-3 bedroom condo',
      priority: 'hot',
      status: 'qualified',
      lastActivity: 'Active conversation - 3 minutes ago',
      insights: [
        'Pre-approved for $480K mortgage',
        'First-time buyer program eligible',
        'Urgency due to lease expiration',
        'Partner involved in decision making'
      ]
    },
    {
      id: '2',
      name: 'Michael Chen',
      score: 92,
      budget: '$600K - $700K',
      timeline: 'Next 2 weeks',
      location: 'Suburban family area',
      propertyType: '3-4 bedroom house',
      priority: 'hot',
      status: 'appointment',
      lastActivity: 'Viewing scheduled - 2 hours ago',
      insights: [
        'Cash buyer - no financing needed',
        'Relocating for job - time sensitive',
        'Excellent credit score (780+)',
        'Previous property sale completed'
      ]
    },
    {
      id: '3',
      name: 'Sarah Williams',
      score: 70,
      budget: '$750K - $850K',
      timeline: '3-6 months',
      location: 'School district priority',
      propertyType: '4+ bedroom house',
      priority: 'warm',
      status: 'contacted',
      lastActivity: 'Follow-up needed - 1 hour ago',
      insights: [
        'Considering multiple areas',
        'School ratings very important',
        'Current home needs to sell first',
        'Budget depends on sale price'
      ]
    }
  ]

  const selectedLeadData = leads.find(lead => lead.id === selectedLead)

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-500'
    if (score >= 60) return 'text-yellow-500'
    return 'text-red-500'
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'hot': return 'bg-red-500'
      case 'warm': return 'bg-yellow-500'
      case 'cold': return 'bg-blue-500'
      default: return 'bg-muted'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'qualified': return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'appointment': return <Calendar className="w-4 h-4 text-blue-500" />
      case 'contacted': return <Clock className="w-4 h-4 text-yellow-500" />
      default: return <AlertTriangle className="w-4 h-4 text-muted-foreground" />
    }
  }

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold">Lead Intelligence</h2>
        <button className="btn btn-ghost text-sm">
          <TrendingUp className="w-4 h-4 mr-2" />
          Analytics
        </button>
      </div>

      {/* Lead Selection */}
      <div className="space-y-2 mb-6">
        {leads.slice(0, 3).map((lead) => (
          <button
            key={lead.id}
            onClick={() => setSelectedLead(lead.id)}
            className={`w-full p-3 rounded-lg text-left transition-all ${
              selectedLead === lead.id
                ? 'bg-foreground text-background'
                : 'bg-muted hover:bg-accent'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${getPriorityColor(lead.priority)}`} />
                <span className="font-medium">{lead.name}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-sm font-medium ${
                  selectedLead === lead.id ? 'text-background' : getScoreColor(lead.score)
                }`}>
                  {lead.score}%
                </span>
                {getStatusIcon(lead.status)}
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* Selected Lead Details */}
      {selectedLeadData && (
        <motion.div
          key={selectedLeadData.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          {/* Qualification Score */}
          <div className="bg-muted rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium">Qualification Score</span>
              <span className={`text-lg font-bold ${getScoreColor(selectedLeadData.score)}`}>
                {selectedLeadData.score}%
              </span>
            </div>
            <div className="w-full bg-background rounded-full h-2">
              <motion.div
                className={`h-full rounded-full ${
                  selectedLeadData.score >= 80 ? 'bg-green-500' :
                  selectedLeadData.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                initial={{ width: 0 }}
                animate={{ width: `${selectedLeadData.score}%` }}
                transition={{ duration: 0.8 }}
              />
            </div>
          </div>

          {/* Lead Details */}
          <div className="grid grid-cols-1 gap-3">
            <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
              <DollarSign className="w-4 h-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Budget Range</p>
                <p className="text-sm font-medium">{selectedLeadData.budget}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
              <Calendar className="w-4 h-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Timeline</p>
                <p className="text-sm font-medium">{selectedLeadData.timeline}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
              <MapPin className="w-4 h-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Preferred Area</p>
                <p className="text-sm font-medium">{selectedLeadData.location}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
              <User className="w-4 h-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Property Type</p>
                <p className="text-sm font-medium">{selectedLeadData.propertyType}</p>
              </div>
            </div>
          </div>

          {/* AI Insights */}
          <div>
            <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
              <Star className="w-4 h-4" />
              AI Insights
            </h4>
            <div className="space-y-2">
              {selectedLeadData.insights.map((insight, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-start gap-2 p-2 bg-muted rounded text-sm"
                >
                  <div className="w-1.5 h-1.5 bg-foreground rounded-full mt-2 flex-shrink-0" />
                  <span>{insight}</span>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Last Activity */}
          <div className="bg-accent rounded-lg p-3">
            <p className="text-xs text-muted-foreground mb-1">Last Activity</p>
            <p className="text-sm font-medium">{selectedLeadData.lastActivity}</p>
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-2 gap-2">
            <button className="btn btn-primary text-sm">
              <Calendar className="w-4 h-4 mr-2" />
              Schedule
            </button>
            <button className="btn btn-secondary text-sm">
              View Details
              <ArrowRight className="w-4 h-4 ml-2" />
            </button>
          </div>
        </motion.div>
      )}
    </div>
  )
}