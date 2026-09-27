import { useEffect } from 'react'
import { Controller, useForm } from 'react-hook-form'

import { Alert, Button, Input, Modal, Select, Textarea } from '../../../components/ui'
import type { Task, TaskStatus } from '../../../types/task'
import { useCreateTask } from '../hooks/useCreateTask'
import { useUpdateTask } from '../hooks/useUpdateTask'
import { AssigneeSelect } from './AssigneeSelect'

interface TaskFormValues {
  title: string
  description: string
  due_date: string
  assigned_to: string
  status: TaskStatus
}

// COMPLETED is deliberately not offered as a PATCH target: completing goes
// through the row's "Complete" button (POST /tasks/{id}/complete), which stamps
// completed_at and enqueues the activity job. It's only listed when the task
// is already completed, so it can be reopened from here.
const STATUS_OPTIONS: { value: TaskStatus; label: string }[] = [
  { value: 'TODO', label: 'To do' },
  { value: 'IN_PROGRESS', label: 'In progress' },
]

interface TaskFormModalProps {
  isOpen: boolean
  onClose: () => void
  task?: Task
}

export function TaskFormModal({ isOpen, onClose, task }: TaskFormModalProps) {
  const isEditing = Boolean(task)
  const createTask = useCreateTask()
  const updateTask = useUpdateTask()
  const mutation = isEditing ? updateTask : createTask

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm<TaskFormValues>({
    defaultValues: { title: '', description: '', due_date: '', assigned_to: '', status: 'TODO' },
  })

  useEffect(() => {
    if (isOpen) {
      reset({
        title: task?.title ?? '',
        description: task?.description ?? '',
        due_date: task?.due_date ?? '',
        assigned_to: task?.assigned_to ?? '',
        status: task?.status ?? 'TODO',
      })
    }
  }, [isOpen, task, reset])

  const onSubmit = (values: TaskFormValues) => {
    // Reassignment while editing is a dedicated action (the inline
    // assignee control on each row, backed by POST /assign) rather than
    // part of this form, so the edit payload never touches assigned_to.
    if (isEditing && task) {
      updateTask.mutate(
        {
          taskId: task.id,
          input: {
            title: values.title,
            description: values.description || null,
            due_date: values.due_date || null,
            // Only sent when changed, so saving an untouched completed task
            // doesn't needlessly re-PATCH its status.
            ...(values.status !== task.status && { status: values.status }),
          },
        },
        { onSuccess: onClose },
      )
    } else {
      createTask.mutate(
        {
          title: values.title,
          description: values.description || null,
          due_date: values.due_date || null,
          assigned_to: values.assigned_to || null,
        },
        { onSuccess: onClose },
      )
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={isEditing ? 'Edit task' : 'New task'}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
        <Input
          label="Title"
          error={errors.title?.message}
          {...register('title', {
            required: 'Title is required',
            maxLength: { value: 200, message: 'Title must be 200 characters or fewer' },
          })}
        />
        <Textarea
          label="Description"
          placeholder="Optional details"
          {...register('description')}
        />
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <Input label="Due date" type="date" {...register('due_date')} />
          {isEditing && task && (
            // Explicit id: Select derives its id from name, and "status" is
            // also the name of the filter bar's radio group.
            <Select id="task-form-status" label="Status" {...register('status')}>
              {task.status === 'COMPLETED' && <option value="COMPLETED">Done</option>}
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          )}
        </div>
        {!isEditing && (
          <Controller
            name="assigned_to"
            control={control}
            render={({ field }) => <AssigneeSelect value={field.value} onChange={field.onChange} />}
          />
        )}

        {mutation.error && (
          <Alert tone="error">{mutation.error.message}</Alert>
        )}

        <div className="flex flex-col-reverse gap-2 pt-2 sm:flex-row sm:justify-end">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Saving…' : isEditing ? 'Save changes' : 'Create task'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
