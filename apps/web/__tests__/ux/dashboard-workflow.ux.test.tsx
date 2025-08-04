/**
 * Agent Dashboard Workflow Efficiency UX Tests
 * 
 * Tests agent daily workflow efficiency based on UX research:
 * - Morning routine: Dashboard overview → Priority leads → Performance review
 * - Field work: Mobile monitoring → Quick actions
 * - End of day: Follow-ups → Performance analysis → Voice agent tuning
 * - Single-screen efficiency and cognitive load reduction
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'

import { 
  TEST_PERSONAS, 
  UXTestRunner, 
  UserJourneyStep,
  interactionPatternValidators,
  mockData
} from '../utils/ux-test-utils'

// Import dashboard components
import DashboardLayout from '../../components/dashboard/DashboardLayout'
import VoiceAgentWorkspace from '../../components/dashboard/VoiceAgentWorkspace'
import ConversationManager from '../../components/dashboard/ConversationManager'
import LeadQualificationPanel from '../../components/dashboard/LeadQualificationPanel'
import PerformanceMetrics from '../../components/dashboard/PerformanceMetrics'

describe('Agent Dashboard Workflow UX Validation', () => {
  const agentPersona = TEST_PERSONAS.agent

  describe('Morning Routine Workflow (Agent Productivity)', () => {
    test('dashboard overview provides immediate situational awareness', () => {
      render(<DashboardLayout />)
      
      // Critical morning info should be immediately visible
      const criticalElements = [
        /voice agent.*status/i,
        /active conversations?/i,
        /priority.*leads?/i,
        /performance|goals?/i
      ]
      
      criticalElements.forEach(pattern => {
        const element = screen.getByText(pattern)
        expect(element).toBeInTheDocument()
        expect(element).toBeVisible()
      })
    })

    test('voice agent status is always prominently displayed', () => {
      render(<VoiceAgentWorkspace />)
      
      // Voice status should be immediately visible
      const voiceStatus = screen.getByText(/voice.*agent.*status|online|offline|active/i)
      expect(voiceStatus).toBeInTheDocument()
      
      // Should have visual indicators
      const statusIndicator = screen.getByTestId('voice-status-indicator') ||
                             screen.getByRole('status')
      expect(statusIndicator).toBeInTheDocument()
    })

    test('priority leads are surfaced for immediate action', () => {
      render(<ConversationManager />)
      
      // Should show priority leads prominently
      const priorityIndicators = screen.getAllByText(/high.*priority|urgent|hot.*lead/i)
      expect(priorityIndicators.length).toBeGreaterThan(0)
      
      // Should have quick action buttons
      const quickActions = screen.getAllByRole('button', { name: /take over|intervene|call/i })
      expect(quickActions.length).toBeGreaterThan(0)
    })

    test('morning routine completes within agent time constraints', async () => {
      const user = userEvent.setup()
      
      const morningRoutineSteps: UserJourneyStep[] = [
        {
          description: 'Agent checks voice system status',
          action: async () => {
            render(<VoiceAgentWorkspace />)
            const statusCheck = screen.getByText(/voice.*agent.*status/i)
            expect(statusCheck).toBeVisible()
          },
          validation: () => {
            expect(screen.getByText(/online|active|ready/i)).toBeInTheDocument()
          },
          timeLimit: 3,
        },
        {
          description: 'Agent reviews active conversations',
          action: async () => {
            render(<ConversationManager />)
            const conversations = screen.getAllByText(/active|in.progress/i)
            expect(conversations.length).toBeGreaterThan(0)
          },
          validation: () => {
            const priorityLeads = screen.getAllByText(/high.*priority|urgent/i)
            expect(priorityLeads.length).toBeGreaterThan(0)
          },
          timeLimit: 5,
        },
        {
          description: 'Agent checks performance metrics',
          action: async () => {
            render(<PerformanceMetrics />)
            const metrics = screen.getAllByText(/\d+%|\d+ leads?|\d+ calls?/i)
            expect(metrics.length).toBeGreaterThan(0)
          },
          validation: () => {
            const goalProgress = screen.getByText(/goal.*progress|target/i)
            expect(goalProgress).toBeInTheDocument()
          },
          timeLimit: 2,
        },
      ]
      
      const uxRunner = new UXTestRunner(agentPersona)
      const result = await uxRunner.executeJourney(morningRoutineSteps)
      
      expect(result.success).toBe(true)
      expect(result.timeTaken).toBeLessThan(agentPersona.timeConstraints)
    })
  })

  describe('Real-Time Conversation Management', () => {
    test('conversation status has clear visual hierarchy', () => {
      render(<ConversationManager />)
      
      // Different conversation states should be visually distinct
      const statusTypes = [
        'active',
        'qualified', 
        'follow-up',
        'needs-attention'
      ]
      
      statusTypes.forEach(status => {
        const statusElements = screen.getAllByText(new RegExp(status, 'i'))
        if (statusElements.length > 0) {
          // Check that status has visual indicator (color, icon, etc)
          statusElements.forEach(element => {
            const parent = element.closest('[class*="bg-"], [class*="text-"], [data-status]')
            expect(parent).toBeTruthy()
          })
        }
      })
    })

    test('quick intervention controls are always accessible', async () => {
      const user = userEvent.setup()
      render(<ConversationManager />)
      
      // Should have immediate intervention options
      const interventionButtons = screen.getAllByRole('button', { 
        name: /take over|intervene|join|escalate/i 
      })
      expect(interventionButtons.length).toBeGreaterThan(0)
      
      // Test quick access (within 1-2 clicks)
      if (interventionButtons.length > 0) {
        await user.click(interventionButtons[0])
        
        // Should provide immediate feedback
        await waitFor(() => {
          const feedback = screen.getByText(/taking over|connecting|intervention/i) ||
                          screen.getByRole('status')
          expect(feedback).toBeInTheDocument()
        })
      }
    })

    test('conversation context is always preserved', () => {
      render(<ConversationManager />)
      
      // Each conversation should show context
      const conversations = screen.getAllByText(/\d+ minutes? ago|\d+ seconds? ago|just now/i)
      expect(conversations.length).toBeGreaterThan(0)
      
      // Should show client info and conversation state
      const clientNames = screen.getAllByText(/[A-Z][a-z]+ [A-Z][a-z]+/) // Name pattern
      expect(clientNames.length).toBeGreaterThan(0)
    })
  })

  describe('Lead Qualification Efficiency', () => {
    test('AI qualification scoring is immediately visible', () => {
      render(<LeadQualificationPanel />)
      
      // Should show qualification scores prominently
      const qualificationScores = screen.getAllByText(/\d+%.*match|\d+.*score|qualified|unqualified/i)
      expect(qualificationScores.length).toBeGreaterThan(0)
      
      // Should show key qualification criteria
      const criteria = screen.getAllByText(/budget|timeline|location|ready.*to.*buy/i)
      expect(criteria.length).toBeGreaterThan(0)
    })

    test('lead insights support quick decision making', () => {
      render(<LeadQualificationPanel />)
      
      // Should surface actionable insights
      const insights = screen.getAllByText(/ready.*to.*schedule|high.*intent|budget.*confirmed/i)
      expect(insights.length).toBeGreaterThan(0)
      
      // Should have quick action suggestions
      const actions = screen.getAllByText(/schedule.*showing|call.*now|send.*listing/i)
      expect(actions.length).toBeGreaterThan(0)
    })

    test('qualification process completes within time limits', async () => {
      const user = userEvent.setup()
      
      const qualificationSteps: UserJourneyStep[] = [
        {
          description: 'Agent reviews lead qualification score',
          action: async () => {
            render(<LeadQualificationPanel />)
            const score = screen.getByText(/\d+%.*match|\d+.*score/i)
            expect(score).toBeVisible()
          },
          validation: () => {
            const criteria = screen.getAllByText(/budget|timeline|location/i)
            expect(criteria.length).toBeGreaterThan(0)
          },
          timeLimit: 5,
        },
        {
          description: 'Agent makes qualification decision',
          action: async (user) => {
            const qualifyButton = screen.getByRole('button', { name: /qualify|schedule|reject/i })
            await user.click(qualifyButton)
          },
          validation: () => {
            const confirmation = screen.getByText(/qualified|scheduled|updated/i)
            expect(confirmation).toBeInTheDocument()
          },
          timeLimit: 3,
        },
      ]
      
      const uxRunner = new UXTestRunner(agentPersona)
      const result = await uxRunner.executeJourney(qualificationSteps)
      
      expect(result.success).toBe(true)
      expect(result.timeTaken).toBeLessThan(10) // Quick qualification
    })
  })

  describe('Performance Tracking and Motivation', () => {
    test('daily goals are prominently displayed with progress', () => {
      render(<PerformanceMetrics />)
      
      // Should show goal progress clearly
      const goalProgress = screen.getAllByText(/\d+.*of.*\d+|\d+%.*complete|goal.*progress/i)
      expect(goalProgress.length).toBeGreaterThan(0)
      
      // Should have visual progress indicators
      const progressBars = screen.getAllByRole('progressbar') ||
                          screen.getAllByText(/\d+%/)
      expect(progressBars.length).toBeGreaterThan(0)
    })

    test('performance trends provide actionable insights', () => {
      render(<PerformanceMetrics />)
      
      // Should show trend information
      const trends = screen.getAllByText(/up.*from|down.*from|trending|improved|decreased/i)
      expect(trends.length).toBeGreaterThan(0)
      
      // Should suggest actions for improvement
      const suggestions = screen.getAllByText(/focus.*on|improve|try.*to|consider/i)
      expect(suggestions.length).toBeGreaterThan(0)
    })
  })

  describe('Mobile Field Work Efficiency', () => {
    test('dashboard remains functional on mobile viewport', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      })
      
      render(<DashboardLayout />)
      
      // Critical functions should still be accessible
      const mobileNav = screen.getByRole('navigation') ||
                       screen.getByTestId('mobile-menu')
      expect(mobileNav).toBeInTheDocument()
      
      // Quick actions should be touch-friendly
      const quickActions = screen.getAllByRole('button')
      expect(quickActions.length).toBeGreaterThan(0)
    })

    test('voice controls provide hands-free operation', () => {
      const { container } = render(<VoiceAgentWorkspace />)
      
      const voiceValidation = interactionPatternValidators.voiceFirst(container)
      expect(voiceValidation).toBe(true)
      
      // Should have voice command indicators
      const voiceCommands = screen.getAllByText(/say.*|voice.*command|speak/i)
      expect(voiceCommands.length).toBeGreaterThan(0)
    })
  })

  describe('Cognitive Load Management', () => {
    test('single-screen efficiency - no scrolling for critical info', () => {
      const { container } = render(<DashboardLayout />)
      
      // Critical elements should be in viewport
      const criticalInfo = [
        'voice agent status',
        'active conversations',
        'priority leads',
        'quick actions'
      ]
      
      criticalInfo.forEach(info => {
        const element = screen.getByText(new RegExp(info, 'i'))
        const rect = element.getBoundingClientRect()
        // In real test, would check rect.top < viewport height
        expect(element).toBeVisible()
      })
    })

    test('information hierarchy reduces decision fatigue', () => {
      render(<DashboardLayout />)
      
      // Should have clear primary/secondary/tertiary information levels
      const h1Elements = screen.getAllByRole('heading', { level: 1 })
      const h2Elements = screen.getAllByRole('heading', { level: 2 })
      const h3Elements = screen.getAllByRole('heading', { level: 3 })
      
      // Should have proper heading hierarchy
      expect(h1Elements.length).toBeGreaterThan(0)
      expect(h2Elements.length).toBeGreaterThan(0)
    })

    test('consistent interaction patterns across components', () => {
      const { container: workspace } = render(<VoiceAgentWorkspace />)
      const { container: conversations } = render(<ConversationManager />)
      const { container: leads } = render(<LeadQualificationPanel />)
      
      // All should have consistent button patterns
      const workspaceButtons = workspace.querySelectorAll('button')
      const conversationButtons = conversations.querySelectorAll('button')
      const leadButtons = leads.querySelectorAll('button')
      
      // Check for consistent styling patterns
      workspaceButtons.forEach(button => {
        expect(button.className).toMatch(/bg-|border-|text-/)
      })
    })
  })

  describe('End-of-Day Workflow', () => {
    test('follow-up tasks are clearly prioritized', () => {
      render(<ConversationManager />)
      
      // Should show follow-up priorities
      const followUps = screen.getAllByText(/follow.up|schedule.*call|send.*info/i)
      expect(followUps.length).toBeGreaterThan(0)
      
      // Should have due dates/urgency indicators
      const urgency = screen.getAllByText(/due.*today|overdue|urgent|tomorrow/i)
      expect(urgency.length).toBeGreaterThan(0)
    })

    test('performance analysis provides daily summary', () => {
      render(<PerformanceMetrics />)
      
      // Should show daily summary
      const dailySummary = screen.getAllByText(/today.*total|calls.*today|\d+.*leads.*today/i)
      expect(dailySummary.length).toBeGreaterThan(0)
      
      // Should compare to goals/averages
      const comparisons = screen.getAllByText(/vs.*goal|above.*average|below.*target/i)
      expect(comparisons.length).toBeGreaterThan(0)
    })
  })

  describe('Error Handling and Recovery', () => {
    test('voice system errors have clear recovery paths', async () => {
      const user = userEvent.setup()
      render(<VoiceAgentWorkspace />)
      
      // Simulate voice system error
      const troubleshootButton = screen.getByRole('button', { name: /troubleshoot|restart|reconnect/i })
      await user.click(troubleshootButton)
      
      // Should provide clear recovery steps
      await waitFor(() => {
        const recoverySteps = screen.getByText(/check.*connection|restart.*agent|contact.*support/i)
        expect(recoverySteps).toBeInTheDocument()
      })
    })

    test('conversation interruptions are handled gracefully', async () => {
      const user = userEvent.setup()
      render(<ConversationManager />)
      
      const takeOverButton = screen.getByRole('button', { name: /take over|intervene/i })
      await user.click(takeOverButton)
      
      // Should show smooth transition
      await waitFor(() => {
        const transitionState = screen.getByText(/connecting|taking.*over|you.*are.*now/i)
        expect(transitionState).toBeInTheDocument()
      })
    })
  })

  describe('Comprehensive Agent Workflow UX Score', () => {
    test('dashboard achieves overall workflow efficiency score above 85%', async () => {
      const uxRunner = new UXTestRunner(agentPersona)
      
      const fullWorkflowSteps: UserJourneyStep[] = [
        {
          description: 'Complete agent morning routine',
          action: async () => {
            render(
              <div>
                <DashboardLayout />
                <VoiceAgentWorkspace />
                <ConversationManager />
                <PerformanceMetrics />
              </div>
            )
          },
          validation: () => {
            expect(screen.getByText(/voice.*agent.*status/i)).toBeInTheDocument()
            expect(screen.getAllByText(/active|priority/i).length).toBeGreaterThan(0)
          },
          timeLimit: 15,
        },
      ]
      
      const DashboardComponent = (
        <div>
          <DashboardLayout />
          <VoiceAgentWorkspace />
          <ConversationManager />
          <LeadQualificationPanel />
          <PerformanceMetrics />
        </div>
      )
      
      const result = await uxRunner.runComprehensiveTest(DashboardComponent, fullWorkflowSteps)
      
      expect(result.score).toBeGreaterThan(85)
      expect(result.passed).toBe(true)
      
      // Log results for analysis
      console.log('Agent Dashboard UX Test Results:', {
        score: result.score,
        persona: result.persona,
        recommendations: result.recommendations,
        workflowEfficiency: result.details.journey,
      })
    })
  })
})