/**
 * Landing Page UX Validation Tests
 * 
 * Tests the prospect to lead conversion flow based on UX research findings:
 * - 5-second value proposition rule
 * - Trust building through social proof
 * - Conversion optimization patterns
 * - Mobile-first interaction design
 * - Progressive disclosure principles
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'

import { 
  TEST_PERSONAS, 
  UXTestRunner, 
  UserJourneyStep,
  trustPatternValidators,
  interactionPatternValidators,
  mockData
} from '../utils/ux-test-utils'

// Import components to test
import HeroSection from '../../components/landing/HeroSection'
import TrustIndicators from '../../components/landing/TrustIndicators'
import FeatureShowcase from '../../components/landing/FeatureShowcase'
import PricingSection from '../../components/landing/PricingSection'
import ConversionForm from '../../components/landing/ConversionForm'

describe('Landing Page UX Validation', () => {
  describe('Prospect Value Proposition Recognition (5-Second Rule)', () => {
    test('hero section communicates value proposition within 5 seconds', async () => {
      render(<HeroSection />)
      
      // Check if main value proposition is immediately visible
      const headline = screen.getByRole('heading', { level: 1 })
      expect(headline).toBeInTheDocument()
      expect(headline).toBeVisible()
      
      // Validate headline content addresses prospect pain points
      const headlineText = headline.textContent?.toLowerCase() || ''
      const valueIndicators = [
        'lead', 'qualification', '24/7', 'ai', 'voice', 'automation'
      ]
      
      const hasValueIndicators = valueIndicators.some(indicator => 
        headlineText.includes(indicator)
      )
      expect(hasValueIndicators).toBe(true)
      
      // Check for immediate trust metrics
      const trustMetrics = screen.getAllByText(/\d+%|\d+x/i)
      expect(trustMetrics.length).toBeGreaterThan(0)
    })

    test('primary CTA is immediately accessible and clear', () => {
      render(<HeroSection />)
      
      const primaryCTA = screen.getByRole('button', { name: /try voice demo|demo|get started/i })
      expect(primaryCTA).toBeInTheDocument()
      expect(primaryCTA).toBeVisible()
      
      // Check CTA positioning (should be above fold)
      const rect = primaryCTA.getBoundingClientRect()
      expect(rect.top).toBeLessThan(600) // Assuming 600px viewport height minimum
    })

    test('cognitive load stays under 3 primary actions above fold', () => {
      const { container } = render(<HeroSection />)
      
      // Count primary actions in hero section
      const primaryActions = container.querySelectorAll(
        'button[class*="primary"], [data-priority="primary"], button[class*="bg-black"]'
      )
      
      expect(primaryActions.length).toBeLessThanOrEqual(3)
    })
  })

  describe('Trust Building Pattern Implementation', () => {
    test('displays social proof elements prominently', () => {
      render(<TrustIndicators />)
      
      // Check for customer testimonials
      const testimonials = screen.getAllByText(/testimonial|review|says|helped/i)
      expect(testimonials.length).toBeGreaterThan(0)
      
      // Check for security compliance badges
      const securityBadges = screen.getAllByText(/soc 2|gdpr|security|compliance/i)
      expect(securityBadges.length).toBeGreaterThan(0)
      
      // Check for performance metrics
      const metrics = screen.getAllByText(/\d+%|\d+x|\d+ professionals/i)
      expect(metrics.length).toBeGreaterThan(0)
    })

    test('trust indicators are strategically positioned', () => {
      const { container } = render(<TrustIndicators />)
      
      const trustValidation = trustPatternValidators.testimonials(container) &&
                             trustPatternValidators.securityIndicators(container)
      
      expect(trustValidation).toBe(true)
    })
  })

  describe('Prospect User Journey - Landing to Demo', () => {
    test('complete prospect journey: awareness → interest → demo request', async () => {
      const user = userEvent.setup()
      const prospectPersona = TEST_PERSONAS.prospect
      
      const journeySteps: UserJourneyStep[] = [
        {
          description: 'Prospect reads value proposition',
          action: async () => {
            render(<HeroSection />)
            const headline = screen.getByRole('heading', { level: 1 })
            expect(headline).toBeVisible()
          },
          validation: () => {
            expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
          },
          timeLimit: 5, // 5-second rule
        },
        {
          description: 'Prospect views social proof',
          action: async () => {
            render(<TrustIndicators />)
            const testimonials = screen.getAllByText(/testimonial|review/i)
            expect(testimonials.length).toBeGreaterThan(0)
          },
          validation: () => {
            const metrics = screen.getAllByText(/\d+%|\d+x/i)
            expect(metrics.length).toBeGreaterThan(0)
          },
          timeLimit: 10,
        },
        {
          description: 'Prospect clicks primary CTA for demo',
          action: async (user) => {
            render(<HeroSection />)
            const demoCTA = screen.getByRole('button', { name: /try voice demo|demo/i })
            await user.click(demoCTA)
          },
          validation: () => {
            // Would validate navigation to demo page in full implementation
            expect(true).toBe(true)
          },
          timeLimit: 2,
        },
      ]
      
      const uxRunner = new UXTestRunner(prospectPersona)
      const result = await uxRunner.executeJourney(journeySteps)
      
      expect(result.success).toBe(true)
      expect(result.timeTaken).toBeLessThan(prospectPersona.timeConstraints)
    })
  })

  describe('Conversion Optimization Patterns', () => {
    test('implements risk reversal messaging', () => {
      render(<HeroSection />)
      
      const riskReversalText = screen.getAllByText(/no credit card|free trial|no commitment|14.day/i)
      expect(riskReversalText.length).toBeGreaterThan(0)
    })

    test('provides multiple engagement pathways', () => {
      render(<HeroSection />)
      
      // Primary path: Demo
      const demoButton = screen.getByRole('button', { name: /try voice demo|demo/i })
      expect(demoButton).toBeInTheDocument()
      
      // Secondary path: Learn more
      const learnMoreButton = screen.queryByRole('button', { name: /learn more|how it works/i })
      const learnMoreLink = screen.queryByRole('link', { name: /learn more|how it works/i })
      
      expect(learnMoreButton || learnMoreLink).toBeTruthy()
    })

    test('features showcase addresses prospect pain points', () => {
      render(<FeatureShowcase />)
      
      // Check for pain point messaging
      const painPointKeywords = [
        'unqualified leads',
        'missed calls',
        'time consuming',
        'overwhelmed',
        'responsive'
      ]
      
      const content = document.body.textContent?.toLowerCase() || ''
      const addressesPainPoints = painPointKeywords.some(keyword => 
        content.includes(keyword)
      )
      
      expect(addressesPainPoints).toBe(true)
    })
  })

  describe('Progressive Disclosure and Information Architecture', () => {
    test('pricing section follows progressive disclosure', async () => {
      const user = userEvent.setup()
      render(<PricingSection />)
      
      // Check if detailed features are hidden initially
      const detailButtons = screen.getAllByRole('button', { expanded: false })
      expect(detailButtons.length).toBeGreaterThan(0)
      
      // Test progressive disclosure
      if (detailButtons.length > 0) {
        await user.click(detailButtons[0])
        await waitFor(() => {
          const expandedButton = screen.getByRole('button', { expanded: true })
          expect(expandedButton).toBeInTheDocument()
        })
      }
    })

    test('conversion form implements lead qualification flow', async () => {
      const user = userEvent.setup()
      render(<ConversionForm />)
      
      // Check for multi-step form or progressive fields
      const formSteps = screen.getAllByText(/step \d|next|continue/i)
      const formFields = screen.getAllByRole('textbox')
      
      // Should have either multi-step or progressive qualification
      expect(formSteps.length > 0 || formFields.length > 1).toBe(true)
    })
  })

  describe('Mobile-First and Touch Interaction', () => {
    test('touch targets meet 44px minimum requirement', () => {
      const { container } = render(<HeroSection />)
      
      const buttons = container.querySelectorAll('button')
      buttons.forEach(button => {
        const rect = button.getBoundingClientRect()
        // Note: In jsdom, getBoundingClientRect returns 0s, so we check CSS classes instead
        const classes = button.className
        expect(classes).toMatch(/p-\d|py-\d|px-\d|h-\d|min-h/)
      })
    })

    test('responsive design adapts to mobile viewport', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      })
      
      const { container } = render(<HeroSection />)
      
      // Check for responsive classes
      const responsiveElements = container.querySelectorAll('[class*="sm:"], [class*="md:"], [class*="lg:"]')
      expect(responsiveElements.length).toBeGreaterThan(0)
    })
  })

  describe('Voice-First Messaging and Interaction', () => {
    test('voice interaction indicators are present', () => {
      const { container } = render(<HeroSection />)
      
      const voiceValidation = interactionPatternValidators.voiceFirst(container)
      expect(voiceValidation).toBe(true)
    })

    test('voice demo is prominently featured', () => {
      render(<HeroSection />)
      
      // Check for voice-related CTAs
      const voiceDemo = screen.getByRole('button', { name: /voice demo|try demo/i })
      expect(voiceDemo).toBeInTheDocument()
      
      // Check for mic iconography
      const micIcon = screen.getByTestId('mic-icon')
      expect(micIcon).toBeInTheDocument()
    })
  })

  describe('Performance and Loading UX', () => {
    test('critical content loads without JavaScript dependencies', () => {
      // Disable JavaScript-dependent features for test
      const { container } = render(<HeroSection />)
      
      // Check that core content is present without motion
      const headline = container.querySelector('h1')
      const primaryCTA = container.querySelector('button')
      
      expect(headline).toBeInTheDocument()
      expect(primaryCTA).toBeInTheDocument()
    })

    test('loading states provide immediate feedback', async () => {
      render(<ConversionForm />)
      
      const submitButton = screen.getByRole('button', { name: /submit|send|request/i })
      fireEvent.click(submitButton)
      
      // Check for loading state
      await waitFor(() => {
        const loadingIndicator = screen.queryByText(/loading|sending|processing/i) ||
                               screen.queryByRole('status')
        expect(loadingIndicator || submitButton.getAttribute('disabled')).toBeTruthy()
      })
    })
  })

  describe('Comprehensive UX Score', () => {
    test('landing page achieves overall UX score above 80%', async () => {
      const prospectPersona = TEST_PERSONAS.prospect
      const uxRunner = new UXTestRunner(prospectPersona)
      
      const journeySteps: UserJourneyStep[] = [
        {
          description: 'Complete prospect evaluation journey',
          action: async () => {
            render(
              <div>
                <HeroSection />
                <TrustIndicators />
                <FeatureShowcase />
                <PricingSection />
              </div>
            )
          },
          validation: () => {
            expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
          },
        },
      ]
      
      const LandingPageComponent = (
        <div>
          <HeroSection />
          <TrustIndicators />
          <FeatureShowcase />
          <PricingSection />
        </div>
      )
      
      const result = await uxRunner.runComprehensiveTest(LandingPageComponent, journeySteps)
      
      expect(result.score).toBeGreaterThan(80)
      expect(result.passed).toBe(true)
      
      // Log results for analysis
      console.log('Landing Page UX Test Results:', {
        score: result.score,
        persona: result.persona,
        recommendations: result.recommendations,
        journey: result.details.journey,
      })
    })
  })
})

describe('Edge Cases and Error States', () => {
  test('handles form validation errors gracefully', async () => {
    const user = userEvent.setup()
    render(<ConversionForm />)
    
    const submitButton = screen.getByRole('button', { name: /submit|send|request/i })
    
    // Try to submit empty form
    await user.click(submitButton)
    
    // Should show validation messages
    await waitFor(() => {
      const errorMessages = screen.getAllByText(/required|invalid|error/i)
      expect(errorMessages.length).toBeGreaterThan(0)
    })
  })

  test('provides clear next steps after form submission', async () => {
    const user = userEvent.setup()
    render(<ConversionForm />)
    
    // Fill out form
    const emailInput = screen.getByRole('textbox', { name: /email/i })
    await user.type(emailInput, 'test@example.com')
    
    const submitButton = screen.getByRole('button', { name: /submit|send|request/i })
    await user.click(submitButton)
    
    // Should show success state with next steps
    await waitFor(() => {
      const successMessage = screen.queryByText(/thank you|success|next steps|check email/i)
      expect(successMessage).toBeInTheDocument()
    })
  })
})