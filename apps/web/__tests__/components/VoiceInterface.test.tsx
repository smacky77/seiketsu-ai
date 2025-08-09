/**
 * Comprehensive unit tests for VoiceInterface component
 * Tests voice interaction, AI processing, and user experience
 */
import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { VoiceInterface } from '@/components/features/voice/VoiceInterface'
import { useVoiceEngine } from '@/lib/voice-ai/hooks/useVoiceEngine'
import { useVoiceAnalytics } from '@/lib/voice-ai/hooks/useVoiceAnalytics'

// Mock hooks
vi.mock('@/lib/voice-ai/hooks/useVoiceEngine')
vi.mock('@/lib/voice-ai/hooks/useVoiceAnalytics')
vi.mock('@/lib/voice-ai/services/AudioProcessor')

const mockUseVoiceEngine = vi.mocked(useVoiceEngine)
const mockUseVoiceAnalytics = vi.mocked(useVoiceAnalytics)

describe('VoiceInterface', () => {
  const mockVoiceEngine = {
    isListening: false,
    isProcessing: false,
    transcript: '',
    response: '',
    confidence: 0,
    error: null,
    isSupported: true,
    startListening: vi.fn(),
    stopListening: vi.fn(),
    processVoiceInput: vi.fn(),
    reset: vi.fn()
  }

  const mockAnalytics = {
    trackVoiceInteraction: vi.fn(),
    trackConversationStart: vi.fn(),
    trackConversationEnd: vi.fn(),
    trackError: vi.fn()
  }

  beforeEach(() => {
    mockUseVoiceEngine.mockReturnValue(mockVoiceEngine)
    mockUseVoiceAnalytics.mockReturnValue(mockAnalytics)
    
    // Mock MediaRecorder API
    global.MediaRecorder = vi.fn().mockImplementation(() => ({
      start: vi.fn(),
      stop: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      state: 'inactive'
    }))

    // Mock getUserMedia
    global.navigator.mediaDevices = {
      getUserMedia: vi.fn().mockResolvedValue({
        getTracks: () => [{ stop: vi.fn() }]
      })
    } as any
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders initial state correctly', () => {
    render(<VoiceInterface />)
    
    expect(screen.getByRole('button', { name: /start voice/i })).toBeInTheDocument()
    expect(screen.getByText(/ready to listen/i)).toBeInTheDocument()
    expect(screen.queryByText(/listening/i)).not.toBeInTheDocument()
  })

  it('displays unsupported message when voice not supported', () => {
    mockUseVoiceEngine.mockReturnValue({
      ...mockVoiceEngine,
      isSupported: false
    })

    render(<VoiceInterface />)
    
    expect(screen.getByText(/voice input not supported/i)).toBeInTheDocument()
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('starts listening when start button is clicked', async () => {
    render(<VoiceInterface />)
    
    const startButton = screen.getByRole('button', { name: /start voice/i })
    
    await act(async () => {
      fireEvent.click(startButton)
    })

    expect(mockVoiceEngine.startListening).toHaveBeenCalledTimes(1)
    expect(mockAnalytics.trackConversationStart).toHaveBeenCalledTimes(1)
  })

  it('displays listening state correctly', () => {
    mockUseVoiceEngine.mockReturnValue({
      ...mockVoiceEngine,
      isListening: true
    })

    render(<VoiceInterface />)
    
    expect(screen.getByText(/listening/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /stop/i })).toBeInTheDocument()
    expect(screen.getByTestId('voice-visualizer')).toBeInTheDocument()
  })

  it('displays transcript when available', () => {
    const transcript = "Hello, I'm looking for a house"
    mockUseVoiceEngine.mockReturnValue({
      ...mockVoiceEngine,
      transcript,
      confidence: 0.95
    })

    render(<VoiceInterface />)
    
    expect(screen.getByText(transcript)).toBeInTheDocument()
    expect(screen.getByText(/95% confidence/i)).toBeInTheDocument()
  })

  it('displays AI response when available', () => {
    const response = "I'd be happy to help you find a house. What's your budget?"
    mockUseVoiceEngine.mockReturnValue({
      ...mockVoiceEngine,
      response
    })

    render(<VoiceInterface />)
    
    expect(screen.getByText(response)).toBeInTheDocument()
    expect(screen.getByTestId('ai-response-audio')).toBeInTheDocument()
  })

  it('displays processing state correctly', () => {
    mockUseVoiceEngine.mockReturnValue({
      ...mockVoiceEngine,
      isProcessing: true
    })

    render(<VoiceInterface />)
    
    expect(screen.getByText(/processing/i)).toBeInTheDocument()
    expect(screen.getByTestId('processing-spinner')).toBeInTheDocument()
  })

  it('handles errors correctly', () => {
    const error = 'Microphone access denied'
    mockUseVoiceEngine.mockReturnValue({
      ...mockVoiceEngine,
      error
    })

    render(<VoiceInterface />)
    
    expect(screen.getByText(error)).toBeInTheDocument()
    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(mockAnalytics.trackError).toHaveBeenCalledWith('voice_error', { error })
  })

  it('stops listening when stop button is clicked', async () => {
    mockUseVoiceEngine.mockReturnValue({
      ...mockVoiceEngine,
      isListening: true
    })

    render(<VoiceInterface />)
    
    const stopButton = screen.getByRole('button', { name: /stop/i })
    
    await act(async () => {
      fireEvent.click(stopButton)
    })

    expect(mockVoiceEngine.stopListening).toHaveBeenCalledTimes(1)
    expect(mockAnalytics.trackConversationEnd).toHaveBeenCalledTimes(1)
  })

  it('resets conversation when reset button is clicked', async () => {
    mockUseVoiceEngine.mockReturnValue({
      ...mockVoiceEngine,
      transcript: 'Previous conversation',
      response: 'Previous response'
    })

    render(<VoiceInterface />)
    
    const resetButton = screen.getByRole('button', { name: /reset/i })
    
    await act(async () => {
      fireEvent.click(resetButton)
    })

    expect(mockVoiceEngine.reset).toHaveBeenCalledTimes(1)
  })

  it('tracks voice interactions correctly', async () => {
    const transcript = "I want to buy a house"
    const response = "Great! Let me help you with that."

    mockUseVoiceEngine.mockReturnValue({
      ...mockVoiceEngine,
      transcript,
      response
    })

    render(<VoiceInterface />)

    await waitFor(() => {
      expect(mockAnalytics.trackVoiceInteraction).toHaveBeenCalledWith({
        transcript,
        response,
        confidence: expect.any(Number),
        processingTimeMs: expect.any(Number)
      })
    })
  })

  it('handles microphone permissions correctly', async () => {
    // Mock permission denied
    global.navigator.mediaDevices.getUserMedia = vi.fn().mockRejectedValue(
      new Error('Permission denied')
    )

    render(<VoiceInterface />)
    
    const startButton = screen.getByRole('button', { name: /start voice/i })
    
    await act(async () => {
      fireEvent.click(startButton)
    })

    await waitFor(() => {
      expect(screen.getByText(/microphone permission/i)).toBeInTheDocument()
    })

    expect(mockAnalytics.trackError).toHaveBeenCalledWith('permission_error', {
      error: 'Permission denied'
    })
  })

  it('displays conversation history', () => {
    const conversationHistory = [
      { type: 'user', content: 'Hello', timestamp: Date.now() - 10000 },
      { type: 'assistant', content: 'Hi there!', timestamp: Date.now() - 5000 }
    ]

    render(<VoiceInterface conversationHistory={conversationHistory} />)
    
    expect(screen.getByText('Hello')).toBeInTheDocument()
    expect(screen.getByText('Hi there!')).toBeInTheDocument()
    expect(screen.getAllByTestId('conversation-message')).toHaveLength(2)
  })

  it('auto-scrolls conversation to bottom', async () => {
    const scrollIntoViewMock = vi.fn()
    Element.prototype.scrollIntoView = scrollIntoViewMock

    const { rerender } = render(<VoiceInterface />)

    // Add new message
    rerender(
      <VoiceInterface 
        conversationHistory={[
          { type: 'user', content: 'New message', timestamp: Date.now() }
        ]}
      />
    )

    await waitFor(() => {
      expect(scrollIntoViewMock).toHaveBeenCalled()
    })
  })

  it('supports keyboard shortcuts', async () => {
    render(<VoiceInterface />)
    
    // Test spacebar to start/stop
    await act(async () => {
      fireEvent.keyDown(document, { key: ' ', code: 'Space' })
    })

    expect(mockVoiceEngine.startListening).toHaveBeenCalledTimes(1)

    // Mock listening state
    mockUseVoiceEngine.mockReturnValue({
      ...mockVoiceEngine,
      isListening: true
    })

    await act(async () => {
      fireEvent.keyDown(document, { key: ' ', code: 'Space' })
    })

    expect(mockVoiceEngine.stopListening).toHaveBeenCalledTimes(1)
  })

  it('handles voice confidence levels appropriately', () => {
    const testConfidenceLevels = [
      { confidence: 0.9, expectedClass: 'confidence-high' },
      { confidence: 0.7, expectedClass: 'confidence-medium' },
      { confidence: 0.4, expectedClass: 'confidence-low' }
    ]

    testConfidenceLevels.forEach(({ confidence, expectedClass }) => {
      mockUseVoiceEngine.mockReturnValue({
        ...mockVoiceEngine,
        transcript: 'Test transcript',
        confidence
      })

      const { container } = render(<VoiceInterface />)
      
      expect(container.querySelector(`.${expectedClass}`)).toBeInTheDocument()
    })
  })

  it('provides audio playback controls for responses', () => {
    mockUseVoiceEngine.mockReturnValue({
      ...mockVoiceEngine,
      response: 'Audio response available'
    })

    render(<VoiceInterface />)
    
    const audioPlayer = screen.getByTestId('ai-response-audio')
    const playButton = screen.getByRole('button', { name: /play response/i })
    
    expect(audioPlayer).toBeInTheDocument()
    expect(playButton).toBeInTheDocument()
  })

  it('shows processing time metrics', () => {
    mockUseVoiceEngine.mockReturnValue({
      ...mockVoiceEngine,
      transcript: 'Test input',
      response: 'Test response',
      processingTimeMs: 145
    })

    render(<VoiceInterface />)
    
    expect(screen.getByText(/145ms/i)).toBeInTheDocument()
    expect(screen.getByText(/response time/i)).toBeInTheDocument()
  })

  it('supports accessibility features', () => {
    render(<VoiceInterface />)
    
    const mainButton = screen.getByRole('button', { name: /start voice/i })
    
    // Should have proper ARIA attributes
    expect(mainButton).toHaveAttribute('aria-describedby')
    expect(screen.getByRole('status')).toBeInTheDocument()
    
    // Should support screen reader announcements
    mockUseVoiceEngine.mockReturnValue({
      ...mockVoiceEngine,
      transcript: 'Hello world'
    })

    const { rerender } = render(<VoiceInterface />)
    
    rerender(<VoiceInterface />)
    
    expect(screen.getByRole('status')).toHaveTextContent(/new transcript/i)
  })

  it('handles offline scenarios', () => {
    // Mock offline status
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false
    })

    render(<VoiceInterface />)
    
    expect(screen.getByText(/offline/i)).toBeInTheDocument()
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('implements proper cleanup on unmount', () => {
    const { unmount } = render(<VoiceInterface />)
    
    unmount()
    
    // Verify cleanup was called
    expect(mockVoiceEngine.stopListening).toHaveBeenCalled()
  })
})

describe('VoiceInterface Integration', () => {
  it('completes full voice interaction flow', async () => {
    const mockEngine = {
      ...mockVoiceEngine,
      startListening: vi.fn().mockImplementation(() => {
        // Simulate listening state change
        setTimeout(() => {
          mockUseVoiceEngine.mockReturnValue({
            ...mockVoiceEngine,
            isListening: true
          })
        }, 100)
      }),
      processVoiceInput: vi.fn().mockImplementation(async () => {
        // Simulate processing and response
        return {
          transcript: 'I need help finding a house',
          response: 'I\'d be happy to help you find a house!',
          confidence: 0.92,
          processingTimeMs: 156
        }
      })
    }

    mockUseVoiceEngine.mockReturnValue(mockEngine)

    render(<VoiceInterface />)
    
    // Start voice interaction
    const startButton = screen.getByRole('button', { name: /start voice/i })
    
    await act(async () => {
      fireEvent.click(startButton)
    })

    // Verify analytics tracking
    expect(mockAnalytics.trackConversationStart).toHaveBeenCalled()
    expect(mockAnalytics.trackVoiceInteraction).toHaveBeenCalled()
  })

  it('handles real-time voice updates', async () => {
    let voiceEngineState = { ...mockVoiceEngine }
    
    mockUseVoiceEngine.mockImplementation(() => voiceEngineState)

    const { rerender } = render(<VoiceInterface />)

    // Simulate real-time transcript updates
    await act(async () => {
      voiceEngineState = { ...voiceEngineState, transcript: 'Hello' }
      rerender(<VoiceInterface />)
    })

    expect(screen.getByText('Hello')).toBeInTheDocument()

    await act(async () => {
      voiceEngineState = { ...voiceEngineState, transcript: 'Hello, I need help' }
      rerender(<VoiceInterface />)
    })

    expect(screen.getByText('Hello, I need help')).toBeInTheDocument()
  })
})

describe('VoiceInterface Performance', () => {
  it('renders efficiently with large conversation history', () => {
    const largeHistory = Array.from({ length: 100 }, (_, i) => ({
      type: i % 2 === 0 ? 'user' : 'assistant',
      content: `Message ${i}`,
      timestamp: Date.now() - (100 - i) * 1000
    }))

    const startTime = performance.now()
    render(<VoiceInterface conversationHistory={largeHistory} />)
    const endTime = performance.now()

    // Should render quickly even with large history
    expect(endTime - startTime).toBeLessThan(50) // 50ms threshold
  })

  it('debounces rapid state updates', async () => {
    let updateCount = 0
    const mockEngineWithUpdates = {
      ...mockVoiceEngine,
      transcript: '',
      startListening: vi.fn()
    }

    mockUseVoiceEngine.mockImplementation(() => {
      updateCount++
      return mockEngineWithUpdates
    })

    const { rerender } = render(<VoiceInterface />)

    // Rapid updates
    for (let i = 0; i < 10; i++) {
      await act(async () => {
        mockEngineWithUpdates.transcript = `Update ${i}`
        rerender(<VoiceInterface />)
      })
    }

    // Component should handle rapid updates gracefully
    expect(screen.getByText('Update 9')).toBeInTheDocument()
  })
})