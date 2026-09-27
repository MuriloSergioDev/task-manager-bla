import type { Task } from '../../../types/task'
import { useAuth } from '../../auth/useAuth'

/** Mirrors backend TaskAuthorizationService so the UI only offers actions
 *  the API will accept; the API remains the actual enforcement point. */
export function useTaskPermissions(task: Task) {
  const { user } = useAuth()

  const isOwner = user?.id === task.owner_id
  const isAssignee = user?.id === task.assigned_to
  const isInvolved = isOwner || isAssignee

  const canEdit = isInvolved
  const canComplete = isInvolved && task.status !== 'COMPLETED'
  const canDelete = isOwner

  return { isOwner, isAssignee, isInvolved, canEdit, canComplete, canDelete }
}
