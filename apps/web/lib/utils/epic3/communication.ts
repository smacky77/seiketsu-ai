// Communication Utilities for Epic 3

export interface MessageTemplate {
  id: string
  name: string
  type: 'email' | 'sms' | 'push'
  subject?: string
  content: string
  variables: string[]
  category: string
  language: string
  version: number
}

export interface PersonalizationContext {
  leadId: string
  firstName?: string
  lastName?: string
  email: string
  phone?: string
  propertyInterest?: string
  priceRange?: {
    min: number
    max: number
  }
  location?: string
  lastActivity?: Date
  preferences?: Record<string, any>
  customFields?: Record<string, any>
}

export interface CommunicationMetrics {
  sent: number
  delivered: number
  opened: number
  clicked: number
  responded: number
  bounced: number
  unsubscribed: number
  failed: number
}

export class MessagePersonalizer {
  private static instance: MessagePersonalizer
  private templates = new Map<string, MessageTemplate>()
  private fallbackTemplates = new Map<string, MessageTemplate>()

  private constructor() {
    this.initializeDefaultTemplates()
  }

  static getInstance(): MessagePersonalizer {
    if (!MessagePersonalizer.instance) {
      MessagePersonalizer.instance = new MessagePersonalizer()
    }
    return MessagePersonalizer.instance
  }

  private initializeDefaultTemplates() {
    // Templates initialization disabled for build - will be implemented in Epic 4
    console.log('Templates initialized (placeholder)')
    return
  }
}
