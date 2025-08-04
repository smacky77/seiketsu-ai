// Enterprise Voice Agent Platform Types
export interface User {
  id: string
  email: string
  name: string
  avatar?: string
  role: UserRole
  organizationId: string
  permissions: Permission[]
  createdAt: Date
  updatedAt: Date
}

export interface Organization {
  id: string
  name: string
  slug: string
  domain?: string
  logo?: string
  settings: OrganizationSettings
  subscription: Subscription
  createdAt: Date
  updatedAt: Date
}

export interface OrganizationSettings {
  voiceSettings: VoiceSettings
  integrations: Integration[]
  branding: BrandingSettings
  security: SecuritySettings
}

export interface VoiceSettings {
  defaultVoice: string
  voiceSpeed: number
  language: string
  enableTranscription: boolean
  enableRecording: boolean
  maxCallDuration: number
}

export interface BrandingSettings {
  primaryColor: string
  logoUrl?: string
  companyName: string
  websiteUrl?: string
}

export interface SecuritySettings {
  requireMFA: boolean
  sessionTimeout: number
  allowedDomains: string[]
  ipWhitelist: string[]
}

export type UserRole = 'admin' | 'manager' | 'agent' | 'viewer'

export type Permission = 
  | 'agents.view'
  | 'agents.create'
  | 'agents.edit'
  | 'agents.delete'
  | 'leads.view'
  | 'leads.edit'
  | 'leads.export'
  | 'analytics.view'
  | 'settings.view'
  | 'settings.edit'
  | 'users.view'
  | 'users.manage'

// Voice Agent Types
export interface VoiceAgent {
  id: string
  name: string
  organizationId: string
  status: AgentStatus
  configuration: AgentConfiguration
  metrics: AgentMetrics
  createdAt: Date
  updatedAt: Date
}

export type AgentStatus = 'active' | 'inactive' | 'training' | 'error'

export interface AgentConfiguration {
  personality: PersonalitySettings
  knowledgeBase: KnowledgeBase
  integrations: AgentIntegration[]
  callFlow: CallFlow
}

export interface PersonalitySettings {
  name: string
  voice: string
  tone: 'professional' | 'friendly' | 'casual' | 'formal'
  language: string
  greetingMessage: string
  fallbackMessage: string
}

export interface KnowledgeBase {
  properties: Property[]
  marketData: MarketData[]
  companyInfo: CompanyInfo
  faqItems: FAQItem[]
}

export interface AgentIntegration {
  type: 'crm' | 'mls' | 'calendar' | 'email' | 'sms'
  config: Record<string, any>
  enabled: boolean
}

export interface CallFlow {
  steps: CallFlowStep[]
  conditions: CallFlowCondition[]
}

export interface CallFlowStep {
  id: string
  type: 'greeting' | 'question' | 'information' | 'transfer' | 'end'
  content: string
  nextStep?: string
  conditions?: string[]
}

export interface CallFlowCondition {
  id: string
  field: string
  operator: 'equals' | 'contains' | 'greater_than' | 'less_than'
  value: string
  nextStep: string
}

// Lead Management Types
export interface Lead {
  id: string
  organizationId: string
  status: LeadStatus
  score: number
  contact: ContactInfo
  preferences: LeadPreferences
  interactions: Interaction[]
  notes: Note[]
  createdAt: Date
  updatedAt: Date
}

export type LeadStatus = 'new' | 'qualified' | 'contacted' | 'scheduled' | 'converted' | 'lost'

export interface ContactInfo {
  firstName: string
  lastName: string
  email: string
  phone: string
  address?: Address
}

export interface Address {
  street: string
  city: string
  state: string
  zipCode: string
  country: string
}

export interface LeadPreferences {
  propertyType: PropertyType[]
  priceRange: PriceRange
  location: string[]
  bedrooms?: number
  bathrooms?: number
  features: string[]
}

export type PropertyType = 'single_family' | 'condo' | 'townhouse' | 'multi_family' | 'commercial' | 'land'

export interface PriceRange {
  min: number
  max: number
}

export interface Interaction {
  id: string
  type: InteractionType
  timestamp: Date
  duration?: number
  summary: string
  transcript?: string
  outcome: InteractionOutcome
  agentId?: string
  metadata: Record<string, any>
}

export type InteractionType = 'voice_call' | 'email' | 'sms' | 'chat' | 'meeting'
export type InteractionOutcome = 'positive' | 'neutral' | 'negative' | 'follow_up_required'

export interface Note {
  id: string
  content: string
  authorId: string
  createdAt: Date
  updatedAt: Date
}

// Property Types
export interface Property {
  id: string
  mlsId?: string
  address: Address
  details: PropertyDetails
  images: PropertyImage[]
  status: PropertyStatus
  listingAgent?: Agent
  createdAt: Date
  updatedAt: Date
}

export interface PropertyDetails {
  type: PropertyType
  price: number
  bedrooms: number
  bathrooms: number
  squareFootage: number
  lotSize?: number
  yearBuilt?: number
  features: string[]
  description: string
}

export interface PropertyImage {
  id: string
  url: string
  caption?: string
  isPrimary: boolean
}

export type PropertyStatus = 'active' | 'pending' | 'sold' | 'withdrawn'

export interface Agent {
  id: string
  name: string
  email: string
  phone: string
  licenseNumber?: string
  photo?: string
}

// Analytics Types
export interface AgentMetrics {
  totalCalls: number
  totalCallTime: number
  averageCallDuration: number
  qualificationRate: number
  conversionRate: number
  satisfactionScore: number
  leadsGenerated: number
  appointmentsScheduled: number
}

export interface DashboardMetrics {
  totalLeads: number
  qualifiedLeads: number
  conversionRate: number
  averageResponseTime: number
  activeAgents: number
  totalCallTime: number
  revenueGenerated: number
  appointmentsScheduled: number
}

// API Types
export interface ApiResponse<T> {
  data: T
  success: boolean
  message?: string
  errors?: string[]
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
}

// WebSocket Types
export interface WebSocketMessage {
  type: WebSocketMessageType
  data: any
  timestamp: Date
}

export type WebSocketMessageType = 
  | 'voice_status_update'
  | 'new_lead'
  | 'call_started'
  | 'call_ended'
  | 'agent_status_change'
  | 'notification'

// Voice Call Types
export interface VoiceCall {
  id: string
  agentId: string
  leadId?: string
  phoneNumber: string
  status: CallStatus
  startTime: Date
  endTime?: Date
  duration?: number
  transcript?: string
  recording?: string
  outcome?: CallOutcome
}

export type CallStatus = 'initiated' | 'ringing' | 'connected' | 'ended' | 'failed'

export interface CallOutcome {
  qualified: boolean
  appointmentScheduled: boolean
  followUpRequired: boolean
  notes: string
  nextAction?: string
}

// Integration Types
export interface Integration {
  id: string
  type: IntegrationType
  name: string
  config: IntegrationConfig
  status: IntegrationStatus
  lastSync?: Date
}

export type IntegrationType = 'crm' | 'mls' | 'calendar' | 'email' | 'sms' | 'webhook'
export type IntegrationStatus = 'connected' | 'disconnected' | 'error' | 'syncing'

export interface IntegrationConfig {
  apiKey?: string
  webhookUrl?: string
  settings: Record<string, any>
}

// Subscription Types
export interface Subscription {
  id: string
  plan: SubscriptionPlan
  status: SubscriptionStatus
  currentPeriodStart: Date
  currentPeriodEnd: Date
  usage: SubscriptionUsage
}

export type SubscriptionPlan = 'starter' | 'professional' | 'enterprise'
export type SubscriptionStatus = 'active' | 'past_due' | 'canceled' | 'trialing'

export interface SubscriptionUsage {
  voiceMinutes: number
  leadsProcessed: number
  agents: number
  integrations: number
}

// UI Component Types
export interface ComponentProps {
  className?: string
  children?: React.ReactNode
}

export interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

export interface TableColumn<T> {
  key: keyof T
  label: string
  sortable?: boolean
  render?: (value: any, item: T) => React.ReactNode
}

export interface FormField {
  name: string
  label: string
  type: 'text' | 'email' | 'tel' | 'textarea' | 'select' | 'checkbox' | 'radio'
  required?: boolean
  options?: SelectOption[]
  validation?: any
}

// Market Data Types
export interface MarketData {
  id: string
  area: string
  averagePrice: number
  medianPrice: number
  pricePerSqft: number
  daysOnMarket: number
  inventoryCount: number
  salesVolume: number
  priceChange: number
  updatedAt: Date
}

export interface CompanyInfo {
  name: string
  address: Address
  phone: string
  email: string
  website: string
  logo?: string
  description: string
}

export interface FAQItem {
  id: string
  question: string
  answer: string
  category: string
  order: number
}

// Error Types
export interface AppError {
  code: string
  message: string
  details?: Record<string, any>
}

// Theme Types
export type Theme = 'light' | 'dark' | 'system'

// Multi-tenant Types
export interface TenantContext {
  organization: Organization
  user: User
  permissions: Permission[]
}