'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

// Navigation based on client portal IA from research
const navigationItems = [
  {
    name: 'Dashboard',
    href: '/portal',
    icon: '🏠',
    description: 'Overview and recommendations'
  },
  {
    name: 'My Properties',
    href: '/portal/properties',
    icon: '🔍',
    description: 'Saved searches and favorites'
  },
  {
    name: 'Appointments',
    href: '/portal/appointments',
    icon: '📅',
    description: 'Schedule and manage viewings'
  },
  {
    name: 'My Agent',
    href: '/portal/agent',
    icon: '👤',
    description: 'Contact and performance'
  },
  {
    name: 'Market Insights',
    href: '/portal/market',
    icon: '📊',
    description: 'Neighborhood analysis'
  }
]

export default function ClientNavigation() {
  const pathname = usePathname()
  const [isCollapsed, setIsCollapsed] = useState(false)
  
  return (
    <nav className={`bg-card border-r border-border transition-all duration-300 ${
      isCollapsed ? 'w-16' : 'w-64'
    } hidden md:block`}>
      <div className="p-4 border-b border-border">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="w-full flex items-center justify-between text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
        >
          {!isCollapsed && 'Navigation'}
          <span className="text-lg">{isCollapsed ? '→' : '←'}</span>
        </button>
      </div>
      
      <div className="p-4 space-y-2">
        {navigationItems.map((item) => {
          const isActive = pathname === item.href
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`block w-full p-3 rounded-lg transition-all duration-200 group ${
                isActive
                  ? 'bg-accent text-accent-foreground'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              }`}
            >
              <div className="flex items-center space-x-3">
                <span className="text-lg">{item.icon}</span>
                {!isCollapsed && (
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm">{item.name}</div>
                    <div className="text-xs opacity-75 truncate">{item.description}</div>
                  </div>
                )}
              </div>
            </Link>
          )
        })}
      </div>
      
      {/* Help and support - always accessible per client research */}
      <div className="absolute bottom-4 left-4 right-4">
        <Link
          href="/portal/help"
          className="block w-full p-3 rounded-lg text-center text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition-colors border border-border"
        >
          {isCollapsed ? '?' : 'Need Help?'}
        </Link>
      </div>
    </nav>
  )
}