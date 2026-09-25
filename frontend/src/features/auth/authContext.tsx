import { createContext, type ReactNode, useContext, useState } from 'react'

import { decodeJwt } from '../../lib/jwt'
import { clearToken, getToken, setToken as persistToken } from '../../lib/tokenStorage'
import type { User } from '../../types/user'

const USER_STORAGE_KEY = 'auth_user'

interface AuthContextValue {
  user: User | null
  isAuthenticated: boolean
  login: (token: string, user: User) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

function isTokenExpired(token: string): boolean {
  try {
    return decodeJwt(token).exp * 1000 <= Date.now()
  } catch {
    return true
  }
}

// Checked at load so a stale token from a previous session (or one that
// simply expired while the tab was closed) never renders the dashboard
// shell before the first API call fails and bounces back to /login -- an
// avoidable flash rather than a security issue (the API rejects it either
// way), but easy to just not have.
function readStoredUser(): User | null {
  const token = getToken()
  if (!token || isTokenExpired(token)) {
    clearToken()
    localStorage.removeItem(USER_STORAGE_KEY)
    return null
  }

  const stored = localStorage.getItem(USER_STORAGE_KEY)
  if (!stored) return null
  try {
    return JSON.parse(stored) as User
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(readStoredUser)

  const login = (token: string, nextUser: User) => {
    persistToken(token)
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(nextUser))
    setUser(nextUser)
  }

  const logout = () => {
    clearToken()
    localStorage.removeItem(USER_STORAGE_KEY)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: user !== null, login, logout }}>
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
