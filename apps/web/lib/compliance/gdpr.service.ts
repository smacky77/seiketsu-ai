// GDPR Compliance Service
import type {
  GDPRConsent,
  DataSubjectRequest,
  DataProcessingActivity,
  PrivacySettings,
  AuditLog
} from '../../types/epic4'
import { apiClient } from '../api/client'

export class GDPRService {
  private readonly baseUrl = '/api/compliance/gdpr'

  // Consent Management
  async recordConsent(consent: Omit<GDPRConsent, 'id' | 'timestamp'>): Promise<GDPRConsent> {
    const response = await apiClient.post<GDPRConsent>(`${this.baseUrl}/consent`, {
      ...consent,
      timestamp: new Date(),
      ipAddress: await this.getClientIP(),
      userAgent: navigator.userAgent
    })
    return response.data
  }

  async getConsent(userId: string, consentType?: string): Promise<GDPRConsent[]> {
    const params = new URLSearchParams()
    if (consentType) params.set('type', consentType)
    
    const response = await apiClient.get<GDPRConsent[]>(
      `${this.baseUrl}/consent/${userId}?${params}`
    )
    return response.data
  }

  async withdrawConsent(userId: string, consentType: string): Promise<void> {
    const response = await apiClient.put<void>(`${this.baseUrl}/consent/${userId}/withdraw`, {
      consentType,
      withdrawnAt: new Date()
    })
    return response.data
  }

  async checkConsentRequired(userId: string, purpose: string): Promise<boolean> {
    const response = await apiClient.get<{ required: boolean }>(
      `${this.baseUrl}/consent/${userId}/check?purpose=${purpose}`
    )
    return response.data.required
  }

  // Data Subject Rights
  async submitDataSubjectRequest(
    request: Omit<DataSubjectRequest, 'id' | 'requestedAt' | 'status' | 'verificationStatus'>
  ): Promise<DataSubjectRequest> {
    const response = await apiClient.post<DataSubjectRequest>(`${this.baseUrl}/requests`, {
      ...request,
      requestedAt: new Date(),
      status: 'pending',
      verificationStatus: 'pending'
    })
    return response.data
  }

  async getDataSubjectRequest(requestId: string): Promise<DataSubjectRequest> {
    const response = await apiClient.get<DataSubjectRequest>(`${this.baseUrl}/requests/${requestId}`)
    return response.data
  }

  async getUserDataSubjectRequests(userId: string): Promise<DataSubjectRequest[]> {
    const response = await apiClient.get<DataSubjectRequest[]>(`${this.baseUrl}/requests/user/${userId}`)
    return response.data
  }

  async processDataSubjectRequest(requestId: string, action: 'approve' | 'reject', notes?: string): Promise<void> {
    const response = await apiClient.put<void>(`${this.baseUrl}/requests/${requestId}/process`, {
      action,
      notes,
      processedAt: new Date()
    })
    return response.data
  }

  // Data Access Request (Article 15)
  async fulfillDataAccessRequest(userId: string): Promise<{
    personalData: Record<string, any>
    processingActivities: DataProcessingActivity[]
    consents: GDPRConsent[]
    exportUrl: string
  }> {
    const response = await apiClient.get<{
      personalData: Record<string, any>
      processingActivities: DataProcessingActivity[]
      consents: GDPRConsent[]
      exportUrl: string
    }>(`${this.baseUrl}/data-access/${userId}`)
    return response.data
  }

  // Data Portability Request (Article 20)
  async fulfillDataPortabilityRequest(userId: string, format: 'json' | 'csv' | 'xml' = 'json'): Promise<{
    downloadUrl: string
    expiresAt: Date
  }> {
    const response = await apiClient.post<{
      downloadUrl: string
      expiresAt: Date
    }>(`${this.baseUrl}/data-portability/${userId}`, { format })
    return response.data
  }

  // Right to Erasure (Article 17)
  async fulfillErasureRequest(userId: string, retainLegal: boolean = true): Promise<{
    deletedRecords: Record<string, number>
    retainedRecords: Record<string, number>
    anonymizedRecords: Record<string, number>
  }> {
    const response = await apiClient.delete<{
      deletedRecords: Record<string, number>
      retainedRecords: Record<string, number>
      anonymizedRecords: Record<string, number>
    }>(`${this.baseUrl}/erasure/${userId}?retainLegal=${retainLegal}`)
    return response.data
  }

  // Privacy Settings Management
  async getPrivacySettings(userId: string): Promise<PrivacySettings> {
    const response = await apiClient.get<PrivacySettings>(`${this.baseUrl}/privacy-settings/${userId}`)
    return response.data
  }

  async updatePrivacySettings(userId: string, settings: Partial<PrivacySettings>): Promise<PrivacySettings> {
    const response = await apiClient.put<PrivacySettings>(`${this.baseUrl}/privacy-settings/${userId}`, {
      ...settings,
      updatedAt: new Date()
    })
    return response.data
  }

  // Data Processing Activities (Article 30)
  async getProcessingActivities(tenantId?: string): Promise<DataProcessingActivity[]> {
    const params = tenantId ? `?tenantId=${tenantId}` : ''
    const response = await apiClient.get<DataProcessingActivity[]>(`${this.baseUrl}/processing-activities${params}`)
    return response.data
  }

  async createProcessingActivity(activity: Omit<DataProcessingActivity, 'id' | 'lastReviewed'>): Promise<DataProcessingActivity> {
    const response = await apiClient.post<DataProcessingActivity>(`${this.baseUrl}/processing-activities`, {
      ...activity,
      lastReviewed: new Date()
    })
    return response.data
  }

  async updateProcessingActivity(activityId: string, updates: Partial<DataProcessingActivity>): Promise<DataProcessingActivity> {
    const response = await apiClient.put<DataProcessingActivity>(`${this.baseUrl}/processing-activities/${activityId}`, {
      ...updates,
      lastReviewed: new Date()
    })
    return response.data
  }

  // Breach Notification (Article 33/34)
  async reportDataBreach(breach: {
    description: string
    personalDataCategories: string[]
    affectedSubjects: number
    likelyConsequences: string
    measuresProposed: string
    containmentMeasures?: string
    recoveryMeasures?: string
    preventionMeasures?: string
  }): Promise<{ breachId: string; reportingDeadline: Date }> {
    const response = await apiClient.post<{ breachId: string; reportingDeadline: Date }>(
      `${this.baseUrl}/breach-notification`, 
      {
        ...breach,
        reportedAt: new Date(),
        discoveredAt: new Date()
      }
    )
    return response.data
  }

  // Cookie Consent Management
  async getCookieCategories(): Promise<Array<{
    category: string
    name: string
    description: string
    required: boolean
    cookies: Array<{
      name: string
      purpose: string
      duration: string
      type: 'first-party' | 'third-party'
    }>
  }>> {
    const response = await apiClient.get<Array<{
      category: string
      name: string
      description: string
      required: boolean
      cookies: Array<{
        name: string
        purpose: string
        duration: string
        type: 'first-party' | 'third-party'
      }>
    }>>(`${this.baseUrl}/cookie-categories`)
    return response.data
  }

  async setCookiePreferences(userId: string, preferences: Record<string, boolean>): Promise<void> {
    const response = await apiClient.post<void>(`${this.baseUrl}/cookie-preferences/${userId}`, {
      preferences,
      timestamp: new Date()
    })
    return response.data
  }

  async getCookiePreferences(userId: string): Promise<Record<string, boolean>> {
    const response = await apiClient.get<{ preferences: Record<string, boolean> }>(
      `${this.baseUrl}/cookie-preferences/${userId}`
    )
    return response.data.preferences
  }

  // Legal Basis Assessment
  async assessLegalBasis(
    dataType: string, 
    purpose: string, 
    userId?: string
  ): Promise<{
    legalBasis: 'consent' | 'contract' | 'legal_obligation' | 'vital_interests' | 'public_task' | 'legitimate_interests'
    requiresConsent: boolean
    consentGranted?: boolean
    reasoning: string
  }> {
    const response = await apiClient.post<{
      legalBasis: 'consent' | 'contract' | 'legal_obligation' | 'vital_interests' | 'public_task' | 'legitimate_interests'
      requiresConsent: boolean
      consentGranted?: boolean
      reasoning: string
    }>(`${this.baseUrl}/legal-basis-assessment`, {
      dataType,
      purpose,
      userId
    })
    return response.data
  }

  // Anonymization Services
  async anonymizeUserData(userId: string, dataTypes: string[]): Promise<{
    anonymizedRecords: Record<string, number>
    retainedFields: string[]
    anonymizationTechniques: Record<string, string>
  }> {
    const response = await apiClient.post<{
      anonymizedRecords: Record<string, number>
      retainedFields: string[]
      anonymizationTechniques: Record<string, string>
    }>(`${this.baseUrl}/anonymize/${userId}`, { dataTypes })
    return response.data
  }

  async checkAnonymizationCompliance(
    anonymizedData: Record<string, any>
  ): Promise<{
    isCompliant: boolean
    risks: Array<{
      type: string
      severity: 'low' | 'medium' | 'high'
      description: string
      mitigation: string
    }>
    score: number // 0-100
  }> {
    const response = await apiClient.post<{
      isCompliant: boolean
      risks: Array<{
        type: string
        severity: 'low' | 'medium' | 'high'
        description: string
        mitigation: string
      }>
      score: number
    }>(`${this.baseUrl}/anonymization-compliance-check`, { anonymizedData })
    return response.data
  }

  // Audit and Compliance Reporting
  async getComplianceReport(
    startDate: Date, 
    endDate: Date, 
    tenantId?: string
  ): Promise<{
    period: { start: Date; end: Date }
    metrics: {
      consentRequests: number
      consentGranted: number
      consentWithdrawn: number
      dataSubjectRequests: number
      averageResponseTime: number
      breachNotifications: number
      processingActivities: number
    }
    details: {
      requestsByType: Record<string, number>
      responseTimeByType: Record<string, number>
      consentByCategory: Record<string, { granted: number; withdrawn: number }>
    }
    recommendations: string[]
  }> {
    const params = new URLSearchParams({
      startDate: startDate.toISOString(),
      endDate: endDate.toISOString()
    })
    if (tenantId) params.set('tenantId', tenantId)

    const response = await apiClient.get<{
      period: { start: Date; end: Date }
      metrics: {
        consentRequests: number
        consentGranted: number
        consentWithdrawn: number
        dataSubjectRequests: number
        averageResponseTime: number
        breachNotifications: number
        processingActivities: number
      }
      details: {
        requestsByType: Record<string, number>
        responseTimeByType: Record<string, number>
        consentByCategory: Record<string, { granted: number; withdrawn: number }>
      }
      recommendations: string[]
    }>(`${this.baseUrl}/compliance-report?${params}`)
    return response.data
  }

  // Utility Methods
  private async getClientIP(): Promise<string> {
    try {
      const response = await fetch('https://api.ipify.org?format=json')
      const data = await response.json()
      return data.ip || 'unknown'
    } catch {
      return 'unknown'
    }
  }

  async validateGDPRCompliance(userId: string): Promise<{
    isCompliant: boolean
    issues: Array<{
      severity: 'low' | 'medium' | 'high' | 'critical'
      category: string
      description: string
      remediation: string
    }>
    score: number // 0-100
    lastChecked: Date
  }> {
    const response = await apiClient.get<{
      isCompliant: boolean
      issues: Array<{
        severity: 'low' | 'medium' | 'high' | 'critical'
        category: string
        description: string
        remediation: string
      }>
      score: number
      lastChecked: Date
    }>(`${this.baseUrl}/compliance-validation/${userId}`)
    return response.data
  }

  // Event Logging for Audit Trail
  async logGDPREvent(event: Omit<AuditLog, 'id' | 'timestamp'>): Promise<void> {
    const response = await apiClient.post<void>(`${this.baseUrl}/audit-log`, {
      ...event,
      timestamp: new Date()
    })
    return response.data
  }
}

export const gdprService = new GDPRService()