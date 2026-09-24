import { useQuery } from '@tanstack/react-query'

import type { ApiError } from '../../../types/api'
import type { User } from '../../../types/user'
import { fetchUsers } from '../usersApi'

export function useUsers() {
  return useQuery<User[], ApiError>({
    queryKey: ['users'],
    queryFn: fetchUsers,
    staleTime: 5 * 60_000,
  })
}
