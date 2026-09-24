import { apiClient } from '../../lib/apiClient'
import type { User } from '../../types/user'

export interface AuthCredentials {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export async function login(payload: AuthCredentials): Promise<LoginResponse> {
  const { data } = await apiClient.post<LoginResponse>('/api/v1/auth/login', payload)
  return data
}

export async function register(payload: AuthCredentials): Promise<User> {
  const { data } = await apiClient.post<User>('/api/v1/auth/register', payload)
  return data
}
