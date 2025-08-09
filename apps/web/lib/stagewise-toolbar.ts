// Mock toolbar integration for development
// This file provides a fallback when the actual @21st-extension/toolbar is not available

export interface ToolbarConfig {
  stage?: string
  context?: any
  features?: string[]
}

export class StageWiseToolbar {
  private config: ToolbarConfig = {}

  constructor(config: ToolbarConfig = {}) {
    this.config = config
  }

  init() {
    if (typeof window !== 'undefined') {
      console.log('StageWise Toolbar initialized (mock)', this.config)
    }
  }

  setStage(stage: string) {
    this.config.stage = stage
    console.log('Stage set to:', stage)
  }

  setContext(context: any) {
    this.config.context = context
    console.log('Context updated:', context)
  }

  show() {
    console.log('Toolbar shown')
  }

  hide() {
    console.log('Toolbar hidden')
  }

  destroy() {
    console.log('Toolbar destroyed')
  }
}

// Enhanced toolbar configuration for BMAD Phase 2
const stagewiseConfig = {
  plugins: [
    'voice-processing',
    'real-estate-data',
    'lead-qualification',
    'market-intelligence'
  ],
  theme: 'dark',
  position: 'bottom-right',
  aiAssistance: true,
  realTimeCollaboration: true,
  // Development workflow enhancements
  features: {
    codeGeneration: true,
    apiTesting: true,
    performanceMonitoring: true,
    errorTracking: true,
    realtimeSync: true
  },
  // Integration settings
  integrations: {
    backend: 'http://localhost:8000',
    websocket: 'ws://localhost:8000/ws',
    elevenlabs: process.env.NEXT_PUBLIC_ELEVENLABS_API_KEY
  }
}

// Mock the module that would come from @21st-extension/toolbar
export const initToolbar = (config: ToolbarConfig = {}) => {
  if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
    console.log('Mock toolbar initialized with config:', { ...stagewiseConfig, ...config })
  }
  return new StageWiseToolbar(config)
}

// Initialize the toolbar when your app starts
export function setupStagewise() {
  // Only initialize once and only in development mode
  if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
    initToolbar(stagewiseConfig as any)
  }
}

// For compatibility with existing imports
export const Toolbar = StageWiseToolbar
export default {
  StageWiseToolbar,
  initToolbar,
  setupStagewise,
  version: '1.0.0-mock'
}