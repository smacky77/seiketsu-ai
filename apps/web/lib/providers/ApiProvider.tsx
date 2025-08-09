'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { authService, webSocketService, User } from '@/lib/api';

// API Context
interface ApiContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => Promise<void>;
  refreshAuth: () => Promise<void>;
}

const ApiContext = createContext<ApiContextType | undefined>(undefined);

// API Provider Component
export function ApiProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize authentication
  useEffect(() => {
    const initAuth = async () => {
      try {
        // Check if user is already authenticated
        const currentUser = authService.getCurrentUser();
        if (currentUser) {
          setUser(currentUser);
        } else {
          // Try to verify token
          const token = authService.getAccessToken();
          if (token) {
            try {
              const verifiedUser = await authService.verifyToken();
              setUser(verifiedUser);
            } catch (error) {
              // Token invalid, clear auth
              authService.logout();
            }
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  // Login function
  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await authService.login({ email, password });
      setUser(response.user);
    } finally {
      setIsLoading(false);
    }
  };

  // Register function
  const register = async (data: any) => {
    setIsLoading(true);
    try {
      const response = await authService.register(data);
      setUser(response.user);
    } finally {
      setIsLoading(false);
    }
  };

  // Logout function
  const logout = async () => {
    setIsLoading(true);
    try {
      await authService.logout();
      setUser(null);
      // Disconnect all WebSocket connections
      webSocketService.disconnectAll();
    } finally {
      setIsLoading(false);
    }
  };

  // Refresh authentication
  const refreshAuth = async () => {
    try {
      const refreshToken = authService.getRefreshToken();
      if (refreshToken) {
        const response = await authService.refreshToken(refreshToken);
        setUser(response.user);
      }
    } catch (error) {
      // Refresh failed, logout
      await logout();
    }
  };

  const value: ApiContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    refreshAuth,
  };

  return (
    <ApiContext.Provider value={value}>
      {children}
    </ApiContext.Provider>
  );
}

// Hook to use API context
export function useApi() {
  const context = useContext(ApiContext);
  if (context === undefined) {
    throw new Error('useApi must be used within an ApiProvider');
  }
  return context;
}

// Hook for authenticated requests
export function useAuthenticatedApi() {
  const { isAuthenticated, refreshAuth } = useApi();
  
  useEffect(() => {
    // Set up token refresh interceptor
    const refreshInterceptor = async (response: Response) => {
      if (response.status === 401 && isAuthenticated) {
        try {
          await refreshAuth();
          // Retry the original request
          return fetch(response.url, {
            method: response.type,
            headers: response.headers,
          });
        } catch (error) {
          // Refresh failed, redirect to login
          window.location.href = '/login';
        }
      }
      return response;
    };

    // Note: This would need to be implemented in the API client
    // apiClient.addResponseInterceptor(refreshInterceptor);
  }, [isAuthenticated, refreshAuth]);

  return { isAuthenticated };
}