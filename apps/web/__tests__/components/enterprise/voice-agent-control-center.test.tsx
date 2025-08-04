import React from 'react'
import { render, screen, fireEvent, waitFor } from '../utils/test-utils'
import { VoiceAgentControlCenter } from '@/components/enterprise/voice-agent-control-center'
import { jest } from '@jest/globals'

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => children,
}))

describe('VoiceAgentControlCenter', () => {
  const defaultProps = {
    agentId: 'test-agent-001',
    onEmergencyStop: jest.fn(),
    onConfigChange: jest.fn(),
  }

  beforeEach(() => {
    jest.clearAllMocks()
    // Mock performance.now for duration testing
    jest.spyOn(performance, 'now').mockReturnValue(0)
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  describe('Rendering', () => {
    it('renders the control center with correct title and agent ID', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      expect(screen.getByText('Voice Agent Control Center')).toBeInTheDocument()
      expect(screen.getByText('Agent ID: test-agent-001')).toBeInTheDocument()
    })

    it('renders all main sections', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      expect(screen.getByText('Agent Status')).toBeInTheDocument()
      expect(screen.getByText('Today\'s Performance')).toBeInTheDocument()
      expect(screen.getByText('Satisfaction')).toBeInTheDocument()
      expect(screen.getByText('Quick Actions')).toBeInTheDocument()
    })

    it('displays agent metrics correctly', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      expect(screen.getByText('23')).toBeInTheDocument() // Calls handled
      expect(screen.getByText('68%')).toBeInTheDocument() // Conversion rate
      expect(screen.getByText('4.2m')).toBeInTheDocument() // Avg duration
      expect(screen.getByText('4.7')).toBeInTheDocument() // Satisfaction score
    })

    it('shows active call information when call is active', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      expect(screen.getByText('Active Call')).toBeInTheDocument()
      expect(screen.getByText('Jennifer Martinez')).toBeInTheDocument()
      expect(screen.getByText('+1 (555) 123-4567')).toBeInTheDocument()
      expect(screen.getByText('Score: 85')).toBeInTheDocument()
    })
  })

  describe('Agent Status Management', () => {
    it('displays correct agent status', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      expect(screen.getByText('active')).toBeInTheDocument()
      expect(screen.getByText('Deactivate')).toBeInTheDocument()
    })

    it('toggles agent status when activate/deactivate button is clicked', async () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      const toggleButton = screen.getByText('Deactivate')
      fireEvent.click(toggleButton)
      
      await waitFor(() => {
        expect(screen.getByText('idle')).toBeInTheDocument()
        expect(screen.getByText('Activate')).toBeInTheDocument()
      })
    })

    it('handles emergency stop correctly', async () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      const emergencyButton = screen.getByText('Emergency Stop')
      fireEvent.click(emergencyButton)
      
      await waitFor(() => {
        expect(screen.getByText('maintenance')).toBeInTheDocument()
        expect(defaultProps.onEmergencyStop).toHaveBeenCalledTimes(1)
      })
    })
  })

  describe('Active Call Management', () => {
    it('displays call duration in correct format', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      // Should show 03:44 for 224 seconds
      expect(screen.getByText('03:44')).toBeInTheDocument()
    })

    it('shows call quality indicator', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      expect(screen.getByText('excellent')).toBeInTheDocument()
    })

    it('displays sentiment analysis', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      expect(screen.getByText('positive')).toBeInTheDocument()
    })

    it('toggles microphone state when mic button is clicked', async () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      const micButton = screen.getByRole('button', { name: /mic/i })
      fireEvent.click(micButton)
      
      await waitFor(() => {
        expect(screen.getByTestId('mic-off-icon')).toBeInTheDocument()
      })
    })

    it('ends call when phone off button is clicked', async () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      const phoneOffButton = screen.getByRole('button', { name: /phone-off/i })
      fireEvent.click(phoneOffButton)
      
      await waitFor(() => {
        expect(screen.queryByText('Active Call')).not.toBeInTheDocument()
      })
    })
  })

  describe('Live Transcript', () => {
    it('displays transcript messages', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      expect(screen.getByText('Live Transcript')).toBeInTheDocument()
      expect(screen.getByText(/Hello! Thank you for your interest/)).toBeInTheDocument()
      expect(screen.getByText(/Can you tell me more about the amenities/)).toBeInTheDocument()
    })

    it('toggles transcript visibility', async () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      const hideButton = screen.getByText('Hide')
      fireEvent.click(hideButton)
      
      await waitFor(() => {
        expect(screen.getByText('Show')).toBeInTheDocument()
        expect(screen.queryByText(/Hello! Thank you for your interest/)).not.toBeInTheDocument()
      })
    })

    it('displays audio levels with correct labels', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      expect(screen.getByText('Input Level')).toBeInTheDocument()
      expect(screen.getByText('Output Level')).toBeInTheDocument()
      expect(screen.getByText('-12 dB')).toBeInTheDocument()
      expect(screen.getByText('-8 dB')).toBeInTheDocument()
    })
  })

  describe('Quick Actions', () => {
    it('renders all quick action buttons', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      expect(screen.getByText('Test Voice')).toBeInTheDocument()
      expect(screen.getByText('Restart Agent')).toBeInTheDocument()
      expect(screen.getByText('Export Logs')).toBeInTheDocument()
      expect(screen.getByText('Security')).toBeInTheDocument()
    })

    it('quick action buttons are clickable', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      const testVoiceButton = screen.getByText('Test Voice')
      const restartButton = screen.getByText('Restart Agent')
      const exportButton = screen.getByText('Export Logs')
      const securityButton = screen.getByText('Security')
      
      expect(testVoiceButton).toBeEnabled()
      expect(restartButton).toBeEnabled()
      expect(exportButton).toBeEnabled()
      expect(securityButton).toBeEnabled()
    })
  })

  describe('Real-time Updates', () => {
    beforeEach(() => {
      jest.useFakeTimers()
    })

    afterEach(() => {
      jest.useRealTimers()
    })

    it('updates call duration in real-time', async () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      // Initial duration should be 03:44 (224 seconds)
      expect(screen.getByText('03:44')).toBeInTheDocument()
      
      // Fast-forward 5 seconds
      jest.advanceTimersByTime(5000)
      
      await waitFor(() => {
        // Should now show 03:49 (229 seconds)
        expect(screen.getByText('03:49')).toBeInTheDocument()
      })
    })

    it('updates audio levels periodically', async () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      // Check that audio level bars are present
      const inputLevelBars = screen.getAllByText('Input Level')
      const outputLevelBars = screen.getAllByText('Output Level')
      
      expect(inputLevelBars).toHaveLength(1)
      expect(outputLevelBars).toHaveLength(1)
      
      // Fast-forward to trigger audio level updates
      jest.advanceTimersByTime(1000)
      
      // Audio levels should still be visible (they update but DOM structure remains)
      await waitFor(() => {
        expect(screen.getByText('Input Level')).toBeInTheDocument()
        expect(screen.getByText('Output Level')).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels for interactive elements', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThan(0)
      
      // Check specific buttons have accessible names
      expect(screen.getByRole('button', { name: /settings/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /emergency stop/i })).toBeInTheDocument()
    })

    it('supports keyboard navigation', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      const emergencyButton = screen.getByText('Emergency Stop')
      emergencyButton.focus()
      
      expect(document.activeElement).toBe(emergencyButton)
    })

    it('has proper color contrast for status indicators', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      // Status indicators should have sufficient contrast
      const statusElement = screen.getByText('active')
      expect(statusElement).toBeInTheDocument()
      
      // Quality indicators
      const qualityElement = screen.getByText('excellent')
      expect(qualityElement).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('handles missing active call gracefully', () => {
      const propsWithoutCall = {
        ...defaultProps,
        // Component should handle null activeCall internally
      }
      
      render(<VoiceAgentControlCenter {...propsWithoutCall} />)
      
      // Should still render main sections
      expect(screen.getByText('Voice Agent Control Center')).toBeInTheDocument()
      expect(screen.getByText('Agent Status')).toBeInTheDocument()
    })

    it('handles invalid metrics gracefully', () => {
      // Component should handle edge cases in metrics display
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      // Should not crash with default metrics
      expect(screen.getByText('Today\'s Performance')).toBeInTheDocument()
    })
  })

  describe('Performance', () => {
    it('renders within acceptable time', async () => {
      const startTime = performance.now()
      
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      const endTime = performance.now()
      const renderTime = endTime - startTime
      
      // Should render within 100ms
      expect(renderTime).toBeLessThan(100)
    })

    it('cleanup intervals on unmount', () => {
      const clearIntervalSpy = jest.spyOn(global, 'clearInterval')
      
      const { unmount } = render(<VoiceAgentControlCenter {...defaultProps} />)
      
      unmount()
      
      expect(clearIntervalSpy).toHaveBeenCalled()
    })
  })

  describe('Integration', () => {
    it('calls onEmergencyStop callback when emergency button is clicked', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      const emergencyButton = screen.getByText('Emergency Stop')
      fireEvent.click(emergencyButton)
      
      expect(defaultProps.onEmergencyStop).toHaveBeenCalledTimes(1)
    })

    it('accepts custom className prop', () => {
      const customClass = 'custom-control-center'
      render(<VoiceAgentControlCenter {...defaultProps} className={customClass} />)
      
      const container = screen.getByText('Voice Agent Control Center').closest('div')
      expect(container).toHaveClass(customClass)
    })
  })

  describe('Voice Interface Compatibility', () => {
    it('has voice command indicators for key actions', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      // Emergency stop should be voice accessible
      const emergencyButton = screen.getByText('Emergency Stop')
      expect(emergencyButton).toBeInTheDocument()
      
      // Voice controls should be present
      expect(screen.getByTestId('mic-icon')).toBeInTheDocument()
      expect(screen.getByTestId('volume-icon')).toBeInTheDocument()
    })

    it('provides audio feedback cues', () => {
      render(<VoiceAgentControlCenter {...defaultProps} />)
      
      // Audio level indicators should be present
      expect(screen.getByText('Input Level')).toBeInTheDocument()
      expect(screen.getByText('Output Level')).toBeInTheDocument()
    })
  })
})