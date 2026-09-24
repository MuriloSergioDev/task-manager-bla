import { useMutation, useQueryClient } from '@tanstack/react-query'

import type { ApiError } from '../../../types/api'
import type { Task } from '../../../types/task'
import { completeTask } from '../tasksApi'

export function useCompleteTask() {
  const queryClient = useQueryClient()

  return useMutation<Task, ApiError, string>({
    mutationFn: (taskId: string) => completeTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}
