import { useMutation, useQueryClient } from '@tanstack/react-query'

import type { ApiError } from '../../../types/api'
import type { Task, TaskCreateInput } from '../../../types/task'
import { createTask } from '../tasksApi'

export function useCreateTask() {
  const queryClient = useQueryClient()

  return useMutation<Task, ApiError, TaskCreateInput>({
    mutationFn: (input: TaskCreateInput) => createTask(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}
