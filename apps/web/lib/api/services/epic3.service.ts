import { apiClient } from '../client'

// Market Intelligence Types
export interface MarketAnalysisRequest {
  location: string
  propertyType?: string
  priceRange?: {
    min: number
    max: number
  }
  timeframe?: '30d' | '90d' | '1y'
}

export interface PropertyValuePrediction {
  propertyId: string
  address: string
  currentValue: number
  predictedValue: number
  confidence: number
  timeframe: string
  factors: string[]
}

export interface MarketTrend {
  period: string
  averagePrice: number
  medianPrice: number
  volumeSold: number
  daysOnMarket: number
  priceChange: number
}

export interface CompetitiveAnalysis {
  competitor: string
  marketShare: number
  averageCommission: number
  clientSatisfaction: number
  strengths: string[]
  weaknesses: string[]
}

// Communication Types
export interface EmailCampaign {
  id: string
  name: string
  subject: string
  content: string
  status: 'draft' | 'scheduled' | 'active' | 'paused' | 'completed'
  scheduledAt?: Date
  metrics: {
    sent: number
    opened: number
    clicked: number
    bounced: number
    unsubscribed: number
  }
}

export interface SMSCampaign {
  id: string
  name: string
  message: string
  status: 'draft' | 'scheduled' | 'active' | 'paused' | 'completed'
  scheduledAt?: Date
  metrics: {
    sent: number
    delivered: number
    failed: number
    replied: number
  }
}

export interface CommunicationWorkflow {
  id: string
  name: string
  triggerType: 'property_view' | 'inquiry' | 'showing_request' | 'manual'
  steps: WorkflowStep[]
  active: boolean
  metrics: {
    triggered: number
    completed: number
    abandoned: number
  }
}

export interface WorkflowStep {
  id: string
  type: 'email' | 'sms' | 'call' | 'task' | 'delay'
  delay: number
  template: string
  conditions?: string[]
}

// Scheduling Types
export interface SchedulingAvailability {
  agentId: string
  date: string
  timeSlots: TimeSlot[]
}

export interface TimeSlot {
  startTime: string
  endTime: string
  available: boolean
  appointmentId?: string
}

export interface AppointmentBookingRequest {
  agentId: string
  clientName: string
  clientEmail: string
  clientPhone: string
  propertyId?: string
  appointmentType: 'showing' | 'consultation' | 'listing_appointment' | 'closing'
  scheduledTime: Date
  duration: number
  notes?: string
}

export interface AppointmentReminder {
  appointmentId: string
  reminderType: 'email' | 'sms' | 'push'
  scheduledFor: Date
  status: 'scheduled' | 'sent' | 'failed'
}

// Market Intelligence Service
export class MarketIntelligenceService {
  static async getMarketAnalysis(request: MarketAnalysisRequest) {
    const response = await apiClient.post('/api/v1/market-intelligence/analysis', request)
    return response.data
  }

  static async getPropertyPredictions(propertyIds: string[]) {
    const response = await apiClient.post('/api/v1/market-intelligence/predictions', {
      propertyIds
    })
    return response.data as PropertyValuePrediction[]
  }

  static async getMarketTrends(location: string, timeframe: string = '1y') {
    const response = await apiClient.get(`/api/v1/market-intelligence/trends`, {
      params: { location, timeframe }
    })
    return response.data as MarketTrend[]
  }

  static async getCompetitiveAnalysis(location: string) {
    const response = await apiClient.get(`/api/v1/market-intelligence/competitive`, {
      params: { location }
    })
    return response.data as CompetitiveAnalysis[]
  }

  static async generateMarketReport(request: MarketAnalysisRequest) {
    const response = await apiClient.post('/api/v1/market-intelligence/report', request)
    return response.data
  }
}

// Communication Service
export class CommunicationService {
  // Email Campaigns
  static async getEmailCampaigns() {
    const response = await apiClient.get('/api/v1/communication/email/campaigns')
    return response.data as EmailCampaign[]
  }

  static async createEmailCampaign(campaign: Partial<EmailCampaign>) {
    const response = await apiClient.post('/api/v1/communication/email/campaigns', campaign)
    return response.data as EmailCampaign
  }

  static async updateEmailCampaign(id: string, updates: Partial<EmailCampaign>) {
    const response = await apiClient.put(`/api/v1/communication/email/campaigns/${id}`, updates)
    return response.data as EmailCampaign
  }

  static async pauseEmailCampaign(id: string) {
    const response = await apiClient.post(`/api/v1/communication/email/campaigns/${id}/pause`)
    return response.data
  }

  static async resumeEmailCampaign(id: string) {
    const response = await apiClient.post(`/api/v1/communication/email/campaigns/${id}/resume`)
    return response.data
  }

  // SMS Campaigns
  static async getSMSCampaigns() {
    const response = await apiClient.get('/api/v1/communication/sms/campaigns')
    return response.data as SMSCampaign[]
  }

  static async createSMSCampaign(campaign: Partial<SMSCampaign>) {
    const response = await apiClient.post('/api/v1/communication/sms/campaigns', campaign)
    return response.data as SMSCampaign
  }

  static async updateSMSCampaign(id: string, updates: Partial<SMSCampaign>) {
    const response = await apiClient.put(`/api/v1/communication/sms/campaigns/${id}`, updates)
    return response.data as SMSCampaign
  }

  // Communication Workflows
  static async getWorkflows() {
    const response = await apiClient.get('/api/v1/communication/workflows')
    return response.data as CommunicationWorkflow[]
  }

  static async createWorkflow(workflow: Partial<CommunicationWorkflow>) {
    const response = await apiClient.post('/api/v1/communication/workflows', workflow)
    return response.data as CommunicationWorkflow
  }

  static async updateWorkflow(id: string, updates: Partial<CommunicationWorkflow>) {
    const response = await apiClient.put(`/api/v1/communication/workflows/${id}`, updates)
    return response.data as CommunicationWorkflow
  }

  static async triggerWorkflow(workflowId: string, leadId: string, context?: any) {
    const response = await apiClient.post(`/api/v1/communication/workflows/${workflowId}/trigger`, {
      leadId,
      context
    })
    return response.data
  }

  // Personalization
  static async getPersonalizationRules() {
    const response = await apiClient.get('/api/v1/communication/personalization/rules')
    return response.data
  }

  static async updatePersonalizationRules(rules: any) {
    const response = await apiClient.put('/api/v1/communication/personalization/rules', rules)
    return response.data
  }

  static async getOptimalSendTimes(audienceId?: string) {
    const response = await apiClient.get('/api/v1/communication/optimization/send-times', {
      params: { audienceId }
    })
    return response.data
  }
}

// Scheduling Service
export class SchedulingService {
  // Availability Management
  static async getAgentAvailability(agentId: string, startDate: string, endDate: string) {
    const response = await apiClient.get(`/api/v1/scheduling/availability/${agentId}`, {
      params: { startDate, endDate }
    })
    return response.data as SchedulingAvailability[]
  }

  static async updateAgentAvailability(agentId: string, availability: Partial<SchedulingAvailability>) {
    const response = await apiClient.put(`/api/v1/scheduling/availability/${agentId}`, availability)
    return response.data
  }

  static async getAvailableTimeSlots(agentId: string, date: string, duration: number) {
    const response = await apiClient.get(`/api/v1/scheduling/time-slots`, {
      params: { agentId, date, duration }
    })
    return response.data as TimeSlot[]
  }

  // Appointment Booking
  static async bookAppointment(booking: AppointmentBookingRequest) {
    const response = await apiClient.post('/api/v1/scheduling/appointments', booking)
    return response.data
  }

  static async getAppointments(agentId?: string, startDate?: string, endDate?: string) {
    const response = await apiClient.get('/api/v1/scheduling/appointments', {
      params: { agentId, startDate, endDate }
    })
    return response.data
  }

  static async updateAppointment(appointmentId: string, updates: any) {
    const response = await apiClient.put(`/api/v1/scheduling/appointments/${appointmentId}`, updates)
    return response.data
  }

  static async cancelAppointment(appointmentId: string, reason?: string) {
    const response = await apiClient.delete(`/api/v1/scheduling/appointments/${appointmentId}`)
    return response.data
  }

  // Reminders
  static async scheduleReminder(reminder: Omit<AppointmentReminder, 'status'>) {
    const response = await apiClient.post('/api/v1/scheduling/reminders', reminder)
    return response.data as AppointmentReminder
  }

  static async getReminders(appointmentId?: string) {
    const response = await apiClient.get('/api/v1/scheduling/reminders', {
      params: { appointmentId }
    })
    return response.data as AppointmentReminder[]
  }

  static async updateReminderSettings(settings: any) {
    const response = await apiClient.put('/api/v1/scheduling/reminders/settings', settings)
    return response.data
  }

  // Calendar Integration
  static async getCalendarIntegrations() {
    const response = await apiClient.get('/api/v1/scheduling/calendar/integrations')
    return response.data
  }

  static async connectCalendar(provider: string, credentials: any) {
    const response = await apiClient.post('/api/v1/scheduling/calendar/connect', {
      provider,
      credentials
    })
    return response.data
  }

  static async syncCalendar(integrationId: string) {
    const response = await apiClient.post(`/api/v1/scheduling/calendar/sync/${integrationId}`)
    return response.data
  }

  static async disconnectCalendar(integrationId: string) {
    const response = await apiClient.delete(`/api/v1/scheduling/calendar/integrations/${integrationId}`)
    return response.data
  }

  // Smart Scheduling
  static async getSmartSuggestions(requirements: any) {
    const response = await apiClient.post('/api/v1/scheduling/smart/suggestions', requirements)
    return response.data
  }

  static async optimizeSchedule(agentId: string, date: string) {
    const response = await apiClient.post(`/api/v1/scheduling/smart/optimize`, {
      agentId,
      date
    })
    return response.data
  }
}

// Analytics and Monitoring
export class Epic3AnalyticsService {
  static async getSystemMetrics(timeframe: string = '24h') {
    const response = await apiClient.get('/api/v1/epic3/metrics/system', {
      params: { timeframe }
    })
    return response.data
  }

  static async getPerformanceMetrics(service?: string, timeframe: string = '24h') {
    const response = await apiClient.get('/api/v1/epic3/metrics/performance', {
      params: { service, timeframe }
    })
    return response.data
  }

  static async getServiceHealth() {
    const response = await apiClient.get('/api/v1/epic3/health')
    return response.data
  }

  static async getAlerts(status?: string, severity?: string) {
    const response = await apiClient.get('/api/v1/epic3/alerts', {
      params: { status, severity }
    })
    return response.data
  }

  static async acknowledgeAlert(alertId: string) {
    const response = await apiClient.post(`/api/v1/epic3/alerts/${alertId}/acknowledge`)
    return response.data
  }

  static async resolveAlert(alertId: string) {
    const response = await apiClient.post(`/api/v1/epic3/alerts/${alertId}/resolve`)
    return response.data
  }

  static async createIncident(incident: any) {
    const response = await apiClient.post('/api/v1/epic3/incidents', incident)
    return response.data
  }

  static async updateIncident(incidentId: string, updates: any) {
    const response = await apiClient.put(`/api/v1/epic3/incidents/${incidentId}`, updates)
    return response.data
  }
}

// Unified Epic 3 Service
export class Epic3Service {
  static market = MarketIntelligenceService
  static communication = CommunicationService
  static scheduling = SchedulingService
  static analytics = Epic3AnalyticsService
}