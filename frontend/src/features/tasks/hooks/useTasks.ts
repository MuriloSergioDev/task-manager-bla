import { keepPreviousData, useQuery } from '@tanstack/react-query'

import type { ApiError } from '../../../types/api'
import type { TaskFilterValues, TaskListResponse } from '../../../types/task'
import { toQueryParams } from '../taskFilterState'
import { fetchTasks } from '../tasksApi'

export function useTasks(filters: TaskFilterValues, page: number) {
  const params = toQueryParams(filters, page)

  return useQuery<TaskListResponse, ApiError>({
    queryKey: ['tasks', params],
    queryFn: () => fetchTasks(params),
    // Keep showing the current page while the next one loads, instead of
    // flashing a spinner on every page change.
    placeholderData: keepPreviousData,
  })
}
