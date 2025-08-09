// Epic 4: Enterprise Compliance & Advanced Customization Types

// GDPR Compliance Types
export interface GDPRConsent {
  id: string
  userId: string
  consentType: 'marketing' | 'analytics' | 'functional' | 'necessary'
  granted: boolean
  timestamp: Date
  ipAddress: string
  userAgent: string
  consentMethod: 'explicit' | 'implicit' | 'opt-in' | 'opt-out'
  withdrawnAt?: Date
  expiresAt?: Date
  legalBasis: 'consent' | 'contract' | 'legal_obligation' | 'vital_interests' | 'public_task' | 'legitimate_interests'
}

export interface DataSubjectRequest {
  id: string
  userId: string
  requestType: 'access' | 'rectification' | 'erasure' | 'portability' | 'restriction' | 'objection'
  status: 'pending' | 'in_progress' | 'completed' | 'rejected'
  requestedAt: Date
  completedAt?: Date
  requestDetails: string
  responseData?: any
  verificationStatus: 'pending' | 'verified' | 'failed'
  processingNotes?: string
}

export interface DataProcessingActivity {
  id: string
  name: string
  description: string
  legalBasis: string
  dataCategories: string[]
  dataSubjects: string[]
  recipients: string[]
  retentionPeriod: number // days
  securityMeasures: string[]
  crossBorderTransfers: boolean
  transferMechanisms?: string[]
  lastReviewed: Date
  responsible: string
}

export interface PrivacySettings {
  userId: string
  dataProcessing: {
    analytics: boolean
    marketing: boolean
    personalization: boolean
    thirdPartySharing: boolean
  }
  communication: {
    emailMarketing: boolean
    smsMarketing: boolean
    pushNotifications: boolean
    productUpdates: boolean
  }
  dataRetention: {
    voiceRecordings: number // days
    conversationLogs: number
    analyticsData: number
    personalData: number
  }
  cookiePreferences: {
    necessary: boolean
    functional: boolean
    analytics: boolean
    marketing: boolean
  }
  updatedAt: Date
}

// SOC 2 Compliance Types
export interface AuditLog {
  id: string
  timestamp: Date
  userId?: string
  sessionId?: string
  action: string
  resource: string
  resourceId?: string
  ipAddress: string
  userAgent: string
  outcome: 'success' | 'failure' | 'error'
  riskLevel: 'low' | 'medium' | 'high' | 'critical'
  details: Record<string, any>
  correlationId?: string
}

export interface SecurityEvent {
  id: string
  timestamp: Date
  eventType: 'authentication' | 'authorization' | 'data_access' | 'configuration_change' | 'security_incident' | 'system'
  severity: 'info' | 'warning' | 'error' | 'critical'
  userId?: string
  ipAddress: string
  description: string
  metadata: Record<string, any>
  resolved: boolean
  resolvedAt?: Date
  resolvedBy?: string
}

export interface ComplianceMetrics {
  period: string
  dataSubjectRequests: {
    total: number
    completed: number
    averageResponseTime: number
    breaches: number
  }
  auditLogs: {
    totalEvents: number
    securityEvents: number
    failedAttempts: number
    errorRate: number
  }
  dataRetention: {
    recordsProcessed: number
    recordsDeleted: number
    complianceRate: number
  }
  accessControl: {
    activeUsers: number
    privilegedUsers: number
    failedLogins: number
    accountLockouts: number
  }
}

// White Label Customization Types
export interface BrandConfiguration {
  tenantId: string
  brandName: string
  logo: {
    primary: string
    secondary?: string
    favicon: string
    dimensions: {
      width: number
      height: number
    }
  }
  colors: {
    primary: string
    secondary: string
    accent: string
    background: string
    surface: string
    text: {
      primary: string
      secondary: string
      muted: string
    }
    status: {
      success: string
      warning: string
      error: string
      info: string
    }
  }
  typography: {
    fontFamily: {
      sans: string
      serif?: string
      mono?: string
    }
    fontSizes: Record<string, string>
    fontWeights: Record<string, number>
    lineHeights: Record<string, number>
  }
  customCss?: string
  updatedAt: Date
  createdBy: string
}

export interface WhiteLabelSettings {
  tenantId: string
  customization: {
    hideSourceBranding: boolean
    customDomain?: string
    customEmailDomain?: string
    customSupportEmail?: string
    showPoweredBy: boolean
  }
  features: {
    voiceAI: boolean
    marketIntelligence: boolean
    automatedCommunication: boolean
    smartScheduling: boolean
    customWorkflows: boolean
    apiAccess: boolean
    whiteLabeling: boolean
    multiTenant: boolean
  }
  limits: {
    maxUsers: number
    maxConversations: number
    maxAPIRequests: number
    maxStorageGB: number
  }
  billing: {
    plan: string
    billingCycle: 'monthly' | 'annual'
    customPricing: boolean
  }
}

// RBAC (Role-Based Access Control) Types
export interface Permission {
  id: string
  name: string
  description: string
  resource: string
  action: 'create' | 'read' | 'update' | 'delete' | 'execute' | '*'
  scope?: 'own' | 'tenant' | 'global'
  conditions?: Record<string, any>
}

export interface Role {
  id: string
  name: string
  description: string
  permissions: Permission[]
  isSystem: boolean
  tenantId?: string
  inheritedRoles?: string[]
  createdAt: Date
  updatedAt: Date
}

export interface UserRole {
  userId: string
  roleId: string
  tenantId?: string
  assignedBy: string
  assignedAt: Date
  expiresAt?: Date
  conditions?: Record<string, any>
}

export interface AccessControlPolicy {
  id: string
  name: string
  description: string
  rules: AccessControlRule[]
  priority: number
  active: boolean
  tenantId?: string
  createdBy: string
  createdAt: Date
}

export interface AccessControlRule {
  id: string
  condition: string // JSON logic expression
  effect: 'allow' | 'deny'
  resources: string[]
  actions: string[]
  principals?: string[] // user IDs or role IDs
}

// Custom Workflow Builder Types
export interface WorkflowTemplate {
  id: string
  name: string
  description: string
  category: 'lead_qualification' | 'communication' | 'follow_up' | 'property_management' | 'custom'
  version: string
  isPublic: boolean
  tenantId?: string
  steps: WorkflowTemplateStep[]
  triggers: WorkflowTrigger[]
  variables: WorkflowVariable[]
  createdBy: string
  createdAt: Date
  updatedAt: Date
  usageCount: number
}

export interface WorkflowTemplateStep {
  id: string
  name: string
  type: 'action' | 'condition' | 'delay' | 'parallel' | 'loop' | 'manual' | 'api_call' | 'notification'
  config: Record<string, any>
  position: {
    x: number
    y: number
  }
  connections: {
    input: string[]
    output: string[]
  }
  conditions?: {
    if: string // JSON logic
    then: string // next step ID
    else?: string // alternative step ID
  }
}

export interface WorkflowTrigger {
  id: string
  type: 'manual' | 'scheduled' | 'event' | 'webhook' | 'api'
  config: Record<string, any>
  active: boolean
}

export interface WorkflowVariable {
  id: string
  name: string
  type: 'string' | 'number' | 'boolean' | 'object' | 'array'
  required: boolean
  defaultValue?: any
  description: string
  validation?: {
    pattern?: string
    min?: number
    max?: number
    enum?: any[]
  }
}

export interface WorkflowExecution {
  id: string
  workflowId: string
  templateId: string
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled'
  startedAt: Date
  completedAt?: Date
  triggeredBy: string
  context: Record<string, any>
  currentStep?: string
  stepHistory: WorkflowExecutionStep[]
  error?: string
  output?: Record<string, any>
}

export interface WorkflowExecutionStep {
  stepId: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped'
  startedAt: Date
  completedAt?: Date
  input?: Record<string, any>
  output?: Record<string, any>
  error?: string
  retryCount: number
}

// Data Retention Types
export interface DataRetentionPolicy {
  id: string
  name: string
  description: string
  dataType: 'voice_recordings' | 'conversation_logs' | 'user_data' | 'analytics' | 'audit_logs'
  retentionPeriod: number // days
  archivePeriod?: number // days before deletion
  deletionMethod: 'soft' | 'hard' | 'anonymize'
  legalHold: boolean
  complianceRequirement?: string
  tenantId?: string
  active: boolean
  createdAt: Date
  updatedAt: Date
  lastExecuted?: Date
  nextExecution: Date
}

export interface DataRetentionExecution {
  id: string
  policyId: string
  executedAt: Date
  recordsProcessed: number
  recordsArchived: number
  recordsDeleted: number
  recordsAnonymized: number
  status: 'success' | 'partial' | 'failed'
  errors?: string[]
  executionTime: number // seconds
}

// SSO Integration Types
export interface SAMLConfiguration {
  tenantId: string
  entityId: string
  ssoUrl: string
  sloUrl?: string
  x509Certificate: string
  nameIdFormat: 'email' | 'persistent' | 'transient'
  attributeMapping: {
    email: string
    firstName: string
    lastName: string
    roles?: string
  }
  signRequests: boolean
  encryptAssertions: boolean
  active: boolean
  metadata?: string
}

export interface OAuthConfiguration {
  tenantId: string
  provider: 'google' | 'microsoft' | 'okta' | 'auth0' | 'custom'
  clientId: string
  clientSecret: string // encrypted
  authorizationUrl: string
  tokenUrl: string
  userInfoUrl: string
  scopes: string[]
  attributeMapping: {
    email: string
    firstName: string
    lastName: string
    roles?: string
  }
  active: boolean
}

export interface SSOSession {
  id: string
  userId: string
  tenantId: string
  provider: 'saml' | 'oauth'
  sessionToken: string
  expiresAt: Date
  attributes: Record<string, any>
  createdAt: Date
  lastAccessed: Date
  ipAddress: string
  userAgent: string
}

// API Rate Limiting Types
export interface RateLimitPolicy {
  id: string
  name: string
  description: string
  tenantId?: string
  endpoint?: string // specific endpoint or * for all
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | '*'
  limit: number
  window: number // seconds
  burstLimit?: number
  quotaLimit?: number // per billing period
  active: boolean
  priority: number
  createdAt: Date
}

export interface RateLimitUsage {
  key: string // user:endpoint or tenant:endpoint
  policyId: string
  requests: number
  resetAt: Date
  quotaUsed: number
  blocked: boolean
  lastRequest: Date
}

// Multi-Tenant Architecture Types
export interface Tenant {
  id: string
  name: string
  slug: string
  domain?: string
  status: 'active' | 'suspended' | 'trial' | 'cancelled'
  plan: 'starter' | 'professional' | 'enterprise' | 'custom'
  settings: TenantSettings
  limits: TenantLimits
  billing: TenantBilling
  createdAt: Date
  updatedAt: Date
  createdBy: string
}

export interface TenantSettings {
  timezone: string
  locale: string
  currency: string
  features: string[]
  branding?: BrandConfiguration
  sso?: {
    saml?: SAMLConfiguration
    oauth?: OAuthConfiguration
  }
  dataRetention: {
    voiceRecordings: number
    conversationLogs: number
    auditLogs: number
  }
  security: {
    enforceSSO: boolean
    require2FA: boolean
    sessionTimeout: number
    ipWhitelist?: string[]
  }
}

export interface TenantLimits {
  maxUsers: number
  maxConversations: number
  maxAPIRequests: number
  maxStorageGB: number
  maxWorkflows: number
  rateLimit: {
    requests: number
    window: number
  }
}

export interface TenantBilling {
  customerId: string
  subscriptionId: string
  plan: string
  status: 'active' | 'past_due' | 'cancelled' | 'trialing'
  currentPeriodStart: Date
  currentPeriodEnd: Date
  trialEnd?: Date
  usage: {
    users: number
    conversations: number
    apiRequests: number
    storageGB: number
  }
}

// Backup and Disaster Recovery Types
export interface BackupPolicy {
  id: string
  name: string
  description: string
  frequency: 'hourly' | 'daily' | 'weekly' | 'monthly'
  retentionDays: number
  includeFiles: boolean
  includeDatabase: boolean
  includeConfiguration: boolean
  encryptionEnabled: boolean
  compressionEnabled: boolean
  destination: 's3' | 'gcs' | 'azure' | 'local'
  destinationConfig: Record<string, any>
  tenantId?: string
  active: boolean
  createdAt: Date
  updatedAt: Date
  lastBackup?: Date
  nextBackup: Date
}

export interface BackupRecord {
  id: string
  policyId: string
  startedAt: Date
  completedAt?: Date
  status: 'in_progress' | 'completed' | 'failed' | 'partial'
  size: number // bytes
  location: string
  checksum: string
  encrypted: boolean
  compressed: boolean
  metadata: {
    version: string
    tenantId?: string
    dataTypes: string[]
    recordCount: Record<string, number>
  }
  error?: string
  restorable: boolean
}

export interface DisasterRecoveryPlan {
  id: string
  name: string
  description: string
  rtoMinutes: number // Recovery Time Objective
  rpoMinutes: number // Recovery Point Objective
  triggers: string[]
  procedures: DisasterRecoveryProcedure[]
  contacts: {
    primary: string
    secondary: string
    escalation: string[]
  }
  resources: {
    backupLocation: string
    alternateInfrastructure: string
    communicationChannels: string[]
  }
  active: boolean
  lastTested?: Date
  nextTest: Date
  createdAt: Date
  updatedAt: Date
}

export interface DisasterRecoveryProcedure {
  id: string
  name: string
  description: string
  order: number
  automated: boolean
  estimatedDuration: number // minutes
  dependencies: string[]
  commands?: string[]
  manualSteps?: string[]
  verificationSteps: string[]
  responsible: string
}

// Dashboard and Analytics Types for Epic 4
export interface Epic4Analytics {
  compliance: {
    gdprRequests: number
    gdprResponseTime: number
    consentRate: number
    dataRetentionCompliance: number
  }
  security: {
    auditEvents: number
    securityIncidents: number
    failedLogins: number
    ssoUsage: number
  }
  customization: {
    activeTenants: number
    whitelabelUsage: number
    customWorkflows: number
    brandingCustomization: number
  }
  performance: {
    apiLatency: number
    errorRate: number
    uptime: number
    backupSuccess: number
  }
}

// All interfaces are already exported above