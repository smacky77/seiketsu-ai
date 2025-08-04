'use client'

import { useState } from 'react'

// Appointment management based on client convenience patterns from UX research
interface Appointment {
  id: string
  property: {
    address: string
    price: number
    image: string
  }
  dateTime: string
  duration: number
  type: 'viewing' | 'consultation' | 'signing'
  agent: string
  status: 'confirmed' | 'pending' | 'rescheduled'
  notes?: string
}

const mockAppointments: Appointment[] = [
  {
    id: '1',
    property: {
      address: '1234 Pine St #304',
      price: 575000,
      image: '/api/placeholder/300/200'
    },
    dateTime: '2024-08-04T14:00:00',
    duration: 60,
    type: 'viewing',
    agent: 'Michael Chen',
    status: 'confirmed',
    notes: 'Bring parking questions'
  },
  {
    id: '2',
    property: {
      address: '5678 Bell St #507',
      price: 625000,
      image: '/api/placeholder/300/200'
    },
    dateTime: '2024-08-06T10:30:00',
    duration: 45,
    type: 'viewing',
    agent: 'Michael Chen',
    status: 'confirmed'
  },
  {
    id: '3',
    property: {
      address: 'Virtual Consultation',
      price: 0,
      image: ''
    },
    dateTime: '2024-08-08T16:00:00',
    duration: 30,
    type: 'consultation',
    agent: 'Michael Chen',
    status: 'pending'
  }
]

export default function UpcomingAppointments() {
  const [selectedAppointment, setSelectedAppointment] = useState<string | null>(null)
  
  const formatDateTime = (dateTime: string) => {
    const date = new Date(dateTime)
    return {
      date: date.toLocaleDateString('en-US', { 
        weekday: 'short', 
        month: 'short', 
        day: 'numeric' 
      }),
      time: date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit' 
      })
    }
  }
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed': return 'bg-green-100 text-green-800'
      case 'pending': return 'bg-yellow-100 text-yellow-800'
      case 'rescheduled': return 'bg-blue-100 text-blue-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }
  
  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-foreground">Upcoming Appointments</h2>
          <p className="text-sm text-muted-foreground">
            Your scheduled viewings and consultations
          </p>
        </div>
        <button className="btn btn-primary text-sm">
          Schedule New
        </button>
      </div>
      
      <div className="space-y-4">
        {mockAppointments.map((appointment) => {
          const { date, time } = formatDateTime(appointment.dateTime)
          
          return (
            <div
              key={appointment.id}
              className={`border border-border rounded-lg p-4 transition-all duration-200 cursor-pointer ${
                selectedAppointment === appointment.id
                  ? 'border-foreground bg-accent'
                  : 'hover:border-muted-foreground'
              }`}
              onClick={() => setSelectedAppointment(
                selectedAppointment === appointment.id ? null : appointment.id
              )}
            >
              <div className="flex items-start space-x-4">
                {/* Date/time column */}
                <div className="text-center min-w-[80px]">
                  <div className="text-sm font-medium text-foreground">{date}</div>
                  <div className="text-lg font-bold text-foreground">{time}</div>
                  <div className="text-xs text-muted-foreground">
                    {appointment.duration}min
                  </div>
                </div>
                
                {/* Appointment details */}
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="font-medium text-foreground">
                        {appointment.type === 'viewing' ? 'Property Viewing' : 'Consultation'}
                      </div>
                      {appointment.property.address !== 'Virtual Consultation' && (
                        <div className="text-sm text-muted-foreground">
                          {appointment.property.address}
                        </div>
                      )}
                      {appointment.property.price > 0 && (
                        <div className="text-sm font-medium text-foreground">
                          ${appointment.property.price.toLocaleString()}
                        </div>
                      )}
                    </div>
                    
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      getStatusColor(appointment.status)
                    }`}>
                      {appointment.status}
                    </span>
                  </div>
                  
                  <div className="text-sm text-muted-foreground mb-3">
                    with {appointment.agent}
                  </div>
                  
                  {appointment.notes && (
                    <div className="text-sm bg-muted rounded p-2 mb-3">
                      📝 {appointment.notes}
                    </div>
                  )}
                  
                  {/* Quick actions */}
                  <div className="flex space-x-2">
                    <button className="btn btn-secondary text-xs">
                      Reschedule
                    </button>
                    <button className="btn btn-ghost text-xs">
                      Add to Calendar
                    </button>
                    <button className="btn btn-ghost text-xs">
                      Get Directions
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
      
      {/* Calendar integration */}
      <div className="mt-6 p-4 bg-muted rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-medium text-foreground">Calendar Integration</div>
            <div className="text-sm text-muted-foreground">
              Sync with Google Calendar for reminders
            </div>
          </div>
          <button className="btn btn-secondary text-sm">
            Connect Calendar
          </button>
        </div>
      </div>
    </div>
  )
}