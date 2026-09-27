import axios, { type AxiosError } from 'axios'

import type { ApiError } from '../types/api'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
  // The access token lives in an httpOnly cookie set by the API, so the
  // browser -- not this client -- attaches it; it just needs to be sent.
  withCredentials: true,
})

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (shouldRedirectToLogin(error.response?.status, error.config?.url, window.location.pathname)) {
      window.location.href = '/login'
    }
    return Promise.reject(toApiError(error))
  },
)

/** A 401 from an auth endpoint just means "not signed in" (the /auth/me
 *  session probe, or a failed login) and the route guards handle it;
 *  redirecting on those would bounce a signed-out visitor off /register.
 *  Any other 401 means the session expired mid-use: sign in again. */
export function shouldRedirectToLogin(
  status: number | undefined,
  requestUrl: string | undefined,
  currentPath: string,
): boolean {
  const isAuthEndpoint = requestUrl?.startsWith('/api/v1/auth/') ?? false
  return status === 401 && !isAuthEndpoint && currentPath !== '/login'
}

/** Normalises any axios failure into the one error shape the UI renders. */
export function toApiError(error: AxiosError): ApiError {
  return {
    status: error.response?.status ?? 0,
    message: extractMessage(error),
    details: error.response?.data,
  }
}

function extractMessage(error: AxiosError): string {
  const data = error.response?.data as { detail?: unknown } | undefined

  if (typeof data?.detail === 'string') {
    return data.detail
  }

  if (Array.isArray(data?.detail)) {
    const first = data.detail[0] as { msg?: string } | undefined
    if (first?.msg) {
      return first.msg
    }
  }

  return error.message || 'An unexpected error occurred'
}
