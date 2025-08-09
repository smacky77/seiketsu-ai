'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { 
  Mail, 
  MessageSquare, 
  Clock, 
  Users, 
  Send, 
  Settings,
  Play,
  Pause,
  BarChart3,
  Target,
  Zap,
  CheckCircle,
  AlertCircle
} from 'lucide-react'

interface EmailCampaign {
  id: string
  name: string
  status: 'active' | 'paused' | 'draft'
  sent: number
  opened: number
  clicked: number
  leads: number
}

interface SMSCampaign {
  id: string
  name: string
  status: 'active' | 'paused' | 'draft'
  sent: number
  delivered: number
  responded: number
}

interface FollowUpSequence {
  id: string
  name: string
  triggerType: 'property_view' | 'inquiry' | 'showing_request' | 'manual'
  steps: number
  active: boolean
  completionRate: number
}

export function CommunicationWorkflowPanel() {
  const [selectedCampaign, setSelectedCampaign] = useState<string | null>(null)
  
  const emailCampaigns: EmailCampaign[] = [
    {
      id: '1',
      name: 'New Listing Alerts - Premium',
      status: 'active',
      sent: 2847,
      opened: 1423,
      clicked: 456,
      leads: 89
    },
    {
      id: '2', 
      name: 'Market Update Newsletter',
      status: 'active',
      sent: 5621,
      opened: 2810,
      clicked: 234,
      leads: 34
    },
    {
      id: '3',
      name: 'First-Time Buyer Guide',
      status: 'paused',
      sent: 1205,
      opened: 723,
      clicked: 187,
      leads: 45
    }
  ]

  const smsCampaigns: SMSCampaign[] = [
    {
      id: '1',
      name: 'Showing Confirmations',
      status: 'active',
      sent: 1456,
      delivered: 1441,
      responded: 892
    },
    {
      id: '2',
      name: 'Price Drop Alerts',
      status: 'active', 
      sent: 892,
      delivered: 889,
      responded: 234
    },
    {
      id: '3',
      name: 'Open House Reminders',
      status: 'active',
      sent: 567,
      delivered: 563,
      responded: 123
    }
  ]

  const followUpSequences: FollowUpSequence[] = [
    {
      id: '1',
      name: 'Property Inquiry Follow-up',
      triggerType: 'inquiry',
      steps: 5,
      active: true,
      completionRate: 78
    },
    {
      id: '2',
      name: 'Post-Showing Nurture',
      triggerType: 'showing_request',
      steps: 3,
      active: true,
      completionRate: 85
    },
    {
      id: '3',
      name: 'Warm Lead Cultivation',
      triggerType: 'property_view',
      steps: 7,
      active: true,
      completionRate: 62
    }
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'paused':
        return <Pause className="h-4 w-4 text-yellow-600" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-600" />
    }
  }

  const getTriggerTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'property_view': 'Property View',
      'inquiry': 'Inquiry Submitted', 
      'showing_request': 'Showing Requested',
      'manual': 'Manual Trigger'
    }
    return labels[type] || type
  }

  return (
    <div className="space-y-6">
      {/* Communication Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Messages Sent
            </CardTitle>
            <Send className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12,847</div>
            <p className="text-xs text-muted-foreground">
              +18.2% from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Engagement Rate
            </CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">24.5%</div>
            <p className="text-xs text-muted-foreground">
              +3.1% from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Generated Leads
            </CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">168</div>
            <p className="text-xs text-muted-foreground">
              +12.8% from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Response Time
            </CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">4.2m</div>
            <p className="text-xs text-muted-foreground">
              Average response time
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Communication Workflow Tabs */}
      <Tabs defaultValue="email" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="email">Email Campaigns</TabsTrigger>
          <TabsTrigger value="sms">SMS Messaging</TabsTrigger>
          <TabsTrigger value="sequences">Follow-up Sequences</TabsTrigger>
          <TabsTrigger value="personalization">Personalization</TabsTrigger>
        </TabsList>

        <TabsContent value="email" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Email Campaigns</h3>
            <Button>
              <Mail className="h-4 w-4 mr-2" />
              Create Campaign
            </Button>
          </div>

          <div className="space-y-4">
            {emailCampaigns.map((campaign) => (
              <Card key={campaign.id} className="cursor-pointer hover:shadow-md transition-shadow"
                    onClick={() => setSelectedCampaign(campaign.id)}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      {getStatusIcon(campaign.status)}
                      {campaign.name}
                    </CardTitle>
                    <div className="flex gap-2">
                      <Button size="sm" variant="ghost">
                        <Settings className="h-4 w-4" />
                      </Button>
                      <Button size="sm" variant="ghost">
                        <BarChart3 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-slate-600">Sent</div>
                      <div className="font-bold text-lg">{campaign.sent.toLocaleString()}</div>
                    </div>
                    <div>
                      <div className="text-slate-600">Opened</div>
                      <div className="font-bold text-lg text-blue-600">
                        {campaign.opened.toLocaleString()}
                      </div>
                      <div className="text-xs text-slate-500">
                        {((campaign.opened / campaign.sent) * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-slate-600">Clicked</div>
                      <div className="font-bold text-lg text-green-600">
                        {campaign.clicked.toLocaleString()}
                      </div>
                      <div className="text-xs text-slate-500">
                        {((campaign.clicked / campaign.opened) * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-slate-600">Leads</div>
                      <div className="font-bold text-lg text-purple-600">
                        {campaign.leads}
                      </div>
                      <div className="text-xs text-slate-500">
                        {((campaign.leads / campaign.clicked) * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="sms" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">SMS Campaigns</h3>
            <Button>
              <MessageSquare className="h-4 w-4 mr-2" />
              Create SMS Campaign
            </Button>
          </div>

          <div className="space-y-4">
            {smsCampaigns.map((campaign) => (
              <Card key={campaign.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      {getStatusIcon(campaign.status)}
                      {campaign.name}
                    </CardTitle>
                    <div className="flex gap-2">
                      <Button size="sm" variant="ghost">
                        <Settings className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-slate-600">Sent</div>
                      <div className="font-bold text-lg">{campaign.sent.toLocaleString()}</div>
                    </div>
                    <div>
                      <div className="text-slate-600">Delivered</div>
                      <div className="font-bold text-lg text-blue-600">
                        {campaign.delivered.toLocaleString()}
                      </div>
                      <div className="text-xs text-slate-500">
                        {((campaign.delivered / campaign.sent) * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-slate-600">Responded</div>
                      <div className="font-bold text-lg text-green-600">
                        {campaign.responded.toLocaleString()}
                      </div>
                      <div className="text-xs text-slate-500">
                        {((campaign.responded / campaign.delivered) * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="sequences" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Follow-up Sequences</h3>
            <Button>
              <Clock className="h-4 w-4 mr-2" />
              Create Sequence
            </Button>
          </div>

          <div className="space-y-4">
            {followUpSequences.map((sequence) => (
              <Card key={sequence.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      {sequence.active ? (
                        <CheckCircle className="h-4 w-4 text-green-600" />
                      ) : (
                        <Pause className="h-4 w-4 text-gray-600" />
                      )}
                      {sequence.name}
                    </CardTitle>
                    <div className="flex gap-2">
                      <Button size="sm" variant="ghost">
                        <Settings className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-slate-600">Trigger</div>
                      <div className="font-medium">{getTriggerTypeLabel(sequence.triggerType)}</div>
                    </div>
                    <div>
                      <div className="text-slate-600">Steps</div>
                      <div className="font-bold text-lg">{sequence.steps}</div>
                    </div>
                    <div>
                      <div className="text-slate-600">Completion Rate</div>
                      <div className="font-bold text-lg text-green-600">
                        {sequence.completionRate}%
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="personalization" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Personalization Rules</CardTitle>
                <CardDescription>
                  Configure dynamic content based on lead data
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Price Range Preference</label>
                  <Input placeholder="Show properties in ${price_min} - ${price_max} range" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Location Interest</label>
                  <Input placeholder="Properties in ${preferred_neighborhoods}" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Property Type</label>
                  <Input placeholder="${property_type} homes matching your criteria" />
                </div>
                <Button className="w-full">Save Personalization Rules</Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Smart Timing</CardTitle>
                <CardDescription>
                  AI-optimized send times for maximum engagement
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <div className="font-medium">Optimal Email Time</div>
                      <div className="text-sm text-slate-600">Tuesday, 10:30 AM</div>
                    </div>
                    <div className="text-green-600 font-bold">+23% open rate</div>
                  </div>
                  <div className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <div className="font-medium">Best SMS Time</div>
                      <div className="text-sm text-slate-600">Wednesday, 2:15 PM</div>
                    </div>
                    <div className="text-green-600 font-bold">+31% response rate</div>
                  </div>
                  <div className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <div className="font-medium">Follow-up Cadence</div>
                      <div className="text-sm text-slate-600">3, 7, 14 day intervals</div>
                    </div>
                    <div className="text-blue-600 font-bold">Optimized</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}