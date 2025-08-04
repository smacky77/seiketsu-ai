// Audio utility functions for voice AI

export interface AudioConstraints {
  sampleRate?: number
  channelCount?: number
  echoCancellation?: boolean
  noiseSuppression?: boolean
  autoGainControl?: boolean
  latency?: number
}

export interface AudioAnalysis {
  volume: number
  frequency: number
  noise: number
  quality: number
  clipping: boolean
}

// Convert audio buffer to different formats
export async function convertAudioBuffer(
  audioBuffer: AudioBuffer,
  targetFormat: 'wav' | 'mp3' | 'pcm' = 'wav'
): Promise<Blob> {
  const sampleRate = audioBuffer.sampleRate
  const channels = audioBuffer.numberOfChannels
  const length = audioBuffer.length
  
  if (targetFormat === 'pcm') {
    // Convert to PCM (raw audio data)
    const pcmData = new Float32Array(length * channels)
    
    for (let channel = 0; channel < channels; channel++) {
      const channelData = audioBuffer.getChannelData(channel)
      for (let i = 0; i < length; i++) {
        pcmData[i * channels + channel] = channelData[i]
      }
    }
    
    return new Blob([pcmData], { type: 'audio/pcm' })
  }
  
  if (targetFormat === 'wav') {
    // Convert to WAV format
    const wavBuffer = audioBufferToWav(audioBuffer)
    return new Blob([wavBuffer], { type: 'audio/wav' })
  }
  
  // MP3 conversion would require additional libraries
  throw new Error('MP3 conversion not implemented')
}

// Convert AudioBuffer to WAV format
function audioBufferToWav(audioBuffer: AudioBuffer): ArrayBuffer {
  const numberOfChannels = audioBuffer.numberOfChannels
  const sampleRate = audioBuffer.sampleRate
  const format = 1 // PCM
  const bitDepth = 16
  
  const bytesPerSample = bitDepth / 8
  const blockAlign = numberOfChannels * bytesPerSample
  const byteRate = sampleRate * blockAlign
  const dataSize = audioBuffer.length * blockAlign
  const bufferSize = 44 + dataSize
  
  const buffer = new ArrayBuffer(bufferSize)
  const view = new DataView(buffer)
  
  // WAV header
  const writeString = (offset: number, string: string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i))
    }
  }
  
  writeString(0, 'RIFF')
  view.setUint32(4, bufferSize - 8, true)
  writeString(8, 'WAVE')
  writeString(12, 'fmt ')
  view.setUint32(16, 16, true) // Subchunk1Size
  view.setUint16(20, format, true)
  view.setUint16(22, numberOfChannels, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, byteRate, true)
  view.setUint16(32, blockAlign, true)
  view.setUint16(34, bitDepth, true)
  writeString(36, 'data')
  view.setUint32(40, dataSize, true)
  
  // Convert float samples to 16-bit PCM
  let offset = 44
  for (let i = 0; i < audioBuffer.length; i++) {
    for (let channel = 0; channel < numberOfChannels; channel++) {
      const sample = audioBuffer.getChannelData(channel)[i]
      const intSample = Math.max(-1, Math.min(1, sample))
      view.setInt16(offset, intSample * 0x7FFF, true)
      offset += 2
    }
  }
  
  return buffer
}

// Analyze audio quality and characteristics
export function analyzeAudio(audioData: Float32Array, sampleRate: number): AudioAnalysis {
  const length = audioData.length
  
  // Calculate RMS volume
  let sum = 0
  for (let i = 0; i < length; i++) {
    sum += audioData[i] * audioData[i]
  }
  const volume = Math.sqrt(sum / length)
  
  // Simple frequency analysis (dominant frequency)
  const fftSize = Math.min(2048, Math.pow(2, Math.floor(Math.log2(length))))
  const frequencies = simpleFFT(audioData.slice(0, fftSize))
  
  let maxMagnitude = 0
  let dominantFrequency = 0
  
  for (let i = 1; i < frequencies.length / 2; i++) {
    const magnitude = Math.sqrt(frequencies[i * 2] ** 2 + frequencies[i * 2 + 1] ** 2)
    if (magnitude > maxMagnitude) {
      maxMagnitude = magnitude
      dominantFrequency = (i * sampleRate) / fftSize
    }
  }
  
  // Detect noise (high-frequency content analysis)
  const highFreqEnergy = frequencies
    .slice(Math.floor(frequencies.length * 0.6))
    .reduce((sum, val, i) => sum + (i % 2 === 0 ? val * val : 0), 0)
  
  const totalEnergy = frequencies.reduce((sum, val, i) => sum + (i % 2 === 0 ? val * val : 0), 0)
  const noise = totalEnergy > 0 ? highFreqEnergy / totalEnergy : 0
  
  // Detect clipping
  const clippingThreshold = 0.95
  const clippingSamples = audioData.filter(sample => Math.abs(sample) > clippingThreshold).length
  const clipping = clippingSamples / length > 0.01 // More than 1% clipped
  
  // Calculate overall quality score
  let quality = 1.0
  quality -= Math.min(0.5, noise) // Reduce for noise
  quality -= clipping ? 0.3 : 0 // Reduce for clipping
  quality -= volume < 0.01 ? 0.4 : 0 // Reduce for very low volume
  quality -= volume > 0.8 ? 0.2 : 0 // Reduce for very high volume
  quality = Math.max(0, Math.min(1, quality))
  
  return {
    volume,
    frequency: dominantFrequency,
    noise,
    quality,
    clipping
  }
}

// Simple FFT implementation for frequency analysis
function simpleFFT(audioData: Float32Array): Float32Array {
  const N = audioData.length
  if (N <= 1) return audioData
  
  // Ensure N is power of 2
  const n = Math.pow(2, Math.floor(Math.log2(N)))
  const data = new Float32Array(n * 2) // Complex numbers (real, imaginary)
  
  // Copy input data (real part only)
  for (let i = 0; i < n; i++) {
    data[i * 2] = audioData[i] || 0
    data[i * 2 + 1] = 0
  }
  
  // Bit-reverse
  for (let i = 0; i < n; i++) {
    const j = reverseBits(i, Math.log2(n))
    if (j > i) {
      // Swap
      const tempReal = data[i * 2]
      const tempImag = data[i * 2 + 1]
      data[i * 2] = data[j * 2]
      data[i * 2 + 1] = data[j * 2 + 1]
      data[j * 2] = tempReal
      data[j * 2 + 1] = tempImag
    }
  }
  
  // FFT
  for (let size = 2; size <= n; size *= 2) {
    const halfSize = size / 2
    const step = (2 * Math.PI) / size
    
    for (let i = 0; i < n; i += size) {
      for (let j = 0; j < halfSize; j++) {
        const u = i + j
        const v = i + j + halfSize
        
        const angle = -j * step
        const cos = Math.cos(angle)
        const sin = Math.sin(angle)
        
        const tReal = data[v * 2] * cos - data[v * 2 + 1] * sin
        const tImag = data[v * 2] * sin + data[v * 2 + 1] * cos
        
        data[v * 2] = data[u * 2] - tReal
        data[v * 2 + 1] = data[u * 2 + 1] - tImag
        data[u * 2] += tReal
        data[u * 2 + 1] += tImag
      }
    }
  }
  
  return data
}

function reverseBits(num: number, bits: number): number {
  let result = 0
  for (let i = 0; i < bits; i++) {
    result = (result << 1) | (num & 1)
    num >>= 1
  }
  return result
}

// Create optimal audio constraints for different use cases
export function getOptimalConstraints(useCase: 'conversation' | 'recording' | 'streaming'): AudioConstraints {
  const baseConstraints: AudioConstraints = {
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true
  }
  
  switch (useCase) {
    case 'conversation':
      return {
        ...baseConstraints,
        sampleRate: 16000, // Sufficient for speech
        channelCount: 1,
        latency: 0.02 // 20ms for real-time conversation
      }
    
    case 'recording':
      return {
        ...baseConstraints,
        sampleRate: 44100, // High quality recording
        channelCount: 2,
        latency: 0.1 // 100ms acceptable for recording
      }
    
    case 'streaming':
      return {
        ...baseConstraints,
        sampleRate: 22050, // Balance quality and bandwidth
        channelCount: 1,
        latency: 0.05 // 50ms for streaming
      }
    
    default:
      return baseConstraints
  }
}

// Audio level normalization
export function normalizeAudioLevel(audioData: Float32Array, targetLevel = 0.5): Float32Array {
  // Calculate current RMS level
  let sum = 0
  for (let i = 0; i < audioData.length; i++) {
    sum += audioData[i] * audioData[i]
  }
  const currentLevel = Math.sqrt(sum / audioData.length)
  
  if (currentLevel === 0) return audioData
  
  // Calculate gain needed
  const gain = targetLevel / currentLevel
  
  // Apply gain with soft limiting to prevent clipping
  const normalized = new Float32Array(audioData.length)
  for (let i = 0; i < audioData.length; i++) {
    let sample = audioData[i] * gain
    
    // Soft limiting
    if (Math.abs(sample) > 0.95) {
      sample = Math.sign(sample) * (0.95 - Math.exp(-Math.abs(sample) + 0.95))
    }
    
    normalized[i] = sample
  }
  
  return normalized
}

// Detect silence in audio data
export function detectSilence(
  audioData: Float32Array, 
  threshold = 0.01, 
  minDuration = 500,
  sampleRate = 44100
): Array<{ start: number; end: number; duration: number }> {
  const silencePeriods: Array<{ start: number; end: number; duration: number }> = []
  const minSamples = (minDuration / 1000) * sampleRate
  
  let silenceStart = -1
  
  for (let i = 0; i < audioData.length; i++) {
    const isSilent = Math.abs(audioData[i]) < threshold
    
    if (isSilent && silenceStart === -1) {
      silenceStart = i
    } else if (!isSilent && silenceStart !== -1) {
      const silenceLength = i - silenceStart
      
      if (silenceLength >= minSamples) {
        const startTime = (silenceStart / sampleRate) * 1000
        const endTime = (i / sampleRate) * 1000
        
        silencePeriods.push({
          start: startTime,
          end: endTime,
          duration: endTime - startTime
        })
      }
      
      silenceStart = -1
    }
  }
  
  // Handle silence at the end
  if (silenceStart !== -1) {
    const silenceLength = audioData.length - silenceStart
    if (silenceLength >= minSamples) {
      const startTime = (silenceStart / sampleRate) * 1000
      const endTime = (audioData.length / sampleRate) * 1000
      
      silencePeriods.push({
        start: startTime,
        end: endTime,
        duration: endTime - startTime
      })
    }
  }
  
  return silencePeriods
}

// Audio crossfading utility
export function crossfade(
  audio1: Float32Array,
  audio2: Float32Array,
  fadeLength = 1000,
  sampleRate = 44100
): Float32Array {
  const fadeSamples = Math.floor((fadeLength / 1000) * sampleRate)
  const totalLength = audio1.length + audio2.length - fadeSamples
  const result = new Float32Array(totalLength)
  
  // Copy first audio up to fade point
  const fadeStart = audio1.length - fadeSamples
  for (let i = 0; i < fadeStart; i++) {
    result[i] = audio1[i]
  }
  
  // Crossfade section
  for (let i = 0; i < fadeSamples; i++) {
    const fadeRatio = i / fadeSamples
    const sample1 = audio1[fadeStart + i] * (1 - fadeRatio)
    const sample2 = audio2[i] * fadeRatio
    result[fadeStart + i] = sample1 + sample2
  }
  
  // Copy remaining second audio
  for (let i = fadeSamples; i < audio2.length; i++) {
    result[fadeStart + i] = audio2[i]
  }
  
  return result
}

// Check browser audio capabilities
export function checkAudioCapabilities(): {
  getUserMedia: boolean
  audioContext: boolean
  webRTC: boolean
  mediaRecorder: boolean
  supportedFormats: string[]
} {
  const capabilities = {
    getUserMedia: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
    audioContext: !!(window.AudioContext || (window as any).webkitAudioContext),
    webRTC: !!(window.RTCPeerConnection || (window as any).webkitRTCPeerConnection),
    mediaRecorder: !!(window.MediaRecorder),
    supportedFormats: [] as string[]
  }
  
  // Check supported formats
  if (capabilities.mediaRecorder) {
    const formats = ['audio/webm', 'audio/mp4', 'audio/wav', 'audio/ogg']
    formats.forEach(format => {
      if (MediaRecorder.isTypeSupported(format)) {
        capabilities.supportedFormats.push(format)
      }
    })
  }
  
  return capabilities
}

// Audio latency measurement
export async function measureAudioLatency(audioContext: AudioContext): Promise<number> {
  return new Promise((resolve) => {
    const startTime = audioContext.currentTime
    const oscillator = audioContext.createOscillator()
    const analyser = audioContext.createAnalyser()
    
    oscillator.connect(analyser)
    oscillator.frequency.value = 1000 // 1kHz test tone
    oscillator.start()
    
    const checkLatency = () => {
      const dataArray = new Uint8Array(analyser.frequencyBinCount)
      analyser.getByteFrequencyData(dataArray)
      
      // Find peak frequency
      let maxValue = 0
      for (let i = 0; i < dataArray.length; i++) {
        if (dataArray[i] > maxValue) {
          maxValue = dataArray[i]
        }
      }
      
      if (maxValue > 100) { // Threshold for detection
        const latency = (audioContext.currentTime - startTime) * 1000 // Convert to ms
        oscillator.stop()
        resolve(latency)
      } else {
        requestAnimationFrame(checkLatency)
      }
    }
    
    requestAnimationFrame(checkLatency)
  })
}