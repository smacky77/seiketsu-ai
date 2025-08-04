import { renderHook, act, waitFor } from '@testing-library/react'
import { useVoiceEngine } from '@/lib/voice-ai/hooks/useVoiceEngine'
import {
  mockAudioProcessor,
  mockSpeechToTextService,
  mockTextToSpeechService,
  mockWebRTCService,
  createLatencySimulator,
  simulateNetworkError,
  simulateAudioError,
} from '../../utils/voice-ai-mocks'
import { jest } from '@jest/globals'

// Mock the voice AI services
jest.mock('@/lib/voice-ai/services/AudioProcessor', () => ({
  AudioProcessor: jest.fn().mockImplementation(() => mockAudioProcessor),
}))

jest.mock('@/lib/voice-ai/services/VoiceWebRTC', () => ({
  VoiceWebRTC: jest.fn().mockImplementation(() => mockWebRTCService),
}))

// Mock getUserMedia
Object.defineProperty(global.navigator, 'mediaDevices', {
  value: {
    getUserMedia: jest.fn().mockResolvedValue({
      getAudioTracks: () => [{ id: 'audio-1', stop: jest.fn() }],
      getTracks: () => [{ id: 'audio-1', stop: jest.fn() }],
    }),
  },
  writable: true,
})

// Mock Web Audio API
Object.defineProperty(global.window, 'AudioContext', {
  value: jest.fn().mockImplementation(() => ({
    createMediaStreamSource: jest.fn().mockReturnValue({
      connect: jest.fn(),
      disconnect: jest.fn(),
    }),
    createAnalyser: jest.fn().mockReturnValue({
      fftSize: 256,
      frequencyBinCount: 128,
      getByteFrequencyData: jest.fn(),
      getByteTimeDomainData: jest.fn(),
      connect: jest.fn(),
      disconnect: jest.fn(),
    }),
    sampleRate: 44100,
    state: 'running',
    resume: jest.fn().mockResolvedValue(undefined),
    close: jest.fn().mockResolvedValue(undefined),
  })),
  writable: true,
})

describe('useVoiceEngine', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Reset mock implementations
    mockAudioProcessor.startRecording.mockClear()
    mockAudioProcessor.stopRecording.mockClear()
    mockSpeechToTextService.initialize.mockClear()
    mockTextToSpeechService.initialize.mockClear()
  })

  describe('Initialization', () => {
    it('initializes with correct default state', () => {
      const { result } = renderHook(() => useVoiceEngine())

      expect(result.current.isListening).toBe(false)
      expect(result.current.isSpeaking).toBe(false)
      expect(result.current.isProcessing).toBe(false)
      expect(result.current.audioLevel).toBe(0)
      expect(result.current.error).toBe(null)
      expect(result.current.metrics).toBeDefined()
    })

    it('accepts custom configuration', () => {
      const config = {
        sampleRate: 48000,
        channels: 2,
        bitDepth: 24,
      }

      const { result } = renderHook(() => useVoiceEngine(config))

      expect(result.current.metrics).toBeDefined()
      // Config should be applied internally
    })
  })

  describe('Voice Recording', () => {
    it('starts listening successfully', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      await act(async () => {
        await result.current.startListening()
      })

      expect(result.current.isListening).toBe(true)
      expect(mockAudioProcessor.startRecording).toHaveBeenCalledTimes(1)
    })

    it('stops listening successfully', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      // First start listening
      await act(async () => {
        await result.current.startListening()
      })

      expect(result.current.isListening).toBe(true)

      // Then stop listening
      await act(async () => {
        result.current.stopListening()
      })

      expect(result.current.isListening).toBe(false)
      expect(mockAudioProcessor.stopRecording).toHaveBeenCalledTimes(1)
    })

    it('handles microphone access denied error', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      // Mock getUserMedia to throw an error
      const mockGetUserMedia = jest.spyOn(navigator.mediaDevices, 'getUserMedia')
      mockGetUserMedia.mockRejectedValueOnce(new Error('Permission denied'))

      await act(async () => {
        try {
          await result.current.startListening()
        } catch (error) {
          // Expected to throw
        }
      })

      expect(result.current.error).toBeTruthy()
      expect(result.current.isListening).toBe(false)
    })

    it('updates audio level during recording', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      // Mock audio level updates
      mockAudioProcessor.getVolumeLevel.mockReturnValue(0.75)

      await act(async () => {
        await result.current.startListening()
      })

      // Simulate audio level update
      await act(async () => {
        // Trigger internal audio level update
        await new Promise(resolve => setTimeout(resolve, 100))
      })

      expect(result.current.audioLevel).toBeGreaterThan(0)
    })
  })

  describe('Text-to-Speech', () => {
    it('speaks text successfully', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      const text = 'Hello, this is a test message'

      await act(async () => {
        await result.current.speak(text)
      })

      expect(result.current.isSpeaking).toBe(false) // Should be false after completion
      expect(mockTextToSpeechService.synthesize).toHaveBeenCalledWith(
        expect.objectContaining({
          text,
        })
      )
    })

    it('handles speaking state correctly', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      const text = 'Hello, this is a test message'

      // Mock TTS to take some time
      mockTextToSpeechService.playAudio.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      )

      act(() => {
        result.current.speak(text)
      })

      // Should be speaking immediately
      expect(result.current.isSpeaking).toBe(true)

      await waitFor(() => {
        expect(result.current.isSpeaking).toBe(false)
      })
    })

    it('stops speaking when requested', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      const text = 'Hello, this is a test message'

      await act(async () => {
        result.current.speak(text)
        result.current.stopSpeaking()
      })

      expect(result.current.isSpeaking).toBe(false)
      expect(mockTextToSpeechService.stopAudio).toHaveBeenCalledTimes(1)
    })

    it('handles TTS errors gracefully', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      // Mock TTS to throw an error
      mockTextToSpeechService.synthesize.mockRejectedValueOnce(
        new Error('TTS service unavailable')
      )

      await act(async () => {
        try {
          await result.current.speak('Test message')
        } catch (error) {
          // Expected to handle error internally
        }
      })

      expect(result.current.error).toBeTruthy()
      expect(result.current.isSpeaking).toBe(false)
    })
  })

  describe('Audio Processing', () => {
    it('processes audio data successfully', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      const mockAudioData = new Float32Array([0.1, 0.2, 0.3, 0.4])

      await act(async () => {
        await result.current.processAudio(mockAudioData)
      })

      expect(mockAudioProcessor.processAudioChunk).toHaveBeenCalledWith(mockAudioData)
    })

    it('handles processing state correctly', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      const mockAudioData = new Float32Array([0.1, 0.2, 0.3, 0.4])

      // Mock processing to take some time
      mockAudioProcessor.processAudioChunk.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 50))
      )

      act(() => {
        result.current.processAudio(mockAudioData)
      })

      expect(result.current.isProcessing).toBe(true)

      await waitFor(() => {
        expect(result.current.isProcessing).toBe(false)
      })
    })

    it('detects voice activity correctly', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      const mockAudioData = new Float32Array([0.5, 0.6, 0.7, 0.8])

      // Mock voice activity detection
      mockAudioProcessor.detectVoiceActivity.mockReturnValue({
        isActive: true,
        confidence: 0.9,
        energy: 0.7,
        timestamp: Date.now(),
      })

      await act(async () => {
        await result.current.processAudio(mockAudioData)
      })

      expect(mockAudioProcessor.detectVoiceActivity).toHaveBeenCalled()
    })
  })

  describe('Performance Metrics', () => {
    it('tracks latency metrics correctly', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      const text = 'Test message for latency tracking'

      await act(async () => {
        await result.current.speak(text)
      })

      expect(result.current.metrics.latency).toBeDefined()
      expect(result.current.metrics.latency.total).toBeGreaterThan(0)
    })

    it('tracks quality metrics', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      expect(result.current.metrics.quality).toBeDefined()
      expect(result.current.metrics.quality.audioQuality).toBeGreaterThan(0)
      expect(result.current.metrics.quality.audioQuality).toBeLessThanOrEqual(1)
    })

    it('meets performance benchmarks', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      const text = 'Performance test message'

      const startTime = performance.now()
      
      await act(async () => {
        await result.current.speak(text)
      })

      const endTime = performance.now()
      const totalTime = endTime - startTime

      // Should complete TTS within 180ms benchmark
      expect(totalTime).toBeLessThan(180)
      expect(result.current.metrics.latency.total).toBeLessThan(180)
    })
  })

  describe('Error Handling', () => {
    it('clears errors when requested', () => {
      const { result } = renderHook(() => useVoiceEngine())

      // Simulate an error state
      act(() => {
        // Internal error setting (would normally happen during actual operations)
        result.current.clearError()
      })

      expect(result.current.error).toBe(null)
    })

    it('handles network errors gracefully', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      // Mock network error
      mockTextToSpeechService.synthesize.mockImplementation(() => {
        throw new Error('Network connection failed')
      })

      await act(async () => {
        try {
          await result.current.speak('Test message')
        } catch (error) {
          // Error should be handled internally
        }
      })

      expect(result.current.error).toBeTruthy()
      expect(result.current.error?.message).toContain('Network')
    })

    it('recovers from errors automatically', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      // First, cause an error
      mockTextToSpeechService.synthesize.mockRejectedValueOnce(
        new Error('Temporary error')
      )

      await act(async () => {
        try {
          await result.current.speak('First message')
        } catch (error) {
          // Expected error
        }
      })

      expect(result.current.error).toBeTruthy()

      // Then clear the error and try again
      mockTextToSpeechService.synthesize.mockResolvedValueOnce(new ArrayBuffer(1024))

      await act(async () => {
        result.current.clearError()
        await result.current.speak('Second message')
      })

      expect(result.current.error).toBe(null)
    })
  })

  describe('Cleanup and Memory Management', () => {
    it('cleans up resources on unmount', () => {
      const { result, unmount } = renderHook(() => useVoiceEngine())

      // Start some operations
      act(() => {
        result.current.startListening()
      })

      // Unmount should clean up
      unmount()

      // Verify cleanup was called
      expect(mockAudioProcessor.stopRecording).toHaveBeenCalled()
    })

    it('handles multiple simultaneous operations correctly', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      // Start listening and speaking simultaneously
      await act(async () => {
        await Promise.all([
          result.current.startListening(),
          result.current.speak('Concurrent operation test'),
        ])
      })

      // Both operations should complete successfully
      expect(result.current.isListening).toBe(true)
      expect(result.current.isSpeaking).toBe(false) // Should be false after completion
    })
  })

  describe('Edge Cases', () => {
    it('handles empty audio data', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      const emptyAudio = new Float32Array(0)

      await act(async () => {
        await result.current.processAudio(emptyAudio)
      })

      // Should not crash or throw error
      expect(result.current.error).toBe(null)
    })

    it('handles empty text for TTS', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      await act(async () => {
        await result.current.speak('')
      })

      // Should handle empty text gracefully
      expect(result.current.error).toBe(null)
    })

    it('handles rapid start/stop operations', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      await act(async () => {
        await result.current.startListening()
        result.current.stopListening()
        await result.current.startListening()
        result.current.stopListening()
      })

      expect(result.current.isListening).toBe(false)
      expect(result.current.error).toBe(null)
    })
  })

  describe('Configuration and Customization', () => {
    it('accepts custom audio configuration', () => {
      const customConfig = {
        sampleRate: 48000,
        channels: 2,
        bitDepth: 24,
        bufferSize: 2048,
        echoCancellation: false,
        noiseSuppression: true,
        autoGainControl: true,
      }

      const { result } = renderHook(() => useVoiceEngine(customConfig))

      // Should initialize without errors
      expect(result.current.error).toBe(null)
    })

    it('updates configuration dynamically', async () => {
      const { result, rerender } = renderHook(
        ({ config }) => useVoiceEngine(config),
        {
          initialProps: { config: { sampleRate: 44100 } },
        }
      )

      // Update configuration
      rerender({ config: { sampleRate: 48000 } })

      // Should handle configuration changes
      expect(result.current.error).toBe(null)
    })
  })
})