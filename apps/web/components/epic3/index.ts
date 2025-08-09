// Epic 3: Advanced Real Estate Market Intelligence & Automated Communication
// Component Index

// Main Dashboard Components
export { MarketIntelligenceDashboard } from './MarketIntelligenceDashboard'
export { CommunicationWorkflowPanel } from './CommunicationWorkflowPanel'
export { IntelligentSchedulingSystem } from './IntelligentSchedulingSystem'

// Monitoring & Analytics Components
export { SystemMonitoringDashboard } from './SystemMonitoringDashboard'
export { PerformanceMetrics } from './PerformanceMetrics'
export { AlertManagementPanel } from './AlertManagementPanel'

// Sub-components (can be exported if needed individually)
// Market Intelligence Sub-components
export type { MarketMetric, PropertyPrediction, CompetitorInsight } from '@/types/epic3'

// Communication Sub-components  
export type { EmailCampaign, SMSCampaign, CommunicationWorkflow } from '@/types/epic3'

// Scheduling Sub-components
export type { Agent, Appointment, TimeSlot, CalendarIntegration } from '@/types/epic3'

// Monitoring Sub-components
export type { SystemMetric, ServiceHealth, Alert, Incident } from '@/types/epic3'

// Component Props Types (for external consumption)
export interface Epic3ComponentProps {
  className?: string
  onDataChange?: (data: any) => void
  refreshInterval?: number
  theme?: 'light' | 'dark'
}

export interface MarketIntelligenceDashboardProps extends Epic3ComponentProps {
  location?: string
  timeframe?: '30d' | '90d' | '1y'
  showPredictions?: boolean
  showCompetitive?: boolean
}

export interface CommunicationWorkflowPanelProps extends Epic3ComponentProps {
  defaultTab?: 'email' | 'sms' | 'sequences' | 'personalization'
  showMetrics?: boolean
  enableCampaignManagement?: boolean
}

export interface IntelligentSchedulingSystemProps extends Epic3ComponentProps {
  defaultView?: 'appointments' | 'availability' | 'calendar' | 'automation'
  agentId?: string
  showCalendarIntegration?: boolean
}

export interface SystemMonitoringDashboardProps extends Epic3ComponentProps {
  autoRefresh?: boolean
  alertThreshold?: {
    cpu: number
    memory: number
    disk: number
    network: number
  }
}

export interface PerformanceMetricsProps extends Epic3ComponentProps {
  timeframe?: '1h' | '6h' | '24h' | '7d' | '30d'
  services?: string[]
  showComparison?: boolean
}

export interface AlertManagementPanelProps extends Epic3ComponentProps {
  defaultSeverity?: 'all' | 'critical' | 'high' | 'medium' | 'low'
  showResolved?: boolean
  enableBulkActions?: boolean
}

// Epic 3 Configuration Types
export interface Epic3Config {
  marketIntelligence: {
    enabled: boolean
    refreshInterval: number
    defaultLocation: string
    predictionsEnabled: boolean
    competitiveAnalysisEnabled: boolean
  }
  communication: {
    enabled: boolean
    emailCampaignsEnabled: boolean
    smsCampaignsEnabled: boolean
    workflowsEnabled: boolean
    personalizationEnabled: boolean
  }
  scheduling: {
    enabled: boolean
    calendarIntegrationEnabled: boolean
    smartSchedulingEnabled: boolean
    reminderSystemEnabled: boolean
  }
  monitoring: {
    enabled: boolean
    alertingEnabled: boolean
    incidentManagementEnabled: boolean
    performanceTrackingEnabled: boolean
  }
}

// Default Epic 3 Configuration
export const defaultEpic3Config: Epic3Config = {
  marketIntelligence: {
    enabled: true,
    refreshInterval: 300000, // 5 minutes
    defaultLocation: '',
    predictionsEnabled: true,
    competitiveAnalysisEnabled: true
  },
  communication: {
    enabled: true,
    emailCampaignsEnabled: true,
    smsCampaignsEnabled: true,
    workflowsEnabled: true,
    personalizationEnabled: true
  },
  scheduling: {
    enabled: true,
    calendarIntegrationEnabled: true,
    smartSchedulingEnabled: true,
    reminderSystemEnabled: true
  },
  monitoring: {
    enabled: true,
    alertingEnabled: true,
    incidentManagementEnabled: true,
    performanceTrackingEnabled: true
  }
}

// Epic 3 Feature Flags
export enum Epic3Features {
  MARKET_INTELLIGENCE = 'market_intelligence',
  PROPERTY_PREDICTIONS = 'property_predictions',
  COMPETITIVE_ANALYSIS = 'competitive_analysis',
  EMAIL_CAMPAIGNS = 'email_campaigns',
  SMS_CAMPAIGNS = 'sms_campaigns',
  COMMUNICATION_WORKFLOWS = 'communication_workflows',
  PERSONALIZATION = 'personalization',
  INTELLIGENT_SCHEDULING = 'intelligent_scheduling',
  CALENDAR_INTEGRATION = 'calendar_integration',
  APPOINTMENT_REMINDERS = 'appointment_reminders',
  SYSTEM_MONITORING = 'system_monitoring',
  PERFORMANCE_METRICS = 'performance_metrics',
  ALERT_MANAGEMENT = 'alert_management',
  INCIDENT_RESPONSE = 'incident_response'
}

// Utility function to check if feature is enabled
function checkEpic3FeatureEnabled(feature: Epic3Features, config: Epic3Config): boolean {
  switch (feature) {
    case Epic3Features.MARKET_INTELLIGENCE:
      return config.marketIntelligence.enabled
    case Epic3Features.PROPERTY_PREDICTIONS:
      return config.marketIntelligence.enabled && config.marketIntelligence.predictionsEnabled
    case Epic3Features.COMPETITIVE_ANALYSIS:
      return config.marketIntelligence.enabled && config.marketIntelligence.competitiveAnalysisEnabled
    case Epic3Features.EMAIL_CAMPAIGNS:
      return config.communication.enabled && config.communication.emailCampaignsEnabled
    case Epic3Features.SMS_CAMPAIGNS:
      return config.communication.enabled && config.communication.smsCampaignsEnabled
    case Epic3Features.COMMUNICATION_WORKFLOWS:
      return config.communication.enabled && config.communication.workflowsEnabled
    case Epic3Features.PERSONALIZATION:
      return config.communication.enabled && config.communication.personalizationEnabled
    case Epic3Features.INTELLIGENT_SCHEDULING:
      return config.scheduling.enabled
    case Epic3Features.CALENDAR_INTEGRATION:
      return config.scheduling.enabled && config.scheduling.calendarIntegrationEnabled
    case Epic3Features.APPOINTMENT_REMINDERS:
      return config.scheduling.enabled && config.scheduling.reminderSystemEnabled
    case Epic3Features.SYSTEM_MONITORING:
      return config.monitoring.enabled
    case Epic3Features.PERFORMANCE_METRICS:
      return config.monitoring.enabled && config.monitoring.performanceTrackingEnabled
    case Epic3Features.ALERT_MANAGEMENT:
      return config.monitoring.enabled && config.monitoring.alertingEnabled
    case Epic3Features.INCIDENT_RESPONSE:
      return config.monitoring.enabled && config.monitoring.incidentManagementEnabled
    default:
      return false
  }
}

export const isEpic3FeatureEnabled = checkEpic3FeatureEnabled

// Epic 3 Event Types for analytics and tracking
export enum Epic3Events {
  // Market Intelligence Events
  MARKET_ANALYSIS_REQUESTED = 'market_analysis_requested',
  PROPERTY_PREDICTION_GENERATED = 'property_prediction_generated',
  COMPETITIVE_ANALYSIS_VIEWED = 'competitive_analysis_viewed',
  MARKET_REPORT_GENERATED = 'market_report_generated',
  
  // Communication Events
  EMAIL_CAMPAIGN_CREATED = 'email_campaign_created',
  EMAIL_CAMPAIGN_SENT = 'email_campaign_sent',
  SMS_CAMPAIGN_CREATED = 'sms_campaign_created',
  SMS_CAMPAIGN_SENT = 'sms_campaign_sent',
  WORKFLOW_TRIGGERED = 'workflow_triggered',
  WORKFLOW_COMPLETED = 'workflow_completed',
  PERSONALIZATION_RULE_APPLIED = 'personalization_rule_applied',
  
  // Scheduling Events
  APPOINTMENT_BOOKED = 'appointment_booked',
  APPOINTMENT_RESCHEDULED = 'appointment_rescheduled',
  APPOINTMENT_CANCELLED = 'appointment_cancelled',
  CALENDAR_SYNCED = 'calendar_synced',
  REMINDER_SENT = 'reminder_sent',
  SMART_SUGGESTION_GENERATED = 'smart_suggestion_generated',
  
  // Monitoring Events
  ALERT_TRIGGERED = 'alert_triggered',
  ALERT_ACKNOWLEDGED = 'alert_acknowledged',
  ALERT_RESOLVED = 'alert_resolved',
  INCIDENT_CREATED = 'incident_created',
  INCIDENT_RESOLVED = 'incident_resolved',
  PERFORMANCE_THRESHOLD_BREACHED = 'performance_threshold_breached'
}

// Component Status Types
export enum ComponentStatus {
  LOADING = 'loading',
  READY = 'ready',
  ERROR = 'error',
  REFRESHING = 'refreshing'
}

// Utility functions exported above

// All types exported above