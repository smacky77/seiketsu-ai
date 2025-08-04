// Conversation utility functions for voice AI

import type {
  ConversationContext,
  ConversationTurn,
  IntentRecognition,
  LeadQualificationData,
  PropertyInquiry
} from '../types'

// Conversation flow analysis
export interface ConversationFlow {
  phase: 'opening' | 'discovery' | 'qualification' | 'presentation' | 'objection_handling' | 'closing'
  transitions: Array<{
    from: string
    to: string
    timestamp: number
    trigger: string
  }>
  stuckPoints: Array<{
    phase: string
    duration: number
    reason: string
  }>
  efficiency: number // 0-1 scale
}

// Conversation patterns
export interface ConversationPattern {
  name: string
  pattern: RegExp | ((turns: ConversationTurn[]) => boolean)
  significance: 'high' | 'medium' | 'low'
  action?: string
}

// Real estate conversation patterns
export const REAL_ESTATE_PATTERNS: ConversationPattern[] = [
  {
    name: 'buying_signal',
    pattern: /ready to buy|let's do it|sounds good|when can we|i'm interested|make an offer/i,
    significance: 'high',
    action: 'move_to_closing'
  },
  {
    name: 'price_objection',
    pattern: /too expensive|can't afford|over budget|too much/i,
    significance: 'high',
    action: 'handle_price_objection'
  },
  {
    name: 'timeline_urgency',
    pattern: /asap|immediately|urgent|soon|deadline|time sensitive/i,
    significance: 'high',
    action: 'prioritize_urgency'
  },
  {
    name: 'location_flexibility',
    pattern: /anywhere|flexible|open to|willing to consider|doesn't matter/i,
    significance: 'medium',
    action: 'expand_search'
  },
  {
    name: 'family_motivation',
    pattern: /family|kids|children|baby|growing|school district/i,
    significance: 'medium',
    action: 'focus_family_features'
  },
  {
    name: 'investment_focus',
    pattern: /investment|rental|income|roi|cash flow|appreciation/i,
    significance: 'medium',
    action: 'shift_to_investment'
  },
  {
    name: 'hesitation',
    pattern: /not sure|maybe|think about it|need time|hesitant/i,
    significance: 'medium',
    action: 'address_concerns'
  },
  {
    name: 'competitor_mention',
    pattern: /other agent|another realtor|someone else|comparing/i,
    significance: 'high',
    action: 'differentiate_value'
  }
]

// Analyze conversation flow
export function analyzeConversationFlow(conversation: ConversationContext): ConversationFlow {
  const turns = conversation.turns
  const phases = detectPhases(turns)
  
  // Calculate transitions
  const transitions = []
  for (let i = 1; i < phases.length; i++) {
    transitions.push({
      from: phases[i - 1].phase,
      to: phases[i].phase,
      timestamp: phases[i].timestamp,
      trigger: phases[i].trigger
    })
  }
  
  // Detect stuck points (phases that last too long)
  const stuckPoints = []
  for (let i = 0; i < phases.length; i++) {
    const duration = i < phases.length - 1 
      ? phases[i + 1].timestamp - phases[i].timestamp
      : Date.now() - phases[i].timestamp
    
    const expectedDuration = getExpectedPhaseDuration(phases[i].phase)
    if (duration > expectedDuration * 2) {
      stuckPoints.push({
        phase: phases[i].phase,
        duration,
        reason: diagnosePhaseProblem(phases[i].phase, turns.slice(phases[i].turnIndex))
      })
    }
  }
  
  // Calculate efficiency (ideal vs actual flow)
  const idealPhases = ['opening', 'discovery', 'qualification', 'presentation', 'closing']
  const actualPhases = phases.map(p => p.phase)
  const efficiency = calculateFlowEfficiency(idealPhases, actualPhases)
  
  return {
    phase: phases[phases.length - 1]?.phase || 'opening',
    transitions,
    stuckPoints,
    efficiency
  }
}

// Detect conversation phases
function detectPhases(turns: ConversationTurn[]): Array<{
  phase: ConversationFlow['phase']
  timestamp: number
  turnIndex: number
  trigger: string
}> {
  const phases: Array<{
    phase: ConversationFlow['phase']
    timestamp: number
    turnIndex: number
    trigger: string
  }> = []
  
  let currentPhase: ConversationFlow['phase'] = 'opening'
  phases.push({
    phase: currentPhase,
    timestamp: turns[0]?.timestamp || Date.now(),
    turnIndex: 0,
    trigger: 'conversation_start'
  })
  
  for (let i = 0; i < turns.length; i++) {
    const turn = turns[i]
    const text = turn.text.toLowerCase()
    
    let newPhase: ConversationFlow['phase'] | null = null
    let trigger = ''
    
    // Phase detection rules
    if (currentPhase === 'opening' && (
      /what are you looking for|tell me about|interested in|need|want/i.test(text)
    )) {
      newPhase = 'discovery'
      trigger = 'started_discovery'
    } else if ((currentPhase === 'discovery' || currentPhase === 'opening') && (
      /budget|price|afford|timeline|when|where|location/i.test(text)
    )) {
      newPhase = 'qualification'
      trigger = 'started_qualification'
    } else if (currentPhase === 'qualification' && (
      /show me|available|listings|properties|options/i.test(text)
    )) {
      newPhase = 'presentation'
      trigger = 'requested_properties'
    } else if (/but|however|concern|worried|not sure|problem/i.test(text)) {
      newPhase = 'objection_handling'
      trigger = 'objection_raised'
    } else if (/ready|interested|schedule|appointment|next step|let's do it/i.test(text)) {
      newPhase = 'closing'
      trigger = 'buying_signal'
    }
    
    if (newPhase && newPhase !== currentPhase) {
      phases.push({
        phase: newPhase,
        timestamp: turn.timestamp,
        turnIndex: i,
        trigger
      })
      currentPhase = newPhase
    }
  }
  
  return phases
}

// Get expected duration for conversation phases (in milliseconds)
function getExpectedPhaseDuration(phase: ConversationFlow['phase']): number {
  const durations = {
    opening: 2 * 60 * 1000, // 2 minutes
    discovery: 5 * 60 * 1000, // 5 minutes
    qualification: 8 * 60 * 1000, // 8 minutes
    presentation: 10 * 60 * 1000, // 10 minutes
    objection_handling: 5 * 60 * 1000, // 5 minutes
    closing: 3 * 60 * 1000 // 3 minutes
  }
  
  return durations[phase] || 5 * 60 * 1000
}

// Diagnose why a phase might be stuck
function diagnosePhaseProblem(phase: ConversationFlow['phase'], turns: ConversationTurn[]): string {
  const recentText = turns.slice(-5).map(t => t.text.toLowerCase()).join(' ')
  
  switch (phase) {
    case 'opening':
      return 'Customer not responding to opening questions'
    
    case 'discovery':
      if (recentText.includes('not sure') || recentText.includes('don\'t know')) {
        return 'Customer unclear about needs'
      }
      return 'Need to ask more discovery questions'
    
    case 'qualification':
      if (recentText.includes('budget') && recentText.includes('not')) {
        return 'Budget resistance'
      }
      if (recentText.includes('timeline') && recentText.includes('flexible')) {
        return 'No urgency established'
      }
      return 'Qualification incomplete'
    
    case 'presentation':
      if (recentText.includes('not interested') || recentText.includes('wrong')) {
        return 'Properties not matching criteria'
      }
      return 'Need better property selection'
    
    case 'objection_handling':
      return 'Objections not fully addressed'
    
    case 'closing':
      return 'Customer not ready to commit'
    
    default:
      return 'Unknown issue'
  }
}

// Calculate flow efficiency
function calculateFlowEfficiency(ideal: string[], actual: string[]): number {
  // Simple efficiency calculation based on phase progression
  let score = 0
  let expectedIndex = 0
  
  for (const phase of actual) {
    const idealIndex = ideal.indexOf(phase)
    if (idealIndex >= expectedIndex) {
      score += 1
      expectedIndex = idealIndex + 1
    } else {
      score += 0.5 // Partial credit for revisiting earlier phases
    }
  }
  
  return Math.min(1, score / ideal.length)
}

// Detect conversation patterns
export function detectPatterns(turns: ConversationTurn[]): Array<{
  pattern: ConversationPattern
  matches: Array<{
    turn: ConversationTurn
    confidence: number
  }>
}> {
  const results: Array<{
    pattern: ConversationPattern
    matches: Array<{
      turn: ConversationTurn
      confidence: number
    }>
  }> = []
  
  for (const pattern of REAL_ESTATE_PATTERNS) {
    const matches: Array<{
      turn: ConversationTurn
      confidence: number
    }> = []
    
    if (pattern.pattern instanceof RegExp) {
      // Regex pattern matching
      for (const turn of turns) {
        if (pattern.pattern.test(turn.text)) {
          matches.push({
            turn,
            confidence: turn.confidence || 0.8
          })
        }
      }
    } else if (typeof pattern.pattern === 'function') {
      // Function-based pattern matching
      if (pattern.pattern(turns)) {
        matches.push({
          turn: turns[turns.length - 1], // Use last turn as representative
          confidence: 0.7
        })
      }
    }
    
    if (matches.length > 0) {
      results.push({ pattern, matches })
    }
  }
  
  return results.sort((a, b) => {
    // Sort by significance and number of matches
    const significanceWeight = { high: 3, medium: 2, low: 1 }
    const scoreA = significanceWeight[a.pattern.significance] * a.matches.length
    const scoreB = significanceWeight[b.pattern.significance] * b.matches.length
    return scoreB - scoreA
  })
}

// Generate conversation summary
export function generateConversationSummary(conversation: ConversationContext): {
  overview: string
  keyPoints: string[]
  concerns: string[]
  nextSteps: string[]
  qualificationLevel: 'low' | 'medium' | 'high'
} {
  const turns = conversation.turns
  const userTurns = turns.filter(t => t.speaker === 'user')
  const allText = turns.map(t => t.text).join(' ').toLowerCase()
  
  // Generate overview
  const duration = conversation.endTime 
    ? Math.round((conversation.endTime - conversation.startTime) / 60000)
    : Math.round((Date.now() - conversation.startTime) / 60000)
  
  const overview = `${duration}-minute conversation with ${userTurns.length} user responses. ` +
    `Discussed ${extractTopics(allText).join(', ')}.`
  
  // Extract key points
  const keyPoints = extractKeyPoints(turns)
  
  // Identify concerns/objections
  const concerns = extractConcerns(userTurns)
  
  // Determine next steps
  const nextSteps = determineNextSteps(turns, conversation.qualificationData)
  
  // Assess qualification level
  const qualificationLevel = assessQualificationLevel(conversation.qualificationData)
  
  return {
    overview,
    keyPoints,
    concerns,
    nextSteps,
    qualificationLevel
  }
}

// Extract topics discussed in conversation
function extractTopics(text: string): string[] {
  const topics = []
  
  const topicKeywords = {
    budget: /budget|price|cost|afford|financing|mortgage/i,
    location: /location|area|neighborhood|address|where/i,
    timeline: /when|timeline|soon|urgent|schedule/i,
    features: /bedroom|bathroom|garage|yard|space|size/i,
    family: /family|kids|children|school|education/i,
    investment: /investment|rental|income|roi/i
  }
  
  for (const [topic, pattern] of Object.entries(topicKeywords)) {
    if (pattern.test(text)) {
      topics.push(topic)
    }
  }
  
  return topics
}

// Extract key points from conversation
function extractKeyPoints(turns: ConversationTurn[]): string[] {
  const points: string[] = []
  
  for (const turn of turns) {
    const text = turn.text.toLowerCase()
    
    // Budget mentions
    const budgetMatch = turn.text.match(/\$[\d,]+/g)
    if (budgetMatch) {
      points.push(`Budget discussed: ${budgetMatch.join(', ')}`)
    }
    
    // Timeline mentions
    if (/immediately|asap|urgent|soon/i.test(text)) {
      points.push('Urgent timeline indicated')
    }
    
    // Location specifics
    const locationMatch = text.match(/(downtown|uptown|north|south|east|west|\w+\s+area)/gi)
    if (locationMatch) {
      points.push(`Interested in: ${locationMatch.join(', ')}`)
    }
    
    // Property type preferences
    const propertyMatch = text.match(/(house|condo|apartment|townhouse|single family)/gi)
    if (propertyMatch) {
      points.push(`Property type: ${propertyMatch.join(', ')}`)
    }
  }
  
  return [...new Set(points)].slice(0, 5) // Remove duplicates, limit to 5
}

// Extract concerns and objections
function extractConcerns(userTurns: ConversationTurn[]): string[] {
  const concerns: string[] = []
  
  const concernPatterns = {
    price: /too expensive|can't afford|over budget|too much/i,
    location: /too far|wrong area|don't like the location/i,
    timing: /not ready|too soon|need more time/i,
    features: /too small|too big|not what I need/i,
    market: /market conditions|prices falling|wait for better time/i,
    process: /complicated|too much paperwork|stressful/i
  }
  
  for (const turn of userTurns) {
    for (const [concern, pattern] of Object.entries(concernPatterns)) {
      if (pattern.test(turn.text)) {
        concerns.push(concern.charAt(0).toUpperCase() + concern.slice(1) + ' concerns')
        break // One concern per turn
      }
    }
  }
  
  return [...new Set(concerns)]
}

// Determine next steps based on conversation
function determineNextSteps(
  turns: ConversationTurn[], 
  qualification?: LeadQualificationData
): string[] {
  const steps: string[] = []
  const recentText = turns.slice(-3).map(t => t.text.toLowerCase()).join(' ')
  
  // Based on qualification score
  if (qualification) {
    if (qualification.score > 80) {
      steps.push('Schedule property viewing')
      steps.push('Prepare listing presentation')
    } else if (qualification.score > 60) {
      steps.push('Complete qualification process')
      steps.push('Send targeted property recommendations')
    } else {
      steps.push('Continue needs assessment')
      steps.push('Build rapport and trust')
    }
  } else {
    steps.push('Begin qualification process')
  }
  
  // Based on recent conversation
  if (recentText.includes('schedule') || recentText.includes('appointment')) {
    steps.push('Confirm appointment details')
  }
  
  if (recentText.includes('call back') || recentText.includes('follow up')) {
    steps.push('Schedule follow-up call')
  }
  
  if (recentText.includes('information') || recentText.includes('details')) {
    steps.push('Send requested information')
  }
  
  // Based on timeline urgency
  if (qualification?.timeline?.urgency === 'immediate') {
    steps.unshift('Immediate follow-up required') // Add to beginning
  }
  
  return steps.slice(0, 4) // Limit to 4 steps
}

// Assess overall qualification level
function assessQualificationLevel(qualification?: LeadQualificationData): 'low' | 'medium' | 'high' {
  if (!qualification) return 'low'
  
  const score = qualification.score
  
  if (score >= 75) return 'high'
  if (score >= 50) return 'medium'
  return 'low'
}

// Create property inquiry from conversation
export function createPropertyInquiryFromConversation(
  conversation: ConversationContext
): PropertyInquiry {
  const allText = conversation.turns.map(t => t.text).join(' ')
  const qualification = conversation.qualificationData
  
  const inquiry: PropertyInquiry = {
    location: '',
    propertyType: '',
    features: [],
    urgency: 'exploring'
  }
  
  // Extract from qualification data first
  if (qualification) {
    if (qualification.location?.preferred) {
      inquiry.location = qualification.location.preferred[0]
    }
    
    if (qualification.propertyType?.type) {
      inquiry.propertyType = qualification.propertyType.type
    }
    
    if (qualification.propertyType?.features) {
      inquiry.features = qualification.propertyType.features
    }
    
    if (qualification.budget) {
      inquiry.priceRange = {
        min: qualification.budget.min || 0,
        max: qualification.budget.max || 0
      }
    }
    
    if (qualification.timeline?.urgency) {
      inquiry.urgency = qualification.timeline.urgency
    }
  }
  
  // Extract from conversation text as fallback
  if (!inquiry.location) {
    const locationMatch = allText.match(/(downtown|uptown|north|south|east|west|\w+\s+area)/gi)
    if (locationMatch) {
      inquiry.location = locationMatch[0]
    }
  }
  
  if (!inquiry.propertyType) {
    const typeMatch = allText.match(/(house|home|condo|apartment|townhouse)/gi)
    if (typeMatch) {
      inquiry.propertyType = typeMatch[0].toLowerCase()
    }
  }
  
  // Extract room requirements
  const roomMatches = allText.match(/(\d+)\s+(bedroom|bathroom|bed|bath)/gi)
  if (roomMatches) {
    roomMatches.forEach(match => {
      const [count, type] = match.split(/\s+/)
      if (type.toLowerCase().includes('bed')) {
        inquiry.bedrooms = parseInt(count)
      } else if (type.toLowerCase().includes('bath')) {
        inquiry.bathrooms = parseInt(count)
      }
    })
  }
  
  return inquiry
}

// Calculate conversation quality score
export function calculateConversationQuality(conversation: ConversationContext): {
  overall: number
  flow: number
  engagement: number
  qualification: number
  resolution: number
} {
  const turns = conversation.turns
  
  // Flow quality (smooth progression through phases)
  const flow = analyzeConversationFlow(conversation)
  const flowScore = flow.efficiency * 100
  
  // Engagement quality (balanced participation, appropriate responses)
  const userTurns = turns.filter(t => t.speaker === 'user').length
  const agentTurns = turns.filter(t => t.speaker === 'agent').length
  const balance = userTurns > 0 && agentTurns > 0 
    ? Math.min(userTurns, agentTurns) / Math.max(userTurns, agentTurns)
    : 0
  const engagementScore = balance * 100
  
  // Qualification quality (completeness of information gathered)
  const qualificationScore = conversation.qualificationData?.score || 0
  
  // Resolution quality (clear next steps, addressed concerns)
  const hasNextSteps = conversation.analytics?.nextSteps.length > 0
  const addressedConcerns = conversation.analytics?.objections.length === 0
  const resolutionScore = (hasNextSteps ? 50 : 0) + (addressedConcerns ? 50 : 0)
  
  // Overall quality (weighted average)
  const overall = (
    flowScore * 0.25 +
    engagementScore * 0.25 +
    qualificationScore * 0.25 +
    resolutionScore * 0.25
  )
  
  return {
    overall: Math.round(overall),
    flow: Math.round(flowScore),
    engagement: Math.round(engagementScore),
    qualification: Math.round(qualificationScore),
    resolution: Math.round(resolutionScore)
  }
}