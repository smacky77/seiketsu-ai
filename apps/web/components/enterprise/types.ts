// Type definitions for Enterprise Components

// Voice Agent Types
export type VoiceStatus = 'idle' | 'listening' | 'processing' | 'speaking' | 'error'
export type CallStatus = 'incoming' | 'active' | 'on-hold' | 'ended' | 'missed'
export type AgentStatus = 'available' | 'busy' | 'break' | 'offline'
export type CallQuality = 'excellent' | 'good' | 'fair' | 'poor'

// Lead Management Types
export type LeadStatus = 'new' | 'contacted' | 'qualified' | 'appointment' | 'converted' | 'lost'
export type LeadSource = 'website' | 'phone' | 'referral' | 'social' | 'advertisement' | 'other'
export type Priority = 'low' | 'medium' | 'high' | 'urgent'

// Multi-Tenant Types
export type OrganizationStatus = 'active' | 'suspended' | 'trial' | 'expired'
export type SubscriptionTier = 'starter' | 'professional' | 'enterprise' | 'custom'
export type UserRole = 'owner' | 'admin' | 'manager' | 'agent' | 'viewer'

// Integration Types
export type IntegrationStatus = 'connected' | 'disconnected' | 'error' | 'syncing' | 'pending'
export type IntegrationType = 'crm' | 'mls' | 'email' | 'sms' | 'calendar' | 'analytics' | 'storage' | 'payment' | 'webhook'

// Common Enterprise Types
export interface BaseEntity {
  id: string
  createdAt: Date
  updatedAt?: Date
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  pageSize: number
  hasMore: boolean
}

export interface FilterOptions {
  search?: string
  status?: string[]
  dateRange?: {
    start: Date
    end: Date
  }
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

export interface MetricData {
  label: string
  value: number | string
  change?: number
  trend?: 'up' | 'down' | 'neutral'
  format?: 'number' | 'currency' | 'percentage' | 'duration'
}

export interface ChartDataPoint {
  [key: string]: any
  timestamp?: Date
}

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface WebSocketMessage {
  type: string
  payload: any
  timestamp: Date
  id?: string
}

// Performance monitoring types
export interface PerformanceMetrics {
  responseTime: number
  throughput: number
  errorRate: number
  uptime: number
  lastUpdated: Date
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'down'
  services: ServiceHealth[]
  lastCheck: Date
}

export interface ServiceHealth {
  name: string
  status: 'up' | 'down' | 'degraded'
  responseTime?: number
  lastCheck: Date
  message?: string
}

// Audit and compliance types
export interface AuditLog {
  id: string
  userId: string
  action: string
  resource: string
  resourceId?: string
  details: Record<string, any>
  timestamp: Date
  ipAddress?: string
  userAgent?: string
}

export interface ComplianceReport {
  id: string
  type: 'gdpr' | 'ccpa' | 'sox' | 'hipaa' | 'custom'
  status: 'compliant' | 'non-compliant' | 'pending'
  findings: string[]
  recommendations: string[]
  generatedAt: Date
  validUntil: Date
}

// Configuration types
export interface ComponentConfig {
  enabled: boolean
  settings: Record<string, any>
  permissions?: string[]
  featureFlags?: Record<string, boolean>
}

export interface EnterpriseSettings {
  organization: {
    name: string
    domain: string
    timezone: string
    locale: string
  }
  security: {
    twoFactorRequired: boolean
    sessionTimeout: number
    passwordPolicy: PasswordPolicy
    ipWhitelist: string[]
  }
  features: {
    voiceAgent: ComponentConfig
    leadManagement: ComponentConfig
    analytics: ComponentConfig
    integrations: ComponentConfig
  }
  billing: {
    tier: SubscriptionTier
    limits: UsageLimits
    billingEmail: string
    nextBillingDate: Date
  }
}

export interface PasswordPolicy {
  minLength: number
  requireUppercase: boolean
  requireLowercase: boolean
  requireNumbers: boolean
  requireSymbols: boolean
  maxAge: number
}

export interface UsageLimits {
  voiceMinutes: number
  leads: number
  apiCalls: number
  storage: number
  integrations: number
  users: number
}

// Event types for real-time updates
export interface SystemEvent {
  type: string
  source: string
  data: any
  timestamp: Date
  severity: 'info' | 'warning' | 'error' | 'critical'
}

export interface NotificationPreferences {
  email: boolean
  sms: boolean
  push: boolean
  inApp: boolean
  webhook?: string
}

// Export utility types
export type Nullable<T> = T | null
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>
export type RequiredBy<T, K extends keyof T> = T & Required<Pick<T, K>>