import { useCallback, useEffect, useState } from 'react'
import { useVoiceAIStore } from '../stores/voiceAIStore'
import type { 
  LeadQualificationData,
  LeadProfile,
  ConversationTurn,
  PropertyInquiry
} from '../types'

interface UseLeadQualificationOptions {
  minScore?: number // Minimum score to consider qualified
  autoScore?: boolean
  enableRealTimeUpdates?: boolean
  weightings?: QualificationWeightings
}

interface QualificationWeightings {
  budget: number
  timeline: number
  location: number
  propertyType: number
  motivation: number
  decisionMaker: number
  contactInfo: number
}

interface QualificationInsights {
  strengths: string[]
  gaps: string[]
  recommendations: string[]
  nextQuestions: string[]
  urgencyLevel: 'low' | 'medium' | 'high' | 'critical'
  conversionProbability: number
}

const DEFAULT_WEIGHTINGS: QualificationWeightings = {
  budget: 25,
  timeline: 20,
  location: 15,
  propertyType: 10,
  motivation: 15,
  decisionMaker: 10,
  contactInfo: 5
}

export function useLeadQualification(options: UseLeadQualificationOptions = {}) {
  const {
    currentLead,
    qualificationData,
    currentConversation,
    updateQualificationData,
    updateLeadProfile
  } = useVoiceAIStore()

  const [insights, setInsights] = useState<QualificationInsights>({
    strengths: [],
    gaps: [],
    recommendations: [],
    nextQuestions: [],
    urgencyLevel: 'low',
    conversionProbability: 0
  })

  const weightings = { ...DEFAULT_WEIGHTINGS, ...options.weightings }
  const minScore = options.minScore || 70

  // Calculate qualification score
  const calculateScore = useCallback((data: LeadQualificationData): number => {
    let totalScore = 0
    let totalWeight = 0

    // Budget scoring
    if (data.budget) {
      const budgetScore = Math.min(100, data.budget.confidence * 100)
      totalScore += (budgetScore * weightings.budget)
      totalWeight += weightings.budget
    }

    // Timeline scoring
    if (data.timeline) {
      let timelineScore = data.timeline.confidence * 100
      
      // Bonus for urgency
      switch (data.timeline.urgency) {
        case 'immediate':
          timelineScore = Math.min(100, timelineScore + 20)
          break
        case 'soon':
          timelineScore = Math.min(100, timelineScore + 10)
          break
        case 'exploring':
          timelineScore = Math.max(30, timelineScore - 10)
          break
      }
      
      totalScore += (timelineScore * weightings.timeline)
      totalWeight += weightings.timeline
    }

    // Location scoring
    if (data.location) {
      const locationScore = data.location.confidence * 100
      totalScore += (locationScore * weightings.location)
      totalWeight += weightings.location
    }

    // Property type scoring
    if (data.propertyType) {
      const propertyScore = data.propertyType.confidence * 100
      totalScore += (propertyScore * weightings.propertyType)
      totalWeight += weightings.propertyType
    }

    // Motivation scoring
    if (data.motivation) {
      const motivationScore = data.motivation.confidence * 100
      totalScore += (motivationScore * weightings.motivation)
      totalWeight += weightings.motivation
    }

    // Decision maker scoring
    if (data.decisionMaker) {
      let decisionScore = data.decisionMaker.confidence * 100
      if (data.decisionMaker.isDecisionMaker) {
        decisionScore = Math.min(100, decisionScore + 25)
      }
      totalScore += (decisionScore * weightings.decisionMaker)
      totalWeight += weightings.decisionMaker
    }

    // Contact info scoring
    if (data.contactInfo) {
      let contactScore = 0
      if (data.contactInfo.phone) contactScore += 40
      if (data.contactInfo.email) contactScore += 40
      if (data.contactInfo.preferredContact) contactScore += 20
      
      totalScore += (contactScore * weightings.contactInfo)
      totalWeight += weightings.contactInfo
    }

    return totalWeight > 0 ? Math.round(totalScore / totalWeight) : 0
  }, [weightings])

  // Update qualification from conversation turn
  const updateFromTurn = useCallback((turn: ConversationTurn) => {
    if (turn.speaker !== 'user') return

    const updates: Partial<LeadQualificationData> = {}
    const text = turn.text.toLowerCase()

    // Extract budget information
    const budgetMatches = turn.text.match(/\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)[k]?/g)
    if (budgetMatches) {
      const amounts = budgetMatches.map(match => {
        const value = parseFloat(match.replace(/[$,]/g, ''))
        return match.includes('k') ? value * 1000 : value
      }).filter(val => val > 10000) // Filter out non-price numbers

      if (amounts.length > 0) {
        updates.budget = {
          min: Math.min(...amounts),
          max: amounts.length > 1 ? Math.max(...amounts) : Math.min(...amounts) * 1.2,
          confidence: turn.confidence || 0.8
        }
      }
    }

    // Extract timeline information
    const timelineKeywords = {
      immediate: /immediately|asap|right away|urgent|now/i,
      soon: /soon|within (\d+)? ?(weeks?|months?)|next month/i,
      exploring: /looking around|just browsing|exploring|maybe|thinking about/i,
      future: /next year|eventually|someday|not sure when/i
    }

    for (const [urgency, pattern] of Object.entries(timelineKeywords)) {
      if (pattern.test(text)) {
        updates.timeline = {
          urgency: urgency as any,
          confidence: turn.confidence || 0.7
        }
        break
      }
    }

    // Extract location preferences
    const locationPattern = /(downtown|uptown|north|south|east|west|central|suburb|city|town|neighborhood|area|district)/gi
    const locationMatches = text.match(locationPattern)
    if (locationMatches) {
      updates.location = {
        preferred: [...new Set(locationMatches.map(l => l.toLowerCase()))],
        flexibility: text.includes('flexible') || text.includes('open to') ? 0.8 : 0.5,
        confidence: turn.confidence || 0.7
      }
    }

    // Extract property type information
    const propertyTypes = /(house|home|condo|apartment|townhouse|villa|mansion|studio|single family|multi-family)/gi
    const propertyMatches = text.match(propertyTypes)
    if (propertyMatches) {
      updates.propertyType = {
        type: propertyMatches[0].toLowerCase(),
        features: propertyMatches.map(p => p.toLowerCase()),
        confidence: turn.confidence || 0.7
      }
    }

    // Extract room requirements
    const roomPattern = /(\d+)\s*(bed|bedroom|bath|bathroom)/gi
    const roomMatches = text.match(roomPattern)
    if (roomMatches && updates.propertyType) {
      updates.propertyType.features = [
        ...updates.propertyType.features,
        ...roomMatches.map(r => r.toLowerCase())
      ]
    }

    // Extract motivation
    const motivationKeywords = {
      'growing family': /growing family|expecting|baby|kids|children/i,
      'downsizing': /downsize|smaller|empty nest|retire/i,
      'investment': /investment|rental|income property|portfolio/i,
      'relocation': /moving|relocating|new job|transfer/i,
      'first time buyer': /first time|first home|never bought/i,
      'upgrade': /bigger|larger|upgrade|more space/i
    }

    for (const [motivation, pattern] of Object.entries(motivationKeywords)) {
      if (pattern.test(text)) {
        updates.motivation = {
          primary: motivation,
          secondary: [],
          confidence: turn.confidence || 0.7
        }
        break
      }
    }

    // Extract decision maker information
    if (/decision|decide|my wife|my husband|partner|together|family decision/i.test(text)) {
      const isDecisionMaker = /i decide|my decision|up to me/i.test(text)
      updates.decisionMaker = {
        isDecisionMaker,
        influencers: isDecisionMaker ? [] : ['spouse/partner'],
        confidence: turn.confidence || 0.6
      }
    }

    // Extract contact information
    const phonePattern = /(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/g
    const emailPattern = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g
    
    const phoneMatch = turn.text.match(phonePattern)
    const emailMatch = turn.text.match(emailPattern)
    
    if (phoneMatch || emailMatch) {
      updates.contactInfo = {
        phone: phoneMatch?.[0],
        email: emailMatch?.[0],
        preferredContact: phoneMatch ? 'phone' : 'email'
      }
    }

    // Apply updates if any were found
    if (Object.keys(updates).length > 0) {
      updateQualificationData(updates)
    }
  }, [updateQualificationData])

  // Generate insights based on current qualification data
  const generateInsights = useCallback((): QualificationInsights => {
    if (!qualificationData) {
      return {
        strengths: [],
        gaps: ['No qualification data available'],
        recommendations: ['Start qualification process'],
        nextQuestions: ['What type of property are you looking for?'],
        urgencyLevel: 'low',
        conversionProbability: 0
      }
    }

    const strengths: string[] = []
    const gaps: string[] = []
    const recommendations: string[] = []
    const nextQuestions: string[] = []

    // Analyze budget
    if (qualificationData.budget) {
      if (qualificationData.budget.confidence > 0.7) {
        strengths.push('Budget clearly defined')
      } else {
        gaps.push('Budget needs clarification')
        nextQuestions.push('Can you share your budget range for this purchase?')
      }
    } else {
      gaps.push('No budget information')
      nextQuestions.push('What\'s your budget for your new home?')
    }

    // Analyze timeline
    if (qualificationData.timeline) {
      if (qualificationData.timeline.urgency === 'immediate') {
        strengths.push('Immediate buying intent')
        recommendations.push('Schedule property viewings ASAP')
      } else if (qualificationData.timeline.urgency === 'soon') {
        strengths.push('Near-term buying timeline')
      } else {
        gaps.push('Timeline is exploratory')
        nextQuestions.push('When are you hoping to make this move?')
      }
    } else {
      gaps.push('No timeline established')
      nextQuestions.push('What\'s your ideal timeline for purchasing?')
    }

    // Analyze location
    if (qualificationData.location && qualificationData.location.confidence > 0.6) {
      strengths.push('Location preferences defined')
    } else {
      gaps.push('Location preferences unclear')
      nextQuestions.push('Which areas are you most interested in?')
    }

    // Analyze decision making
    if (qualificationData.decisionMaker?.isDecisionMaker) {
      strengths.push('Can make buying decisions')
    } else if (qualificationData.decisionMaker) {
      gaps.push('Not the sole decision maker')
      recommendations.push('Include other decision makers in conversations')
    } else {
      gaps.push('Decision making process unknown')
      nextQuestions.push('Who else will be involved in this decision?')
    }

    // Analyze contact info
    if (qualificationData.contactInfo?.phone && qualificationData.contactInfo?.email) {
      strengths.push('Complete contact information')
    } else {
      gaps.push('Incomplete contact information')
      nextQuestions.push('What\'s the best way to follow up with you?')
    }

    // Determine urgency level
    let urgencyLevel: QualificationInsights['urgencyLevel'] = 'low'
    
    if (qualificationData.timeline?.urgency === 'immediate' && qualificationData.budget?.confidence > 0.7) {
      urgencyLevel = 'critical'
    } else if (qualificationData.timeline?.urgency === 'soon' || qualificationData.score > 80) {
      urgencyLevel = 'high'
    } else if (qualificationData.score > 50) {
      urgencyLevel = 'medium'
    }

    // Calculate conversion probability
    const score = qualificationData.score || 0
    let probability = score / 100

    // Adjust based on specific factors
    if (qualificationData.timeline?.urgency === 'immediate') probability += 0.2
    if (qualificationData.decisionMaker?.isDecisionMaker) probability += 0.1
    if (qualificationData.budget?.confidence > 0.8) probability += 0.1

    const conversionProbability = Math.min(1, Math.max(0, probability))

    return {
      strengths,
      gaps,
      recommendations,
      nextQuestions,
      urgencyLevel,
      conversionProbability
    }
  }, [qualificationData])

  // Update insights when qualification data changes
  useEffect(() => {
    const newInsights = generateInsights()
    setInsights(newInsights)
  }, [qualificationData, generateInsights])

  // Auto-update from conversation turns
  useEffect(() => {
    if (!options.enableRealTimeUpdates || !currentConversation) return

    const lastTurn = currentConversation.turns[currentConversation.turns.length - 1]
    if (lastTurn && lastTurn.speaker === 'user') {
      updateFromTurn(lastTurn)
    }
  }, [currentConversation, options.enableRealTimeUpdates, updateFromTurn])

  // Manual qualification update
  const updateQualification = useCallback((updates: Partial<LeadQualificationData>) => {
    const currentData = qualificationData || {
      score: 0,
      budget: { confidence: 0 },
      timeline: { confidence: 0 },
      location: { confidence: 0 },
      propertyType: { confidence: 0 },
      motivation: { confidence: 0 },
      decisionMaker: { confidence: 0 }
    }

    const updatedData = { ...currentData, ...updates }
    updatedData.score = calculateScore(updatedData)

    updateQualificationData(updatedData)
  }, [qualificationData, calculateScore, updateQualificationData])

  // Create property inquiry from qualification data
  const createPropertyInquiry = useCallback((): PropertyInquiry | null => {
    if (!qualificationData) return null

    const inquiry: PropertyInquiry = {
      location: qualificationData.location?.preferred?.[0] || '',
      propertyType: qualificationData.propertyType?.type || '',
      features: qualificationData.propertyType?.features || [],
      urgency: qualificationData.timeline?.urgency || 'exploring'
    }

    if (qualificationData.budget) {
      inquiry.priceRange = {
        min: qualificationData.budget.min || 0,
        max: qualificationData.budget.max || 0
      }
    }

    // Extract room requirements
    const roomFeatures = inquiry.features.filter(f => f.includes('bed') || f.includes('bath'))
    roomFeatures.forEach(feature => {
      const match = feature.match(/(\d+)\s*(bed|bath)/i)
      if (match) {
        const count = parseInt(match[1])
        if (match[2].toLowerCase().includes('bed')) {
          inquiry.bedrooms = count
        } else {
          inquiry.bathrooms = count
        }
      }
    })

    return inquiry
  }, [qualificationData])

  // Get next qualification questions
  const getNextQuestions = useCallback((): string[] => {
    return insights.nextQuestions.slice(0, 3) // Return top 3 questions
  }, [insights.nextQuestions])

  // Check if lead is qualified
  const isQualified = useCallback((): boolean => {
    return (qualificationData?.score || 0) >= minScore
  }, [qualificationData, minScore])

  // Get qualification summary
  const getSummary = useCallback((): string => {
    if (!qualificationData) return 'No qualification data'

    const score = qualificationData.score
    const timeline = qualificationData.timeline?.urgency || 'unknown'
    const budget = qualificationData.budget ? 'defined' : 'undefined'
    
    return `Score: ${score}/100, Timeline: ${timeline}, Budget: ${budget}`
  }, [qualificationData])

  return {
    // Current data
    data: qualificationData,
    lead: currentLead,
    insights,
    
    // Scores and status
    score: qualificationData?.score || 0,
    isQualified: isQualified(),
    urgencyLevel: insights.urgencyLevel,
    conversionProbability: insights.conversionProbability,
    
    // Actions
    update: updateQualification,
    updateFromTurn,
    
    // Utilities
    createPropertyInquiry,
    getNextQuestions,
    getSummary,
    
    // Analysis
    strengths: insights.strengths,
    gaps: insights.gaps,
    recommendations: insights.recommendations,
    nextQuestions: insights.nextQuestions
  }
}