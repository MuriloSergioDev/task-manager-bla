import { Plus } from 'lucide-react'
import { useEffect, useState } from 'react'

import { Button, EmptyState, Pagination, Spinner } from '../components/ui'
import { TaskFilters } from '../features/tasks/components/TaskFilters'
import { TaskFormModal } from '../features/tasks/components/TaskFormModal'
import { TaskList } from '../features/tasks/components/TaskList'
import { useTasks } from '../features/tasks/hooks/useTasks'
import { useTaskFilters } from '../features/tasks/taskFilterState'

export function DashboardPage() {
  const { filters, page, updateFilters, setPage } = useTaskFilters()
  const { data, isLoading, error } = useTasks(filters, page)
  const [isCreateOpen, setIsCreateOpen] = useState(false)

  const hasActiveFilters = Boolean(filters.status || filters.dueDateFrom || filters.dueDateTo)
  const clearFilters = () => updateFilters({ status: undefined, dueDateFrom: undefined, dueDateTo: undefined })

  // Deleting the last task on the last page (or a stale bookmarked URL)
  // leaves us past the end -- step back to the last page that exists.
  const lastPage = data?.pages
  useEffect(() => {
    if (lastPage !== undefined && page > Math.max(lastPage, 1)) {
      setPage(Math.max(lastPage, 1))
    }
  }, [lastPage, page, setPage])

  const newTaskButton = (
    <Button onClick={() => setIsCreateOpen(true)}>
      <Plus className="h-4 w-4" aria-hidden="true" />
      New task
    </Button>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-display-sm font-extrabold text-ink sm:text-display">
            Tasks
          </h1>
          <p className="mt-2.5 text-lead text-muted" aria-live="polite">
            {data
              ? `${data.total} ${data.total === 1 ? 'task' : 'tasks'} ${
                  hasActiveFilters ? 'match these filters' : 'you own or are assigned to'
                }`
              : 'Loading your tasks…'}
          </p>
        </div>
        <div className="shrink-0">{newTaskButton}</div>
      </div>

      <TaskFilters filters={filters} onChange={updateFilters} />

      <section aria-label="Task list" className="overflow-hidden rounded-sheet border border-line bg-sheet">
        {isLoading && (
          <div className="flex justify-center p-16">
            <Spinner className="h-7 w-7 text-faint" />
          </div>
        )}

        {error && (
          <EmptyState
            tone="error"
            title="Tasks couldn't be loaded"
            description={`${error.message || 'The server returned an error.'} Check your connection and reload the page.`}
          />
        )}

        {data && data.items.length === 0 &&
          (hasActiveFilters ? (
            <EmptyState
              title="Nothing matches these filters"
              description="Widen the date range or pick a different status."
              action={
                <Button variant="secondary" onClick={clearFilters}>
                  Clear filters
                </Button>
              }
            />
          ) : (
            <EmptyState
              title="Your queue is empty"
              description="Create a task to get started. Tasks that teammates assign to you will show up here too."
              action={newTaskButton}
            />
          ))}

        {data && data.items.length > 0 && (
          <>
            <TaskList tasks={data.items} />
            <Pagination
              page={data.page}
              pages={data.pages}
              pageSize={data.page_size}
              total={data.total}
              onPageChange={setPage}
            />
          </>
        )}
      </section>

      <TaskFormModal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} />
    </div>
  )
}
