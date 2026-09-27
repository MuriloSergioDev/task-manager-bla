import { useQuery, useQueryClient } from '@tanstack/react-query'
import type { ReactNode } from 'react'

import type { User } from '../../types/user'
import { getCurrentUser, logout as logoutRequest } from './authApi'
import { AuthContext } from './authContext'

const CURRENT_USER_QUERY_KEY = ['auth', 'me'] as const

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
