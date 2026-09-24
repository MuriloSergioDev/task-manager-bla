import { useEffect } from 'react'
import { useForm } from 'react-hook-form'

import { Button } from '../../../components/ui/Button'
import { Input } from '../../../components/ui/Input'
import { Modal } from '../../../components/ui/Modal'
import type { Task } from '../../../types/task'
import { useCreateTask } from '../hooks/useCreateTask'
import { useUpdateTask } from '../hooks/useUpdateTask'
import { AssigneeSelect } from './AssigneeSelect'

interface TaskFormValues {
  title: string
  description: string
  due_date: string
  assigned_to: string
}

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
    setValue,
    watch,
    formState: { errors },
  } = useForm<TaskFormValues>({
    defaultValues: { title: '', description: '', due_date: '', assigned_to: '' },
  })

  useEffect(() => {
    if (isOpen) {
      reset({
        title: task?.title ?? '',
        description: task?.description ?? '',
        due_date: task?.due_date ?? '',
        assigned_to: task?.assigned_to ?? '',
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
    <Modal isOpen={isOpen} onClose={onClose} title={isEditing ? 'Edit task' : 'Create task'}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <Input
          label="Title"
          error={errors.title?.message}
          {...register('title', {
            required: 'Title is required',
            maxLength: { value: 200, message: 'Title must be 200 characters or fewer' },
          })}
        />
        <Input label="Description" {...register('description')} />
        <Input label="Due date" type="date" {...register('due_date')} />
        {!isEditing && (
          <AssigneeSelect
            value={watch('assigned_to')}
            onChange={(value) => setValue('assigned_to', value)}
          />
        )}

        {mutation.error && (
          <p className="text-sm text-red-600" role="alert">
            {mutation.error.message}
          </p>
        )}

        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Saving…' : 'Save'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
