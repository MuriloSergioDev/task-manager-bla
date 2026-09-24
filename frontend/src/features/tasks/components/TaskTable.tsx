import { useState } from 'react'

import type { Task } from '../../../types/task'
import { TaskFormModal } from './TaskFormModal'
import { TaskRow } from './TaskRow'

export function TaskTable({ tasks }: { tasks: Task[] }) {
  const [editingTask, setEditingTask] = useState<Task | null>(null)

  if (tasks.length === 0) {
    return <p className="p-6 text-center text-sm text-gray-500">No tasks match these filters.</p>
  }

  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-left">
          <thead>
            <tr className="border-b border-gray-200 text-xs font-medium uppercase text-gray-500">
              <th className="px-4 py-2">Title</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Due date</th>
              <th className="px-4 py-2">Assigned to</th>
              <th className="px-4 py-2" />
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => (
              <TaskRow key={task.id} task={task} onEdit={() => setEditingTask(task)} />
            ))}
          </tbody>
        </table>
      </div>
      {/* Rendered once, outside <table>, rather than per-row inside <tbody>
          -- a fixed-position overlay div is not valid table markup. */}
      <TaskFormModal
        isOpen={editingTask !== null}
        onClose={() => setEditingTask(null)}
        task={editingTask ?? undefined}
      />
    </>
  )
}
