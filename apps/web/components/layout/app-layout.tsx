'use client'

import React from 'react'
import Link from 'next/link'

interface AppLayoutProps {
  children: React.ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex h-screen bg-background">
      {/* Simple sidebar */}
      <div className="w-64 bg-card border-r border-border p-4">
        <div className="flex items-center space-x-2 mb-6">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-primary-foreground text-sm">S</span>
          </div>
          <span className="font-semibold text-lg">Seiketsu AI</span>
        </div>
        
        {/* Navigation */}
        <nav className="space-y-2">
          <Link href="/dashboard" className="block px-3 py-2 rounded-lg text-sm hover:bg-muted">
            Dashboard
          </Link>
          <Link href="/agents" className="block px-3 py-2 rounded-lg text-sm hover:bg-muted">
            Voice Agents
          </Link>
          <Link href="/leads" className="block px-3 py-2 rounded-lg text-sm hover:bg-muted">
            Leads
          </Link>
          <Link href="/analytics" className="block px-3 py-2 rounded-lg text-sm hover:bg-muted">
            Analytics
          </Link>
        </nav>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col">
        <header className="border-b border-border p-4">
          <h1 className="text-xl font-semibold">Seiketsu AI Platform</h1>
        </header>
        
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  )
}

// Layout wrapper that includes auth protection
export function ProtectedAppLayout({ children }: AppLayoutProps) {
  return <AppLayout>{children}</AppLayout>
}
