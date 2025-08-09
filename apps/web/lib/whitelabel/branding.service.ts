// White Label Branding Service
import type {
  BrandConfiguration,
  WhiteLabelSettings,
  Tenant
} from '../../types/epic4'
import { apiClient } from '../api/client'

export class BrandingService {
  private readonly baseUrl = '/api/whitelabel/branding'

  // Brand Configuration Management
  async getBrandConfiguration(tenantId: string): Promise<BrandConfiguration> {
    const response = await apiClient.get<BrandConfiguration>(`${this.baseUrl}/${tenantId}`)
    return response.data
  }

  async updateBrandConfiguration(
    tenantId: string, 
    config: Partial<BrandConfiguration>
  ): Promise<BrandConfiguration> {
    const response = await apiClient.put<BrandConfiguration>(`${this.baseUrl}/${tenantId}`, {
      ...config,
      tenantId,
      updatedAt: new Date()
    })
    return response.data
  }

  async createBrandConfiguration(config: Omit<BrandConfiguration, 'updatedAt'>): Promise<BrandConfiguration> {
    const response = await apiClient.post<BrandConfiguration>(`${this.baseUrl}`, {
      ...config,
      updatedAt: new Date()
    })
    return response.data
  }

  // Logo Management
  async uploadLogo(
    tenantId: string, 
    logoFile: File, 
    type: 'primary' | 'secondary' | 'favicon'
  ): Promise<{
    url: string
    dimensions: { width: number; height: number }
    size: number
  }> {
    const formData = new FormData()
    formData.append('logo', logoFile)
    formData.append('type', type)
    formData.append('tenantId', tenantId)

    const response = await apiClient.post<{
      url: string
      dimensions: { width: number; height: number }
      size: number
    }>(`${this.baseUrl}/${tenantId}/logo`, formData)
    return response.data
  }

  async deleteLogo(tenantId: string, type: 'primary' | 'secondary' | 'favicon'): Promise<void> {
    const response = await apiClient.delete<void>(`${this.baseUrl}/${tenantId}/logo/${type}`)
    return response.data
  }

  // Color Palette Management
  async generateColorPalette(primaryColor: string): Promise<{
    primary: string
    secondary: string
    accent: string
    background: string
    surface: string
    text: {
      primary: string
      secondary: string
      muted: string
    }
    status: {
      success: string
      warning: string
      error: string
      info: string
    }
  }> {
    const response = await apiClient.post<{
      primary: string
      secondary: string
      accent: string
      background: string
      surface: string
      text: {
        primary: string
        secondary: string
        muted: string
      }
      status: {
        success: string
        warning: string
        error: string
        info: string
      }
    }>(`${this.baseUrl}/color-palette/generate`, { primaryColor })
    return response.data
  }

  async validateColorPalette(colors: Record<string, string>): Promise<{
    isValid: boolean
    issues: Array<{
      color: string
      issue: string
      severity: 'low' | 'medium' | 'high'
      suggestion: string
    }>
    accessibility: {
      contrastRatios: Record<string, number>
      wcagCompliant: boolean
      recommendations: string[]
    }
  }> {
    const response = await apiClient.post<{
      isValid: boolean
      issues: Array<{
        color: string
        issue: string
        severity: 'low' | 'medium' | 'high'
        suggestion: string
      }>
      accessibility: {
        contrastRatios: Record<string, number>
        wcagCompliant: boolean
        recommendations: string[]
      }
    }>(`${this.baseUrl}/color-palette/validate`, { colors })
    return response.data
  }

  // Typography Management
  async getFontOptions(): Promise<Array<{
    family: string
    category: 'sans-serif' | 'serif' | 'monospace' | 'display'
    variants: string[]
    previewUrl: string
    license: 'free' | 'paid'
    popularity: number
  }>> {
    const response = await apiClient.get<Array<{
      family: string
      category: 'sans-serif' | 'serif' | 'monospace' | 'display'
      variants: string[]
      previewUrl: string
      license: 'free' | 'paid'
      popularity: number
    }>>(`${this.baseUrl}/fonts`)
    return response.data
  }

  async loadFont(fontFamily: string): Promise<{
    cssUrl: string
    fallbacks: string[]
    loaded: boolean
  }> {
    const response = await apiClient.post<{
      cssUrl: string
      fallbacks: string[]
      loaded: boolean
    }>(`${this.baseUrl}/fonts/load`, { fontFamily })
    return response.data
  }

  // CSS Generation and Management
  async generateCSS(tenantId: string): Promise<{
    css: string
    variables: Record<string, string>
    mediaQueries: Record<string, string>
    size: number
  }> {
    const response = await apiClient.post<{
      css: string
      variables: Record<string, string>
      mediaQueries: Record<string, string>
      size: number
    }>(`${this.baseUrl}/${tenantId}/css/generate`)
    return response.data
  }

  async updateCustomCSS(tenantId: string, customCSS: string): Promise<{
    isValid: boolean
    errors: string[]
    warnings: string[]
    minified: string
  }> {
    const response = await apiClient.put<{
      isValid: boolean
      errors: string[]
      warnings: string[]
      minified: string
    }>(`${this.baseUrl}/${tenantId}/css/custom`, { customCSS })
    return response.data
  }

  async getCSSVariables(tenantId: string): Promise<Record<string, string>> {
    const response = await apiClient.get<{ variables: Record<string, string> }>(
      `${this.baseUrl}/${tenantId}/css/variables`
    )
    return response.data.variables
  }

  // Theme Templates
  async getThemeTemplates(): Promise<Array<{
    id: string
    name: string
    description: string
    category: 'professional' | 'modern' | 'minimal' | 'bold' | 'creative'
    previewUrl: string
    colors: Record<string, string>
    typography: Record<string, string>
    popularity: number
    tags: string[]
  }>> {
    const response = await apiClient.get<Array<{
      id: string
      name: string
      description: string
      category: 'professional' | 'modern' | 'minimal' | 'bold' | 'creative'
      previewUrl: string
      colors: Record<string, string>
      typography: Record<string, string>
      popularity: number
      tags: string[]
    }>>(`${this.baseUrl}/templates`)
    return response.data
  }

  async applyThemeTemplate(tenantId: string, templateId: string): Promise<BrandConfiguration> {
    const response = await apiClient.post<BrandConfiguration>(
      `${this.baseUrl}/${tenantId}/templates/${templateId}/apply`
    )
    return response.data
  }

  async createCustomTemplate(
    name: string,
    config: Partial<BrandConfiguration>,
    isPublic = false
  ): Promise<{
    templateId: string
    name: string
    createdAt: Date
  }> {
    const response = await apiClient.post<{
      templateId: string
      name: string
      createdAt: Date
    }>(`${this.baseUrl}/templates`, {
      name,
      config,
      isPublic,
      createdAt: new Date()
    })
    return response.data
  }

  // Brand Asset Management
  async uploadBrandAsset(
    tenantId: string,
    file: File,
    category: 'image' | 'icon' | 'background' | 'pattern',
    metadata?: {
      alt?: string
      description?: string
      tags?: string[]
    }
  ): Promise<{
    assetId: string
    url: string
    category: string
    size: number
    dimensions?: { width: number; height: number }
    format: string
  }> {
    const formData = new FormData()
    formData.append('asset', file)
    formData.append('category', category)
    formData.append('tenantId', tenantId)
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata))
    }

    const response = await apiClient.post<{
      assetId: string
      url: string
      category: string
      size: number
      dimensions?: { width: number; height: number }
      format: string
    }>(`${this.baseUrl}/${tenantId}/assets`, formData)
    return response.data
  }

  async getBrandAssets(
    tenantId: string,
    category?: string
  ): Promise<Array<{
    assetId: string
    url: string
    category: string
    size: number
    dimensions?: { width: number; height: number }
    format: string
    uploadedAt: Date
    metadata?: Record<string, any>
  }>> {
    const params = category ? `?category=${category}` : ''
    const response = await apiClient.get<Array<{
      assetId: string
      url: string
      category: string
      size: number
      dimensions?: { width: number; height: number }
      format: string
      uploadedAt: Date
      metadata?: Record<string, any>
    }>>(`${this.baseUrl}/${tenantId}/assets${params}`)
    return response.data
  }

  async deleteBrandAsset(tenantId: string, assetId: string): Promise<void> {
    const response = await apiClient.delete<void>(`${this.baseUrl}/${tenantId}/assets/${assetId}`)
    return response.data
  }

  // Preview and Testing
  async generatePreview(
    config: Partial<BrandConfiguration>,
    component: 'dashboard' | 'login' | 'landing' | 'voice-interface'
  ): Promise<{
    previewUrl: string
    expiresAt: Date
    screenshotUrl: string
  }> {
    const response = await apiClient.post<{
      previewUrl: string
      expiresAt: Date
      screenshotUrl: string
    }>(`${this.baseUrl}/preview`, {
      config,
      component,
      timestamp: new Date()
    })
    return response.data
  }

  async validateBrandCompliance(config: BrandConfiguration): Promise<{
    isCompliant: boolean
    issues: Array<{
      category: 'accessibility' | 'usability' | 'performance' | 'consistency'
      severity: 'low' | 'medium' | 'high'
      description: string
      recommendation: string
    }>
    score: number // 0-100
    recommendations: string[]
  }> {
    const response = await apiClient.post<{
      isCompliant: boolean
      issues: Array<{
        category: 'accessibility' | 'usability' | 'performance' | 'consistency'
        severity: 'low' | 'medium' | 'high'
        description: string
        recommendation: string
      }>
      score: number
      recommendations: string[]
    }>(`${this.baseUrl}/compliance/validate`, { config })
    return response.data
  }

  // White Label Settings
  async getWhiteLabelSettings(tenantId: string): Promise<WhiteLabelSettings> {
    const response = await apiClient.get<WhiteLabelSettings>(`${this.baseUrl}/${tenantId}/settings`)
    return response.data
  }

  async updateWhiteLabelSettings(
    tenantId: string,
    settings: Partial<WhiteLabelSettings>
  ): Promise<WhiteLabelSettings> {
    const response = await apiClient.put<WhiteLabelSettings>(`${this.baseUrl}/${tenantId}/settings`, {
      ...settings,
      tenantId
    })
    return response.data
  }

  // Domain Management
  async setupCustomDomain(
    tenantId: string,
    domain: string,
    sslCertificate?: {
      certificate: string
      privateKey: string
      chain?: string
    }
  ): Promise<{
    domain: string
    status: 'pending' | 'active' | 'failed'
    dnsRecords: Array<{
      type: 'CNAME' | 'A' | 'TXT'
      name: string
      value: string
      ttl: number
    }>
    sslStatus: 'pending' | 'active' | 'failed'
    verificationToken: string
  }> {
    const response = await apiClient.post<{
      domain: string
      status: 'pending' | 'active' | 'failed'
      dnsRecords: Array<{
        type: 'CNAME' | 'A' | 'TXT'
        name: string
        value: string
        ttl: number
      }>
      sslStatus: 'pending' | 'active' | 'failed'
      verificationToken: string
    }>(`${this.baseUrl}/${tenantId}/domain`, {
      domain,
      sslCertificate
    })
    return response.data
  }

  async verifyCustomDomain(tenantId: string, domain: string): Promise<{
    verified: boolean
    issues: string[]
    dnsStatus: Record<string, boolean>
    sslStatus: 'valid' | 'invalid' | 'expired' | 'pending'
  }> {
    const response = await apiClient.post<{
      verified: boolean
      issues: string[]
      dnsStatus: Record<string, boolean>
      sslStatus: 'valid' | 'invalid' | 'expired' | 'pending'
    }>(`${this.baseUrl}/${tenantId}/domain/${domain}/verify`)
    return response.data
  }

  // Export and Import
  async exportBrandConfiguration(tenantId: string): Promise<{
    config: BrandConfiguration
    assets: Array<{ id: string; url: string; category: string }>
    exportUrl: string
    expiresAt: Date
  }> {
    const response = await apiClient.get<{
      config: BrandConfiguration
      assets: Array<{ id: string; url: string; category: string }>
      exportUrl: string
      expiresAt: Date
    }>(`${this.baseUrl}/${tenantId}/export`)
    return response.data
  }

  async importBrandConfiguration(
    tenantId: string,
    configFile: File
  ): Promise<{
    success: boolean
    imported: {
      config: boolean
      assets: number
      fonts: number
    }
    errors: string[]
    warnings: string[]
  }> {
    const formData = new FormData()
    formData.append('config', configFile)
    formData.append('tenantId', tenantId)

    const response = await apiClient.post<{
      success: boolean
      imported: {
        config: boolean
        assets: number
        fonts: number
      }
      errors: string[]
      warnings: string[]
    }>(`${this.baseUrl}/${tenantId}/import`, formData)
    return response.data
  }

  // Analytics and Usage
  async getBrandingAnalytics(
    tenantId: string,
    period: '7d' | '30d' | '90d' = '30d'
  ): Promise<{
    period: string
    metrics: {
      pageViews: number
      uniqueVisitors: number
      averageSessionTime: number
      bounceRate: number
    }
    brandRecognition: {
      logoViews: number
      colorSchemeRating: number
      userFeedback: number
    }
    performance: {
      loadTime: number
      cssSize: number
      imageOptimization: number
    }
    trends: Array<{
      date: string
      views: number
      engagement: number
    }>
  }> {
    const response = await apiClient.get<{
      period: string
      metrics: {
        pageViews: number
        uniqueVisitors: number
        averageSessionTime: number
        bounceRate: number
      }
      brandRecognition: {
        logoViews: number
        colorSchemeRating: number
        userFeedback: number
      }
      performance: {
        loadTime: number
        cssSize: number
        imageOptimization: number
      }
      trends: Array<{
        date: string
        views: number
        engagement: number
      }>
    }>(`${this.baseUrl}/${tenantId}/analytics?period=${period}`)
    return response.data
  }

  // Client-side utilities
  async applyBrandingToDOM(tenantId: string): Promise<void> {
    try {
      const config = await this.getBrandConfiguration(tenantId)
      const { css } = await this.generateCSS(tenantId)

      // Create or update brand style element
      let styleElement = document.getElementById('brand-styles') as HTMLStyleElement
      if (!styleElement) {
        styleElement = document.createElement('style')
        styleElement.id = 'brand-styles'
        document.head.appendChild(styleElement)
      }
      styleElement.textContent = css

      // Update favicon if provided
      if (config.logo.favicon) {
        let faviconElement = document.querySelector('link[rel="icon"]') as HTMLLinkElement
        if (!faviconElement) {
          faviconElement = document.createElement('link')
          faviconElement.rel = 'icon'
          document.head.appendChild(faviconElement)
        }
        faviconElement.href = config.logo.favicon
      }

      // Update page title if brand name is different
      if (config.brandName && document.title.includes('Seiketsu')) {
        document.title = document.title.replace('Seiketsu', config.brandName)
      }
    } catch (error) {
      console.error('Failed to apply branding to DOM:', error)
    }
  }

  // Utility method to check if branding is applied
  isBrandingApplied(tenantId: string): boolean {
    const styleElement = document.getElementById('brand-styles')
    return !!styleElement && styleElement.hasAttribute('data-tenant-id')
  }
}

export const brandingService = new BrandingService()