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

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { OrganizationSwitcher } from "./organization-switcher"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useAuth, usePermissions } from "@/lib/auth/auth-provider"
import { VoiceStatusIndicator } from "@/components/ui/voice-status"
import { useVoiceStore } from "@/lib/stores/voice-store"

interface AppLayoutProps {
  children: React.ReactNode
}

interface NavigationItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  permission?: string
  badge?: string | number
}

export function AppLayout({ children }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = React.useState(false)
  const pathname = usePathname()
  const { user, organization } = useAuthStore()
  const { logout } = useAuth()
  const { hasPermission } = usePermissions()
  const { activeAgent, connectionStatus } = useVoiceStore()

  // Get organization slug from pathname for navigation
  const orgSlug = pathname.split('/')[2] || organization?.slug

  const navigation: NavigationItem[] = [
    {
      name: 'Dashboard',
      href: `/org/${orgSlug}/dashboard`,
      icon: Home,
    },
    {
      name: 'Voice Agents',
      href: `/org/${orgSlug}/agents`,
      icon: Bot,
      permission: 'agents.view',
    },
    {
      name: 'Leads',
      href: `/org/${orgSlug}/leads`,
      icon: Users,
      permission: 'leads.view',
      badge: '12', // This would come from a real-time count
    },
    {
      name: 'Analytics',
      href: `/org/${orgSlug}/analytics`,
      icon: BarChart3,
      permission: 'analytics.view',
    },
    {
      name: 'Conversations',
      href: `/org/${orgSlug}/conversations`,
      icon: MessageSquare,
      permission: 'leads.view',
    },
    {
      name: 'Settings',
      href: `/org/${orgSlug}/settings`,
      icon: Settings,
      permission: 'settings.view',
    },
  ]\n\n  const filteredNavigation = navigation.filter(item => \n    !item.permission || hasPermission(item.permission as any)\n  )\n\n  const handleLogout = async () => {\n    try {\n      await logout()\n    } catch (error) {\n      console.error('Logout failed:', error)\n    }\n  }\n\n  return (\n    <div className=\"flex h-screen bg-background\">\n      {/* Mobile sidebar overlay */}\n      {sidebarOpen && (\n        <div \n          className=\"fixed inset-0 z-40 lg:hidden\"\n          onClick={() => setSidebarOpen(false)}\n        >\n          <div className=\"absolute inset-0 bg-background/80 backdrop-blur-sm\" />\n        </div>\n      )}\n\n      {/* Sidebar */}\n      <div className={cn(\n        \"fixed inset-y-0 left-0 z-50 w-64 bg-card border-r border-border transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0\",\n        sidebarOpen ? \"translate-x-0\" : \"-translate-x-full\"\n      )}>\n        <div className=\"flex h-full flex-col\">\n          {/* Sidebar header */}\n          <div className=\"flex items-center justify-between p-4 border-b border-border\">\n            <div className=\"flex items-center space-x-2\">\n              <div className=\"w-8 h-8 bg-primary rounded-lg flex items-center justify-center\">\n                <Phone className=\"w-4 h-4 text-primary-foreground\" />\n              </div>\n              <span className=\"font-semibold text-lg\">Seiketsu AI</span>\n            </div>\n            <Button\n              variant=\"ghost\"\n              size=\"icon\"\n              className=\"lg:hidden\"\n              onClick={() => setSidebarOpen(false)}\n            >\n              <X className=\"w-4 h-4\" />\n            </Button>\n          </div>\n\n          {/* Organization switcher */}\n          <div className=\"p-4 border-b border-border\">\n            <OrganizationSwitcher className=\"w-full\" />\n          </div>\n\n          {/* Voice agent status */}\n          {activeAgent && (\n            <div className=\"p-4 border-b border-border\">\n              <div className=\"flex items-center space-x-3 p-3 bg-muted/50 rounded-lg\">\n                <VoiceStatusIndicator \n                  status={connectionStatus === 'connected' ? 'listening' : 'idle'} \n                  size=\"sm\" \n                />\n                <div className=\"flex-1 min-w-0\">\n                  <p className=\"text-sm font-medium truncate\">{activeAgent.name}</p>\n                  <p className=\"text-xs text-muted-foreground capitalize\">\n                    {connectionStatus}\n                  </p>\n                </div>\n              </div>\n            </div>\n          )}\n\n          {/* Navigation */}\n          <nav className=\"flex-1 p-4 space-y-1 overflow-y-auto\">\n            {filteredNavigation.map((item) => {\n              const isActive = pathname === item.href\n              return (\n                <Link\n                  key={item.name}\n                  href={item.href}\n                  className={cn(\n                    \"flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors\",\n                    isActive\n                      ? \"bg-primary text-primary-foreground\"\n                      : \"text-muted-foreground hover:bg-muted hover:text-foreground\"\n                  )}\n                >\n                  <div className=\"flex items-center space-x-3\">\n                    <item.icon className=\"w-4 h-4\" />\n                    <span>{item.name}</span>\n                  </div>\n                  {item.badge && (\n                    <span className={cn(\n                      \"px-2 py-0.5 text-xs rounded-full\",\n                      isActive \n                        ? \"bg-primary-foreground/20 text-primary-foreground\"\n                        : \"bg-primary text-primary-foreground\"\n                    )}>\n                      {item.badge}\n                    </span>\n                  )}\n                </Link>\n              )\n            })}\n          </nav>\n\n          {/* User menu */}\n          <div className=\"p-4 border-t border-border\">\n            <DropdownMenu>\n              <DropdownMenuTrigger asChild>\n                <Button variant=\"ghost\" className=\"w-full justify-start p-2 h-auto\">\n                  <div className=\"flex items-center space-x-3 flex-1\">\n                    <Avatar className=\"w-8 h-8\">\n                      <AvatarImage src={user?.avatar} alt={user?.name} />\n                      <AvatarFallback>\n                        {user?.name?.split(' ').map(n => n[0]).join('').toUpperCase() || 'U'}\n                      </AvatarFallback>\n                    </Avatar>\n                    <div className=\"flex-1 text-left\">\n                      <p className=\"text-sm font-medium truncate\">{user?.name}</p>\n                      <p className=\"text-xs text-muted-foreground truncate\">{user?.email}</p>\n                    </div>\n                    <ChevronDown className=\"w-4 h-4\" />\n                  </div>\n                </Button>\n              </DropdownMenuTrigger>\n              <DropdownMenuContent align=\"end\" className=\"w-56\">\n                <DropdownMenuLabel>My Account</DropdownMenuLabel>\n                <DropdownMenuSeparator />\n                <DropdownMenuItem asChild>\n                  <Link href={`/org/${orgSlug}/profile`}>\n                    <User className=\"mr-2 h-4 w-4\" />\n                    Profile\n                  </Link>\n                </DropdownMenuItem>\n                <DropdownMenuItem asChild>\n                  <Link href={`/org/${orgSlug}/settings`}>\n                    <Settings className=\"mr-2 h-4 w-4\" />\n                    Settings\n                  </Link>\n                </DropdownMenuItem>\n                <DropdownMenuSeparator />\n                <DropdownMenuItem onClick={handleLogout}>\n                  <LogOut className=\"mr-2 h-4 w-4\" />\n                  Log out\n                </DropdownMenuItem>\n              </DropdownMenuContent>\n            </DropdownMenu>\n          </div>\n        </div>\n      </div>\n\n      {/* Main content */}\n      <div className=\"flex-1 flex flex-col lg:pl-0\">\n        {/* Mobile header */}\n        <header className=\"lg:hidden flex items-center justify-between p-4 border-b border-border bg-background\">\n          <Button\n            variant=\"ghost\"\n            size=\"icon\"\n            onClick={() => setSidebarOpen(true)}\n          >\n            <Menu className=\"w-5 h-5\" />\n          </Button>\n          <div className=\"flex items-center space-x-2\">\n            <div className=\"w-6 h-6 bg-primary rounded flex items-center justify-center\">\n              <Phone className=\"w-3 h-3 text-primary-foreground\" />\n            </div>\n            <span className=\"font-semibold\">Seiketsu AI</span>\n          </div>\n          <div className=\"w-10\" /> {/* Spacer for centering */}\n        </header>\n\n        {/* Page content */}\n        <main className=\"flex-1 overflow-auto\">\n          {children}\n        </main>\n      </div>\n    </div>\n  )\n}\n\n// Layout wrapper that includes auth protection\nexport function ProtectedAppLayout({ children }: AppLayoutProps) {\n  const { user, isAuthenticated } = useAuthStore()\n  const { isLoading } = useAuth()\n\n  if (isLoading) {\n    return (\n      <div className=\"flex items-center justify-center min-h-screen\">\n        <div className=\"flex flex-col items-center space-y-4\">\n          <div className=\"animate-spin rounded-full h-8 w-8 border-b-2 border-primary\"></div>\n          <p className=\"text-sm text-muted-foreground\">Loading...</p>\n        </div>\n      </div>\n    )\n  }\n\n  if (!isAuthenticated || !user) {\n    return (\n      <div className=\"flex items-center justify-center min-h-screen\">\n        <div className=\"text-center\">\n          <h1 className=\"text-2xl font-semibold mb-2\">Access Denied</h1>\n          <p className=\"text-muted-foreground mb-4\">Please log in to continue.</p>\n          <Button asChild>\n            <Link href=\"/login\">Go to Login</Link>\n          </Button>\n        </div>\n      </div>\n    )\n  }\n\n  return <AppLayout>{children}</AppLayout>\n}"