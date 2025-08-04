'use client'

import { useState } from 'react'

// Trust-building header based on UX research
export default function ClientHeader() {
  const [showNotifications, setShowNotifications] = useState(false)
  
  return (
    <header className="bg-card border-b border-border px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Seiketsu branding with trust indicators */}
        <div className="flex items-center space-x-4">
          <div className="text-xl font-bold text-foreground">Seiketsu AI</div>
          <div className="hidden sm:flex items-center space-x-2 text-sm text-muted-foreground">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span>System Active</span>
          </div>
        </div>
        
        {/* Trust-building status indicators */}
        <div className="flex items-center space-x-6">
          {/* Agent availability status */}
          <div className="hidden md:flex items-center space-x-2 text-sm">
            <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center">
              👤
            </div>
            <div>
              <div className="font-medium">Michael Chen</div>
              <div className="text-xs text-muted-foreground">Available now</div>
            </div>
          </div>
          
          {/* Notification indicator */}
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative p-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            <span className="text-lg">🔔</span>
            <span className="absolute -top-1 -right-1 w-4 h-4 bg-accent text-accent-foreground text-xs rounded-full flex items-center justify-center">
              2
            </span>
          </button>
          
          {/* Quick contact button */}
          <button className="btn btn-primary text-sm">
            Contact Agent
          </button>
        </div>
      </div>
      
      {/* Notifications dropdown */}
      {showNotifications && (
        <div className="absolute top-full right-6 mt-2 w-80 bg-card border border-border rounded-lg shadow-lg z-50">
          <div className="p-4 border-b border-border">
            <h3 className="font-medium">Recent Updates</h3>
          </div>
          <div className="p-4 space-y-3">
            <div className="text-sm">
              <div className="font-medium">New property match found</div>
              <div className="text-muted-foreground">Capitol Hill condo - $565K</div>
              <div className="text-xs text-muted-foreground">2 hours ago</div>
            </div>
            <div className="text-sm">
              <div className="font-medium">Appointment confirmed</div>
              <div className="text-muted-foreground">Tomorrow at 2:00 PM</div>
              <div className="text-xs text-muted-foreground">4 hours ago</div>
            </div>
          </div>
        </div>
      )}
    </header>
  )
}