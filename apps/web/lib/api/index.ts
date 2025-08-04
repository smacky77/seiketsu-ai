// API Services Export
export { apiClient, ApiError } from './client';
export { API_CONFIG } from './config';

// Service exports
export { authService } from './services/auth.service';
export { voiceService, VoiceStream } from './services/voice.service';
export { propertyService } from './services/property.service';
export { leadsService } from './services/leads.service';
export { marketService } from './services/market.service';
export { 
  webSocketService, 
  WebSocketConnection,
  WEBSOCKET_CHANNELS,
  createVoiceConnection,
  createNotificationsConnection,
  createAnalyticsConnection,
  createLeadsConnection,
  createPropertiesConnection,
  createMarketConnection
} from './services/websocket.service';

// Type exports
export type { 
  User, 
  LoginRequest, 
  RegisterRequest, 
  AuthResponse 
} from './services/auth.service';

export type { 
  VoiceAgent, 
  Conversation, 
  ConversationTurn, 
  VoiceSynthesisRequest, 
  VoiceRecognitionRequest, 
  VoiceAnalytics 
} from './services/voice.service';

export type { 
  Property, 
  PriceChange, 
  MarketTrend, 
  PropertySearchParams, 
  PropertyAnalytics 
} from './services/property.service';

export type { 
  Lead, 
  Interaction, 
  LeadQualificationResult, 
  LeadAnalytics 
} from './services/leads.service';

export type { 
  MarketTrend as MarketTrendData, 
  MarketInsight, 
  MarketForecast, 
  CompetitorAnalysis, 
  MarketOpportunity 
} from './services/market.service';

export type { 
  WebSocketMessage, 
  WebSocketConfig 
} from './services/websocket.service';