import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import type { 
  VoiceAIState, 
  VoiceAIConfig, 
  ConversationContext, 
  VoiceAgent, 
  LeadProfile,
  LeadQualificationData,
  VoiceAIMetrics,
  VoiceAIError,
  ConversationTurn
} from '../types'

interface VoiceAIActions {
  // Initialization
  initialize: (config: VoiceAIConfig) => Promise<void>
  shutdown: () => void
  
  // Connection Management
  connect: () => Promise<void>
  disconnect: () => void
  setConnectionState: (state: VoiceAIState['connectionState']) => void
  
  // Conversation Management
  startConversation: (leadId?: string, agentId?: string) => Promise<ConversationContext>
  endConversation: () => Promise<void>
  addConversationTurn: (turn: ConversationTurn) => void
  updateConversationMetadata: (metadata: Partial<ConversationContext['metadata']>) => void
  
  // Agent Management
  setActiveAgent: (agent: VoiceAgent | null) => void
  updateAgentMetrics: (agentId: string, metrics: Partial<VoiceAgent['metrics']>) => void
  
  // Lead Management
  setCurrentLead: (lead: LeadProfile) => void
  updateLeadProfile: (updates: Partial<LeadProfile>) => void
  updateQualificationData: (data: Partial<LeadQualificationData>) => void
  
  // Audio State
  setListening: (listening: boolean) => void
  setSpeaking: (speaking: boolean) => void
  setProcessing: (processing: boolean) => void
  updateAudioLevels: (input: number, output: number) => void
  setInputMuted: (muted: boolean) => void
  setOutputMuted: (muted: boolean) => void
  
  // Metrics and Analytics
  updateMetrics: (metrics: Partial<VoiceAIMetrics>) => void
  recordLatency: (type: keyof VoiceAIMetrics['latency'], value: number) => void
  incrementMetric: (path: string) => void
  
  // Error Handling
  setError: (error: VoiceAIError | null) => void
  clearError: () => void
  
  // Utilities
  reset: () => void
  getConversationDuration: () => number
  getCurrentQualificationScore: () => number
}

type VoiceAIStore = VoiceAIState & VoiceAIActions

const initialMetrics: VoiceAIMetrics = {
  latency: {
    speechToText: 0,
    processing: 0,
    textToSpeech: 0,
    total: 0
  },
  quality: {
    audioQuality: 0,
    transcriptionAccuracy: 0,
    responseRelevance: 0
  },
  engagement: {
    userSpeakingTime: 0,
    agentSpeakingTime: 0,
    silenceTime: 0,
    interruptionCount: 0
  },
  performance: {
    cpuUsage: 0,
    memoryUsage: 0,
    networkLatency: 0,
    errorRate: 0
  }
}

const initialState: VoiceAIState = {
  isInitialized: false,
  isConnected: false,
  isListening: false,
  isSpeaking: false,
  isProcessing: false,
  metrics: initialMetrics,
  connectionState: 'disconnected',
  audioState: {
    inputLevel: 0,
    outputLevel: 0,
    isInputMuted: false,
    isOutputMuted: false
  }
}

export const useVoiceAIStore = create<VoiceAIStore>()(
  subscribeWithSelector((set, get) => ({
    ...initialState,

    // Initialization
    initialize: async (config: VoiceAIConfig) => {
      try {
        set({ isInitialized: false, error: undefined })
        
        // Initialize audio context
        if (typeof window !== 'undefined' && window.AudioContext) {
          // Basic initialization - will be extended by services
          await new Promise(resolve => setTimeout(resolve, 100))
        }
        
        set({ 
          isInitialized: true,
          connectionState: 'disconnected'
        })
      } catch (error) {
        set({ 
          error: {
            code: 'INITIALIZATION_FAILED',
            message: error instanceof Error ? error.message : 'Failed to initialize voice AI',
            recoverable: true,
            timestamp: Date.now()
          }
        })
      }
    },

    shutdown: () => {
      const { currentConversation } = get()
      if (currentConversation) {
        get().endConversation()
      }
      set({ 
        ...initialState,
        isInitialized: false 
      })
    },

    // Connection Management
    connect: async () => {
      try {
        set({ connectionState: 'connecting', error: undefined })
        
        // Simulate connection process
        await new Promise(resolve => setTimeout(resolve, 500))
        
        set({ 
          isConnected: true,
          connectionState: 'connected'
        })
      } catch (error) {
        set({ 
          connectionState: 'error',
          error: {
            code: 'CONNECTION_FAILED',
            message: error instanceof Error ? error.message : 'Failed to connect',
            recoverable: true,
            timestamp: Date.now()
          }
        })
      }
    },

    disconnect: () => {
      const { currentConversation } = get()
      if (currentConversation) {
        get().endConversation()
      }
      set({ 
        isConnected: false,
        connectionState: 'disconnected',
        isListening: false,
        isSpeaking: false,
        isProcessing: false
      })
    },

    setConnectionState: (state) => set({ 
      connectionState: state,
      isConnected: state === 'connected'
    }),

    // Conversation Management
    startConversation: async (leadId, agentId) => {
      const conversation: ConversationContext = {
        id: `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        leadId,
        agentId: agentId || 'default',
        startTime: Date.now(),
        turns: [],
        metadata: {
          platform: 'web',
          channel: 'voice',
          source: 'website'
        },
        analytics: {
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

      set({ currentConversation: conversation })
      return conversation
    },

    endConversation: async () => {
      const { currentConversation, qualificationData } = get()
      if (!currentConversation) return

      const endedConversation: ConversationContext = {
        ...currentConversation,
        endTime: Date.now(),
        qualificationData,
        analytics: {
          ...currentConversation.analytics!,
          duration: Date.now() - currentConversation.startTime
        }
      }

      // Store conversation (would typically save to backend)
      console.log('Conversation ended:', endedConversation)

      set({ 
        currentConversation: undefined,
        currentLead: undefined,
        qualificationData: undefined,
        isListening: false,
        isSpeaking: false,
        isProcessing: false
      })
    },

    addConversationTurn: (turn) => {
      const { currentConversation } = get()
      if (!currentConversation) return

      const updatedConversation = {
        ...currentConversation,
        turns: [...currentConversation.turns, turn]
      }

      set({ currentConversation: updatedConversation })
    },

    updateConversationMetadata: (metadata) => {
      const { currentConversation } = get()
      if (!currentConversation) return

      const updatedConversation = {
        ...currentConversation,
        metadata: { ...currentConversation.metadata, ...metadata }
      }

      set({ currentConversation: updatedConversation })
    },

    // Agent Management
    setActiveAgent: (agent) => set({ activeAgent: agent || undefined }),

    updateAgentMetrics: (agentId, metrics) => {
      const { activeAgent } = get()
      if (activeAgent && activeAgent.id === agentId) {
        set({
          activeAgent: {
            ...activeAgent,
            metrics: { ...activeAgent.metrics, ...metrics }
          }
        })
      }
    },

    // Lead Management
    setCurrentLead: (lead) => set({ currentLead: lead }),

    updateLeadProfile: (updates) => {
      const { currentLead } = get()
      if (!currentLead) return

      const updatedLead = { ...currentLead, ...updates }
      set({ currentLead: updatedLead })
    },

    updateQualificationData: (data) => {
      const { qualificationData } = get()
      const updated = qualificationData ? { ...qualificationData, ...data } : data as LeadQualificationData
      set({ qualificationData: updated })
    },

    // Audio State
    setListening: (listening) => set({ isListening: listening }),
    setSpeaking: (speaking) => set({ isSpeaking: speaking }),
    setProcessing: (processing) => set({ isProcessing: processing }),

    updateAudioLevels: (input, output) => {
      const { audioState } = get()
      set({
        audioState: {
          ...audioState,
          inputLevel: input,
          outputLevel: output
        }
      })
    },

    setInputMuted: (muted) => {
      const { audioState } = get()
      set({
        audioState: { ...audioState, isInputMuted: muted }
      })
    },

    setOutputMuted: (muted) => {
      const { audioState } = get()
      set({
        audioState: { ...audioState, isOutputMuted: muted }
      })
    },

    // Metrics and Analytics
    updateMetrics: (metrics) => {
      const { metrics: currentMetrics } = get()
      set({
        metrics: {
          latency: { ...currentMetrics.latency, ...metrics.latency },
          quality: { ...currentMetrics.quality, ...metrics.quality },
          engagement: { ...currentMetrics.engagement, ...metrics.engagement },
          performance: { ...currentMetrics.performance, ...metrics.performance }
        }
      })
    },

    recordLatency: (type, value) => {
      const { metrics } = get()
      const updatedLatency = { ...metrics.latency, [type]: value }
      
      // Calculate total latency
      updatedLatency.total = Object.values(updatedLatency).reduce((sum, val) => sum + val, 0)
      
      set({
        metrics: {
          ...metrics,
          latency: updatedLatency
        }
      })
    },

    incrementMetric: (path) => {
      const { metrics } = get()
      const pathParts = path.split('.')
      
      if (pathParts.length === 2) {
        const [category, metric] = pathParts
        if (category in metrics && metric in (metrics as any)[category]) {
          set({
            metrics: {
              ...metrics,
              [category]: {
                ...(metrics as any)[category],
                [metric]: (metrics as any)[category][metric] + 1
              }
            }
          })
        }
      }
    },

    // Error Handling
    setError: (error) => set({ error: error || undefined }),
    clearError: () => set({ error: undefined }),

    // Utilities
    reset: () => set({ 
      ...initialState,
      isInitialized: get().isInitialized 
    }),

    getConversationDuration: () => {
      const { currentConversation } = get()
      if (!currentConversation) return 0
      return Date.now() - currentConversation.startTime
    },

    getCurrentQualificationScore: () => {
      const { qualificationData } = get()
      return qualificationData?.score || 0
    }
  }))
)

// Subscribe to connection state changes for cleanup
useVoiceAIStore.subscribe(
  (state) => state.connectionState,
  (connectionState, prevConnectionState) => {
    if (prevConnectionState === 'connected' && connectionState === 'disconnected') {
      // Cleanup when disconnected
      useVoiceAIStore.getState().reset()
    }
  }
)

// Subscribe to error states for auto-recovery
useVoiceAIStore.subscribe(
  (state) => state.error,
  (error) => {
    if (error && error.recoverable) {
      // Auto-clear recoverable errors after 5 seconds
      setTimeout(() => {
        if (useVoiceAIStore.getState().error === error) {
          useVoiceAIStore.getState().clearError()
        }
      }, 5000)
    }
  }
)