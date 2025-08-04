// Enterprise API Client with multi-tenant support and enhanced features
import { API_CONFIG, getHeaders, buildUrl, replacePathParams } from './config';
import type { ApiResponse, PaginatedResponse } from '@/types';

// Enhanced error handling for enterprise
export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data?: any
  ) {
    super(`API Error: ${status} ${statusText}`);
    this.name = 'ApiError';
  }

  get isNetworkError(): boolean {
    return this.status === 0
  }

  get isClientError(): boolean {
    return this.status >= 400 && this.status < 500
  }

  get isServerError(): boolean {
    return this.status >= 500
  }

  get isAuthError(): boolean {
    return this.status === 401 || this.status === 403
  }

  get isValidationError(): boolean {
    return this.status === 422
  }

  get isRateLimited(): boolean {
    return this.status === 429
  }
}

// Request interceptor type
type RequestInterceptor = (config: RequestInit) => RequestInit | Promise<RequestInit>;
type ResponseInterceptor = (response: Response) => Response | Promise<Response>;

// Enterprise API Client Class
export class ApiClient {
  private token?: string;
  private organizationId?: string;
  private requestInterceptors: RequestInterceptor[] = [];
  private responseInterceptors: ResponseInterceptor[] = [];
  private retryAttempts: number = 3;
  private retryDelay: number = 1000;

  constructor(token?: string, organizationId?: string) {
    this.token = token;
    this.organizationId = organizationId;
  }

  // Set authentication token
  setToken(token: string) {
    this.token = token;
  }

  // Clear authentication token
  clearToken() {
    this.token = undefined;
  }

  // Set organization context for multi-tenant support
  setOrganization(organizationId: string) {
    this.organizationId = organizationId;
  }

  // Clear organization context
  clearOrganization() {
    this.organizationId = undefined;
  }

  // Generate unique request ID for tracing
  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Set retry configuration
  setRetryConfig(attempts: number, delay: number) {
    this.retryAttempts = attempts;
    this.retryDelay = delay;
  }

  // Add request interceptor
  addRequestInterceptor(interceptor: RequestInterceptor) {
    this.requestInterceptors.push(interceptor);
  }

  // Add response interceptor
  addResponseInterceptor(interceptor: ResponseInterceptor) {
    this.responseInterceptors.push(interceptor);
  }

  // Apply request interceptors
  private async applyRequestInterceptors(config: RequestInit): Promise<RequestInit> {
    let finalConfig = config;
    
    for (const interceptor of this.requestInterceptors) {
      finalConfig = await interceptor(finalConfig);
    }
    
    return finalConfig;
  }

  // Apply response interceptors
  private async applyResponseInterceptors(response: Response): Promise<Response> {
    let finalResponse = response;
    
    for (const interceptor of this.responseInterceptors) {
      finalResponse = await interceptor(finalResponse);
    }
    
    return finalResponse;
  }

  // Base request method with retry logic and enterprise features
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    pathParams?: Record<string, string>,
    queryParams?: Record<string, any>,
    retryCount: number = 0
  ): Promise<ApiResponse<T>> {
    try {
      // Replace path parameters
      const finalEndpoint = pathParams ? replacePathParams(endpoint, pathParams) : endpoint;
      
      // Build URL with query parameters
      const url = buildUrl(finalEndpoint, queryParams);
      
      // Prepare request configuration with enterprise headers
      let config: RequestInit = {
        ...options,
        headers: {
          ...getHeaders(this.token),
          ...(this.organizationId && { 'X-Organization-ID': this.organizationId }),
          'X-Request-ID': this.generateRequestId(),
          ...options.headers,
        },
      };
      
      // Apply request interceptors
      config = await this.applyRequestInterceptors(config);
      
      // Make request
      const response = await fetch(url, config);
      
      // Apply response interceptors
      const finalResponse = await this.applyResponseInterceptors(response);
      
      // Handle errors with retry logic
      if (!finalResponse.ok) {
        const errorData = await finalResponse.json().catch(() => null);
        const error = new ApiError(finalResponse.status, finalResponse.statusText, errorData);
        
        // Retry logic for specific error types
        if (this.shouldRetry(error, retryCount)) {
          await this.delay(this.retryDelay * Math.pow(2, retryCount)); // Exponential backoff
          return this.request(endpoint, options, pathParams, queryParams, retryCount + 1);
        }
        
        throw error;
      }
      
      // Parse response
      const data = await finalResponse.json();
      return {
        success: true,
        data: data.data || data,
        message: data.message,
        ...data
      } as ApiResponse<T>;
      
    } catch (error) {
      // Re-throw API errors
      if (error instanceof ApiError) {
        // Retry network errors
        if (error.isNetworkError && retryCount < this.retryAttempts) {
          await this.delay(this.retryDelay * Math.pow(2, retryCount));
          return this.request(endpoint, options, pathParams, queryParams, retryCount + 1);
        }
        throw error;
      }
      
      // Handle network errors
      if (error instanceof Error) {
        const networkError = new ApiError(0, 'Network Error', { message: error.message });
        if (retryCount < this.retryAttempts) {
          await this.delay(this.retryDelay * Math.pow(2, retryCount));
          return this.request(endpoint, options, pathParams, queryParams, retryCount + 1);
        }
        throw networkError;
      }
      
      // Unknown error
      throw new ApiError(0, 'Unknown Error', error);
    }
  }

  // Utility methods
  private shouldRetry(error: ApiError, retryCount: number): boolean {
    if (retryCount >= this.retryAttempts) return false;
    return error.isNetworkError || error.status >= 500 || error.isRateLimited;
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // HTTP Methods with enhanced typing
  async get<T>(
    endpoint: string,
    queryParams?: Record<string, any>,
    pathParams?: Record<string, string>
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' }, pathParams, queryParams);
  }

  async post<T>(
    endpoint: string,
    data?: any,
    pathParams?: Record<string, string>,
    queryParams?: Record<string, any>
  ): Promise<ApiResponse<T>> {
    return this.request<T>(
      endpoint,
      {
        method: 'POST',
        body: data ? JSON.stringify(data) : undefined,
      },
      pathParams,
      queryParams
    );
  }

  async put<T>(
    endpoint: string,
    data?: any,
    pathParams?: Record<string, string>,
    queryParams?: Record<string, any>
  ): Promise<ApiResponse<T>> {
    return this.request<T>(
      endpoint,
      {
        method: 'PUT',
        body: data ? JSON.stringify(data) : undefined,
      },
      pathParams,
      queryParams
    );
  }

  async patch<T>(
    endpoint: string,
    data?: any,
    pathParams?: Record<string, string>,
    queryParams?: Record<string, any>
  ): Promise<ApiResponse<T>> {
    return this.request<T>(
      endpoint,
      {
        method: 'PATCH',
        body: data ? JSON.stringify(data) : undefined,
      },
      pathParams,
      queryParams
    );
  }

  async delete<T>(
    endpoint: string,
    pathParams?: Record<string, string>,
    queryParams?: Record<string, any>
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' }, pathParams, queryParams);
  }

  // Paginated requests for enterprise data tables
  async getPaginated<T>(
    endpoint: string,
    params?: {
      page?: number
      limit?: number
      sort?: string
      order?: 'asc' | 'desc'
      [key: string]: any
    }
  ): Promise<PaginatedResponse<T>> {
    const response = await this.get<T[]>(endpoint, params);
    return response as unknown as PaginatedResponse<T>;
  }

  // File upload with progress tracking
  async upload<T>(
    endpoint: string,
    file: File,
    additionalData?: Record<string, any>,
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, String(value));
      });
    }

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const progress = (event.loaded / event.total) * 100;
          onProgress(Math.round(progress));
        }
      });
      
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve({
              success: true,
              data: response.data || response,
              message: response.message,
              ...response
            });
          } catch (error) {
            reject(new ApiError(xhr.status, 'Invalid JSON response'));
          }
        } else {
          try {
            const errorData = JSON.parse(xhr.responseText);
            reject(new ApiError(xhr.status, xhr.statusText, errorData));
          } catch {
            reject(new ApiError(xhr.status, xhr.statusText));
          }
        }
      });
      
      xhr.addEventListener('error', () => {
        reject(new ApiError(0, 'Network error during upload'));
      });
      
      const url = buildUrl(endpoint);
      xhr.open('POST', url);
      
      // Set headers
      const headers = getHeaders(this.token);
      Object.entries(headers).forEach(([key, value]) => {
        if (key !== 'Content-Type') { // Let browser set Content-Type for FormData
          xhr.setRequestHeader(key, value);
        }
      });
      
      if (this.organizationId) {
        xhr.setRequestHeader('X-Organization-ID', this.organizationId);
      }
      
      xhr.setRequestHeader('X-Request-ID', this.generateRequestId());
      xhr.send(formData);
    });
  }

  // Batch requests for efficiency
  async batch<T>(requests: Array<{
    endpoint: string
    method?: string
    data?: any
    pathParams?: Record<string, string>
    queryParams?: Record<string, any>
  }>): Promise<ApiResponse<T[]>> {
    return this.post<T[]>('/api/batch', { requests });
  }

  // Health check endpoint
  async healthCheck(): Promise<ApiResponse<{ status: string; timestamp: string }>> {
    return this.get('/api/health');
  }

  // WebSocket connection helper
  createWebSocket(endpoint: string): WebSocket {
    const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = typeof window !== 'undefined' ? window.location.host : 'localhost:3000';
    const wsUrl = `${protocol}//${host}/ws${endpoint}`;
    
    const ws = new WebSocket(wsUrl);
    
    // Add auth and organization context to connection
    ws.addEventListener('open', () => {
      if (this.token || this.organizationId) {
        ws.send(JSON.stringify({
          type: 'auth',
          token: this.token,
          organizationId: this.organizationId
        }));
      }
    });
    
    return ws;
  }
}

// Create singleton instance
export const apiClient = new ApiClient();

// Export for use in services
export default apiClient;

// Enterprise API utilities
export const createAuthenticatedClient = (token: string, organizationId?: string) => {
  return new ApiClient(token, organizationId);
};

export const createOrganizationClient = (organizationId: string) => {
  const client = new ApiClient();
  client.setOrganization(organizationId);
  return client;
};