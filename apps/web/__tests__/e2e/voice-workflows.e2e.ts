/**
 * End-to-End tests for critical voice AI workflows
 * Tests complete user journeys using Playwright
 */
import { test, expect, Page, BrowserContext } from '@playwright/test'

// Test data and utilities
const TEST_USER = {
  email: 'e2e.test@example.com',
  password: 'E2ETestPassword123!',
  name: 'E2E Test User'
}

const TEST_AGENT_CONFIG = {
  name: 'E2E Test Agent',
  voice_id: 'test_voice_id',
  greeting: 'Hello! I\'m your AI real estate assistant.',
  personality: 'professional'
}

class VoiceWorkflowHelper {
  constructor(private page: Page) {}

  async mockVoiceAPIs() {
    // Mock ElevenLabs API
    await this.page.route('**/v1/text-to-speech/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'audio/mpeg',
        body: Buffer.from('mock-audio-data')
      })
    })

    // Mock OpenAI API
    await this.page.route('**/v1/chat/completions', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          choices: [{
            message: {
              content: 'I\'d be happy to help you find a property. What\'s your budget?',
              role: 'assistant'
            }
          }],
          usage: { total_tokens: 50 }
        })
      })
    })

    // Mock Whisper API
    await this.page.route('**/v1/audio/transcriptions', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          text: 'I\'m looking for a house under 500k'
        })
      })
    })
  }

  async mockMediaDevices() {
    // Mock MediaRecorder and getUserMedia
    await this.page.addInitScript(() => {
      // Mock MediaRecorder
      class MockMediaRecorder {
        state = 'inactive'
        ondataavailable: ((event: any) => void) | null = null
        onstop: (() => void) | null = null
        
        start() {
          this.state = 'recording'
          // Simulate data available
          setTimeout(() => {
            if (this.ondataavailable) {
              this.ondataavailable({
                data: new Blob(['mock-audio-data'], { type: 'audio/webm' })
              })
            }
          }, 100)
        }
        
        stop() {
          this.state = 'inactive'
          if (this.onstop) {
            this.onstop()
          }
        }
        
        addEventListener(event: string, handler: any) {
          if (event === 'dataavailable') {
            this.ondataavailable = handler
          } else if (event === 'stop') {
            this.onstop = handler
          }
        }
        
        removeEventListener() {}
      }
      
      window.MediaRecorder = MockMediaRecorder as any
      
      // Mock getUserMedia
      navigator.mediaDevices = {
        getUserMedia: async () => ({
          getTracks: () => [{ stop: () => {} }]
        })
      } as any
    })
  }

  async login() {
    await this.page.goto('/login')
    await this.page.fill('[data-testid="email-input"]', TEST_USER.email)
    await this.page.fill('[data-testid="password-input"]', TEST_USER.password)
    await this.page.click('[data-testid="login-button"]')
    await this.page.waitForURL('/dashboard')
  }

  async navigateToVoiceInterface() {
    await this.page.click('[data-testid="voice-ai-nav"]')
    await this.page.waitForSelector('[data-testid="voice-interface"]')
  }

  async startVoiceInteraction() {
    await this.page.click('[data-testid="start-voice-button"]')
    await expect(this.page.locator('[data-testid="voice-status"]')).toContainText('Listening')
  }

  async stopVoiceInteraction() {
    await this.page.click('[data-testid="stop-voice-button"]')
    await expect(this.page.locator('[data-testid="voice-status"]')).toContainText('Ready')
  }

  async waitForTranscript(expectedText?: string) {
    const transcriptLocator = this.page.locator('[data-testid="voice-transcript"]')
    await transcriptLocator.waitFor({ state: 'visible' })
    
    if (expectedText) {
      await expect(transcriptLocator).toContainText(expectedText)
    }
    
    return transcriptLocator
  }

  async waitForAIResponse(expectedText?: string) {
    const responseLocator = this.page.locator('[data-testid="ai-response"]')
    await responseLocator.waitFor({ state: 'visible' })
    
    if (expectedText) {
      await expect(responseLocator).toContainText(expectedText)
    }
    
    return responseLocator
  }
}

test.describe('Voice AI Workflows', () => {
  let helper: VoiceWorkflowHelper

  test.beforeEach(async ({ page, context }) => {
    helper = new VoiceWorkflowHelper(page)
    
    // Setup mocks
    await helper.mockVoiceAPIs()
    await helper.mockMediaDevices()
    
    // Mock authentication
    await context.addCookies([{
      name: 'session',
      value: 'mock-session-token',
      domain: 'localhost',
      path: '/'
    }])
  })

  test('Complete voice conversation workflow', async ({ page }) => {
    // Navigate to voice interface
    await page.goto('/dashboard')
    await helper.navigateToVoiceInterface()

    // Verify initial state
    await expect(page.locator('[data-testid="voice-status"]')).toContainText('Ready to listen')
    await expect(page.locator('[data-testid="start-voice-button"]')).toBeEnabled()

    // Start voice interaction
    await helper.startVoiceInteraction()

    // Verify listening state
    await expect(page.locator('[data-testid="voice-visualizer"]')).toBeVisible()
    await expect(page.locator('[data-testid="stop-voice-button"]')).toBeVisible()

    // Simulate voice input processing
    await page.waitForTimeout(2000) // Simulate speaking time

    // Stop recording
    await helper.stopVoiceInteraction()

    // Wait for transcript
    const transcript = await helper.waitForTranscript()
    await expect(transcript).toContainText('looking for a house')

    // Wait for AI response
    const response = await helper.waitForAIResponse()
    await expect(response).toContainText('help you find a property')

    // Verify conversation history is updated
    const conversationHistory = page.locator('[data-testid="conversation-history"]')
    await expect(conversationHistory.locator('[data-testid="user-message"]')).toBeVisible()
    await expect(conversationHistory.locator('[data-testid="ai-message"]')).toBeVisible()

    // Verify analytics tracking
    const analyticsEvents = await page.evaluate(() => 
      (window as any).__analytics_events || []
    )
    expect(analyticsEvents).toContainEqual(
      expect.objectContaining({
        event: 'voice_interaction_completed',
        properties: expect.objectContaining({
          transcript_length: expect.any(Number),
          response_time_ms: expect.any(Number)
        })
      })
    )
  })

  test('Voice agent configuration workflow', async ({ page }) => {
    await page.goto('/dashboard/voice-agents')

    // Create new voice agent
    await page.click('[data-testid="create-agent-button"]')
    await page.fill('[data-testid="agent-name-input"]', TEST_AGENT_CONFIG.name)
    await page.selectOption('[data-testid="voice-select"]', TEST_AGENT_CONFIG.voice_id)
    await page.fill('[data-testid="greeting-input"]', TEST_AGENT_CONFIG.greeting)
    await page.selectOption('[data-testid="personality-select"]', TEST_AGENT_CONFIG.personality)

    // Configure advanced settings
    await page.click('[data-testid="advanced-settings-toggle"]')
    await page.fill('[data-testid="response-time-input"]', '150')
    await page.fill('[data-testid="confidence-threshold-input"]', '0.8')

    // Save agent configuration
    await page.click('[data-testid="save-agent-button"]')

    // Verify agent was created
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible()
    await expect(page.locator(`[data-testid="agent-${TEST_AGENT_CONFIG.name}"]`)).toBeVisible()

    // Test agent with voice interface
    await page.click(`[data-testid="test-agent-${TEST_AGENT_CONFIG.name}"]`)
    await helper.navigateToVoiceInterface()

    // Verify agent greeting is displayed
    await expect(page.locator('[data-testid="agent-greeting"]')).toContainText(TEST_AGENT_CONFIG.greeting)

    // Test voice interaction with configured agent
    await helper.startVoiceInteraction()
    await page.waitForTimeout(1000)
    await helper.stopVoiceInteraction()

    // Verify response uses configured personality
    await helper.waitForAIResponse()
    const responseStyle = await page.locator('[data-testid="ai-response"]').getAttribute('data-personality')
    expect(responseStyle).toBe(TEST_AGENT_CONFIG.personality)
  })

  test('Lead qualification through voice workflow', async ({ page }) => {
    await helper.navigateToVoiceInterface()

    // Start conversation focused on lead qualification
    await helper.startVoiceInteraction()
    await page.waitForTimeout(1000)
    await helper.stopVoiceInteraction()

    // Mock transcript that should trigger lead qualification
    await page.evaluate(() => {
      // Simulate lead qualification scenario
      const mockQualificationData = {
        transcript: "I'm looking to buy a 3-bedroom house in downtown, budget is around 400k",
        aiResponse: "Great! I can help you find a 3-bedroom home in downtown within your budget.",
        leadData: {
          budget_min: 350000,
          budget_max: 450000,
          bedrooms: 3,
          location: "downtown",
          timeline: "3_months"
        }
      }

      // Trigger qualification flow
      window.dispatchEvent(new CustomEvent('leadQualified', { 
        detail: mockQualificationData 
      }))
    })

    // Verify lead qualification UI appears
    await expect(page.locator('[data-testid="lead-qualification-panel"]')).toBeVisible()
    
    // Check lead qualification details
    await expect(page.locator('[data-testid="lead-budget"]')).toContainText('$350,000 - $450,000')
    await expect(page.locator('[data-testid="lead-bedrooms"]')).toContainText('3')
    await expect(page.locator('[data-testid="lead-location"]')).toContainText('downtown')

    // Save qualified lead
    await page.click('[data-testid="save-lead-button"]')

    // Navigate to leads dashboard
    await page.click('[data-testid="leads-nav"]')
    await page.waitForURL('/dashboard/leads')

    // Verify lead appears in dashboard
    const leadRow = page.locator('[data-testid="lead-row"]').first()
    await expect(leadRow).toBeVisible()
    await expect(leadRow.locator('[data-testid="lead-source"]')).toContainText('Voice AI')
    await expect(leadRow.locator('[data-testid="lead-status"]')).toContainText('Qualified')

    // View lead details
    await leadRow.click()
    await expect(page.locator('[data-testid="lead-detail-panel"]')).toBeVisible()
    await expect(page.locator('[data-testid="lead-conversation-link"]')).toBeVisible()
  })

  test('Voice analytics and performance monitoring', async ({ page }) => {
    // Complete several voice interactions
    await helper.navigateToVoiceInterface()

    for (let i = 0; i < 3; i++) {
      await helper.startVoiceInteraction()
      await page.waitForTimeout(1500) // Vary interaction lengths
      await helper.stopVoiceInteraction()
      await helper.waitForTranscript()
      await helper.waitForAIResponse()
      await page.waitForTimeout(500)
    }

    // Navigate to analytics dashboard
    await page.click('[data-testid="analytics-nav"]')
    await page.waitForURL('/dashboard/analytics')

    // Verify voice interaction metrics
    const voiceMetrics = page.locator('[data-testid="voice-metrics-panel"]')
    await expect(voiceMetrics).toBeVisible()

    // Check key metrics are displayed
    await expect(voiceMetrics.locator('[data-testid="total-interactions"]')).toContainText('3')
    await expect(voiceMetrics.locator('[data-testid="avg-response-time"]')).toBeVisible()
    await expect(voiceMetrics.locator('[data-testid="confidence-score"]')).toBeVisible()
    await expect(voiceMetrics.locator('[data-testid="success-rate"]')).toBeVisible()

    // Verify performance charts
    await expect(page.locator('[data-testid="response-time-chart"]')).toBeVisible()
    await expect(page.locator('[data-testid="interaction-volume-chart"]')).toBeVisible()

    // Test drill-down functionality
    await page.click('[data-testid="view-interaction-details"]')
    await expect(page.locator('[data-testid="interaction-detail-modal"]')).toBeVisible()

    // Verify detailed interaction data
    const interactionDetails = page.locator('[data-testid="interaction-details"]')
    await expect(interactionDetails.locator('[data-testid="transcript-detail"]')).toBeVisible()
    await expect(interactionDetails.locator('[data-testid="response-detail"]')).toBeVisible()
    await expect(interactionDetails.locator('[data-testid="timing-breakdown"]')).toBeVisible()
  })

  test('Error handling and recovery workflows', async ({ page }) => {
    await helper.navigateToVoiceInterface()

    // Test microphone permission error
    await page.addInitScript(() => {
      navigator.mediaDevices.getUserMedia = async () => {
        throw new Error('Permission denied')
      }
    })

    await page.click('[data-testid="start-voice-button"]')

    // Verify error handling
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
    await expect(page.locator('[data-testid="error-message"]')).toContainText('microphone permission')

    // Test error recovery
    await page.click('[data-testid="grant-permission-button"]')
    await expect(page.locator('[data-testid="permission-instructions"]')).toBeVisible()

    // Test API error handling
    await page.route('**/api/v1/voice/process', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      })
    })

    // Mock successful permission grant
    await page.addInitScript(() => {
      navigator.mediaDevices.getUserMedia = async () => ({
        getTracks: () => [{ stop: () => {} }]
      })
    })

    await helper.startVoiceInteraction()
    await page.waitForTimeout(1000)
    await helper.stopVoiceInteraction()

    // Verify API error handling
    await expect(page.locator('[data-testid="processing-error"]')).toBeVisible()
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible()

    // Test retry functionality
    await page.route('**/api/v1/voice/process', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          transcript: 'Retry successful',
          response: 'I heard you this time!',
          confidence: 0.9
        })
      })
    })

    await page.click('[data-testid="retry-button"]')
    await helper.waitForTranscript('Retry successful')
    await helper.waitForAIResponse('I heard you this time')
  })

  test('Accessibility compliance for voice interface', async ({ page }) => {
    await helper.navigateToVoiceInterface()

    // Test keyboard navigation
    await page.keyboard.press('Tab')
    await expect(page.locator('[data-testid="start-voice-button"]')).toBeFocused()

    // Test spacebar activation
    await page.keyboard.press('Space')
    await expect(page.locator('[data-testid="voice-status"]')).toContainText('Listening')

    // Stop with spacebar
    await page.keyboard.press('Space')
    await expect(page.locator('[data-testid="voice-status"]')).toContainText('Ready')

    // Test ARIA attributes
    const voiceButton = page.locator('[data-testid="start-voice-button"]')
    await expect(voiceButton).toHaveAttribute('aria-describedby')
    await expect(voiceButton).toHaveAttribute('role', 'button')

    // Test screen reader announcements
    const statusRegion = page.locator('[role="status"]')
    await expect(statusRegion).toBeVisible()

    // Test high contrast mode support
    await page.emulateMedia({ colorScheme: 'dark' })
    await expect(page.locator('[data-testid="voice-interface"]')).toBeVisible()

    // Test focus management
    await helper.startVoiceInteraction()
    await expect(page.locator('[data-testid="stop-voice-button"]')).toBeFocused()
  })

  test('Performance under load simulation', async ({ page }) => {
    await helper.navigateToVoiceInterface()

    // Measure baseline performance
    const startTime = Date.now()

    // Simulate rapid voice interactions
    for (let i = 0; i < 5; i++) {
      await helper.startVoiceInteraction()
      await page.waitForTimeout(500)
      await helper.stopVoiceInteraction()
      await helper.waitForTranscript()
      await helper.waitForAIResponse()
    }

    const totalTime = Date.now() - startTime
    const averageTime = totalTime / 5

    // Verify performance is acceptable
    expect(averageTime).toBeLessThan(3000) // 3 seconds per interaction

    // Check for memory leaks
    const memoryUsage = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0
    })

    // Memory usage should be reasonable
    expect(memoryUsage).toBeLessThan(50 * 1024 * 1024) // 50MB threshold

    // Verify UI remains responsive
    await expect(page.locator('[data-testid="start-voice-button"]')).toBeEnabled()
  })
})

test.describe('Mobile Voice Workflows', () => {
  test.use({ 
    viewport: { width: 375, height: 667 }, // iPhone SE dimensions
    isMobile: true,
    hasTouch: true
  })

  test('Mobile voice interface workflow', async ({ page }) => {
    const helper = new VoiceWorkflowHelper(page)
    await helper.mockVoiceAPIs()
    await helper.mockMediaDevices()

    await page.goto('/dashboard')
    await helper.navigateToVoiceInterface()

    // Verify mobile-optimized layout
    await expect(page.locator('[data-testid="mobile-voice-interface"]')).toBeVisible()
    
    // Test touch interactions
    await page.tap('[data-testid="start-voice-button"]')
    await expect(page.locator('[data-testid="voice-status"]')).toContainText('Listening')

    // Verify mobile-specific features
    await expect(page.locator('[data-testid="voice-visualizer-mobile"]')).toBeVisible()
    
    // Test mobile gesture controls
    await page.tap('[data-testid="stop-voice-button"]')
    await helper.waitForTranscript()
    await helper.waitForAIResponse()

    // Verify mobile conversation history
    const conversationHistory = page.locator('[data-testid="mobile-conversation-history"]')
    await expect(conversationHistory).toBeVisible()
  })
})