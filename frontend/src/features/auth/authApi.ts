import { apiClient } from '../../lib/apiClient'
import type { User } from '../../types/user'

export interface AuthCredentials {
  email: string
  password: string
}

export async function login(payload: AuthCredentials): Promise<User> {
  const { data } = await apiClient.post<User>('/api/v1/auth/login', payload)
  return data
}

export async function register(payload: AuthCredentials): Promise<User> {
  const { data } = await apiClient.post<User>('/api/v1/auth/register', payload)
  return data
}

export async function logout(): Promise<void> {
  await apiClient.post('/api/v1/auth/logout')
}

export async function getCurrentUser(): Promise<User> {
  const { data } = await apiClient.get<User>('/api/v1/auth/me')
  return data
}
