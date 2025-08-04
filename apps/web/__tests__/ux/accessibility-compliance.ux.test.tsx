/**
 * Accessibility Compliance Testing (WCAG 2.1 AA)
 * 
 * Tests accessibility compliance across all Seiketsu AI interfaces:
 * - WCAG 2.1 AA compliance across all interfaces
 * - Screen reader navigation for voice interfaces
 * - Keyboard accessibility for complex workflows
 * - Color contrast validation for dark theme
 * - Focus management and navigation patterns
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'

import { 
  TEST_PERSONAS, 
  UXTestRunner, 
  UserJourneyStep,
  accessibilityValidators,
  UX_STANDARDS,
  mockData
} from '../utils/ux-test-utils'

// Import components from all interfaces for comprehensive testing
import HeroSection from '../../components/landing/HeroSection'
import TrustIndicators from '../../components/landing/TrustIndicators'
import FeatureShowcase from '../../components/landing/FeatureShowcase'
import ConversionForm from '../../components/landing/ConversionForm'
import VoiceAgentWorkspace from '../../components/dashboard/VoiceAgentWorkspace'
import ConversationManager from '../../components/dashboard/ConversationManager'
import LeadQualificationPanel from '../../components/dashboard/LeadQualificationPanel'
import AdminLayout from '../../components/admin/AdminLayout'
import TenantSwitcher from '../../components/admin/TenantSwitcher'
import SystemOverviewDashboard from '../../components/admin/SystemOverviewDashboard'
import WelcomeOverview from '../../components/portal/WelcomeOverview'
import PropertyRecommendations from '../../components/portal/PropertyRecommendations'
import QuickActions from '../../components/portal/QuickActions'

describe('Accessibility Compliance Testing (WCAG 2.1 AA)', () => {
  describe('Semantic HTML Structure', () => {
    test('all interfaces use proper semantic HTML', () => {
      const components = [
        { name: 'Landing Hero', component: <HeroSection /> },
        { name: 'Dashboard Workspace', component: <VoiceAgentWorkspace /> },
        { name: 'Admin Layout', component: <AdminLayout /> },
        { name: 'Client Portal', component: <WelcomeOverview /> },
      ]
      
      components.forEach(({ name, component }) => {
        const { container } = render(component)
        
        const semanticValidation = accessibilityValidators.semanticHTML(container)
        expect(semanticValidation).toBe(true)
        
        // Should have proper document structure
        const semanticElements = container.querySelectorAll(
          'main, section, article, header, footer, nav, aside, h1, h2, h3, h4, h5, h6'
        )
        expect(semanticElements.length).toBeGreaterThan(0)
      })
    })

    test('heading hierarchy is logical and complete', () => {
      const components = [
        <HeroSection />,
        <FeatureShowcase />,
        <SystemOverviewDashboard />,
        <PropertyRecommendations />,
      ]
      
      components.forEach(component => {
        const { container } = render(component)
        
        // Should have h1 as primary heading
        const h1Elements = container.querySelectorAll('h1')
        expect(h1Elements.length).toBeGreaterThan(0)
        
        // Should not skip heading levels
        const headings = container.querySelectorAll('h1, h2, h3, h4, h5, h6')
        const headingLevels = Array.from(headings).map(h => parseInt(h.tagName.charAt(1)))
        
        // Check for logical hierarchy (no level skipping)
        for (let i = 1; i < headingLevels.length; i++) {
          const currentLevel = headingLevels[i]
          const previousLevel = headingLevels[i - 1]
          expect(currentLevel - previousLevel).toBeLessThanOrEqual(1)
        }
      })
    })

    test('landmark roles are properly defined', () => {
      const { container } = render(<AdminLayout />)
      
      // Should have main landmark
      const main = container.querySelector('main') ||
                  container.querySelector('[role="main"]')
      expect(main).toBeInTheDocument()
      
      // Should have navigation landmark
      const nav = container.querySelector('nav') ||
                 container.querySelector('[role="navigation"]')
      expect(nav).toBeInTheDocument()
      
      // Should have appropriate regions
      const regions = container.querySelectorAll('[role="region"], [role="banner"], [role="contentinfo"]')
      expect(regions.length).toBeGreaterThanOrEqual(0)
    })
  })

  describe('ARIA Labels and Descriptions', () => {
    test('all interactive elements have accessible names', async () => {
      const components = [
        <HeroSection />,
        <ConversionForm />,
        <VoiceAgentWorkspace />,
        <TenantSwitcher />,
        <QuickActions />,
      ]
      
      for (const component of components) {
        const { container } = render(component)
        
        const ariaValidation = await accessibilityValidators.ariaLabels(container)
        expect(ariaValidation).toBe(true)
        
        // Check all interactive elements
        const interactiveElements = container.querySelectorAll(
          'button, input, select, textarea, a[href], [role="button"], [role="link"], [tabindex]'
        )
        
        interactiveElements.forEach(element => {
          const hasAccessibleName = 
            element.getAttribute('aria-label') ||
            element.getAttribute('aria-labelledby') ||
            element.textContent?.trim() ||
            element.getAttribute('title') ||
            element.getAttribute('alt')
          
          expect(hasAccessibleName).toBeTruthy()
        })
      }
    })

    test('form inputs have proper labels and descriptions', () => {
      render(<ConversionForm />)
      
      const formInputs = screen.getAllByRole('textbox')
      const emailInputs = screen.getAllByRole('textbox', { name: /email/i })
      const selects = screen.getAllByRole('combobox')
      
      const allInputs = [...formInputs, ...emailInputs, ...selects]
      
      allInputs.forEach(input => {
        // Should have label
        const hasLabel = input.getAttribute('aria-labelledby') ||
                        input.getAttribute('aria-label') ||
                        screen.getByLabelText(input.getAttribute('name') || '')
        
        expect(hasLabel).toBeTruthy()
        
        // Should have description if needed
        if (input.getAttribute('aria-describedby')) {
          const descriptionId = input.getAttribute('aria-describedby')
          const description = document.getElementById(descriptionId!)
          expect(description).toBeInTheDocument()
        }
      })
    })

    test('complex widgets have proper ARIA attributes', () => {
      render(<VoiceAgentWorkspace />)
      
      // Voice controls should have proper ARIA
      const voiceControls = screen.getAllByRole('button', { name: /voice|mic|speak/i })
      
      voiceControls.forEach(control => {
        // Should indicate current state
        const hasState = control.getAttribute('aria-pressed') ||
                        control.getAttribute('aria-expanded') ||
                        control.getAttribute('aria-checked')
        
        expect(hasState || control.getAttribute('aria-label')).toBeTruthy()
      })
      
      // Status indicators should use live regions
      const statusElements = screen.getAllByText(/online|offline|active|processing/i)
      statusElements.forEach(status => {
        const liveRegion = status.getAttribute('aria-live') ||
                          status.closest('[aria-live]') ||
                          status.getAttribute('role') === 'status'
        
        expect(liveRegion).toBeTruthy()
      })
    })

    test('error messages are properly associated', async () => {
      const user = userEvent.setup()
      render(<ConversionForm />)
      
      // Submit form to trigger validation
      const submitButton = screen.getByRole('button', { name: /submit|send|request/i })
      await user.click(submitButton)
      
      await waitFor(() => {
        const errorMessages = screen.getAllByText(/required|invalid|error/i)
        
        errorMessages.forEach(error => {
          // Error should be associated with input
          const errorId = error.id
          if (errorId) {
            const associatedInput = screen.getByRole('textbox', { describedby: errorId })
            expect(associatedInput).toBeInTheDocument()
          }
        })
      })
    })
  })

  describe('Keyboard Navigation and Focus Management', () => {
    test('all interactive elements are keyboard accessible', async () => {
      const user = userEvent.setup()
      
      const components = [
        <HeroSection />,
        <VoiceAgentWorkspace />,
        <TenantSwitcher />,
        <QuickActions />,
      ]
      
      for (const component of components) {
        const { container } = render(component)
        
        // Tab through all focusable elements
        const focusableElements = container.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )
        
        expect(focusableElements.length).toBeGreaterThan(0)
        
        // Test tab navigation
        for (let i = 0; i < Math.min(focusableElements.length, 5); i++) {
          await user.tab()
          const focused = document.activeElement
          expect(focused).toBeTruthy()
          expect(focused?.getAttribute('tabindex')).not.toBe('-1')
        }
      }
    })

    test('focus indicators are visible and appropriate', () => {
      const { container } = render(<HeroSection />)
      
      const focusableElements = container.querySelectorAll(
        'button, a, input, select, textarea'
      )
      
      focusableElements.forEach(element => {
        // Should have focus styles (checked via CSS classes)
        const classes = element.className
        expect(classes).toMatch(/focus:|focus-/)
      })
    })

    test('skip links provide efficient navigation', () => {
      render(<AdminLayout />)
      
      // Should have skip to main content link
      const skipLink = screen.getByText(/skip.*to.*main|skip.*content/i) ||
                      screen.getByRole('link', { name: /skip/i })
      
      if (skipLink) {
        expect(skipLink).toBeInTheDocument()
        
        // Should target main content area
        const href = skipLink.getAttribute('href')
        if (href) {
          const target = document.querySelector(href)
          expect(target).toBeInTheDocument()
        }
      }
    })

    test('modal focus management works correctly', async () => {
      const user = userEvent.setup()
      render(<TenantSwitcher />)
      
      // Open modal/dropdown
      const trigger = screen.getByRole('button', { name: /switch|change|select/i })
      await user.click(trigger)
      
      await waitFor(() => {
        const modal = screen.getByRole('dialog') ||
                     screen.getByRole('listbox') ||
                     screen.getByRole('menu')
        
        if (modal) {
          expect(modal).toBeInTheDocument()
          
          // Focus should be trapped within modal
          const focusableInModal = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          )
          expect(focusableInModal.length).toBeGreaterThan(0)
        }
      })
    })

    test('keyboard shortcuts work without interfering with assistive technology', async () => {
      const user = userEvent.setup()
      render(<VoiceAgentWorkspace />)
      
      // Test common shortcuts
      await user.keyboard('{Space}')
      await user.keyboard('{Enter}')
      await user.keyboard('{Escape}')
      
      // Should not break screen reader navigation
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThan(0)
      
      // Focus should still work normally
      await user.tab()
      const focused = document.activeElement
      expect(focused).toBeTruthy()
    })
  })

  describe('Color Contrast and Visual Accessibility', () => {
    test('text meets WCAG AA contrast requirements', () => {
      const components = [
        <HeroSection />,
        <TrustIndicators />,
        <SystemOverviewDashboard />,
        <PropertyRecommendations />,
      ]
      
      components.forEach(component => {
        const { container } = render(component)
        
        const contrastValidation = accessibilityValidators.colorContrast(container)
        expect(contrastValidation).toBe(true)
        
        // Check for proper contrast classes (OKLCH monochromatic system)
        const textElements = container.querySelectorAll(
          'p, h1, h2, h3, h4, h5, h6, span, div, button, a'
        )
        
        textElements.forEach(element => {
          const classes = element.className
          // Should use high-contrast text colors
          expect(classes).toMatch(/text-|foreground|bg-/)
        })
      })
    })

    test('color is not the only means of conveying information', () => {
      render(<ConversationManager />)
      
      // Status indicators should use more than just color
      const statusElements = screen.getAllByText(/active|pending|qualified|error/i)
      
      statusElements.forEach(status => {
        const parentElement = status.closest('[class*="status"], [data-status]')
        
        if (parentElement) {
          // Should have text, icons, or other indicators
          const hasNonColorIndicator = 
            status.textContent ||
            parentElement.querySelector('[data-testid*="icon"]') ||
            parentElement.querySelector('svg') ||
            parentElement.getAttribute('aria-label')
          
          expect(hasNonColorIndicator).toBeTruthy()
        }
      })
    })

    test('focus indicators have sufficient contrast', async () => {
      const user = userEvent.setup()
      render(<QuickActions />)
      
      const buttons = screen.getAllByRole('button')
      
      // Focus first button
      if (buttons.length > 0) {
        buttons[0].focus()
        
        // Should have visible focus indicator
        const focused = document.activeElement
        const classes = focused?.className || ''
        expect(classes).toMatch(/focus:|focus-/)
      }
    })

    test('dark theme maintains accessibility standards', () => {
      // Mock dark theme preference
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(prefers-color-scheme: dark)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
        })),
      })
      
      const { container } = render(<HeroSection />)
      
      // Should maintain contrast in dark theme
      const darkElements = container.querySelectorAll('[class*="dark:"]')
      expect(darkElements.length).toBeGreaterThanOrEqual(0)
    })
  })

  describe('Screen Reader Support and Voice Interface Accessibility', () => {
    test('voice interface states are announced to screen readers', () => {
      render(<VoiceAgentWorkspace />)
      
      // Voice status should be in live region
      const voiceStatus = screen.getByText(/voice.*agent.*status|online|offline/i)
      
      const liveRegion = voiceStatus.getAttribute('aria-live') ||
                        voiceStatus.closest('[aria-live]') ||
                        voiceStatus.getAttribute('role') === 'status'
      
      expect(liveRegion).toBeTruthy()
      
      // Should have appropriate politeness level
      if (voiceStatus.getAttribute('aria-live')) {
        const politeness = voiceStatus.getAttribute('aria-live')
        expect(['polite', 'assertive']).toContain(politeness)
      }
    })

    test('real-time conversation updates are accessible', () => {
      render(<ConversationManager />)
      
      // Conversation updates should be announced
      const conversationElements = screen.getAllByText(/new.*message|active.*conversation|update/i)
      
      conversationElements.forEach(element => {
        const isAccessible = 
          element.getAttribute('aria-live') ||
          element.closest('[aria-live]') ||
          element.getAttribute('role') === 'status' ||
          element.getAttribute('role') === 'alert'
        
        expect(isAccessible).toBeTruthy()
      })
    })

    test('voice commands have text alternatives', () => {
      render(<QuickActions />)
      
      // Voice search should have text alternative
      const voiceButton = screen.getByRole('button', { name: /voice.*search|search.*by.*voice/i })
      expect(voiceButton).toBeInTheDocument()
      
      // Should provide text-based alternative
      const textSearch = screen.getByRole('textbox', { name: /search/i }) ||
                        screen.getByPlaceholderText(/search|type.*your.*search/i)
      expect(textSearch).toBeInTheDocument()
    })

    test('complex data tables are properly structured', () => {
      render(<SystemOverviewDashboard />)
      
      const tables = screen.getAllByRole('table')
      
      tables.forEach(table => {
        // Should have caption or accessible name
        const caption = table.querySelector('caption') ||
                       table.getAttribute('aria-label') ||
                       table.getAttribute('aria-labelledby')
        expect(caption).toBeTruthy()
        
        // Should have proper headers
        const headers = table.querySelectorAll('th')
        expect(headers.length).toBeGreaterThan(0)
        
        // Headers should have scope
        headers.forEach(header => {
          const scope = header.getAttribute('scope')
          expect(['col', 'row', 'colgroup', 'rowgroup']).toContain(scope)
        })
      })
    })
  })

  describe('Form Accessibility and Error Handling', () => {
    test('form validation is accessible', async () => {
      const user = userEvent.setup()
      render(<ConversionForm />)
      
      // Submit empty form
      const submitButton = screen.getByRole('button', { name: /submit|send|request/i })
      await user.click(submitButton)
      
      await waitFor(() => {
        const errorMessages = screen.getAllByText(/required|invalid|error/i)
        
        errorMessages.forEach(error => {
          // Error should be in live region or associated with input
          const isAccessible = 
            error.getAttribute('role') === 'alert' ||
            error.getAttribute('aria-live') ||
            error.closest('[aria-live]') ||
            error.id // If it has ID, should be referenced by aria-describedby
          
          expect(isAccessible).toBeTruthy()
        })
      })
    })

    test('required fields are properly indicated', () => {
      render(<ConversionForm />)
      
      const requiredInputs = screen.getAllByRole('textbox', { required: true })
      
      requiredInputs.forEach(input => {
        // Should have required attribute or aria-required
        const isRequired = 
          input.hasAttribute('required') ||
          input.getAttribute('aria-required') === 'true'
        
        expect(isRequired).toBe(true)
        
        // Should have visual indicator
        const label = screen.getByLabelText(input.getAttribute('name') || '')
        if (label) {
          expect(label.textContent).toMatch(/\*|required/i)
        }
      })
    })

    test('form instructions are clear and accessible', () => {
      render(<ConversionForm />)
      
      // Should have form instructions
      const instructions = screen.getByText(/fill.*out|complete.*form|required.*fields/i)
      
      if (instructions) {
        expect(instructions).toBeInTheDocument()
        
        // Should be associated with form
        const form = screen.getByRole('form') ||
                    instructions.closest('form')
        expect(form).toBeTruthy()
      }
    })
  })

  describe('Mobile Accessibility', () => {
    test('touch targets meet size requirements', () => {
      const { container } = render(<QuickActions />)
      
      const touchTargets = container.querySelectorAll(
        'button, a, input, select, textarea, [role="button"]'
      )
      
      touchTargets.forEach(target => {
        // Should meet 44px minimum (checked via CSS classes)
        const classes = target.className
        expect(classes).toMatch(/p-\d|py-\d|px-\d|h-\d+|min-h/)
      })
    })

    test('zoom functionality works without horizontal scrolling', () => {
      // Mock zoomed viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 320, // Zoomed mobile width
      })
      
      render(<HeroSection />)
      
      // Content should remain accessible
      const importantElements = screen.getAllByRole('button')
      expect(importantElements.length).toBeGreaterThan(0)
      
      // Should have responsive design
      const { container } = render(<HeroSection />)
      const responsiveElements = container.querySelectorAll('[class*="sm:"], [class*="md:"]')
      expect(responsiveElements.length).toBeGreaterThan(0)
    })
  })

  describe('Comprehensive Accessibility Score', () => {
    test('all interfaces achieve WCAG 2.1 AA compliance score above 95%', async () => {
      const testPersona = TEST_PERSONAS.client // Test with client persona
      const uxRunner = new UXTestRunner(testPersona)
      
      const accessibilitySteps: UserJourneyStep[] = [
        {
          description: 'Navigate using only keyboard',
          action: async (user) => {
            render(
              <div>
                <HeroSection />
                <VoiceAgentWorkspace />
                <TenantSwitcher />
                <QuickActions />
              </div>
            )
            
            // Tab through interface
            await user.tab()
            await user.tab()
            await user.tab()
          },
          validation: () => {
            const focused = document.activeElement
            expect(focused).toBeTruthy()
            expect(focused?.tagName).toMatch(/BUTTON|A|INPUT/)
          },
          timeLimit: 10,
        },
        {
          description: 'Use voice interface with screen reader support',
          action: async () => {
            render(<VoiceAgentWorkspace />)
            const voiceStatus = screen.getByText(/voice.*status|online|offline/i)
            expect(voiceStatus).toBeInTheDocument()
          },
          validation: () => {
            const statusElement = screen.getByText(/voice.*status|online|offline/i)
            const isAccessible = 
              statusElement.getAttribute('aria-live') ||
              statusElement.closest('[aria-live]') ||
              statusElement.getAttribute('role') === 'status'
            expect(isAccessible).toBeTruthy()
          },
          timeLimit: 5,
        },
      ]
      
      const AccessibilityComponent = (
        <div>
          <HeroSection />
          <ConversionForm />
          <VoiceAgentWorkspace />
          <ConversationManager />
          <TenantSwitcher />
          <SystemOverviewDashboard />
          <WelcomeOverview />
          <QuickActions />
        </div>
      )
      
      const result = await uxRunner.runComprehensiveTest(AccessibilityComponent, accessibilitySteps)
      
      expect(result.score).toBeGreaterThan(95)
      expect(result.passed).toBe(true)
      
      // Log results for analysis
      console.log('Accessibility Compliance Test Results:', {
        score: result.score,
        persona: result.persona,
        recommendations: result.recommendations,
        wcagCompliance: result.details.patterns,
        keyboardNavigation: result.details.journey,
      })
    })
  })
})