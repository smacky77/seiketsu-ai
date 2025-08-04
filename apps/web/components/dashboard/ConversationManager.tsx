'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  MessageCircle, 
  Phone, 
  Clock, 
  Star, 
  ArrowRight,
  MoreHorizontal,
  Play,
  Volume2
} from 'lucide-react'

interface Conversation {
  id: string
  leadName: string
  status: 'active' | 'qualified' | 'follow-up' | 'archived'
  duration: string
  lastMessage: string
  qualificationScore: number
  propertyInterest: string
  timestamp: string
  priority: 'high' | 'medium' | 'low'
}

export function ConversationManager() {
  const [activeFilter, setActiveFilter] = useState<'all' | 'active' | 'qualified' | 'follow-up'>('all')
  
  const conversations: Conversation[] = [
    {
      id: '1',
      leadName: 'Jennifer Martinez',
      status: 'active',
      duration: '00:03:42',
      lastMessage: 'I\'m interested in viewing the downtown condo this weekend.',
      qualificationScore: 85,
      propertyInterest: '2BR Downtown Condo - $450K',
      timestamp: 'Now',
      priority: 'high'
    },
    {
      id: '2',
      leadName: 'Michael Chen',
      status: 'qualified',
      duration: '00:05:23',
      lastMessage: 'Can you schedule a viewing for tomorrow afternoon?',
      qualificationScore: 92,
      propertyInterest: '3BR Suburban Home - $650K',
      timestamp: '5 min ago',
      priority: 'high'
    },
    {
      id: '3',
      leadName: 'Sarah Williams',
      status: 'follow-up',
      duration: '00:02:15',
      lastMessage: 'I need to discuss this with my spouse first.',
      qualificationScore: 70,
      propertyInterest: '4BR Family Home - $780K',
      timestamp: '1 hour ago',
      priority: 'medium'
    },
    {
      id: '4',
      leadName: 'David Rodriguez',
      status: 'qualified',
      duration: '00:07:45',
      lastMessage: 'What are the HOA fees for this property?',
      qualificationScore: 88,
      propertyInterest: '1BR Luxury Condo - $550K',
      timestamp: '2 hours ago',
      priority: 'medium'
    }
  ]

  const filteredConversations = conversations.filter(conv => 
    activeFilter === 'all' || conv.status === activeFilter
  )

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-500'
      case 'qualified': return 'text-blue-500'
      case 'follow-up': return 'text-yellow-500'
      default: return 'text-muted-foreground'
    }
  }

  const getPriorityIndicator = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-500'
      case 'medium': return 'bg-yellow-500'
      case 'low': return 'bg-green-500'
      default: return 'bg-muted'
    }
  }

  const filters = [
    { key: 'all', label: 'All Conversations', count: conversations.length },
    { key: 'active', label: 'Active', count: conversations.filter(c => c.status === 'active').length },
    { key: 'qualified', label: 'Qualified', count: conversations.filter(c => c.status === 'qualified').length },
    { key: 'follow-up', label: 'Follow-up', count: conversations.filter(c => c.status === 'follow-up').length },
  ]

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold">Recent Conversations</h2>
        <button className="btn btn-ghost text-sm">
          View All
          <ArrowRight className="w-4 h-4 ml-2" />
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-6 overflow-x-auto">
        {filters.map((filter) => (
          <button
            key={filter.key}
            onClick={() => setActiveFilter(filter.key as any)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
              activeFilter === filter.key
                ? 'bg-foreground text-background'
                : 'bg-muted text-muted-foreground hover:bg-accent'
            }`}
          >
            {filter.label}
            <span className={`px-2 py-0.5 rounded-full text-xs ${
              activeFilter === filter.key
                ? 'bg-background/20 text-background'
                : 'bg-background text-foreground'
            }`}>
              {filter.count}
            </span>
          </button>
        ))}
      </div>

      {/* Conversation List */}
      <div className="space-y-3">
        {filteredConversations.map((conversation, index) => (
          <motion.div
            key={conversation.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="p-4 bg-muted rounded-lg hover:bg-accent transition-colors cursor-pointer group"
          >
            <div className="flex items-start justify-between">
              {/* Lead Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <div className={`w-2 h-2 rounded-full ${getPriorityIndicator(conversation.priority)}`} />
                  <h3 className="font-medium text-foreground truncate">
                    {conversation.leadName}
                  </h3>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(conversation.status)} bg-current/10`}>
                    {conversation.status}
                  </span>
                </div>
                
                <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                  {conversation.lastMessage}
                </p>
                
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    <span>{conversation.duration}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Star className="w-3 h-3" />
                    <span>{conversation.qualificationScore}% qualified</span>
                  </div>
                  <span>{conversation.timestamp}</span>
                </div>
                
                <div className="mt-2 text-xs text-muted-foreground truncate">
                  Interest: {conversation.propertyInterest}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button className="p-2 text-muted-foreground hover:text-foreground rounded-lg hover:bg-background">
                  <Play className="w-4 h-4" />
                </button>
                <button className="p-2 text-muted-foreground hover:text-foreground rounded-lg hover:bg-background">
                  <Phone className="w-4 h-4" />
                </button>
                <button className="p-2 text-muted-foreground hover:text-foreground rounded-lg hover:bg-background">
                  <MoreHorizontal className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Quick Actions for Active Conversations */}
            {conversation.status === 'active' && (
              <div className="flex gap-2 mt-3 pt-3 border-t border-border">
                <button className="btn btn-secondary text-xs">
                  Take Over Call
                </button>
                <button className="btn btn-ghost text-xs">
                  Add Notes
                </button>
                <button className="btn btn-ghost text-xs">
                  <Volume2 className="w-3 h-3 mr-1" />
                  Listen In
                </button>
              </div>
            )}
          </motion.div>
        ))}
      </div>

      {/* Empty State */}
      {filteredConversations.length === 0 && (
        <div className="text-center py-12">
          <MessageCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">No conversations found</h3>
          <p className="text-muted-foreground">
            {activeFilter === 'all' 
              ? 'No conversations have been recorded yet.'
              : `No ${activeFilter} conversations available.`
            }
          </p>
        </div>
      )}
    </div>
  )
}