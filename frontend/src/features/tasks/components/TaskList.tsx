import { useState } from 'react'

import type { Task } from '../../../types/task'
import { useUsers } from '../hooks/useUsers'
import { TaskFormModal } from './TaskFormModal'
import { TaskListItem } from './TaskListItem'

export function TaskList({ tasks }: { tasks: Task[] }) {
  // Looked up once for the whole list and passed down, keeping rows free of
  // their own data fetching.
  const { data: users } = useUsers()
  const [editingTask, setEditingTask] = useState<Task | null>(null)

  return (
    <>
      <ul className="divide-y divide-line">
        {tasks.map((task) => (
          <TaskListItem
            key={task.id}
            task={task}
            users={users}
            onEdit={() => setEditingTask(task)}
          />
        ))}
      </ul>

      {/* One shared edit modal for the whole list rather than one per row. */}
      <TaskFormModal
        isOpen={editingTask !== null}
        onClose={() => setEditingTask(null)}
        task={editingTask ?? undefined}
      />
    </>
  )
}
