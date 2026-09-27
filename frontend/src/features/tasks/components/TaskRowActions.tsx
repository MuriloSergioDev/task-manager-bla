import { Check, Pencil, Trash2 } from 'lucide-react'
import { useState } from 'react'

import { Button, ConfirmDialog, StatusBadge } from '../../../components/ui'
import type { Task } from '../../../types/task'
import { useCompleteTask } from '../hooks/useCompleteTask'
import { useDeleteTask } from '../hooks/useDeleteTask'

interface TaskRowActionsProps {
  task: Task
  canEdit: boolean
  canComplete: boolean
  onEdit: () => void
}

export function TaskRowActions({ task, canEdit, canComplete, onEdit }: TaskRowActionsProps) {
  const completeTask = useCompleteTask()
  const deleteTask = useDeleteTask()
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false)

  if (!canComplete && !canEdit) {
    return null
  }

  return (
    <div className="flex items-center gap-1 md:justify-end">
      {canComplete && (
        <Button
          variant="secondary"
          size="sm"
          onClick={() => completeTask.mutate(task.id)}
          disabled={completeTask.isPending}
          className="mr-1"
        >
          <Check className="h-4 w-4" aria-hidden="true" />
          Complete
        </Button>
      )}
      {canEdit && (
        <>
          <Button
            // Icon-only so the row's one labelled action, Complete, stands
            // out; each still has a task-specific accessible name.
            variant="ghost"
            size="icon"
            onClick={onEdit}
            aria-label={`Edit "${task.title}"`}
            title="Edit"
          >
            <Pencil className="h-4 w-4" aria-hidden="true" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsDeleteConfirmOpen(true)}
            aria-label={`Delete "${task.title}"`}
            title="Delete"
            className="hover:bg-late-wash hover:text-late"
          >
            <Trash2 className="h-4 w-4" aria-hidden="true" />
          </Button>
          <ConfirmDialog
            isOpen={isDeleteConfirmOpen}
            title="Delete this task?"
            description="It's removed for you and for anyone it's assigned to. This can't be undone."
            confirmLabel="Delete task"
            isConfirming={deleteTask.isPending}
            errorMessage={deleteTask.error?.message}
            onCancel={() => setIsDeleteConfirmOpen(false)}
            onConfirm={() => deleteTask.mutate(task.id, { onSuccess: () => setIsDeleteConfirmOpen(false) })}
          >
            <div className="flex items-center gap-3 rounded-control border border-line bg-wash px-3 py-2.5">
              <p className="min-w-0 flex-1 truncate text-sm font-semibold text-ink">{task.title}</p>
              <StatusBadge status={task.status} />
            </div>
          </ConfirmDialog>
        </>
      )}
    </div>
  )
}
