'use client'

// Communication transparency based on client trust patterns from UX research
interface Activity {
  id: string
  type: 'message' | 'viewing' | 'recommendation' | 'update' | 'document'
  title: string
  description: string
  timestamp: string
  agent?: string
  status?: 'read' | 'unread'
  actionRequired?: boolean
}

const mockActivities: Activity[] = [
  {
    id: '1',
    type: 'recommendation',
    title: 'New property match found',
    description: '3-bedroom condo in Capitol Hill matches your criteria - $565K',
    timestamp: '2024-08-03T16:30:00',
    agent: 'Michael Chen',
    status: 'unread',
    actionRequired: true
  },
  {
    id: '2',
    type: 'message',
    title: 'Message from Michael',
    description: 'Great viewing today! I\'ve prepared a market analysis for the Pine St property.',
    timestamp: '2024-08-03T14:15:00',
    agent: 'Michael Chen',
    status: 'read'
  },
  {
    id: '3',
    type: 'viewing',
    title: 'Viewing completed',
    description: 'Pine St #304 viewing completed - feedback requested',
    timestamp: '2024-08-03T14:00:00',
    agent: 'Michael Chen',
    status: 'read',
    actionRequired: true
  },
  {
    id: '4',
    type: 'document',
    title: 'Market analysis ready',
    description: 'Capitol Hill neighborhood report and comparable sales analysis',
    timestamp: '2024-08-03T11:30:00',
    agent: 'Michael Chen',
    status: 'read'
  },
  {
    id: '5',
    type: 'update',
    title: 'Search preferences updated',
    description: 'Budget range adjusted to $450K-$600K based on our conversation',
    timestamp: '2024-08-02T16:45:00',
    agent: 'Michael Chen',
    status: 'read'
  }
]

export default function RecentActivity() {
  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'message': return '💬'
      case 'viewing': return '🏠'
      case 'recommendation': return '✨'
      case 'update': return '🔄'
      case 'document': return '📄'
      default: return '🔔'
    }
  }
  
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))
    
    if (diffHours < 1) return 'Just now'
    if (diffHours < 24) return `${diffHours}h ago`
    
    const diffDays = Math.floor(diffHours / 24)
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays} days ago`
    
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    })
  }
  
  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-foreground">Recent Activity</h2>
          <p className="text-sm text-muted-foreground">
            Communication history and updates
          </p>
        </div>
        <button className="btn btn-ghost text-sm">
          View All
        </button>
      </div>
      
      <div className="space-y-4">
        {mockActivities.map((activity) => (
          <div
            key={activity.id}
            className={`flex items-start space-x-4 p-4 rounded-lg transition-colors ${
              activity.status === 'unread'
                ? 'bg-accent border-l-4 border-foreground'
                : 'bg-muted'
            }`}
          >
            {/* Activity icon */}
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
              activity.status === 'unread'
                ? 'bg-foreground text-background'
                : 'bg-background text-foreground'
            }`}>
              {getActivityIcon(activity.type)}
            </div>
            
            {/* Activity content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between mb-1">
                <div className="font-medium text-foreground">
                  {activity.title}
                  {activity.actionRequired && (
                    <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                      Action Required
                    </span>
                  )}
                </div>
                <div className="text-xs text-muted-foreground whitespace-nowrap ml-4">
                  {formatTimestamp(activity.timestamp)}
                </div>
              </div>
              
              <div className="text-sm text-muted-foreground mb-2">
                {activity.description}
              </div>
              
              {activity.agent && (
                <div className="text-xs text-muted-foreground">
                  from {activity.agent}
                </div>
              )}
              
              {/* Quick actions for actionable items */}
              {activity.actionRequired && (
                <div className="mt-3 flex space-x-2">
                  {activity.type === 'recommendation' && (
                    <>
                      <button className="btn btn-primary text-xs">
                        View Property
                      </button>
                      <button className="btn btn-secondary text-xs">
                        Schedule Viewing
                      </button>
                    </>
                  )}
                  {activity.type === 'viewing' && (
                    <>
                      <button className="btn btn-primary text-xs">
                        Give Feedback
                      </button>
                      <button className="btn btn-secondary text-xs">
                        View Photos
                      </button>
                    </>
                  )}
                  <button className="btn btn-ghost text-xs">
                    Mark as Read
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      
      {/* Communication preferences */}
      <div className="mt-6 p-4 bg-muted rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-medium text-foreground">Notification Preferences</div>
            <div className="text-sm text-muted-foreground">
              Choose how you want to be updated
            </div>
          </div>
          <button className="btn btn-secondary text-sm">
            Customize
          </button>
        </div>
      </div>
    </div>
  )
}