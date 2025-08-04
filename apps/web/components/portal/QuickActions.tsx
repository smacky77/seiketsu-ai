'use client'

import { useState } from 'react'

// Quick actions based on client self-service needs from UX research
export default function QuickActions() {
  const [showVoiceSearch, setShowVoiceSearch] = useState(false)
  
  const quickActions = [
    {
      icon: '🎤',
      title: 'Voice Search',
      description: 'Tell us what you\'re looking for',
      action: () => setShowVoiceSearch(true),
      primary: true
    },
    {
      icon: '📅',
      title: 'Schedule Viewing',
      description: 'Book your next appointment',
      action: () => {},
      primary: false
    },
    {
      icon: '📊',
      title: 'Market Report',
      description: 'Get neighborhood insights',
      action: () => {},
      primary: false
    },
    {
      icon: '💬',
      title: 'Contact Agent',
      description: 'Reach Michael directly',
      action: () => {},
      primary: false
    }
  ]
  
  return (
    <>
      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-lg font-bold text-foreground mb-4">Quick Actions</h2>
        
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action, index) => (
            <button
              key={index}
              onClick={action.action}
              className={`p-4 rounded-lg text-left transition-all duration-200 ${
                action.primary
                  ? 'bg-foreground text-background hover:bg-muted-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              }`}
            >
              <div className="text-2xl mb-2">{action.icon}</div>
              <div className="font-medium text-sm mb-1">{action.title}</div>
              <div className="text-xs opacity-75">{action.description}</div>
            </button>
          ))}
        </div>
      </div>
      
      {/* Voice Search Modal */}
      {showVoiceSearch && (
        <div className="fixed inset-0 bg-background bg-opacity-90 flex items-center justify-center z-50">
          <div className="bg-card border border-border rounded-lg p-8 max-w-md w-full mx-4">
            <div className="text-center">
              <div className="text-6xl mb-4">🎤</div>
              <h3 className="text-xl font-bold text-foreground mb-2">
                Voice Property Search
              </h3>
              <p className="text-sm text-muted-foreground mb-6">
                Describe what you're looking for and I'll find matching properties
              </p>
              
              {/* Simulated voice interface */}
              <div className="bg-muted rounded-lg p-4 mb-6">
                <div className="flex items-center justify-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                </div>
                <div className="text-sm text-foreground mt-2">
                  Listening... Try saying "Show me 2-bedroom condos under $600K in Capitol Hill"
                </div>
              </div>
              
              <div className="flex space-x-3">
                <button 
                  onClick={() => setShowVoiceSearch(false)}
                  className="btn btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button className="btn btn-primary flex-1">
                  Start Recording
                </button>
              </div>
              
              {/* Alternative text input */}
              <div className="mt-4 text-xs text-muted-foreground">
                Or type your search:
                <input 
                  type="text" 
                  placeholder="Describe your ideal property..."
                  className="w-full mt-2 p-2 border border-border rounded bg-background text-foreground text-sm"
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}