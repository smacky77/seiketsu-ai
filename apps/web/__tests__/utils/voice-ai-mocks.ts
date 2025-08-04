import { jest } from '@jest/globals'
import type {
  VoiceAIConfig,
  ConversationContext,
  VoiceAgent,
  VoiceAIMetrics,
  VoiceAIState,
  SpeechToTextResult,
  TextToSpeechRequest,
  LeadQualificationData,
} from '@/lib/voice-ai/types'

// Mock Audio Processing
export const mockAudioProcessor = {
  startRecording: jest.fn().mockResolvedValue(undefined),
  stopRecording: jest.fn().mockResolvedValue(new Blob()),
  processAudioChunk: jest.fn().mockReturnValue(new Float32Array(1024)),
  getVolumeLevel: jest.fn().mockReturnValue(0.5),
  detectVoiceActivity: jest.fn().mockReturnValue({
    isActive: true,
    confidence: 0.9,
    energy: 0.7,
    timestamp: Date.now(),
  }),
  applyNoiseReduction: jest.fn(),
  normalizeAudio: jest.fn(),
}

// Mock Speech-to-Text Service
export const mockSpeechToTextService = {
  initialize: jest.fn().mockResolvedValue(undefined),
  startTranscription: jest.fn().mockResolvedValue(undefined),
  stopTranscription: jest.fn().mockResolvedValue(undefined),
  processAudio: jest.fn().mockResolvedValue({
    text: 'Hello, I am looking for a house',
    confidence: 0.95,
    isFinal: true,
    timestamp: Date.now(),
  } as SpeechToTextResult),
  getTranscriptionStream: jest.fn().mockReturnValue({
    subscribe: jest.fn(),
    unsubscribe: jest.fn(),
  }),
}

// Mock Text-to-Speech Service
export const mockTextToSpeechService = {
  initialize: jest.fn().mockResolvedValue(undefined),
  synthesize: jest.fn().mockResolvedValue(new ArrayBuffer(1024)),
  getVoices: jest.fn().mockResolvedValue([
    { id: 'voice-1', name: 'Sarah', language: 'en-US' },
    { id: 'voice-2', name: 'David', language: 'en-US' },
  ]),
  playAudio: jest.fn().mockResolvedValue(undefined),
  stopAudio: jest.fn(),
  setVoiceSettings: jest.fn(),
}

// Mock WebRTC Service
export const mockWebRTCService = {
  initialize: jest.fn().mockResolvedValue(undefined),
  createPeerConnection: jest.fn().mockReturnValue({
    addTrack: jest.fn(),
    createOffer: jest.fn().mockResolvedValue({}),
    createAnswer: jest.fn().mockResolvedValue({}),
    setLocalDescription: jest.fn().mockResolvedValue(undefined),
    setRemoteDescription: jest.fn().mockResolvedValue(undefined),
    close: jest.fn(),
    addEventListener: jest.fn(),
  }),
  getUserMedia: jest.fn().mockResolvedValue({
    getAudioTracks: () => [{ id: 'audio-1', stop: jest.fn() }],
    getTracks: () => [{ id: 'audio-1', stop: jest.fn() }],
  }),
  closeConnection: jest.fn(),
  getConnectionStats: jest.fn().mockResolvedValue({
    bytesReceived: 1024,
    bytesSent: 512,
    packetsLost: 0,
    jitter: 10,
    roundTripTime: 50,
  }),
}

// Mock Conversation Engine
export const mockConversationEngine = {
  initialize: jest.fn().mockResolvedValue(undefined),
  processMessage: jest.fn().mockResolvedValue({
    response: 'Thank you for your interest. What type of property are you looking for?',
    intent: 'property_inquiry',
    entities: { property_type: 'house' },
    confidence: 0.9,
    shouldQualify: true,
  }),
  getConversationHistory: jest.fn().mockReturnValue([]),
  analyzeIntent: jest.fn().mockReturnValue({
    intent: 'property_inquiry',
    confidence: 0.9,
    entities: {},
  }),
  generateResponse: jest.fn().mockResolvedValue('How can I help you today?'),
  updateContext: jest.fn(),
  getQualificationData: jest.fn().mockReturnValue({
    score: 75,
    budget: { min: 200000, max: 400000, confidence: 0.8 },
    timeline: { urgency: 'soon', confidence: 0.9 },
  }),
}

// Mock AI Model Integration
export const mockAIModelIntegration = {
  initialize: jest.fn().mockResolvedValue(undefined),
  generateCompletion: jest.fn().mockResolvedValue({
    text: 'I understand you\'re looking for a property. Let me help you find the perfect match.',
    usage: { promptTokens: 50, completionTokens: 25, totalTokens: 75 },
    finishReason: 'stop',
  }),
  analyzeConversation: jest.fn().mockResolvedValue({
    sentiment: { polarity: 0.2, magnitude: 0.8, label: 'positive' },
    topics: ['real estate', 'property search'],
    intent: 'property_inquiry',
    qualificationScore: 80,
  }),
  extractEntities: jest.fn().mockResolvedValue({
    location: 'downtown',
    propertyType: 'apartment',
    budget: '300000',
  }),
  classifyIntent: jest.fn().mockResolvedValue({
    intent: 'property_inquiry',
    confidence: 0.95,
    category: 'lead_generation',
  }),
}

// Mock Voice AI Provider
export const mockVoiceAIProvider = {
  state: {
    isInitialized: true,
    isConnected: true,
    isListening: false,
    isSpeaking: false,
    isProcessing: false,
    connectionState: 'connected' as const,
    audioState: {
      inputLevel: 0,
      outputLevel: 0,
      isInputMuted: false,
      isOutputMuted: false,
    },
    metrics: {
      latency: { total: 150 },
      quality: { audioQuality: 0.95 },
    },
  } as VoiceAIState,
  
  actions: {
    initialize: jest.fn().mockResolvedValue(undefined),
    startListening: jest.fn().mockResolvedValue(undefined),
    stopListening: jest.fn().mockResolvedValue(undefined),
    speak: jest.fn().mockResolvedValue(undefined),
    processText: jest.fn().mockResolvedValue(undefined),
    qualifyLead: jest.fn().mockResolvedValue(undefined),
    updateMetrics: jest.fn(),
    handleError: jest.fn(),
    connect: jest.fn().mockResolvedValue(undefined),
    disconnect: jest.fn(),
  },
  
  events: {
    onVoiceActivity: jest.fn(),
    onSpeechRecognized: jest.fn(),
    onIntentDetected: jest.fn(),
    onQualificationUpdated: jest.fn(),
    onError: jest.fn(),
    onMetricsUpdated: jest.fn(),
  },
}

// Mock Voice Agent Hooks
export const mockUseVoiceAgent = () => ({
  agent: {
    id: 'agent-1',
    name: 'Sarah',
    isActive: true,
    personality: { tone: 'professional', pace: 'normal', enthusiasm: 0.7 },
  },
  isLoading: false,
  error: null,
  switchAgent: jest.fn(),
  updateAgentSettings: jest.fn(),
})

export const mockUseConversationManager = () => ({
  conversation: {
    id: 'conv-1',
    turns: [],
    startTime: Date.now(),
    agentId: 'agent-1',
  },
  isActive: false,
  startConversation: jest.fn().mockResolvedValue('conv-1'),
  endConversation: jest.fn().mockResolvedValue(undefined),
  addTurn: jest.fn(),
  getHistory: jest.fn().mockReturnValue([]),
  analyzeConversation: jest.fn().mockResolvedValue({}),
})

export const mockUseVoiceEngine = () => ({
  isListening: false,
  isSpeaking: false,
  isProcessing: false,
  audioLevel: 0,
  startListening: jest.fn().mockResolvedValue(undefined),
  stopListening: jest.fn(),
  speak: jest.fn().mockResolvedValue(undefined),
  stopSpeaking: jest.fn(),
  processAudio: jest.fn().mockResolvedValue(undefined),
  error: null,
  metrics: {
    latency: { total: 150 },
    quality: { audioQuality: 0.95 },
  },
  clearError: jest.fn(),
})

export const mockUseLeadQualification = () => ({
  qualificationData: {
    score: 85,
    budget: { min: 300000, max: 500000, confidence: 0.8 },
    timeline: { urgency: 'soon', confidence: 0.9 },
  } as LeadQualificationData,
  isQualifying: false,
  qualifyFromText: jest.fn().mockResolvedValue(undefined),
  updateQualification: jest.fn(),
  resetQualification: jest.fn(),
  getQualificationSummary: jest.fn().mockReturnValue('Highly qualified lead'),
})

export const mockUseVoiceAnalytics = () => ({
  metrics: {
    totalConversations: 150,
    averageLatency: 180,
    qualificationRate: 0.75,
    conversionRate: 0.15,
  },
  isLoading: false,
  error: null,
  refreshMetrics: jest.fn().mockResolvedValue(undefined),
  getMetricsHistory: jest.fn().mockResolvedValue([]),
  exportMetrics: jest.fn().mockResolvedValue('metrics-export.csv'),
})

// Performance Testing Utilities
export const createLatencySimulator = (baseLatency = 100, jitter = 20) => {
  return () => new Promise(resolve => {
    const delay = baseLatency + (Math.random() - 0.5) * jitter
    setTimeout(resolve, Math.max(0, delay))
  })
}

export const createAudioQualitySimulator = (baseQuality = 0.9, variance = 0.1) => {
  return () => {
    const quality = baseQuality + (Math.random() - 0.5) * variance
    return Math.max(0, Math.min(1, quality))
  }
}

// Error Simulation Utilities
export const simulateNetworkError = () => {
  throw new Error('Network connection failed')
}

export const simulateAudioError = () => {
  throw new Error('Microphone access denied')
}

export const simulateProcessingError = () => {
  throw new Error('AI processing timeout')
}

// Test Data Generators
export const generateConversationTurn = (overrides = {}) => ({
  id: `turn-${Date.now()}`,
  timestamp: Date.now(),
  speaker: 'user' as const,
  text: 'I am looking for a 3-bedroom house',
  confidence: 0.9,
  intent: 'property_inquiry',
  entities: { bedrooms: '3', propertyType: 'house' },
  ...overrides,
})

export const generateVoiceMetrics = (overrides = {}) => ({
  latency: {
    speechToText: 80 + Math.random() * 40,
    processing: 30 + Math.random() * 20,
    textToSpeech: 60 + Math.random() * 30,
    total: 170 + Math.random() * 90,
  },
  quality: {
    audioQuality: 0.85 + Math.random() * 0.15,
    transcriptionAccuracy: 0.88 + Math.random() * 0.12,
    responseRelevance: 0.82 + Math.random() * 0.18,
  },
  ...overrides,
})

export const generateLeadData = (overrides = {}) => ({
  id: `lead-${Date.now()}`,
  firstName: 'John',
  lastName: 'Doe',
  email: 'john.doe@example.com',
  phone: '+1-555-0123',
  qualificationScore: 75 + Math.random() * 25,
  status: 'qualified' as const,
  ...overrides,
})

// WebSocket Event Simulation
export const simulateWebSocketEvents = (mockWs: any) => ({
  simulateVoiceActivity: (isActive = true) => {
    mockWs.simulateMessage({
      type: 'voice_activity',
      data: { isActive, confidence: 0.9, timestamp: Date.now() },
    })
  },
  
  simulateSpeechRecognition: (text = 'Hello world') => {
    mockWs.simulateMessage({
      type: 'speech_recognized',
      data: { text, confidence: 0.95, isFinal: true, timestamp: Date.now() },
    })
  },
  
  simulateIntentDetection: (intent = 'property_inquiry') => {
    mockWs.simulateMessage({
      type: 'intent_detected',
      data: { intent, confidence: 0.9, entities: {} },     
    })
  },
  
  simulateQualificationUpdate: (score = 80) => {
    mockWs.simulateMessage({
      type: 'qualification_updated',
      data: { score, budget: { min: 200000, max: 400000, confidence: 0.8 } },
    })
  },
  
  simulateError: (message = 'Test error') => {
    mockWs.simulateMessage({
      type: 'error',
      data: { code: 'TEST_ERROR', message, recoverable: true, timestamp: Date.now() },
    })
  },
})

export default {
  mockAudioProcessor,
  mockSpeechToTextService,
  mockTextToSpeechService,
  mockWebRTCService,
  mockConversationEngine,
  mockAIModelIntegration,
  mockVoiceAIProvider,
  mockUseVoiceAgent,
  mockUseConversationManager,
  mockUseVoiceEngine,
  mockUseLeadQualification,
  mockUseVoiceAnalytics,
}