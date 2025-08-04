// API Configuration for Backend Integration
export const API_CONFIG = {
  // Base URLs
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
  
  // API Endpoints
  ENDPOINTS: {
    // Authentication
    AUTH: {
      LOGIN: '/api/auth/login',
      REGISTER: '/api/auth/register',
      LOGOUT: '/api/auth/logout',
      REFRESH: '/api/auth/refresh',
      VERIFY: '/api/auth/verify'
    },
    
    // Voice Agent
    VOICE: {
      AGENTS: '/api/voice/agents',
      CONVERSATIONS: '/api/voice/conversations',
      TRAINING: '/api/voice/training',
      ANALYTICS: '/api/voice/analytics',
      SYNTHESIS: '/api/voice/synthesis',
      RECOGNITION: '/api/voice/recognition'
    },
    
    // Real Estate
    PROPERTIES: {
      LIST: '/api/properties',
      SEARCH: '/api/properties/search',
      DETAILS: '/api/properties/:id',
      MLS_SYNC: '/api/properties/mls/sync',
      ANALYTICS: '/api/properties/analytics'
    },
    
    // Leads
    LEADS: {
      LIST: '/api/leads',
      CREATE: '/api/leads',
      DETAILS: '/api/leads/:id',
      QUALIFY: '/api/leads/:id/qualify',
      ASSIGN: '/api/leads/:id/assign',
      ANALYTICS: '/api/leads/analytics'
    },
    
    // Market Intelligence
    MARKET: {
      TRENDS: '/api/market/trends',
      INSIGHTS: '/api/market/insights',
      FORECASTS: '/api/market/forecasts',
      COMPETITORS: '/api/market/competitors'
    },
    
    // Communication
    COMMUNICATION: {
      CALLS: '/api/communication/calls',
      MESSAGES: '/api/communication/messages',
      EMAILS: '/api/communication/emails',
      APPOINTMENTS: '/api/communication/appointments'
    },
    
    // Tenant Management
    TENANT: {
      PROFILE: '/api/tenant/profile',
      SETTINGS: '/api/tenant/settings',
      USERS: '/api/tenant/users',
      BILLING: '/api/tenant/billing'
    }
  },
  
  // Request Configuration
  REQUEST: {
    TIMEOUT: 30000,
    RETRY_ATTEMPTS: 3,
    RETRY_DELAY: 1000
  },
  
  // WebSocket Configuration
  WEBSOCKET: {
    RECONNECT_INTERVAL: 5000,
    MAX_RECONNECT_ATTEMPTS: 10,
    PING_INTERVAL: 30000
  }
};

// API Headers
export const getHeaders = (token?: string): HeadersInit => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
};

// API URL Builder
export const buildUrl = (endpoint: string, params?: Record<string, any>): string => {
  const url = `${API_CONFIG.BASE_URL}${endpoint}`;
  
  if (params && Object.keys(params).length > 0) {
    const queryString = new URLSearchParams(params).toString();
    return `${url}?${queryString}`;
  }
  
  return url;
};

// Replace path parameters
export const replacePathParams = (path: string, params: Record<string, string>): string => {
  let result = path;
  
  Object.entries(params).forEach(([key, value]) => {
    result = result.replace(`:${key}`, value);
  });
  
  return result;
};