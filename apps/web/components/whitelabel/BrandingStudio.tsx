'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Card } from '../ui/card'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { brandingService } from '../../lib/whitelabel/branding.service'
import type { BrandConfiguration } from '../../types/epic4'

interface BrandingStudioProps {
  tenantId: string
  onConfigurationChange?: (config: BrandConfiguration) => void
}

interface ColorPicker {
  color: string
  isOpen: boolean
}

export function BrandingStudio({ tenantId, onConfigurationChange }: BrandingStudioProps) {
  const [activeTab, setActiveTab] = useState<'logo' | 'colors' | 'typography' | 'preview' | 'assets'>('logo')
  const [config, setConfig] = useState<BrandConfiguration | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [colorPicker, setColorPicker] = useState<ColorPicker>({ color: '', isOpen: false })
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [templates, setTemplates] = useState<any[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    loadBrandingData()
  }, [tenantId])

  const loadBrandingData = async () => {
    setLoading(true)
    try {
      const [brandConfig, themeTemplates] = await Promise.all([
        brandingService.getBrandConfiguration(tenantId).catch(() => null),
        brandingService.getThemeTemplates()
      ])

      if (brandConfig) {
        setConfig(brandConfig)
      } else {
        // Create default configuration
        const defaultConfig: BrandConfiguration = {
          tenantId,
          brandName: 'Your Brand',
          logo: {
            primary: '',
            favicon: '',
            dimensions: { width: 200, height: 60 }
          },
          colors: {
            primary: '#3B82F6',
            secondary: '#8B5CF6',
            accent: '#F59E0B',
            background: '#FFFFFF',
            surface: '#F9FAFB',
            text: {
              primary: '#111827',
              secondary: '#6B7280',
              muted: '#9CA3AF'
            },
            status: {
              success: '#10B981',
              warning: '#F59E0B',
              error: '#EF4444',
              info: '#3B82F6'
            }
          },
          typography: {
            fontFamily: {
              sans: 'Inter, system-ui, sans-serif'
            },
            fontSizes: {
              xs: '0.75rem',
              sm: '0.875rem',
              base: '1rem',
              lg: '1.125rem',
              xl: '1.25rem',
              '2xl': '1.5rem',
              '3xl': '1.875rem',
              '4xl': '2.25rem'
            },
            fontWeights: {
              normal: 400,
              medium: 500,
              semibold: 600,
              bold: 700
            },
            lineHeights: {
              tight: 1.25,
              normal: 1.5,
              relaxed: 1.625
            }
          },
          updatedAt: new Date(),
          createdBy: 'system'
        }
        setConfig(defaultConfig)
      }
      
      setTemplates(themeTemplates)
    } catch (error) {
      console.error('Failed to load branding data:', error)
    }
    setLoading(false)
  }

  const handleConfigUpdate = async (updates: Partial<BrandConfiguration>) => {
    if (!config) return

    const updatedConfig = { ...config, ...updates, updatedAt: new Date() }
    setConfig(updatedConfig)

    setSaving(true)
    try {
      const savedConfig = await brandingService.updateBrandConfiguration(tenantId, updatedConfig)
      setConfig(savedConfig)
      onConfigurationChange?.(savedConfig)
    } catch (error) {
      console.error('Failed to save configuration:', error)
    }
    setSaving(false)
  }

  const handleLogoUpload = async (event: React.ChangeEvent<HTMLInputElement>, type: 'primary' | 'secondary' | 'favicon') => {
    const file = event.target.files?.[0]
    if (!file || !config) return

    try {
      const result = await brandingService.uploadLogo(tenantId, file, type)
      
      handleConfigUpdate({
        logo: {
          ...config.logo,
          [type]: result.url,
          ...(type === 'primary' && { dimensions: result.dimensions })
        }
      })
    } catch (error) {
      console.error('Failed to upload logo:', error)
    }
  }

  const handleColorChange = (colorPath: string, value: string) => {
    if (!config) return

    const colorPaths = colorPath.split('.')
    let updatedColors = { ...config.colors }

    if (colorPaths.length === 1) {
      updatedColors = { ...updatedColors, [colorPaths[0]]: value }
    } else if (colorPaths.length === 2) {
      updatedColors = {
        ...updatedColors,
        [colorPaths[0]]: {
          ...(updatedColors as any)[colorPaths[0]],
          [colorPaths[1]]: value
        }
      }
    }

    handleConfigUpdate({ colors: updatedColors })
  }

  const generateColorPalette = async () => {
    if (!config) return

    try {
      const palette = await brandingService.generateColorPalette(config.colors.primary)
      handleConfigUpdate({ colors: palette })
    } catch (error) {
      console.error('Failed to generate color palette:', error)
    }
  }

  const handleTemplateApply = async (templateId: string) => {
    try {
      const newConfig = await brandingService.applyThemeTemplate(tenantId, templateId)
      setConfig(newConfig)
      onConfigurationChange?.(newConfig)
    } catch (error) {
      console.error('Failed to apply template:', error)
    }
  }

  const generatePreview = async (component: 'dashboard' | 'login' | 'landing' | 'voice-interface') => {
    if (!config) return

    try {
      const preview = await brandingService.generatePreview(config, component)
      setPreviewUrl(preview.previewUrl)
    } catch (error) {
      console.error('Failed to generate preview:', error)
    }
  }

  const ColorInput = ({ 
    label, 
    value, 
    onChange, 
    path 
  }: { 
    label: string
    value: string
    onChange: (value: string) => void
    path: string
  }) => (
    <div className="flex items-center gap-3">
      <div
        className="w-8 h-8 rounded border-2 border-gray-300 cursor-pointer"
        style={{ backgroundColor: value }}
        onClick={() => setColorPicker({ color: path, isOpen: true })}
      />
      <div className="flex-1">
        <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
        <Input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="font-mono text-sm"
          placeholder="#FFFFFF"
        />
      </div>
    </div>
  )

  const tabs = [
    { id: 'logo' as const, label: 'Logo & Assets', icon: '🎨' },
    { id: 'colors' as const, label: 'Colors', icon: '🌈' },
    { id: 'typography' as const, label: 'Typography', icon: '📝' },
    { id: 'preview' as const, label: 'Preview', icon: '👁️' },
    { id: 'assets' as const, label: 'Brand Assets', icon: '📁' }
  ]

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading branding studio...</p>
        </div>
      </div>
    )
  }

  if (!config) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="p-8 text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Configuration Error</h2>
          <p className="text-gray-600 mb-4">Failed to load branding configuration.</p>
          <Button onClick={loadBrandingData}>Retry</Button>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Branding Studio</h1>
            <p className="text-gray-600">Customize your brand identity and visual appearance</p>
          </div>
          <div className="flex items-center gap-4">
            {saving && <span className="text-sm text-gray-500">Saving...</span>}
            <Button
              onClick={() => brandingService.applyBrandingToDOM(tenantId)}
              variant="outline"
            >
              Apply Live Preview
            </Button>
            <Button onClick={() => generatePreview('dashboard')}>
              Generate Preview
            </Button>
          </div>
        </div>

        {/* Brand Info */}
        <Card className="p-6 mb-8">
          <div className="flex items-center gap-4">
            {config.logo.primary && (
              <img
                src={config.logo.primary}
                alt={config.brandName}
                className="h-12 w-auto"
              />
            )}
            <div>
              <h2 className="text-xl font-semibold text-gray-900">{config.brandName}</h2>
              <p className="text-gray-600">Tenant ID: {tenantId}</p>
            </div>
          </div>
        </Card>

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
          {activeTab === 'logo' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Brand Information</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Brand Name
                    </label>
                    <Input
                      value={config.brandName}
                      onChange={(e) => handleConfigUpdate({ brandName: e.target.value })}
                      placeholder="Your Brand Name"
                    />
                  </div>
                </div>
              </Card>

              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Logo Upload</h3>
                <div className="space-y-6">
                  {/* Primary Logo */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Primary Logo
                    </label>
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                      {config.logo.primary ? (
                        <div>
                          <img
                            src={config.logo.primary}
                            alt="Primary Logo"
                            className="h-16 mx-auto mb-4"
                          />
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => fileInputRef.current?.click()}
                          >
                            Change Logo
                          </Button>
                        </div>
                      ) : (
                        <div>
                          <div className="text-4xl mb-2">🎨</div>
                          <Button
                            variant="outline"
                            onClick={() => fileInputRef.current?.click()}
                          >
                            Upload Primary Logo
                          </Button>
                        </div>
                      )}
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        onChange={(e) => handleLogoUpload(e, 'primary')}
                        className="hidden"
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      Recommended: PNG or SVG, max 2MB, transparent background
                    </p>
                  </div>

                  {/* Favicon */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Favicon
                    </label>
                    <div className="flex items-center gap-4">
                      {config.logo.favicon && (
                        <img
                          src={config.logo.favicon}
                          alt="Favicon"
                          className="w-8 h-8"
                        />
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          const input = document.createElement('input')
                          input.type = 'file'
                          input.accept = 'image/*'
                          input.onchange = (e) => handleLogoUpload(e as any, 'favicon')
                          input.click()
                        }}
                      >
                        {config.logo.favicon ? 'Change' : 'Upload'} Favicon
                      </Button>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      Recommended: 32x32 or 64x64 pixels, ICO or PNG format
                    </p>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {activeTab === 'colors' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">Color Palette</h3>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={generateColorPalette}
                  >
                    Generate Palette
                  </Button>
                </div>
                <div className="space-y-4">
                  <ColorInput
                    label="Primary Color"
                    value={config.colors.primary}
                    onChange={(value) => handleColorChange('primary', value)}
                    path="primary"
                  />
                  <ColorInput
                    label="Secondary Color"
                    value={config.colors.secondary}
                    onChange={(value) => handleColorChange('secondary', value)}
                    path="secondary"
                  />
                  <ColorInput
                    label="Accent Color"
                    value={config.colors.accent}
                    onChange={(value) => handleColorChange('accent', value)}
                    path="accent"
                  />
                  <ColorInput
                    label="Background"
                    value={config.colors.background}
                    onChange={(value) => handleColorChange('background', value)}
                    path="background"
                  />
                </div>
              </Card>

              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Text Colors</h3>
                <div className="space-y-4">
                  <ColorInput
                    label="Primary Text"
                    value={config.colors.text.primary}
                    onChange={(value) => handleColorChange('text.primary', value)}
                    path="text.primary"
                  />
                  <ColorInput
                    label="Secondary Text"
                    value={config.colors.text.secondary}
                    onChange={(value) => handleColorChange('text.secondary', value)}
                    path="text.secondary"
                  />
                  <ColorInput
                    label="Muted Text"
                    value={config.colors.text.muted}
                    onChange={(value) => handleColorChange('text.muted', value)}
                    path="text.muted"
                  />
                </div>

                <h3 className="text-lg font-semibold mb-4 mt-6">Status Colors</h3>
                <div className="space-y-4">
                  <ColorInput
                    label="Success"
                    value={config.colors.status.success}
                    onChange={(value) => handleColorChange('status.success', value)}
                    path="status.success"
                  />
                  <ColorInput
                    label="Warning"
                    value={config.colors.status.warning}
                    onChange={(value) => handleColorChange('status.warning', value)}
                    path="status.warning"
                  />
                  <ColorInput
                    label="Error"
                    value={config.colors.status.error}
                    onChange={(value) => handleColorChange('status.error', value)}
                    path="status.error"
                  />
                  <ColorInput
                    label="Info"
                    value={config.colors.status.info}
                    onChange={(value) => handleColorChange('status.info', value)}
                    path="status.info"
                  />
                </div>
              </Card>
            </div>
          )}

          {activeTab === 'typography' && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Typography Settings</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Font Family
                  </label>
                  <select
                    value={config.typography.fontFamily.sans}
                    onChange={(e) => handleConfigUpdate({
                      typography: {
                        ...config.typography,
                        fontFamily: {
                          ...config.typography.fontFamily,
                          sans: e.target.value
                        }
                      }
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="Inter, system-ui, sans-serif">Inter</option>
                    <option value="Poppins, system-ui, sans-serif">Poppins</option>
                    <option value="Roboto, system-ui, sans-serif">Roboto</option>
                    <option value="Open Sans, system-ui, sans-serif">Open Sans</option>
                    <option value="Lato, system-ui, sans-serif">Lato</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Preview
                  </label>
                  <div
                    className="p-4 border border-gray-300 rounded-md"
                    style={{ fontFamily: config.typography.fontFamily.sans }}
                  >
                    <div className="text-2xl font-bold mb-2">Your Brand</div>
                    <div className="text-lg mb-1">Welcome to our platform</div>
                    <div className="text-sm text-gray-600">
                      This is how your typography will look across the platform.
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {activeTab === 'preview' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Preview Options</h3>
                <div className="grid grid-cols-2 gap-4">
                  <Button
                    variant="outline"
                    onClick={() => generatePreview('dashboard')}
                    className="h-24 flex flex-col items-center justify-center"
                  >
                    <div className="text-2xl mb-1">📊</div>
                    <span>Dashboard</span>
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => generatePreview('login')}
                    className="h-24 flex flex-col items-center justify-center"
                  >
                    <div className="text-2xl mb-1">🔐</div>
                    <span>Login Page</span>
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => generatePreview('landing')}
                    className="h-24 flex flex-col items-center justify-center"
                  >
                    <div className="text-2xl mb-1">🏠</div>
                    <span>Landing Page</span>
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => generatePreview('voice-interface')}
                    className="h-24 flex flex-col items-center justify-center"
                  >
                    <div className="text-2xl mb-1">🎤</div>
                    <span>Voice Interface</span>
                  </Button>
                </div>
              </Card>

              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Live Preview</h3>
                {previewUrl ? (
                  <div className="aspect-video">
                    <iframe
                      src={previewUrl}
                      className="w-full h-full border rounded-lg"
                      title="Brand Preview"
                    />
                  </div>
                ) : (
                  <div className="aspect-video bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center">
                    <div className="text-center text-gray-500">
                      <div className="text-4xl mb-2">👁️</div>
                      <p>Click a preview option to see your branding in action</p>
                    </div>
                  </div>
                )}
              </Card>
            </div>
          )}

          {activeTab === 'assets' && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Theme Templates</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {templates.map(template => (
                  <div key={template.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="aspect-video bg-gray-100 rounded mb-3 flex items-center justify-center">
                      <span className="text-gray-500">Preview</span>
                    </div>
                    <h4 className="font-medium mb-2">{template.name}</h4>
                    <p className="text-sm text-gray-600 mb-3">{template.description}</p>
                    <div className="flex flex-wrap gap-1 mb-3">
                      {template.tags.slice(0, 3).map((tag: string) => (
                        <span key={tag} className="px-2 py-1 bg-gray-100 text-xs rounded">
                          {tag}
                        </span>
                      ))}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleTemplateApply(template.id)}
                      className="w-full"
                    >
                      Apply Template
                    </Button>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

export default BrandingStudio