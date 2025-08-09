// SOC 2 Compliance Service
import type {
  AuditLog,
  SecurityEvent,
  ComplianceMetrics
} from '../../types/epic4'
import { apiClient } from '../api/client'

export class SOC2Service {
  private readonly baseUrl = '/api/compliance/soc2'

  // Audit Logging (Security - A1.1)
  async createAuditLog(log: Omit<AuditLog, 'id' | 'timestamp'>): Promise<AuditLog> {
    const response = await apiClient.post<AuditLog>(`${this.baseUrl}/audit-logs`, {
      ...log,
      timestamp: new Date()
    })
    return response.data
  }

  async getAuditLogs(
    filters: {
      startDate?: Date
      endDate?: Date
      userId?: string
      action?: string
      resource?: string
      outcome?: 'success' | 'failure' | 'error'
      riskLevel?: 'low' | 'medium' | 'high' | 'critical'
      limit?: number
      offset?: number
    } = {}
  ): Promise<{
    logs: AuditLog[]
    total: number
    hasMore: boolean
  }> {
    const params = new URLSearchParams()
    
    if (filters.startDate) params.set('startDate', filters.startDate.toISOString())
    if (filters.endDate) params.set('endDate', filters.endDate.toISOString())
    if (filters.userId) params.set('userId', filters.userId)
    if (filters.action) params.set('action', filters.action)
    if (filters.resource) params.set('resource', filters.resource)
    if (filters.outcome) params.set('outcome', filters.outcome)
    if (filters.riskLevel) params.set('riskLevel', filters.riskLevel)
    if (filters.limit) params.set('limit', filters.limit.toString())
    if (filters.offset) params.set('offset', filters.offset.toString())

    const response = await apiClient.get<{
      logs: AuditLog[]
      total: number
      hasMore: boolean
    }>(`${this.baseUrl}/audit-logs?${params}`)
    return response.data
  }

  async searchAuditLogs(
    query: string,
    filters: {
      startDate?: Date
      endDate?: Date
      limit?: number
    } = {}
  ): Promise<AuditLog[]> {
    const params = new URLSearchParams({ query })
    
    if (filters.startDate) params.set('startDate', filters.startDate.toISOString())
    if (filters.endDate) params.set('endDate', filters.endDate.toISOString())
    if (filters.limit) params.set('limit', filters.limit.toString())

    const response = await apiClient.get<AuditLog[]>(`${this.baseUrl}/audit-logs/search?${params}`)
    return response.data
  }

  // Security Event Management (Security - A1.2)
  async createSecurityEvent(event: Omit<SecurityEvent, 'id' | 'timestamp' | 'resolved'>): Promise<SecurityEvent> {
    const response = await apiClient.post<SecurityEvent>(`${this.baseUrl}/security-events`, {
      ...event,
      timestamp: new Date(),
      resolved: false
    })
    return response.data
  }

  async getSecurityEvents(
    filters: {
      startDate?: Date
      endDate?: Date
      eventType?: string
      severity?: 'info' | 'warning' | 'error' | 'critical'
      resolved?: boolean
      limit?: number
    } = {}
  ): Promise<SecurityEvent[]> {
    const params = new URLSearchParams()
    
    if (filters.startDate) params.set('startDate', filters.startDate.toISOString())
    if (filters.endDate) params.set('endDate', filters.endDate.toISOString())
    if (filters.eventType) params.set('eventType', filters.eventType)
    if (filters.severity) params.set('severity', filters.severity)
    if (filters.resolved !== undefined) params.set('resolved', filters.resolved.toString())
    if (filters.limit) params.set('limit', filters.limit.toString())

    const response = await apiClient.get<SecurityEvent[]>(`${this.baseUrl}/security-events?${params}`)
    return response.data
  }

  async resolveSecurityEvent(eventId: string, resolvedBy: string, resolution?: string): Promise<SecurityEvent> {
    const response = await apiClient.put<SecurityEvent>(`${this.baseUrl}/security-events/${eventId}/resolve`, {
      resolved: true,
      resolvedAt: new Date(),
      resolvedBy,
      resolution
    })
    return response.data
  }

  // Access Control Monitoring (Availability - CC6.1)
  async logAccessEvent(event: {
    userId?: string
    sessionId?: string
    action: string
    resource: string
    resourceId?: string
    ipAddress: string
    userAgent: string
    outcome: 'success' | 'failure' | 'error'
    metadata?: Record<string, any>
  }): Promise<void> {
    await this.createAuditLog({
      ...event,
      riskLevel: event.outcome === 'failure' ? 'medium' : 'low',
      details: event.metadata || {}
    })
  }

  async getFailedLoginAttempts(
    timeframe: { start: Date; end: Date },
    threshold: number = 5
  ): Promise<Array<{
    ipAddress: string
    userId?: string
    attempts: number
    lastAttempt: Date
    blocked: boolean
  }>> {
    const response = await apiClient.post<Array<{
      ipAddress: string
      userId?: string
      attempts: number
      lastAttempt: Date
      blocked: boolean
    }>>(`${this.baseUrl}/failed-logins`, {
      startDate: timeframe.start,
      endDate: timeframe.end,
      threshold
    })
    return response.data
  }

  // Change Management (Common Criteria - CC8.1)
  async logConfigurationChange(change: {
    userId: string
    component: string
    changeType: 'create' | 'update' | 'delete'
    oldValue?: any
    newValue?: any
    reason?: string
    approvedBy?: string
  }): Promise<void> {
    await this.createAuditLog({
      userId: change.userId,
      action: `config_${change.changeType}`,
      resource: 'system_configuration',
      resourceId: change.component,
      ipAddress: 'system',
      userAgent: 'system',
      outcome: 'success',
      riskLevel: 'high',
      details: {
        component: change.component,
        changeType: change.changeType,
        oldValue: change.oldValue,
        newValue: change.newValue,
        reason: change.reason,
        approvedBy: change.approvedBy
      }
    })
  }

  // Data Processing Monitoring (Processing Integrity - PI1.1)
  async logDataProcessingEvent(event: {
    userId?: string
    processType: string
    dataType: string
    recordCount: number
    processingResult: 'success' | 'partial' | 'failure'
    errorDetails?: string
    metadata?: Record<string, any>
  }): Promise<void> {
    await this.createAuditLog({
      userId: event.userId,
      action: `data_processing_${event.processType}`,
      resource: 'data_processor',
      resourceId: event.dataType,
      ipAddress: 'system',
      userAgent: 'system',
      outcome: event.processingResult === 'failure' ? 'error' : 'success',
      riskLevel: event.processingResult === 'failure' ? 'high' : 'low',
      details: {
        processType: event.processType,
        dataType: event.dataType,
        recordCount: event.recordCount,
        processingResult: event.processingResult,
        errorDetails: event.errorDetails,
        ...event.metadata
      }
    })
  }

  // System Monitoring (Availability - CC7.1)
  async logSystemEvent(event: {
    eventType: 'startup' | 'shutdown' | 'error' | 'performance' | 'maintenance'
    component: string
    severity: 'info' | 'warning' | 'error' | 'critical'
    description: string
    metrics?: Record<string, number>
    metadata?: Record<string, any>
  }): Promise<void> {
    await this.createSecurityEvent({
      eventType: 'system',
      severity: event.severity,
      userId: undefined,
      ipAddress: 'system',
      description: event.description,
      metadata: {
        component: event.component,
        eventSubtype: event.eventType,
        metrics: event.metrics,
        ...event.metadata
      }
    })
  }

  // Compliance Reporting
  async generateComplianceReport(
    startDate: Date,
    endDate: Date,
    tenantId?: string
  ): Promise<{
    period: { start: Date; end: Date }
    metrics: ComplianceMetrics
    controls: Array<{
      controlId: string
      name: string
      category: 'security' | 'availability' | 'processing_integrity' | 'confidentiality' | 'privacy'
      status: 'compliant' | 'non_compliant' | 'partially_compliant'
      evidence: string[]
      gaps: string[]
      remediation: string[]
    }>
    riskAssessment: {
      overallRisk: 'low' | 'medium' | 'high' | 'critical'
      riskFactors: Array<{
        factor: string
        impact: 'low' | 'medium' | 'high'
        probability: 'low' | 'medium' | 'high'
        mitigation: string
      }>
    }
    recommendations: Array<{
      priority: 'high' | 'medium' | 'low'
      category: string
      description: string
      implementationCost: 'low' | 'medium' | 'high'
      timeline: string
    }>
  }> {
    const params = new URLSearchParams({
      startDate: startDate.toISOString(),
      endDate: endDate.toISOString()
    })
    if (tenantId) params.set('tenantId', tenantId)

    const response = await apiClient.get<{
      period: { start: Date; end: Date }
      metrics: ComplianceMetrics
      controls: Array<{
        controlId: string
        name: string
        category: 'security' | 'availability' | 'processing_integrity' | 'confidentiality' | 'privacy'
        status: 'compliant' | 'non_compliant' | 'partially_compliant'
        evidence: string[]
        gaps: string[]
        remediation: string[]
      }>
      riskAssessment: {
        overallRisk: 'low' | 'medium' | 'high' | 'critical'
        riskFactors: Array<{
          factor: string
          impact: 'low' | 'medium' | 'high'
          probability: 'low' | 'medium' | 'high'
          mitigation: string
        }>
      }
      recommendations: Array<{
        priority: 'high' | 'medium' | 'low'
        category: string
        description: string
        implementationCost: 'low' | 'medium' | 'high'
        timeline: string
      }>
    }>(`${this.baseUrl}/compliance-report?${params}`)
    return response.data
  }

  // Control Testing
  async executeControlTest(controlId: string, testData?: Record<string, any>): Promise<{
    testId: string
    controlId: string
    executedAt: Date
    result: 'pass' | 'fail' | 'partial'
    findings: Array<{
      severity: 'low' | 'medium' | 'high' | 'critical'
      description: string
      evidence: string
      remediation: string
    }>
    evidence: string[]
    nextTestDate: Date
  }> {
    const response = await apiClient.post<{
      testId: string
      controlId: string
      executedAt: Date
      result: 'pass' | 'fail' | 'partial'
      findings: Array<{
        severity: 'low' | 'medium' | 'high' | 'critical'
        description: string
        evidence: string
        remediation: string
      }>
      evidence: string[]
      nextTestDate: Date
    }>(`${this.baseUrl}/control-tests/${controlId}/execute`, {
      testData,
      executedAt: new Date()
    })
    return response.data
  }

  async getControlTestResults(
    controlId?: string,
    startDate?: Date,
    endDate?: Date
  ): Promise<Array<{
    testId: string
    controlId: string
    executedAt: Date
    result: 'pass' | 'fail' | 'partial'
    findings: number
    evidence: number
    tester: string
  }>> {
    const params = new URLSearchParams()
    if (controlId) params.set('controlId', controlId)
    if (startDate) params.set('startDate', startDate.toISOString())
    if (endDate) params.set('endDate', endDate.toISOString())

    const response = await apiClient.get<Array<{
      testId: string
      controlId: string
      executedAt: Date
      result: 'pass' | 'fail' | 'partial'
      findings: number
      evidence: number
      tester: string
    }>>(`${this.baseUrl}/control-tests?${params}`)
    return response.data
  }

  // Incident Response
  async createIncident(incident: {
    title: string
    description: string
    severity: 'low' | 'medium' | 'high' | 'critical'
    affectedSystems: string[]
    detectedBy: string
    metadata?: Record<string, any>
  }): Promise<{
    incidentId: string
    status: 'open' | 'investigating' | 'resolved' | 'closed'
    createdAt: Date
    assignedTo?: string
  }> {
    // Log as security event
    await this.createSecurityEvent({
      eventType: 'security_incident',
      severity: incident.severity === 'low' ? 'warning' : 
                incident.severity === 'medium' ? 'error' : 'critical',
      userId: incident.detectedBy,
      ipAddress: 'system',
      description: `Security incident: ${incident.title}`,
      metadata: {
        affectedSystems: incident.affectedSystems,
        ...incident.metadata
      }
    })

    const response = await apiClient.post<{
      incidentId: string
      status: 'open' | 'investigating' | 'resolved' | 'closed'
      createdAt: Date
      assignedTo?: string
    }>(`${this.baseUrl}/incidents`, {
      ...incident,
      status: 'open',
      createdAt: new Date()
    })
    return response.data
  }

  // Vulnerability Management
  async reportVulnerability(vulnerability: {
    title: string
    description: string
    severity: 'low' | 'medium' | 'high' | 'critical'
    component: string
    version?: string
    cveId?: string
    discoveredBy: string
    metadata?: Record<string, any>
  }): Promise<{
    vulnerabilityId: string
    status: 'open' | 'confirmed' | 'fixing' | 'fixed' | 'risk_accepted'
    createdAt: Date
  }> {
    // Log as security event
    await this.createSecurityEvent({
      eventType: 'security_incident',
      severity: vulnerability.severity === 'low' ? 'warning' : 
                vulnerability.severity === 'medium' ? 'error' : 'critical',
      userId: vulnerability.discoveredBy,
      ipAddress: 'system',
      description: `Vulnerability reported: ${vulnerability.title}`,
      metadata: {
        component: vulnerability.component,
        version: vulnerability.version,
        cveId: vulnerability.cveId,
        ...vulnerability.metadata
      }
    })

    const response = await apiClient.post<{
      vulnerabilityId: string
      status: 'open' | 'confirmed' | 'fixing' | 'fixed' | 'risk_accepted'
      createdAt: Date
    }>(`${this.baseUrl}/vulnerabilities`, {
      ...vulnerability,
      status: 'open',
      createdAt: new Date()
    })
    return response.data
  }

  // Metrics and Analytics
  async getSecurityMetrics(timeframe: { start: Date; end: Date }): Promise<{
    auditEvents: {
      total: number
      byRiskLevel: Record<string, number>
      byOutcome: Record<string, number>
      byResource: Record<string, number>
    }
    securityEvents: {
      total: number
      bySeverity: Record<string, number>
      byType: Record<string, number>
      resolved: number
      unresolved: number
    }
    accessControl: {
      loginAttempts: number
      successfulLogins: number
      failedLogins: number
      uniqueUsers: number
      blockedIPs: number
    }
    trends: {
      dailyEvents: Array<{ date: string; count: number }>
      topRisks: Array<{ risk: string; count: number }>
      topResources: Array<{ resource: string; count: number }>
    }
  }> {
    const params = new URLSearchParams({
      startDate: timeframe.start.toISOString(),
      endDate: timeframe.end.toISOString()
    })

    const response = await apiClient.get<{
      auditEvents: {
        total: number
        byRiskLevel: Record<string, number>
        byOutcome: Record<string, number>
        byResource: Record<string, number>
      }
      securityEvents: {
        total: number
        bySeverity: Record<string, number>
        byType: Record<string, number>
        resolved: number
        unresolved: number
      }
      accessControl: {
        loginAttempts: number
        successfulLogins: number
        failedLogins: number
        uniqueUsers: number
        blockedIPs: number
      }
      trends: {
        dailyEvents: Array<{ date: string; count: number }>
        topRisks: Array<{ risk: string; count: number }>
        topResources: Array<{ resource: string; count: number }>
      }
    }>(`${this.baseUrl}/security-metrics?${params}`)
    return response.data
  }

  // Continuous Monitoring
  async healthCheck(): Promise<{
    status: 'healthy' | 'degraded' | 'unhealthy'
    timestamp: Date
    services: Array<{
      name: string
      status: 'up' | 'down' | 'degraded'
      responseTime: number
      lastCheck: Date
    }>
    metrics: {
      cpuUsage: number
      memoryUsage: number
      diskUsage: number
      networkLatency: number
    }
    alerts: number
    incidents: number
  }> {
    const response = await apiClient.get<{
      status: 'healthy' | 'degraded' | 'unhealthy'
      timestamp: Date
      services: Array<{
        name: string
        status: 'up' | 'down' | 'degraded'
        responseTime: number
        lastCheck: Date
      }>
      metrics: {
        cpuUsage: number
        memoryUsage: number
        diskUsage: number
        networkLatency: number
      }
      alerts: number
      incidents: number
    }>(`${this.baseUrl}/health`)
    return response.data
  }
}

export const soc2Service = new SOC2Service()