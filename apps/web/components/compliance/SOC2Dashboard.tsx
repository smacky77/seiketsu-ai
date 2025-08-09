'use client'

import React, { useState, useEffect } from 'react'
import { Card } from '../ui/card'
import { Button } from '../ui/button'
import { soc2Service } from '../../lib/compliance/soc2.service'
import type { AuditLog, SecurityEvent } from '../../types/epic4'

interface SOC2DashboardProps {
  tenantId?: string
}

interface SecurityMetrics {
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
}

interface ControlStatus {
  controlId: string
  name: string
  category: 'security' | 'availability' | 'processing_integrity' | 'confidentiality' | 'privacy'
  status: 'compliant' | 'non_compliant' | 'partially_compliant'
  lastTested: Date
  nextTest: Date
  evidence: number
  findings: number
}

export function SOC2Dashboard({ tenantId }: SOC2DashboardProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'audit' | 'security' | 'controls' | 'reports'>('overview')
  const [metrics, setMetrics] = useState<SecurityMetrics | null>(null)
  const [recentAuditLogs, setRecentAuditLogs] = useState<AuditLog[]>([])
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([])
  const [controlsStatus, setControlsStatus] = useState<ControlStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [timeframe, setTimeframe] = useState<'24h' | '7d' | '30d'>('7d')

  useEffect(() => {
    loadDashboardData()
  }, [tenantId, timeframe])

  const loadDashboardData = async () => {
    setLoading(true)
    try {
      const endDate = new Date()
      const startDate = new Date()
      
      switch (timeframe) {
        case '24h':
          startDate.setHours(startDate.getHours() - 24)
          break
        case '7d':
          startDate.setDate(startDate.getDate() - 7)
          break
        case '30d':
          startDate.setDate(startDate.getDate() - 30)
          break
      }

      const [securityMetrics, auditLogs, events] = await Promise.all([
        soc2Service.getSecurityMetrics({ start: startDate, end: endDate }),
        soc2Service.getAuditLogs({ 
          startDate, 
          endDate, 
          limit: 20 
        }),
        soc2Service.getSecurityEvents({ 
          startDate, 
          endDate, 
          limit: 10 
        })
      ])

      setMetrics(securityMetrics)
      setRecentAuditLogs(auditLogs.logs)
      setSecurityEvents(events)

      // Mock controls data
      const mockControls: ControlStatus[] = [
        {
          controlId: 'CC6.1',
          name: 'Logical Access Controls',
          category: 'security',
          status: 'compliant',
          lastTested: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000),
          nextTest: new Date(Date.now() + 25 * 24 * 60 * 60 * 1000),
          evidence: 15,
          findings: 0
        },
        {
          controlId: 'CC7.1',
          name: 'System Monitoring',
          category: 'availability',
          status: 'compliant',
          lastTested: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
          nextTest: new Date(Date.now() + 28 * 24 * 60 * 60 * 1000),
          evidence: 22,
          findings: 0
        },
        {
          controlId: 'PI1.1',
          name: 'Data Processing Integrity',
          category: 'processing_integrity',
          status: 'partially_compliant',
          lastTested: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000),
          nextTest: new Date(Date.now() + 20 * 24 * 60 * 60 * 1000),
          evidence: 8,
          findings: 2
        },
        {
          controlId: 'CC4.1',
          name: 'Data Confidentiality',
          category: 'confidentiality',
          status: 'compliant',
          lastTested: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
          nextTest: new Date(Date.now() + 23 * 24 * 60 * 60 * 1000),
          evidence: 18,
          findings: 0
        }
      ]
      setControlsStatus(mockControls)
    } catch (error) {
      console.error('Failed to load SOC2 dashboard data:', error)
    }
    setLoading(false)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'compliant':
        return 'bg-green-100 text-green-800'
      case 'partially_compliant':
        return 'bg-yellow-100 text-yellow-800'
      case 'non_compliant':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'low':
        return 'text-green-600'
      case 'medium':
        return 'text-yellow-600'
      case 'high':
        return 'text-orange-600'
      case 'critical':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  const formatDate = (date: Date | string) => {
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const tabs = [
    { id: 'overview' as const, label: 'Overview', icon: '📊' },
    { id: 'audit' as const, label: 'Audit Trail', icon: '📋' },
    { id: 'security' as const, label: 'Security Events', icon: '🔒' },
    { id: 'controls' as const, label: 'Controls', icon: '⚙️' },
    { id: 'reports' as const, label: 'Reports', icon: '📄' }
  ]

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading SOC 2 compliance dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">SOC 2 Compliance Dashboard</h1>
            <p className="text-gray-600">Monitor security controls, audit trails, and compliance status</p>
          </div>
          <div className="flex items-center gap-4">
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value as '24h' | '7d' | '30d')}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="24h">Last 24 hours</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
            </select>
            <Button
              onClick={loadDashboardData}
              variant="outline"
              size="sm"
            >
              Refresh
            </Button>
          </div>
        </div>

        {/* Key Metrics */}
        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Audit Events</p>
                  <p className="text-2xl font-bold text-gray-900">{metrics.auditEvents.total.toLocaleString()}</p>
                </div>
                <div className="text-blue-500">
                  📋
                </div>
              </div>
              <div className="mt-4 text-sm text-gray-500">
                Success: {metrics.auditEvents.byOutcome.success || 0} | 
                Failed: {metrics.auditEvents.byOutcome.failure || 0}
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Security Events</p>
                  <p className="text-2xl font-bold text-gray-900">{metrics.securityEvents.total}</p>
                </div>
                <div className="text-red-500">
                  🚨
                </div>
              </div>
              <div className="mt-4 text-sm text-gray-500">
                Resolved: {metrics.securityEvents.resolved} | 
                Open: {metrics.securityEvents.unresolved}
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Login Success Rate</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {metrics.accessControl.loginAttempts > 0 
                      ? Math.round((metrics.accessControl.successfulLogins / metrics.accessControl.loginAttempts) * 100)
                      : 0}%
                  </p>
                </div>
                <div className="text-green-500">
                  🔐
                </div>
              </div>
              <div className="mt-4 text-sm text-gray-500">
                {metrics.accessControl.successfulLogins} / {metrics.accessControl.loginAttempts} attempts
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Active Users</p>
                  <p className="text-2xl font-bold text-gray-900">{metrics.accessControl.uniqueUsers}</p>
                </div>
                <div className="text-purple-500">
                  👥
                </div>
              </div>
              <div className="mt-4 text-sm text-gray-500">
                Blocked IPs: {metrics.accessControl.blockedIPs}
              </div>
            </Card>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Controls Status */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Control Status Overview</h3>
                <div className="space-y-3">
                  {controlsStatus.map(control => (
                    <div key={control.controlId} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <div className="font-medium">{control.controlId} - {control.name}</div>
                        <div className="text-sm text-gray-600 capitalize">{control.category}</div>
                      </div>
                      <div className="text-right">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(control.status)}`}>
                          {control.status.replace('_', ' ')}
                        </span>
                        <div className="text-xs text-gray-500 mt-1">
                          Next test: {formatDate(control.nextTest)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Recent Security Events */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Recent Security Events</h3>
                <div className="space-y-3">
                  {securityEvents.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <div className="text-4xl mb-2">✅</div>
                      <p>No security events in the selected timeframe</p>
                    </div>
                  ) : (
                    securityEvents.map(event => (
                      <div key={event.id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div>
                          <div className="font-medium">{event.eventType}</div>
                          <div className="text-sm text-gray-600">{event.description}</div>
                          <div className="text-xs text-gray-500 mt-1">
                            {formatDate(event.timestamp)} • IP: {event.ipAddress}
                          </div>
                        </div>
                        <div className="text-right">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            event.severity === 'critical' ? 'bg-red-100 text-red-800' :
                            event.severity === 'error' ? 'bg-orange-100 text-orange-800' :
                            event.severity === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            {event.severity}
                          </span>
                          <div className="text-xs text-gray-500 mt-1">
                            {event.resolved ? '✅ Resolved' : '🔄 Open'}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </Card>
            </div>
          )}

          {activeTab === 'audit' && (
            <Card className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold">Audit Trail</h3>
                <div className="flex items-center gap-4">
                  <select className="px-3 py-2 border border-gray-300 rounded-md text-sm">
                    <option>All Actions</option>
                    <option>Authentication</option>
                    <option>Data Access</option>
                    <option>Configuration</option>
                  </select>
                  <select className="px-3 py-2 border border-gray-300 rounded-md text-sm">
                    <option>All Risk Levels</option>
                    <option>Critical</option>
                    <option>High</option>
                    <option>Medium</option>
                    <option>Low</option>
                  </select>
                </div>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Timestamp
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        User
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Action
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Resource
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Outcome
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Risk Level
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {recentAuditLogs.map(log => (
                      <tr key={log.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatDate(log.timestamp)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {log.userId || 'System'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {log.action}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {log.resource}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            log.outcome === 'success' ? 'bg-green-100 text-green-800' :
                            log.outcome === 'failure' ? 'bg-red-100 text-red-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {log.outcome}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`font-medium ${getRiskLevelColor(log.riskLevel)}`}>
                            {log.riskLevel.toUpperCase()}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {activeTab === 'controls' && (
            <div className="space-y-6">
              {controlsStatus.map(control => (
                <Card key={control.controlId} className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold">{control.controlId} - {control.name}</h3>
                      <p className="text-gray-600 capitalize">{control.category} Control</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(control.status)}`}>
                      {control.status.replace('_', ' ')}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-gray-600">Last Tested</p>
                      <p className="font-medium">{formatDate(control.lastTested)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Next Test</p>
                      <p className="font-medium">{formatDate(control.nextTest)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Evidence Items</p>
                      <p className="font-medium">{control.evidence}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Findings</p>
                      <p className={`font-medium ${control.findings > 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {control.findings}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      View Evidence
                    </Button>
                    <Button variant="outline" size="sm">
                      Run Test
                    </Button>
                    {control.findings > 0 && (
                      <Button variant="outline" size="sm" className="text-red-600">
                        View Findings
                      </Button>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}

          {activeTab === 'reports' && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Compliance Reports</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer">
                  <div className="text-2xl mb-2">📊</div>
                  <h4 className="font-medium mb-2">SOC 2 Type II Report</h4>
                  <p className="text-sm text-gray-600 mb-3">
                    Comprehensive compliance report covering all trust service criteria
                  </p>
                  <Button variant="outline" size="sm">Generate Report</Button>
                </div>
                
                <div className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer">
                  <div className="text-2xl mb-2">🔒</div>
                  <h4 className="font-medium mb-2">Security Controls Assessment</h4>
                  <p className="text-sm text-gray-600 mb-3">
                    Detailed assessment of security control effectiveness
                  </p>
                  <Button variant="outline" size="sm">Generate Report</Button>
                </div>
                
                <div className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer">
                  <div className="text-2xl mb-2">📋</div>
                  <h4 className="font-medium mb-2">Audit Log Summary</h4>
                  <p className="text-sm text-gray-600 mb-3">
                    Summary of audit events and security incidents
                  </p>
                  <Button variant="outline" size="sm">Generate Report</Button>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

export default SOC2Dashboard