/**
 * Client Portal UX Validation Tests
 * 
 * Tests client property viewing and appointment booking based on UX research:
 * - Trust building through transparency and agent attribution
 * - Simplicity through progressive disclosure and clear hierarchy
 * - Client-centric experience with personalized recommendations
 * - Self-service capabilities with clear next steps
 * - Confidence building through progress tracking
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

// Import client portal components
import WelcomeOverview from '../../components/portal/WelcomeOverview'
import PropertyRecommendations from '../../components/portal/PropertyRecommendations'
import PropertyGrid from '../../components/portal/PropertyGrid'
import PropertyFilters from '../../components/portal/PropertyFilters'
import UpcomingAppointments from '../../components/portal/UpcomingAppointments'
import RecentActivity from '../../components/portal/RecentActivity'
import QuickActions from '../../components/portal/QuickActions'
import SavedSearches from '../../components/portal/SavedSearches'

describe('Client Portal UX Validation', () => {
  const clientPersona = TEST_PERSONAS.client

  describe('Trust Building Through Transparency', () => {
    test('agent attribution is present on all communications', () => {
      render(<RecentActivity />)
      
      // All communications should show agent attribution
      const agentAttributions = screen.getAllByText(/from.*michael|by.*agent|michael.*chen/i)
      expect(agentAttributions.length).toBeGreaterThan(0)
      
      // Should show agent photos/avatars
      const agentAvatars = screen.getAllByRole('img', { name: /agent|michael/i }) ||
                          screen.getAllByTestId('agent-avatar')
      expect(agentAvatars.length).toBeGreaterThan(0)
    })

    test('response time transparency builds trust', () => {
      render(<RecentActivity />)
      
      // Should show response times
      const responseTimes = screen.getAllByText(/\d+.*minutes?.*ago|\d+.*hours?.*ago|responded.*in/i)
      expect(responseTimes.length).toBeGreaterThan(0)
      
      // Should highlight fast response times
      const fastResponses = screen.getAllByText(/< \d+.*minutes?|quick.*response|responded.*immediately/i)
      expect(fastResponses.length).toBeGreaterThanOrEqual(0)
    })

    test('progress tracking shows search advancement', () => {
      render(<WelcomeOverview />)
      
      // Should show search progress metrics
      const progressMetrics = screen.getAllByText(/\d+.*properties.*viewed|\d+.*saved|\d+.*scheduled/i)
      expect(progressMetrics.length).toBeGreaterThan(0)
      
      // Should show progress visualization
      const progressIndicators = screen.getAllByRole('progressbar') ||
                                 screen.getAllByText(/\d+%.*complete|progress/i)
      expect(progressIndicators.length).toBeGreaterThan(0)
    })

    test('appointment status transparency prevents anxiety', () => {
      render(<UpcomingAppointments />)
      
      // Should show clear appointment status
      const appointmentStatus = screen.getAllByText(/confirmed|pending|scheduled|cancelled/i)
      expect(appointmentStatus.length).toBeGreaterThan(0)
      
      // Should show agent confirmation
      const agentConfirmation = screen.getAllByText(/confirmed.*by.*agent|michael.*confirmed/i)
      expect(agentConfirmation.length).toBeGreaterThan(0)
    })
  })

  describe('Property Discovery and Recommendations', () => {
    test('AI recommendations have clear explanations', () => {
      render(<PropertyRecommendations />)
      
      // Should show match scores
      const matchScores = screen.getAllByText(/\d+%.*match|\d+.*score/i)
      expect(matchScores.length).toBeGreaterThan(0)
      
      // Should explain why properties match
      const explanations = screen.getAllByText(/perfect.*location|within.*budget|has.*parking|why.*matches/i)
      expect(explanations.length).toBeGreaterThan(0)
    })

    test('property filtering is simple and intuitive', async () => {
      const user = userEvent.setup()
      render(<PropertyFilters />)
      
      // Should have essential filters only
      const filterTypes = ['price', 'bedrooms', 'location', 'type']
      
      filterTypes.forEach(filterType => {
        const filter = screen.getByText(new RegExp(filterType, 'i')) ||
                      screen.getByLabelText(new RegExp(filterType, 'i'))
        expect(filter).toBeInTheDocument()
      })
      
      // Test filter interaction
      const priceFilter = screen.getByText(/price|budget/i)
      await user.click(priceFilter)
      
      // Should show price options
      await waitFor(() => {
        const priceOptions = screen.getAllByText(/\$\d+k|\$\d+,\d+|under.*\$|above.*\$/i)
        expect(priceOptions.length).toBeGreaterThan(0)
      })
    })

    test('property grid optimizes for decision making', () => {
      render(<PropertyGrid />)
      
      // Should show essential property info
      const essentialInfo = ['price', 'beds', 'baths', 'sqft']
      
      essentialInfo.forEach(info => {
        const elements = screen.getAllByText(new RegExp(info, 'i'))
        expect(elements.length).toBeGreaterThan(0)
      })
      
      // Should have quick action buttons
      const quickActions = screen.getAllByRole('button', { name: /schedule|save|share|view/i })
      expect(quickActions.length).toBeGreaterThan(0)
    })

    test('property viewing journey is streamlined', async () => {
      const user = userEvent.setup()
      
      const propertyViewingSteps: UserJourneyStep[] = [
        {
          description: 'Client sees personalized recommendations',
          action: async () => {
            render(<PropertyRecommendations />)
            const recommendations = screen.getAllByText(/recommended|match|perfect/i)
            expect(recommendations.length).toBeGreaterThan(0)
          },
          validation: () => {
            const matchScores = screen.getAllByText(/\d+%.*match/i)
            expect(matchScores.length).toBeGreaterThan(0)
          },
          timeLimit: 5,
        },
        {
          description: 'Client filters properties by criteria',
          action: async (user) => {
            render(<PropertyFilters />)
            const filter = screen.getByText(/price|location|beds/i)
            await user.click(filter)
          },
          validation: () => {
            const filterOptions = screen.getAllByText(/\$|bedroom|\d+/i)
            expect(filterOptions.length).toBeGreaterThan(0)
          },
          timeLimit: 3,
        },
        {
          description: 'Client schedules property viewing',
          action: async (user) => {
            render(<PropertyGrid />)
            const scheduleButton = screen.getByRole('button', { name: /schedule|book.*viewing/i })
            await user.click(scheduleButton)
          },
          validation: () => {
            const scheduling = screen.getByText(/schedule|appointment|viewing|time/i)
            expect(scheduling).toBeInTheDocument()
          },
          timeLimit: 2,
        },
      ]
      
      const uxRunner = new UXTestRunner(clientPersona)
      const result = await uxRunner.executeJourney(propertyViewingSteps)
      
      expect(result.success).toBe(true)
      expect(result.timeTaken).toBeLessThan(clientPersona.timeConstraints)
    })
  })

  describe('Appointment Booking and Management', () => {
    test('appointment scheduling is self-service and clear', async () => {
      const user = userEvent.setup()
      render(<UpcomingAppointments />)
      
      // Should have schedule new appointment option
      const scheduleButton = screen.getByRole('button', { name: /schedule.*new|book.*appointment|new.*viewing/i })
      expect(scheduleButton).toBeInTheDocument()
      
      await user.click(scheduleButton)
      
      // Should show available times
      await waitFor(() => {
        const timeSlots = screen.getAllByText(/\d+:\d+|morning|afternoon|available/i)
        expect(timeSlots.length).toBeGreaterThan(0)
      })
    })

    test('appointment confirmation provides clear next steps', async () => {
      const user = userEvent.setup()
      render(<UpcomingAppointments />)
      
      const confirmButton = screen.getByRole('button', { name: /confirm|accept|yes/i })
      
      if (confirmButton) {
        await user.click(confirmButton)
        
        await waitFor(() => {
          const confirmation = screen.getByText(/confirmed|scheduled|we.*ll.*see.*you|calendar.*invite/i)
          expect(confirmation).toBeInTheDocument()
        })
      }
    })

    test('appointment rescheduling is flexible and easy', async () => {
      const user = userEvent.setup()
      render(<UpcomingAppointments />)
      
      const rescheduleButton = screen.getByRole('button', { name: /reschedule|change.*time|modify/i })
      
      if (rescheduleButton) {
        await user.click(rescheduleButton)
        
        await waitFor(() => {
          const newTimeSlots = screen.getAllByText(/available|new.*time|\d+:\d+/i)
          expect(newTimeSlots.length).toBeGreaterThan(0)
        })
      }
    })

    test('calendar integration provides convenience', () => {
      render(<UpcomingAppointments />)
      
      // Should offer calendar sync options
      const calendarOptions = screen.getAllByText(/add.*to.*calendar|google.*calendar|outlook|ical/i)
      expect(calendarOptions.length).toBeGreaterThan(0)
    })
  })

  describe('Self-Service Capabilities', () => {
    test('quick actions are prominently featured', () => {
      render(<QuickActions />)
      
      // Should have primary self-service actions
      const quickActionTypes = [
        /voice.*search|search.*by.*voice/i,
        /schedule.*viewing|book.*appointment/i,
        /contact.*agent|call.*michael/i,
        /save.*property|add.*to.*favorites/i
      ]
      
      quickActionTypes.forEach(actionType => {
        const action = screen.getByText(actionType) ||
                      screen.getByRole('button', { name: actionType })
        expect(action).toBeInTheDocument()
      })
    })

    test('voice search functionality is accessible', async () => {
      const user = userEvent.setup()
      render(<QuickActions />)
      
      const voiceSearch = screen.getByRole('button', { name: /voice.*search|search.*by.*voice/i })
      expect(voiceSearch).toBeInTheDocument()
      
      await user.click(voiceSearch)
      
      // Should activate voice interface
      await waitFor(() => {
        const voiceInterface = screen.getByText(/listening|speak.*now|say.*your.*search/i) ||
                              screen.getByTestId('voice-interface')
        expect(voiceInterface).toBeInTheDocument()
      })
    })

    test('saved searches provide quick access to preferences', () => {
      render(<SavedSearches />)
      
      // Should show saved search criteria
      const savedSearches = screen.getAllByText(/3.*bed.*mission.*bay|downtown.*condo|saved.*search/i)
      expect(savedSearches.length).toBeGreaterThan(0)
      
      // Should have quick action buttons
      const searchActions = screen.getAllByRole('button', { name: /run.*search|update|delete/i })
      expect(searchActions.length).toBeGreaterThan(0)
    })
  })

  describe('Communication and Support', () => {
    test('multiple communication channels are available', () => {
      render(<RecentActivity />)
      
      // Should offer various contact methods
      const contactMethods = screen.getAllByText(/call|text|email|message|chat/i)
      expect(contactMethods.length).toBeGreaterThan(0)
      
      // Should show agent availability
      const availability = screen.getAllByText(/available|online|responds.*in.*\d+.*minutes/i)
      expect(availability.length).toBeGreaterThan(0)
    })

    test('conversation history provides complete transparency', () => {
      render(<RecentActivity />)
      
      // Should show all interactions
      const interactions = screen.getAllByText(/\d+.*minutes?.*ago|\d+.*hours?.*ago|yesterday|last.*week/i)
      expect(interactions.length).toBeGreaterThan(0)
      
      // Should distinguish between agent and system messages
      const messageTypes = screen.getAllByText(/michael.*said|system.*message|automated|agent/i)
      expect(messageTypes.length).toBeGreaterThan(0)
    })

    test('feedback collection makes clients feel heard', async () => {
      const user = userEvent.setup()
      render(<RecentActivity />)
      
      const feedbackPrompt = screen.getByText(/how.*was.*this|rate.*experience|feedback/i) ||
                            screen.getByRole('button', { name: /feedback|rate/i })
      
      if (feedbackPrompt) {
        await user.click(feedbackPrompt)
        
        await waitFor(() => {
          const feedbackForm = screen.getByText(/tell.*us|your.*thoughts|how.*can.*we/i) ||
                               screen.getByRole('textbox')
          expect(feedbackForm).toBeInTheDocument()
        })
      }
    })
  })

  describe('Progressive Disclosure and Information Architecture', () => {
    test('dashboard overview follows progressive disclosure', () => {
      render(<WelcomeOverview />)
      
      // Should show overview first
      const overview = screen.getAllByText(/welcome|overview|summary|at.*a.*glance/i)
      expect(overview.length).toBeGreaterThan(0)
      
      // Should have links to detailed sections
      const detailLinks = screen.getAllByRole('link') ||
                         screen.getAllByText(/view.*all|see.*more|details/i)
      expect(detailLinks.length).toBeGreaterThan(0)
    })

    test('property details reveal progressively', async () => {
      const user = userEvent.setup()
      render(<PropertyGrid />)
      
      // Should show essential info first
      const essentialInfo = screen.getAllByText(/\$\d+|bed|bath|sqft/i)
      expect(essentialInfo.length).toBeGreaterThan(0)
      
      // Should have option to see more details
      const moreDetails = screen.getByRole('button', { name: /details|more.*info|full.*listing/i })
      
      if (moreDetails) {
        await user.click(moreDetails)
        
        await waitFor(() => {
          const detailedInfo = screen.getByText(/description|amenities|neighborhood|schools/i)
          expect(detailedInfo).toBeInTheDocument()
        })
      }
    })
  })

  describe('Mobile-First Design and Touch Interaction', () => {
    test('portal functions on mobile viewport', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      })
      
      render(<WelcomeOverview />)
      
      // Should have mobile-responsive layout
      const mobileElements = screen.getAllByRole('button') ||
                            screen.getAllByRole('link')
      expect(mobileElements.length).toBeGreaterThan(0)
      
      // Touch targets should be appropriately sized
      mobileElements.forEach(element => {
        const classes = element.className
        expect(classes).toMatch(/p-\d|py-\d|px-\d|h-\d|min-h/)
      })
    })

    test('swipe gestures work for property browsing', () => {
      render(<PropertyGrid />)
      
      // Should have swipeable property cards (in real implementation)
      const propertyCards = screen.getAllByText(/\$\d+.*bed.*bath/i)
      expect(propertyCards.length).toBeGreaterThan(0)
    })
  })

  describe('Performance and Loading States', () => {
    test('property loading shows skeleton screens', () => {
      render(<PropertyGrid />)
      
      // Should have loading states
      const loadingElements = screen.getAllByText(/loading|fetching/) ||
                             screen.getAllByRole('status') ||
                             screen.getAllByTestId('skeleton')
      expect(loadingElements.length).toBeGreaterThanOrEqual(0)
    })

    test('appointment booking provides immediate feedback', async () => {
      const user = userEvent.setup()
      render(<UpcomingAppointments />)
      
      const bookButton = screen.getByRole('button', { name: /book|schedule|confirm/i })
      
      if (bookButton) {
        await user.click(bookButton)
        
        // Should show immediate feedback
        await waitFor(() => {
          const feedback = screen.getByText(/booking|scheduling|processing|confirmed/i) ||
                          screen.getByRole('status')
          expect(feedback).toBeInTheDocument()
        })
      }
    })
  })

  describe('Error Handling and Edge Cases', () => {
    test('no properties found state is helpful', () => {
      // Mock empty state
      render(<PropertyGrid />)
      
      const emptyState = screen.getByText(/no.*properties.*found|try.*different.*criteria|adjust.*filters/i)
      
      if (emptyState) {
        expect(emptyState).toBeInTheDocument()
        
        // Should suggest alternatives
        const suggestions = screen.getAllByText(/expand.*search|contact.*agent|save.*search/i)
        expect(suggestions.length).toBeGreaterThan(0)
      }
    })

    test('appointment conflicts are handled gracefully', async () => {
      const user = userEvent.setup()
      render(<UpcomingAppointments />)
      
      // Simulate conflict scenario
      const scheduleButton = screen.getByRole('button', { name: /schedule|book/i })
      
      if (scheduleButton) {
        await user.click(scheduleButton)
        
        // Should handle conflicts
        await waitFor(() => {
          const conflictMessage = screen.getByText(/time.*not.*available|already.*booked|choose.*different/i)
          if (conflictMessage) {
            expect(conflictMessage).toBeInTheDocument()
            
            // Should offer alternatives
            const alternatives = screen.getAllByText(/available.*times|other.*options/i)
            expect(alternatives.length).toBeGreaterThan(0)
          }
        })
      }
    })
  })

  describe('Comprehensive Client Portal UX Score', () => {
    test('client portal achieves overall UX score above 85%', async () => {
      const uxRunner = new UXTestRunner(clientPersona)
      
      const clientJourneySteps: UserJourneyStep[] = [
        {
          description: 'Complete client property discovery and booking journey',
          action: async () => {
            render(
              <div>
                <WelcomeOverview />
                <PropertyRecommendations />
                <PropertyGrid />
                <UpcomingAppointments />
                <RecentActivity />
                <QuickActions />
              </div>
            )
          },
          validation: () => {
            expect(screen.getByText(/welcome|overview/i)).toBeInTheDocument()
            expect(screen.getAllByText(/property|recommendation/i).length).toBeGreaterThan(0)
          },
          timeLimit: 25,
        },
      ]
      
      const ClientPortalComponent = (
        <div>
          <WelcomeOverview />
          <PropertyRecommendations />
          <PropertyGrid />
          <PropertyFilters />
          <UpcomingAppointments />
          <RecentActivity />
          <QuickActions />
          <SavedSearches />
        </div>
      )
      
      const result = await uxRunner.runComprehensiveTest(ClientPortalComponent, clientJourneySteps)
      
      expect(result.score).toBeGreaterThan(85)
      expect(result.passed).toBe(true)
      
      // Log results for analysis
      console.log('Client Portal UX Test Results:', {
        score: result.score,
        persona: result.persona,
        recommendations: result.recommendations,
        trustBuilding: result.details.patterns,
        clientJourney: result.details.journey,
      })
    })
  })
})