// WebSocket Service for Real-time Features
import { API_CONFIG } from '../config';
import { authService } from './auth.service';

// Types
export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: string;
}

export interface WebSocketConfig {
  url: string;
  protocols?: string[];
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  pingInterval?: number;
}

// WebSocket Manager Class
class WebSocketService {
  private connections: Map<string, WebSocketConnection> = new Map();
  private defaultConfig: WebSocketConfig;

  constructor() {
    this.defaultConfig = {
      url: API_CONFIG.WS_URL,
      reconnectInterval: API_CONFIG.WEBSOCKET.RECONNECT_INTERVAL,
      maxReconnectAttempts: API_CONFIG.WEBSOCKET.MAX_RECONNECT_ATTEMPTS,
      pingInterval: API_CONFIG.WEBSOCKET.PING_INTERVAL,
    };
  }

  // Create or get connection
  getConnection(
    channel: string,
    config?: Partial<WebSocketConfig>
  ): WebSocketConnection {
    if (!this.connections.has(channel)) {
      const finalConfig = { ...this.defaultConfig, ...config };
      const connection = new WebSocketConnection(channel, finalConfig);
      this.connections.set(channel, connection);
    }

    return this.connections.get(channel)!;
  }

  // Remove connection
  removeConnection(channel: string): void {
    const connection = this.connections.get(channel);
    if (connection) {
      connection.disconnect();
      this.connections.delete(channel);
    }
  }

  // Disconnect all connections
  disconnectAll(): void {
    this.connections.forEach((connection) => {
      connection.disconnect();
    });
    this.connections.clear();
  }

  // Get all active connections
  getActiveConnections(): string[] {
    return Array.from(this.connections.keys()).filter((channel) => {
      const connection = this.connections.get(channel);
      return connection && connection.isConnected();
    });
  }
}

// WebSocket Connection Class
export class WebSocketConnection {
  private ws: WebSocket | null = null;
  private channel: string;
  private config: WebSocketConfig;
  private eventHandlers: { [event: string]: Function[] } = {};
  private reconnectAttempts = 0;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private pingInterval: NodeJS.Timeout | null = null;
  private isReconnecting = false;

  constructor(channel: string, config: WebSocketConfig) {
    this.channel = channel;
    this.config = config;
  }

  // Connect to WebSocket
  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // Build WebSocket URL with authentication
        const token = authService.getAccessToken();
        const wsUrl = `${this.config.url}/${this.channel}${token ? `?token=${token}` : ''}`;

        this.ws = new WebSocket(wsUrl, this.config.protocols);

        this.ws.onopen = () => {
          this.reconnectAttempts = 0;
          this.isReconnecting = false;
          this.startPing();
          this.emit('connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.emit('message', message);
            
            // Handle specific message types
            if (message.type) {
              this.emit(message.type, message.payload);
            }
          } catch (error) {
            this.emit('error', new Error('Failed to parse message'));
          }
        };

        this.ws.onerror = (error) => {
          this.emit('error', error);
          if (!this.isReconnecting) {
            reject(error);
          }
        };

        this.ws.onclose = (event) => {
          this.stopPing();
          this.emit('disconnected', event);
          
          // Auto-reconnect if not manually closed
          if (event.code !== 1000 && this.shouldReconnect()) {
            this.scheduleReconnect();
          }
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  // Send message
  send(type: string, payload: any): void {
    if (this.isConnected()) {
      const message: WebSocketMessage = {
        type,
        payload,
        timestamp: new Date().toISOString(),
      };

      this.ws!.send(JSON.stringify(message));
    } else {
      this.emit('error', new Error('WebSocket is not connected'));
    }
  }

  // Send raw data (for binary data like audio)
  sendRaw(data: string | ArrayBuffer | Blob): void {
    if (this.isConnected()) {
      this.ws!.send(data);
    } else {
      this.emit('error', new Error('WebSocket is not connected'));
    }
  }

  // Disconnect
  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    this.stopPing();

    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
  }

  // Check if connected
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
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
      this.eventHandlers[event].forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`Error in WebSocket event handler for ${event}:`, error);
        }
      });
    }
  }

  // Check if should reconnect
  private shouldReconnect(): boolean {
    return (
      this.config.maxReconnectAttempts === undefined ||
      this.reconnectAttempts < this.config.maxReconnectAttempts
    );
  }

  // Schedule reconnection
  private scheduleReconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }

    this.isReconnecting = true;
    this.reconnectAttempts++;

    const delay = Math.min(
      (this.config.reconnectInterval || 5000) * Math.pow(2, this.reconnectAttempts - 1),
      30000
    );

    this.emit('reconnecting', { attempt: this.reconnectAttempts, delay });

    this.reconnectTimeout = setTimeout(() => {
      this.connect().catch((error) => {
        this.emit('reconnectFailed', { attempt: this.reconnectAttempts, error });
        
        if (this.shouldReconnect()) {
          this.scheduleReconnect();
        }
      });
    }, delay);
  }

  // Start ping to keep connection alive
  private startPing(): void {
    if (this.config.pingInterval && this.config.pingInterval > 0) {
      this.pingInterval = setInterval(() => {
        if (this.isConnected()) {
          this.send('ping', {});
        }
      }, this.config.pingInterval);
    }
  }

  // Stop ping
  private stopPing(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }
}

// Predefined channels for common use cases
export const WEBSOCKET_CHANNELS = {
  VOICE: 'voice',
  NOTIFICATIONS: 'notifications',
  ANALYTICS: 'analytics',
  LEADS: 'leads',
  PROPERTIES: 'properties',
  MARKET: 'market',
} as const;

// Create singleton instance
export const webSocketService = new WebSocketService();

// Helper functions for common operations
export const createVoiceConnection = () => 
  webSocketService.getConnection(WEBSOCKET_CHANNELS.VOICE);

export const createNotificationsConnection = () => 
  webSocketService.getConnection(WEBSOCKET_CHANNELS.NOTIFICATIONS);

export const createAnalyticsConnection = () => 
  webSocketService.getConnection(WEBSOCKET_CHANNELS.ANALYTICS);

export const createLeadsConnection = () => 
  webSocketService.getConnection(WEBSOCKET_CHANNELS.LEADS);

export const createPropertiesConnection = () => 
  webSocketService.getConnection(WEBSOCKET_CHANNELS.PROPERTIES);

export const createMarketConnection = () => 
  webSocketService.getConnection(WEBSOCKET_CHANNELS.MARKET);

export default webSocketService;