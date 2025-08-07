"use client"

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/stores/auth-store'
import { apiClient } from '@/lib/api/client'
import type { User, Organization } from '@/types'

interface AuthContextType {
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  register: (userData: RegisterData) => Promise<void>
  refreshToken: () => Promise<void>
  resetPassword: (email: string) => Promise<void>
  verifyEmail: (token: string) => Promise<void>
}

interface RegisterData {
  email: string
  password: string
  firstName: string
  lastName: string
  organizationName?: string
  phoneNumber?: string
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()
  const { 
    user, 
    organization, 
    login: setAuthData, 
    logout: clearAuthData,
    setLoading,
    setError 
  } = useAuthStore()

  // Initialize auth state on mount
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const token = localStorage.getItem('seiketsu_auth_token')
        if (token) {
          apiClient.setToken(token)
          await refreshToken()
        }
      } catch (error) {
        console.error('Failed to initialize auth:', error)
        clearAuthData()
      } finally {
        setIsLoading(false)
      }
    }

    initializeAuth()
  }, [])

  // Set organization context when it changes
  useEffect(() => {
    if (organization) {
      apiClient.setOrganization(organization.id)
    }
  }, [organization])

  const login = async (email: string, password: string) => {
    try {
      setLoading(true)
      setError(null)

      const response = await apiClient.post<{
        user: User
        organization: Organization
        token: string
        refreshToken: string
      }>('/api/auth/login', { email, password })

      if (response.success && response.data) {
        const { user, organization, token, refreshToken } = response.data
        
        // Store tokens
        localStorage.setItem('seiketsu_auth_token', token)
        localStorage.setItem('seiketsu_refresh_token', refreshToken)
        
        // Set API client token
        apiClient.setToken(token)
        apiClient.setOrganization(organization.id)
        
        // Update auth store
        setAuthData(user, organization)
        
        // Redirect to dashboard
        router.push(`/org/${organization.slug}/dashboard`)
      } else {
        throw new Error(response.message || 'Login failed')
      }
    } catch (error: any) {
      setError(error.message || 'Login failed')
      throw error
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    try {
      setLoading(true)
      
      // Call logout endpoint to invalidate server-side session
      await apiClient.post('/api/auth/logout').catch(() => {
        // Ignore errors - we're logging out anyway
      })
      
      // Clear local storage
      localStorage.removeItem('seiketsu_auth_token')
      localStorage.removeItem('seiketsu_refresh_token')
      
      // Clear API client
      apiClient.clearToken()
      apiClient.clearOrganization()
      
      // Clear auth store
      clearAuthData()
      
      // Redirect to login
      router.push('/login')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      setLoading(false)
    }
  }

  const register = async (userData: RegisterData) => {
    try {
      setLoading(true)
      setError(null)

      const response = await apiClient.post<{
        user: User
        organization: Organization
        token: string
        refreshToken: string
      }>('/api/auth/register', userData)

      if (response.success && response.data) {
        const { user, organization, token, refreshToken } = response.data
        
        // Store tokens
        localStorage.setItem('seiketsu_auth_token', token)
        localStorage.setItem('seiketsu_refresh_token', refreshToken)
        
        // Set API client token
        apiClient.setToken(token)
        apiClient.setOrganization(organization.id)
        
        // Update auth store
        setAuthData(user, organization)
        
        // Redirect to onboarding
        router.push(`/org/${organization.slug}/onboarding`)
      } else {
        throw new Error(response.message || 'Registration failed')
      }
    } catch (error: any) {
      setError(error.message || 'Registration failed')
      throw error
    } finally {
      setLoading(false)
    }
  }

  const refreshToken = async () => {
    try {
      const refreshToken = localStorage.getItem('seiketsu_refresh_token')
      if (!refreshToken) {
        throw new Error('No refresh token available')
      }

      const response = await apiClient.post<{
        user: User
        organization: Organization
        token: string
        refreshToken: string
      }>('/api/auth/refresh', { refreshToken })

      if (response.success && response.data) {
        const { user, organization, token, refreshToken: newRefreshToken } = response.data
        
        // Update tokens
        localStorage.setItem('seiketsu_auth_token', token)
        localStorage.setItem('seiketsu_refresh_token', newRefreshToken)
        
        // Update API client
        apiClient.setToken(token)
        apiClient.setOrganization(organization.id)
        
        // Update auth store
        setAuthData(user, organization)
      } else {
        throw new Error('Token refresh failed')
      }
    } catch (error) {
      console.error('Token refresh failed:', error)
      clearAuthData()
      throw error
    }
  }

  const resetPassword = async (email: string) => {
    try {
      setLoading(true)
      setError(null)

      const response = await apiClient.post('/api/auth/reset-password', { email })
      
      if (!response.success) {
        throw new Error(response.message || 'Password reset failed')
      }
    } catch (error: any) {
      setError(error.message || 'Password reset failed')
      throw error
    } finally {
      setLoading(false)
    }
  }

  const verifyEmail = async (token: string) => {
    try {
      setLoading(true)
      setError(null)

      const response = await apiClient.post('/api/auth/verify-email', { token })
      
      if (!response.success) {
        throw new Error(response.message || 'Email verification failed')
      }
      
      // Refresh user data after verification
      if (user) {
        await refreshToken()
      }
    } catch (error: any) {
      setError(error.message || 'Email verification failed')
      throw error
    } finally {
      setLoading(false)
    }
  }

  const value: AuthContextType = {
    isLoading,
    login,
    logout,
    register,
    refreshToken,
    resetPassword,
    verifyEmail,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Higher-order component for protected routes
export function withAuth<P extends object>(Component: React.ComponentType<P>) {
  return function AuthenticatedComponent(props: P) {
    const { user, isAuthenticated } = useAuthStore()
    const { isLoading } = useAuth()
    const router = useRouter()

    useEffect(() => {
      if (!isLoading && !isAuthenticated) {
        router.push('/login')
      }
    }, [isLoading, isAuthenticated, router])

    if (isLoading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      )
    }

    if (!isAuthenticated || !user) {
      return null
    }

    return <Component {...props} />
  }
}

// Hook for role-based access control
export function usePermissions() {
  const { user, hasPermission, hasAnyPermission } = useAuthStore()
  
  return {
    user,
    hasPermission,
    hasAnyPermission,
    isAdmin: user?.role === 'admin',
    isManager: user?.role === 'manager',
    isAgent: user?.role === 'agent',
    canViewLeads: hasPermission('leads.view'),
    canEditLeads: hasPermission('leads.edit'),
    canViewAgents: hasPermission('agents.view'),
    canManageAgents: hasAnyPermission(['agents.create', 'agents.edit', 'agents.delete']),
    canViewAnalytics: hasPermission('analytics.view'),
    canManageSettings: hasPermission('settings.edit'),
    canManageUsers: hasPermission('users.manage'),
  }
}