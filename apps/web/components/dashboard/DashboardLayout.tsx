'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Mic, 
  Phone, 
  Users, 
  BarChart3, 
  Settings, 
  Bell,
  Search,
  Menu,
  X
} from 'lucide-react'

interface DashboardLayoutProps {
  children: React.ReactNode
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  
  const navigation = [
    { name: 'Voice Agent', href: '/dashboard', icon: Mic, current: true },
    { name: 'Conversations', href: '/dashboard/conversations', icon: Phone },
    { name: 'Leads', href: '/dashboard/leads', icon: Users },
    { name: 'Performance', href: '/dashboard/performance', icon: BarChart3 },
    { name: 'Settings', href: '/dashboard/settings', icon: Settings },
  ]

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <motion.div
        initial={false}
        animate={{ x: sidebarOpen ? 0 : '-100%' }}
        className="fixed inset-y-0 left-0 z-50 w-64 bg-card border-r border-border lg:translate-x-0 lg:static lg:inset-0"
      >
        <div className="flex h-16 items-center gap-2 px-6 border-b border-border">
          <div className="w-8 h-8 bg-foreground rounded-lg flex items-center justify-center">
            <Mic className="w-5 h-5 text-background" />
          </div>
          <span className="text-lg font-semibold">Seiketsu AI</span>
          <button
            onClick={() => setSidebarOpen(false)}
            className="ml-auto p-1 lg:hidden"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 p-4">
          <ul className="space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon
              return (
                <li key={item.name}>
                  <a
                    href={item.href}
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      item.current
                        ? 'bg-accent text-accent-foreground'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    {item.name}
                  </a>
                </li>
              )
            })}
          </ul>
        </nav>

        {/* Agent Status */}
        <div className="p-4 border-t border-border">
          <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground">Agent Active</p>
              <p className="text-xs text-muted-foreground truncate">
                Voice system operational
              </p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Mobile overlay for sidebar */}
        {sidebarOpen && (
          <div 
            className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
        {/* Top header */}
        <header className="sticky top-0 z-30 bg-background/80 backdrop-blur-lg border-b border-border">
          <div className="flex h-16 items-center gap-4 px-6">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 lg:hidden"
            >
              <Menu className="w-5 h-5" />
            </button>

            {/* Search */}
            <div className="flex-1 max-w-lg">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search conversations, leads, properties..."
                  className="w-full pl-10 pr-4 py-2 bg-muted rounded-lg border-0 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-foreground"
                />
              </div>
            </div>

            {/* Notifications */}
            <button className="relative p-2 text-muted-foreground hover:text-foreground">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
            </button>

            {/* Agent profile */}
            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-sm font-medium">Sarah Chen</p>
                <p className="text-xs text-muted-foreground">Real Estate Agent</p>
              </div>
              <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center">
                <span className="text-sm font-medium">SC</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="min-h-[calc(100vh-4rem)]">
          {children}
        </main>
      </div>
    </div>
  )
}