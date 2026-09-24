import { apiClient } from '../../lib/apiClient'
import type { User } from '../../types/user'

interface UserListResponse {
  items: User[]
}

export async function fetchUsers(): Promise<User[]> {
  const { data } = await apiClient.get<UserListResponse>('/api/v1/users')
  return data.items
}
