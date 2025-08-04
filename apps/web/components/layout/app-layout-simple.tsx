"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { 
  BarChart3, 
  Bot, 
  Building, 
  Home, 
  Menu, 
  MessageSquare, 
  Phone, 
  Settings, 
  Users, 
  X,
  ChevronDown,
  LogOut,
  User
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { VoiceStatusIndicator } from "@/components/ui/voice-status"
import { OrganizationSwitcher } from "@/components/layout/organization-switcher"
import { cn } from "@/lib/utils"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useAuth } from "@/lib/auth/auth-provider"

interface AppLayoutProps {
  children: React.ReactNode
}

interface NavigationItem {
  name: string
  href: string
  icon: React.ComponentType<any>
  badge?: string
  permission?: string
}

export function AppLayout({ children }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = React.useState(false)
  const pathname = usePathname()
  const { user, logout } = useAuthStore()
  
  // Mock data for demo
  const orgSlug = 'demo-org'
  const activeAgent = { name: 'AI Agent Alpha' }
  const connectionStatus = 'connected'

  const hasPermission = (permission: string) => true // Simplified for demo

  const navigation: NavigationItem[] = [
    {
      name: 'Dashboard',
      href: `/org/${orgSlug}`,
      icon: Home,
    },
    {
      name: 'Voice Agents',
      href: `/org/${orgSlug}/agents`,
      icon: Bot,
      badge: '3',
    },
    {
      name: 'Leads',
      href: `/org/${orgSlug}/leads`,
      icon: Users,
      badge: '12',
    },
    {
      name: 'Conversations',
      href: `/org/${orgSlug}/conversations`,
      icon: MessageSquare,
    },
    {
      name: 'Analytics',
      href: `/org/${orgSlug}/analytics`,
      icon: BarChart3,
    },
    {
      name: 'Properties',
      href: `/org/${orgSlug}/properties`,
      icon: Building,
    },
    {
      name: 'Settings',
      href: `/org/${orgSlug}/settings`,
      icon: Settings,
      permission: 'settings.view',
    },
  ]

  const filteredNavigation = navigation.filter(item => 
    !item.permission || hasPermission(item.permission as any)
  )

  const handleLogout = async () => {
    try {
      await logout()
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        >
          <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" />
        </div>
      )}

      {/* Sidebar */}
      <div className={cn(
        "fixed inset-y-0 left-0 z-50 w-64 bg-card border-r border-border transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0",
        sidebarOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex h-full flex-col">
          {/* Sidebar header */}
          <div className="flex items-center justify-between p-4 border-b border-border">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Phone className="w-4 h-4 text-primary-foreground" />
              </div>
              <span className="font-semibold text-lg">Seiketsu AI</span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="w-4 h-4" />
            </Button>
          </div>

          {/* Organization switcher */}
          <div className="p-4 border-b border-border">
            <OrganizationSwitcher className="w-full" />
          </div>

          {/* Voice agent status */}
          {activeAgent && (
            <div className="p-4 border-b border-border">
              <div className="flex items-center space-x-3 p-3 bg-muted/50 rounded-lg">
                <VoiceStatusIndicator 
                  status={connectionStatus === 'connected' ? 'listening' : 'idle'} 
                  size="sm" 
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{activeAgent.name}</p>
                  <p className="text-xs text-muted-foreground capitalize">
                    {connectionStatus}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            {filteredNavigation.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  <div className="flex items-center space-x-3">
                    <item.icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span className={cn(
                      "px-2 py-0.5 text-xs rounded-full",
                      isActive 
                        ? "bg-primary-foreground/20 text-primary-foreground"
                        : "bg-primary text-primary-foreground"
                    )}>
                      {item.badge}
                    </span>
                  )}
                </Link>
              )
            })}
          </nav>

          {/* User menu */}
          <div className="p-4 border-t border-border">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="w-full justify-start p-2 h-auto">
                  <div className="flex items-center space-x-3 flex-1">
                    <Avatar className="w-8 h-8">
                      <AvatarImage src={user?.avatar} alt={user?.name} />
                      <AvatarFallback>
                        {user?.name?.split(' ').map(n => n[0]).join('').toUpperCase() || 'U'}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 text-left">
                      <p className="text-sm font-medium truncate">{user?.name || 'Demo User'}</p>
                      <p className="text-xs text-muted-foreground truncate">{user?.email || 'demo@seiketsu.ai'}</p>
                    </div>
                    <ChevronDown className="w-4 h-4" />
                  </div>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>My Account</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link href={`/org/${orgSlug}/profile`}>
                    <User className="mr-2 h-4 w-4" />
                    Profile
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link href={`/org/${orgSlug}/settings`}>
                    <Settings className="mr-2 h-4 w-4" />
                    Settings
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col lg:pl-0">
        {/* Mobile header */}
        <header className="lg:hidden flex items-center justify-between p-4 border-b border-border bg-background">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="w-5 h-5" />
          </Button>
          <div className="flex items-center space-x-2">
            <div className="w-6 h-6 bg-primary rounded flex items-center justify-center">
              <Phone className="w-3 h-3 text-primary-foreground" />
            </div>
            <span className="font-semibold">Seiketsu AI</span>
          </div>
          <div className="w-10" /> {/* Spacer for centering */}
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}

// Layout wrapper that includes auth protection
export function ProtectedAppLayout({ children }: AppLayoutProps) {
  const { user, isAuthenticated } = useAuthStore()
  const { isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-semibold mb-2">Access Denied</h1>
          <p className="text-muted-foreground mb-4">Please log in to continue.</p>
          <Button asChild>
            <Link href="/login">Go to Login</Link>
          </Button>
        </div>
      </div>
    )
  }

  return <AppLayout>{children}</AppLayout>
}