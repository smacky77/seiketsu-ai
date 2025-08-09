import { useCallback, useEffect, useState } from 'react'
import { useVoiceAIStore } from '../stores/voiceAIStore'
import type { 
  ConversationAnalytics,
  VoiceAIMetrics,
  ConversationContext,
  ConversationTurn,
  LeadQualificationData
} from '../types'

interface UseVoiceAnalyticsOptions {
  trackInRealTime?: boolean
  calculateSentiment?: boolean
  trackEngagement?: boolean
  updateInterval?: number // ms
}

interface AnalyticsSnapshot {
  timestamp: number
  metrics: VoiceAIMetrics
  conversationAnalytics?: ConversationAnalytics
  qualificationScore: number
  engagementScore: number
}

interface PerformanceMetrics {
  averageLatency: number
  successRate: number
  userSatisfaction: number
  conversionRate: number
  responseQuality: number
}

interface ConversationInsights {
  dominantSpeaker: 'user' | 'agent' | 'balanced'
  conversationFlow: 'smooth' | 'interrupted' | 'fragmented'
  topicProgression: string[]
  emotionalJourney: Array<{ timestamp: number; emotion: string; intensity: number }>
  qualificationProgress: number
  recommendedActions: string[]
}

export function useVoiceAnalytics(options: UseVoiceAnalyticsOptions = {}) {
  const {
    currentConversation,
    qualificationData,
    metrics: storeMetrics
  } = useVoiceAIStore()

  const [analytics, setAnalytics] = useState<ConversationAnalytics | null>(null)
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics>({
    averageLatency: 0,
    successRate: 0,
    userSatisfaction: 0,
    conversionRate: 0,
    responseQuality: 0
  })
  const [insights, setInsights] = useState<ConversationInsights | null>(null)
  const [snapshots, setSnapshots] = useState<AnalyticsSnapshot[]>([])

  // Calculate conversation analytics
  const calculateAnalytics = useCallback((conversation: ConversationContext): ConversationAnalytics => {
    const turns = conversation.turns
    const totalTurns = turns.length
    
    if (totalTurns === 0) {
      return {
        duration: 0,
        talkTimeRatio: 0,
        interruptionCount: 0,
        sentimentTrend: [],
        engagementScore: 0,
        keyTopics: [],
        objections: [],
        nextSteps: [],
        followUpRequired: false
      }
    }

    const userTurns = turns.filter(t => t.speaker === 'user')
    const agentTurns = turns.filter(t => t.speaker === 'agent')
    const duration = Date.now() - conversation.startTime

    // Calculate talk time ratio (agent speaking time / total time)
    const talkTimeRatio = totalTurns > 0 ? agentTurns.length / totalTurns : 0

    // Detect interruptions (consecutive turns by same speaker or very short response times)
    let interruptionCount = 0
    for (let i = 1; i < turns.length; i++) {
      const current = turns[i]
      const previous = turns[i - 1]
      
      // Same speaker in consecutive turns = interruption
      if (current.speaker === previous.speaker) {
        interruptionCount++
      }
      
      // Very quick response (< 1 second) = potential interruption
      if (current.timestamp - previous.timestamp < 1000) {
        interruptionCount++
      }
    }

    // Calculate sentiment trend
    const sentimentTrend = turns
      .filter(t => t.sentiment)
      .map(t => ({
        timestamp: t.timestamp,
        sentiment: t.sentiment!.polarity
      }))

    // Extract key topics from conversation
    const keyTopics = extractKeyTopics(turns)
    
    // Detect objections
    const objections = detectObjections(turns)
    
    // Calculate engagement score
    const engagementScore = calculateEngagementScore(turns, duration)
    
    // Determine next steps
    const nextSteps = determineNextSteps(turns, qualificationData)
    
    return {
      duration,
      talkTimeRatio,
      interruptionCount,
      sentimentTrend,
      engagementScore,
      keyTopics,
      objections,
      nextSteps,
      followUpRequired: engagementScore > 60 && (qualificationData?.score || 0) > 50
    }
  }, [qualificationData])

  // Extract key topics from conversation turns
  const extractKeyTopics = useCallback((turns: ConversationTurn[]): string[] => {
    const topicKeywords = {
      budget: /budget|price|cost|afford|expensive|cheap|money|financing|mortgage|loan/i,
      location: /location|area|neighborhood|district|zone|address|where|place/i,
      timeline: /when|time|schedule|urgent|soon|deadline|timing|asap|immediately/i,
      features: /bedroom|bathroom|kitchen|garage|yard|pool|view|space|size|square feet/i,
      schools: /school|education|district|rating|kids|children|family/i,
      investment: /investment|rental|income|roi|appreciation|property value|market/i,
      condition: /condition|repair|renovation|new|old|updated|maintenance/i,
      negotiation: /negotiate|offer|counter|price reduction|deal|terms/i
    }

    const topics: Set<string> = new Set()
    const allText = turns.map(t => t.text).join(' ').toLowerCase()

    Object.entries(topicKeywords).forEach(([topic, pattern]) => {
      if (pattern.test(allText)) {
        topics.add(topic)
      }
    })

    return Array.from(topics)
  }, [])

  // Detect objections in conversation
  const detectObjections = useCallback((turns: ConversationTurn[]): string[] => {
    const objectionPatterns = {
      price: /too expensive|can't afford|over budget|too much money|price is high/i,
      timing: /not ready|too soon|need more time|not the right time/i,
      location: /wrong area|don't like the location|too far|not convenient/i,
      features: /not what I'm looking for|missing features|too small|too big/i,
      market: /market is bad|prices are falling|want to wait|timing is wrong/i,
      competition: /need to see more|shopping around|comparing options/i,
      trust: /need to think|not sure|hesitant|concerned|worried/i
    }

    const objections: Set<string> = new Set()
    const userTurns = turns.filter(t => t.speaker === 'user')

    userTurns.forEach(turn => {
      Object.entries(objectionPatterns).forEach(([objection, pattern]) => {
        if (pattern.test(turn.text)) {
          objections.add(objection)
        }
      })
    })

    return Array.from(objections)
  }, [])

  // Calculate engagement score based on conversation patterns
  const calculateEngagementScore = useCallback((turns: ConversationTurn[], duration: number): number => {
    if (turns.length === 0) return 0

    let score = 0

    // Base score from interaction frequency
    const interactionRate = turns.length / (duration / 60000) // turns per minute
    score += Math.min(30, interactionRate * 10)

    // Balance between user and agent participation
    const userTurns = turns.filter(t => t.speaker === 'user').length
    const agentTurns = turns.filter(t => t.speaker === 'agent').length
    
    if (userTurns > 0 && agentTurns > 0) {
      const balance = Math.min(userTurns, agentTurns) / Math.max(userTurns, agentTurns)
      score += balance * 25
    }

    // Response length variety (not too short, not too long)
    const avgResponseLength = turns.reduce((sum, t) => sum + t.text.length, 0) / turns.length
    if (avgResponseLength > 20 && avgResponseLength < 200) {
      score += 20
    }

    // Positive sentiment bonus
    const positiveTurns = turns.filter(t => t.sentiment && t.sentiment.polarity > 0.2)
    if (positiveTurns.length > 0) {
      score += (positiveTurns.length / turns.length) * 15
    }

    // Question asking (shows interest)
    const questionTurns = turns.filter(t => t.text.includes('?'))
    score += Math.min(10, questionTurns.length * 2)

    return Math.min(100, Math.max(0, score))
  }, [])

  // Determine next steps based on conversation
  const determineNextSteps = useCallback((
    turns: ConversationTurn[], 
    qualification?: LeadQualificationData | null
  ): string[] => {
    const steps: string[] = []
    const lastTurn = turns[turns.length - 1]
    
    if (!qualification) {
      steps.push('Complete lead qualification')
      return steps
    }

    // Based on qualification score
    if (qualification.score > 80) {
      steps.push('Schedule property viewing')
      steps.push('Prepare customized listing presentation')
    } else if (qualification.score > 60) {
      steps.push('Address remaining qualification gaps')
      steps.push('Send targeted property recommendations')
    } else {
      steps.push('Continue qualification process')
      steps.push('Build rapport and trust')
    }

    // Based on timeline urgency
    if (qualification.timeline?.urgency === 'immediate') {
      steps.push('Schedule urgent follow-up call')
      steps.push('Prepare immediate property options')
    } else if (qualification.timeline?.urgency === 'soon') {
      steps.push('Schedule follow-up within 24 hours')
    }

    // Based on objections
    const objections = detectObjections(turns)
    if (objections.includes('price')) {
      steps.push('Prepare financing options presentation')
    }
    if (objections.includes('location')) {
      steps.push('Expand location search criteria')
    }

    // Based on conversation flow
    if (lastTurn?.speaker === 'user' && lastTurn.text.includes('?')) {
      steps.push('Respond to pending question')
    }

    return steps.slice(0, 5) // Return top 5 steps
  }, [detectObjections])

  // Generate conversation insights
  const generateInsights = useCallback((conversation: ConversationContext): ConversationInsights => {
    const turns = conversation.turns
    const userTurns = turns.filter(t => t.speaker === 'user').length
    const agentTurns = turns.filter(t => t.speaker === 'agent').length

    // Determine dominant speaker
    let dominantSpeaker: ConversationInsights['dominantSpeaker'] = 'balanced'
    if (userTurns > agentTurns * 1.5) {
      dominantSpeaker = 'user'
    } else if (agentTurns > userTurns * 1.5) {
      dominantSpeaker = 'agent'
    }

    // Analyze conversation flow
    let conversationFlow: ConversationInsights['conversationFlow'] = 'smooth'
    const interruptionRate = analytics?.interruptionCount ? analytics.interruptionCount / turns.length : 0
    
    if (interruptionRate > 0.3) {
      conversationFlow = 'interrupted'
    } else if (interruptionRate > 0.1) {
      conversationFlow = 'fragmented'
    }

    // Track topic progression
    const topicProgression = extractKeyTopics(turns)

    // Mock emotional journey (would use actual emotion detection)
    const emotionalJourney = turns
      .filter(t => t.sentiment)
      .map(t => ({
        timestamp: t.timestamp,
        emotion: t.sentiment!.polarity > 0.3 ? 'positive' : 
                 t.sentiment!.polarity < -0.3 ? 'negative' : 'neutral',
        intensity: Math.abs(t.sentiment!.polarity)
      }))

    // Calculate qualification progress
    const qualificationProgress = qualificationData?.score || 0

    // Generate recommendations
    const recommendedActions = determineNextSteps(turns, qualificationData)

    return {
      dominantSpeaker,
      conversationFlow,
      topicProgression,
      emotionalJourney,
      qualificationProgress,
      recommendedActions
    }
  }, [analytics, extractKeyTopics, qualificationData, determineNextSteps])

  // Update analytics when conversation changes
  useEffect(() => {
    if (currentConversation && options.trackInRealTime) {
      const newAnalytics = calculateAnalytics(currentConversation)
      setAnalytics(newAnalytics)
      
      const newInsights = generateInsights(currentConversation)
      setInsights(newInsights)
    }
  }, [currentConversation, options.trackInRealTime, calculateAnalytics, generateInsights])

  // Update performance metrics
  useEffect(() => {
    if (storeMetrics) {
      const newPerformanceMetrics: PerformanceMetrics = {
        averageLatency: storeMetrics.latency.total,
        successRate: Math.max(0, 1 - storeMetrics.performance.errorRate),
        userSatisfaction: analytics?.engagementScore || 0,
        conversionRate: insights?.qualificationProgress || 0,
        responseQuality: storeMetrics.quality.responseRelevance * 100
      }
      
      setPerformanceMetrics(newPerformanceMetrics)
    }
  }, [storeMetrics, analytics, insights])

  // Take analytics snapshot
  const takeSnapshot = useCallback(() => {
    if (!currentConversation || !storeMetrics) return

    const snapshot: AnalyticsSnapshot = {
      timestamp: Date.now(),
      metrics: { ...storeMetrics },
      conversationAnalytics: analytics ? { ...analytics } : undefined,
      qualificationScore: qualificationData?.score || 0,
      engagementScore: analytics?.engagementScore || 0
    }

    setSnapshots(prev => [...prev.slice(-19), snapshot]) // Keep last 20 snapshots
  }, [currentConversation, storeMetrics, analytics, qualificationData])

  // Auto-snapshot at intervals
  useEffect(() => {
    if (!options.updateInterval) return

    const interval = setInterval(takeSnapshot, options.updateInterval)
    return () => clearInterval(interval)
  }, [options.updateInterval, takeSnapshot])

  // Get analytics summary
  const getSummary = useCallback(() => {
    if (!analytics || !currentConversation) {
      return 'No analytics data available'
    }

    const duration = Math.round(analytics.duration / 1000 / 60) // minutes
    const turns = currentConversation.turns.length
    const engagement = Math.round(analytics.engagementScore)
    const qualification = Math.round(qualificationData?.score || 0)

    return `${duration}min conversation, ${turns} turns, ${engagement}% engagement, ${qualification}% qualified`
  }, [analytics, currentConversation, qualificationData])

  // Export analytics data
  const exportData = useCallback(() => {
    return {
      conversation: currentConversation,
      analytics,
      performanceMetrics,
      insights,
      snapshots,
      qualification: qualificationData
    }
  }, [currentConversation, analytics, performanceMetrics, insights, snapshots, qualificationData])

  // Reset analytics
  const reset = useCallback(() => {
    setAnalytics(null)
    setInsights(null)
    setSnapshots([])
    setPerformanceMetrics({
      averageLatency: 0,
      successRate: 0,
      userSatisfaction: 0,
      conversionRate: 0,
      responseQuality: 0
    })
  }, [])

  return {
    // Current analytics
    analytics,
    insights,
    performanceMetrics,
    
    // Snapshots and history
    snapshots,
    
    // Utilities
    takeSnapshot,
    getSummary,
    exportData,
    reset,
    
    // Computed values
    isEngaged: (analytics?.engagementScore || 0) > 60,
    isQualified: (qualificationData?.score || 0) > 70,
    needsAttention: (analytics?.interruptionCount || 0) > 3 || (analytics?.engagementScore || 0) < 40,
    
    // Key metrics (for easy access)
    duration: analytics?.duration || 0,
    turnCount: currentConversation?.turns.length || 0,
    engagementScore: analytics?.engagementScore || 0,
    qualificationScore: qualificationData?.score || 0,
    talkTimeRatio: analytics?.talkTimeRatio || 0,
    averageLatency: performanceMetrics.averageLatency,
    
    // Insights
    dominantSpeaker: insights?.dominantSpeaker || 'balanced',
    conversationFlow: insights?.conversationFlow || 'smooth',
    keyTopics: analytics?.keyTopics || [],
    objections: analytics?.objections || [],
    nextSteps: analytics?.nextSteps || [],
    recommendedActions: insights?.recommendedActions || []
  }
}