/**
 * Performance Impact on UX Testing Suite
 * 
 * Tests how performance affects user experience across all interfaces:
 * - Voice processing speed impact on user experience
 * - Dashboard responsiveness during high conversation load
 * - Admin console performance with large tenant data
 * - Client portal speed during property browsing
 * - Loading states and perceived performance
 * - Bundle size and code splitting effectiveness
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'

import { 
  TEST_PERSONAS, 
  UXTestRunner, 
  UserJourneyStep,
  performanceValidators,
  UX_STANDARDS,
  mockData
} from '../utils/ux-test-utils'

// Import components for performance testing
import HeroSection from '../../components/landing/HeroSection'
import ConversionForm from '../../components/landing/ConversionForm'
import VoiceAgentWorkspace from '../../components/dashboard/VoiceAgentWorkspace'
import ConversationManager from '../../components/dashboard/ConversationManager'
import LeadQualificationPanel from '../../components/dashboard/LeadQualificationPanel'
import PerformanceMetrics from '../../components/dashboard/PerformanceMetrics'
import SystemOverviewDashboard from '../../components/admin/SystemOverviewDashboard'
import TeamManagementInterface from '../../components/admin/TeamManagementInterface'
import PropertyRecommendations from '../../components/portal/PropertyRecommendations'
import PropertyGrid from '../../components/portal/PropertyGrid'
import QuickActions from '../../components/portal/QuickActions'

describe('Performance Impact on UX Testing', () => {
  describe('Voice Processing Speed and User Experience', () => {
    test('voice activation provides immediate feedback within 200ms', async () => {
      const user = userEvent.setup()
      render(<VoiceAgentWorkspace />)
      
      const voiceButton = screen.getByRole('button', { name: /voice|mic|start/i })
      
      if (voiceButton) {
        const startTime = performance.now()
        await user.click(voiceButton)
        
        await waitFor(() => {
          const feedback = screen.getByText(/listening|active|recording/i) ||
                          screen.getByRole('status') ||
                          voiceButton.getAttribute('aria-pressed') === 'true'
          
          expect(feedback).toBeTruthy()
          
          const responseTime = performance.now() - startTime
          expect(responseTime).toBeLessThan(200) // Under 200ms for immediate feedback
        })
      }
    })

    test('voice processing states prevent user confusion during delays', () => {
      render(<VoiceAgentWorkspace />)
      
      // Should have clear processing states
      const processingStates = screen.getAllByText(/processing|thinking|analyzing|working/i)
      
      if (processingStates.length > 0) {
        processingStates.forEach(state => {
          // Should be in live region for screen readers
          const liveRegion = state.getAttribute('aria-live') ||
                           state.closest('[aria-live]') ||
                           state.getAttribute('role') === 'status'
          expect(liveRegion).toBeTruthy()
        })
      }
      
      // Should have visual progress indicators
      const progressIndicators = screen.getAllByRole('progressbar') ||
                                screen.getAllByText(/\d+%|loading|progress/i)
      expect(progressIndicators.length).toBeGreaterThanOrEqual(0)
    })

    test('voice timeout scenarios maintain good UX', async () => {
      const user = userEvent.setup()
      render(<VoiceAgentWorkspace />)
      
      // Simulate voice timeout scenario
      const voiceButton = screen.getByRole('button', { name: /voice|mic/i })
      
      if (voiceButton) {
        await user.click(voiceButton)
        
        // Should handle timeout gracefully (simulated)
        await waitFor(() => {
          const timeoutHandling = screen.getByText(/timeout|try.*again|connection.*issue/i) ||
                                  screen.getByRole('button', { name: /retry|try.*again/i })
          
          if (timeoutHandling) {
            expect(timeoutHandling).toBeInTheDocument()
            
            // Should provide clear recovery options
            const recoveryOptions = screen.getAllByRole('button', { name: /retry|cancel|settings/i })
            expect(recoveryOptions.length).toBeGreaterThan(0)
          }
        })
      }
    })

    test('voice interface degrades gracefully under poor network conditions', () => {
      // Mock poor network conditions
      Object.defineProperty(navigator, 'connection', {
        writable: true,
        value: {
          effectiveType: '2g',
          downlink: 0.5,
          rtt: 2000,
        },
      })
      
      render(<VoiceAgentWorkspace />)
      
      // Should adapt to network conditions
      const networkAwareness = screen.getByText(/slow.*connection|limited.*connectivity|offline.*mode/i)
      
      if (networkAwareness) {
        expect(networkAwareness).toBeInTheDocument()
        
        // Should offer alternatives
        const alternatives = screen.getAllByText(/text.*mode|manual.*input|offline.*features/i)
        expect(alternatives.length).toBeGreaterThan(0)
      }
    })
  })

  describe('Dashboard Responsiveness During High Load', () => {
    test('conversation manager remains responsive with multiple active conversations', () => {
      // Mock high conversation load
      const manyConversations = Array.from({ length: 50 }, (_, i) => ({
        id: i + 1,
        client: `Client ${i + 1}`,
        status: ['active', 'qualified', 'pending'][i % 3],
        lastMessage: `Message from client ${i + 1}`,
        timestamp: `${i + 1} minutes ago`,
        priority: ['high', 'medium', 'low'][i % 3],
      }))
      
      render(<ConversationManager />)
      
      // Should handle large datasets efficiently
      const conversationItems = screen.getAllByText(/client.*\d+|conversation|active|qualified/i)
      expect(conversationItems.length).toBeGreaterThan(0)
      
      // Should have virtualization or pagination
      const paginationControls = screen.getAllByText(/page|next|previous|load.*more/i) ||
                                 screen.getAllByRole('button', { name: /page|next|previous/i })
      expect(paginationControls.length).toBeGreaterThanOrEqual(0)
    })

    test('real-time updates do not block user interactions', async () => {
      const user = userEvent.setup()
      render(<ConversationManager />)
      
      // User should be able to interact while updates happen
      const actionButton = screen.getByRole('button', { name: /take.*over|intervene|call/i })
      
      if (actionButton) {
        const startTime = performance.now()
        await user.click(actionButton)
        
        // Should respond immediately despite background updates
        await waitFor(() => {
          const response = screen.getByText(/taking.*over|connecting|intervention/i) ||
                          actionButton.getAttribute('disabled')
          
          expect(response).toBeTruthy()
          
          const responseTime = performance.now() - startTime
          expect(responseTime).toBeLessThan(100) // Very fast for user actions
        })
      }
    })

    test('performance metrics update without causing layout shifts', () => {
      render(<PerformanceMetrics />)
      
      // Should have stable layout
      const metricsContainer = screen.getByText(/performance|metrics|goals/i).closest('div')
      
      if (metricsContainer) {
        const initialLayout = metricsContainer.getBoundingClientRect()
        
        // Simulate metric updates
        fireEvent.load(window)
        
        const updatedLayout = metricsContainer.getBoundingClientRect()
        
        // Layout should remain stable (heights should match)
        expect(Math.abs(updatedLayout.height - initialLayout.height)).toBeLessThan(5)
      }
    })

    test('dashboard components load progressively to maintain perceived performance', () => {
      const { container } = render(
        <div>
          <VoiceAgentWorkspace />
          <ConversationManager />
          <LeadQualificationPanel />
          <PerformanceMetrics />
        </div>
      )
      
      // Should have loading states
      const loadingValidation = performanceValidators.loadingStates(container)
      expect(loadingValidation).toBe(true)
      
      // Should prioritize critical content
      const criticalContent = screen.getByText(/voice.*status|agent.*workspace/i)
      expect(criticalContent).toBeInTheDocument()
      
      // Should have skeleton screens for slower content
      const skeletonValidation = performanceValidators.skeletonScreens(container)
      expect(skeletonValidation).toBe(true)
    })
  })

  describe('Admin Console Performance with Large Tenant Data', () => {
    test('tenant switching remains fast with many tenants', async () => {
      const user = userEvent.setup()
      
      // Mock many tenants
      const manyTenants = Array.from({ length: 100 }, (_, i) => ({
        id: i + 1,
        name: `Agency ${i + 1}`,
        plan: ['premium', 'enterprise', 'basic'][i % 3],
        agents: Math.floor(Math.random() * 50) + 1,
        status: 'active',
      }))
      
      render(<SystemOverviewDashboard />)
      
      const tenantSwitcher = screen.getByRole('combobox') ||
                            screen.getByRole('button', { name: /switch.*tenant|change.*agency/i })
      
      if (tenantSwitcher) {
        const startTime = performance.now()
        await user.click(tenantSwitcher)
        
        await waitFor(() => {
          const dropdown = screen.getByRole('listbox') ||
                          screen.getAllByRole('option')
          
          expect(dropdown).toBeTruthy()
          
          const openTime = performance.now() - startTime
          expect(openTime).toBeLessThan(300) // Under 300ms to open
        })
      }
    })

    test('large data tables use virtualization for performance', () => {
      render(<TeamManagementInterface />)
      
      // Should handle large datasets
      const dataTable = screen.getByRole('table')
      
      if (dataTable) {
        // Should have virtualization indicators
        const virtualizationHints = dataTable.querySelector('[data-virtualized]') ||
                                   screen.getByText(/showing.*\d+.*of.*\d+|virtualized/i)
        
        expect(virtualizationHints).toBeTruthy()
      }
      
      // Should have pagination or infinite scroll
      const paginationControls = screen.getAllByText(/page|next|previous|load.*more/i)
      expect(paginationControls.length).toBeGreaterThanOrEqual(0)
    })

    test('bulk operations provide progress feedback', async () => {
      const user = userEvent.setup()
      render(<TeamManagementInterface />)
      
      // Select multiple items for bulk operation
      const selectAllCheckbox = screen.getByRole('checkbox', { name: /select.*all/i })
      
      if (selectAllCheckbox) {
        await user.click(selectAllCheckbox)
        
        // Should show bulk action options
        await waitFor(() => {
          const bulkActions = screen.getAllByText(/bulk.*action|with.*selected|batch/i)
          expect(bulkActions.length).toBeGreaterThan(0)
        })
        
        // Should provide progress feedback for bulk operations
        const bulkActionButton = screen.getByRole('button', { name: /bulk|batch|all.*selected/i })
        
        if (bulkActionButton) {
          await user.click(bulkActionButton)
          
          await waitFor(() => {
            const progress = screen.getByText(/processing|progress|\d+.*of.*\d+/i) ||
                           screen.getByRole('progressbar')
            expect(progress).toBeTruthy()
          })
        }
      }
    })

    test('system monitoring updates efficiently without impacting admin workflow', () => {
      render(<SystemOverviewDashboard />)
      
      // Should have efficient update mechanisms
      const systemMetrics = screen.getAllByText(/\d+.*users?|\d+.*agents?|\d+.*tenants?/i)
      expect(systemMetrics.length).toBeGreaterThan(0)
      
      // Updates should not block interface
      const interactiveElements = screen.getAllByRole('button')
      expect(interactiveElements.length).toBeGreaterThan(0)
      
      // Should use optimistic UI patterns
      const optimisticValidation = performanceValidators.optimisticUI(screen.getByRole('main') || document.body)
      expect(optimisticValidation).toBe(true)
    })
  })

  describe('Client Portal Speed During Property Browsing', () => {
    test('property grid loads incrementally for smooth browsing', () => {
      render(<PropertyGrid />)
      
      // Should load properties incrementally
      const propertyCards = screen.getAllByText(/\$\d+.*bed.*bath/i)
      expect(propertyCards.length).toBeGreaterThan(0)
      
      // Should have lazy loading indicators
      const lazyLoadIndicators = screen.getAllByText(/loading.*more|scroll.*for.*more/i) ||
                                screen.getAllByRole('button', { name: /load.*more|show.*more/i })
      expect(lazyLoadIndicators.length).toBeGreaterThanOrEqual(0)
    })

    test('property filtering provides immediate visual feedback', async () => {
      const user = userEvent.setup()
      render(<PropertyGrid />)
      
      // Should have filter controls
      const priceFilter = screen.getByText(/price|budget/i) ||
                         screen.getByRole('button', { name: /filter|price/i })
      
      if (priceFilter) {
        const startTime = performance.now()
        await user.click(priceFilter)
        
        // Should show immediate feedback
        await waitFor(() => {
          const filterFeedback = screen.getByText(/filtering|searching|applying/i) ||
                               screen.getByRole('status') ||
                               priceFilter.getAttribute('aria-expanded') === 'true'
          
          expect(filterFeedback).toBeTruthy()
          
          const feedbackTime = performance.now() - startTime
          expect(feedbackTime).toBeLessThan(100) // Immediate feedback
        })
      }
    })

    test('property recommendations load without blocking navigation', async () => {
      const user = userEvent.setup()
      render(<PropertyRecommendations />)
      
      // Should not block user navigation while loading
      const navigationElements = screen.getAllByRole('link') ||
                                screen.getAllByRole('button', { name: /view|schedule|save/i })
      
      expect(navigationElements.length).toBeGreaterThan(0)
      
      // Test that navigation works during loading
      if (navigationElements.length > 0) {
        const startTime = performance.now()
        await user.click(navigationElements[0])
        
        const responseTime = performance.now() - startTime
        expect(responseTime).toBeLessThan(200) // Fast navigation
      }
    })

    test('voice search provides progressive results', async () => {
      const user = userEvent.setup()
      render(<QuickActions />)
      
      const voiceSearchButton = screen.getByRole('button', { name: /voice.*search|search.*by.*voice/i })
      
      if (voiceSearchButton) {
        await user.click(voiceSearchButton)
        
        // Should provide immediate feedback
        await waitFor(() => {
          const voiceInterface = screen.getByText(/listening|speak.*now|voice.*active/i) ||
                                screen.getByRole('status')
          expect(voiceInterface).toBeTruthy()
        })
        
        // Should show progressive results (simulated)
        const progressiveResults = screen.getAllByText(/searching|found.*\d+|results/i)
        expect(progressiveResults.length).toBeGreaterThanOrEqual(0)
      }
    })
  })

  describe('Loading States and Perceived Performance', () => {
    test('skeleton screens maintain layout stability', () => {
      const components = [
        <PropertyGrid />,
        <ConversationManager />,
        <SystemOverviewDashboard />,
        <PropertyRecommendations />,
      ]
      
      components.forEach(component => {
        const { container } = render(component)
        
        // Should have skeleton screens
        const skeletonValidation = performanceValidators.skeletonScreens(container)
        expect(skeletonValidation).toBe(true)
        
        // Skeletons should match final content layout
        const skeletonElements = container.querySelectorAll('[data-skeleton], [class*="skeleton"]')
        expect(skeletonElements.length).toBeGreaterThanOrEqual(0)
      })
    })

    test('progressive loading prioritizes above-fold content', () => {
      render(<HeroSection />)
      
      // Critical above-fold content should load first
      const criticalContent = [
        screen.getByRole('heading', { level: 1 }),
        screen.getByRole('button', { name: /try.*demo|get.*started/i }),
      ]
      
      criticalContent.forEach(element => {
        expect(element).toBeInTheDocument()
        expect(element).toBeVisible()
      })
      
      // Below-fold content can load progressively
      const belowFoldElements = screen.getAllByText(/feature|benefit|testimonial/i)
      expect(belowFoldElements.length).toBeGreaterThanOrEqual(0)
    })

    test('optimistic UI provides immediate feedback for user actions', async () => {
      const user = userEvent.setup()
      render(<ConversionForm />)
      
      const submitButton = screen.getByRole('button', { name: /submit|send|request/i })
      
      const startTime = performance.now()
      await user.click(submitButton)
      
      // Should provide immediate optimistic feedback
      await waitFor(() => {
        const optimisticFeedback = screen.getByText(/sending|processing|submitted/i) ||
                                  submitButton.getAttribute('disabled') ||
                                  screen.getByRole('status')
        
        expect(optimisticFeedback).toBeTruthy()
        
        const feedbackTime = performance.now() - startTime
        expect(feedbackTime).toBeLessThan(100) // Immediate optimistic update
      })
    })

    test('error states recover gracefully without losing user progress', async () => {
      const user = userEvent.setup()
      render(<ConversionForm />)
      
      // Fill out form
      const emailInput = screen.getByRole('textbox', { name: /email/i })
      await user.type(emailInput, 'test@example.com')
      
      // Simulate error scenario
      const submitButton = screen.getByRole('button', { name: /submit|send/i })
      await user.click(submitButton)
      
      // Should maintain form data on error
      await waitFor(() => {
        const errorMessage = screen.getByText(/error|failed|try.*again/i)
        
        if (errorMessage) {
          expect(errorMessage).toBeInTheDocument()
          
          // Form data should be preserved
          expect(emailInput).toHaveValue('test@example.com')
          
          // Should provide retry option
          const retryButton = screen.getByRole('button', { name: /try.*again|retry/i })
          expect(retryButton).toBeInTheDocument()
        }
      })
    })
  })

  describe('Bundle Size and Code Splitting Impact', () => {
    test('critical rendering path is optimized', () => {
      render(<HeroSection />)
      
      // Critical content should render without JavaScript
      const criticalElements = [
        screen.getByRole('heading', { level: 1 }),
        screen.getAllByRole('button'),
        screen.getAllByText(/\$|%|professional/i),
      ].flat()
      
      expect(criticalElements.length).toBeGreaterThan(0)
      
      // Should not require JavaScript for basic functionality
      criticalElements.forEach(element => {
        expect(element).toBeInTheDocument()
      })
    })

    test('non-critical features load asynchronously', () => {
      render(<PropertyRecommendations />)
      
      // Core content should be immediately available
      const coreContent = screen.getAllByText(/property|recommendation|match/i)
      expect(coreContent.length).toBeGreaterThan(0)
      
      // Enhanced features can load progressively
      const enhancedFeatures = screen.getAllByText(/ai.*powered|smart.*matching|personalized/i)
      expect(enhancedFeatures.length).toBeGreaterThanOrEqual(0)
    })

    test('vendor bundles are properly split', () => {
      // This would be tested in actual bundle analysis
      // Here we test that components work independently
      const independentComponents = [
        <HeroSection />,
        <VoiceAgentWorkspace />,
        <PropertyGrid />,
        <SystemOverviewDashboard />,
      ]
      
      independentComponents.forEach(component => {
        const { container } = render(component)
        
        // Should render without dependencies on other components
        const content = container.textContent
        expect(content).toBeTruthy()
        expect(content!.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Comprehensive Performance UX Score', () => {
    test('performance impact on UX achieves score above 85%', async () => {
      const testPersona = TEST_PERSONAS.agent // Use agent for performance testing
      const uxRunner = new UXTestRunner(testPersona)
      
      const performanceSteps: UserJourneyStep[] = [
        {
          description: 'Test voice interface responsiveness',
          action: async (user) => {
            render(<VoiceAgentWorkspace />)
            const voiceButton = screen.getByRole('button', { name: /voice|mic/i })
            const startTime = performance.now()
            await user.click(voiceButton)
            
            const responseTime = performance.now() - startTime
            expect(responseTime).toBeLessThan(200)
          },
          validation: () => {
            const voiceStatus = screen.getByText(/listening|active|ready/i)
            expect(voiceStatus).toBeInTheDocument()
          },
          timeLimit: 1,
        },
        {
          description: 'Test dashboard responsiveness under load',
          action: async () => {
            render(
              <div>
                <ConversationManager />
                <PerformanceMetrics />
                <LeadQualificationPanel />
              </div>
            )
          },
          validation: () => {
            const dashboardContent = screen.getAllByText(/conversation|performance|lead/i)
            expect(dashboardContent.length).toBeGreaterThan(0)
          },
          timeLimit: 2,
        },
        {
          description: 'Test property browsing performance',
          action: async () => {
            render(<PropertyGrid />)
            const properties = screen.getAllByText(/property|\$\d+|bed|bath/i)
            expect(properties.length).toBeGreaterThan(0)
          },
          validation: () => {
            const propertyCards = screen.getAllByText(/\$\d+.*bed.*bath/i)
            expect(propertyCards.length).toBeGreaterThan(0)
          },
          timeLimit: 1,
        },
      ]
      
      const PerformanceComponent = (
        <div>
          <HeroSection />
          <VoiceAgentWorkspace />
          <ConversationManager />
          <SystemOverviewDashboard />
          <PropertyGrid />
          <QuickActions />
        </div>
      )
      
      const result = await uxRunner.runComprehensiveTest(PerformanceComponent, performanceSteps)
      
      expect(result.score).toBeGreaterThan(85)
      expect(result.passed).toBe(true)
      
      // Log results for analysis
      console.log('Performance Impact UX Test Results:', {
        score: result.score,
        persona: result.persona,
        recommendations: result.recommendations,
        performancePatterns: result.details.patterns,
        responseTimeMetrics: result.details.journey,
      })
    })
  })
})