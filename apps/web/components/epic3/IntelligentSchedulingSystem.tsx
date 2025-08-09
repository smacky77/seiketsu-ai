'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Calendar, 
  Clock, 
  User, 
  MapPin, 
  Phone, 
  Mail,
  CheckCircle,
  AlertCircle,
  CalendarDays,
  Settings,
  Bell,
  Users
} from 'lucide-react'

interface Appointment {
  id: string
  clientName: string
  clientPhone: string
  clientEmail: string
  propertyAddress: string
  appointmentType: 'showing' | 'consultation' | 'listing_appointment' | 'closing'
  scheduledTime: Date
  duration: number
  status: 'confirmed' | 'pending' | 'completed' | 'cancelled'
  agentId: string
  agentName: string
}

interface AgentAvailability {
  agentId: string
  agentName: string
  status: 'available' | 'busy' | 'out_of_office'
  nextAvailable: Date
  todayBookings: number
  weeklyBookings: number
}

interface CalendarIntegration {
  provider: string
  connected: boolean
  lastSync: Date
  eventsCount: number
}

export function IntelligentSchedulingSystem() {
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [viewMode, setViewMode] = useState<'day' | 'week' | 'month'>('day')
  
  const upcomingAppointments: Appointment[] = [
    {
      id: '1',
      clientName: 'John & Sarah Martinez',
      clientPhone: '(555) 123-4567',
      clientEmail: 'john.martinez@email.com',
      propertyAddress: '123 Oak Street, Downtown District',
      appointmentType: 'showing',
      scheduledTime: new Date(2024, 11, 15, 10, 30),
      duration: 60,
      status: 'confirmed',
      agentId: 'agent1',
      agentName: 'Michael Chen'
    },
    {
      id: '2',
      clientName: 'Emma Thompson',
      clientPhone: '(555) 987-6543',
      clientEmail: 'emma.thompson@email.com',
      propertyAddress: '456 Maple Avenue, Suburbia',
      appointmentType: 'consultation',
      scheduledTime: new Date(2024, 11, 15, 14, 0),
      duration: 90,
      status: 'pending',
      agentId: 'agent2',
      agentName: 'Lisa Rodriguez'
    },
    {
      id: '3',
      clientName: 'Robert Johnson',
      clientPhone: '(555) 456-7890',
      clientEmail: 'robert.johnson@email.com',
      propertyAddress: '789 Pine Road, Riverside',
      appointmentType: 'listing_appointment',
      scheduledTime: new Date(2024, 11, 15, 16, 30),
      duration: 120,
      status: 'confirmed',
      agentId: 'agent1',
      agentName: 'Michael Chen'
    }
  ]

  const agentAvailability: AgentAvailability[] = [
    {
      agentId: 'agent1',
      agentName: 'Michael Chen',
      status: 'available',
      nextAvailable: new Date(2024, 11, 15, 12, 0),
      todayBookings: 4,
      weeklyBookings: 18
    },
    {
      agentId: 'agent2',
      agentName: 'Lisa Rodriguez',
      status: 'busy',
      nextAvailable: new Date(2024, 11, 15, 15, 30),
      todayBookings: 6,
      weeklyBookings: 22
    },
    {
      agentId: 'agent3',
      agentName: 'David Kim',
      status: 'available',
      nextAvailable: new Date(2024, 11, 15, 9, 0),
      todayBookings: 3,
      weeklyBookings: 15
    }
  ]

  const calendarIntegrations: CalendarIntegration[] = [
    {
      provider: 'Google Calendar',
      connected: true,
      lastSync: new Date(2024, 11, 15, 8, 45),
      eventsCount: 127
    },
    {
      provider: 'Outlook Calendar',
      connected: true,
      lastSync: new Date(2024, 11, 15, 8, 40),
      eventsCount: 89
    },
    {
      provider: 'Apple Calendar',
      connected: false,
      lastSync: new Date(),
      eventsCount: 0
    }
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'confirmed':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'pending':
        return <AlertCircle className="h-4 w-4 text-yellow-600" />
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-blue-600" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-600" />
    }
  }

  const getAppointmentTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'showing': 'bg-blue-100 text-blue-800',
      'consultation': 'bg-green-100 text-green-800',
      'listing_appointment': 'bg-purple-100 text-purple-800',
      'closing': 'bg-orange-100 text-orange-800'
    }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  const getAgentStatusColor = (status: string) => {
    switch (status) {
      case 'available':
        return 'text-green-600'
      case 'busy':
        return 'text-red-600'
      case 'out_of_office':
        return 'text-gray-600'
      default:
        return 'text-gray-600'
    }
  }

  return (
    <div className="space-y-6">
      {/* Scheduling Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Today's Appointments
            </CardTitle>
            <CalendarDays className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">13</div>
            <p className="text-xs text-muted-foreground">
              +2 from yesterday
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Booking Success Rate
            </CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">94.2%</div>
            <p className="text-xs text-muted-foreground">
              +1.3% from last week
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Avg Response Time
            </CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1.8h</div>
            <p className="text-xs text-muted-foreground">
              Automated confirmations
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              No-Show Rate
            </CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3.1%</div>
            <p className="text-xs text-muted-foreground">
              -0.8% with reminders
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Scheduling Management Tabs */}
      <Tabs defaultValue="appointments" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="appointments">Appointments</TabsTrigger>
          <TabsTrigger value="availability">Agent Availability</TabsTrigger>
          <TabsTrigger value="calendar">Calendar Sync</TabsTrigger>
          <TabsTrigger value="automation">Automation</TabsTrigger>
        </TabsList>

        <TabsContent value="appointments" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Upcoming Appointments</h3>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                <Calendar className="h-4 w-4 mr-2" />
                View Calendar
              </Button>
              <Button>
                <CalendarDays className="h-4 w-4 mr-2" />
                Book Appointment
              </Button>
            </div>
          </div>

          <div className="space-y-4">
            {upcomingAppointments.map((appointment) => (
              <Card key={appointment.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      {getStatusIcon(appointment.status)}
                      <div>
                        <CardTitle className="text-lg">{appointment.clientName}</CardTitle>
                        <div className="flex items-center gap-4 text-sm text-slate-600 mt-1">
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {appointment.scheduledTime.toLocaleDateString()} at{' '}
                            {appointment.scheduledTime.toLocaleTimeString([], {
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </div>
                          <div className="flex items-center gap-1">
                            <User className="h-3 w-3" />
                            {appointment.agentName}
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 text-xs rounded-full ${getAppointmentTypeColor(appointment.appointmentType)}`}>
                        {appointment.appointmentType.replace('_', ' ')}
                      </span>
                      <Button size="sm" variant="ghost">
                        <Settings className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <MapPin className="h-4 w-4 text-slate-500" />
                        <span>{appointment.propertyAddress}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-slate-500" />
                        <span>{appointment.duration} minutes</span>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Phone className="h-4 w-4 text-slate-500" />
                        <span>{appointment.clientPhone}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Mail className="h-4 w-4 text-slate-500" />
                        <span>{appointment.clientEmail}</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="availability" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Agent Availability</h3>
            <Button>
              <Users className="h-4 w-4 mr-2" />
              Manage Schedules
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {agentAvailability.map((agent) => (
              <Card key={agent.agentId}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{agent.agentName}</CardTitle>
                    <span className={`text-sm font-medium ${getAgentStatusColor(agent.status)}`}>
                      {agent.status.replace('_', ' ')}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="text-sm">
                    <div className="text-slate-600">Next Available</div>
                    <div className="font-medium">
                      {agent.nextAvailable.toLocaleDateString()} at{' '}
                      {agent.nextAvailable.toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <div className="text-slate-600">Today</div>
                      <div className="font-bold text-lg">{agent.todayBookings}</div>
                    </div>
                    <div>
                      <div className="text-slate-600">This Week</div>
                      <div className="font-bold text-lg">{agent.weeklyBookings}</div>
                    </div>
                  </div>
                  <Button size="sm" className="w-full">
                    View Schedule
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="calendar" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Calendar Integrations</h3>
            <Button>
              <CalendarDays className="h-4 w-4 mr-2" />
              Add Integration
            </Button>
          </div>

          <div className="space-y-4">
            {calendarIntegrations.map((integration, index) => (
              <Card key={index}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      {integration.connected ? (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      ) : (
                        <AlertCircle className="h-5 w-5 text-gray-400" />
                      )}
                      {integration.provider}
                    </CardTitle>
                    <div className="flex gap-2">
                      {integration.connected ? (
                        <Button size="sm" variant="outline">
                          Sync Now
                        </Button>
                      ) : (
                        <Button size="sm">
                          Connect
                        </Button>
                      )}
                    </div>
                  </div>
                </CardHeader>
                {integration.connected && (
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="text-slate-600">Last Sync</div>
                        <div className="font-medium">
                          {integration.lastSync.toLocaleDateString()} at{' '}
                          {integration.lastSync.toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </div>
                      </div>
                      <div>
                        <div className="text-slate-600">Synced Events</div>
                        <div className="font-bold text-lg">{integration.eventsCount}</div>
                      </div>
                    </div>
                  </CardContent>
                )}
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="automation" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="h-5 w-5 text-blue-600" />
                  Automated Reminders
                </CardTitle>
                <CardDescription>
                  Configure automatic appointment reminders
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <div className="font-medium">24 Hours Before</div>
                      <div className="text-sm text-slate-600">Email + SMS</div>
                    </div>
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  </div>
                  <div className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <div className="font-medium">2 Hours Before</div>
                      <div className="text-sm text-slate-600">SMS only</div>
                    </div>
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  </div>
                  <div className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <div className="font-medium">15 Minutes Before</div>
                      <div className="text-sm text-slate-600">Push notification</div>
                    </div>
                    <AlertCircle className="h-5 w-5 text-gray-400" />
                  </div>
                </div>
                <Button className="w-full">Configure Reminders</Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5 text-purple-600" />
                  Smart Scheduling
                </CardTitle>
                <CardDescription>
                  AI-powered scheduling optimization
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <div className="font-medium">Buffer Time</div>
                      <div className="text-sm text-slate-600">15 minutes between appointments</div>
                    </div>
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  </div>
                  <div className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <div className="font-medium">Travel Time</div>
                      <div className="text-sm text-slate-600">Auto-calculate drive time</div>
                    </div>
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  </div>
                  <div className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <div className="font-medium">Workload Balance</div>
                      <div className="text-sm text-slate-600">Distribute evenly across agents</div>
                    </div>
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  </div>
                </div>
                <Button className="w-full">Update Settings</Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}