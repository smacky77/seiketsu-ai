import type { 
  VoiceWebRTCConnection, 
  VoiceAIEventListener, 
  VoiceAIError,
  VoiceAIEvent 
} from '../types'

interface WebRTCConfig {
  iceServers: RTCIceServer[]
  constraints: {
    audio: MediaTrackConstraints
    video?: false
  }
  codecs: {
    audio: string[] // e.g., ['opus', 'PCMU', 'PCMA']
  }
  rtcConfig?: RTCConfiguration
}

export class VoiceWebRTC extends EventTarget {
  private connection: VoiceWebRTCConnection = {
    connectionState: 'new',
    iceConnectionState: 'new',
    signalingState: 'stable'
  }
  
  private config: WebRTCConfig
  private listeners: VoiceAIEventListener[] = []
  private isInitialized = false
  private localAudioSender: RTCRtpSender | null = null
  
  constructor(config: Partial<WebRTCConfig> = {}) {
    super()
    this.config = {
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
      ],
      constraints: {
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 44100,
          channelCount: 1
        }
      },
      codecs: {
        audio: ['opus', 'PCMU', 'PCMA']
      },
      ...config
    }
  }

  async initialize(): Promise<void> {
    try {
      // Create peer connection
      this.connection.peerConnection = new RTCPeerConnection({
        iceServers: this.config.iceServers,
        ...this.config.rtcConfig
      })

      this.setupPeerConnectionHandlers()
      this.isInitialized = true
      
      console.log('VoiceWebRTC initialized')
    } catch (error) {
      throw new Error(`Failed to initialize WebRTC: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  private setupPeerConnectionHandlers(): void {
    const pc = this.connection.peerConnection!
    
    // Connection state monitoring
    pc.onconnectionstatechange = () => {
      this.connection.connectionState = pc.connectionState
      this.emitEvent({
        type: 'connection_state_changed',
        data: { state: pc.connectionState }
      })
      
      console.log('WebRTC connection state:', pc.connectionState)
    }
    
    pc.oniceconnectionstatechange = () => {
      this.connection.iceConnectionState = pc.iceConnectionState
      console.log('ICE connection state:', pc.iceConnectionState)
      
      if (pc.iceConnectionState === 'failed') {
        this.handleConnectionError('ICE connection failed')
      }
    }
    
    pc.onsignalingstatechange = () => {
      this.connection.signalingState = pc.signalingState
      console.log('Signaling state:', pc.signalingState)
    }
    
    // ICE candidate handling
    pc.onicecandidate = (event) => {
      if (event.candidate) {
        this.emitEvent({
          type: 'ice_candidate',
          data: { candidate: event.candidate }
        })
      }
    }
    
    // Remote stream handling
    pc.ontrack = (event) => {
      console.log('Received remote track:', event.track.kind)
      if (event.track.kind === 'audio') {
        this.connection.remoteStream = event.streams[0]
        this.emitEvent({
          type: 'remote_stream',
          data: { stream: event.streams[0] }
        })
      }
    }
    
    // Data channel handling
    pc.ondatachannel = (event) => {
      const channel = event.channel
      this.setupDataChannelHandlers(channel)
    }
  }

  private setupDataChannelHandlers(channel: RTCDataChannel): void {
    channel.onopen = () => {
      console.log('Data channel opened:', channel.label)
      this.emitEvent({
        type: 'data_channel_open',
        data: { channel: channel.label }
      })
    }
    
    channel.onclose = () => {
      console.log('Data channel closed:', channel.label)
    }
    
    channel.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.emitEvent({
          type: 'data_channel_message',
          data: { message: data, channel: channel.label }
        })
      } catch (error) {
        console.warn('Invalid JSON received on data channel:', event.data)
      }
    }
    
    channel.onerror = (error) => {
      console.error('Data channel error:', error)
      this.handleConnectionError(`Data channel error: ${error}`)
    }
  }

  async startCall(): Promise<void> {
    if (!this.isInitialized || !this.connection.peerConnection) {
      throw new Error('WebRTC not initialized')
    }

    try {
      // Get local media stream
      this.connection.localStream = await navigator.mediaDevices.getUserMedia(this.config.constraints)
      
      // Add local stream to peer connection
      this.connection.localStream.getTracks().forEach(track => {
        if (track.kind === 'audio') {
          this.localAudioSender = this.connection.peerConnection!.addTrack(
            track, 
            this.connection.localStream!
          )
        }
      })

      // Create data channel for control messages
      this.connection.dataChannel = this.connection.peerConnection.createDataChannel('control', {
        ordered: true
      })
      this.setupDataChannelHandlers(this.connection.dataChannel)
      
      // Set up preferred codecs
      await this.configureAudioCodecs()
      
      console.log('Call started with local stream')
      this.emitEvent({
        type: 'call_started',
        data: { localStream: this.connection.localStream }
      })
      
    } catch (error) {
      this.handleConnectionError(`Failed to start call: ${error instanceof Error ? error.message : 'Unknown error'}`)
      throw error
    }
  }

  async createOffer(): Promise<RTCSessionDescriptionInit> {
    if (!this.connection.peerConnection) {
      throw new Error('Peer connection not available')
    }

    try {
      const offer = await this.connection.peerConnection.createOffer({
        offerToReceiveAudio: true,
        offerToReceiveVideo: false
      })
      
      await this.connection.peerConnection.setLocalDescription(offer)
      console.log('Created and set local offer')
      
      return offer
    } catch (error) {
      throw new Error(`Failed to create offer: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  async createAnswer(): Promise<RTCSessionDescriptionInit> {
    if (!this.connection.peerConnection) {
      throw new Error('Peer connection not available')
    }

    try {
      const answer = await this.connection.peerConnection.createAnswer()
      await this.connection.peerConnection.setLocalDescription(answer)
      console.log('Created and set local answer')
      
      return answer
    } catch (error) {
      throw new Error(`Failed to create answer: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  async setRemoteDescription(description: RTCSessionDescriptionInit): Promise<void> {
    if (!this.connection.peerConnection) {
      throw new Error('Peer connection not available')
    }

    try {
      await this.connection.peerConnection.setRemoteDescription(description)
      console.log('Set remote description:', description.type)
    } catch (error) {
      throw new Error(`Failed to set remote description: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  async addIceCandidate(candidate: RTCIceCandidateInit): Promise<void> {
    if (!this.connection.peerConnection) {
      throw new Error('Peer connection not available')
    }

    try {
      await this.connection.peerConnection.addIceCandidate(candidate)
      console.log('Added ICE candidate')
    } catch (error) {
      console.warn('Failed to add ICE candidate:', error)
    }
  }

  private async configureAudioCodecs(): Promise<void> {
    if (!this.connection.peerConnection) return

    const transceivers = this.connection.peerConnection.getTransceivers()
    const audioTransceiver = transceivers.find(t => t.receiver.track?.kind === 'audio')
    
    if (audioTransceiver) {
      // Set preferred codecs
      const capabilities = RTCRtpSender.getCapabilities('audio')
      if (capabilities) {
        const preferredCodecs = capabilities.codecs.filter(codec => 
          this.config.codecs.audio.some(preferred => 
            codec.mimeType.toLowerCase().includes(preferred.toLowerCase())
          )
        )
        
        if (preferredCodecs.length > 0) {
          await audioTransceiver.setCodecPreferences(preferredCodecs)
          console.log('Set preferred audio codecs:', preferredCodecs.map(c => c.mimeType))
        }
      }
    }
  }

  // Audio control methods
  setMicrophoneMuted(muted: boolean): void {
    if (this.localAudioSender && this.localAudioSender.track) {
      this.localAudioSender.track.enabled = !muted
      this.emitEvent({
        type: 'microphone_muted',
        data: { muted }
      })
    }
  }

  isMicrophoneMuted(): boolean {
    return this.localAudioSender?.track ? !this.localAudioSender.track.enabled : true
  }

  adjustMicrophoneVolume(volume: number): void {
    // This would typically be handled by audio processing pipeline
    // For now, just emit event for external handling
    this.emitEvent({
      type: 'microphone_volume_changed',
      data: { volume: Math.max(0, Math.min(1, volume)) }
    })
  }

  // Data channel messaging
  sendMessage(message: any, channel = 'control'): void {
    if (this.connection.dataChannel && this.connection.dataChannel.readyState === 'open') {
      try {
        this.connection.dataChannel.send(JSON.stringify(message))
      } catch (error) {
        console.error('Failed to send message:', error)
      }
    } else {
      console.warn('Data channel not available for sending message')
    }
  }

  // Connection quality monitoring
  async getConnectionStats(): Promise<RTCStatsReport | null> {
    if (!this.connection.peerConnection) return null

    try {
      return await this.connection.peerConnection.getStats()
    } catch (error) {
      console.error('Failed to get connection stats:', error)
      return null
    }
  }

  async getAudioStats(): Promise<any> {
    const stats = await this.getConnectionStats()
    if (!stats) return null

    const audioStats: any = {}
    
    stats.forEach((report) => {
      if (report.type === 'inbound-rtp' && report.kind === 'audio') {
        audioStats.inbound = {
          bytesReceived: report.bytesReceived,
          packetsReceived: report.packetsReceived,
          packetsLost: report.packetsLost,
          jitter: report.jitter,
          audioLevel: report.audioLevel
        }
      } else if (report.type === 'outbound-rtp' && report.kind === 'audio') {
        audioStats.outbound = {
          bytesSent: report.bytesSent,
          packetsSent: report.packetsSent,
          targetBitrate: report.targetBitrate
        }
      }
    })
    
    return audioStats
  }

  // Call management
  async endCall(): Promise<void> {
    // Stop local stream
    if (this.connection.localStream) {
      this.connection.localStream.getTracks().forEach(track => track.stop())
      this.connection.localStream = null
    }

    // Close data channel
    if (this.connection.dataChannel) {
      this.connection.dataChannel.close()
      this.connection.dataChannel = null
    }

    // Close peer connection
    if (this.connection.peerConnection) {
      this.connection.peerConnection.close()
      this.connection.peerConnection = null
    }

    this.localAudioSender = null
    
    console.log('Call ended')
    this.emitEvent({
      type: 'call_ended',
      data: {}
    })
  }

  private handleConnectionError(message: string): void {
    const error: VoiceAIError = {
      code: 'WEBRTC_ERROR',
      message,
      recoverable: true,
      timestamp: Date.now()
    }
    
    this.emitEvent({
      type: 'error',
      data: error
    })
  }

  // Event management
  addEventListener(listener: VoiceAIEventListener): void {
    this.listeners.push(listener)
  }

  removeEventListener(listener: VoiceAIEventListener): void {
    const index = this.listeners.indexOf(listener)
    if (index > -1) {
      this.listeners.splice(index, 1)
    }
  }

  private emitEvent(event: VoiceAIEvent): void {
    this.listeners.forEach(listener => {
      try {
        listener(event)
      } catch (error) {
        console.error('Error in WebRTC event listener:', error)
      }
    })
  }

  // Cleanup
  destroy(): void {
    this.endCall()
    this.listeners = []
    console.log('VoiceWebRTC destroyed')
  }

  // Getters
  get connectionState(): RTCPeerConnectionState {
    return this.connection.connectionState
  }

  get iceConnectionState(): RTCIceConnectionState {
    return this.connection.iceConnectionState
  }

  get signalingState(): RTCSignalingState {
    return this.connection.signalingState
  }

  get localStream(): MediaStream | null {
    return this.connection.localStream || null
  }

  get remoteStream(): MediaStream | null {
    return this.connection.remoteStream || null
  }

  get isConnected(): boolean {
    return this.connection.connectionState === 'connected'
  }
}