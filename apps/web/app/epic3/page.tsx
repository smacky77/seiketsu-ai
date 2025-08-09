'use client'

import React from 'react'
import { MarketIntelligenceDashboard } from '@/components/epic3/MarketIntelligenceDashboard'
import { CommunicationWorkflowPanel } from '@/components/epic3/CommunicationWorkflowPanel'
import { IntelligentSchedulingSystem } from '@/components/epic3/IntelligentSchedulingSystem'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ExternalLink } from 'lucide-react'

export default function Epic3Page() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 p-4">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-slate-900">
            Epic 3: Advanced Real Estate Market Intelligence
          </h1>
          <p className="text-xl text-slate-600 max-w-3xl mx-auto">
            Leverage AI-driven market analysis, automated communication workflows, 
            and intelligent scheduling to revolutionize your real estate operations.
          </p>
          <div className="flex justify-center gap-4">
            <Button asChild>
              <a href="/epic3/monitoring">
                <ExternalLink className="w-4 h-4 mr-2" />
                Monitoring Dashboard
              </a>
            </Button>
          </div>
        </div>

        {/* Market Intelligence Dashboard */}
        <section>
          <Card className="border-2 border-blue-200 shadow-lg">
            <CardHeader className="bg-blue-50">
              <CardTitle className="text-2xl text-blue-900">
                Market Intelligence Dashboard
              </CardTitle>
              <CardDescription className="text-blue-700">
                AI-powered market analysis, property value predictions, and competitive insights
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              <MarketIntelligenceDashboard />
            </CardContent>
          </Card>
        </section>

        {/* Communication Workflow System */}
        <section>
          <Card className="border-2 border-green-200 shadow-lg">
            <CardHeader className="bg-green-50">
              <CardTitle className="text-2xl text-green-900">
                Automated Communication System
              </CardTitle>
              <CardDescription className="text-green-700">
                Email automation, SMS messaging, and personalized follow-up sequences
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              <CommunicationWorkflowPanel />
            </CardContent>
          </Card>
        </section>

        {/* Intelligent Scheduling */}
        <section>
          <Card className="border-2 border-purple-200 shadow-lg">
            <CardHeader className="bg-purple-50">
              <CardTitle className="text-2xl text-purple-900">
                Intelligent Scheduling System
              </CardTitle>
              <CardDescription className="text-purple-700">
                Smart appointment booking with availability management and automated reminders
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              <IntelligentSchedulingSystem />
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  )
}