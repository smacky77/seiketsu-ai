import React, { ReactElement, ReactNode } from 'react'
import { render, RenderOptions, RenderResult } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { NextRouter } from 'next/router'
import { jest } from '@jest/globals'

// Mock implementations for voice AI services
export const mockVoiceAIConfig = {
  elevenlabs: {
    apiKey: 'test-api-key',
    voiceId: 'test-voice-id',
    modelId: 'test-model',
    stability: 0.5,
    similarityBoost: 0.75,
    style: 0.5,
  },
  openai: {
    apiKey: 'test-openai-key',
    model: 'gpt-4',
    temperature: 0.7,
    maxTokens: 150,
  },
  realtime: {
    maxLatency: 180,
    audioSampleRate: 44100,
    channels: 1,
    bitDepth: 16,
  },
  features: {
    wakeWordDetection: true,
    voiceBiometrics: false,
    emotionDetection: true,
    backgroundNoiseSupression: true,
  },
}

export const mockConversationTurn = {
  id: 'test-turn-1',
  timestamp: Date.now(),
  speaker: 'user' as const,
  text: 'Hello, I\'m looking for a house',
  confidence: 0.95,
  intent: 'property_inquiry',
  entities: {
    property_type: 'house',
  },
  sentiment: {
    polarity: 0.2,
    magnitude: 0.8,
    label: 'positive' as const,
  },
  duration: 2500,
}

export const mockLeadQualificationData = {
  score: 85,
  budget: {
    min: 300000,
    max: 500000,
    confidence: 0.8,
  },
  timeline: {
    urgency: 'soon' as const,
    confidence: 0.9,
  },
  location: {
    preferred: ['Downtown', 'Midtown'],
    flexibility: 0.7,
    confidence: 0.85,
  },
  propertyType: {
    type: 'house',
    features: ['garden', 'parking'],
    confidence: 0.9,
  },
  motivation: {
    primary: 'investment',
    secondary: ['rental income'],
    confidence: 0.8,
  },
  decisionMaker: {
    isDecisionMaker: true,
    influencers: [],
    confidence: 0.95,
  },
}

export const mockVoiceAgent = {
  id: 'agent-1',
  name: 'Sarah',
  voiceId: 'voice-sarah-1',
  personality: {
    tone: 'professional' as const,
    pace: 'normal' as const,
    enthusiasm: 0.7,
  },
  expertise: ['residential', 'commercial'],
  systemPrompt: 'You are a helpful real estate assistant',
  conversationRules: {
    maxTurnLength: 300,
    allowInterruptions: true,
    escalationTriggers: ['angry', 'confused'],
  },
  isActive: true,
  metrics: {
    conversationsHandled: 150,
    averageQualificationScore: 82,
    conversionRate: 0.15,
    averageCallDuration: 8.5,
  },
}

export const mockVoiceAIMetrics = {
  latency: {
    speechToText: 120,
    processing: 50,
    textToSpeech: 80,
    total: 250,
  },
  quality: {
    audioQuality: 0.95,
    transcriptionAccuracy: 0.92,
    responseRelevance: 0.88,
  },
  engagement: {
    userSpeakingTime: 45000,
    agentSpeakingTime: 38000,
    silenceTime: 5000,
    interruptionCount: 2,
  },
  performance: {
    cpuUsage: 15.5,
    memoryUsage: 256,
    networkLatency: 45,
    errorRate: 0.02,
  },
}

// Mock WebSocket implementation
export class MockWebSocket {
  onopen: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  
  readyState: number = WebSocket.CONNECTING
  
  constructor(url: string) {
    setTimeout(() => {
      this.readyState = WebSocket.OPEN
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 100)
  }
  
  send(data: string | ArrayBufferLike | Blob | ArrayBufferView): void {
    // Mock send implementation
  }
  
  close(code?: number, reason?: string): void {
    this.readyState = WebSocket.CLOSED
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code, reason }))
    }
  }
  
  simulateMessage(data: any): void {
    if (this.onmessage && this.readyState === WebSocket.OPEN) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }))
    }
  }
  
  simulateError(): void {
    if (this.onerror) {
      this.onerror(new Event('error'))
    }
  }
}

// Mock MediaDevices and getUserMedia
export const mockGetUserMedia = jest.fn().mockResolvedValue({
  getAudioTracks: () => [
    {
      id: 'audio-track-1',
      kind: 'audio',
      enabled: true,
      muted: false,
      stop: jest.fn(),
    },
  ],
  getTracks: () => [
    {
      id: 'audio-track-1',
      kind: 'audio',
      enabled: true,
      muted: false,
      stop: jest.fn(),
    },
  ],
  addTrack: jest.fn(),
  removeTrack: jest.fn(),
  clone: jest.fn(),
})

// Mock Web Audio API
export const mockAudioContext = {
  createMediaStreamSource: jest.fn().mockReturnValue({
    connect: jest.fn(),
    disconnect: jest.fn(),
  }),
  createAnalyser: jest.fn().mockReturnValue({
    fftSize: 256,
    frequencyBinCount: 128,
    getByteFrequencyData: jest.fn(),
    getByteTimeDomainData: jest.fn(),
    connect: jest.fn(),
    disconnect: jest.fn(),
  }),
  createGain: jest.fn().mockReturnValue({
    gain: { value: 1 },
    connect: jest.fn(),
    disconnect: jest.fn(),
  }),
  destination: {},
  sampleRate: 44100,
  close: jest.fn(),
  resume: jest.fn().mockResolvedValue(undefined),
  suspend: jest.fn().mockResolvedValue(undefined),
  state: 'running',
}

// Mock RTCPeerConnection
export const mockRTCPeerConnection = {
  addStream: jest.fn(),
  addTrack: jest.fn(),
  close: jest.fn(),
  createAnswer: jest.fn().mockResolvedValue({}),
  createDataChannel: jest.fn().mockReturnValue({
    send: jest.fn(),
    close: jest.fn(),
    onopen: null,
    onclose: null,
    onmessage: null,
  }),
  createOffer: jest.fn().mockResolvedValue({}),
  getStats: jest.fn().mockResolvedValue(new Map()),
  setLocalDescription: jest.fn().mockResolvedValue(undefined),
  setRemoteDescription: jest.fn().mockResolvedValue(undefined),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  connectionState: 'new',
  iceConnectionState: 'new',
  signalingState: 'stable',
}

// Enhanced render function with providers
interface ExtendedRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  preloadedState?: any
  queryClient?: QueryClient
  router?: Partial<NextRouter>
}

const AllTheProviders = ({ 
  children, 
  queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
}: {
  children: ReactNode
  queryClient?: QueryClient
}) => {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

export const renderWithProviders = (
  ui: ReactElement,
  options: ExtendedRenderOptions = {}
): RenderResult => {
  const { queryClient, ...renderOptions } = options

  const Wrapper = ({ children }: { children: ReactNode }) => (
    <AllTheProviders queryClient={queryClient}>
      {children}
    </AllTheProviders>
  )

  return render(ui, { wrapper: Wrapper, ...renderOptions })
}

// Performance testing utilities
export const measureRenderTime = async (
  renderFunction: () => Promise<RenderResult> | RenderResult
): Promise<{ result: RenderResult; renderTime: number }> => {
  const startTime = performance.now()
  const result = await renderFunction()
  const endTime = performance.now()
  const renderTime = endTime - startTime
  
  return { result, renderTime }
}

export const waitForAsyncUpdates = () => 
  new Promise(resolve => setTimeout(resolve, 0))

// Accessibility testing utilities
export const getAccessibilityViolations = async (container: HTMLElement) => {
  const { default: axe } = await import('@axe-core/react')
  return new Promise((resolve) => {
    axe(React, { preload: false }, 1000, (results) => {
      resolve(results.violations)
    })
  })
}

// Voice AI specific test utilities
export const createMockVoiceAIProvider = (initialState = {}) => ({
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
  metrics: mockVoiceAIMetrics,
  startListening: jest.fn(),
  stopListening: jest.fn(),
  speak: jest.fn(),
  processText: jest.fn(),
  qualifyLead: jest.fn(),
  ...initialState,
})

// WebSocket testing utilities
export const createMockWebSocketService = () => ({
  connect: jest.fn().mockResolvedValue(new MockWebSocket('ws://localhost')),
  disconnect: jest.fn(),
  send: jest.fn(),
  subscribe: jest.fn(),
  unsubscribe: jest.fn(),
  isConnected: true,
})

// API service mocks
export const createMockApiService = () => ({
  leads: {
    getAll: jest.fn().mockResolvedValue([]),
    getById: jest.fn().mockResolvedValue({}),
    create: jest.fn().mockResolvedValue({}),
    update: jest.fn().mockResolvedValue({}),
    delete: jest.fn().mockResolvedValue({}),
  },
  voice: {
    startSession: jest.fn().mockResolvedValue({}),
    endSession: jest.fn().mockResolvedValue({}),
    processAudio: jest.fn().mockResolvedValue({}),
  },
  analytics: {
    getMetrics: jest.fn().mockResolvedValue(mockVoiceAIMetrics),
    getConversations: jest.fn().mockResolvedValue([]),
  },
})

// Multi-tenant testing utilities
export const createMockTenantContext = (tenantId = 'test-tenant') => ({
  currentTenant: {
    id: tenantId,
    name: 'Test Organization',
    domain: 'test.example.com',
    status: 'active' as const,
    tier: 'professional' as const,
  },
  switchTenant: jest.fn(),
  canAccess: jest.fn().mockReturnValue(true),
})

// Custom matchers for voice AI testing
export const voiceAIMatchers = {
  toHaveValidLatency: (received: number, threshold = 180) => {
    const pass = received <= threshold
    return {
      message: () =>
        `expected ${received}ms to ${
          pass ? 'not ' : ''
        }be within acceptable latency threshold of ${threshold}ms`,
      pass,
    }
  },
  
  toHaveValidAudioQuality: (received: number, threshold = 0.8) => {
    const pass = received >= threshold
    return {
      message: () =>
        `expected audio quality ${received} to ${
          pass ? 'not ' : ''
        }be above threshold of ${threshold}`,
      pass,
    }
  },
}

// Export everything
export * from '@testing-library/react'
export { renderWithProviders as render }