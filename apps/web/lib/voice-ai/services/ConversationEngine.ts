import type { 
  ConversationContext,
  ConversationTurn,
  IntentRecognition,
  LeadQualificationData,
  VoiceAgent,
  EmotionDetection,
  VoiceAIEventListener,
  VoiceAIEvent,
  PropertyInquiry
} from '../types'

interface ConversationRule {
  trigger: string | RegExp
  action: string
  parameters?: Record<string, any>
  priority: number
}

interface ConversationState {
  phase: 'greeting' | 'discovery' | 'qualification' | 'presentation' | 'objection_handling' | 'closing' | 'follow_up'
  lastIntent: string
  contextMemory: Record<string, any>
  qualificationProgress: Record<string, boolean>
  objections: string[]
  nextActions: string[]
}

export class ConversationEngine {
  private context: ConversationContext | null = null
  private agent: VoiceAgent | null = null
  private state: ConversationState
  private listeners: VoiceAIEventListener[] = []
  private rules: ConversationRule[] = []
  private isProcessing = false
  
  // Real estate conversation patterns
  private qualificationQuestions = {
    budget: [
      "What's your budget range for this purchase?",
      "Have you been pre-approved for a mortgage?",
      "What price range are you comfortable with?"
    ],
    timeline: [
      "When are you looking to make a move?",
      "Is this purchase urgent or are you exploring options?",
      "What's your ideal timeline?"
    ],
    location: [
      "Which areas are you most interested in?",
      "Are you flexible with location?",
      "What's driving your location preference?"
    ],
    motivation: [
      "What's prompting you to buy now?",
      "Is this for your primary residence?",
      "What's most important to you in your next home?"
    ],
    requirements: [
      "How many bedrooms do you need?",
      "Any specific features you're looking for?",
      "What's your must-have list?"
    ]
  }

  constructor() {
    this.state = {
      phase: 'greeting',
      lastIntent: '',
      contextMemory: {},
      qualificationProgress: {},
      objections: [],
      nextActions: []
    }
    
    this.initializeRules()
  }

  private initializeRules(): void {
    this.rules = [
      // Greeting phase
      {
        trigger: /hello|hi|hey|good (morning|afternoon|evening)/i,
        action: 'greeting_response',
        priority: 10
      },
      
      // Property inquiry
      {
        trigger: /looking for|interested in|want to buy|property|house|home/i,
        action: 'property_inquiry',
        priority: 8
      },
      
      // Budget qualification
      {
        trigger: /budget|price|cost|afford|mortgage|financing/i,
        action: 'budget_qualification',
        priority: 9
      },
      
      // Timeline qualification
      {
        trigger: /when|timeline|urgent|soon|immediately|time frame/i,
        action: 'timeline_qualification',
        priority: 8
      },
      
      // Location preferences
      {
        trigger: /where|location|area|neighborhood|district|zone/i,
        action: 'location_qualification',
        priority: 7
      },
      
      // Objection handling
      {
        trigger: /too expensive|can't afford|not sure|maybe|think about it/i,
        action: 'handle_objection',
        priority: 9
      },
      
      // Closing signals
      {
        trigger: /ready|let's do it|sounds good|interested|schedule|appointment/i,
        action: 'attempt_close',
        priority: 10
      },
      
      // Information requests
      {
        trigger: /tell me more|details|information|specs|features/i,
        action: 'provide_information',
        priority: 6
      }
    ]
  }

  async startConversation(context: ConversationContext, agent: VoiceAgent): Promise<void> {
    this.context = context
    this.agent = agent
    this.state.phase = 'greeting'
    
    console.log('Conversation started:', {
      conversationId: context.id,
      agentId: agent.id,
      leadId: context.leadId
    })
    
    // Send initial greeting
    const greeting = this.generateGreeting()
    await this.addTurn('agent', greeting)
    
    this.emitEvent({
      type: 'conversation_started',
      data: { context, agent, greeting }
    })
  }

  async processUserInput(text: string, confidence = 1.0): Promise<string> {
    if (!this.context || !this.agent) {
      throw new Error('Conversation not started')
    }

    this.isProcessing = true
    
    try {
      // Add user turn
      await this.addTurn('user', text, { confidence })
      
      // Analyze intent
      const intent = this.analyzeIntent(text)
      this.state.lastIntent = intent.intent
      
      // Update conversation state
      this.updateConversationState(text, intent)
      
      // Generate response
      const response = await this.generateResponse(text, intent)
      
      // Add agent turn
      await this.addTurn('agent', response)
      
      // Update qualification data
      this.updateQualificationData(text, intent)
      
      // Emit events
      this.emitEvent({
        type: 'intent_detected',
        data: intent
      })
      
      this.emitEvent({
        type: 'conversation_turn',
        data: this.context.turns[this.context.turns.length - 1]
      })
      
      return response
      
    } finally {
      this.isProcessing = false
    }
  }

  private async addTurn(speaker: 'user' | 'agent', text: string, metadata: any = {}): Promise<ConversationTurn> {
    const turn: ConversationTurn = {
      id: `turn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      speaker,
      text,
      confidence: metadata.confidence,
      intent: metadata.intent,
      entities: metadata.entities,
      sentiment: metadata.sentiment
    }
    
    if (this.context) {
      this.context.turns.push(turn)
      
      // Update analytics
      if (this.context.analytics) {
        this.updateAnalytics(turn)
      }
    }
    
    return turn
  }

  private analyzeIntent(text: string): IntentRecognition {
    const normalizedText = text.toLowerCase()
    
    // Check against conversation rules
    for (const rule of this.rules.sort((a, b) => b.priority - a.priority)) {
      const trigger = typeof rule.trigger === 'string' 
        ? new RegExp(rule.trigger, 'i') 
        : rule.trigger
      
      if (trigger.test(normalizedText)) {
        return {
          intent: rule.action,
          confidence: 0.8,
          entities: this.extractEntities(text, rule.action),
          domain: 'real_estate'
        }
      }
    }
    
    // Default intent
    return {
      intent: 'general_inquiry',
      confidence: 0.5,
      entities: {},
      domain: 'general'
    }
  }

  private extractEntities(text: string, intent: string): Record<string, any> {
    const entities: Record<string, any> = {}
    const normalizedText = text.toLowerCase()
    
    // Extract price/budget entities
    const priceMatches = text.match(/\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)[k]?/g)
    if (priceMatches) {
      entities.budget = priceMatches.map(match => {
        const value = parseFloat(match.replace(/[$,]/g, ''))
        return match.includes('k') ? value * 1000 : value
      })
    }
    
    // Extract location entities
    const locationPattern = /(downtown|uptown|north|south|east|west|central|suburb|city|town)/gi
    const locationMatches = text.match(locationPattern)
    if (locationMatches) {
      entities.location = locationMatches
    }
    
    // Extract property type entities
    const propertyTypes = /(house|home|condo|apartment|townhouse|villa|mansion|studio)/gi
    const propertyMatches = text.match(propertyTypes)
    if (propertyMatches) {
      entities.propertyType = propertyMatches
    }
    
    // Extract room count entities
    const roomPattern = /(\d+)\s*(bed|bedroom|bath|bathroom)/gi
    const roomMatches = text.match(roomPattern)
    if (roomMatches) {
      entities.rooms = roomMatches
    }
    
    // Extract timeline entities
    const timelinePattern = /(immediately|asap|soon|month|months|year|urgent|flexible)/gi
    const timelineMatches = text.match(timelinePattern)
    if (timelineMatches) {
      entities.timeline = timelineMatches
    }
    
    return entities
  }

  private updateConversationState(text: string, intent: IntentRecognition): void {
    // Update phase based on intent
    switch (intent.intent) {
      case 'greeting_response':
        this.state.phase = 'discovery'
        break
      case 'property_inquiry':
        this.state.phase = 'qualification'
        break
      case 'budget_qualification':
      case 'timeline_qualification':
      case 'location_qualification':
        this.state.phase = 'qualification'
        this.state.qualificationProgress[intent.intent] = true
        break
      case 'handle_objection':
        this.state.phase = 'objection_handling'
        this.state.objections.push(text)
        break
      case 'attempt_close':
        this.state.phase = 'closing'
        break
    }
    
    // Store entities in context memory
    Object.assign(this.state.contextMemory, intent.entities)
  }

  private async generateResponse(text: string, intent: IntentRecognition): Promise<string> {
    const responses = this.getResponseTemplates(intent.intent)
    
    if (responses.length === 0) {
      return this.generateFallbackResponse(text)
    }
    
    // Select response based on conversation state
    let selectedResponse = responses[Math.floor(Math.random() * responses.length)]
    
    // Personalize response with entities and context
    selectedResponse = this.personalizeResponse(selectedResponse, intent.entities)
    
    return selectedResponse
  }

  private getResponseTemplates(intent: string): string[] {
    const responses: Record<string, string[]> = {
      greeting_response: [
        "Hello! I'm here to help you find your perfect home. What type of property are you looking for?",
        "Hi there! Great to speak with you. Tell me, what's bringing you to the market today?",
        "Welcome! I'd love to help you with your real estate needs. What can I tell you about?"
      ],
      
      property_inquiry: [
        "That sounds exciting! To help you find the best options, could you tell me your budget range?",
        "Perfect! Let me ask a few questions to understand your needs better. What's your price range?",
        "Great! I have some wonderful properties that might interest you. What's your budget looking like?"
      ],
      
      budget_qualification: [
        "That's a good budget to work with. Have you been pre-approved for financing?",
        "Excellent! That opens up some great options. When are you looking to make a move?",
        "Perfect! With that budget, we have several properties that would be ideal. What's your timeline?"
      ],
      
      timeline_qualification: [
        "That timeline works well. Which areas are you most interested in?",
        "Good to know! Location is so important. What neighborhoods are you considering?",
        "Perfect timing! Where would you like to focus your search?"
      ],
      
      location_qualification: [
        "Those are excellent areas! What type of property are you looking for?",
        "Great choice of location! How many bedrooms do you need?",
        "I know those areas well! What features are most important to you?"
      ],
      
      handle_objection: [
        "I understand your concerns. Let me show you how we can work within your comfort zone.",
        "That's a valid point. Many of my clients felt the same way initially. Here's what I found...",
        "I appreciate your honesty. Let's explore some options that might address those concerns."
      ],
      
      attempt_close: [
        "Wonderful! I'd love to schedule a time to show you some properties. When works best for you?",
        "That's great to hear! Let's set up an appointment. Are you available this weekend?",
        "Perfect! I have the ideal property in mind. Can we schedule a viewing tomorrow?"
      ],
      
      provide_information: [
        "I'd be happy to share more details. This property features...",
        "Absolutely! Here's what makes this special...",
        "Great question! Let me tell you about the key features..."
      ]
    }
    
    return responses[intent] || []
  }

  private personalizeResponse(template: string, entities: Record<string, any>): string {
    let response = template
    
    // Replace placeholders with actual values
    if (entities.budget) {
      response = response.replace(/\{budget\}/g, `$${entities.budget[0].toLocaleString()}`)
    }
    
    if (entities.location) {
      response = response.replace(/\{location\}/g, entities.location[0])
    }
    
    if (entities.propertyType) {
      response = response.replace(/\{propertyType\}/g, entities.propertyType[0])
    }
    
    return response
  }

  private generateFallbackResponse(text: string): string {
    const fallbacks = [
      "That's interesting! Could you tell me more about what you're looking for?",
      "I want to make sure I understand correctly. Can you elaborate on that?",
      "Thanks for sharing that. What else would you like to know?",
      "I appreciate that information. How can I best help you today?"
    ]
    
    return fallbacks[Math.floor(Math.random() * fallbacks.length)]
  }

  private generateGreeting(): string {
    const greetings = [
      "Hello! Thank you for your interest in real estate. I'm here to help you find your perfect home.",
      "Hi there! I'm excited to help you with your property search. What brings you to the market today?",
      "Welcome! I'm your personal real estate assistant. Let's find you the ideal property!"
    ]
    
    return greetings[Math.floor(Math.random() * greetings.length)]
  }

  private updateQualificationData(text: string, intent: IntentRecognition): void {
    if (!this.context) return
    
    const qualification = this.context.qualificationData || {
      score: 0,
      budget: { confidence: 0 },
      timeline: { confidence: 0 },
      location: { confidence: 0 },
      propertyType: { confidence: 0 },
      motivation: { confidence: 0 },
      decisionMaker: { confidence: 0 }
    }
    
    // Update based on extracted entities
    if (intent.entities.budget) {
      qualification.budget = {
        min: Math.min(...intent.entities.budget),
        max: Math.max(...intent.entities.budget),
        confidence: intent.confidence
      }
    }
    
    if (intent.entities.timeline) {
      const timelineMap: Record<string, string> = {
        'immediately': 'immediate',
        'asap': 'immediate',
        'soon': 'soon',
        'urgent': 'immediate',
        'flexible': 'exploring'
      }
      
      qualification.timeline = {
        urgency: timelineMap[intent.entities.timeline[0]] || 'exploring',
        confidence: intent.confidence
      }
    }
    
    if (intent.entities.location) {
      qualification.location = {
        preferred: intent.entities.location,
        flexibility: 0.7,
        confidence: intent.confidence
      }
    }
    
    if (intent.entities.propertyType) {
      qualification.propertyType = {
        type: intent.entities.propertyType[0],
        features: intent.entities.propertyType,
        confidence: intent.confidence
      }
    }
    
    // Calculate overall qualification score
    const scores = [
      qualification.budget?.confidence || 0,
      qualification.timeline?.confidence || 0,
      qualification.location?.confidence || 0,
      qualification.propertyType?.confidence || 0
    ]
    
    qualification.score = Math.round(
      (scores.reduce((sum, score) => sum + score, 0) / scores.length) * 100
    )
    
    this.context.qualificationData = qualification
    
    this.emitEvent({
      type: 'qualification_updated',
      data: qualification
    })
  }

  private updateAnalytics(turn: ConversationTurn): void {
    if (!this.context?.analytics) return
    
    const analytics = this.context.analytics
    
    // Update talk time ratio
    const totalTurns = this.context.turns.length
    const agentTurns = this.context.turns.filter(t => t.speaker === 'agent').length
    analytics.talkTimeRatio = agentTurns / totalTurns
    
    // Detect interruptions (simplified)
    if (turn.speaker === 'user' && this.context.turns[this.context.turns.length - 2]?.speaker === 'agent') {
      analytics.interruptionCount++
    }
    
    // Extract key topics (simplified)
    const text = turn.text.toLowerCase()
    const topics = ['budget', 'location', 'timeline', 'features', 'mortgage', 'schools']
    topics.forEach(topic => {
      if (text.includes(topic) && !analytics.keyTopics.includes(topic)) {
        analytics.keyTopics.push(topic)
      }
    })
    
    // Detect objections
    const objectionKeywords = ['expensive', 'too much', 'can\'t afford', 'not sure', 'think about it']
    objectionKeywords.forEach(keyword => {
      if (text.includes(keyword) && !analytics.objections.includes(keyword)) {
        analytics.objections.push(keyword)
      }
    })
    
    // Update engagement score (simplified)
    analytics.engagementScore = Math.min(100, 
      (analytics.keyTopics.length * 10) + 
      (this.context.turns.length * 2) - 
      (analytics.objections.length * 5)
    )
  }

  // Event management
  addEventListener(listener: VoiceAIEventListener): void {
    this.listeners.push(listener)
  }

  removeEventListener(listener: VoiceAIEventListener): void {
    const index = this.listeners.indexOf(listener)
    if (index > -1) {
      this.listeners.splice(index, 1)
    }
  }

  private emitEvent(event: VoiceAIEvent): void {
    this.listeners.forEach(listener => {
      try {
        listener(event)
      } catch (error) {
        console.error('Error in conversation event listener:', error)
      }
    })
  }

  // Getters
  get currentPhase(): string {
    return this.state.phase
  }

  get qualificationProgress(): Record<string, boolean> {
    return { ...this.state.qualificationProgress }
  }

  get conversationContext(): ConversationContext | null {
    return this.context
  }

  get isActive(): boolean {
    return this.context !== null && this.agent !== null
  }

  // Cleanup
  endConversation(): void {
    if (this.context) {
      this.context.endTime = Date.now()
      
      this.emitEvent({
        type: 'conversation_ended',
        data: { context: this.context }
      })
    }
    
    this.context = null
    this.agent = null
    this.state = {
      phase: 'greeting',
      lastIntent: '',
      contextMemory: {},
      qualificationProgress: {},
      objections: [],
      nextActions: []
    }
  }

  destroy(): void {
    this.endConversation()
    this.listeners = []
  }
}