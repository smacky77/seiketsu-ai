'use client'

import { useState } from 'react'
import AgentProfile from '@/components/portal/AgentProfile'
import CommunicationHistory from '@/components/portal/CommunicationHistory'
import PerformanceMetrics from '@/components/portal/PerformanceMetrics'
import ContactMethods from '@/components/portal/ContactMethods'

export default function AgentPage() {
  const [activeTab, setActiveTab] = useState<'profile' | 'communication' | 'performance'>('profile')
  
  const tabs = [
    { id: 'profile', label: 'Agent Profile', icon: '👤' },
    { id: 'communication', label: 'Messages', icon: '💬' },
    { id: 'performance', label: 'Performance', icon: '📊' }
  ]
  
  return (
    <div className="space-y-6">
      {/* Page header with agent connection emphasis */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <div>
            <h1 className="text-2xl font-bold text-foreground">My Agent</h1>
            <p className="text-muted-foreground">
              Your dedicated real estate professional
            </p>
          </div>
          
          {/* Agent availability indicator */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-sm text-muted-foreground">Available now</span>
            </div>
            <ContactMethods compact />
          </div>
        </div>
      </div>
      
      {/* Tab navigation */}
      <div className="border-b border-border">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-foreground text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
      
      {/* Tab content */}
      <div className="min-h-96">
        {activeTab === 'profile' && <AgentProfile />}
        {activeTab === 'communication' && <CommunicationHistory />}
        {activeTab === 'performance' && <PerformanceMetrics />}
      </div>
    </div>
  )
}