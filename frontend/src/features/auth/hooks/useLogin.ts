import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import type { ApiError } from '../../../types/api'
import type { User } from '../../../types/user'
import { login, type AuthCredentials } from '../authApi'
import { useAuth } from '../useAuth'

export function useLogin() {
  const { login: setAuth } = useAuth()
  const navigate = useNavigate()

  return useMutation<User, ApiError, AuthCredentials>({
    mutationFn: (payload: AuthCredentials) => login(payload),
    onSuccess: (user) => {
      setAuth(user)
      navigate('/dashboard', { replace: true })
    },
  })
}
