import { useQuery, useQueryClient } from '@tanstack/react-query'
import { createContext, type ReactNode, useContext } from 'react'

import type { User } from '../../types/user'
import { getCurrentUser, logout as logoutRequest } from './authApi'

const CURRENT_USER_QUERY_KEY = ['auth', 'me'] as const

interface AuthContextValue {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (user: User) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()

  // The access token is an httpOnly cookie the browser controls, so the app
  // has no client-readable signal of "am I logged in" -- session state has
  // to be asked of the API, once, on load.
  const { data: user, isLoading } = useQuery({
    queryKey: CURRENT_USER_QUERY_KEY,
    queryFn: getCurrentUser,
    retry: false,
    staleTime: Infinity,
  })

  const login = (nextUser: User) => {
    queryClient.setQueryData(CURRENT_USER_QUERY_KEY, nextUser)
  }

  const logout = () => {
    queryClient.setQueryData(CURRENT_USER_QUERY_KEY, null)
    void logoutRequest()
  }

  return (
    <AuthContext.Provider
      value={{
        user: user ?? null,
        isAuthenticated: user != null,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
