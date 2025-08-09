'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '../ui/button'
import { Card } from '../ui/card'
import { gdprService } from '../../lib/compliance/gdpr.service'
import type { GDPRConsent, PrivacySettings } from '../../types/epic4'

interface ConsentManagerProps {
  userId: string
  onConsentUpdate?: (consents: GDPRConsent[]) => void
  showBanner?: boolean
  position?: 'top' | 'bottom'
  theme?: 'light' | 'dark'
}

interface ConsentCategory {
  id: string
  name: string
  description: string
  required: boolean
  purposes: string[]
  cookies: Array<{
    name: string
    purpose: string
    duration: string
    type: 'first-party' | 'third-party'
  }>
}

export function ConsentManager({ 
  userId, 
  onConsentUpdate, 
  showBanner = true, 
  position = 'bottom',
  theme = 'light' 
}: ConsentManagerProps) {
  const [showModal, setShowModal] = useState(false)
  const [showBannerState, setShowBannerState] = useState(false)
  const [consents, setConsents] = useState<GDPRConsent[]>([])
  const [categories, setCategories] = useState<ConsentCategory[]>([])
  const [preferences, setPreferences] = useState<Record<string, boolean>>({})
  const [privacySettings, setPrivacySettings] = useState<PrivacySettings | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadConsentData()
  }, [userId])

  useEffect(() => {
    // Check if user needs to see consent banner
    const hasSeenBanner = localStorage.getItem(`consent-banner-${userId}`)
    const hasNecessaryConsents = consents.some(c => c.consentType === 'necessary' && c.granted)
    
    if (!hasSeenBanner && !hasNecessaryConsents && showBanner) {
      setShowBannerState(true)
    }
  }, [consents, userId, showBanner])

  const loadConsentData = async () => {
    try {
      const [userConsents, cookieCategories, userPrivacySettings] = await Promise.all([
        gdprService.getConsent(userId),
        gdprService.getCookieCategories(),
        gdprService.getPrivacySettings(userId).catch(() => null)
      ])

      setConsents(userConsents)
      setCategories(cookieCategories.map(cat => ({
        id: cat.category,
        name: cat.name,
        description: cat.description,
        required: cat.required,
        purposes: cat.cookies.map(c => c.purpose),
        cookies: cat.cookies
      })))

      // Set current preferences
      const currentPreferences: Record<string, boolean> = {}
      cookieCategories.forEach(cat => {
        const consent = userConsents.find(c => c.consentType === cat.category as any)
        currentPreferences[cat.category] = consent ? consent.granted : cat.required
      })
      setPreferences(currentPreferences)
      setPrivacySettings(userPrivacySettings)
    } catch (error) {
      console.error('Failed to load consent data:', error)
    }
  }

  const handleAcceptAll = async () => {
    setLoading(true)
    try {
      const allCategories = ['necessary', 'functional', 'analytics', 'marketing']
      const consentPromises = allCategories.map(category => 
        gdprService.recordConsent({
          userId,
          consentType: category as any,
          granted: true,
          consentMethod: 'explicit',
          legalBasis: 'consent',
          ipAddress: 'unknown',
          userAgent: navigator.userAgent
        })
      )

      const newConsents = await Promise.all(consentPromises)
      setConsents(newConsents)
      
      // Update preferences
      const newPreferences = Object.fromEntries(allCategories.map(cat => [cat, true]))
      setPreferences(newPreferences)
      await gdprService.setCookiePreferences(userId, newPreferences)

      setShowBannerState(false)
      setShowModal(false)
      localStorage.setItem(`consent-banner-${userId}`, 'seen')
      
      await gdprService.logGDPREvent({
        userId,
        action: 'consent_accept_all',
        resource: 'consent_manager',
        ipAddress: 'unknown',
        userAgent: navigator.userAgent,
        outcome: 'success',
        riskLevel: 'low',
        details: { categories: allCategories }
      })

      onConsentUpdate?.(newConsents)
    } catch (error) {
      console.error('Failed to save consent:', error)
    }
    setLoading(false)
  }

  const handleRejectAll = async () => {
    setLoading(true)
    try {
      const optionalCategories = categories.filter(cat => !cat.required).map(cat => cat.id)
      const necessaryCategories = categories.filter(cat => cat.required).map(cat => cat.id)
      
      const consentPromises = [
        ...optionalCategories.map(category => 
          gdprService.recordConsent({
            userId,
            consentType: category as any,
            granted: false,
            consentMethod: 'explicit',
            legalBasis: 'consent',
            ipAddress: 'unknown',
            userAgent: navigator.userAgent
          })
        ),
        ...necessaryCategories.map(category => 
          gdprService.recordConsent({
            userId,
            consentType: category as any,
            granted: true,
            consentMethod: 'explicit',
            legalBasis: 'legal_obligation',
            ipAddress: 'unknown',
            userAgent: navigator.userAgent
          })
        )
      ]

      const newConsents = await Promise.all(consentPromises)
      setConsents(newConsents)
      
      // Update preferences
      const newPreferences = Object.fromEntries([
        ...optionalCategories.map(cat => [cat, false]),
        ...necessaryCategories.map(cat => [cat, true])
      ])
      setPreferences(newPreferences)
      await gdprService.setCookiePreferences(userId, newPreferences)

      setShowBannerState(false)
      setShowModal(false)
      localStorage.setItem(`consent-banner-${userId}`, 'seen')
      
      await gdprService.logGDPREvent({
        userId,
        action: 'consent_reject_optional',
        resource: 'consent_manager',
        ipAddress: 'unknown',
        userAgent: navigator.userAgent,
        outcome: 'success',
        riskLevel: 'low',
        details: { optional: optionalCategories, necessary: necessaryCategories }
      })

      onConsentUpdate?.(newConsents)
    } catch (error) {
      console.error('Failed to save consent:', error)
    }
    setLoading(false)
  }

  const handleCustomizeConsent = () => {
    setShowBannerState(false)
    setShowModal(true)
  }

  const handleSavePreferences = async () => {
    setLoading(true)
    try {
      const consentPromises = Object.entries(preferences).map(([category, granted]) =>
        gdprService.recordConsent({
          userId,
          consentType: category as any,
          granted,
          consentMethod: 'explicit',
          legalBasis: granted ? 'consent' : 'legal_obligation',
          ipAddress: 'unknown',
          userAgent: navigator.userAgent
        })
      )

      const newConsents = await Promise.all(consentPromises)
      setConsents(newConsents)
      await gdprService.setCookiePreferences(userId, preferences)

      setShowModal(false)
      localStorage.setItem(`consent-banner-${userId}`, 'seen')
      
      await gdprService.logGDPREvent({
        userId,
        action: 'consent_customize',
        resource: 'consent_manager',
        ipAddress: 'unknown',
        userAgent: navigator.userAgent,
        outcome: 'success',
        riskLevel: 'low',
        details: { preferences }
      })

      onConsentUpdate?.(newConsents)
    } catch (error) {
      console.error('Failed to save preferences:', error)
    }
    setLoading(false)
  }

  const handlePreferenceChange = (category: string, granted: boolean) => {
    setPreferences(prev => ({ ...prev, [category]: granted }))
  }

  const handleWithdrawConsent = async (category: string) => {
    try {
      await gdprService.withdrawConsent(userId, category)
      await loadConsentData()
      
      await gdprService.logGDPREvent({
        userId,
        action: 'consent_withdraw',
        resource: 'consent_manager',
        ipAddress: 'unknown',
        userAgent: navigator.userAgent,
        outcome: 'success',
        riskLevel: 'medium',
        details: { category }
      })
    } catch (error) {
      console.error('Failed to withdraw consent:', error)
    }
  }

  // Consent Banner
  const ConsentBanner = () => (
    <div className={`fixed ${position === 'top' ? 'top-0' : 'bottom-0'} left-0 right-0 z-50 ${
      theme === 'dark' ? 'bg-gray-900 text-white' : 'bg-white text-gray-900'
    } shadow-lg border-t border-gray-200`}>
      <div className="max-w-7xl mx-auto p-4">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex-1">
            <p className="text-sm">
              We use cookies and similar technologies to enhance your experience, analyze usage, and personalize content. 
              By clicking "Accept All", you consent to our use of cookies.{' '}
              <button 
                onClick={() => setShowModal(true)}
                className="underline hover:no-underline font-medium"
              >
                Learn more
              </button>
            </p>
          </div>
          <div className="flex gap-3 flex-shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRejectAll}
              disabled={loading}
            >
              Reject All
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleCustomizeConsent}
              disabled={loading}
            >
              Customize
            </Button>
            <Button
              size="sm"
              onClick={handleAcceptAll}
              disabled={loading}
            >
              Accept All
            </Button>
          </div>
        </div>
      </div>
    </div>
  )

  // Consent Modal
  const ConsentModal = () => (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <Card className="w-full max-w-2xl max-h-[80vh] m-4 overflow-hidden">
        <div className="p-6 border-b">
          <h2 className="text-xl font-semibold">Privacy Preferences</h2>
          <p className="text-sm text-gray-600 mt-1">
            Choose which cookies and data processing you're comfortable with. You can change these settings at any time.
          </p>
        </div>
        
        <div className="overflow-y-auto max-h-[50vh] p-6">
          {categories.map(category => (
            <div key={category.id} className="mb-6 last:mb-0">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h3 className="font-medium flex items-center gap-2">
                    {category.name}
                    {category.required && (
                      <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        Required
                      </span>
                    )}
                  </h3>
                  <p className="text-sm text-gray-600">{category.description}</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={preferences[category.id] || false}
                    onChange={(e) => handlePreferenceChange(category.id, e.target.checked)}
                    disabled={category.required}
                    className="sr-only"
                  />
                  <div className={`relative w-11 h-6 rounded-full transition-colors ${
                    (preferences[category.id] || category.required)
                      ? 'bg-blue-600'
                      : 'bg-gray-300'
                  }`}>
                    <div className={`absolute top-0.5 left-0.5 bg-white w-5 h-5 rounded-full transition-transform ${
                      (preferences[category.id] || category.required) ? 'translate-x-5' : 'translate-x-0'
                    }`} />
                  </div>
                </label>
              </div>
              
              {category.cookies.length > 0 && (
                <div className="ml-4 text-xs text-gray-500">
                  <details className="mt-2">
                    <summary className="cursor-pointer hover:text-gray-700">
                      View cookies ({category.cookies.length})
                    </summary>
                    <div className="mt-2 space-y-1">
                      {category.cookies.map((cookie, index) => (
                        <div key={index} className="flex justify-between items-center py-1">
                          <span className="font-mono">{cookie.name}</span>
                          <span className="text-right">
                            {cookie.type} • {cookie.duration}
                          </span>
                        </div>
                      ))}
                    </div>
                  </details>
                </div>
              )}
              
              {category.purposes.length > 0 && (
                <div className="ml-4 text-xs text-gray-500 mt-2">
                  <strong>Purposes:</strong> {category.purposes.join(', ')}
                </div>
              )}
            </div>
          ))}
        </div>
        
        <div className="border-t p-6 flex justify-between">
          <Button
            variant="outline"
            onClick={() => setShowModal(false)}
            disabled={loading}
          >
            Cancel
          </Button>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={handleRejectAll}
              disabled={loading}
            >
              Reject All
            </Button>
            <Button
              onClick={handleSavePreferences}
              disabled={loading}
            >
              Save Preferences
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )

  // Current Consents Display (for settings page)
  const CurrentConsents = () => (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Current Consent Status</h3>
      <div className="space-y-4">
        {categories.map(category => {
          const consent = consents.find(c => c.consentType === category.id as any)
          return (
            <div key={category.id} className="flex items-center justify-between py-2 border-b last:border-b-0">
              <div>
                <div className="font-medium">{category.name}</div>
                <div className="text-sm text-gray-600">
                  Status: {consent?.granted ? 'Granted' : 'Not granted'}
                  {consent && (
                    <span className="ml-2">
                      • {new Date(consent.timestamp).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </div>
              {consent?.granted && !category.required && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleWithdrawConsent(category.id)}
                  className="text-red-600 hover:text-red-700"
                >
                  Withdraw
                </Button>
              )}
            </div>
          )
        })}
      </div>
      <div className="mt-4 pt-4 border-t">
        <Button
          variant="outline"
          onClick={handleCustomizeConsent}
          className="w-full"
        >
          Update Preferences
        </Button>
      </div>
    </Card>
  )

  return (
    <>
      {showBannerState && <ConsentBanner />}
      {showModal && <ConsentModal />}
      <CurrentConsents />
    </>
  )
}

export default ConsentManager