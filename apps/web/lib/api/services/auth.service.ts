// Authentication Service
import { apiClient } from '../client';
import { API_CONFIG } from '../config';

// Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  company?: string;
  phone?: string;
}

export interface AuthResponse {
  user: User;
  tokens: {
    access: string;
    refresh: string;
  };
}

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  company?: string;
  phone?: string;
  role: string;
  tenantId: string;
  createdAt: string;
  updatedAt: string;
}

// Auth Service Class
class AuthService {
  private currentUser: User | null = null;

  // Login
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>(
      API_CONFIG.ENDPOINTS.AUTH.LOGIN,
      credentials
    );
    
    // Store tokens and user
    this.setAuth(response);
    
    return response;
  }

  // Register
  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>(
      API_CONFIG.ENDPOINTS.AUTH.REGISTER,
      data
    );
    
    // Store tokens and user
    this.setAuth(response);
    
    return response;
  }

  // Logout
  async logout(): Promise<void> {
    try {
      await apiClient.post(API_CONFIG.ENDPOINTS.AUTH.LOGOUT);
    } finally {
      this.clearAuth();
    }
  }

  // Refresh token
  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>(
      API_CONFIG.ENDPOINTS.AUTH.REFRESH,
      { refreshToken }
    );
    
    // Update tokens
    this.setAuth(response);
    
    return response;
  }

  // Verify token
  async verifyToken(): Promise<User> {
    const response = await apiClient.get<{ user: User }>(
      API_CONFIG.ENDPOINTS.AUTH.VERIFY
    );
    
    this.currentUser = response.user;
    return response.user;
  }

  // Get current user
  getCurrentUser(): User | null {
    return this.currentUser;
  }

  // Check if authenticated
  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }

  // Get access token
  getAccessToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  }

  // Get refresh token
  getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('refresh_token');
  }

  // Set authentication data
  private setAuth(authResponse: AuthResponse): void {
    if (typeof window === 'undefined') return;
    
    // Store tokens
    localStorage.setItem('access_token', authResponse.tokens.access);
    localStorage.setItem('refresh_token', authResponse.tokens.refresh);
    
    // Store user
    this.currentUser = authResponse.user;
    localStorage.setItem('user', JSON.stringify(authResponse.user));
    
    // Update API client token
    apiClient.setToken(authResponse.tokens.access);
  }

  // Clear authentication data
  private clearAuth(): void {
    if (typeof window === 'undefined') return;
    
    // Clear tokens
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    
    // Clear user
    this.currentUser = null;
    
    // Clear API client token
    apiClient.clearToken();
  }

  // Initialize auth from storage
  initializeAuth(): void {
    if (typeof window === 'undefined') return;
    
    const token = this.getAccessToken();
    const userStr = localStorage.getItem('user');
    
    if (token && userStr) {
      try {
        this.currentUser = JSON.parse(userStr);
        apiClient.setToken(token);
      } catch (error) {
        this.clearAuth();
      }
    }
  }
}

// Create singleton instance
export const authService = new AuthService();

// Initialize on import
if (typeof window !== 'undefined') {
  authService.initializeAuth();
}

export default authService;