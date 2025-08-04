import React from 'react'
import { render, screen, fireEvent, waitFor } from '../utils/test-utils'
import { VoiceAgentControlCenter } from '@/components/enterprise/voice-agent-control-center'
import {
  testScreenReaderCompatibility,
  testKeyboardNavigation,
  testAriaAttributes,
  testVoiceInterfaceAccessibility,
  testColorContrast,
  accessibilityMatchers,
  testVoiceCommandAccessibility,
  runAutomatedAccessibilityTests,
} from '../utils/accessibility-utils'
import { jest } from '@jest/globals'

// Extend Jest matchers
expect.extend(accessibilityMatchers)

// Mock speech synthesis for voice interface testing
const mockSpeechSynthesis = {
  speak: jest.fn(),
  cancel: jest.fn(),
  pause: jest.fn(),
  resume: jest.fn(),
  getVoices: jest.fn().mockReturnValue([
    { name: 'Female Voice', lang: 'en-US' },
    { name: 'Male Voice', lang: 'en-US' },
  ]),
}

Object.defineProperty(global.window, 'speechSynthesis', {
  value: mockSpeechSynthesis,
  writable: true,
})

// Mock Web Speech API
Object.defineProperty(global.window, 'SpeechRecognition', {
  value: jest.fn().mockImplementation(() => ({
    start: jest.fn(),
    stop: jest.fn(),
    abort: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
  })),
  writable: true,
})

describe('Voice Interface Accessibility Tests', () => {
  const defaultProps = {
    agentId: 'accessibility-test-agent',
    onEmergencyStop: jest.fn(),
    onConfigChange: jest.fn(),
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('WCAG 2.1 AA Compliance', () => {
    it('meets color contrast requirements', () => {
      const { container } = render(<VoiceAgentControlCenter {...defaultProps} />)
      
      // Test status indicators
      const statusElement = screen.getByText('active')
      expect(statusElement).toHaveSufficientColorContrast(4.5)
      
      // Test quality indicators
      const qualityElement = screen.getByText('excellent')
      expect(qualityElement).toHaveSufficientColorContrast(4.5)
      
      // Test button text
      const emergencyButton = screen.getByText('Emergency Stop')
      expect(emergencyButton).toHaveSufficientColorContrast(4.5)
    })

    it('provides proper focus indicators', async () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      const focusableElements = [
        screen.getByText('Settings'),
        screen.getByText('Emergency Stop'),
        screen.getByText('Deactivate'),
        screen.getByRole('button', { name: /mic/i }),
      ]
      
      for (const element of focusableElements) {
        element.focus()
        expect(element).toHaveFocus()
        
        // Check for visible focus indicator
        const computedStyle = getComputedStyle(element)
        expect(
          computedStyle.outline !== 'none' || 
          computedStyle.boxShadow.includes('inset')
        ).toBe(true)
      }
    })

    it('supports keyboard navigation', async () => {
      const { container } = render(<VoiceAgentControlCenter {...defaultProps} />)
      
      const navResult = await testKeyboardNavigation(container)
      
      expect(navResult.focusableCount).toBeGreaterThan(0)
      expect(navResult.focusOrderMatches).toBe(true)
      expect(container).toSupportKeyboardNavigation()
    })

    it('has valid ARIA attributes', () => {
      const { container } = render(<VoiceAgentControlCenter {...defaultProps} />)
      
      expect(container).toHaveValidAriaAttributes()
      
      // Check specific ARIA attributes
      const micButton = screen.getByRole('button', { name: /mic/i })
      expect(micButton).toHaveAttribute('role', 'button')
      
      // Check for proper button labels
      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(
          button.getAttribute('aria-label') || 
          button.textContent || 
          button.getAttribute('title')
        ).toBeTruthy()
      })
    })
  })

  describe('Screen Reader Compatibility', () => {
    it('provides comprehensive screen reader support', () => {
      const { container } = render(<VoiceAgentControlCenter {...defaultProps} />)
      
      const issues = testScreenReaderCompatibility(container)
      expect(issues).toHaveLength(0)
    })

    it('announces voice agent status changes', async () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      // Check for status announcements
      const statusElement = screen.getByText('active')
      expect(statusElement).toHaveAttribute('aria-live', 'polite')
      
      // Toggle agent status
      const toggleButton = screen.getByText('Deactivate')
      fireEvent.click(toggleButton)
      
      await waitFor(() => {
        const newStatusElement = screen.getByText('idle')
        expect(newStatusElement).toBeInTheDocument()
      })
    })

    it('provides descriptive labels for voice controls', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      const micButton = screen.getByRole('button', { name: /mic/i })
      expect(micButton).toHaveAttribute('aria-label', 'Toggle microphone')
      
      const volumeButton = screen.getByRole('button', { name: /volume/i })
      expect(volumeButton).toHaveAttribute('aria-label', 'Adjust volume')
      
      const phoneButton = screen.getByRole('button', { name: /phone-off/i })
      expect(phoneButton).toHaveAttribute('aria-label', 'End call')
    })

    it('announces conversation transcript updates', async () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      const transcriptContainer = screen.getByText('Live Transcript').closest('[role="region"]')
      expect(transcriptContainer).toHaveAttribute('aria-live', 'polite')
      expect(transcriptContainer).toHaveAttribute('aria-label', 'Live conversation transcript')
    })

    it('provides context for audio levels', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      const inputLevelElement = screen.getByText('Input Level').closest('div')
      expect(inputLevelElement).toHaveAttribute('role', 'progressbar')
      expect(inputLevelElement).toHaveAttribute('aria-label', 'Microphone input level')
      
      const outputLevelElement = screen.getByText('Output Level').closest('div')
      expect(outputLevelElement).toHaveAttribute('role', 'progressbar')
      expect(outputLevelElement).toHaveAttribute('aria-label', 'Audio output level')
    })
  })

  describe('Voice Command Accessibility', () => {
    it('supports voice command accessibility features', () => {
      const { container } = render(<VoiceAgentControlCenter {...defaultProps} />)
      
      expect(container).toSupportVoiceInterface()
    })

    it('provides voice command alternatives for visual actions', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      // Emergency stop should support voice command
      const emergencyButton = screen.getByText('Emergency Stop')
      const voiceResult = testVoiceCommandAccessibility(emergencyButton, 'emergency stop')
      expect(voiceResult.isAccessible).toBe(true)
      
      // Voice controls should support commands
      const micButton = screen.getByRole('button', { name: /mic/i })
      const micVoiceResult = testVoiceCommandAccessibility(micButton, 'toggle microphone')
      expect(micVoiceResult.isAccessible).toBe(true)
    })

    it('announces voice command availability', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      // Check for voice command hints
      const helpText = screen.getByText(/voice commands available/i)
      expect(helpText).toBeInTheDocument()
      expect(helpText).toHaveAttribute('role', 'status')
    })

    it('provides audio feedback for voice interactions', async () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      // Click microphone button
      const micButton = screen.getByRole('button', { name: /mic/i })
      fireEvent.click(micButton)
      
      // Should trigger audio feedback
      await waitFor(() => {
        expect(mockSpeechSynthesis.speak).toHaveBeenCalledWith(
          expect.objectContaining({
            text: expect.stringContaining('microphone')
          })
        )
      })
    })
  })

  describe('Multi-Modal Accessibility', () => {
    it('provides multiple ways to access functionality', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      // Emergency stop should be accessible via:
      // 1. Mouse click
      // 2. Keyboard (Enter/Space)
      // 3. Voice command
      const emergencyButton = screen.getByText('Emergency Stop')
      
      // Test mouse interaction
      fireEvent.click(emergencyButton)
      expect(defaultProps.onEmergencyStop).toHaveBeenCalled()
      
      // Test keyboard interaction
      fireEvent.keyDown(emergencyButton, { key: 'Enter' })
      fireEvent.keyDown(emergencyButton, { key: ' ' })
    })

    it('synchronizes visual and audio information', async () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      // Visual status should match audio announcements
      const statusElement = screen.getByText('active')
      expect(statusElement).toBeInTheDocument()
      
      // Audio should describe the same status
      await waitFor(() => {
        expect(mockSpeechSynthesis.speak).toHaveBeenCalledWith(
          expect.objectContaining({
            text: expect.stringContaining('agent is active')
          })
        )
      })
    })

    it('provides redundant information across modalities', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      // Call quality should be indicated both visually and textually
      const qualityElement = screen.getByText('excellent')
      expect(qualityElement).toBeInTheDocument()
      
      // Should also have accessible description
      const qualityContainer = qualityElement.closest('[role="status"]')
      expect(qualityContainer).toHaveAttribute('aria-describedby', 'quality-description')
      
      const qualityDescription = screen.getByText(/call quality is excellent/i)
      expect(qualityDescription).toBeInTheDocument()
    })
  })

  describe('Error Accessibility', () => {
    it('announces errors accessibly', async () => {
      const onEmergencyStop = jest.fn().mockImplementation(() => {
        throw new Error('Emergency stop failed')
      })
      
      render(<VoiceAgentControlCenter {...defaultProps} onEmergencyStop={onEmergencyStop} />)
      
      const emergencyButton = screen.getByText('Emergency Stop')
      fireEvent.click(emergencyButton)
      
      // Error should be announced
      await waitFor(() => {
        const errorElement = screen.getByRole('alert')
        expect(errorElement).toBeInTheDocument()
        expect(errorElement).toHaveTextContent(/error/i)
      })
    })

    it('provides recovery instructions', async () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      // Simulate connection error
      const errorElement = screen.getByRole('alert', { name: /connection error/i })
      expect(errorElement).toBeInTheDocument()
      
      // Should provide recovery instructions
      const recoveryInstructions = screen.getByText(/to recover, try/i)
      expect(recoveryInstructions).toBeInTheDocument()
      expect(recoveryInstructions).toHaveAttribute('role', 'status')
    })

    it('maintains accessibility during error states', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      // Even with errors, controls should remain accessible
      const micButton = screen.getByRole('button', { name: /mic/i })
      expect(micButton).toBeEnabled()
      expect(micButton).toHaveAttribute('tabindex', '0')
    })
  })

  describe('Performance Impact on Accessibility', () => {
    it('maintains accessibility performance under load', async () => {
      const startTime = performance.now()
      
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      // Simulate heavy accessibility tree
      const buttons = screen.getAllByRole('button')
      const headings = screen.getAllByRole('heading')
      const regions = screen.getAllByRole('region')
      
      const endTime = performance.now()
      const renderTime = endTime - startTime
      
      // Should render accessibility features within reasonable time
      expect(renderTime).toBeLessThan(200) // 200ms threshold
      expect(buttons.length).toBeGreaterThan(0)
      expect(headings.length).toBeGreaterThan(0)
      expect(regions.length).toBeGreaterThan(0)
    })

    it('does not degrade during real-time updates', async () => {
      const { container } = render(<VoiceAgentControlCenter {...defaultProps} />)
      
      // Start with valid accessibility
      let issues = testScreenReaderCompatibility(container)
      expect(issues).toHaveLength(0)
      
      // Simulate real-time updates
      for (let i = 0; i < 10; i++) {
        await act(async () => {
          // Trigger updates that would happen during real conversation
          fireEvent.click(screen.getByRole('button', { name: /mic/i }))
          await new Promise(resolve => setTimeout(resolve, 100))
        })
      }
      
      // Accessibility should still be maintained
      issues = testScreenReaderCompatibility(container)
      expect(issues).toHaveLength(0)
    })
  })

  describe('Automated Accessibility Testing', () => {
    it('passes automated accessibility audit', async () => {
      const { container } = render(<VoiceAgentControlCenter {...defaultProps} />)
      
      const results = await runAutomatedAccessibilityTests(container, {
        level: 'AA',
        tags: ['wcag2a', 'wcag2aa', 'wcag21aa'],
      })
      
      expect(results.violations).toHaveLength(0)
    })

    it('passes voice interface specific tests', async () => {
      const { container } = render(<VoiceAgentControlCenter {...defaultProps} />)
      
      const voiceIssues = testVoiceInterfaceAccessibility(container)
      expect(voiceIssues).toHaveLength(0)
    })

    it('validates ARIA implementation', () => {
      const { container } = render(<VoiceAgentControlCenter {...defaultProps} />)
      
      const ariaIssues = testAriaAttributes(container)
      expect(ariaIssues).toHaveLength(0)
    })
  })

  describe('Accessibility Documentation', () => {
    it('provides accessibility usage examples', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      // Check for accessibility help text
      const helpButton = screen.getByRole('button', { name: /accessibility help/i })
      expect(helpButton).toBeInTheDocument()
      
      fireEvent.click(helpButton)
      
      const helpDialog = screen.getByRole('dialog', { name: /accessibility guide/i })
      expect(helpDialog).toBeInTheDocument()
      
      // Should contain usage instructions
      expect(screen.getByText(/keyboard shortcuts/i)).toBeInTheDocument()
      expect(screen.getByText(/voice commands/i)).toBeInTheDocument()
      expect(screen.getByText(/screen reader support/i)).toBeInTheDocument()
    })

    it('includes accessibility metadata', () => {
      const { container } = render(<VoiceAgentControlCenter {...defaultProps} />)
      
      // Check for accessibility metadata
      const mainRegion = container.querySelector('[role="main"]')
      expect(mainRegion).toHaveAttribute('aria-label', 'Voice Agent Control Center')
      expect(mainRegion).toHaveAttribute('aria-describedby', 'control-center-description')
      
      const description = screen.getByText(/voice agent control interface/i)
      expect(description).toBeInTheDocument()
      expect(description).toHaveAttribute('id', 'control-center-description')
    })
  })
})

// Helper function for async operations
const act = async (callback: () => Promise<void> | void) => {
  const { act: rtlAct } = await import('@testing-library/react')
  return rtlAct(callback)
}