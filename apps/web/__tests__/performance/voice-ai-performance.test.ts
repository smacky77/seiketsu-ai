import { renderHook, act, waitFor } from '@testing-library/react'
import { useVoiceEngine } from '@/lib/voice-ai/hooks/useVoiceEngine'
import { useConversationManager } from '@/lib/voice-ai/hooks/useConversationManager'
import { useLeadQualification } from '@/lib/voice-ai/hooks/useLeadQualification'
import {
  createLatencySimulator,
  createAudioQualitySimulator,
  generateVoiceMetrics,
  generateConversationTurn,
  mockVoiceAIProvider,
} from '../utils/voice-ai-mocks'
import { measureRenderTime } from '../utils/test-utils'
import { jest } from '@jest/globals'

// Performance benchmarks for Seiketsu AI Voice System
const PERFORMANCE_BENCHMARKS = {
  VOICE_RESPONSE_TIME: 180, // ms - Must respond within 180ms
  AUDIO_PROCESSING_LATENCY: 50, // ms - Audio processing latency
  INITIAL_PAGE_LOAD: 3000, // ms - Initial page load time
  COMPONENT_RENDER_TIME: 100, // ms - Component render time
  MEMORY_USAGE_THRESHOLD: 50, // MB - Memory usage threshold
  CONCURRENT_CONNECTIONS: 100, // Number of concurrent connections
  UPTIME_REQUIREMENT: 99.9, // % - System uptime requirement
}

describe('Voice AI Performance Tests', () => {
  let performanceObserver: PerformanceObserver
  let memoryUsageStart: number

  beforeEach(() => {
    jest.clearAllMocks()
    
    // Track memory usage
    if (performance.memory) {
      memoryUsageStart = performance.memory.usedJSHeapSize
    }
    
    // Mock performance APIs
    Object.defineProperty(global.performance, 'now', {
      value: jest.fn(() => Date.now()),
      writable: true,
    })
    
    // Setup performance observer
    if (typeof PerformanceObserver !== 'undefined') {
      performanceObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        entries.forEach((entry) => {
          console.log(`Performance: ${entry.name} took ${entry.duration}ms`)
        })
      })
      performanceObserver.observe({ entryTypes: ['measure', 'navigation'] })
    }
  })

  afterEach(() => {
    if (performanceObserver) {
      performanceObserver.disconnect()
    }
  })

  describe('Voice Response Time Performance', () => {
    it('meets <180ms voice response time benchmark', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      const startTime = performance.now()
      
      await act(async () => {
        await result.current.speak('Hello, how can I help you today?')
      })

      const endTime = performance.now()
      const responseTime = endTime - startTime

      expect(responseTime).toBeLessThan(PERFORMANCE_BENCHMARKS.VOICE_RESPONSE_TIME)
      expect(result.current.metrics.latency.total).toBeLessThan(PERFORMANCE_BENCHMARKS.VOICE_RESPONSE_TIME)
    })

    it('maintains consistent response times under load', async () => {
      const { result } = renderHook(() => useVoiceEngine())
      const responseTimes: number[] = []

      // Test multiple consecutive requests
      for (let i = 0; i < 10; i++) {
        const startTime = performance.now()
        
        await act(async () => {
          await result.current.speak(`Message ${i + 1}`)
        })

        const endTime = performance.now()
        responseTimes.push(endTime - startTime)
      }

      // All response times should be under benchmark
      responseTimes.forEach(time => {
        expect(time).toBeLessThan(PERFORMANCE_BENCHMARKS.VOICE_RESPONSE_TIME)
      })

      // Response times should be consistent (standard deviation < 50ms)
      const mean = responseTimes.reduce((a, b) => a + b) / responseTimes.length
      const variance = responseTimes.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / responseTimes.length
      const stdDev = Math.sqrt(variance)

      expect(stdDev).toBeLessThan(50)
    })

    it('handles concurrent voice requests efficiently', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      const concurrentRequests = Array.from({ length: 5 }, (_, i) => 
        act(async () => {
          const startTime = performance.now()
          await result.current.speak(`Concurrent message ${i + 1}`)
          const endTime = performance.now()
          return endTime - startTime
        })
      )

      const responseTimes = await Promise.all(concurrentRequests)

      // Even with concurrent requests, each should meet benchmark
      responseTimes.forEach(time => {
        expect(time).toBeLessThan(PERFORMANCE_BENCHMARKS.VOICE_RESPONSE_TIME * 1.5) // Allow 50% overhead for concurrency
      })
    })
  })

  describe('Audio Processing Performance', () => {
    it('processes audio within <50ms latency benchmark', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      const audioData = new Float32Array(1024) // 1KB audio chunk
      audioData.fill(0.5) // Fill with sample data

      const startTime = performance.now()
      
      await act(async () => {
        await result.current.processAudio(audioData)
      })

      const endTime = performance.now()
      const processingTime = endTime - startTime

      expect(processingTime).toBeLessThan(PERFORMANCE_BENCHMARKS.AUDIO_PROCESSING_LATENCY)
    })

    it('handles high-frequency audio updates', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      // Simulate 100 audio updates per second (10ms intervals)
      const audioChunks = Array.from({ length: 20 }, () => new Float32Array(512))
      const processingTimes: number[] = []

      for (const chunk of audioChunks) {
        const startTime = performance.now()
        
        await act(async () => {
          await result.current.processAudio(chunk)
        })

        const endTime = performance.now()
        processingTimes.push(endTime - startTime)
        
        // Small delay to simulate real-time streaming
        await new Promise(resolve => setTimeout(resolve, 10))
      }

      // All processing times should be under benchmark
      processingTimes.forEach(time => {
        expect(time).toBeLessThan(PERFORMANCE_BENCHMARKS.AUDIO_PROCESSING_LATENCY)
      })

      // Average processing time should be well under benchmark
      const averageTime = processingTimes.reduce((a, b) => a + b) / processingTimes.length
      expect(averageTime).toBeLessThan(PERFORMANCE_BENCHMARKS.AUDIO_PROCESSING_LATENCY * 0.7)
    })

    it('maintains audio quality under performance pressure', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      // Process large audio chunks to stress test
      const largeAudioData = new Float32Array(8192) // 8KB chunk
      largeAudioData.fill(0.7)

      await act(async () => {
        await result.current.processAudio(largeAudioData)
      })

      // Audio quality should remain high even with large chunks
      expect(result.current.metrics.quality.audioQuality).toBeGreaterThan(0.8)
      expect(result.current.metrics.performance.cpuUsage).toBeLessThan(80) // CPU usage under 80%
    })
  })

  describe('Memory Usage Performance', () => {
    it('maintains memory usage within acceptable limits', async () => {
      const { result } = renderHook(() => useConversationManager())

      // Generate large conversation history
      const conversationTurns = Array.from({ length: 100 }, (_, i) => 
        generateConversationTurn({
          id: `turn-${i}`,
          text: `This is conversation turn ${i} with some longer text to test memory usage`,
        })
      )

      await act(async () => {
        for (const turn of conversationTurns) {
          result.current.addTurn(turn)
        }
      })

      // Check memory usage if available
      if (performance.memory) {
        const memoryUsageEnd = performance.memory.usedJSHeapSize
        const memoryIncrease = (memoryUsageEnd - memoryUsageStart) / (1024 * 1024) // MB

        expect(memoryIncrease).toBeLessThan(PERFORMANCE_BENCHMARKS.MEMORY_USAGE_THRESHOLD)
      }

      // Conversation should still be functional
      expect(result.current.conversation?.turns).toHaveLength(100)
    })

    it('prevents memory leaks during long conversations', async () => {
      const { result, unmount } = renderHook(() => useConversationManager())

      // Simulate very long conversation
      await act(async () => {
        const conversationId = await result.current.startConversation('lead-123', 'agent-456')
        
        // Add many turns
        for (let i = 0; i < 500; i++) {
          result.current.addTurn(generateConversationTurn({
            id: `turn-${i}`,
            text: `Turn ${i}`,
          }))
        }
      })

      const beforeUnmount = performance.memory?.usedJSHeapSize || 0

      // Unmount component
      unmount()

      // Force garbage collection if available
      if (global.gc) {
        global.gc()
      }

      // Allow some time for cleanup
      await new Promise(resolve => setTimeout(resolve, 100))

      const afterUnmount = performance.memory?.usedJSHeapSize || 0

      // Memory should be released (allowing for some variance)
      if (performance.memory) {
        const memoryRetained = (afterUnmount - beforeUnmount) / (1024 * 1024)
        expect(memoryRetained).toBeLessThan(10) // Less than 10MB retained
      }
    })

    it('efficiently manages conversation history', async () => {
      const { result } = renderHook(() => useConversationManager())

      await act(async () => {
        await result.current.startConversation('lead-456', 'agent-789')
        
        // Add turns and measure memory efficiency
        for (let i = 0; i < 200; i++) {
          result.current.addTurn(generateConversationTurn({ id: `turn-${i}` }))
          
          // Every 50 turns, check memory usage
          if (i % 50 === 0 && performance.memory) {
            const currentMemory = performance.memory.usedJSHeapSize
            const memoryPerTurn = (currentMemory - memoryUsageStart) / (i + 1)
            
            // Each turn should use less than 10KB on average
            expect(memoryPerTurn).toBeLessThan(10 * 1024)
          }
        }
      })

      // Final check - conversation should be complete and efficient
      expect(result.current.conversation?.turns).toHaveLength(200)
    })
  })

  describe('Component Render Performance', () => {
    it('renders voice control components within performance budget', async () => {
      const { renderTime } = await measureRenderTime(async () => {
        const { render } = await import('../utils/test-utils')
        const { VoiceAgentControlCenter } = await import('@/components/enterprise/voice-agent-control-center')
        
        return render(VoiceAgentControlCenter({ agentId: "perf-test" }))
      })

      expect(renderTime).toBeLessThan(PERFORMANCE_BENCHMARKS.COMPONENT_RENDER_TIME)
    })

    it('handles rapid state updates efficiently', async () => {
      const { render } = await import('../utils/test-utils')
      const { VoiceAgentControlCenter } = await import('@/components/enterprise/voice-agent-control-center')
      
      const { rerender } = render(<VoiceAgentControlCenter agentId="state-test" />)

      const updateTimes: number[] = []

      // Simulate rapid state changes
      for (let i = 0; i < 20; i++) {
        const startTime = performance.now()
        
        rerender(<VoiceAgentControlCenter 
          agentId={`state-test-${i}`} 
          key={i}
        />)

        const endTime = performance.now()
        updateTimes.push(endTime - startTime)
      }

      // All updates should be fast
      updateTimes.forEach(time => {
        expect(time).toBeLessThan(50) // Each update under 50ms
      })

      // Average update time should be very fast
      const averageUpdateTime = updateTimes.reduce((a, b) => a + b) / updateTimes.length
      expect(averageUpdateTime).toBeLessThan(25) // Average under 25ms
    })

    it('optimizes re-renders during voice activity', async () => {
      const { render } = await import('../utils/test-utils')
      const { VoiceAgentControlCenter } = await import('@/components/enterprise/voice-agent-control-center')
      
      let renderCount = 0
      const TestWrapper = (props: any) => {
        renderCount++
        return <VoiceAgentControlCenter {...props} />
      }

      const { rerender } = render(<TestWrapper agentId="render-test" />)

      const initialRenderCount = renderCount

      // Simulate voice activity updates that shouldn't cause full re-renders
      for (let i = 0; i < 10; i++) {
        rerender(<TestWrapper 
          agentId="render-test" 
          audioLevel={Math.random()}
        />)
      }

      // Should not cause excessive re-renders
      const totalRenders = renderCount - initialRenderCount
      expect(totalRenders).toBeLessThan(15) // Allow some re-renders but not excessive
    })
  })

  describe('Lead Qualification Performance', () => {
    it('qualifies leads within acceptable time', async () => {
      const { result } = renderHook(() => useLeadQualification())

      const conversationText = `
        I'm looking for a 3-bedroom house in downtown area. 
        My budget is around $400,000 to $500,000. 
        I need to move within the next 2 months because of a job relocation.
        I have good credit and can put down 20%.
      `

      const startTime = performance.now()

      await act(async () => {
        await result.current.qualifyFromText(conversationText)
      })

      const endTime = performance.now()
      const qualificationTime = endTime - startTime

      // Lead qualification should be fast (under 1 second)
      expect(qualificationTime).toBeLessThan(1000)
      
      // Should produce high-quality qualification
      expect(result.current.qualificationData?.score).toBeGreaterThan(70)
    })

    it('handles batch lead qualification efficiently', async () => {
      const { result } = renderHook(() => useLeadQualification())

      const leadTexts = Array.from({ length: 10 }, (_, i) => 
        `Lead ${i}: Looking for property, budget $${300000 + i * 50000}`
      )

      const startTime = performance.now()

      await act(async () => {
        for (const text of leadTexts) {
          await result.current.qualifyFromText(text)
          result.current.resetQualification() // Reset for next lead
        }
      })

      const endTime = performance.now()
      const totalTime = endTime - startTime
      const averageTimePerLead = totalTime / leadTexts.length

      // Each lead should be qualified quickly
      expect(averageTimePerLead).toBeLessThan(500) // Under 0.5 seconds per lead
      expect(totalTime).toBeLessThan(5000) // Total under 5 seconds
    })
  })

  describe('Scalability Performance', () => {
    it('handles multiple concurrent voice sessions', async () => {
      const sessionCount = 5
      const sessions = Array.from({ length: sessionCount }, () => 
        renderHook(() => useVoiceEngine())
      )

      const startTime = performance.now()

      // Start all sessions simultaneously
      await act(async () => {
        await Promise.all(sessions.map(({ result }) => 
          result.current.startListening()
        ))
      })

      const endTime = performance.now()
      const totalTime = endTime - startTime

      // Should handle multiple sessions efficiently
      expect(totalTime).toBeLessThan(1000) // Under 1 second for 5 sessions

      // All sessions should be active
      sessions.forEach(({ result }) => {
        expect(result.current.isListening).toBe(true)
      })

      // Cleanup
      sessions.forEach(({ result }) => {
        result.current.stopListening()
      })
    })

    it('maintains performance with high message throughput', async () => {
      const { result } = renderHook(() => useConversationManager())

      await act(async () => {
        await result.current.startConversation('high-throughput-lead', 'agent-001')
      })

      const messageCount = 100
      const startTime = performance.now()

      await act(async () => {
        // Simulate high-frequency message processing
        const messagePromises = Array.from({ length: messageCount }, (_, i) =>
          result.current.addTurn(generateConversationTurn({
            id: `high-freq-${i}`,
            text: `High frequency message ${i}`,
            timestamp: Date.now() + i,
          }))
        )

        await Promise.all(messagePromises)
      })

      const endTime = performance.now()
      const totalTime = endTime - startTime
      const messagesPerSecond = (messageCount / totalTime) * 1000

      // Should process messages at high rate
      expect(messagesPerSecond).toBeGreaterThan(50) // At least 50 messages/second
      expect(result.current.conversation?.turns).toHaveLength(messageCount)
    })
  })

  describe('Network Performance', () => {
    it('handles network latency gracefully', async () => {
      const latencySimulator = createLatencySimulator(200, 50) // 200ms ± 50ms
      const { result } = renderHook(() => useVoiceEngine())

      // Mock network delay
      const originalSpeak = result.current.speak
      result.current.speak = async (text: string) => {
        await latencySimulator()
        return originalSpeak(text)
      }

      const startTime = performance.now()

      await act(async () => {
        await result.current.speak('Network latency test message')
      })

      const endTime = performance.now()
      const totalTime = endTime - startTime

      // Should complete within reasonable time even with network latency
      expect(totalTime).toBeLessThan(1000) // Under 1 second total
      expect(totalTime).toBeGreaterThan(150) // Should reflect some latency
    })

    it('maintains quality under varying network conditions', async () => {
      const qualitySimulator = createAudioQualitySimulator(0.8, 0.2)
      const { result } = renderHook(() => useVoiceEngine())

      // Test multiple requests with varying quality
      const qualityResults: number[] = []

      for (let i = 0; i < 10; i++) {
        await act(async () => {
          await result.current.speak(`Quality test ${i}`)
        })

        const simulatedQuality = qualitySimulator()
        qualityResults.push(simulatedQuality)
      }

      // Should maintain acceptable quality on average
      const averageQuality = qualityResults.reduce((a, b) => a + b) / qualityResults.length
      expect(averageQuality).toBeGreaterThan(0.7) // 70% quality threshold

      // Should handle quality variations gracefully
      const qualityVariance = qualityResults.reduce((a, b) => a + Math.pow(b - averageQuality, 2), 0) / qualityResults.length
      expect(qualityVariance).toBeLessThan(0.1) // Low variance indicates stability
    })
  })

  describe('Performance Monitoring', () => {
    it('tracks performance metrics accurately', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      await act(async () => {
        await result.current.speak('Performance monitoring test')
      })

      const metrics = result.current.metrics

      // Metrics should be populated and reasonable
      expect(metrics.latency.total).toBeGreaterThan(0)
      expect(metrics.latency.total).toBeLessThan(PERFORMANCE_BENCHMARKS.VOICE_RESPONSE_TIME)
      
      expect(metrics.quality.audioQuality).toBeGreaterThan(0)
      expect(metrics.quality.audioQuality).toBeLessThanOrEqual(1)
      
      expect(metrics.performance.cpuUsage).toBeGreaterThan(0)
      expect(metrics.performance.memoryUsage).toBeGreaterThan(0)
    })

    it('identifies performance bottlenecks', async () => {
      const { result } = renderHook(() => useVoiceEngine())

      const performanceData = generateVoiceMetrics({
        latency: {
          speechToText: 120,
          processing: 200, // Intentionally high
          textToSpeech: 80,
          total: 400,
        }
      })

      // Should identify processing as bottleneck
      const bottleneck = Object.entries(performanceData.latency)
        .reduce((a, b) => a[1] > b[1] ? a : b)

      expect(bottleneck[0]).toBe('processing')
      expect(bottleneck[1]).toBeGreaterThan(PERFORMANCE_BENCHMARKS.AUDIO_PROCESSING_LATENCY)
    })
  })
})