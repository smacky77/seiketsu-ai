'use client'

import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  VoiceAgentControlCenter,
  LeadManagementSystem,
  MultiTenantAdmin,
  RealTimeCommunicationHub,
  AnalyticsDashboard,
  IntegrationManagementCenter
} from '@/components/enterprise'
import {
  Mic,
  Users,
  Building2,
  MessageSquare,
  BarChart3,
  Globe,
  ArrowRight,
  CheckCircle,
  Star,
  Zap
} from 'lucide-react'

const componentInfo = {
  'voice-control': {
    title: 'Voice Agent Control Center',
    description: 'Real-time monitoring and control of AI voice agents with advanced metrics and intervention capabilities.',
    icon: Mic,
    features: [
      'Real-time agent status monitoring',
      'Live call tracking with quality metrics',
      'Emergency intervention controls',
      'Audio level monitoring',
      'Performance analytics'
    ]
  },
  'lead-management': {
    title: 'Lead Management System',
    description: 'Advanced lead qualification pipeline with search, filtering, and conversation history tracking.',
    icon: Users,
    features: [
      'Advanced filtering and search',
      'Lead scoring and prioritization',
      'Conversation history tracking',
      'Automated follow-up scheduling',
      'CRM integration sync'
    ]
  },
  'multi-tenant': {
    title: 'Multi-Tenant Administration',
    description: 'Organization management interface with user roles, billing, and usage analytics.',
    icon: Building2,
    features: [
      'Organization overview dashboard',
      'User role management',
      'Billing and subscription tracking',
      'Usage analytics and limits',
      'Revenue tracking'
    ]
  },
  'communication': {
    title: 'Real-Time Communication Hub',
    description: 'Live conversation monitoring with team collaboration and performance tracking.',
    icon: MessageSquare,
    features: [
      'Live call monitoring',
      'Real-time transcript display',
      'Team chat and collaboration',
      'Agent status dashboard',
      'Performance benchmarking'
    ]
  },
  'analytics': {
    title: 'Analytics Dashboard',
    description: 'Enterprise analytics with ROI tracking, conversion metrics, and performance insights.',
    icon: BarChart3,
    features: [
      'Comprehensive metrics overview',
      'Interactive visualizations',
      'Conversion funnel analysis',
      'Agent performance leaderboards',
      'Customer satisfaction trends'
    ]
  },
  'integrations': {
    title: 'Integration Management Center',
    description: 'CRM, MLS, and third-party service integration management with monitoring.',
    icon: Globe,
    features: [
      'Integration status monitoring',
      'API endpoint health tracking',
      'Webhook management',
      'Rate limit monitoring',
      'Configuration management'
    ]
  }
}

export default function EnterpriseDemo() {
  const [activeTab, setActiveTab] = useState('voice-control')

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-card">
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">Enterprise Components Demo</h1>
              <p className="text-lg text-muted-foreground">
                Advanced production-ready interfaces for Seiketsu AI's Voice Agent Platform
              </p>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span>Production Ready</span>
              <Star className="w-4 h-4 text-yellow-500" />
              <span>Enterprise Grade</span>
              <Zap className="w-4 h-4 text-blue-500" />
              <span>High Performance</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          {/* Tab Navigation */}
          <div className="mb-8">
            <TabsList className="grid grid-cols-2 lg:grid-cols-6 h-auto p-1 bg-muted">
              {Object.entries(componentInfo).map(([key, info]) => {
                const Icon = info.icon
                return (
                  <TabsTrigger
                    key={key}
                    value={key}
                    className="flex flex-col items-center gap-2 py-4 px-3 data-[state=active]:bg-background"
                  >
                    <Icon className="w-5 h-5" />
                    <span className="text-xs font-medium text-center leading-tight">
                      {info.title.split(' ').slice(0, 2).join(' ')}
                    </span>
                  </TabsTrigger>
                )
              })}
            </TabsList>
          </div>

          {/* Component Info Cards */}
          <div className="mb-8">
            <Card>
              <CardHeader>
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-primary/10 rounded-lg">
                    {(() => {
                      const Icon = componentInfo[activeTab as keyof typeof componentInfo]?.icon
                      return Icon ? <Icon className="w-8 h-8 text-primary" /> : null
                    })()}
                  </div>
                  <div className="flex-1">
                    <CardTitle className="text-2xl mb-2">
                      {componentInfo[activeTab as keyof typeof componentInfo]?.title}
                    </CardTitle>
                    <CardDescription className="text-base">
                      {componentInfo[activeTab as keyof typeof componentInfo]?.description}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
                  {componentInfo[activeTab as keyof typeof componentInfo]?.features.map((feature, index) => (
                    <div key={index} className="flex items-center gap-2 p-3 bg-muted/50 rounded-lg">
                      <ArrowRight className="w-4 h-4 text-primary flex-shrink-0" />
                      <span className="text-sm font-medium">{feature}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Component Demos */}
          <TabsContent value="voice-control" className="mt-0">
            <VoiceAgentControlCenter className="animate-in" />
          </TabsContent>

          <TabsContent value="lead-management" className="mt-0">
            <LeadManagementSystem className="animate-in" />
          </TabsContent>

          <TabsContent value="multi-tenant" className="mt-0">
            <MultiTenantAdmin className="animate-in" />
          </TabsContent>

          <TabsContent value="communication" className="mt-0">
            <RealTimeCommunicationHub className="animate-in" />
          </TabsContent>

          <TabsContent value="analytics" className="mt-0">
            <AnalyticsDashboard className="animate-in" />
          </TabsContent>

          <TabsContent value="integrations" className="mt-0">
            <IntegrationManagementCenter className="animate-in" />
          </TabsContent>
        </Tabs>
      </div>

      {/* Footer */}
      <div className="border-t bg-muted/50 mt-16">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center text-muted-foreground">
            <p className="mb-2">
              These components are built with React 18, TypeScript, Tailwind CSS, and Framer Motion
            </p>
            <p className="text-sm">
              Fully accessible (WCAG 2.1 AA), responsive, and optimized for production deployment
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}