import { useMutation, useQueryClient } from '@tanstack/react-query'

import type { ApiError } from '../../../types/api'
import type { Task } from '../../../types/task'
import { assignTask } from '../tasksApi'

interface AssignTaskVariables {
  taskId: string
  assignedTo: string | null
}

export function useAssignTask() {
  const queryClient = useQueryClient()

  return useMutation<Task, ApiError, AssignTaskVariables>({
    mutationFn: ({ taskId, assignedTo }) => assignTask(taskId, assignedTo),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}
