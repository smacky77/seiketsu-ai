'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { ExperimentManager, ExperimentVariant } from '@/lib/ab-testing/experiment-config'
import { AnalyticsTracker } from '@/lib/ab-testing/analytics-tracker'

interface ABTestContextType {
  getVariant: (experimentId: string) => ExperimentVariant | null
  track: (eventName: string, properties?: Record<string, any>) => void
  userId: string
}

const ABTestContext = createContext<ABTestContextType | null>(null)

interface ABTestProviderProps {
  children: React.ReactNode
}

export function ABTestProvider({ children }: ABTestProviderProps) {
  const [userId, setUserId] = useState<string>('')
  const [experimentManager] = useState(() => ExperimentManager.getInstance())
  const [analyticsTracker] = useState(() => AnalyticsTracker.getInstance())

  useEffect(() => {
    // Initialize user ID on client side
    if (typeof window !== 'undefined') {
      let storedUserId = localStorage.getItem('ab_test_user_id')
      if (!storedUserId) {
        storedUserId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
        localStorage.setItem('ab_test_user_id', storedUserId)
      }
      setUserId(storedUserId)
      
      // Track page view
      analyticsTracker.track('page_viewed', {
        page: window.location.pathname,
        referrer: document.referrer,
        user_agent: navigator.userAgent
      }, storedUserId)
    }
  }, [analyticsTracker])

  const getVariant = (experimentId: string): ExperimentVariant | null => {
    if (!userId) return null
    return experimentManager.getUserVariant(userId, experimentId)
  }

  const track = (eventName: string, properties: Record<string, any> = {}) => {
    if (!userId) return
    
    // Enhance properties with current active experiments
    const activeExperiments = experimentManager.getActiveExperiments()
    const enhancedProperties = { ...properties }
    
    activeExperiments.forEach(experiment => {
      const variant = experimentManager.getUserVariant(userId, experiment.id)
      if (variant) {
        enhancedProperties[`experiment_${experiment.id}`] = variant.id
      }
    })
    
    analyticsTracker.track(eventName, enhancedProperties, userId)
  }

  return (
    <ABTestContext.Provider value={{ getVariant, track, userId }}>
      {children}
    </ABTestContext.Provider>
  )
}

export function useABTest() {
  const context = useContext(ABTestContext)
  if (!context) {
    throw new Error('useABTest must be used within an ABTestProvider')
  }
  return context
}

// Hook for specific experiment variants
export function useExperimentVariant(experimentId: string) {
  const { getVariant, track } = useABTest()
  const variant = getVariant(experimentId)

  useEffect(() => {
    if (variant) {
      track('experiment_exposure', {
        experiment_id: experimentId,
        variant_id: variant.id
      })
    }
  }, [variant, experimentId, track])

  return variant
}