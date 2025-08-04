'use client'

import { useState, useEffect } from 'react'
import WelcomeOverview from '@/components/portal/WelcomeOverview'
import PropertyRecommendations from '@/components/portal/PropertyRecommendations'
import UpcomingAppointments from '@/components/portal/UpcomingAppointments'
import RecentActivity from '@/components/portal/RecentActivity'
import QuickActions from '@/components/portal/QuickActions'

// Mock client data based on UX research personas
const mockClientData = {
  name: 'Sarah Johnson',
  agent: {
    name: 'Michael Chen',
    photo: '/api/placeholder/64/64',
    phone: '(555) 123-4567',
    email: 'michael.chen@realestate.com',
    responseTime: '< 2 hours'
  },
  searchStatus: {
    budget: '$450K - $600K',
    location: 'Downtown Seattle',
    propertyType: '2-3 bedroom condo',
    timeline: 'Next 3 months',
    viewedProperties: 12,
    savedProperties: 5,
    scheduledViewings: 3
  },
  preferences: {
    maxPrice: 600000,
    minBedrooms: 2,
    preferredNeighborhoods: ['Capitol Hill', 'Belltown', 'South Lake Union'],
    mustHave: ['Parking', 'In-unit laundry', 'Pet-friendly']
  }
}

export default function ClientPortalDashboard() {
  const [isLoading, setIsLoading] = useState(true)
  
  useEffect(() => {
    // Simulate loading client data
    const timer = setTimeout(() => setIsLoading(false), 1000)
    return () => clearTimeout(timer)
  }, [])
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-foreground mx-auto"></div>
          <p className="text-muted-foreground">Loading your personalized dashboard...</p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="space-y-8">
      {/* Personalized welcome based on client trust patterns */}
      <WelcomeOverview client={mockClientData} />
      
      {/* Quick actions for common client tasks */}
      <QuickActions />
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* AI-curated property recommendations */}
        <div className="lg:col-span-2">
          <PropertyRecommendations preferences={mockClientData.preferences} />
        </div>
        
        {/* Trust-building appointment management */}
        <UpcomingAppointments />
        
        {/* Communication transparency */}
        <RecentActivity />
      </div>
    </div>
  )
}