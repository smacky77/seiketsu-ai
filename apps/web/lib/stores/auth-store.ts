import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, Organization, Permission } from '@/types'

interface AuthState {
  user: User | null
  organization: Organization | null
  permissions: Permission[]
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

interface AuthActions {
  login: (user: User, organization: Organization) => void
  logout: () => void
  updateUser: (user: Partial<User>) => void
  updateOrganization: (organization: Partial<Organization>) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  hasPermission: (permission: Permission) => boolean
  hasAnyPermission: (permissions: Permission[]) => boolean
}

type AuthStore = AuthState & AuthActions

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      organization: null,
      permissions: [],
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      login: (user, organization) => {
        set({
          user,
          organization,
          permissions: user.permissions,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        })
      },

      logout: () => {
        set({
          user: null,
          organization: null,
          permissions: [],
          isAuthenticated: false,
          isLoading: false,
          error: null,
        })
      },

      updateUser: (userData) => {
        const { user } = get()
        if (user) {
          const updatedUser = { ...user, ...userData }
          set({
            user: updatedUser,
            permissions: updatedUser.permissions,
          })
        }
      },

      updateOrganization: (orgData) => {
        const { organization } = get()
        if (organization) {
          set({
            organization: { ...organization, ...orgData },
          })
        }
      },

      setLoading: (loading) => {
        set({ isLoading: loading })
      },

      setError: (error) => {
        set({ error, isLoading: false })
      },

      hasPermission: (permission) => {
        const { permissions } = get()
        return permissions.includes(permission)
      },

      hasAnyPermission: (perms) => {
        const { permissions } = get()
        return perms.some(permission => permissions.includes(permission))
      },
    }),
    {
      name: 'seiketsu-auth',
      partialize: (state) => ({
        user: state.user,
        organization: state.organization,
        permissions: state.permissions,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)