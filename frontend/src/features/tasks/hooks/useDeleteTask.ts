import { useMutation, useQueryClient } from '@tanstack/react-query'

import type { ApiError } from '../../../types/api'
import { deleteTask } from '../tasksApi'

export function useDeleteTask() {
  const queryClient = useQueryClient()

  return useMutation<void, ApiError, string>({
    mutationFn: (taskId: string) => deleteTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}
