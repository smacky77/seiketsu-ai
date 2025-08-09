// Role-Based Access Control (RBAC) Service
import type {
  Permission,
  Role,
  UserRole,
  AccessControlPolicy,
  AccessControlRule
} from '../../types/epic4'
import { apiClient } from '../api/client'

export class RBACService {
  private readonly baseUrl = '/api/rbac'

  // Permission Management
  async getPermissions(resource?: string): Promise<Permission[]> {
    const params = resource ? `?resource=${resource}` : ''
    const response = await apiClient.get<Permission[]>(`${this.baseUrl}/permissions${params}`)
    return response.data
  }

  async createPermission(permission: Omit<Permission, 'id'>): Promise<Permission> {
    const response = await apiClient.post<Permission>(`${this.baseUrl}/permissions`, permission)
    return response.data
  }

  async updatePermission(permissionId: string, updates: Partial<Permission>): Promise<Permission> {
    const response = await apiClient.put<Permission>(`${this.baseUrl}/permissions/${permissionId}`, updates)
    return response.data
  }

  async deletePermission(permissionId: string): Promise<void> {
    const response = await apiClient.delete<void>(`${this.baseUrl}/permissions/${permissionId}`)
    return response.data
  }

  // Role Management
  async getRoles(tenantId?: string): Promise<Role[]> {
    const params = tenantId ? `?tenantId=${tenantId}` : ''
    const response = await apiClient.get<Role[]>(`${this.baseUrl}/roles${params}`)
    return response.data
  }

  async getRole(roleId: string): Promise<Role> {
    const response = await apiClient.get<Role>(`${this.baseUrl}/roles/${roleId}`)
    return response.data
  }

  async createRole(role: Omit<Role, 'id' | 'createdAt' | 'updatedAt'>): Promise<Role> {
    const response = await apiClient.post<Role>(`${this.baseUrl}/roles`, {
      ...role,
      createdAt: new Date(),
      updatedAt: new Date()
    })
    return response.data
  }

  async updateRole(roleId: string, updates: Partial<Role>): Promise<Role> {
    const response = await apiClient.put<Role>(`${this.baseUrl}/roles/${roleId}`, {
      ...updates,
      updatedAt: new Date()
    })
    return response.data
  }

  async deleteRole(roleId: string): Promise<void> {
    const response = await apiClient.delete<void>(`${this.baseUrl}/roles/${roleId}`)
    return response.data
  }

  async cloneRole(roleId: string, newName: string, tenantId?: string): Promise<Role> {
    const response = await apiClient.post<Role>(`${this.baseUrl}/roles/${roleId}/clone`, {
      name: newName,
      tenantId
    })
    return response.data
  }

  // User Role Assignment
  async getUserRoles(userId: string): Promise<UserRole[]> {
    const response = await apiClient.get<UserRole[]>(`${this.baseUrl}/users/${userId}/roles`)
    return response.data
  }

  async assignRole(userRole: Omit<UserRole, 'assignedAt'>): Promise<UserRole> {
    const response = await apiClient.post<UserRole>(`${this.baseUrl}/users/${userRole.userId}/roles`, {
      ...userRole,
      assignedAt: new Date()
    })
    return response.data
  }

  async unassignRole(userId: string, roleId: string, tenantId?: string): Promise<void> {
    const params = tenantId ? `?tenantId=${tenantId}` : ''
    const response = await apiClient.delete<void>(
      `${this.baseUrl}/users/${userId}/roles/${roleId}${params}`
    )
    return response.data
  }

  async updateUserRole(userId: string, roleId: string, updates: Partial<UserRole>): Promise<UserRole> {
    const response = await apiClient.put<UserRole>(
      `${this.baseUrl}/users/${userId}/roles/${roleId}`,
      updates
    )
    return response.data
  }

  // Permission Checking
  async checkPermission(
    userId: string,
    resource: string,
    action: string,
    context?: Record<string, any>
  ): Promise<{
    granted: boolean
    reason: string
    matchedRole?: string
    matchedPermission?: string
    conditions?: Record<string, any>
  }> {
    const response = await apiClient.post<{
      granted: boolean
      reason: string
      matchedRole?: string
      matchedPermission?: string
      conditions?: Record<string, any>
    }>(`${this.baseUrl}/check-permission`, {
      userId,
      resource,
      action,
      context
    })
    return response.data
  }

  async checkMultiplePermissions(
    userId: string,
    permissions: Array<{
      resource: string
      action: string
      context?: Record<string, any>
    }>
  ): Promise<Array<{
    resource: string
    action: string
    granted: boolean
    reason: string
  }>> {
    const response = await apiClient.post<Array<{
      resource: string
      action: string
      granted: boolean
      reason: string
    }>>(`${this.baseUrl}/check-permissions`, {
      userId,
      permissions
    })
    return response.data
  }

  async getUserPermissions(userId: string, tenantId?: string): Promise<{
    permissions: Permission[]
    roles: Array<{
      roleId: string
      roleName: string
      permissions: Permission[]
    }>
    effectivePermissions: Permission[]
  }> {
    const params = tenantId ? `?tenantId=${tenantId}` : ''
    const response = await apiClient.get<{
      permissions: Permission[]
      roles: Array<{
        roleId: string
        roleName: string
        permissions: Permission[]
      }>
      effectivePermissions: Permission[]
    }>(`${this.baseUrl}/users/${userId}/permissions${params}`)
    return response.data
  }

  // Access Control Policies
  async getPolicies(tenantId?: string): Promise<AccessControlPolicy[]> {
    const params = tenantId ? `?tenantId=${tenantId}` : ''
    const response = await apiClient.get<AccessControlPolicy[]>(`${this.baseUrl}/policies${params}`)
    return response.data
  }

  async createPolicy(policy: Omit<AccessControlPolicy, 'id' | 'createdAt'>): Promise<AccessControlPolicy> {
    const response = await apiClient.post<AccessControlPolicy>(`${this.baseUrl}/policies`, {
      ...policy,
      createdAt: new Date()
    })
    return response.data
  }

  async updatePolicy(policyId: string, updates: Partial<AccessControlPolicy>): Promise<AccessControlPolicy> {
    const response = await apiClient.put<AccessControlPolicy>(`${this.baseUrl}/policies/${policyId}`, updates)
    return response.data
  }

  async deletePolicy(policyId: string): Promise<void> {
    const response = await apiClient.delete<void>(`${this.baseUrl}/policies/${policyId}`)
    return response.data
  }

  async evaluatePolicy(
    policyId: string,
    context: {
      userId: string
      resource: string
      action: string
      tenantId?: string
      metadata?: Record<string, any>
    }
  ): Promise<{
    allowed: boolean
    matchedRules: AccessControlRule[]
    decision: 'allow' | 'deny' | 'not_applicable'
    reason: string
  }> {
    const response = await apiClient.post<{
      allowed: boolean
      matchedRules: AccessControlRule[]
      decision: 'allow' | 'deny' | 'not_applicable'
      reason: string
    }>(`${this.baseUrl}/policies/${policyId}/evaluate`, context)
    return response.data
  }

  // Role Templates and Presets
  async getRoleTemplates(): Promise<Array<{
    id: string
    name: string
    description: string
    category: 'admin' | 'user' | 'manager' | 'viewer' | 'custom'
    permissions: Permission[]
    isBuiltIn: boolean
    usage: number
  }>> {
    const response = await apiClient.get<Array<{
      id: string
      name: string
      description: string
      category: 'admin' | 'user' | 'manager' | 'viewer' | 'custom'
      permissions: Permission[]
      isBuiltIn: boolean
      usage: number
    }>>(`${this.baseUrl}/role-templates`)
    return response.data
  }

  async createRoleFromTemplate(
    templateId: string,
    roleName: string,
    tenantId?: string
  ): Promise<Role> {
    const response = await apiClient.post<Role>(`${this.baseUrl}/role-templates/${templateId}/create-role`, {
      name: roleName,
      tenantId
    })
    return response.data
  }

  // Resource Management
  async getResources(): Promise<Array<{
    name: string
    description: string
    actions: string[]
    scopes: string[]
    category: string
  }>> {
    const response = await apiClient.get<Array<{
      name: string
      description: string
      actions: string[]
      scopes: string[]
      category: string
    }>>(`${this.baseUrl}/resources`)
    return response.data
  }

  async registerResource(resource: {
    name: string
    description: string
    actions: string[]
    scopes?: string[]
    category: string
  }): Promise<void> {
    const response = await apiClient.post<void>(`${this.baseUrl}/resources`, resource)
    return response.data
  }

  // Audit and Analytics
  async getAccessLog(
    filters: {
      userId?: string
      resource?: string
      action?: string
      startDate?: Date
      endDate?: Date
      granted?: boolean
      limit?: number
      offset?: number
    } = {}
  ): Promise<{
    logs: Array<{
      id: string
      timestamp: Date
      userId: string
      resource: string
      action: string
      granted: boolean
      reason: string
      ipAddress: string
      userAgent: string
      context?: Record<string, any>
    }>
    total: number
    hasMore: boolean
  }> {
    const params = new URLSearchParams()
    if (filters.userId) params.set('userId', filters.userId)
    if (filters.resource) params.set('resource', filters.resource)
    if (filters.action) params.set('action', filters.action)
    if (filters.startDate) params.set('startDate', filters.startDate.toISOString())
    if (filters.endDate) params.set('endDate', filters.endDate.toISOString())
    if (filters.granted !== undefined) params.set('granted', filters.granted.toString())
    if (filters.limit) params.set('limit', filters.limit.toString())
    if (filters.offset) params.set('offset', filters.offset.toString())

    const response = await apiClient.get<{
      logs: Array<{
        id: string
        timestamp: Date
        userId: string
        resource: string
        action: string
        granted: boolean
        reason: string
        ipAddress: string
        userAgent: string
        context?: Record<string, any>
      }>
      total: number
      hasMore: boolean
    }>(`${this.baseUrl}/access-log?${params}`)
    return response.data
  }

  async getRoleAnalytics(
    tenantId?: string,
    period: '7d' | '30d' | '90d' = '30d'
  ): Promise<{
    totalRoles: number
    activeRoles: number
    mostUsedRoles: Array<{
      roleId: string
      roleName: string
      userCount: number
      lastUsed: Date
    }>
    permissionUsage: Array<{
      permission: string
      usageCount: number
      grantedCount: number
      deniedCount: number
    }>
    accessPatterns: Array<{
      resource: string
      action: string
      frequency: number
      successRate: number
    }>
    trends: Array<{
      date: string
      accessAttempts: number
      uniqueUsers: number
      successRate: number
    }>
  }> {
    const params = new URLSearchParams({ period })
    if (tenantId) params.set('tenantId', tenantId)

    const response = await apiClient.get<{
      totalRoles: number
      activeRoles: number
      mostUsedRoles: Array<{
        roleId: string
        roleName: string
        userCount: number
        lastUsed: Date
      }>
      permissionUsage: Array<{
        permission: string
        usageCount: number
        grantedCount: number
        deniedCount: number
      }>
      accessPatterns: Array<{
        resource: string
        action: string
        frequency: number
        successRate: number
      }>
      trends: Array<{
        date: string
        accessAttempts: number
        uniqueUsers: number
        successRate: number
      }>
    }>(`${this.baseUrl}/analytics?${params}`)
    return response.data
  }

  // Security and Compliance
  async detectRoleConflicts(tenantId?: string): Promise<Array<{
    userId: string
    conflictType: 'permission_conflict' | 'role_inheritance' | 'excessive_privileges'
    severity: 'low' | 'medium' | 'high' | 'critical'
    description: string
    affectedRoles: string[]
    affectedPermissions: string[]
    recommendation: string
  }>> {
    const params = tenantId ? `?tenantId=${tenantId}` : ''
    const response = await apiClient.get<Array<{
      userId: string
      conflictType: 'permission_conflict' | 'role_inheritance' | 'excessive_privileges'
      severity: 'low' | 'medium' | 'high' | 'critical'
      description: string
      affectedRoles: string[]
      affectedPermissions: string[]
      recommendation: string
    }>>(`${this.baseUrl}/security/conflicts${params}`)
    return response.data
  }

  async reviewPrivilegedAccess(tenantId?: string): Promise<Array<{
    userId: string
    userName: string
    roles: string[]
    privilegedPermissions: Permission[]
    riskScore: number // 0-100
    lastAccess: Date
    recommendations: string[]
  }>> {
    const params = tenantId ? `?tenantId=${tenantId}` : ''
    const response = await apiClient.get<Array<{
      userId: string
      userName: string
      roles: string[]
      privilegedPermissions: Permission[]
      riskScore: number
      lastAccess: Date
      recommendations: string[]
    }>>(`${this.baseUrl}/security/privileged-access${params}`)
    return response.data
  }

  async generateComplianceReport(
    tenantId?: string,
    standard: 'soc2' | 'iso27001' | 'gdpr' = 'soc2'
  ): Promise<{
    reportId: string
    standard: string
    generatedAt: Date
    compliance: {
      overallScore: number
      controlsEvaluated: number
      controlsPassed: number
      controlsFailed: number
    }
    findings: Array<{
      controlId: string
      status: 'compliant' | 'non_compliant' | 'partially_compliant'
      description: string
      evidence: string[]
      remediation: string[]
      priority: 'low' | 'medium' | 'high' | 'critical'
    }>
    recommendations: string[]
    downloadUrl: string
  }> {
    const params = new URLSearchParams({ standard })
    if (tenantId) params.set('tenantId', tenantId)

    const response = await apiClient.post<{
      reportId: string
      standard: string
      generatedAt: Date
      compliance: {
        overallScore: number
        controlsEvaluated: number
        controlsPassed: number
        controlsFailed: number
      }
      findings: Array<{
        controlId: string
        status: 'compliant' | 'non_compliant' | 'partially_compliant'
        description: string
        evidence: string[]
        remediation: string[]
        priority: 'low' | 'medium' | 'high' | 'critical'
      }>
      recommendations: string[]
      downloadUrl: string
    }>(`${this.baseUrl}/compliance/report?${params}`)
    return response.data
  }

  // Utility Methods
  async exportRoles(tenantId?: string): Promise<{
    exportUrl: string
    expiresAt: Date
    format: 'json' | 'csv' | 'xlsx'
  }> {
    const params = tenantId ? `?tenantId=${tenantId}` : ''
    const response = await apiClient.get<{
      exportUrl: string
      expiresAt: Date
      format: 'json' | 'csv' | 'xlsx'
    }>(`${this.baseUrl}/export${params}`)
    return response.data
  }

  async importRoles(
    file: File,
    tenantId?: string,
    options: {
      overwrite: boolean
      validateOnly: boolean
    } = { overwrite: false, validateOnly: false }
  ): Promise<{
    success: boolean
    imported: {
      roles: number
      permissions: number
      userAssignments: number
    }
    errors: string[]
    warnings: string[]
    validationResults?: Array<{
      item: string
      issues: string[]
      severity: 'error' | 'warning'
    }>
  }> {
    const formData = new FormData()
    formData.append('file', file)
    if (tenantId) formData.append('tenantId', tenantId)
    formData.append('options', JSON.stringify(options))

    const response = await apiClient.post<{
      success: boolean
      imported: {
        roles: number
        permissions: number
        userAssignments: number
      }
      errors: string[]
      warnings: string[]
      validationResults?: Array<{
        item: string
        issues: string[]
        severity: 'error' | 'warning'
      }>
    }>(`${this.baseUrl}/import`, formData)
    return response.data
  }
}

// Client-side permission checking utilities
export class ClientRBACUtils {
  private permissions: Permission[] = []
  private roles: string[] = []

  constructor(private rbacService: RBACService) {}

  async loadUserPermissions(userId: string, tenantId?: string): Promise<void> {
    try {
      const result = await this.rbacService.getUserPermissions(userId, tenantId)
      this.permissions = result.effectivePermissions
      this.roles = result.roles.map(r => r.roleId)
    } catch (error) {
      console.error('Failed to load user permissions:', error)
      this.permissions = []
      this.roles = []
    }
  }

  hasPermission(resource: string, action: string, scope?: string): boolean {
    return this.permissions.some(permission => 
      permission.resource === resource &&
      (permission.action === action || permission.action === '*') &&
      (!scope || !permission.scope || permission.scope === scope || permission.scope === 'global')
    )
  }

  hasRole(roleId: string): boolean {
    return this.roles.includes(roleId)
  }

  hasAnyRole(roleIds: string[]): boolean {
    return roleIds.some(roleId => this.roles.includes(roleId))
  }

  canAccess(component: string, action: string = 'read'): boolean {
    return this.hasPermission(component, action)
  }

  // React component helper
  renderIfAuthorized<T>(
    resource: string,
    action: string,
    component: T,
    fallback: T | null = null
  ): T | null {
    return this.hasPermission(resource, action) ? component : fallback
  }
}

export const rbacService = new RBACService()
export const clientRBAC = new ClientRBACUtils(rbacService)