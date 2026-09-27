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
    if (error.response?.status === 401 && window.location.pathname !== '/login') {
      window.location.href = '/login'
    }

    const apiError: ApiError = {
      status: error.response?.status ?? 0,
      message: extractMessage(error),
      details: error.response?.data,
    }

    return Promise.reject(apiError)
  },
)

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
