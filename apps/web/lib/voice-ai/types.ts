// Voice AI Core Types and Interfaces

export interface VoiceAIConfig {
  elevenlabs: {
    apiKey: string
    voiceId: string
    modelId?: string
    stability?: number
    similarityBoost?: number
    style?: number
  }
  openai: {
    apiKey: string
    model?: string
    temperature?: number
    maxTokens?: number
  }
  realtime: {
    maxLatency: number // ms
    audioSampleRate: number
    channels: number
    bitDepth: number
  }
  features: {
    wakeWordDetection: boolean
    voiceBiometrics: boolean
    emotionDetection: boolean
    backgroundNoiseSupression: boolean
  }
}

export interface AudioStreamConfig {
  sampleRate: number
  channels: number
  bitDepth: number
  bufferSize: number
  echoCancellation: boolean
  noiseSuppression: boolean
  autoGainControl: boolean
}

export interface VoiceActivityDetection {
  isActive: boolean
  confidence: number
  energy: number
  timestamp: number
}

export interface SpeechToTextResult {
  text: string
  confidence: number
  isFinal: boolean
  alternatives?: Array<{
    text: string
    confidence: number
  }>
  timestamp: number
  speaker?: string
}

export interface TextToSpeechRequest {
  text: string
  voiceId?: string
  modelId?: string
  voiceSettings?: {
    stability: number
    similarityBoost: number
    style?: number
  }
  outputFormat?: 'mp3' | 'wav' | 'pcm'
}

export interface ConversationTurn {
  id: string
  timestamp: number
  speaker: 'user' | 'agent'
  text: string
  audioUrl?: string
  confidence?: number
  intent?: string
  entities?: Record<string, any>
  sentiment?: {
    polarity: number // -1 to 1
    magnitude: number // 0 to 1
    label: 'positive' | 'negative' | 'neutral'
  }
  duration?: number
}

export interface ConversationContext {
  id: string
  leadId?: string
  agentId: string
  startTime: number
  endTime?: number
  turns: ConversationTurn[]
  metadata: {
    platform: string
    channel: string
    campaignId?: string
    source?: string
  }
  qualificationData?: LeadQualificationData
  analytics?: ConversationAnalytics
}

export interface IntentRecognition {
  intent: string
  confidence: number
  entities: Record<string, {
    value: string
    confidence: number
    start: number
    end: number
  }>
  domain?: string
}

export interface LeadQualificationData {
  score: number // 0-100
  budget?: {
    min?: number
    max?: number
    confidence: number
  }
  timeline?: {
    urgency: 'immediate' | 'soon' | 'exploring' | 'future'
    specificDate?: string
    confidence: number
  }
  location?: {
    preferred: string[]
    flexibility: number
    confidence: number
  }
  propertyType?: {
    type: string
    features: string[]
    confidence: number
  }
  motivation?: {
    primary: string
    secondary: string[]
    confidence: number
  }
  decisionMaker?: {
    isDecisionMaker: boolean
    influencers: string[]
    confidence: number
  }
  contactInfo?: {
    phone?: string
    email?: string
    preferredContact: string
    bestTime?: string
  }
}

export interface ConversationAnalytics {
  duration: number
  talkTimeRatio: number // agent vs user
  interruptionCount: number
  sentimentTrend: Array<{
    timestamp: number
    sentiment: number
  }>
  engagementScore: number
  keyTopics: string[]
  objections: string[]
  nextSteps: string[]
  followUpRequired: boolean
}

export interface VoiceAgent {
  id: string
  name: string
  voiceId: string
  personality: {
    tone: 'professional' | 'friendly' | 'casual' | 'authoritative'
    pace: 'slow' | 'normal' | 'fast'
    enthusiasm: number // 0-1
  }
  expertise: string[]
  systemPrompt: string
  conversationRules: {
    maxTurnLength: number
    allowInterruptions: boolean
    escalationTriggers: string[]
  }
  isActive: boolean
  metrics: {
    conversationsHandled: number
    averageQualificationScore: number
    conversionRate: number
    averageCallDuration: number
  }
}

export interface VoiceWebRTCConnection {
  localStream?: MediaStream
  remoteStream?: MediaStream
  peerConnection?: RTCPeerConnection
  dataChannel?: RTCDataChannel
  connectionState: RTCPeerConnectionState
  iceConnectionState: RTCIceConnectionState
  signalingState: RTCSignalingState
}

export interface AudioVisualization {
  frequencyData: Uint8Array
  timeDomainData: Uint8Array
  volume: number
  pitch?: number
  formants?: number[]
}

export interface VoiceCommand {
  trigger: string | RegExp
  action: string
  parameters?: Record<string, any>
  confirmationRequired?: boolean
  description: string
}

export interface VoiceBiometrics {
  voicePrint: Float32Array
  confidence: number
  userId?: string
  enrollmentStatus: 'pending' | 'enrolled' | 'failed'
  lastUpdated: number
}

export interface EmotionDetection {
  emotion: 'happy' | 'sad' | 'angry' | 'neutral' | 'excited' | 'frustrated' | 'confused'
  confidence: number
  arousal: number // 0-1
  valence: number // -1 to 1
  timestamp: number
}

export interface WakeWordConfig {
  keyword: string
  sensitivity: number // 0-1
  enabled: boolean
  customModel?: string
}

export interface VoiceAIError {
  code: string
  message: string
  details?: any
  recoverable: boolean
  timestamp: number
}

export interface VoiceAIMetrics {
  latency: {
    speechToText: number
    processing: number
    textToSpeech: number
    total: number
  }
  quality: {
    audioQuality: number // 0-1
    transcriptionAccuracy: number // 0-1
    responseRelevance: number // 0-1
  }
  engagement: {
    userSpeakingTime: number
    agentSpeakingTime: number
    silenceTime: number
    interruptionCount: number
  }
  performance: {
    cpuUsage: number
    memoryUsage: number
    networkLatency: number
    errorRate: number
  }
}

export type VoiceAIEvent = 
  | { type: 'initialized'; data: any }
  | { type: 'listening_started'; data: any }
  | { type: 'listening_stopped'; data: any }
  | { type: 'recording_started'; data: any }
  | { type: 'recording_stopped'; data: any }
  | { type: 'speech_synthesized'; data: any }
  | { type: 'text_processed'; data: any }
  | { type: 'audio_processed'; data: any }
  | { type: 'conversation_started'; data: any }
  | { type: 'conversation_ended'; data: any }
  | { type: 'connection_state_changed'; data: any }
  | { type: 'ice_candidate'; data: any }
  | { type: 'remote_stream'; data: any }
  | { type: 'data_channel_open'; data: any }
  | { type: 'data_channel_message'; data: any }
  | { type: 'call_started'; data: any }
  | { type: 'call_ended'; data: any }
  | { type: 'microphone_muted'; data: any }
  | { type: 'microphone_volume_changed'; data: any }
  | { type: 'voice_activity_start'; data: VoiceActivityDetection }
  | { type: 'voice_activity_end'; data: VoiceActivityDetection }
  | { type: 'speech_recognized'; data: SpeechToTextResult }
  | { type: 'intent_detected'; data: IntentRecognition }
  | { type: 'emotion_detected'; data: EmotionDetection }
  | { type: 'conversation_turn'; data: ConversationTurn }
  | { type: 'qualification_updated'; data: LeadQualificationData }
  | { type: 'wake_word_detected'; data: { keyword: string; confidence: number } }
  | { type: 'error'; data: VoiceAIError }
  | { type: 'metrics_updated'; data: VoiceAIMetrics }

export interface VoiceAIEventListener {
  (event: VoiceAIEvent): void
}

// Real Estate Specific Types
export interface PropertyInquiry {
  propertyId?: string
  location: string
  priceRange?: {
    min: number
    max: number
  }
  propertyType: string
  bedrooms?: number
  bathrooms?: number
  features: string[]
  urgency: 'immediate' | 'within_month' | 'within_quarter' | 'exploring'
}

export interface LeadProfile {
  id: string
  firstName?: string
  lastName?: string
  email?: string
  phone?: string
  location?: string
  budgetRange?: {
    min: number
    max: number
  }
  timeline?: string
  propertyPreferences?: PropertyInquiry
  communicationPreferences?: {
    preferredTime: string
    preferredMethod: 'phone' | 'email' | 'text'
    frequency: 'daily' | 'weekly' | 'monthly'
  }
  qualificationScore: number
  source: string
  status: 'new' | 'qualified' | 'nurturing' | 'hot' | 'closed' | 'lost'
  assignedAgent?: string
  notes: string
  lastContact?: number
  nextFollowUp?: number
}

export interface CallDisposition {
  outcome: 'appointment_set' | 'callback_requested' | 'not_interested' | 'no_answer' | 'wrong_number' | 'follow_up_needed'
  notes: string
  nextAction?: string
  scheduledCallback?: number
  appointmentDetails?: {
    date: string
    time: string
    location: string
    type: 'showing' | 'consultation' | 'listing_appointment'
  }
}

export interface VoiceAIState {
  isInitialized: boolean
  isConnected: boolean
  currentConversation?: ConversationContext
  activeAgent?: VoiceAgent
  isListening: boolean
  isSpeaking: boolean
  isProcessing: boolean
  currentLead?: LeadProfile
  qualificationData?: LeadQualificationData
  metrics: VoiceAIMetrics
  error?: VoiceAIError
  connectionState: 'disconnected' | 'connecting' | 'connected' | 'error'
  audioState: {
    inputLevel: number
    outputLevel: number
    isInputMuted: boolean
    isOutputMuted: boolean
  }
}