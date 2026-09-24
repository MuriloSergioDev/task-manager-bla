import { useMutation, useQueryClient } from '@tanstack/react-query'

import type { ApiError } from '../../../types/api'
import type { Task, TaskUpdateInput } from '../../../types/task'
import { updateTask } from '../tasksApi'

interface UpdateTaskVariables {
  taskId: string
  input: TaskUpdateInput
}

export function useUpdateTask() {
  const queryClient = useQueryClient()

  return useMutation<Task, ApiError, UpdateTaskVariables>({
    mutationFn: ({ taskId, input }) => updateTask(taskId, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}
