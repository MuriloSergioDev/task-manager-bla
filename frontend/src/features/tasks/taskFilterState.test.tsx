import { act, renderHook } from '@testing-library/react'
import type { ReactNode } from 'react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { PAGE_SIZE, parsePage, parseTaskFilters, toQueryParams, useTaskFilters } from './taskFilterState'

const params = (query: string) => new URLSearchParams(query)

describe('parseTaskFilters', () => {
  it('reads status and due-date range from the URL', () => {
    expect(parseTaskFilters(params('status=IN_PROGRESS&due_date_from=2026-09-01&due_date_to=2026-09-30'))).toEqual({
      status: 'IN_PROGRESS',
      dueDateFrom: '2026-09-01',
      dueDateTo: '2026-09-30',
    })
  })

  it('leaves absent filters undefined', () => {
    expect(parseTaskFilters(params(''))).toEqual({
      status: undefined,
      dueDateFrom: undefined,
      dueDateTo: undefined,
    })
  })

  // Regression: a hand-edited or stale URL (?status=DONE) was passed straight
  // to the API, which rejected it with 422, and the dashboard showed "Tasks
  // couldn't be loaded". Unknown values are ignored instead, like `page`.
  it('ignores a status the API does not know', () => {
    expect(parseTaskFilters(params('status=DONE')).status).toBeUndefined()
    expect(parseTaskFilters(params('status=todo')).status).toBeUndefined()
  })

  it('ignores due dates that are not YYYY-MM-DD', () => {
    const filters = parseTaskFilters(params('due_date_from=yesterday&due_date_to=2026-9-30'))
    expect(filters.dueDateFrom).toBeUndefined()
    expect(filters.dueDateTo).toBeUndefined()
  })
})

describe('parsePage', () => {
  it('reads a positive integer page', () => {
    expect(parsePage(params('page=3'))).toBe(3)
  })

  it.each(['', 'page=0', 'page=-2', 'page=1.5', 'page=abc'])('falls back to page 1 for "%s"', (query) => {
    expect(parsePage(params(query))).toBe(1)
  })
})

describe('toQueryParams', () => {
  it('maps filters to the API parameter names with the page size', () => {
    expect(toQueryParams({ status: 'TODO', dueDateFrom: '2026-09-01' }, 2)).toEqual({
      status: 'TODO',
      due_date_from: '2026-09-01',
      due_date_to: undefined,
      page: 2,
      page_size: PAGE_SIZE,
    })
  })
})

describe('useTaskFilters', () => {
  function setup(initialUrl: string) {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <MemoryRouter initialEntries={[initialUrl]}>{children}</MemoryRouter>
    )
    return renderHook(() => ({ state: useTaskFilters(), location: useLocation() }), { wrapper })
  }

  it('reads filters and page from the URL', () => {
    const { result } = setup('/dashboard?status=COMPLETED&page=2')
    expect(result.current.state.filters.status).toBe('COMPLETED')
    expect(result.current.state.page).toBe(2)
  })

  it('goes back to page 1 when a filter changes', () => {
    const { result } = setup('/dashboard?page=3')
    act(() => result.current.state.updateFilters({ status: 'TODO' }))
    expect(result.current.location.search).toBe('?status=TODO')
    expect(result.current.state.page).toBe(1)
  })

  it('keeps the filters when the page changes', () => {
    const { result } = setup('/dashboard?status=TODO')
    act(() => result.current.state.setPage(2))
    expect(result.current.location.search).toBe('?status=TODO&page=2')
  })

  it('removes cleared filters from the URL', () => {
    const { result } = setup('/dashboard?status=TODO&due_date_from=2026-09-01')
    act(() => result.current.state.updateFilters({ status: undefined, dueDateFrom: undefined }))
    expect(result.current.location.search).toBe('')
  })
})
