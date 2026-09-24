import { useState } from 'react'

import { Button } from '../components/ui/Button'
import { Pagination } from '../components/ui/Pagination'
import { Spinner } from '../components/ui/Spinner'
import { TaskFilters } from '../features/tasks/components/TaskFilters'
import { TaskFormModal } from '../features/tasks/components/TaskFormModal'
import { TaskTable } from '../features/tasks/components/TaskTable'
import { useTasks } from '../features/tasks/hooks/useTasks'
import { useTaskFilters } from '../features/tasks/taskFilterState'

export function DashboardPage() {
  const { filters, updateFilters } = useTaskFilters()
  const { data, isLoading, error } = useTasks(filters)
  const [isCreateOpen, setIsCreateOpen] = useState(false)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">Tasks</h1>
        <Button onClick={() => setIsCreateOpen(true)}>New task</Button>
      </div>

      <TaskFilters filters={filters} onChange={updateFilters} />

      <div className="rounded-lg bg-white shadow-sm">
        {isLoading && (
          <div className="flex justify-center p-10">
            <Spinner className="h-8 w-8 text-blue-600" />
          </div>
        )}

        {error && (
          <p className="p-6 text-center text-sm text-red-600">
            {error.message || 'Failed to load tasks.'}
          </p>
        )}

        {data && (
          <>
            <TaskTable tasks={data.items} />
            <Pagination
              page={data.page}
              pages={data.pages}
              total={data.total}
              onPageChange={(page) => updateFilters({ page })}
            />
          </>
        )}
      </div>

      <TaskFormModal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} />
    </div>
  )
}
