'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Settings, 
  CreditCard, 
  Shield, 
  Zap, 
  Database,
  Globe,
  Bell,
  Lock,
  Key,
  Server,
  Wifi,
  HardDrive,
  Save,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Info,
  ExternalLink,
  Download,
  Upload
} from 'lucide-react'

interface ConfigSection {
  id: string
  title: string
  description: string
  icon: any
  critical: boolean
}

const configSections: ConfigSection[] = [
  {
    id: 'general',
    title: 'General Settings',
    description: 'Basic system configuration and preferences',
    icon: Settings,
    critical: false
  },
  {
    id: 'billing',
    title: 'Billing & Subscription',
    description: 'Manage your subscription plan and billing information',
    icon: CreditCard,
    critical: false
  },
  {
    id: 'security',
    title: 'Security & Access',
    description: 'Authentication, permissions, and security policies',
    icon: Shield,
    critical: true
  },
  {
    id: 'integrations',
    title: 'Integrations',
    description: 'Third-party services and API configurations',
    icon: Zap,
    critical: false
  },
  {
    id: 'data',
    title: 'Data Management',
    description: 'Backup, export, and data retention settings',
    icon: Database,
    critical: true
  },
  {
    id: 'notifications',
    title: 'Notifications',
    description: 'Alert settings and communication preferences',
    icon: Bell,
    critical: false
  }
]

interface SystemConfig {
  general: {
    companyName: string
    timezone: string
    dateFormat: string
    language: string
    businessHours: {
      start: string
      end: string
      timezone: string
    }
  }
  security: {
    passwordPolicy: {
      minLength: number
      requireUppercase: boolean
      requireNumbers: boolean
      requireSymbols: boolean
    }
    sessionTimeout: number
    twoFactorRequired: boolean
    ipRestrictions: string[]
  }
  integrations: {
    mls: {
      enabled: boolean
      provider: string
      apiKey: string
      lastSync: string
    }
    crm: {
      enabled: boolean
      provider: string
      webhookUrl: string
    }
    voiceProvider: {
      provider: string
      apiKey: string
      region: string
    }
  }
  notifications: {
    email: {
      enabled: boolean
      frequency: string
    }
    sms: {
      enabled: boolean
      provider: string
    }
    inApp: {
      enabled: boolean
      types: string[]
    }
  }
}

const mockConfig: SystemConfig = {
  general: {
    companyName: 'Premier Realty Group',
    timezone: 'America/New_York',
    dateFormat: 'MM/DD/YYYY',
    language: 'en-US',
    businessHours: {
      start: '09:00',
      end: '18:00',
      timezone: 'America/New_York'
    }
  },
  security: {
    passwordPolicy: {
      minLength: 8,
      requireUppercase: true,
      requireNumbers: true,
      requireSymbols: false
    },
    sessionTimeout: 30,
    twoFactorRequired: true,
    ipRestrictions: ['192.168.1.0/24', '10.0.0.0/8']
  },
  integrations: {
    mls: {
      enabled: true,
      provider: 'RETS',
      apiKey: '****-****-****-1234',
      lastSync: '2024-08-03T10:30:00Z'
    },
    crm: {
      enabled: true,
      provider: 'Salesforce',
      webhookUrl: 'https://api.company.com/webhook'
    },
    voiceProvider: {
      provider: 'ElevenLabs',
      apiKey: '****-****-****-5678',
      region: 'us-east-1'
    }
  },
  notifications: {
    email: {
      enabled: true,
      frequency: 'immediate'
    },
    sms: {
      enabled: false,
      provider: 'Twilio'
    },
    inApp: {
      enabled: true,
      types: ['lead_qualified', 'system_alerts', 'performance_updates']
    }
  }
}

export function SystemConfigurationPanel() {
  const [activeSection, setActiveSection] = useState('general')
  const [config, setConfig] = useState(mockConfig)
  const [hasChanges, setHasChanges] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  const handleSave = async () => {
    setIsSaving(true)
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    setIsSaving(false)
    setHasChanges(false)
  }

  const renderGeneralSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Company Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Company Name</label>
            <input
              type="text"
              value={config.general.companyName}
              onChange={(e) => {
                setConfig(prev => ({
                  ...prev,
                  general: { ...prev.general, companyName: e.target.value }
                }))
                setHasChanges(true)
              }}
              className="w-full px-3 py-2 bg-muted border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Timezone</label>
            <select
              value={config.general.timezone}
              onChange={(e) => {
                setConfig(prev => ({
                  ...prev,
                  general: { ...prev.general, timezone: e.target.value }
                }))
                setHasChanges(true)
              }}
              className="w-full px-3 py-2 bg-muted border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option value="America/New_York">Eastern Time</option>
              <option value="America/Chicago">Central Time</option>
              <option value="America/Denver">Mountain Time</option>
              <option value="America/Los_Angeles">Pacific Time</option>
            </select>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Business Hours</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Start Time</label>
            <input
              type="time"
              value={config.general.businessHours.start}
              onChange={(e) => {
                setConfig(prev => ({
                  ...prev,
                  general: { 
                    ...prev.general, 
                    businessHours: { ...prev.general.businessHours, start: e.target.value }
                  }
                }))
                setHasChanges(true)
              }}
              className="w-full px-3 py-2 bg-muted border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">End Time</label>
            <input
              type="time"
              value={config.general.businessHours.end}
              onChange={(e) => {
                setConfig(prev => ({
                  ...prev,
                  general: { 
                    ...prev.general, 
                    businessHours: { ...prev.general.businessHours, end: e.target.value }
                  }
                }))
                setHasChanges(true)
              }}
              className="w-full px-3 py-2 bg-muted border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Date Format</label>
            <select
              value={config.general.dateFormat}
              onChange={(e) => {
                setConfig(prev => ({
                  ...prev,
                  general: { ...prev.general, dateFormat: e.target.value }
                }))
                setHasChanges(true)
              }}
              className="w-full px-3 py-2 bg-muted border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option value="MM/DD/YYYY">MM/DD/YYYY</option>
              <option value="DD/MM/YYYY">DD/MM/YYYY</option>
              <option value="YYYY-MM-DD">YYYY-MM-DD</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  )

  const renderSecuritySettings = () => (
    <div className="space-y-6">
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
        <div>
          <div className="font-medium text-yellow-800">Security Configuration</div>
          <div className="text-sm text-yellow-700 mt-1">
            Changes to security settings affect all users and may require re-authentication.
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Password Policy</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Minimum Password Length</label>
            <input
              type="number"
              min="6"
              max="32"
              value={config.security.passwordPolicy.minLength}
              onChange={(e) => {
                setConfig(prev => ({
                  ...prev,
                  security: { 
                    ...prev.security, 
                    passwordPolicy: { 
                      ...prev.security.passwordPolicy, 
                      minLength: parseInt(e.target.value) 
                    }
                  }
                }))
                setHasChanges(true)
              }}
              className="w-32 px-3 py-2 bg-muted border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          
          <div className="space-y-2">
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={config.security.passwordPolicy.requireUppercase}
                onChange={(e) => {
                  setConfig(prev => ({
                    ...prev,
                    security: { 
                      ...prev.security, 
                      passwordPolicy: { 
                        ...prev.security.passwordPolicy, 
                        requireUppercase: e.target.checked 
                      }
                    }
                  }))
                  setHasChanges(true)
                }}
                className="w-4 h-4"
              />
              <span className="text-sm">Require uppercase letters</span>
            </label>
            
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={config.security.passwordPolicy.requireNumbers}
                onChange={(e) => {
                  setConfig(prev => ({
                    ...prev,
                    security: { 
                      ...prev.security, 
                      passwordPolicy: { 
                        ...prev.security.passwordPolicy, 
                        requireNumbers: e.target.checked 
                      }
                    }
                  }))
                  setHasChanges(true)
                }}
                className="w-4 h-4"
              />
              <span className="text-sm">Require numbers</span>
            </label>
            
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={config.security.passwordPolicy.requireSymbols}
                onChange={(e) => {
                  setConfig(prev => ({
                    ...prev,
                    security: { 
                      ...prev.security, 
                      passwordPolicy: { 
                        ...prev.security.passwordPolicy, 
                        requireSymbols: e.target.checked 
                      }
                    }
                  }))
                  setHasChanges(true)
                }}
                className="w-4 h-4"
              />
              <span className="text-sm">Require special characters</span>
            </label>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Session & Access</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Session Timeout (minutes)</label>
            <input
              type="number"
              min="5"
              max="480"
              value={config.security.sessionTimeout}
              onChange={(e) => {
                setConfig(prev => ({
                  ...prev,
                  security: { ...prev.security, sessionTimeout: parseInt(e.target.value) }
                }))
                setHasChanges(true)
              }}
              className="w-32 px-3 py-2 bg-muted border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          
          <div>
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={config.security.twoFactorRequired}
                onChange={(e) => {
                  setConfig(prev => ({
                    ...prev,
                    security: { ...prev.security, twoFactorRequired: e.target.checked }
                  }))
                  setHasChanges(true)
                }}
                className="w-4 h-4"
              />
              <span className="text-sm font-medium">Require Two-Factor Authentication</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  )

  const renderIntegrationSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">MLS Integration</h3>
        <div className="bg-muted rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className={`w-3 h-3 rounded-full ${config.integrations.mls.enabled ? 'bg-green-500' : 'bg-gray-400'}`} />
              <span className="font-medium">MLS Connection</span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={config.integrations.mls.enabled}
                onChange={(e) => {
                  setConfig(prev => ({
                    ...prev,
                    integrations: { 
                      ...prev.integrations, 
                      mls: { ...prev.integrations.mls, enabled: e.target.checked }
                    }
                  }))
                  setHasChanges(true)
                }}
                className="sr-only"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
          
          {config.integrations.mls.enabled && (
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium mb-1">Provider</label>
                <input
                  type="text"
                  value={config.integrations.mls.provider}
                  readOnly
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-muted-foreground"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">API Key</label>
                <input
                  type="password"
                  value={config.integrations.mls.apiKey}
                  onChange={(e) => {
                    setConfig(prev => ({
                      ...prev,
                      integrations: { 
                        ...prev.integrations, 
                        mls: { ...prev.integrations.mls, apiKey: e.target.value }
                      }
                    }))
                    setHasChanges(true)
                  }}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>
              <div className="text-sm text-muted-foreground">
                Last sync: {new Date(config.integrations.mls.lastSync).toLocaleString()}
              </div>
            </div>
          )}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Voice Provider</h3>
        <div className="bg-muted rounded-lg p-4 space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">Provider</label>
            <select
              value={config.integrations.voiceProvider.provider}
              onChange={(e) => {
                setConfig(prev => ({
                  ...prev,
                  integrations: { 
                    ...prev.integrations, 
                    voiceProvider: { ...prev.integrations.voiceProvider, provider: e.target.value }
                  }
                }))
                setHasChanges(true)
              }}
              className="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option value="ElevenLabs">ElevenLabs</option>
              <option value="OpenAI">OpenAI</option>
              <option value="Azure">Azure Cognitive Services</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Region</label>
            <select
              value={config.integrations.voiceProvider.region}
              onChange={(e) => {
                setConfig(prev => ({
                  ...prev,
                  integrations: { 
                    ...prev.integrations, 
                    voiceProvider: { ...prev.integrations.voiceProvider, region: e.target.value }
                  }
                }))
                setHasChanges(true)
              }}
              className="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option value="us-east-1">US East (N. Virginia)</option>
              <option value="us-west-2">US West (Oregon)</option>
              <option value="eu-west-1">Europe (Ireland)</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  )

  const renderNotificationSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Email Notifications</h3>
        <div className="bg-muted rounded-lg p-4 space-y-3">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={config.notifications.email.enabled}
              onChange={(e) => {
                setConfig(prev => ({
                  ...prev,
                  notifications: { 
                    ...prev.notifications, 
                    email: { ...prev.notifications.email, enabled: e.target.checked }
                  }
                }))
                setHasChanges(true)
              }}
              className="w-4 h-4"
            />
            <span className="font-medium">Enable Email Notifications</span>
          </label>
          
          {config.notifications.email.enabled && (
            <div>
              <label className="block text-sm font-medium mb-1">Frequency</label>
              <select
                value={config.notifications.email.frequency}
                onChange={(e) => {
                  setConfig(prev => ({
                    ...prev,
                    notifications: { 
                      ...prev.notifications, 
                      email: { ...prev.notifications.email, frequency: e.target.value }
                    }
                  }))
                  setHasChanges(true)
                }}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
              >
                <option value="immediate">Immediate</option>
                <option value="hourly">Hourly Digest</option>
                <option value="daily">Daily Digest</option>
                <option value="weekly">Weekly Summary</option>
              </select>
            </div>
          )}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">In-App Notifications</h3>
        <div className="bg-muted rounded-lg p-4 space-y-3">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={config.notifications.inApp.enabled}
              onChange={(e) => {
                setConfig(prev => ({
                  ...prev,
                  notifications: { 
                    ...prev.notifications, 
                    inApp: { ...prev.notifications.inApp, enabled: e.target.checked }
                  }
                }))
                setHasChanges(true)
              }}
              className="w-4 h-4"
            />
            <span className="font-medium">Enable In-App Notifications</span>
          </label>
          
          {config.notifications.inApp.enabled && (
            <div className="space-y-2">
              <div className="text-sm font-medium">Notification Types:</div>
              {['lead_qualified', 'system_alerts', 'performance_updates', 'team_activities'].map((type) => (
                <label key={type} className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={config.notifications.inApp.types.includes(type)}
                    onChange={(e) => {
                      const types = e.target.checked 
                        ? [...config.notifications.inApp.types, type]
                        : config.notifications.inApp.types.filter(t => t !== type)
                      setConfig(prev => ({
                        ...prev,
                        notifications: { 
                          ...prev.notifications, 
                          inApp: { ...prev.notifications.inApp, types }
                        }
                      }))
                      setHasChanges(true)
                    }}
                    className="w-4 h-4"
                  />
                  <span className="text-sm capitalize">{type.replace('_', ' ')}</span>
                </label>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )

  const renderContent = () => {
    switch (activeSection) {
      case 'general':
        return renderGeneralSettings()
      case 'security':
        return renderSecuritySettings()
      case 'integrations':
        return renderIntegrationSettings()
      case 'notifications':
        return renderNotificationSettings()
      default:
        return <div>Section under development</div>
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">System Configuration</h1>
          <p className="text-muted-foreground">
            Manage your system settings and preferences
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button className="btn btn-secondary">
            <Download className="w-4 h-4 mr-2" />
            Export Config
          </button>
          {hasChanges && (
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="btn btn-primary"
            >
              {isSaving ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Save className="w-4 h-4 mr-2" />
              )}
              {isSaving ? 'Saving...' : 'Save Changes'}
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Settings Navigation */}
        <div className="space-y-2">
          {configSections.map((section) => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={`w-full flex items-start gap-3 p-4 rounded-lg text-left transition-colors ${
                activeSection === section.id
                  ? 'bg-accent text-accent-foreground'
                  : 'hover:bg-muted'
              }`}
            >
              <div className={`flex-shrink-0 mt-1 ${section.critical ? 'text-red-500' : 'text-muted-foreground'}`}>
                <section.icon className="w-5 h-5" />
                {section.critical && (
                  <AlertTriangle className="w-3 h-3 absolute -mt-1 -ml-1 text-red-500" />
                )}
              </div>
              <div>
                <div className="font-medium">{section.title}</div>
                <div className="text-sm text-muted-foreground">
                  {section.description}
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Settings Content */}
        <div className="lg:col-span-3">
          <div className="card p-6">
            <motion.div
              key={activeSection}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
            >
              {renderContent()}
            </motion.div>
          </div>
        </div>
      </div>

      {/* Changes Indicator */}
      {hasChanges && (
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          className="fixed bottom-6 right-6 bg-card border border-border rounded-lg shadow-lg p-4 flex items-center gap-3"
        >
          <Info className="w-5 h-5 text-blue-500" />
          <span className="text-sm">You have unsaved changes</span>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="btn btn-primary btn-sm"
          >
            {isSaving ? 'Saving...' : 'Save'}
          </button>
        </motion.div>
      )}
    </div>
  )
}