import { AxiosError, AxiosHeaders, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import { describe, expect, it } from 'vitest'

import { shouldRedirectToLogin, toApiError } from './apiClient'

describe('shouldRedirectToLogin', () => {
  it('redirects when a protected request is rejected mid-session', () => {
    expect(shouldRedirectToLogin(401, '/api/v1/tasks', '/dashboard')).toBe(true)
  })

  // Regression: the /auth/me session probe returns 401 for any signed-out
  // visitor, and redirecting on it bounced them off /register.
  it('does not redirect when the session probe finds no session', () => {
    expect(shouldRedirectToLogin(401, '/api/v1/auth/me', '/register')).toBe(false)
  })

  it('does not redirect when a login attempt fails', () => {
    expect(shouldRedirectToLogin(401, '/api/v1/auth/login', '/login')).toBe(false)
  })

  it('does not redirect when already on the login page', () => {
    expect(shouldRedirectToLogin(401, '/api/v1/tasks', '/login')).toBe(false)
  })

  it('does not redirect for errors other than 401', () => {
    expect(shouldRedirectToLogin(403, '/api/v1/tasks/1', '/dashboard')).toBe(false)
    expect(shouldRedirectToLogin(500, '/api/v1/tasks', '/dashboard')).toBe(false)
    expect(shouldRedirectToLogin(undefined, '/api/v1/tasks', '/dashboard')).toBe(false)
  })
})

function axiosError(status: number | null, data?: unknown, message = 'Request failed'): AxiosError {
  const config = { headers: new AxiosHeaders() } as InternalAxiosRequestConfig
  const response =
    status === null
      ? undefined
      : ({ status, data, statusText: '', headers: {}, config } as AxiosResponse)
  return new AxiosError(message, undefined, config, undefined, response)
}

describe('toApiError', () => {
  it('uses the API\'s "detail" message', () => {
    expect(toApiError(axiosError(401, { detail: 'Invalid email or password' }))).toEqual({
      status: 401,
      message: 'Invalid email or password',
      details: { detail: 'Invalid email or password' },
    })
  })

  it('uses the first message of a validation error list', () => {
    const data = { detail: [{ msg: 'Title is required', loc: ['body', 'title'] }] }
    expect(toApiError(axiosError(422, data)).message).toBe('Title is required')
  })

  it('reports a network failure as status 0 with axios\'s message', () => {
    expect(toApiError(axiosError(null, undefined, 'Network Error'))).toMatchObject({
      status: 0,
      message: 'Network Error',
    })
  })

  it('falls back to a generic message when there is nothing better', () => {
    expect(toApiError(axiosError(500, '<html>oops</html>', '')).message).toBe('An unexpected error occurred')
  })
})
