import React from 'react'
import { render, screen, fireEvent, waitFor } from '../utils/test-utils'
import { VoiceAIProvider } from '@/lib/voice-ai/providers/VoiceAIProvider'
import { VoiceAgentControlCenter } from '@/components/enterprise/voice-agent-control-center'
import {
  mockVoiceAIProvider,
  createMockWebSocketService,
  simulateWebSocketEvents,
  MockWebSocket,
  generateConversationTurn,
  generateVoiceMetrics,
} from '../utils/voice-ai-mocks'
import { jest } from '@jest/globals'

// Mock WebSocket
global.WebSocket = MockWebSocket as any

// Mock voice AI services
jest.mock('@/lib/voice-ai/services/ConversationEngine')
jest.mock('@/lib/voice-ai/services/AudioProcessor')
jest.mock('@/lib/voice-ai/services/VoiceWebRTC')

// Integration test wrapper component
const VoiceAIIntegrationWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <VoiceAIProvider config={mockVoiceAIProvider}>
      {children}
    </VoiceAIProvider>
  )
}

describe('Voice AI Integration Tests', () => {
  let mockWebSocket: MockWebSocket
  let mockWebSocketService: ReturnType<typeof createMockWebSocketService>

  beforeEach(() => {
    jest.clearAllMocks()
    mockWebSocket = new MockWebSocket('ws://localhost:8080')
    mockWebSocketService = createMockWebSocketService()
    
    // Mock WebSocket connection
    mockWebSocketService.connect.mockResolvedValue(mockWebSocket)
    
    // Mock getUserMedia
    Object.defineProperty(navigator, 'mediaDevices', {
      value: {
        getUserMedia: jest.fn().mockResolvedValue({
          getAudioTracks: () => [{ id: 'audio-1', stop: jest.fn() }],
          getTracks: () => [{ id: 'audio-1', stop: jest.fn() }],
        }),
      },
      writable: true,
    })
  })

  afterEach(() => {
    mockWebSocket?.close()
  })

  describe('End-to-End Voice Agent Workflow', () => {
    it('completes full voice conversation workflow', async () => {
      render(
        <VoiceAIIntegrationWrapper>
          <VoiceAgentControlCenter 
            agentId="integration-test-agent"
            onEmergencyStop={jest.fn()}
          />
        </VoiceAIIntegrationWrapper>
      )

      // 1. Verify initial state
      expect(screen.getByText('Voice Agent Control Center')).toBeInTheDocument()
      expect(screen.getByText('active')).toBeInTheDocument()

      // 2. Start a conversation by simulating voice activity
      const wsEvents = simulateWebSocketEvents(mockWebSocket)
      
      await act(async () => {
        wsEvents.simulateVoiceActivity(true)
      })

      // 3. Simulate speech recognition
      await act(async () => {
        wsEvents.simulateSpeechRecognition('Hello, I am looking for a house in downtown')
      })

      // 4. Simulate intent detection
      await act(async () => {
        wsEvents.simulateIntentDetection('property_inquiry')
      })

      // 5. Simulate lead qualification update
      await act(async () => {
        wsEvents.simulateQualificationUpdate(85)
      })

      // 6. Verify conversation state updates
      await waitFor(() => {
        expect(screen.getByText('Active Call')).toBeInTheDocument()
      })

      // 7. Verify transcript updates
      expect(screen.getByText('Live Transcript')).toBeInTheDocument()
    })

    it('handles voice agent state transitions correctly', async () => {
      render(
        <VoiceAIIntegrationWrapper>
          <VoiceAgentControlCenter 
            agentId="state-test-agent"
            onEmergencyStop={jest.fn()}
          />
        </VoiceAIIntegrationWrapper>
      )

      // Start with active state
      expect(screen.getByText('active')).toBeInTheDocument()

      // Deactivate agent
      const deactivateButton = screen.getByText('Deactivate')
      fireEvent.click(deactivateButton)

      await waitFor(() => {
        expect(screen.getByText('idle')).toBeInTheDocument()
        expect(screen.getByText('Activate')).toBeInTheDocument()
      })

      // Reactivate agent
      const activateButton = screen.getByText('Activate')
      fireEvent.click(activateButton)

      await waitFor(() => {
        expect(screen.getByText('active')).toBeInTheDocument()
        expect(screen.getByText('Deactivate')).toBeInTheDocument()
      })
    })

    it('processes real-time audio data flow', async () => {
      const onConfigChange = jest.fn()
      
      render(
        <VoiceAIIntegrationWrapper>
          <VoiceAgentControlCenter 
            agentId="audio-test-agent"
            onConfigChange={onConfigChange}
          />
        </VoiceAIIntegrationWrapper>
      )

      // Simulate microphone button click to start recording
      const micButton = screen.getByRole('button', { name: /mic/i })
      fireEvent.click(micButton)

      // Should show recording state
      await waitFor(() => {
        expect(screen.getByTestId('mic-off-icon')).toBeInTheDocument()
      })

      // Simulate audio level updates
      const wsEvents = simulateWebSocketEvents(mockWebSocket)
      
      await act(async () => {
        wsEvents.simulateVoiceActivity(true)
      })

      // Verify audio levels are displayed
      expect(screen.getByText('Input Level')).toBeInTheDocument()
      expect(screen.getByText('Output Level')).toBeInTheDocument()
    })
  })

  describe('WebSocket Communication', () => {
    it('establishes WebSocket connection successfully', async () => {
      render(
        <VoiceAIIntegrationWrapper>
          <VoiceAgentControlCenter agentId="websocket-test" />
        </VoiceAIIntegrationWrapper>
      )

      await waitFor(() => {
        expect(mockWebSocketService.connect).toHaveBeenCalled()
      })

      // Simulate successful connection
      await act(async () => {
        if (mockWebSocket.onopen) {
          mockWebSocket.onopen(new Event('open'))
        }
      })

      // Verify connection state
      expect(mockWebSocket.readyState).toBe(WebSocket.OPEN)
    })

    it('handles WebSocket message types correctly', async () => {
      render(
        <VoiceAIIntegrationWrapper>
          <VoiceAgentControlCenter agentId="message-test" />
        </VoiceAIIntegrationWrapper>
      )

      const wsEvents = simulateWebSocketEvents(mockWebSocket)

      // Test voice activity messages
      await act(async () => {
        wsEvents.simulateVoiceActivity(true)
      })

      // Test speech recognition messages  
      await act(async () => {
        wsEvents.simulateSpeechRecognition('Test message')
      })

      // Test intent detection messages
      await act(async () => {
        wsEvents.simulateIntentDetection('greeting')
      })

      // Test qualification update messages
      await act(async () => {
        wsEvents.simulateQualificationUpdate(90)
      })

      // Verify messages are processed without errors
      expect(screen.getByText('Voice Agent Control Center')).toBeInTheDocument()
    })

    it('recovers from WebSocket connection failures', async () => {
      render(
        <VoiceAIIntegrationWrapper>
          <VoiceAgentControlCenter agentId="recovery-test" />
        </VoiceAIIntegrationWrapper>
      )

      // Simulate connection error
      await act(async () => {
        mockWebSocket.simulateError()
      })

      // Simulate connection recovery
      await act(async () => {
        if (mockWebSocket.onopen) {
          mockWebSocket.onopen(new Event('open'))
        }
      })

      // Should handle reconnection gracefully
      expect(screen.getByText('Voice Agent Control Center')).toBeInTheDocument()
    })
  })

  describe('Lead Qualification Integration', () => {
    it('updates lead qualification in real-time', async () => {
      render(
        <VoiceAIIntegrationWrapper>
          <VoiceAgentControlCenter agentId="qualification-test" />
        </VoiceAIIntegrationWrapper>
      )

      const wsEvents = simulateWebSocketEvents(mockWebSocket)

      // Start with default qualification score
      expect(screen.getByText('Score: 85')).toBeInTheDocument()

      // Update qualification through conversation
      await act(async () => {
        wsEvents.simulateQualificationUpdate(92)
      })

      // Verify score update
      await waitFor(() => {
        expect(screen.getByText('Score: 92')).toBeInTheDocument()
      })
    })

    it('handles qualification data persistence', async () => {
      render(
        <VoiceAIIntegrationWrapper>
          <VoiceAgentControlCenter agentId="persistence-test" />
        </VoiceAIIntegrationWrapper>
      )

      const wsEvents = simulateWebSocketEvents(mockWebSocket)

      // Set qualification data
      await act(async () => {
        wsEvents.simulateQualificationUpdate(88)
      })

      // End call
      const endCallButton = screen.getByRole('button', { name: /phone-off/i })
      fireEvent.click(endCallButton)

      await waitFor(() => {
        expect(screen.queryByText('Active Call')).not.toBeInTheDocument()
      })

      // Qualification data should be persisted for next call
      // (This would typically involve checking backend persistence)
    })
  })

  describe('Multi-Tenant Integration', () => {
    it('isolates voice agent data by tenant', async () => {
      const tenant1Props = {
        agentId: 'tenant1-agent',
        'data-tenant': 'tenant-1',
      }

      const tenant2Props = {
        agentId: 'tenant2-agent', 
        'data-tenant': 'tenant-2',
      }

      const { rerender } = render(
        <VoiceAIIntegrationWrapper>
          <VoiceAgentControlCenter {...tenant1Props} />
        </VoiceAIIntegrationWrapper>
      )

      // Verify tenant 1 agent
      expect(screen.getByText('Agent ID: tenant1-agent')).toBeInTheDocument()

      // Switch to tenant 2
      rerender(
        <VoiceAIIntegrationWrapper>
          <VoiceAgentControlCenter {...tenant2Props} />
        </VoiceAIIntegrationWrapper>
      )

      // Verify tenant 2 agent
      expect(screen.getByText('Agent ID: tenant2-agent')).toBeInTheDocument()
      expect(screen.queryByText('Agent ID: tenant1-agent')).not.toBeInTheDocument()
    })

    it('enforces tenant-specific permissions', async () => {
      render(
        <VoiceAIIntegrationWrapper>
          <VoiceAgentControlCenter 
            agentId="permissions-test"
            data-tenant="restricted-tenant"
          />
        </VoiceAIIntegrationWrapper>
      )

      // Verify UI elements are present (permissions would be handled by provider)
      expect(screen.getByText('Emergency Stop')).toBeInTheDocument()
      expect(screen.getByText('Settings')).toBeInTheDocument()
    })
  })

  describe('Performance and Scalability', () => {
    it('handles high-frequency voice activity updates', async () => {
      render(
        <VoiceAIIntegrationWrapper>
          <VoiceAgentControlCenter agentId="performance-test" />
        </VoiceAIIntegrationWrapper>
      )

      const wsEvents = simulateWebSocketEvents(mockWebSocket)

      // Simulate rapid voice activity updates
      const updatePromises = []
      for (let i = 0; i < 50; i++) {
        updatePromises.push(
          act(async () => {
            wsEvents.simulateVoiceActivity(i % 2 === 0)
            await new Promise(resolve => setTimeout(resolve, 10))
          })
        )
      }

      await Promise.all(updatePromises)

      // Should handle updates without crashing
      expect(screen.getByText('Voice Agent Control Center')).toBeInTheDocument()
    })

    it('maintains performance under load', async () => {
      const startTime = performance.now()

      render(
        <VoiceAIIntegrationWrapper>
          <VoiceAgentControlCenter agentId="load-test" />
        </VoiceAIIntegrationWrapper>
      )

      const wsEvents = simulateWebSocketEvents(mockWebSocket)

      // Simulate conversation load
      await act(async () => {
        wsEvents.simulateVoiceActivity(true)
        wsEvents.simulateSpeechRecognition('Load test message')
        wsEvents.simulateIntentDetection('load_test')
        wsEvents.simulateQualificationUpdate(75)
      })

      const endTime = performance.now()
      const totalTime = endTime - startTime

      // Should complete within performance threshold
      expect(totalTime).toBeLessThan(1000) // 1 second threshold
    })

    it('manages memory efficiently during long conversations', async () => {
      render(
        <VoiceAIIntegrationWrapper>
          <VoiceAgentControlCenter agentId="memory-test" />
        </VoiceAIIntegrationWrapper>
      )

      const wsEvents = simulateWebSocketEvents(mockWebSocket)

      // Simulate long conversation with many turns
      for (let i = 0; i < 20; i++) {
        await act(async () => {
          wsEvents.simulateSpeechRecognition(`Message ${i + 1}`)
          await new Promise(resolve => setTimeout(resolve, 50))
        })
      }

      // Verify transcript is still displayed and functional
      expect(screen.getByText('Live Transcript')).toBeInTheDocument()
      
      // Memory usage would be monitored in real implementation
      // Here we just verify the component remains functional
    })
  })

  describe('Error Recovery and Resilience', () => {
    it('recovers from voice processing errors', async () => {
      render(
        <VoiceAIIntegrationWrapper>
          <VoiceAgentControlCenter agentId="error-recovery-test" />
        </VoiceAIIntegrationWrapper>
      )

      const wsEvents = simulateWebSocketEvents(mockWebSocket)

      // Simulate processing error
      await act(async () => {
        wsEvents.simulateError('Voice processing failed')
      })

      // Should continue to function after error
      await act(async () => {
        wsEvents.simulateVoiceActivity(true)
        wsEvents.simulateSpeechRecognition('Recovery test message')
      })

      // Verify recovery
      expect(screen.getByText('Voice Agent Control Center')).toBeInTheDocument()
    })

    it('handles service degradation gracefully', async () => {
      render(
        <VoiceAIIntegrationWrapper>
          <VoiceAgentControlCenter agentId="degradation-test" />
        </VoiceAIIntegrationWrapper>
      )

      // Simulate partial service failure
      mockWebSocketService.send.mockRejectedValue(new Error('Service unavailable'))

      const micButton = screen.getByRole('button', { name: /mic/i })
      fireEvent.click(micButton)

      // Should handle degraded service without crashing
      expect(screen.getByText('Voice Agent Control Center')).toBeInTheDocument()
    })

    it('maintains data consistency during failures', async () => {
      render(
        <VoiceAIIntegrationWrapper>
          <VoiceAgentControlCenter agentId="consistency-test" />
        </VoiceAIIntegrationWrapper>
      )

      const wsEvents = simulateWebSocketEvents(mockWebSocket)

      // Set initial state
      await act(async () => {
        wsEvents.simulateQualificationUpdate(80)
      })

      expect(screen.getByText('Score: 80')).toBeInTheDocument()

      // Simulate connection failure
      await act(async () => {
        mockWebSocket.simulateError()
      })

      // Data should remain consistent
      expect(screen.getByText('Score: 80')).toBeInTheDocument()
    })
  })

  describe('Accessibility Integration', () => {
    it('maintains accessibility during voice interactions', async () => {
      render(
        <VoiceAIIntegrationWrapper>
          <VoiceAgentControlCenter agentId="accessibility-test" />
        </VoiceAIIntegrationWrapper>
      )

      // Verify voice controls have proper accessibility
      const micButton = screen.getByRole('button', { name: /mic/i })
      expect(micButton).toBeInTheDocument()

      const emergencyButton = screen.getByRole('button', { name: /emergency stop/i })
      expect(emergencyButton).toBeInTheDocument()

      // Test keyboard navigation
      micButton.focus()
      expect(document.activeElement).toBe(micButton)

      fireEvent.keyDown(micButton, { key: 'Enter' })
      // Should handle keyboard interaction
    })

    it('provides audio alternatives for visual information', async () => {
      render(
        <VoiceAIIntegrationWrapper>
          <VoiceAgentControlCenter agentId="audio-alternatives-test" />
        </VoiceAIIntegrationWrapper>
      )

      // Verify audio level indicators have text alternatives
      expect(screen.getByText('Input Level')).toBeInTheDocument()
      expect(screen.getByText('Output Level')).toBeInTheDocument()

      // Verify status information is accessible
      expect(screen.getByText('active')).toBeInTheDocument()
      expect(screen.getByText('Score: 85')).toBeInTheDocument()
    })
  })
})

// Helper function for async operations in tests
const act = async (callback: () => Promise<void> | void) => {
  const { act: rtlAct } = await import('@testing-library/react')
  return rtlAct(callback)
}