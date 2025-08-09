// Voice Service with ElevenLabs Integration
import { apiClient } from '../client';
import { API_CONFIG } from '../config';

// Types
export interface VoiceAgent {
  id: string;
  name: string;
  voiceId: string;
  personality: string;
  skills: string[];
  language: string;
  isActive: boolean;
  tenantId: string;
  createdAt: string;
  updatedAt: string;
}

export interface Conversation {
  id: string;
  agentId: string;
  leadId?: string;
  transcript: ConversationTurn[];
  summary: string;
  sentiment: string;
  duration: number;
  outcome: string;
  createdAt: string;
  updatedAt: string;
}

export interface ConversationTurn {
  id: string;
  speaker: 'agent' | 'lead';
  text: string;
  audioUrl?: string;
  timestamp: string;
  sentiment?: string;
  intent?: string;
}

export interface VoiceSynthesisRequest {
  text: string;
  voiceId: string;
  settings?: {
    stability?: number;
    similarityBoost?: number;
    style?: number;
    speakerBoost?: boolean;
  };
}

export interface VoiceRecognitionRequest {
  audioData: Blob | ArrayBuffer;
  language?: string;
}

export interface VoiceAnalytics {
  totalConversations: number;
  averageDuration: number;
  successRate: number;
  sentimentDistribution: {
    positive: number;
    neutral: number;
    negative: number;
  };
  topIntents: Array<{
    intent: string;
    count: number;
  }>;
}

// Voice Service Class
class VoiceService {
  // Get all voice agents
  async getAgents(): Promise<VoiceAgent[]> {
    const response = await apiClient.get<VoiceAgent[]>(API_CONFIG.ENDPOINTS.VOICE.AGENTS);
    return response.data;
  }

  // Get voice agent by ID
  async getAgent(id: string): Promise<VoiceAgent> {
    const response = await apiClient.get<VoiceAgent>(
      API_CONFIG.ENDPOINTS.VOICE.AGENTS,
      undefined,
      { id }
    );
    return response.data;
  }

  // Create voice agent
  async createAgent(data: Partial<VoiceAgent>): Promise<VoiceAgent> {
    const response = await apiClient.post<VoiceAgent>(API_CONFIG.ENDPOINTS.VOICE.AGENTS, data);
    return response.data;
  }

  // Update voice agent
  async updateAgent(id: string, data: Partial<VoiceAgent>): Promise<VoiceAgent> {
    const response = await apiClient.put<VoiceAgent>(
      API_CONFIG.ENDPOINTS.VOICE.AGENTS,
      data,
      { id }
    );
    return response.data;
  }

  // Delete voice agent
  async deleteAgent(id: string): Promise<void> {
    await apiClient.delete(API_CONFIG.ENDPOINTS.VOICE.AGENTS, { id });
  }

  // Get conversations
  async getConversations(params?: {
    agentId?: string;
    leadId?: string;
    startDate?: string;
    endDate?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ conversations: Conversation[]; total: number }> {
    const response = await apiClient.get<{ conversations: Conversation[]; total: number }>(
      API_CONFIG.ENDPOINTS.VOICE.CONVERSATIONS,
      params
    );
    return response.data;
  }

  // Get conversation by ID
  async getConversation(id: string): Promise<Conversation> {
    const response = await apiClient.get<Conversation>(
      API_CONFIG.ENDPOINTS.VOICE.CONVERSATIONS,
      undefined,
      { id }
    );
    return response.data;
  }

  // Start conversation
  async startConversation(data: {
    agentId: string;
    leadId?: string;
    context?: any;
  }): Promise<Conversation> {
    const response = await apiClient.post<Conversation>(
      API_CONFIG.ENDPOINTS.VOICE.CONVERSATIONS,
      data
    );
    return response.data;
  }

  // End conversation
  async endConversation(id: string, summary?: string): Promise<Conversation> {
    const response = await apiClient.patch<Conversation>(
      API_CONFIG.ENDPOINTS.VOICE.CONVERSATIONS,
      { summary },
      { id }
    );
    return response.data;
  }

  // Synthesize speech with ElevenLabs
  async synthesizeSpeech(request: VoiceSynthesisRequest): Promise<{
    audioUrl: string;
    audioData?: ArrayBuffer;
  }> {
    const response = await apiClient.post<{
      audioUrl: string;
      audioData?: ArrayBuffer;
    }>(API_CONFIG.ENDPOINTS.VOICE.SYNTHESIS, request);
    return response.data;
  }

  // Recognize speech
  async recognizeSpeech(request: VoiceRecognitionRequest): Promise<{
    text: string;
    confidence: number;
    language: string;
  }> {
    const formData = new FormData();
    
    if (request.audioData instanceof Blob) {
      formData.append('audio', request.audioData);
    } else {
      formData.append('audio', new Blob([request.audioData]));
    }
    
    if (request.language) {
      formData.append('language', request.language);
    }

    // Override headers for multipart/form-data
    const response = await apiClient.post<{
      text: string;
      confidence: number;
      language: string;
    }>(API_CONFIG.ENDPOINTS.VOICE.RECOGNITION, formData);
    return response.data;
  }

  // Train voice agent
  async trainAgent(agentId: string, trainingData: {
    conversations?: string[];
    documents?: string[];
    settings?: any;
  }): Promise<{ status: string; jobId: string }> {
    const response = await apiClient.post<{ status: string; jobId: string }>(
      API_CONFIG.ENDPOINTS.VOICE.TRAINING,
      trainingData,
      { agentId }
    );
    return response.data;
  }

  // Get training status
  async getTrainingStatus(jobId: string): Promise<{
    status: 'pending' | 'running' | 'completed' | 'failed';
    progress: number;
    error?: string;
  }> {
    const response = await apiClient.get<{
      status: 'pending' | 'running' | 'completed' | 'failed';
      progress: number;
      error?: string;
    }>(API_CONFIG.ENDPOINTS.VOICE.TRAINING, { jobId });
    return response.data;
  }

  // Get voice analytics
  async getAnalytics(params?: {
    agentId?: string;
    startDate?: string;
    endDate?: string;
  }): Promise<VoiceAnalytics> {
    const response = await apiClient.get<VoiceAnalytics>(
      API_CONFIG.ENDPOINTS.VOICE.ANALYTICS,
      params
    );
    return response.data;
  }

  // Real-time voice processing with WebSocket
  createVoiceStream(agentId: string): VoiceStream {
    return new VoiceStream(agentId);
  }
}

// Real-time Voice Stream Class
export class VoiceStream {
  private ws: WebSocket | null = null;
  private agentId: string;
  private eventHandlers: { [event: string]: Function[] } = {};

  constructor(agentId: string) {
    this.agentId = agentId;
  }

  // Connect to voice stream
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${API_CONFIG.WS_URL}/voice/${this.agentId}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          this.emit('connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          this.emit('message', data);
          
          // Handle specific message types
          if (data.type) {
            this.emit(data.type, data.payload);
          }
        };

        this.ws.onerror = (error) => {
          this.emit('error', error);
          reject(error);
        };

        this.ws.onclose = () => {
          this.emit('disconnected');
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  // Send audio data
  sendAudio(audioData: ArrayBuffer | Blob): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(audioData);
    }
  }

  // Send text message
  sendText(text: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'text',
        payload: { text }
      }));
    }
  }

  // Disconnect
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  // Event handling
  on(event: string, handler: Function): void {
    if (!this.eventHandlers[event]) {
      this.eventHandlers[event] = [];
    }
    this.eventHandlers[event].push(handler);
  }

  off(event: string, handler: Function): void {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event] = this.eventHandlers[event].filter(h => h !== handler);
    }
  }

  private emit(event: string, data?: any): void {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event].forEach(handler => handler(data));
    }
  }
}

// Create singleton instance
export const voiceService = new VoiceService();

export default voiceService;