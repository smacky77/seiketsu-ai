// Analytics Tracking System for A/B Tests
// Comprehensive conversion tracking and statistical analysis

export interface ConversionEvent {
  eventName: string
  userId: string
  sessionId: string
  experimentId?: string
  variantId?: string
  properties: Record<string, any>
  timestamp: Date
  value?: number
}

export interface ConversionGoal {
  id: string
  name: string
  eventName: string
  description: string
  valueType: 'binary' | 'count' | 'revenue'
  filters?: Record<string, any>
}

export interface FunnelStep {
  id: string
  name: string
  eventName: string
  order: number
  description: string
}

export interface ConversionFunnel {
  id: string
  name: string
  steps: FunnelStep[]
  description: string
}

// Conversion goals for client acquisition optimization
export const CONVERSION_GOALS: Record<string, ConversionGoal> = {
  // Primary conversion goals
  demo_booking: {
    id: 'demo_booking',
    name: 'Demo Booking Rate',
    eventName: 'demo_booked',
    description: 'User books a product demo',
    valueType: 'binary'
  },
  
  trial_signup: {
    id: 'trial_signup',
    name: 'Trial Signup Rate',
    eventName: 'trial_started',
    description: 'User signs up for free trial',
    valueType: 'binary'
  },
  
  trial_to_paid: {
    id: 'trial_to_paid',
    name: 'Trial to Paid Conversion',
    eventName: 'subscription_created',
    description: 'Trial user converts to paid subscription',
    valueType: 'binary'
  },
  
  // Secondary conversion goals
  cta_click: {
    id: 'cta_click',
    name: 'CTA Click Rate',
    eventName: 'cta_clicked',
    description: 'User clicks primary call-to-action',
    valueType: 'binary'
  },
  
  form_completion: {
    id: 'form_completion',
    name: 'Form Completion Rate',
    eventName: 'form_completed',
    description: 'User completes lead capture form',
    valueType: 'binary'
  },
  
  pricing_view: {
    id: 'pricing_view',
    name: 'Pricing Page Engagement',
    eventName: 'pricing_viewed',
    description: 'User visits and engages with pricing page',
    valueType: 'binary'
  },
  
  // Email engagement goals
  email_open: {
    id: 'email_open',
    name: 'Email Open Rate',
    eventName: 'email_opened',
    description: 'User opens outreach email',
    valueType: 'binary'
  },
  
  email_click: {
    id: 'email_click',
    name: 'Email Click Rate',
    eventName: 'email_clicked',
    description: 'User clicks link in email',
    valueType: 'binary'
  },
  
  // Demo experience goals
  demo_completion: {
    id: 'demo_completion',
    name: 'Demo Completion Rate',
    eventName: 'demo_completed',
    description: 'User completes full demo experience',
    valueType: 'binary'
  },
  
  demo_engagement: {
    id: 'demo_engagement',
    name: 'Demo Engagement Score',
    eventName: 'demo_interaction',
    description: 'User interaction level during demo',
    valueType: 'count'
  },
  
  // Revenue goals
  revenue_per_visitor: {
    id: 'revenue_per_visitor',
    name: 'Revenue Per Visitor',
    eventName: 'subscription_created',
    description: 'Revenue generated per website visitor',
    valueType: 'revenue'
  }
}

// Conversion funnels for analyzing drop-off points
export const CONVERSION_FUNNELS: Record<string, ConversionFunnel> = {
  landing_to_paid: {
    id: 'landing_to_paid',
    name: 'Landing Page to Paid Customer',
    description: 'Complete conversion funnel from landing page visit to paid subscription',
    steps: [
      { id: 'page_view', name: 'Landing Page View', eventName: 'page_viewed', order: 1, description: 'User visits landing page' },
      { id: 'cta_click', name: 'CTA Click', eventName: 'cta_clicked', order: 2, description: 'User clicks primary CTA' },
      { id: 'form_start', name: 'Form Started', eventName: 'form_started', order: 3, description: 'User begins lead form' },
      { id: 'form_complete', name: 'Form Completed', eventName: 'form_completed', order: 4, description: 'User completes lead form' },
      { id: 'demo_booked', name: 'Demo Booked', eventName: 'demo_booked', order: 5, description: 'User books product demo' },
      { id: 'demo_attended', name: 'Demo Attended', eventName: 'demo_attended', order: 6, description: 'User attends scheduled demo' },
      { id: 'trial_started', name: 'Trial Started', eventName: 'trial_started', order: 7, description: 'User signs up for trial' },
      { id: 'trial_activated', name: 'Trial Activated', eventName: 'trial_activated', order: 8, description: 'User actively uses trial' },
      { id: 'subscription_created', name: 'Paid Subscription', eventName: 'subscription_created', order: 9, description: 'User converts to paid plan' }
    ]
  },

  email_to_demo: {
    id: 'email_to_demo',
    name: 'Email Outreach to Demo',
    description: 'Email outreach conversion funnel',
    steps: [
      { id: 'email_sent', name: 'Email Sent', eventName: 'email_sent', order: 1, description: 'Outreach email sent' },
      { id: 'email_opened', name: 'Email Opened', eventName: 'email_opened', order: 2, description: 'User opens email' },
      { id: 'email_clicked', name: 'Email Clicked', eventName: 'email_clicked', order: 3, description: 'User clicks email link' },
      { id: 'landing_visited', name: 'Landing Page Visited', eventName: 'page_viewed', order: 4, description: 'User visits landing page from email' },
      { id: 'demo_booked', name: 'Demo Booked', eventName: 'demo_booked', order: 5, description: 'User books demo from email campaign' }
    ]
  },

  pricing_to_trial: {
    id: 'pricing_to_trial',
    name: 'Pricing Page to Trial',
    description: 'Pricing page conversion funnel',
    steps: [
      { id: 'pricing_viewed', name: 'Pricing Viewed', eventName: 'pricing_viewed', order: 1, description: 'User views pricing page' },
      { id: 'pricing_calculated', name: 'ROI Calculated', eventName: 'roi_calculated', order: 2, description: 'User uses ROI calculator' },
      { id: 'plan_selected', name: 'Plan Selected', eventName: 'plan_selected', order: 3, description: 'User selects pricing plan' },
      { id: 'trial_started', name: 'Trial Started', eventName: 'trial_started', order: 4, description: 'User starts trial' }
    ]
  }
}

// Analytics tracking class
export class AnalyticsTracker {
  private static instance: AnalyticsTracker
  private events: ConversionEvent[] = []
  private goals: Map<string, ConversionGoal> = new Map()
  private funnels: Map<string, ConversionFunnel> = new Map()
  private integrations: Map<string, any> = new Map()

  static getInstance(): AnalyticsTracker {
    if (!AnalyticsTracker.instance) {
      AnalyticsTracker.instance = new AnalyticsTracker()
    }
    return AnalyticsTracker.instance
  }

  constructor() {
    // Load conversion goals and funnels
    Object.entries(CONVERSION_GOALS).forEach(([id, goal]) => {
      this.goals.set(id, goal)
    })
    
    Object.entries(CONVERSION_FUNNELS).forEach(([id, funnel]) => {
      this.funnels.set(id, funnel)
    })

    this.initializeIntegrations()
  }

  // Initialize third-party analytics integrations
  private initializeIntegrations(): void {
    // Google Analytics 4
    if (typeof window !== 'undefined' && (window as any).gtag) {
      this.integrations.set('ga4', (window as any).gtag)
    }

    // Facebook Pixel
    if (typeof window !== 'undefined' && (window as any).fbq) {
      this.integrations.set('facebook', (window as any).fbq)
    }

    // Mixpanel
    if (typeof window !== 'undefined' && (window as any).mixpanel) {
      this.integrations.set('mixpanel', (window as any).mixpanel)
    }

    // PostHog
    if (typeof window !== 'undefined' && (window as any).posthog) {
      this.integrations.set('posthog', (window as any).posthog)
    }
  }

  // Track conversion event
  track(eventName: string, properties: Record<string, any> = {}, userId?: string): void {
    const event: ConversionEvent = {
      eventName,
      userId: userId || this.generateAnonymousId(),
      sessionId: this.getSessionId(),
      experimentId: properties.experimentId,
      variantId: properties.variantId,
      properties,
      timestamp: new Date(),
      value: properties.value || 0
    }

    // Store event locally
    this.events.push(event)

    // Send to third-party integrations
    this.sendToIntegrations(event)

    // Check for conversion goal completion
    this.checkConversionGoals(event)

    // Update funnel progress
    this.updateFunnelProgress(event)
  }

  // Send event to third-party analytics platforms
  private sendToIntegrations(event: ConversionEvent): void {
    // Google Analytics 4
    const ga4 = this.integrations.get('ga4')
    if (ga4) {
      ga4('event', event.eventName, {
        user_id: event.userId,
        session_id: event.sessionId,
        experiment_id: event.experimentId,
        variant_id: event.variantId,
        value: event.value,
        ...event.properties
      })
    }

    // Facebook Pixel
    const fbq = this.integrations.get('facebook')
    if (fbq) {
      fbq('track', this.mapEventToFacebookEvent(event.eventName), {
        value: event.value,
        currency: 'USD',
        content_name: event.properties.content_name,
        ...event.properties
      })
    }

    // Mixpanel
    const mixpanel = this.integrations.get('mixpanel')
    if (mixpanel) {
      mixpanel.track(event.eventName, {
        distinct_id: event.userId,
        experiment_id: event.experimentId,
        variant_id: event.variantId,
        ...event.properties
      })
    }

    // PostHog
    const posthog = this.integrations.get('posthog')
    if (posthog) {
      posthog.capture(event.eventName, {
        $user_id: event.userId,
        $session_id: event.sessionId,
        experiment_id: event.experimentId,
        variant_id: event.variantId,
        ...event.properties
      })
    }
  }

  // Map internal events to Facebook standard events
  private mapEventToFacebookEvent(eventName: string): string {
    const eventMap: Record<string, string> = {
      'demo_booked': 'Lead',
      'trial_started': 'StartTrial',
      'subscription_created': 'Purchase',
      'form_completed': 'CompleteRegistration',
      'cta_clicked': 'InitiateCheckout',
      'page_viewed': 'ViewContent'
    }
    return eventMap[eventName] || 'CustomEvent'
  }

  // Check if event triggers any conversion goals
  private checkConversionGoals(event: ConversionEvent): void {
    this.goals.forEach((goal, goalId) => {
      if (goal.eventName === event.eventName) {
        // Check filters if any
        if (goal.filters) {
          const meetsFilters = Object.entries(goal.filters).every(([key, value]) => 
            event.properties[key] === value
          )
          if (!meetsFilters) return
        }

        // Track goal completion
        this.track('goal_completed', {
          goal_id: goalId,
          goal_name: goal.name,
          experiment_id: event.experimentId,
          variant_id: event.variantId
        }, event.userId)
      }
    })
  }

  // Update funnel progress for user
  private updateFunnelProgress(event: ConversionEvent): void {
    this.funnels.forEach((funnel) => {
      const step = funnel.steps.find(s => s.eventName === event.eventName)
      if (step) {
        this.track('funnel_step_completed', {
          funnel_id: funnel.id,
          funnel_name: funnel.name,
          step_id: step.id,
          step_name: step.name,
          step_order: step.order,
          experiment_id: event.experimentId,
          variant_id: event.variantId
        }, event.userId)
      }
    })
  }

  // Generate anonymous user ID
  private generateAnonymousId(): string {
    if (typeof window !== 'undefined') {
      let anonymousId = localStorage.getItem('anonymous_id')
      if (!anonymousId) {
        anonymousId = 'anon_' + Math.random().toString(36).substr(2, 9)
        localStorage.setItem('anonymous_id', anonymousId)
      }
      return anonymousId
    }
    return 'anon_' + Math.random().toString(36).substr(2, 9)
  }

  // Get or generate session ID
  private getSessionId(): string {
    if (typeof window !== 'undefined') {
      let sessionId = sessionStorage.getItem('session_id')
      if (!sessionId) {
        sessionId = 'sess_' + Date.now().toString() + '_' + Math.random().toString(36).substr(2, 9)
        sessionStorage.setItem('session_id', sessionId)
      }
      return sessionId
    }
    return 'sess_' + Date.now().toString() + '_' + Math.random().toString(36).substr(2, 9)
  }

  // Get conversion rate for a specific goal and experiment
  getConversionRate(goalId: string, experimentId?: string, variantId?: string): number {
    const goalEvents = this.events.filter(event => {
      return event.eventName === 'goal_completed' && 
             event.properties.goal_id === goalId &&
             (!experimentId || event.experimentId === experimentId) &&
             (!variantId || event.variantId === variantId)
    })

    const totalEvents = this.events.filter(event => {
      return (!experimentId || event.experimentId === experimentId) &&
             (!variantId || event.variantId === variantId)
    })

    return totalEvents.length > 0 ? (goalEvents.length / totalEvents.length) * 100 : 0
  }

  // Get funnel conversion rates
  getFunnelConversionRates(funnelId: string, experimentId?: string, variantId?: string): Record<string, number> {
    const funnel = this.funnels.get(funnelId)
    if (!funnel) return {}

    const rates: Record<string, number> = {}
    
    for (let i = 0; i < funnel.steps.length; i++) {
      const currentStep = funnel.steps[i]
      const nextStep = funnel.steps[i + 1]
      
      if (nextStep) {
        const currentStepEvents = this.events.filter(event => 
          event.eventName === 'funnel_step_completed' &&
          event.properties.step_id === currentStep.id &&
          event.properties.funnel_id === funnelId &&
          (!experimentId || event.experimentId === experimentId) &&
          (!variantId || event.variantId === variantId)
        )
        
        const nextStepEvents = this.events.filter(event => 
          event.eventName === 'funnel_step_completed' &&
          event.properties.step_id === nextStep.id &&
          event.properties.funnel_id === funnelId &&
          (!experimentId || event.experimentId === experimentId) &&
          (!variantId || event.variantId === variantId)
        )
        
        const conversionRate = currentStepEvents.length > 0 ? 
          (nextStepEvents.length / currentStepEvents.length) * 100 : 0
        
        rates[`${currentStep.id}_to_${nextStep.id}`] = conversionRate
      }
    }
    
    return rates
  }

  // Get all events for a user
  getUserEvents(userId: string): ConversionEvent[] {
    return this.events.filter(event => event.userId === userId)
  }

  // Get experiment metrics
  getExperimentMetrics(experimentId: string): Record<string, any> {
    const experimentEvents = this.events.filter(event => event.experimentId === experimentId)
    const variants = [...new Set(experimentEvents.map(event => event.variantId))].filter(Boolean)
    
    const metrics: Record<string, any> = {}
    
    variants.forEach(variantId => {
      const variantEvents = experimentEvents.filter(event => event.variantId === variantId)
      metrics[variantId!] = {
        totalEvents: variantEvents.length,
        uniqueUsers: [...new Set(variantEvents.map(event => event.userId))].length,
        conversionGoals: {}
      }
      
      // Calculate conversion rates for each goal
      this.goals.forEach((goal, goalId) => {
        const conversionRate = this.getConversionRate(goalId, experimentId, variantId)
        metrics[variantId!].conversionGoals[goalId] = {
          rate: conversionRate,
          name: goal.name
        }
      })
    })
    
    return metrics
  }
}