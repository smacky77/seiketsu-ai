'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '../ui/button'
import { Card } from '../ui/card'
import ConsentManager from './ConsentManager'
import DataSubjectRights from './DataSubjectRights'
import { gdprService } from '../../lib/compliance/gdpr.service'
import type { PrivacySettings, GDPRConsent } from '../../types/epic4'

interface PrivacyDashboardProps {
  userId: string
}

interface PrivacyMetrics {
  dataProcessed: number
  consentGiven: number
  requestsSubmitted: number
  lastDataAccess: string
  dataRetentionDays: number
  cookiesActive: number
}

export function PrivacyDashboard({ userId }: PrivacyDashboardProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'consent' | 'rights' | 'settings' | 'history'>('overview')
  const [privacySettings, setPrivacySettings] = useState<PrivacySettings | null>(null)
  const [metrics, setMetrics] = useState<PrivacyMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [complianceScore, setComplianceScore] = useState<number>(0)

  useEffect(() => {
    loadPrivacyData()
  }, [userId])

  const loadPrivacyData = async () => {
    setLoading(true)
    try {
      const [settings, validation] = await Promise.all([
        gdprService.getPrivacySettings(userId).catch(() => null),
        gdprService.validateGDPRCompliance(userId)
      ])

      setPrivacySettings(settings)
      setComplianceScore(validation.score)

      // Load metrics
      const mockMetrics: PrivacyMetrics = {
        dataProcessed: 847,
        consentGiven: 3,
        requestsSubmitted: 0,
        lastDataAccess: '2024-01-15T10:30:00Z',
        dataRetentionDays: settings?.dataRetention.personalData || 365,
        cookiesActive: 12
      }
      setMetrics(mockMetrics)
    } catch (error) {
      console.error('Failed to load privacy data:', error)
    }
    setLoading(false)
  }

  const handlePrivacySettingsUpdate = async (updates: Partial<PrivacySettings>) => {
    try {
      const updatedSettings = await gdprService.updatePrivacySettings(userId, updates)
      setPrivacySettings(updatedSettings)
      
      await gdprService.logGDPREvent({
        userId,
        action: 'privacy_settings_updated',
        resource: 'privacy_dashboard',
        ipAddress: 'unknown',
        userAgent: navigator.userAgent,
        outcome: 'success',
        riskLevel: 'low',
        details: { updatedFields: Object.keys(updates) }
      })
    } catch (error) {
      console.error('Failed to update privacy settings:', error)
    }
  }

  const handleDataDownload = async () => {
    try {
      const dataExport = await gdprService.fulfillDataAccessRequest(userId)
      
      // Create download link
      const response = await fetch(dataExport.exportUrl)
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `my-data-export-${new Date().toISOString().split('T')[0]}.zip`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      await gdprService.logGDPREvent({
        userId,
        action: 'data_export_downloaded',
        resource: 'privacy_dashboard',
        ipAddress: 'unknown',
        userAgent: navigator.userAgent,
        outcome: 'success',
        riskLevel: 'medium',
        details: { exportUrl: dataExport.exportUrl }
      })
    } catch (error) {
      console.error('Failed to download data:', error)
      alert('Failed to generate data export. Please try again or contact support.')
    }
  }

  const getComplianceColor = (score: number) => {
    if (score >= 90) return 'text-green-600'
    if (score >= 70) return 'text-yellow-600'
    return 'text-red-600'
  }

  const tabs = [
    { id: 'overview' as const, label: 'Overview', icon: '📊' },
    { id: 'consent' as const, label: 'Consent', icon: '✅' },
    { id: 'rights' as const, label: 'Your Rights', icon: '🔒' },
    { id: 'settings' as const, label: 'Settings', icon: '⚙️' },
    { id: 'history' as const, label: 'Activity', icon: '📋' }
  ]

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your privacy dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Privacy Dashboard</h1>
          <p className="text-gray-600">
            Manage your data, privacy settings, and exercise your rights under GDPR
          </p>
        </div>

        {/* Privacy Score Card */}
        <Card className="p-6 mb-8 bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Privacy Compliance Score
              </h2>
              <p className="text-gray-600">
                Your current privacy and data protection status
              </p>
            </div>
            <div className="text-right">
              <div className={`text-4xl font-bold ${getComplianceColor(complianceScore)}`}>
                {complianceScore}%
              </div>
              <p className="text-sm text-gray-600">Compliance Level</p>
            </div>
          </div>
          
          <div className="mt-4 bg-gray-200 rounded-full h-3">
            <div 
              className={`h-3 rounded-full transition-all duration-500 ${
                complianceScore >= 90 ? 'bg-green-500' :
                complianceScore >= 70 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${complianceScore}%` }}
            />
          </div>
        </Card>

        {/* Quick Stats */}
        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card className="p-4 text-center">
              <div className="text-2xl font-bold text-blue-600">{metrics.dataProcessed}</div>
              <p className="text-gray-600 text-sm">Data Points Processed</p>
            </Card>
            <Card className="p-4 text-center">
              <div className="text-2xl font-bold text-green-600">{metrics.consentGiven}</div>
              <p className="text-gray-600 text-sm">Active Consents</p>
            </Card>
            <Card className="p-4 text-center">
              <div className="text-2xl font-bold text-purple-600">{metrics.requestsSubmitted}</div>
              <p className="text-gray-600 text-sm">Rights Requests</p>
            </Card>
            <Card className="p-4 text-center">
              <div className="text-2xl font-bold text-orange-600">{metrics.dataRetentionDays}</div>
              <p className="text-gray-600 text-sm">Days Retention</p>
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
            <div className="space-y-6">
              <Card className="p-6">
                <h2 className="text-xl font-semibold mb-4">Privacy Overview</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Data Processing</h3>
                    <p className="text-gray-600 text-sm mb-4">
                      We process your data for voice AI interactions, analytics, and service improvement.
                    </p>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Voice recordings:</span>
                        <span className="text-green-600">✓ Encrypted</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Conversation logs:</span>
                        <span className="text-green-600">✓ Anonymized</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Analytics data:</span>
                        <span className="text-green-600">✓ Aggregated</span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Your Controls</h3>
                    <div className="space-y-3">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleDataDownload}
                        className="w-full justify-start"
                      >
                        📥 Download My Data
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setActiveTab('consent')}
                        className="w-full justify-start"
                      >
                        ✅ Manage Consents
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setActiveTab('rights')}
                        className="w-full justify-start"
                      >
                        🔒 Exercise Your Rights
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>

              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between py-2 border-b">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span className="text-sm">Marketing consent updated</span>
                    </div>
                    <span className="text-xs text-gray-500">2 hours ago</span>
                  </div>
                  <div className="flex items-center justify-between py-2 border-b">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span className="text-sm">Privacy settings reviewed</span>
                    </div>
                    <span className="text-xs text-gray-500">1 day ago</span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                      <span className="text-sm">Voice data processed</span>
                    </div>
                    <span className="text-xs text-gray-500">3 days ago</span>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {activeTab === 'consent' && (
            <ConsentManager 
              userId={userId}
              showBanner={false}
              onConsentUpdate={loadPrivacyData}
            />
          )}

          {activeTab === 'rights' && (
            <DataSubjectRights
              userId={userId}
              onRequestSubmitted={loadPrivacyData}
            />
          )}

          {activeTab === 'settings' && privacySettings && (
            <div className="space-y-6">
              <Card className="p-6">
                <h2 className="text-xl font-semibold mb-4">Privacy Settings</h2>
                
                <div className="space-y-6">
                  {/* Data Processing Settings */}
                  <div>
                    <h3 className="font-medium text-gray-900 mb-3">Data Processing Preferences</h3>
                    <div className="space-y-3">
                      {Object.entries(privacySettings.dataProcessing).map(([key, value]) => (
                        <div key={key} className="flex items-center justify-between">
                          <label className="text-sm text-gray-700 capitalize">
                            {key.replace(/([A-Z])/g, ' $1').toLowerCase()}
                          </label>
                          <input
                            type="checkbox"
                            checked={value}
                            onChange={(e) => handlePrivacySettingsUpdate({
                              dataProcessing: {
                                ...privacySettings.dataProcessing,
                                [key]: e.target.checked
                              }
                            })}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Communication Settings */}
                  <div>
                    <h3 className="font-medium text-gray-900 mb-3">Communication Preferences</h3>
                    <div className="space-y-3">
                      {Object.entries(privacySettings.communication).map(([key, value]) => (
                        <div key={key} className="flex items-center justify-between">
                          <label className="text-sm text-gray-700 capitalize">
                            {key.replace(/([A-Z])/g, ' $1').toLowerCase()}
                          </label>
                          <input
                            type="checkbox"
                            checked={value}
                            onChange={(e) => handlePrivacySettingsUpdate({
                              communication: {
                                ...privacySettings.communication,
                                [key]: e.target.checked
                              }
                            })}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Data Retention Settings */}
                  <div>
                    <h3 className="font-medium text-gray-900 mb-3">Data Retention Periods</h3>
                    <div className="space-y-3">
                      {Object.entries(privacySettings.dataRetention).map(([key, value]) => (
                        <div key={key} className="flex items-center justify-between">
                          <label className="text-sm text-gray-700 capitalize">
                            {key.replace(/([A-Z])/g, ' $1').toLowerCase()} (days)
                          </label>
                          <select
                            value={value}
                            onChange={(e) => handlePrivacySettingsUpdate({
                              dataRetention: {
                                ...privacySettings.dataRetention,
                                [key]: parseInt(e.target.value)
                              }
                            })}
                            className="w-24 px-2 py-1 border border-gray-300 rounded text-sm"
                          >
                            <option value={30}>30 days</option>
                            <option value={90}>90 days</option>
                            <option value={180}>6 months</option>
                            <option value={365}>1 year</option>
                            <option value={730}>2 years</option>
                          </select>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {activeTab === 'history' && (
            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-4">Privacy Activity History</h2>
              <div className="space-y-4">
                <div className="text-center py-12 text-gray-500">
                  <div className="text-4xl mb-4">📋</div>
                  <p>Detailed activity history will be available soon.</p>
                  <p className="text-sm mt-2">This will show all privacy-related actions and data processing activities.</p>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

export default PrivacyDashboard