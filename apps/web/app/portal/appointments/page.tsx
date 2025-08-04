'use client'

import { useState } from 'react'
import AppointmentCalendar from '@/components/portal/AppointmentCalendar'
import AppointmentList from '@/components/portal/AppointmentList'
import ScheduleNew from '@/components/portal/ScheduleNew'

export default function AppointmentsPage() {
  const [viewMode, setViewMode] = useState<'calendar' | 'list'>('calendar')
  const [showScheduler, setShowScheduler] = useState(false)
  
  return (
    <div className="space-y-6">
      {/* Page header with appointment overview */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Appointments</h1>
          <p className="text-muted-foreground">
            Manage your property viewings and consultations
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="flex border border-border rounded-lg overflow-hidden">
            <button
              onClick={() => setViewMode('calendar')}
              className={`px-4 py-2 text-sm ${viewMode === 'calendar' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            >
              📅 Calendar
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-4 py-2 text-sm ${viewMode === 'list' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            >
              📋 List
            </button>
          </div>
          
          <button 
            onClick={() => setShowScheduler(true)}
            className="btn btn-primary"
          >
            Schedule New
          </button>
        </div>
      </div>
      
      {/* Quick stats for confidence building */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-card border border-border rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-foreground">3</div>
          <div className="text-sm text-muted-foreground">Upcoming</div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-foreground">12</div>
          <div className="text-sm text-muted-foreground">Completed</div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-foreground">2.3h</div>
          <div className="text-sm text-muted-foreground">Avg Response</div>
        </div>
      </div>
      
      {/* Main appointment interface */}
      {viewMode === 'calendar' ? (
        <AppointmentCalendar />
      ) : (
        <AppointmentList />
      )}
      
      {/* Schedule new appointment modal */}
      {showScheduler && (
        <ScheduleNew onClose={() => setShowScheduler(false)} />
      )}
    </div>
  )
}