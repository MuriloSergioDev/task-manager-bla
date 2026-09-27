import { createContext } from 'react'

import type { User } from '../../types/user'

export interface AuthContextValue {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (user: User) => void
  logout: () => void
}

// Kept apart from AuthProvider.tsx so that file exports only a component
// (React Fast Refresh requirement); consumers use the useAuth hook.
export const AuthContext = createContext<AuthContextValue | undefined>(undefined)
