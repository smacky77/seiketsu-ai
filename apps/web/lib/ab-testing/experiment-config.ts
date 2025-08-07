// A/B Testing Experiment Configuration System
// Designed for rapid iteration and statistical rigor

export interface ExperimentVariant {
  id: string
  name: string
  weight: number // Traffic allocation percentage
  config: Record<string, any>
  description: string
}

export interface ExperimentConfig {
  id: string
  name: string
  description: string
  status: 'draft' | 'running' | 'paused' | 'completed' | 'archived'
  variants: ExperimentVariant[]
  primaryMetric: string
  secondaryMetrics: string[]
  guardrailMetrics: string[]
  startDate: Date
  endDate?: Date
  minimumSampleSize: number
  confidenceLevel: number
  powerAnalysis: number
  maxRuntime: number // days
  targetSegments?: string[]
  excludeSegments?: string[]
  createdBy: string
  createdAt: Date
  updatedAt: Date
}

// Experiment definitions for client conversion optimization
export const EXPERIMENTS: Record<string, ExperimentConfig> = {
  // 1. LANDING PAGE OPTIMIZATION
  'landing-headline-test': {
    id: 'landing-headline-test',
    name: 'Landing Page Headlines A/B Test',
    description: 'Test different value propositions and headlines for maximum conversion',
    status: 'draft',
    variants: [
      {
        id: 'control',
        name: 'Current: Voice-First Real Estate Intelligence',
        weight: 25,
        config: {
          headline: 'Voice-First Real Estate Intelligence',
          subheadline: 'Transform your real estate business with AI-powered voice agents',
          cta: 'Book Free Demo'
        },
        description: 'Existing headline focusing on technology'
      },
      {
        id: 'roi-focused',
        name: 'ROI-Focused: 3X More Qualified Leads',
        weight: 25,
        config: {
          headline: 'Generate 3X More Qualified Real Estate Leads',
          subheadline: 'AI voice agents qualify prospects 24/7 while you focus on closing deals',
          cta: 'See ROI Calculator'
        },
        description: 'Results-focused headline with specific benefit'
      },
      {
        id: 'time-saving',
        name: 'Time-Saving: Get 40 Hours Back Per Week',
        weight: 25,
        config: {
          headline: 'Get 40 Hours Back Every Week',
          subheadline: 'Let AI handle lead qualification so you can focus on what matters most',
          cta: 'Start Free Trial'
        },
        description: 'Time-saving benefit with specific number'
      },
      {
        id: 'competitive',
        name: 'Competitive: Never Miss Another Lead',
        weight: 25,
        config: {
          headline: 'Never Miss Another Lead Again',
          subheadline: 'While competitors sleep, your AI agent qualifies leads and books appointments',
          cta: 'Get Started Now'
        },
        description: 'Competitive advantage positioning'
      }
    ],
    primaryMetric: 'demo_booking_rate',
    secondaryMetrics: ['time_on_page', 'scroll_depth', 'cta_click_rate'],
    guardrailMetrics: ['bounce_rate', 'page_load_time'],
    startDate: new Date('2025-01-15'),
    minimumSampleSize: 1000,
    confidenceLevel: 95,
    powerAnalysis: 80,
    maxRuntime: 14,
    createdBy: 'conversion-team',
    createdAt: new Date(),
    updatedAt: new Date()
  },

  'cta-optimization': {
    id: 'cta-optimization',
    name: 'CTA Button Optimization',
    description: 'Test different CTA colors, text, and positioning for maximum clicks',
    status: 'draft',
    variants: [
      {
        id: 'control',
        name: 'Blue: Book Free Demo',
        weight: 20,
        config: {
          color: '#3b82f6',
          text: 'Book Free Demo',
          position: 'center',
          size: 'large'
        },
        description: 'Current blue CTA'
      },
      {
        id: 'urgent-red',
        name: 'Red: Get Started Now',
        weight: 20,
        config: {
          color: '#ef4444',
          text: 'Get Started Now',
          position: 'center',
          size: 'large'
        },
        description: 'Urgent red with action-oriented text'
      },
      {
        id: 'trust-green',
        name: 'Green: Try Risk-Free',
        weight: 20,
        config: {
          color: '#10b981',
          text: 'Try Risk-Free',
          position: 'center',
          size: 'large'
        },
        description: 'Trust-building green with risk reduction'
      },
      {
        id: 'premium-purple',
        name: 'Purple: See ROI Calculator',
        weight: 20,
        config: {
          color: '#8b5cf6',
          text: 'See ROI Calculator',
          position: 'center',
          size: 'large'
        },
        description: 'Premium purple with value-focused text'
      },
      {
        id: 'social-orange',
        name: 'Orange: Join 500+ Agents',
        weight: 20,
        config: {
          color: '#f97316',
          text: 'Join 500+ Agents',
          position: 'center',
          size: 'large'
        },
        description: 'Social proof orange'
      }
    ],
    primaryMetric: 'cta_click_rate',
    secondaryMetrics: ['demo_booking_rate', 'form_completion_rate'],
    guardrailMetrics: ['bounce_rate'],
    startDate: new Date('2025-01-20'),
    minimumSampleSize: 800,
    confidenceLevel: 95,
    powerAnalysis: 80,
    maxRuntime: 10,
    createdBy: 'conversion-team',
    createdAt: new Date(),
    updatedAt: new Date()
  },

  // 2. PRICING DISPLAY OPTIMIZATION
  'pricing-presentation': {
    id: 'pricing-presentation',
    name: 'Pricing Display Strategy',
    description: 'Test different pricing presentation methods for maximum conversion',
    status: 'draft',
    variants: [
      {
        id: 'control',
        name: 'Standard Monthly Pricing',
        weight: 25,
        config: {
          displayType: 'monthly',
          showAnnualDiscount: false,
          priceFirst: true,
          showFeatures: true
        },
        description: 'Current monthly pricing display'
      },
      {
        id: 'annual-focus',
        name: 'Annual Pricing with Discount',
        weight: 25,
        config: {
          displayType: 'annual',
          showAnnualDiscount: true,
          priceFirst: true,
          showFeatures: true,
          discountBadge: 'Save 30%'
        },
        description: 'Annual pricing with prominent discount'
      },
      {
        id: 'value-first',
        name: 'Features First, Price Second',
        weight: 25,
        config: {
          displayType: 'monthly',
          showAnnualDiscount: true,
          priceFirst: false,
          showFeatures: true,
          valueProps: true
        },
        description: 'Lead with value, price secondary'
      },
      {
        id: 'roi-calculator',
        name: 'Interactive ROI Calculator',
        weight: 25,
        config: {
          displayType: 'calculator',
          showROI: true,
          interactive: true,
          showPayback: true
        },
        description: 'Interactive calculator showing ROI'
      }
    ],
    primaryMetric: 'pricing_to_demo_rate',
    secondaryMetrics: ['time_on_pricing', 'calculator_usage', 'trial_signup_rate'],
    guardrailMetrics: ['pricing_abandonment_rate'],
    startDate: new Date('2025-01-25'),
    minimumSampleSize: 1200,
    confidenceLevel: 95,
    powerAnalysis: 80,
    maxRuntime: 21,
    createdBy: 'pricing-team',
    createdAt: new Date(),
    updatedAt: new Date()
  },

  // 3. DEMO EXPERIENCE OPTIMIZATION
  'demo-duration': {
    id: 'demo-duration',
    name: 'Demo Duration & Focus Testing',
    description: 'Optimize demo length and content focus for conversion',
    status: 'draft',
    variants: [
      {
        id: 'control',
        name: '15min Full Feature Demo',
        weight: 33,
        config: {
          duration: 15,
          focusAreas: ['features', 'technology', 'integration'],
          interactivity: 'medium',
          pricingReveal: 'end'
        },
        description: 'Current comprehensive demo'
      },
      {
        id: 'quick-roi',
        name: '10min ROI-Focused Demo',
        weight: 33,
        config: {
          duration: 10,
          focusAreas: ['roi', 'results', 'case-studies'],
          interactivity: 'high',
          pricingReveal: 'middle'
        },
        description: 'Shorter, results-focused demo'
      },
      {
        id: 'interactive',
        name: '20min Interactive Experience',
        weight: 34,
        config: {
          duration: 20,
          focusAreas: ['hands-on', 'customization', 'implementation'],
          interactivity: 'very-high',
          pricingReveal: 'early'
        },
        description: 'Longer, hands-on interactive demo'
      }
    ],
    primaryMetric: 'demo_to_trial_rate',
    secondaryMetrics: ['demo_completion_rate', 'engagement_score', 'followup_response_rate'],
    guardrailMetrics: ['demo_dropout_rate', 'negative_feedback_rate'],
    startDate: new Date('2025-02-01'),
    minimumSampleSize: 600,
    confidenceLevel: 95,
    powerAnalysis: 80,
    maxRuntime: 28,
    createdBy: 'demo-team',
    createdAt: new Date(),
    updatedAt: new Date()
  },

  // 4. EMAIL OUTREACH OPTIMIZATION
  'email-subject-lines': {
    id: 'email-subject-lines',
    name: 'Cold Email Subject Line Testing',
    description: 'Test different email subject line approaches for maximum open rates',
    status: 'draft',
    variants: [
      {
        id: 'control',
        name: 'Direct: AI Voice Agents for Real Estate',
        weight: 20,
        config: {
          subject: 'AI Voice Agents for Real Estate - 15min Demo?',
          tone: 'professional',
          personalization: 'low'
        },
        description: 'Direct, professional approach'
      },
      {
        id: 'curiosity',
        name: 'Curiosity: How Sarah Added 40 Leads/Week',
        weight: 20,
        config: {
          subject: 'How Sarah added 40 qualified leads per week',
          tone: 'story',
          personalization: 'medium'
        },
        description: 'Curiosity-driven with case study'
      },
      {
        id: 'urgency',
        name: 'Urgency: Missing Leads While You Sleep?',
        weight: 20,
        config: {
          subject: 'Missing leads while you sleep? (Quick fix)',
          tone: 'urgent',
          personalization: 'high'
        },
        description: 'Urgency with problem/solution'
      },
      {
        id: 'social-proof',
        name: 'Social Proof: 500+ Agents Using This',
        weight: 20,
        config: {
          subject: '500+ agents using this lead qualification method',
          tone: 'social',
          personalization: 'medium'
        },
        description: 'Social proof approach'
      },
      {
        id: 'question',
        name: 'Question: Tired of Qualifying Leads?',
        weight: 20,
        config: {
          subject: 'Tired of spending 20 hours/week qualifying leads?',
          tone: 'conversational',
          personalization: 'high'
        },
        description: 'Question-based engagement'
      }
    ],
    primaryMetric: 'email_open_rate',
    secondaryMetrics: ['email_click_rate', 'demo_booking_from_email', 'reply_rate'],
    guardrailMetrics: ['unsubscribe_rate', 'spam_complaints'],
    startDate: new Date('2025-01-18'),
    minimumSampleSize: 2000,
    confidenceLevel: 95,
    powerAnalysis: 80,
    maxRuntime: 7,
    createdBy: 'outreach-team',
    createdAt: new Date(),
    updatedAt: new Date()
  }
}

// Experiment states and management
export class ExperimentManager {
  private static instance: ExperimentManager
  private experiments: Map<string, ExperimentConfig> = new Map()
  private userAssignments: Map<string, Record<string, string>> = new Map()

  static getInstance(): ExperimentManager {
    if (!ExperimentManager.instance) {
      ExperimentManager.instance = new ExperimentManager()
    }
    return ExperimentManager.instance
  }

  constructor() {
    // Load experiments from config
    Object.entries(EXPERIMENTS).forEach(([id, config]) => {
      this.experiments.set(id, config)
    })
  }

  // Get user's variant for an experiment
  getUserVariant(userId: string, experimentId: string): ExperimentVariant | null {
    const experiment = this.experiments.get(experimentId)
    if (!experiment || experiment.status !== 'running') {
      return null
    }

    // Check if user already has assignment
    const userExperiments = this.userAssignments.get(userId) || {}
    if (userExperiments[experimentId]) {
      const variantId = userExperiments[experimentId]
      return experiment.variants.find(v => v.id === variantId) || null
    }

    // Assign user to variant based on traffic weights
    const variant = this.assignUserToVariant(userId, experiment)
    if (variant) {
      userExperiments[experimentId] = variant.id
      this.userAssignments.set(userId, userExperiments)
    }

    return variant
  }

  private assignUserToVariant(userId: string, experiment: ExperimentConfig): ExperimentVariant | null {
    // Use consistent hash-based assignment
    const hash = this.hashString(userId + experiment.id)
    const normalizedHash = (hash % 10000) / 10000
    
    let cumulativeWeight = 0
    for (const variant of experiment.variants) {
      cumulativeWeight += variant.weight / 100
      if (normalizedHash <= cumulativeWeight) {
        return variant
      }
    }
    
    return experiment.variants[0] // Fallback to first variant
  }

  private hashString(str: string): number {
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash // Convert to 32-bit integer
    }
    return Math.abs(hash)
  }

  // Update experiment status
  updateExperimentStatus(experimentId: string, status: ExperimentConfig['status']): void {
    const experiment = this.experiments.get(experimentId)
    if (experiment) {
      experiment.status = status
      experiment.updatedAt = new Date()
    }
  }

  // Get all active experiments
  getActiveExperiments(): ExperimentConfig[] {
    return Array.from(this.experiments.values())
      .filter(exp => exp.status === 'running')
  }

  // Get experiment by ID
  getExperiment(experimentId: string): ExperimentConfig | null {
    return this.experiments.get(experimentId) || null
  }
}

// Utility functions for experiment configuration
export const experimentUtils = {
  calculateRequiredSampleSize(baselineRate: number, minimumDetectableEffect: number, power: number = 0.8, alpha: number = 0.05): number {
    // Simplified sample size calculation for conversion rate tests
    const z_alpha = 1.96 // for 95% confidence
    const z_beta = 0.84 // for 80% power
    
    const p1 = baselineRate
    const p2 = baselineRate * (1 + minimumDetectableEffect)
    
    const pooled_p = (p1 + p2) / 2
    const pooled_se = Math.sqrt(2 * pooled_p * (1 - pooled_p))
    
    const n = Math.pow((z_alpha + z_beta) * pooled_se / (p2 - p1), 2)
    
    return Math.ceil(n)
  },

  getExperimentDuration(sampleSize: number, dailyTraffic: number): number {
    return Math.ceil(sampleSize / dailyTraffic)
  },

  validateExperimentConfig(config: ExperimentConfig): string[] {
    const errors: string[] = []
    
    if (config.variants.length < 2) {
      errors.push('Experiment must have at least 2 variants')
    }
    
    const totalWeight = config.variants.reduce((sum, v) => sum + v.weight, 0)
    if (Math.abs(totalWeight - 100) > 0.01) {
      errors.push('Variant weights must sum to 100%')
    }
    
    if (config.minimumSampleSize < 100) {
      errors.push('Minimum sample size must be at least 100')
    }
    
    return errors
  }
}