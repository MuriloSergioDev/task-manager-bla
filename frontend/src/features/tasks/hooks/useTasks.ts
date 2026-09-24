import { useQuery } from '@tanstack/react-query'

import type { ApiError } from '../../../types/api'
import type { TaskFilterValues, TaskListResponse } from '../../../types/task'
import { toQueryParams } from '../taskFilterState'
import { fetchTasks } from '../tasksApi'

export function useTasks(filters: TaskFilterValues) {
  const params = toQueryParams(filters)

  return useQuery<TaskListResponse, ApiError>({
    queryKey: ['tasks', params],
    queryFn: () => fetchTasks(params),
  })
}
