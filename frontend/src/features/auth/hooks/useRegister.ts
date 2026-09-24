import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import type { ApiError } from '../../../types/api'
import type { User } from '../../../types/user'
import { register, type AuthCredentials } from '../authApi'

export function useRegister() {
  const navigate = useNavigate()

  return useMutation<User, ApiError, AuthCredentials>({
    mutationFn: (payload: AuthCredentials) => register(payload),
    onSuccess: () => {
      navigate('/login', { replace: true, state: { justRegistered: true } })
    },
  })
}
