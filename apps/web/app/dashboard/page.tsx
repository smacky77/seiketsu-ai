'use client'

import { VoiceAgentWorkspace } from '../../components/dashboard/VoiceAgentWorkspace'
import { ConversationManager } from '../../components/dashboard/ConversationManager'
import { LeadQualificationPanel } from '../../components/dashboard/LeadQualificationPanel'
import { PerformanceMetrics } from '../../components/dashboard/PerformanceMetrics'
import { DashboardLayout } from '../../components/dashboard/DashboardLayout'

export default function AgentDashboard() {
  return (
    <DashboardLayout>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-6">
        {/* Primary Workspace - Voice Agent Controls */}
        <div className="lg:col-span-2 space-y-6">
          <VoiceAgentWorkspace />
          <ConversationManager />
        </div>
        
        {/* Secondary Panel - Lead Intelligence & Performance */}
        <div className="space-y-6">
          <LeadQualificationPanel />
          <PerformanceMetrics />
        </div>
      </div>
    </DashboardLayout>
  )
}