// Market Intelligence Types
export interface MarketMetric {
  label: string
  value: string
  change: number
  trend: 'up' | 'down' | 'stable'
  icon: React.ComponentType<any>
}

export interface PropertyPrediction {
  address: string
  currentValue: number
  predictedValue: number
  confidence: number
  timeframe: string
  factors?: string[]
}

export interface MarketTrendData {
  period: string
  averagePrice: number
  medianPrice: number
  volumeSold: number
  daysOnMarket: number
  priceChange: number
  inventory: number
}

export interface CompetitorInsight {
  competitor: string
  marketShare: number
  averageCommission: number
  clientSatisfaction: number
  strength: string
  weaknesses?: string[]
  recentActivity?: string
}

export interface MarketOpportunity {
  type: 'opportunity' | 'risk' | 'trend' | 'recommendation'
  title: string
  description: string
  impact: 'low' | 'medium' | 'high'
  confidence: number
  actionItems?: string[]
}

// Communication System Types
export interface EmailCampaignMetrics {
  sent: number
  opened: number
  clicked: number
  bounced: number
  unsubscribed: number
  leads: number
}

export interface EmailCampaign {
  id: string
  name: string
  subject: string
  content: string
  status: 'draft' | 'scheduled' | 'active' | 'paused' | 'completed'
  scheduledAt?: Date
  createdAt: Date
  metrics: EmailCampaignMetrics
  segmentation?: CampaignSegmentation
  template?: EmailTemplate
}

export interface SMSCampaignMetrics {
  sent: number
  delivered: number
  failed: number
  replied: number
  optedOut: number
}

export interface SMSCampaign {
  id: string
  name: string
  message: string
  status: 'draft' | 'scheduled' | 'active' | 'paused' | 'completed'
  scheduledAt?: Date
  createdAt: Date
  metrics: SMSCampaignMetrics
  segmentation?: CampaignSegmentation
}

export interface CampaignSegmentation {
  criteria: string
  audienceSize: number
  filters: SegmentationFilter[]
}

export interface SegmentationFilter {
  field: string
  operator: 'equals' | 'contains' | 'greater_than' | 'less_than' | 'in' | 'not_in'
  value: any
}

export interface EmailTemplate {
  id: string
  name: string
  subject: string
  content: string
  variables: string[]
  category: string
}

export interface WorkflowStep {
  id: string
  type: 'email' | 'sms' | 'call' | 'task' | 'delay' | 'condition'
  delay: number
  template?: string
  conditions?: WorkflowCondition[]
  nextSteps?: string[]
}

export interface WorkflowCondition {
  field: string
  operator: string
  value: any
}

export interface CommunicationWorkflow {
  id: string
  name: string
  description?: string
  triggerType: 'property_view' | 'inquiry' | 'showing_request' | 'manual' | 'time_based'
  triggerConditions?: WorkflowCondition[]
  steps: WorkflowStep[]
  active: boolean
  createdAt: Date
  metrics: {
    triggered: number
    completed: number
    abandoned: number
    conversionRate: number
  }
}

export interface PersonalizationRule {
  id: string
  name: string
  field: string
  template: string
  conditions?: WorkflowCondition[]
  priority: number
}

export interface OptimalTiming {
  channel: 'email' | 'sms'
  dayOfWeek: string
  timeOfDay: string
  timezone: string
  improvementPercentage: number
  confidence: number
}

// Scheduling System Types
export interface Agent {
  id: string
  name: string
  email: string
  phone: string
  status: 'available' | 'busy' | 'out_of_office'
  specializations: string[]
  avatar?: string
}

export interface TimeSlot {
  startTime: string
  endTime: string
  available: boolean
  appointmentId?: string
  bufferTime?: number
}

export interface SchedulingAvailability {
  agentId: string
  agent: Agent
  date: string
  timeSlots: TimeSlot[]
  workingHours: {
    start: string
    end: string
  }
  breaks: TimeSlot[]
}

export interface Appointment {
  id: string
  clientName: string
  clientPhone: string
  clientEmail: string
  propertyId?: string
  propertyAddress?: string
  appointmentType: 'showing' | 'consultation' | 'listing_appointment' | 'closing' | 'follow_up'
  scheduledTime: Date
  duration: number
  status: 'scheduled' | 'confirmed' | 'completed' | 'cancelled' | 'no_show'
  agentId: string
  agentName: string
  notes?: string
  createdAt: Date
  updatedAt: Date
  reminders: AppointmentReminder[]
}

export interface AppointmentReminder {
  id: string
  appointmentId: string
  reminderType: 'email' | 'sms' | 'push' | 'call'
  scheduledFor: Date
  status: 'scheduled' | 'sent' | 'failed' | 'cancelled'
  template?: string
  sentAt?: Date
}

export interface CalendarIntegration {
  id: string
  provider: 'google' | 'outlook' | 'apple' | 'calendly'
  agentId: string
  connected: boolean
  lastSync: Date
  eventsCount: number
  syncStatus: 'synced' | 'syncing' | 'error'
  credentials?: any
  settings: CalendarSettings
}

export interface CalendarSettings {
  syncDirection: 'both' | 'to_calendar' | 'from_calendar'
  bufferTime: number
  workingHours: {
    start: string
    end: string
  }
  workingDays: string[]
  timeZone: string
}

export interface SmartSchedulingSuggestion {
  agentId: string
  agentName: string
  suggestedTime: Date
  duration: number
  confidence: number
  factors: string[]
  alternatives: Date[]
}

export interface SchedulingRule {
  id: string
  name: string
  type: 'buffer_time' | 'travel_time' | 'workload_balance' | 'client_preference'
  parameters: any
  active: boolean
  priority: number
}

// System Monitoring Types
export interface SystemMetric {
  name: string
  value: number
  unit: string
  status: 'healthy' | 'warning' | 'critical'
  threshold: number
  icon: React.ComponentType<any>
  trend?: {
    direction: 'up' | 'down' | 'stable'
    change: number
    period: string
  }
}

export interface ServiceHealth {
  name: string
  status: 'online' | 'degraded' | 'offline'
  responseTime: number
  uptime: number
  lastCheck: Date
  endpoints?: EndpointHealth[]
}

export interface EndpointHealth {
  path: string
  status: number
  responseTime: number
  lastCheck: Date
}

export interface Alert {
  id: string
  title: string
  description: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  status: 'active' | 'acknowledged' | 'resolved'
  service: string
  timestamp: Date
  acknowledged_by?: string
  acknowledged_at?: Date
  resolved_at?: Date
  tags: string[]
  metadata?: any
}

export interface Incident {
  id: string
  title: string
  description: string
  status: 'investigating' | 'identified' | 'monitoring' | 'resolved'
  priority: 'p1' | 'p2' | 'p3' | 'p4'
  created_at: Date
  resolved_at?: Date
  assigned_to: string
  affected_services: string[]
  estimated_resolution?: Date
  timeline: IncidentTimelineEvent[]
}

export interface IncidentTimelineEvent {
  id: string
  timestamp: Date
  type: 'created' | 'updated' | 'assigned' | 'resolved' | 'commented'
  description: string
  author: string
}

export interface NotificationRule {
  id: string
  name: string
  description?: string
  conditions: string
  channels: ('email' | 'sms' | 'slack' | 'webhook' | 'push')[]
  active: boolean
  recipients: string[]
  cooldown?: number
  escalation?: NotificationEscalation[]
}

export interface NotificationEscalation {
  delay: number
  recipients: string[]
  channels: string[]
}

export interface PerformanceMetric {
  metric: string
  current: number
  previous: number
  unit: string
  trend: 'up' | 'down' | 'stable'
  target?: number
  status?: 'excellent' | 'good' | 'fair' | 'poor'
}

export interface APIEndpointMetric {
  endpoint: string
  method: string
  requests: number
  avgResponseTime: number
  errorRate: number
  throughput: number
  p95ResponseTime: number
  p99ResponseTime: number
}

// Analytics Types
export interface Epic3Analytics {
  marketIntelligence: {
    analysisRequests: number
    predictionAccuracy: number
    reportGeneration: number
    apiLatency: number
  }
  communication: {
    emailsSent: number
    smsDelivered: number
    engagementRate: number
    workflowCompletions: number
  }
  scheduling: {
    appointmentsBooked: number
    bookingSuccessRate: number
    noShowRate: number
    averageBookingTime: number
  }
  system: {
    uptime: number
    responseTime: number
    errorRate: number
    throughput: number
  }
}

// Dashboard Types
export interface DashboardWidget {
  id: string
  type: 'metric' | 'chart' | 'table' | 'map' | 'list'
  title: string
  size: 'small' | 'medium' | 'large'
  position: {
    x: number
    y: number
    width: number
    height: number
  }
  config: any
  dataSource: string
  refreshInterval?: number
}

export interface Dashboard {
  id: string
  name: string
  description?: string
  widgets: DashboardWidget[]
  layout: string
  permissions: string[]
  createdAt: Date
  updatedAt: Date
}

// All interfaces are already exported above
