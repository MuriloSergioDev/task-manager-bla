import { StatusBadge } from '../../../components/ui/Badge'
import { Button } from '../../../components/ui/Button'
import type { Task } from '../../../types/task'
import { useAuth } from '../../auth/authContext'
import { useAssignTask } from '../hooks/useAssignTask'
import { useCompleteTask } from '../hooks/useCompleteTask'
import { useDeleteTask } from '../hooks/useDeleteTask'
import { useUsers } from '../hooks/useUsers'
import { AssigneeSelect } from './AssigneeSelect'

interface TaskRowProps {
  task: Task
  onEdit: () => void
}

export function TaskRow({ task, onEdit }: TaskRowProps) {
  const { user } = useAuth()
  const { data: users } = useUsers()
  const completeTask = useCompleteTask()
  const deleteTask = useDeleteTask()
  const assignTask = useAssignTask()

  const isOwner = user?.id === task.owner_id
  const isAssignee = user?.id === task.assigned_to
  const canComplete = (isOwner || isAssignee) && task.status !== 'COMPLETED'
  const assigneeEmail = users?.find((candidate) => candidate.id === task.assigned_to)?.email

  return (
    <tr className="border-b border-gray-100">
      <td className="px-4 py-3">
        <p className="font-medium text-gray-900">{task.title}</p>
        {task.description && <p className="text-sm text-gray-500">{task.description}</p>}
      </td>
      <td className="px-4 py-3">
        <StatusBadge status={task.status} />
      </td>
      <td className="px-4 py-3 text-sm text-gray-600">{task.due_date ?? '—'}</td>
      <td className="px-4 py-3 text-sm text-gray-600">
        {isOwner ? (
          <div className="w-40">
            <AssigneeSelect
              label=""
              value={task.assigned_to ?? ''}
              onChange={(assignedTo) =>
                assignTask.mutate({ taskId: task.id, assignedTo: assignedTo || null })
              }
            />
          </div>
        ) : (
          assigneeEmail ?? 'Unassigned'
        )}
      </td>
      <td className="px-4 py-3">
        <div className="flex justify-end gap-2">
          {canComplete && (
            <Button
              variant="secondary"
              onClick={() => completeTask.mutate(task.id)}
              disabled={completeTask.isPending}
            >
              Complete
            </Button>
          )}
          {isOwner && (
            <>
              <Button variant="secondary" onClick={onEdit}>
                Edit
              </Button>
              <Button
                variant="danger"
                onClick={() => {
                  if (window.confirm(`Delete "${task.title}"?`)) {
                    deleteTask.mutate(task.id)
                  }
                }}
                disabled={deleteTask.isPending}
              >
                Delete
              </Button>
            </>
          )}
        </div>
      </td>
    </tr>
  )
}
