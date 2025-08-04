// Enterprise Components for Seiketsu AI Voice Agent Platform
// Advanced production-ready interfaces for enterprise deployments

export { default as VoiceAgentControlCenter } from './voice-agent-control-center'
export { default as LeadManagementSystem } from './lead-management-system'
export { default as MultiTenantAdmin } from './multi-tenant-admin'
export { default as RealTimeCommunicationHub } from './real-time-communication-hub'
export { default as AnalyticsDashboard } from './analytics-dashboard'
export { default as IntegrationManagementCenter } from './integration-management-center'

// Re-export types for external use
export type {
  VoiceStatus,
  CallStatus,
  AgentStatus,
  LeadStatus,
  IntegrationStatus,
  IntegrationType
} from './types'

// Enterprise component configurations
export const ENTERPRISE_COMPONENTS = {
  VOICE_CONTROL: 'voice-agent-control-center',
  LEAD_MANAGEMENT: 'lead-management-system',
  MULTI_TENANT: 'multi-tenant-admin',
  COMMUNICATION: 'real-time-communication-hub',
  ANALYTICS: 'analytics-dashboard',
  INTEGRATIONS: 'integration-management-center'
} as const

// Default configurations for enterprise components
export const DEFAULT_CONFIGS = {
  voiceAgent: {
    refreshInterval: 1000,
    maxCallDuration: 3600, // 1 hour
    emergencyStopEnabled: true
  },
  leadManagement: {
    pageSize: 50,
    autoRefresh: true,
    defaultSort: 'lastContact',
    defaultOrder: 'desc'
  },
  multiTenant: {
    maxOrganizations: 1000,
    billingCurrency: 'USD',
    defaultTimeZone: 'UTC'
  },
  communication: {
    maxActiveCallsDisplay: 10,
    transcriptRetention: 90, // days
    qualityThreshold: 0.8
  },
  analytics: {
    defaultTimeRange: 'month',
    refreshInterval: 30000, // 30 seconds
    maxDataPoints: 100
  },
  integrations: {
    maxRetries: 3,
    timeoutMs: 30000,
    rateLimitBuffer: 0.8
  }
} as const