import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { decodeJwt } from '../../../lib/jwt'
import type { ApiError } from '../../../types/api'
import { login, type AuthCredentials, type LoginResponse } from '../authApi'
import { useAuth } from '../authContext'

export function useLogin() {
  const { login: setAuth } = useAuth()
  const navigate = useNavigate()

  return useMutation<LoginResponse, ApiError, AuthCredentials>({
    mutationFn: (payload: AuthCredentials) => login(payload),
    onSuccess: (data) => {
      const claims = decodeJwt(data.access_token)
      setAuth(data.access_token, { id: claims.sub, email: claims.email, is_active: true })
      navigate('/dashboard', { replace: true })
    },
  })
}
