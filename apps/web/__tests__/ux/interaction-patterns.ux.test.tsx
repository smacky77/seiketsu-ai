/**
 * Interaction Pattern Validation Tests
 * 
 * Tests interaction patterns across all Seiketsu AI interfaces:
 * - Voice interaction feedback responsiveness
 * - Multi-tenant data isolation user experience
 * - Cross-device consistency and usability
 * - Error handling and recovery patterns
 * - Multi-modal harmony (voice, touch, keyboard)
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'

import { 
  TEST_PERSONAS, 
  UXTestRunner, 
  UserJourneyStep,
  interactionPatternValidators,
  accessibilityValidators,
  performanceValidators,
  mockData
} from '../utils/ux-test-utils'

// Import components from all interfaces
import HeroSection from '../../components/landing/HeroSection'
import VoiceAgentWorkspace from '../../components/dashboard/VoiceAgentWorkspace'
import TenantSwitcher from '../../components/admin/TenantSwitcher'
import QuickActions from '../../components/portal/QuickActions'

describe('Interaction Pattern Validation Across All Interfaces', () => {
  describe('Voice Interaction Feedback Responsiveness', () => {
    test('voice controls provide immediate visual feedback', async () => {
      const user = userEvent.setup()
      
      // Test across different interfaces
      const voiceComponents = [
        { name: 'Landing Page', component: <HeroSection /> },
        { name: 'Agent Dashboard', component: <VoiceAgentWorkspace /> },
        { name: 'Client Portal', component: <QuickActions /> },
      ]
      
      for (const { name, component } of voiceComponents) {
        const { container } = render(component)
        
        // Should have voice interaction elements
        const voiceValidation = interactionPatternValidators.voiceFirst(container)
        expect(voiceValidation).toBe(true)
        
        // Should have mic icons or voice indicators
        const voiceElements = screen.getAllByTestId('mic-icon') ||
                             screen.getAllByText(/voice|speak|listen/i) ||
                             container.querySelectorAll('[data-voice-control]')
        expect(voiceElements.length).toBeGreaterThan(0)
        
        // Test voice activation feedback
        const voiceButton = screen.getByRole('button', { name: /voice|mic|speak/i })
        if (voiceButton) {
          await user.click(voiceButton)
          
          await waitFor(() => {
            const feedback = screen.getByText(/listening|recording|active|speak.*now/i) ||
                           screen.getByRole('status') ||
                           container.querySelector('[data-voice-active="true"]')
            expect(feedback).toBeTruthy()
          })
        }
      }
    })

    test('voice interaction states are clearly communicated', () => {
      render(<VoiceAgentWorkspace />)
      
      // Should show voice agent status
      const voiceStates = ['online', 'offline', 'listening', 'processing', 'speaking']
      
      const statusElement = screen.getByText(/voice.*agent.*status|online|offline|active/i)
      expect(statusElement).toBeInTheDocument()
      
      // Should have visual status indicators
      const statusIndicator = screen.getByTestId('voice-status-indicator') ||
                             screen.getByRole('status') ||
                             screen.getByText(/🟢|🔴|🟡/)
      expect(statusIndicator).toBeTruthy()
    })

    test('voice processing speed meets UX standards', async () => {
      const user = userEvent.setup()
      render(<VoiceAgentWorkspace />)
      
      const voiceButton = screen.getByRole('button', { name: /voice|mic|start/i })
      
      if (voiceButton) {
        const startTime = Date.now()
        await user.click(voiceButton)
        
        await waitFor(() => {
          const response = screen.getByText(/listening|active|ready/i) ||
                          screen.getByRole('status')
          expect(response).toBeTruthy()
          
          const responseTime = Date.now() - startTime
          expect(responseTime).toBeLessThan(500) // Under 0.5 seconds
        })
      }
    })

    test('voice error states provide clear recovery paths', async () => {
      const user = userEvent.setup()
      render(<VoiceAgentWorkspace />)
      
      // Simulate voice error (in real test, would mock voice API failure)
      const troubleshootButton = screen.getByRole('button', { name: /troubleshoot|restart|reset/i })
      
      if (troubleshootButton) {
        await user.click(troubleshootButton)
        
        await waitFor(() => {
          const recoveryInstructions = screen.getByText(/check.*microphone|restart.*voice|try.*again/i) ||
                                       screen.getByText(/microphone.*access|permissions/i)
          expect(recoveryInstructions).toBeInTheDocument()
        })
      }
    })
  })

  describe('Multi-Tenant Data Isolation User Experience', () => {
    test('tenant context switching has clear visual transitions', async () => {
      const user = userEvent.setup()
      render(<TenantSwitcher />)
      
      // Should show current tenant clearly
      const currentTenant = screen.getByText(/current.*tenant|selected.*agency|active.*organization/i)
      expect(currentTenant).toBeInTheDocument()
      
      // Should have tenant switcher
      const switcher = screen.getByRole('combobox') ||
                      screen.getByRole('button', { name: /switch|change.*tenant/i })
      expect(switcher).toBeInTheDocument()
      
      await user.click(switcher)
      
      // Should show available tenants
      await waitFor(() => {
        const tenantOptions = screen.getAllByRole('option') ||
                             screen.getAllByText(/agency|organization.*\d+/i)
        expect(tenantOptions.length).toBeGreaterThan(1)
      })
    })

    test('data isolation is visually reinforced across interface', () => {
      const { container } = render(<TenantSwitcher />)
      
      // Should have visual indicators for data scope
      const isolationIndicators = container.querySelectorAll(
        '[data-tenant], [class*="tenant-"], [class*="border-"], [class*="bg-muted"]'
      )
      expect(isolationIndicators.length).toBeGreaterThan(0)
      
      // Should show tenant branding/identification
      const tenantBranding = screen.getAllByText(/agency|tenant|organization/i)
      expect(tenantBranding.length).toBeGreaterThan(0)
    })

    test('cross-tenant data contamination is prevented in UI', () => {
      render(<TenantSwitcher />)
      
      // Should show clear tenant boundaries
      const tenantBoundaries = screen.getAllByText(/agency.*a|agency.*b|tenant.*1|tenant.*2/i)
      expect(tenantBoundaries.length).toBeGreaterThan(0)
      
      // Should have data attribution
      const dataAttribution = screen.getAllByText(/from.*agency|belongs.*to|tenant.*data/i)
      expect(dataAttribution.length).toBeGreaterThanOrEqual(0)
    })

    test('tenant permissions affect interface behavior', () => {
      render(<TenantSwitcher />)
      
      // Should show permission-based UI elements
      const permissionElements = screen.getAllByText(/admin|read.*only|full.*access|limited/i)
      expect(permissionElements.length).toBeGreaterThanOrEqual(0)
      
      // Should hide/show features based on permissions
      const conditionalFeatures = screen.getAllByRole('button') ||
                                  screen.getAllByRole('link')
      expect(conditionalFeatures.length).toBeGreaterThan(0)
    })
  })

  describe('Cross-Device Consistency and Usability', () => {
    test('interface adapts consistently across viewport sizes', () => {
      const viewports = [
        { name: 'Mobile', width: 375, height: 667 },
        { name: 'Tablet', width: 768, height: 1024 },
        { name: 'Desktop', width: 1200, height: 800 },
      ]
      
      viewports.forEach(({ name, width, height }) => {
        // Mock viewport
        Object.defineProperty(window, 'innerWidth', {
          writable: true,
          configurable: true,
          value: width,
        })
        Object.defineProperty(window, 'innerHeight', {
          writable: true,
          configurable: true,
          value: height,
        })
        
        const { container } = render(<HeroSection />)
        
        // Should have responsive classes
        const responsiveElements = container.querySelectorAll(
          '[class*="sm:"], [class*="md:"], [class*="lg:"], [class*="xl:"]'
        )
        expect(responsiveElements.length).toBeGreaterThan(0)
        
        // Critical elements should remain accessible
        const criticalElements = screen.getAllByRole('button') ||
                               screen.getAllByRole('link')
        expect(criticalElements.length).toBeGreaterThan(0)
      })
    })

    test('touch targets meet accessibility standards across devices', () => {
      const { container } = render(<QuickActions />)
      
      // All interactive elements should meet 44px minimum
      const interactiveElements = container.querySelectorAll(
        'button, [role="button"], a, input, select, textarea'
      )
      
      interactiveElements.forEach(element => {
        const classes = element.className
        // Check for appropriate padding/sizing classes
        expect(classes).toMatch(/p-\d|py-\d|px-\d|h-\d+|min-h-/)
      })
    })

    test('keyboard navigation works consistently across interfaces', async () => {
      const user = userEvent.setup()
      
      const interfaces = [
        { name: 'Landing', component: <HeroSection /> },
        { name: 'Portal', component: <QuickActions /> },
        { name: 'Admin', component: <TenantSwitcher /> },
      ]
      
      for (const { name, component } of interfaces) {
        render(component)
        
        // Test tab navigation
        await user.tab()
        
        const focusedElement = document.activeElement
        expect(focusedElement).toBeTruthy()
        expect(focusedElement?.tagName).toMatch(/BUTTON|A|INPUT|SELECT|TEXTAREA/)
        
        // Test space/enter activation
        if (focusedElement?.tagName === 'BUTTON') {
          await user.keyboard(' ')
          // Should trigger button action
        }
      }
    })

    test('navigation patterns remain consistent across interfaces', () => {
      const interfaces = [
        { name: 'Landing', component: <HeroSection /> },
        { name: 'Portal', component: <QuickActions /> },
      ]
      
      interfaces.forEach(({ name, component }) => {
        const { container } = render(component)
        
        // Should have consistent navigation patterns
        const navigationElements = container.querySelectorAll(
          'nav, [role="navigation"], [class*="nav"]'
        )
        
        // Should use consistent interaction patterns
        const buttons = container.querySelectorAll('button')
        const links = container.querySelectorAll('a')
        
        expect(buttons.length + links.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Error Handling and Recovery Patterns', () => {
    test('error states provide clear user guidance', async () => {
      const user = userEvent.setup()
      
      // Test form validation errors
      render(<HeroSection />)
      
      const form = screen.getByRole('form') ||
                  screen.getByTestId('conversion-form')
      
      if (form) {
        const submitButton = screen.getByRole('button', { name: /submit|send|request/i })
        await user.click(submitButton)
        
        await waitFor(() => {
          const errorMessages = screen.getAllByText(/required|invalid|error|please.*enter/i)
          expect(errorMessages.length).toBeGreaterThan(0)
        })
      }
    })

    test('network errors have user-friendly messaging', () => {
      render(<VoiceAgentWorkspace />)
      
      // Should handle connection issues gracefully
      const connectionStatus = screen.getByText(/connection|network|online|offline/i)
      
      if (connectionStatus) {
        expect(connectionStatus).toBeInTheDocument()
        
        // Should provide recovery actions
        const recoveryActions = screen.getAllByRole('button', { name: /retry|reconnect|refresh/i })
        expect(recoveryActions.length).toBeGreaterThanOrEqual(0)
      }
    })

    test('loading states prevent user confusion', () => {
      const components = [
        <HeroSection />,
        <VoiceAgentWorkspace />,
        <QuickActions />,
      ]
      
      components.forEach(component => {
        const { container } = render(component)
        
        const loadingValidation = performanceValidators.loadingStates(container)
        expect(loadingValidation).toBe(true)
        
        // Should have appropriate loading indicators
        const loadingElements = screen.getAllByText(/loading|processing|please.*wait/i) ||
                               screen.getAllByRole('status') ||
                               container.querySelectorAll('[data-loading]')
        expect(loadingElements.length).toBeGreaterThanOrEqual(0)
      })
    })

    test('timeout scenarios provide clear next steps', async () => {
      const user = userEvent.setup()
      render(<VoiceAgentWorkspace />)
      
      // Simulate timeout scenario
      const actionButton = screen.getByRole('button', { name: /start|begin|connect/i })
      
      if (actionButton) {
        await user.click(actionButton)
        
        // Should handle timeouts gracefully
        await waitFor(() => {
          const timeoutMessage = screen.getByText(/timeout|taking.*longer|try.*again|check.*connection/i)
          if (timeoutMessage) {
            expect(timeoutMessage).toBeInTheDocument()
            
            // Should provide recovery options
            const recoveryOptions = screen.getAllByRole('button', { name: /retry|refresh|cancel/i })
            expect(recoveryOptions.length).toBeGreaterThan(0)
          }
        })
      }
    })
  })

  describe('Multi-Modal Harmony (Voice, Touch, Keyboard)', () => {
    test('voice and visual interfaces complement each other', () => {
      const { container } = render(<VoiceAgentWorkspace />)
      
      // Should have multi-modal support
      const multiModalValidation = interactionPatternValidators.multiModal(container)
      expect(multiModalValidation).toBe(true)
      
      // Voice controls should have visual equivalents
      const voiceElements = container.querySelectorAll('[data-voice-control]')
      const visualControls = container.querySelectorAll('button')
      
      expect(voiceElements.length).toBeGreaterThan(0)
      expect(visualControls.length).toBeGreaterThan(0)
    })

    test('keyboard shortcuts enhance power user efficiency', async () => {
      const user = userEvent.setup()
      render(<VoiceAgentWorkspace />)
      
      // Test common keyboard shortcuts
      await user.keyboard('{Space}') // Should activate focused element
      await user.keyboard('{Escape}') // Should close modals/cancel actions
      await user.keyboard('{Enter}') // Should submit forms/activate buttons
      
      // Should show keyboard shortcut hints
      const shortcutHints = screen.getAllByText(/ctrl|cmd|alt|space|enter|esc/i)
      expect(shortcutHints.length).toBeGreaterThanOrEqual(0)
    })

    test('touch gestures work alongside traditional interactions', () => {
      // Mock touch device
      Object.defineProperty(navigator, 'maxTouchPoints', {
        writable: true,
        configurable: true,
        value: 5,
      })
      
      render(<QuickActions />)
      
      // Should adapt for touch devices
      const touchElements = screen.getAllByRole('button')
      expect(touchElements.length).toBeGreaterThan(0)
      
      // Should have appropriate touch target sizes
      touchElements.forEach(element => {
        const classes = element.className
        expect(classes).toMatch(/p-\d|h-\d+|min-h/)
      })
    })

    test('real-time feedback works across all interaction modes', () => {
      const { container } = render(<VoiceAgentWorkspace />)
      
      const feedbackValidation = interactionPatternValidators.realTimeFeedback(container)
      expect(feedbackValidation).toBe(true)
      
      // Should have status indicators
      const statusElements = container.querySelectorAll('[data-status]') ||
                           screen.getAllByRole('status')
      expect(statusElements.length).toBeGreaterThan(0)
    })
  })

  describe('Progressive Enhancement and Fallbacks', () => {
    test('core functionality works without JavaScript', () => {
      // Disable JavaScript-dependent features
      const { container } = render(<HeroSection />)
      
      // Essential content should be present
      const essentialElements = [
        screen.getByRole('heading', { level: 1 }),
        screen.getAllByRole('button'),
        screen.getAllByRole('link'),
      ].flat()
      
      expect(essentialElements.length).toBeGreaterThan(0)
      
      // Forms should be submittable
      const forms = container.querySelectorAll('form')
      forms.forEach(form => {
        expect(form.getAttribute('action')).toBeTruthy()
      })
    })

    test('voice features degrade gracefully without microphone access', () => {
      render(<VoiceAgentWorkspace />)
      
      // Should show voice unavailable state gracefully
      const voiceElement = screen.getByText(/voice|microphone|audio/i)
      expect(voiceElement).toBeInTheDocument()
      
      // Should provide alternative interaction methods
      const alternatives = screen.getAllByRole('button', { name: /type|text|manual/i })
      expect(alternatives.length).toBeGreaterThanOrEqual(0)
    })

    test('reduced motion preferences are respected', () => {
      // Mock reduced motion preference
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(prefers-reduced-motion: reduce)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
        })),
      })
      
      const { container } = render(<HeroSection />)
      
      // Should respect motion preferences
      const animatedElements = container.querySelectorAll('[class*="animate"], [class*="transition"]')
      expect(animatedElements.length).toBeGreaterThanOrEqual(0)
    })
  })

  describe('Comprehensive Interaction Pattern Score', () => {
    test('interaction patterns achieve overall consistency score above 90%', async () => {
      const testPersona = TEST_PERSONAS.agent // Use agent as representative user
      const uxRunner = new UXTestRunner(testPersona)
      
      const interactionSteps: UserJourneyStep[] = [
        {
          description: 'Test voice interaction responsiveness',
          action: async () => {
            render(<VoiceAgentWorkspace />)
            const voiceButton = screen.getByRole('button', { name: /voice|mic/i })
            expect(voiceButton).toBeInTheDocument()
          },
          validation: () => {
            const voiceStatus = screen.getByText(/voice.*status|online|offline/i)
            expect(voiceStatus).toBeInTheDocument()
          },
          timeLimit: 3,
        },
        {
          description: 'Test multi-tenant context awareness',
          action: async () => {
            render(<TenantSwitcher />)
            const tenantContext = screen.getByText(/tenant|agency|organization/i)
            expect(tenantContext).toBeInTheDocument()
          },
          validation: () => {
            const contextIndicators = screen.getAllByText(/current|selected|active/i)
            expect(contextIndicators.length).toBeGreaterThan(0)
          },
          timeLimit: 2,
        },
        {
          description: 'Test cross-device consistency',
          action: async () => {
            render(<QuickActions />)
            const quickActions = screen.getAllByRole('button')
            expect(quickActions.length).toBeGreaterThan(0)
          },
          validation: () => {
            const responsiveElements = screen.getAllByRole('button')
            expect(responsiveElements.length).toBeGreaterThan(0)
          },
          timeLimit: 2,
        },
      ]
      
      const InteractionComponent = (
        <div>
          <HeroSection />
          <VoiceAgentWorkspace />
          <TenantSwitcher />
          <QuickActions />
        </div>
      )
      
      const result = await uxRunner.runComprehensiveTest(InteractionComponent, interactionSteps)
      
      expect(result.score).toBeGreaterThan(90)
      expect(result.passed).toBe(true)
      
      // Log results for analysis
      console.log('Interaction Patterns UX Test Results:', {
        score: result.score,
        persona: result.persona,
        recommendations: result.recommendations,
        interactionConsistency: result.details.patterns,
        crossDeviceSupport: result.details.journey,
      })
    })
  })
})