import { useCallback, useEffect, useState } from 'react'
import { useVoiceAIStore } from '../stores/voiceAIStore'
import type { VoiceAgent, VoiceCommand, EmotionDetection } from '../types'

interface UseVoiceAgentOptions {
  agentId?: string
  enableCommands?: boolean
  enableEmotionTracking?: boolean
  personalityAdjustments?: Partial<VoiceAgent['personality']>
}

interface VoiceAgentState {
  isActive: boolean
  isProcessing: boolean
  currentEmotion?: EmotionDetection
  lastResponse?: string
  responseCount: number
  averageResponseTime: number
  commands: VoiceCommand[]
}

// Default voice commands for real estate agents
const DEFAULT_COMMANDS: VoiceCommand[] = [
  {
    trigger: /show me properties|available listings|what do you have/i,
    action: 'show_properties',
    description: 'Show available properties'
  },
  {
    trigger: /schedule (appointment|viewing|tour)/i,
    action: 'schedule_appointment',
    description: 'Schedule property viewing'
  },
  {
    trigger: /what's my budget|budget range|how much/i,
    action: 'discuss_budget',
    description: 'Discuss budget and financing'
  },
  {
    trigger: /location|area|neighborhood|where/i,
    action: 'discuss_location',
    description: 'Discuss location preferences'
  },
  {
    trigger: /timeline|when|how soon/i,
    action: 'discuss_timeline',
    description: 'Discuss purchase timeline'
  },
  {
    trigger: /features|requirements|must have/i,
    action: 'discuss_requirements',
    description: 'Discuss property requirements'
  },
  {
    trigger: /mortgage|financing|loan|pre-approved/i,
    action: 'discuss_financing',
    description: 'Discuss financing options'
  },
  {
    trigger: /market conditions|prices|trends/i,
    action: 'market_update',
    description: 'Provide market information'
  },
  {
    trigger: /call me back|schedule call|follow up/i,
    action: 'schedule_callback',
    description: 'Schedule follow-up call'
  },
  {
    trigger: /not interested|stop|end/i,
    action: 'end_conversation',
    description: 'End the conversation'
  }
]

export function useVoiceAgent(options: UseVoiceAgentOptions = {}) {
  const {
    activeAgent,
    setActiveAgent,
    updateAgentMetrics
  } = useVoiceAIStore()

  const [state, setState] = useState<VoiceAgentState>({
    isActive: false,
    isProcessing: false,
    responseCount: 0,
    averageResponseTime: 0,
    commands: options.enableCommands ? DEFAULT_COMMANDS : []
  })

  const [responseTimes, setResponseTimes] = useState<number[]>([])

  // Activate an agent
  const activateAgent = useCallback(async (agent: VoiceAgent) => {
    try {
      // Apply personality adjustments if provided
      const adjustedAgent = options.personalityAdjustments
        ? {
            ...agent,
            personality: { ...agent.personality, ...options.personalityAdjustments }
          }
        : agent

      setActiveAgent(adjustedAgent)
      setState(prev => ({ ...prev, isActive: true }))
      
      console.log('Voice agent activated:', agent.name)
    } catch (error) {
      console.error('Failed to activate agent:', error)
      throw error
    }
  }, [setActiveAgent, options.personalityAdjustments])

  // Deactivate current agent
  const deactivateAgent = useCallback(() => {
    setActiveAgent(null)
    setState(prev => ({ 
      ...prev, 
      isActive: false,
      responseCount: 0,
      averageResponseTime: 0
    }))
    setResponseTimes([])
  }, [setActiveAgent])

  // Process user input with the active agent
  const processInput = useCallback(async (
    input: string,
    context?: Record<string, any>
  ): Promise<string> => {
    if (!activeAgent) {
      throw new Error('No active agent')
    }

    const startTime = Date.now()
    setState(prev => ({ ...prev, isProcessing: true }))

    try {
      // Check for voice commands first
      if (options.enableCommands) {
        const matchedCommand = state.commands.find(cmd => {
          const trigger = typeof cmd.trigger === 'string' 
            ? new RegExp(cmd.trigger, 'i') 
            : cmd.trigger
          return trigger.test(input)
        })

        if (matchedCommand) {
          const response = await handleCommand(matchedCommand, input, context)
          return response
        }
      }

      // Generate contextual response based on agent personality
      const response = await generateAgentResponse(input, context)
      
      // Track response time
      const responseTime = Date.now() - startTime
      const newResponseTimes = [...responseTimes, responseTime].slice(-10) // Keep last 10
      setResponseTimes(newResponseTimes)
      
      const avgResponseTime = newResponseTimes.reduce((sum, time) => sum + time, 0) / newResponseTimes.length
      
      setState(prev => ({
        ...prev,
        isProcessing: false,
        lastResponse: response,
        responseCount: prev.responseCount + 1,
        averageResponseTime: avgResponseTime
      }))

      // Update agent metrics
      updateAgentMetrics(activeAgent.id, {
        conversationsHandled: activeAgent.metrics.conversationsHandled + 1,
        averageCallDuration: avgResponseTime
      })

      return response
    } catch (error) {
      setState(prev => ({ ...prev, isProcessing: false }))
      throw error
    }
  }, [
    activeAgent,
    options.enableCommands,
    state.commands,
    responseTimes,
    updateAgentMetrics
  ])

  // Handle voice commands
  const handleCommand = useCallback(async (
    command: VoiceCommand,
    input: string,
    context?: Record<string, any>
  ): Promise<string> => {
    switch (command.action) {
      case 'show_properties':
        return generatePropertyResponse(context)
      
      case 'schedule_appointment':
        return "I'd be happy to schedule a property viewing for you. What day and time works best?"
      
      case 'discuss_budget':
        return "Let's talk about your budget. What price range are you comfortable with for your new home?"
      
      case 'discuss_location':
        return "Location is so important! What areas or neighborhoods are you most interested in?"
      
      case 'discuss_timeline':
        return "When are you looking to make this move? Are you in a hurry or can we take our time to find the perfect property?"
      
      case 'discuss_requirements':
        return "Tell me about your must-haves. How many bedrooms do you need? Any specific features that are important to you?"
      
      case 'discuss_financing':
        return "Great question! Have you spoken with a lender yet? I can recommend some excellent mortgage professionals if you'd like."
      
      case 'market_update':
        return generateMarketResponse(context)
      
      case 'schedule_callback':
        return "Of course! What's the best number to reach you and when would be a good time for me to call?"
      
      case 'end_conversation':
        return "Thank you for your time today! I'll follow up with you soon. Have a great day!"
      
      default:
        return await generateAgentResponse(input, context)
    }
  }, [])

  // Generate agent response based on personality
  const generateAgentResponse = useCallback(async (
    input: string,
    context?: Record<string, any>
  ): Promise<string> => {
    if (!activeAgent) return "I'm sorry, I'm not available right now."

    const { personality } = activeAgent
    
    // Base responses that can be adjusted based on personality
    const responses: Record<string, string[]> = {
      professional: [
        "I understand your needs. Let me provide you with the most suitable options.",
        "That's an excellent question. Based on my experience in the market...",
        "I'd be happy to help you with that. Here's what I recommend..."
      ],
      friendly: [
        "That sounds great! I'm excited to help you find your perfect home.",
        "Oh, I love helping with that! Let me share what I know...",
        "That's wonderful! I have some fantastic options that might interest you."
      ],
      casual: [
        "Cool! Yeah, I can definitely help you out with that.",
        "No problem at all! Here's the scoop on that...",
        "Awesome question! So here's what's up..."
      ],
      authoritative: [
        "Based on current market conditions and my expertise...",
        "I can assure you that my recommendation is...",
        "With my years of experience in this market, I strongly advise..."
      ]
    }

    const toneResponses = responses[personality.tone] || responses.professional
    let baseResponse = toneResponses[Math.floor(Math.random() * toneResponses.length)]

    // Adjust enthusiasm
    if (personality.enthusiasm > 0.7) {
      baseResponse = baseResponse.replace(/\./g, '!')
    }

    // Add context-specific information
    if (context) {
      if (context.propertyType) {
        baseResponse += ` I have some excellent ${context.propertyType} properties that might be perfect for you.`
      }
      if (context.budget) {
        baseResponse += ` With your budget of ${context.budget}, we have great options available.`
      }
      if (context.location) {
        baseResponse += ` The ${context.location} area has some wonderful properties right now.`
      }
    }

    return baseResponse
  }, [activeAgent])

  // Generate property-specific responses
  const generatePropertyResponse = useCallback((context?: Record<string, any>): string => {
    const responses = [
      "I have several properties that would be perfect for you. Would you like me to send you some listings?",
      "Great! I've got some fantastic options. Let me pull up properties that match your criteria.",
      "Perfect timing! I just got some new listings that I think you'll love. Can I show them to you?"
    ]

    let response = responses[Math.floor(Math.random() * responses.length)]

    if (context?.budget) {
      response += ` I have properties within your ${context.budget} budget range.`
    }

    return response
  }, [])

  // Generate market update responses
  const generateMarketResponse = useCallback((context?: Record<string, any>): string => {
    const marketResponses = [
      "The market is quite active right now. Properties are moving quickly, especially in desirable areas.",
      "We're seeing strong demand in the current market. It's a good time to buy if you find the right property.",
      "Market conditions are favorable for buyers who are prepared and ready to move quickly."
    ]

    return marketResponses[Math.floor(Math.random() * marketResponses.length)]
  }, [])

  // Update agent personality in real-time
  const updatePersonality = useCallback((updates: Partial<VoiceAgent['personality']>) => {
    if (!activeAgent) return

    const updatedAgent = {
      ...activeAgent,
      personality: { ...activeAgent.personality, ...updates }
    }

    setActiveAgent(updatedAgent)
  }, [activeAgent, setActiveAgent])

  // Add custom voice command
  const addCommand = useCallback((command: VoiceCommand) => {
    setState(prev => ({
      ...prev,
      commands: [...prev.commands, command]
    }))
  }, [])

  // Remove voice command
  const removeCommand = useCallback((trigger: string | RegExp) => {
    setState(prev => ({
      ...prev,
      commands: prev.commands.filter(cmd => cmd.trigger !== trigger)
    }))
  }, [])

  // Track emotion changes
  const updateEmotion = useCallback((emotion: EmotionDetection) => {
    if (!options.enableEmotionTracking) return

    setState(prev => ({ ...prev, currentEmotion: emotion }))

    // Adjust agent response based on detected emotion
    if (activeAgent && emotion.confidence > 0.7) {
      const personalityAdjustments: Partial<VoiceAgent['personality']> = {}

      switch (emotion.emotion) {
        case 'frustrated':
        case 'angry':
          personalityAdjustments.tone = 'professional'
          personalityAdjustments.pace = 'slow'
          personalityAdjustments.enthusiasm = Math.max(0.3, activeAgent.personality.enthusiasm - 0.2)
          break
        
        case 'excited':
        case 'happy':
          personalityAdjustments.enthusiasm = Math.min(1, activeAgent.personality.enthusiasm + 0.2)
          break
        
        case 'confused':
          personalityAdjustments.pace = 'slow'
          personalityAdjustments.tone = 'friendly'
          break
        
        case 'sad':
          personalityAdjustments.tone = 'friendly'
          personalityAdjustments.enthusiasm = Math.max(0.3, activeAgent.personality.enthusiasm - 0.1)
          break
      }

      if (Object.keys(personalityAdjustments).length > 0) {
        updatePersonality(personalityAdjustments)
      }
    }
  }, [options.enableEmotionTracking, activeAgent, updatePersonality])

  // Get agent performance metrics
  const getMetrics = useCallback(() => {
    if (!activeAgent) return null

    return {
      ...activeAgent.metrics,
      currentSession: {
        responseCount: state.responseCount,
        averageResponseTime: state.averageResponseTime,
        isActive: state.isActive
      }
    }
  }, [activeAgent, state])

  // Auto-activate agent if ID provided
  useEffect(() => {
    if (options.agentId && !activeAgent) {
      // In a real implementation, you would fetch the agent data
      // For now, create a default agent
      const defaultAgent: VoiceAgent = {
        id: options.agentId,
        name: 'AI Real Estate Assistant',
        voiceId: 'default',
        personality: {
          tone: 'friendly',
          pace: 'normal',
          enthusiasm: 0.7
        },
        expertise: ['residential', 'commercial', 'investment'],
        systemPrompt: 'You are a helpful real estate assistant focused on helping clients find their perfect home.',
        conversationRules: {
          maxTurnLength: 500,
          allowInterruptions: true,
          escalationTriggers: ['complaint', 'angry', 'frustrated']
        },
        isActive: true,
        metrics: {
          conversationsHandled: 0,
          averageQualificationScore: 0,
          conversionRate: 0,
          averageCallDuration: 0
        }
      }
      
      activateAgent(defaultAgent)
    }
  }, [options.agentId, activeAgent, activateAgent])

  return {
    // State
    agent: activeAgent,
    isActive: state.isActive,
    isProcessing: state.isProcessing,
    currentEmotion: state.currentEmotion,
    lastResponse: state.lastResponse,
    commands: state.commands,
    
    // Actions
    activate: activateAgent,
    deactivate: deactivateAgent,
    process: processInput,
    updatePersonality,
    updateEmotion,
    
    // Command management
    addCommand,
    removeCommand,
    
    // Metrics
    metrics: getMetrics(),
    responseCount: state.responseCount,
    averageResponseTime: state.averageResponseTime
  }
}