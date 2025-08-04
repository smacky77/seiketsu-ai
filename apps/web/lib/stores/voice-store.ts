import { create } from 'zustand'
import type { VoiceAgent, VoiceCall, AgentStatus } from '@/types'

interface VoiceState {
  agents: VoiceAgent[]
  activeAgent: VoiceAgent | null
  currentCall: VoiceCall | null
  isRecording: boolean
  isConnected: boolean
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error'
  transcript: string
  audioLevel: number
  callHistory: VoiceCall[]
  error: string | null
}

interface VoiceActions {
  // Agent management
  setAgents: (agents: VoiceAgent[]) => void
  addAgent: (agent: VoiceAgent) => void
  updateAgent: (agentId: string, updates: Partial<VoiceAgent>) => void
  removeAgent: (agentId: string) => void
  setActiveAgent: (agent: VoiceAgent | null) => void
  updateAgentStatus: (agentId: string, status: AgentStatus) => void

  // Call management
  startCall: (call: VoiceCall) => void
  endCall: () => void
  updateCall: (updates: Partial<VoiceCall>) => void
  addToCallHistory: (call: VoiceCall) => void

  // Recording and audio
  startRecording: () => void
  stopRecording: () => void
  setAudioLevel: (level: number) => void
  setTranscript: (transcript: string) => void
  appendTranscript: (text: string) => void
  clearTranscript: () => void

  // Connection management
  setConnectionStatus: (status: VoiceState['connectionStatus']) => void
  connect: () => Promise<void>
  disconnect: () => void

  // Error handling
  setError: (error: string | null) => void
  clearError: () => void

  // Utilities
  getAgentById: (id: string) => VoiceAgent | undefined
  getActiveAgentStatus: () => AgentStatus | null
  isAgentActive: (agentId: string) => boolean
}

type VoiceStore = VoiceState & VoiceActions

export const useVoiceStore = create<VoiceStore>((set, get) => ({
  // Initial state
  agents: [],
  activeAgent: null,
  currentCall: null,
  isRecording: false,
  isConnected: false,
  connectionStatus: 'disconnected',
  transcript: '',
  audioLevel: 0,
  callHistory: [],
  error: null,

  // Agent management
  setAgents: (agents) => set({ agents }),

  addAgent: (agent) => {
    const { agents } = get()
    set({ agents: [...agents, agent] })
  },

  updateAgent: (agentId, updates) => {
    const { agents } = get()
    set({
      agents: agents.map(agent =>
        agent.id === agentId ? { ...agent, ...updates } : agent
      ),
    })
  },

  removeAgent: (agentId) => {
    const { agents, activeAgent } = get()
    set({
      agents: agents.filter(agent => agent.id !== agentId),
      activeAgent: activeAgent?.id === agentId ? null : activeAgent,
    })
  },

  setActiveAgent: (agent) => set({ activeAgent: agent }),

  updateAgentStatus: (agentId, status) => {
    const { agents } = get()
    set({
      agents: agents.map(agent =>
        agent.id === agentId ? { ...agent, status } : agent
      ),
    })
  },

  // Call management
  startCall: (call) => {
    set({
      currentCall: call,
      isConnected: true,
      connectionStatus: 'connected',
      transcript: '',
      error: null,
    })
  },

  endCall: () => {
    const { currentCall, callHistory } = get()
    if (currentCall) {
      const endedCall = {
        ...currentCall,
        endTime: new Date(),
        duration: currentCall.startTime 
          ? Math.floor((Date.now() - new Date(currentCall.startTime).getTime()) / 1000)
          : 0,
      }
      set({
        currentCall: null,
        isRecording: false,
        isConnected: false,
        connectionStatus: 'disconnected',
        audioLevel: 0,
        callHistory: [endedCall, ...callHistory.slice(0, 99)], // Keep last 100 calls
      })
    }
  },

  updateCall: (updates) => {
    const { currentCall } = get()
    if (currentCall) {
      set({
        currentCall: { ...currentCall, ...updates },
      })
    }
  },

  addToCallHistory: (call) => {
    const { callHistory } = get()
    set({
      callHistory: [call, ...callHistory.slice(0, 99)],
    })
  },

  // Recording and audio
  startRecording: () => set({ isRecording: true }),

  stopRecording: () => set({ isRecording: false }),

  setAudioLevel: (level) => set({ audioLevel: level }),

  setTranscript: (transcript) => set({ transcript }),

  appendTranscript: (text) => {
    const { transcript } = get()
    set({ transcript: transcript + (transcript ? ' ' : '') + text })
  },

  clearTranscript: () => set({ transcript: '' }),

  // Connection management
  setConnectionStatus: (status) => {
    set({
      connectionStatus: status,
      isConnected: status === 'connected',
      error: status === 'error' ? 'Connection failed' : null,
    })
  },

  connect: async () => {
    try {
      set({ connectionStatus: 'connecting', error: null })
      
      // Simulate connection logic - replace with actual WebRTC/WebSocket implementation
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      set({
        connectionStatus: 'connected',
        isConnected: true,
        error: null,
      })
    } catch (error) {
      set({
        connectionStatus: 'error',
        isConnected: false,
        error: error instanceof Error ? error.message : 'Connection failed',
      })
    }
  },

  disconnect: () => {
    const { currentCall } = get()
    if (currentCall) {
      get().endCall()
    }
    set({
      connectionStatus: 'disconnected',
      isConnected: false,
      isRecording: false,
      audioLevel: 0,
      error: null,
    })
  },

  // Error handling
  setError: (error) => set({ error }),

  clearError: () => set({ error: null }),

  // Utilities
  getAgentById: (id) => {
    const { agents } = get()
    return agents.find(agent => agent.id === id)
  },

  getActiveAgentStatus: () => {
    const { activeAgent } = get()
    return activeAgent?.status || null
  },

  isAgentActive: (agentId) => {
    const { agents } = get()
    const agent = agents.find(a => a.id === agentId)
    return agent?.status === 'active'
  },
}))