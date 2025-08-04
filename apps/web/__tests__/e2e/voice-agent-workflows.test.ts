import { test, expect, Page, BrowserContext } from '@playwright/test'

// End-to-end tests for critical voice agent workflows
// These tests validate complete user journeys through the voice AI system

interface VoiceAgentTestContext {
  page: Page
  context: BrowserContext
  agentId: string
  leadId: string
}

// Test data and configuration
const TEST_CONFIG = {
  VOICE_AGENT_URL: 'http://localhost:3000/enterprise/voice-agent',
  DASHBOARD_URL: 'http://localhost:3000/dashboard',
  API_BASE_URL: 'http://localhost:8000/api',
  TIMEOUT: {
    NAVIGATION: 30000,
    VOICE_RESPONSE: 5000,
    API_RESPONSE: 10000,
  },
  LEAD_DATA: {
    name: 'John Smith',
    phone: '+1-555-123-4567',
    email: 'john.smith@example.com',
    inquiry: 'Looking for a 3-bedroom house in downtown area',
    budget: { min: 350000, max: 500000 },
  },
}

test.describe('Voice Agent End-to-End Workflows', () => {
  let testContext: VoiceAgentTestContext

  test.beforeEach(async ({ page, context }) => {
    testContext = {
      page,
      context,
      agentId: `test-agent-${Date.now()}`,
      leadId: `test-lead-${Date.now()}`,
    }

    // Setup test environment
    await page.goto(TEST_CONFIG.VOICE_AGENT_URL)
    await page.waitForLoadState('networkidle')
    
    // Ensure microphone permissions are granted
    await context.grantPermissions(['microphone'])
  })

  test.describe('Complete Lead Qualification Workflow', () => {
    test('successfully qualifies a lead through voice conversation', async () => {
      const { page } = testContext

      // 1. Start voice agent
      await page.click('[data-testid="activate-agent-button"]')
      await expect(page.locator('[data-testid="agent-status"]')).toContainText('active')

      // 2. Simulate incoming call
      await page.click('[data-testid="simulate-incoming-call"]')
      await page.fill('[data-testid="caller-name"]', TEST_CONFIG.LEAD_DATA.name)
      await page.fill('[data-testid="caller-phone"]', TEST_CONFIG.LEAD_DATA.phone)
      await page.click('[data-testid="accept-call"]')

      // 3. Verify call is active
      await expect(page.locator('[data-testid="active-call-status"]')).toContainText('active')
      await expect(page.locator('[data-testid="caller-name-display"]')).toContainText(TEST_CONFIG.LEAD_DATA.name)

      // 4. Simulate voice interaction (using mock voice input)
      await page.click('[data-testid="mic-button"]')
      await page.evaluate(() => {
        // Simulate voice input via mock speech recognition
        window.dispatchEvent(new CustomEvent('mockSpeechRecognition', {
          detail: { text: 'Hello, I am looking for a house in downtown' }
        }))
      })

      // 5. Verify speech is recognized and processed
      await expect(page.locator('[data-testid="transcript"]')).toContainText('looking for a house')
      
      // 6. Wait for AI response
      await page.waitForSelector('[data-testid="agent-response"]', { 
        timeout: TEST_CONFIG.TIMEOUT.VOICE_RESPONSE 
      })

      // 7. Continue conversation to gather qualification data
      const qualificationQuestions = [
        'My budget is between $350,000 and $500,000',
        'I need at least 3 bedrooms and 2 bathrooms',
        'I prefer downtown or midtown area',
        'I am looking to buy within the next 2 months'
      ]

      for (const response of qualificationQuestions) {
        await page.evaluate((text) => {
          window.dispatchEvent(new CustomEvent('mockSpeechRecognition', {
            detail: { text }
          }))
        }, response)
        
        await page.waitForTimeout(2000) // Allow processing time
      }

      // 8. Verify lead qualification score is calculated
      await expect(page.locator('[data-testid="qualification-score"]')).toBeVisible()
      
      const qualificationScore = await page.locator('[data-testid="qualification-score"]').textContent()
      expect(parseInt(qualificationScore || '0')).toBeGreaterThan(70)

      // 9. Verify qualification data is captured
      await expect(page.locator('[data-testid="budget-range"]')).toContainText('$350,000')
      await expect(page.locator('[data-testid="property-type"]')).toContainText('3 bedrooms')
      await expect(page.locator('[data-testid="timeline"]')).toContainText('2 months')

      // 10. End call and verify data persistence
      await page.click('[data-testid="end-call-button"]')
      await expect(page.locator('[data-testid="call-summary"]')).toBeVisible()
      
      // 11. Navigate to dashboard and verify lead is created
      await page.goto(TEST_CONFIG.DASHBOARD_URL)
      await page.waitForLoadState('networkidle')
      
      await expect(page.locator(`[data-testid="lead-${TEST_CONFIG.LEAD_DATA.name}"]`)).toBeVisible()
    })

    test('handles multiple concurrent conversations', async () => {
      const { page, context } = testContext

      // Open multiple tabs for concurrent conversations
      const page2 = await context.newPage()
      const page3 = await context.newPage()

      await Promise.all([
        page.goto(TEST_CONFIG.VOICE_AGENT_URL),
        page2.goto(TEST_CONFIG.VOICE_AGENT_URL),
        page3.goto(TEST_CONFIG.VOICE_AGENT_URL),
      ])

      // Start agents on all pages
      await Promise.all([
        page.click('[data-testid="activate-agent-button"]'),
        page2.click('[data-testid="activate-agent-button"]'),
        page3.click('[data-testid="activate-agent-button"]'),
      ])

      // Verify all agents are active
      await Promise.all([
        expect(page.locator('[data-testid="agent-status"]')).toContainText('active'),
        expect(page2.locator('[data-testid="agent-status"]')).toContainText('active'),
        expect(page3.locator('[data-testid="agent-status"]')).toContainText('active'),
      ])

      // Simulate concurrent calls
      const callPromises = [
        simulateCall(page, 'Lead 1', '+1-555-001-0001'),
        simulateCall(page2, 'Lead 2', '+1-555-002-0002'),
        simulateCall(page3, 'Lead 3', '+1-555-003-0003'),
      ]

      await Promise.allSettled(callPromises)

      // Verify all calls are handled successfully
      await Promise.all([
        expect(page.locator('[data-testid="active-call-status"]')).toContainText('active'),
        expect(page2.locator('[data-testid="active-call-status"]')).toContainText('active'),
        expect(page3.locator('[data-testid="active-call-status"]')).toContainText('active'),
      ])
    })
  })

  test.describe('Voice Quality and Performance', () => {
    test('maintains voice quality throughout conversation', async () => {
      const { page } = testContext

      await page.click('[data-testid="activate-agent-button"]')
      await simulateCall(page, TEST_CONFIG.LEAD_DATA.name, TEST_CONFIG.LEAD_DATA.phone)

      // Monitor voice quality metrics
      const qualityMetrics = await page.evaluate(async () => {
        const metrics = []
        
        // Simulate 10 voice exchanges
        for (let i = 0; i < 10; i++) {
          window.dispatchEvent(new CustomEvent('mockSpeechRecognition', {
            detail: { text: `Voice quality test message ${i + 1}` }
          }))
          
          await new Promise(resolve => setTimeout(resolve, 1000))
          
          // Capture quality metrics
          const qualityElement = document.querySelector('[data-testid="call-quality"]')
          if (qualityElement) {
            metrics.push(qualityElement.textContent)
          }
        }
        
        return metrics
      })

      // Verify quality remains good throughout
      qualityMetrics.forEach(quality => {
        expect(['excellent', 'good'].includes(quality || '')).toBeTruthy()
      })
    })

    test('meets response time benchmarks', async () => {
      const { page } = testContext

      await page.click('[data-testid="activate-agent-button"]')
      await simulateCall(page, TEST_CONFIG.LEAD_DATA.name, TEST_CONFIG.LEAD_DATA.phone)

      // Test response times
      const responseTimes = await page.evaluate(async () => {
        const times = []
        
        for (let i = 0; i < 5; i++) {
          const startTime = performance.now()
          
          window.dispatchEvent(new CustomEvent('mockSpeechRecognition', {
            detail: { text: `Response time test ${i + 1}` }
          }))
          
          // Wait for agent response
          await new Promise(resolve => {
            const checkResponse = () => {
              if (document.querySelector('[data-testid="agent-response"]')) {
                const endTime = performance.now()
                times.push(endTime - startTime)
                resolve(undefined)
              } else {
                setTimeout(checkResponse, 10)
              }
            }
            checkResponse()
          })
        }
        
        return times
      })

      // All response times should be under 180ms benchmark
      responseTimes.forEach(time => {
        expect(time).toBeLessThan(180)
      })

      // Average response time should be well under benchmark
      const averageTime = responseTimes.reduce((a, b) => a + b) / responseTimes.length
      expect(averageTime).toBeLessThan(120)
    })
  })

  test.describe('Error Recovery and Resilience', () => {
    test('recovers from voice processing errors', async () => {
      const { page } = testContext

      await page.click('[data-testid="activate-agent-button"]')
      await simulateCall(page, TEST_CONFIG.LEAD_DATA.name, TEST_CONFIG.LEAD_DATA.phone)

      // Simulate voice processing error
      await page.evaluate(() => {
        window.dispatchEvent(new CustomEvent('mockVoiceError', {
          detail: { error: 'Speech recognition failed' }
        }))
      })

      // Verify error is displayed
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible()

      // Attempt recovery
      await page.click('[data-testid="retry-voice-button"]')

      // Verify system recovers
      await page.evaluate(() => {
        window.dispatchEvent(new CustomEvent('mockSpeechRecognition', {
          detail: { text: 'Recovery test message' }
        }))
      })

      await expect(page.locator('[data-testid="transcript"]')).toContainText('Recovery test message')
      await expect(page.locator('[data-testid="error-message"]')).not.toBeVisible()
    })

    test('handles network interruptions gracefully', async () => {
      const { page, context } = testContext

      await page.click('[data-testid="activate-agent-button"]')
      await simulateCall(page, TEST_CONFIG.LEAD_DATA.name, TEST_CONFIG.LEAD_DATA.phone)

      // Simulate network interruption
      await context.setOffline(true)
      
      // Verify offline state is handled
      await expect(page.locator('[data-testid="connection-status"]')).toContainText('disconnected')

      // Restore network
      await context.setOffline(false)

      // Verify reconnection
      await expect(page.locator('[data-testid="connection-status"]')).toContainText('connected')
      
      // Verify conversation can continue
      await page.evaluate(() => {
        window.dispatchEvent(new CustomEvent('mockSpeechRecognition', {
          detail: { text: 'Network recovery test' }
        }))
      })

      await expect(page.locator('[data-testid="transcript"]')).toContainText('Network recovery test')
    })
  })

  test.describe('Multi-Tenant Isolation', () => {
    test('isolates voice agent data by tenant', async () => {
      const { page, context } = testContext

      // Setup tenant 1
      await page.goto(`${TEST_CONFIG.VOICE_AGENT_URL}?tenant=tenant1`)
      await page.click('[data-testid="activate-agent-button"]')
      await simulateCall(page, 'Tenant 1 Lead', '+1-555-111-1111')

      // Open new tab for tenant 2
      const page2 = await context.newPage()
      await page2.goto(`${TEST_CONFIG.VOICE_AGENT_URL}?tenant=tenant2`)
      await page2.click('[data-testid="activate-agent-button"]')
      await simulateCall(page2, 'Tenant 2 Lead', '+1-555-222-2222')

      // Verify tenant 1 only sees their data
      await expect(page.locator('[data-testid="caller-name-display"]')).toContainText('Tenant 1 Lead')
      await expect(page.locator('[data-testid="caller-name-display"]')).not.toContainText('Tenant 2 Lead')

      // Verify tenant 2 only sees their data
      await expect(page2.locator('[data-testid="caller-name-display"]')).toContainText('Tenant 2 Lead')
      await expect(page2.locator('[data-testid="caller-name-display"]')).not.toContainText('Tenant 1 Lead')
    })
  })

  test.describe('Accessibility Compliance', () => {
    test('supports keyboard navigation', async () => {
      const { page } = testContext

      // Navigate using only keyboard
      await page.keyboard.press('Tab') // Focus first element
      await page.keyboard.press('Enter') // Activate agent
      
      await expect(page.locator('[data-testid="agent-status"]')).toContainText('active')

      // Navigate to emergency stop using keyboard
      await page.keyboard.press('Tab')
      await page.keyboard.press('Tab')
      await page.keyboard.press('Enter')

      await expect(page.locator('[data-testid="agent-status"]')).toContainText('maintenance')
    })

    test('provides screen reader compatibility', async () => {
      const { page } = testContext

      // Check for ARIA labels and roles
      const ariaElements = await page.locator('[aria-label]').count()
      expect(ariaElements).toBeGreaterThan(5)

      const roleElements = await page.locator('[role]').count()
      expect(roleElements).toBeGreaterThan(3)

      // Check for live regions for dynamic content
      await expect(page.locator('[aria-live]')).toBeVisible()
    })

    test('maintains accessibility during voice interactions', async () => {
      const { page } = testContext

      await page.click('[data-testid="activate-agent-button"]')
      await simulateCall(page, TEST_CONFIG.LEAD_DATA.name, TEST_CONFIG.LEAD_DATA.phone)

      // Voice controls should remain accessible
      const micButton = page.locator('[data-testid="mic-button"]')
      await expect(micButton).toHaveAttribute('aria-label')
      await expect(micButton).toBeEnabled()

      // Transcript should be accessible
      const transcript = page.locator('[data-testid="transcript"]')
      await expect(transcript).toHaveAttribute('role', 'log')
      await expect(transcript).toHaveAttribute('aria-live', 'polite')
    })
  })

  test.describe('Performance Under Load', () => {
    test('maintains performance with extended conversations', async () => {
      const { page } = testContext

      await page.click('[data-testid="activate-agent-button"]')
      await simulateCall(page, TEST_CONFIG.LEAD_DATA.name, TEST_CONFIG.LEAD_DATA.phone)

      // Simulate long conversation (50 exchanges)
      const startTime = Date.now()

      for (let i = 0; i < 50; i++) {
        await page.evaluate((index) => {
          window.dispatchEvent(new CustomEvent('mockSpeechRecognition', {
            detail: { text: `Extended conversation message ${index + 1}` }
          }))
        }, i)
        
        await page.waitForTimeout(100) // Small delay between messages
      }

      const endTime = Date.now()
      const totalTime = endTime - startTime

      // Should handle extended conversation efficiently
      expect(totalTime).toBeLessThan(30000) // Under 30 seconds for 50 exchanges

      // Verify final state is correct
      const transcriptMessages = await page.locator('[data-testid="transcript"] .message').count()
      expect(transcriptMessages).toBeGreaterThan(40) // Should have most messages
    })
  })
})

// Helper function to simulate a call
async function simulateCall(page: Page, callerName: string, callerPhone: string) {
  await page.click('[data-testid="simulate-incoming-call"]')
  await page.fill('[data-testid="caller-name"]', callerName)
  await page.fill('[data-testid="caller-phone"]', callerPhone)
  await page.click('[data-testid="accept-call"]')
  
  await expect(page.locator('[data-testid="active-call-status"]')).toContainText('active')
}

// Performance utility
async function measurePageLoadTime(page: Page, url: string): Promise<number> {
  const startTime = Date.now()
  await page.goto(url)
  await page.waitForLoadState('networkidle')
  return Date.now() - startTime
}

// Accessibility testing utility
async function runAccessibilityAudit(page: Page): Promise<any[]> {
  return await page.evaluate(() => {
    // Mock accessibility audit (in real implementation, use axe-core)
    const violations = []
    
    // Check for missing alt text
    const images = document.querySelectorAll('img:not([alt])')
    if (images.length > 0) {
      violations.push({ rule: 'image-alt', elements: images.length })
    }
    
    // Check for missing form labels
    const unlabeledInputs = document.querySelectorAll('input:not([aria-label]):not([aria-labelledby])')
    if (unlabeledInputs.length > 0) {
      violations.push({ rule: 'label', elements: unlabeledInputs.length })
    }
    
    return violations
  })
}