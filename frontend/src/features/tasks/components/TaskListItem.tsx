import { UserRound } from 'lucide-react'

import { StatusBadge } from '../../../components/ui'
import type { Task } from '../../../types/task'
import type { User } from '../../../types/user'
import { daysOverdue, formatCompletedDate, getDueState } from '../dueDateStatus'
import { useAssignTask } from '../hooks/useAssignTask'
import { useTaskPermissions } from '../hooks/useTaskPermissions'
import { AssigneeSelect } from './AssigneeSelect'
import { DateStub } from './DateStub'
import { TaskRowActions } from './TaskRowActions'
import { TASK_ROW_GRID } from './taskListLayout'

interface TaskListItemProps {
  task: Task
  users: User[] | undefined
  onEdit: () => void
}

/** One task: the date stub, then title/status/assignee/actions as a grid on
 *  md+ that stacks on small screens -- one element for both layouts. */
export function TaskListItem({ task, users, onEdit }: TaskListItemProps) {
  const { isOwner, canEdit, canComplete, canDelete } = useTaskPermissions(task)
  const assignTask = useAssignTask()
  const isDone = task.status === 'COMPLETED'

  const assigneeEmail = users?.find((candidate) => candidate.id === task.assigned_to)?.email

  return (
    <li className="flex gap-4 px-4 py-4 sm:px-6">
      <DateStub task={task} />

      <div className={`grid min-w-0 flex-1 grid-cols-1 gap-3 md:items-center md:gap-5 ${TASK_ROW_GRID}`}>
        <div className="min-w-0">
          {/* Clamped so one very long title can't dominate the list; the
              full text is in the tooltip and the edit dialog. */}
          <p
            title={task.title}
            className={`line-clamp-2 leading-snug font-semibold break-words ${isDone ? 'text-muted' : 'text-ink'}`}
          >
            {task.title}
          </p>
          {task.description && (
            <p className="mt-0.5 line-clamp-2 max-w-prose text-sm break-words leading-relaxed text-muted">
              {task.description}
            </p>
          )}
        </div>

        <div className="flex flex-wrap items-baseline gap-x-2 md:flex-col md:gap-0.5">
          <StatusBadge status={task.status} />
          <StatusDetail task={task} />
        </div>

        <div className="min-w-0 text-sm">
          {isOwner ? (
            <AssigneeSelect
              id={`assignee-${task.id}`}
              label=""
              compact
              ariaLabel={`Assignee for "${task.title}"`}
              value={task.assigned_to ?? ''}
              onChange={(assignedTo) =>
                assignTask.mutate({ taskId: task.id, assignedTo: assignedTo || null })
              }
            />
          ) : (
            <p
              className={`flex min-w-0 items-center gap-1.5 ${assigneeEmail ? 'text-ink-soft' : 'text-muted'}`}
            >
              <UserRound className="h-4 w-4 shrink-0 text-faint" aria-hidden="true" />
              <span className="sr-only">Assigned to: </span>
              <span className="truncate">{assigneeEmail ?? 'Unassigned'}</span>
            </p>
          )}
        </div>

        <TaskRowActions
          task={task}
          canEdit={canEdit}
          canComplete={canComplete}
          canDelete={canDelete}
          onEdit={onEdit}
        />
      </div>
    </li>
  )
}

/** The one extra fact worth stating beside the status, if there is one. */
function StatusDetail({ task }: { task: Task }) {
  if (task.status === 'COMPLETED' && task.completed_at) {
    return <span className="text-label text-muted">{formatCompletedDate(task.completed_at)}</span>
  }
  const state = getDueState(task)
  if (state === 'overdue') {
    const days = daysOverdue(task)
    return (
      <span className="text-label font-semibold text-late">
        {days === 1 ? '1 day late' : `${days} days late`}
      </span>
    )
  }
  if (state === 'today') {
    return <span className="text-label font-semibold text-ink">Due today</span>
  }
  return null
}
