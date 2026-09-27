import { useSearchParams } from 'react-router-dom'

import { isTaskStatus } from '../../lib/taskStatus'
import type { TaskFilterValues, TaskStatus } from '../../types/task'

// Well under the API's cap of 100 (backend/app/presentation/api/dependencies/
// pagination.py); a page of 20 rows stays scannable on mobile.
export const PAGE_SIZE = 20

export interface TaskQueryParams {
  status?: TaskStatus
  due_date_from?: string
  due_date_to?: string
  page: number
  page_size: number
}

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/

function parseDate(value: string | null): string | undefined {
  return value !== null && ISO_DATE.test(value) ? value : undefined
}

/** Values the API would reject (an unknown status, a malformed date, e.g.
 *  from a hand-edited or stale URL) are dropped rather than sent, so the
 *  dashboard shows unfiltered tasks instead of an error. */
export function parseTaskFilters(searchParams: URLSearchParams): TaskFilterValues {
  const status = searchParams.get('status')

  return {
    status: isTaskStatus(status) ? status : undefined,
    dueDateFrom: parseDate(searchParams.get('due_date_from')),
    dueDateTo: parseDate(searchParams.get('due_date_to')),
  }
}

/** Anything that isn't a positive integer (e.g. a hand-edited URL) falls
 *  back to 1 rather than sending a value the API would reject with 422. */
export function parsePage(searchParams: URLSearchParams): number {
  const page = Number(searchParams.get('page'))
  return Number.isInteger(page) && page >= 1 ? page : 1
}

export function toQueryParams(filters: TaskFilterValues, page: number): TaskQueryParams {
  return {
    status: filters.status,
    due_date_from: filters.dueDateFrom,
    due_date_to: filters.dueDateTo,
    page,
    page_size: PAGE_SIZE,
  }
}

function toSearchParams(filters: TaskFilterValues, page: number): URLSearchParams {
  const params = new URLSearchParams()
  if (filters.status) params.set('status', filters.status)
  if (filters.dueDateFrom) params.set('due_date_from', filters.dueDateFrom)
  if (filters.dueDateTo) params.set('due_date_to', filters.dueDateTo)
  if (page > 1) params.set('page', String(page))
  return params
}

/** Filters and page live in the URL so a filtered view survives reloads
 *  and can be bookmarked or shared. */
export function useTaskFilters() {
  const [searchParams, setSearchParams] = useSearchParams()
  const filters = parseTaskFilters(searchParams)
  const page = parsePage(searchParams)

  // A filter change resets to page 1: the old page number is meaningless
  // against a different result set.
  function updateFilters(partial: Partial<TaskFilterValues>) {
    setSearchParams(toSearchParams({ ...filters, ...partial }, 1))
  }

  function setPage(nextPage: number) {
    setSearchParams(toSearchParams(filters, nextPage))
  }

  return { filters, page, updateFilters, setPage }
}
