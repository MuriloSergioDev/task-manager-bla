import { useSearchParams } from 'react-router-dom'

import type { TaskFilterValues, TaskStatus } from '../../types/task'

const DEFAULT_PAGE_SIZE = 20

export interface TaskQueryParams {
  status?: TaskStatus
  due_date_from?: string
  due_date_to?: string
  page: number
  page_size: number
}

export function parseTaskFilters(searchParams: URLSearchParams): TaskFilterValues {
  const status = searchParams.get('status') as TaskStatus | null
  const page = Number(searchParams.get('page') ?? '1') || 1
  const pageSize = Number(searchParams.get('page_size') ?? String(DEFAULT_PAGE_SIZE)) || DEFAULT_PAGE_SIZE

  return {
    status: status ?? undefined,
    dueDateFrom: searchParams.get('due_date_from') ?? undefined,
    dueDateTo: searchParams.get('due_date_to') ?? undefined,
    page,
    pageSize,
  }
}

export function toQueryParams(filters: TaskFilterValues): TaskQueryParams {
  return {
    status: filters.status,
    due_date_from: filters.dueDateFrom,
    due_date_to: filters.dueDateTo,
    page: filters.page,
    page_size: filters.pageSize,
  }
}

export function useTaskFilters() {
  const [searchParams, setSearchParams] = useSearchParams()
  const filters = parseTaskFilters(searchParams)

  function updateFilters(partial: Partial<TaskFilterValues>) {
    const next = { ...filters, ...partial }
    // Changing a filter re-starts pagination, unless the page itself is
    // what changed (e.g. clicking "next").
    if (!('page' in partial)) {
      next.page = 1
    }

    const params = new URLSearchParams()
    if (next.status) params.set('status', next.status)
    if (next.dueDateFrom) params.set('due_date_from', next.dueDateFrom)
    if (next.dueDateTo) params.set('due_date_to', next.dueDateTo)
    params.set('page', String(next.page))
    params.set('page_size', String(next.pageSize))

    setSearchParams(params)
  }

  return { filters, updateFilters }
}
