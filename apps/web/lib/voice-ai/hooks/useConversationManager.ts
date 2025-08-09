import { useCallback, useEffect, useRef, useState } from 'react'
import { useVoiceAIStore } from '../stores/voiceAIStore'
import type { 
  ConversationContext,
  ConversationTurn,
  VoiceAgent,
  LeadProfile,
  LeadQualificationData,
  ConversationAnalytics,
  CallDisposition
} from '../types'

interface UseConversationManagerOptions {
  autoSave?: boolean
  saveInterval?: number // ms
  maxTurns?: number
  enableAnalytics?: boolean
}

interface ConversationMetrics {
  duration: number
  turnCount: number
  userTurns: number
  agentTurns: number
  averageResponseTime: number
  qualificationScore: number
  engagementScore: number
}

export function useConversationManager(options: UseConversationManagerOptions = {}) {
  const {
    currentConversation,
    activeAgent,
    currentLead,
    qualificationData,
    startConversation,
    endConversation,
    addConversationTurn,
    updateConversationMetadata,
    setCurrentLead,
    updateLeadProfile,
    updateQualificationData
  } = useVoiceAIStore()

  const [isActive, setIsActive] = useState(false)
  const [metrics, setMetrics] = useState<ConversationMetrics>({
    duration: 0,
    turnCount: 0,
    userTurns: 0,
    agentTurns: 0,
    averageResponseTime: 0,
    qualificationScore: 0,
    engagementScore: 0
  })

  // Refs for tracking
  const saveIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const responseTimes = useRef<number[]>([])
  const lastUserTurnTime = useRef<number>(0)

  // Start a new conversation
  const start = useCallback(async (lead?: LeadProfile, agent?: VoiceAgent): Promise<ConversationContext> => {
    try {
      // Set lead and agent if provided
      if (lead) {
        setCurrentLead(lead)
      }
      
      const conversation = await startConversation(
        lead?.id,
        agent?.id || activeAgent?.id
      )
      
      setIsActive(true)
      
      // Setup auto-save if enabled
      if (options.autoSave && options.saveInterval) {
        saveIntervalRef.current = setInterval(() => {
          saveConversation()
        }, options.saveInterval)
      }
      
      console.log('Conversation started:', conversation.id)
      return conversation
    } catch (error) {
      console.error('Failed to start conversation:', error)
      throw error
    }
  }, [
    startConversation,
    setCurrentLead,
    activeAgent,
    options.autoSave,
    options.saveInterval
  ])

  // End the current conversation
  const end = useCallback(async (disposition?: CallDisposition): Promise<void> => {
    try {
      if (!currentConversation) return

      // Add disposition if provided
      if (disposition) {
        updateConversationMetadata({
          platform: 'voice',
          channel: 'phone',
          source: 'inbound',
          // disposition data will be handled separately
        } as any)
      }

      await endConversation()
      setIsActive(false)
      
      // Clear auto-save interval
      if (saveIntervalRef.current) {
        clearInterval(saveIntervalRef.current)
        saveIntervalRef.current = null
      }
      
      // Reset metrics
      setMetrics({
        duration: 0,
        turnCount: 0,
        userTurns: 0,
        agentTurns: 0,
        averageResponseTime: 0,
        qualificationScore: 0,
        engagementScore: 0
      })
      
      responseTimes.current = []
      
      console.log('Conversation ended')
    } catch (error) {
      console.error('Failed to end conversation:', error)
      throw error
    }
  }, [currentConversation, endConversation, updateConversationMetadata])

  // Add a turn to the conversation
  const addTurn = useCallback((
    speaker: 'user' | 'agent',
    text: string,
    metadata: Partial<ConversationTurn> = {}
  ): ConversationTurn => {
    if (!currentConversation) {
      throw new Error('No active conversation')
    }

    const turn: ConversationTurn = {
      id: `turn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      speaker,
      text,
      ...metadata
    }

    // Track response times
    if (speaker === 'agent' && lastUserTurnTime.current > 0) {
      const responseTime = turn.timestamp - lastUserTurnTime.current
      responseTimes.current.push(responseTime)
      
      // Keep only last 20 response times for average calculation
      if (responseTimes.current.length > 20) {
        responseTimes.current = responseTimes.current.slice(-20)
      }
    } else if (speaker === 'user') {
      lastUserTurnTime.current = turn.timestamp
    }

    addConversationTurn(turn)
    updateMetrics()
    
    // Check for max turns limit
    if (options.maxTurns && currentConversation.turns.length >= options.maxTurns) {
      console.warn('Maximum turns reached, consider ending conversation')
    }

    return turn
  }, [currentConversation, addConversationTurn, options.maxTurns])

  // Update conversation metrics
  const updateMetrics = useCallback(() => {
    if (!currentConversation) return

    const turns = currentConversation.turns
    const userTurns = turns.filter(t => t.speaker === 'user').length
    const agentTurns = turns.filter(t => t.speaker === 'agent').length
    const duration = Date.now() - currentConversation.startTime
    
    const averageResponseTime = responseTimes.current.length > 0
      ? responseTimes.current.reduce((sum, time) => sum + time, 0) / responseTimes.current.length
      : 0

    const newMetrics: ConversationMetrics = {
      duration,
      turnCount: turns.length,
      userTurns,
      agentTurns,
      averageResponseTime,
      qualificationScore: qualificationData?.score || 0,
      engagementScore: calculateEngagementScore(turns)
    }

    setMetrics(newMetrics)
  }, [currentConversation, qualificationData])

  // Calculate engagement score based on conversation patterns
  const calculateEngagementScore = useCallback((turns: ConversationTurn[]): number => {
    if (turns.length === 0) return 0

    let score = 0
    
    // Base score from turn count (more turns = more engagement)
    score += Math.min(turns.length * 2, 40)
    
    // Bonus for balanced conversation
    const userTurns = turns.filter(t => t.speaker === 'user').length
    const agentTurns = turns.filter(t => t.speaker === 'agent').length
    const balance = userTurns > 0 ? Math.min(agentTurns / userTurns, userTurns / agentTurns) : 0
    score += balance * 20
    
    // Bonus for positive sentiment
    const sentimentTurns = turns.filter(t => t.sentiment && t.sentiment.polarity > 0)
    if (sentimentTurns.length > 0) {
      score += (sentimentTurns.length / turns.length) * 20
    }
    
    // Bonus for specific intents
    const qualificationIntents = turns.filter(t => 
      t.intent && ['budget_qualification', 'timeline_qualification', 'location_qualification'].includes(t.intent)
    )
    score += qualificationIntents.length * 5
    
    // Penalty for very short responses
    const shortResponses = turns.filter(t => t.text.length < 10)
    score -= shortResponses.length * 2
    
    return Math.max(0, Math.min(100, score))
  }, [])

  // Update lead qualification data
  const updateQualification = useCallback((updates: Partial<LeadQualificationData>) => {
    updateQualificationData(updates)
    updateMetrics()
  }, [updateQualificationData, updateMetrics])

  // Save conversation (placeholder for actual persistence)
  const saveConversation = useCallback(async () => {
    if (!currentConversation) return

    try {
      // This would typically save to a backend service
      const conversationData = {
        ...currentConversation,
        metrics,
        qualificationData,
        leadProfile: currentLead
      }
      
      console.log('Saving conversation:', conversationData.id)
      
      // Placeholder for actual save logic
      // await api.conversations.save(conversationData)
    } catch (error) {
      console.error('Failed to save conversation:', error)
    }
  }, [currentConversation, metrics, qualificationData, currentLead])

  // Get conversation summary
  const getSummary = useCallback((): string => {
    if (!currentConversation) return ''

    const turns = currentConversation.turns
    const keyPoints: string[] = []
    
    // Extract key information mentioned
    const budgetTurns = turns.filter(t => 
      t.text.toLowerCase().includes('budget') || 
      t.text.toLowerCase().includes('price') ||
      /\$[\d,]+/.test(t.text)
    )
    if (budgetTurns.length > 0) {
      keyPoints.push('Discussed budget and pricing')
    }
    
    const locationTurns = turns.filter(t => 
      t.text.toLowerCase().includes('location') ||
      t.text.toLowerCase().includes('area') ||
      t.text.toLowerCase().includes('neighborhood')
    )
    if (locationTurns.length > 0) {
      keyPoints.push('Discussed location preferences')
    }
    
    const timelineTurns = turns.filter(t => 
      t.text.toLowerCase().includes('when') ||
      t.text.toLowerCase().includes('timeline') ||
      t.text.toLowerCase().includes('soon')
    )
    if (timelineTurns.length > 0) {
      keyPoints.push('Discussed timeline')
    }
    
    if (qualificationData && qualificationData.score > 70) {
      keyPoints.push('Lead is well qualified')
    }
    
    return keyPoints.length > 0 
      ? `Key discussion points: ${keyPoints.join(', ')}`
      : 'General inquiry conversation'
  }, [currentConversation, qualificationData])

  // Get suggested next actions
  const getNextActions = useCallback((): string[] => {
    const actions: string[] = []
    
    if (!qualificationData) return actions
    
    if (qualificationData.score < 50) {
      actions.push('Continue qualification process')
    }
    
    if (qualificationData.budget && qualificationData.budget.confidence > 0.7) {
      actions.push('Send property recommendations within budget')
    }
    
    if (qualificationData.timeline && qualificationData.timeline.urgency === 'immediate') {
      actions.push('Schedule immediate property viewing')
    }
    
    if (qualificationData.location && qualificationData.location.confidence > 0.7) {
      actions.push('Prepare area-specific market information')
    }
    
    if (qualificationData.score > 80) {
      actions.push('Schedule appointment for property tour')
    }
    
    return actions
  }, [qualificationData])

  // Auto-update metrics when conversation changes
  useEffect(() => {
    if (currentConversation) {
      updateMetrics()
    }
  }, [currentConversation, updateMetrics])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (saveIntervalRef.current) {
        clearInterval(saveIntervalRef.current)
      }
    }
  }, [])

  return {
    // State
    isActive,
    conversation: currentConversation,
    lead: currentLead,
    agent: activeAgent,
    qualification: qualificationData,
    metrics,
    
    // Actions
    start,
    end,
    addTurn,
    updateQualification,
    save: saveConversation,
    
    // Utilities
    getSummary,
    getNextActions,
    
    // Computed values
    duration: metrics.duration,
    turnCount: metrics.turnCount,
    qualificationScore: metrics.qualificationScore,
    engagementScore: metrics.engagementScore,
    averageResponseTime: metrics.averageResponseTime,
    
    // Status checks
    isQualified: (qualificationData?.score || 0) > 70,
    isEngaged: metrics.engagementScore > 60,
    needsFollowUp: (qualificationData?.score || 0) > 50 && (qualificationData?.score || 0) < 80
  }
}