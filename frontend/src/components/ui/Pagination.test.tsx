import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { Pagination } from './Pagination'

describe('Pagination', () => {
  it('shows the range being viewed', () => {
    render(<Pagination page={2} pages={2} pageSize={20} total={35} onPageChange={() => {}} />)
    expect(screen.getByRole('navigation', { name: 'Pagination' }).textContent).toContain('21–35 of 35')
  })

  it('disables Previous on the first page and Next on the last', () => {
    const { rerender } = render(<Pagination page={1} pages={2} pageSize={20} total={35} onPageChange={() => {}} />)
    expect(screen.getByRole<HTMLButtonElement>('button', { name: 'Previous page' }).disabled).toBe(true)
    expect(screen.getByRole<HTMLButtonElement>('button', { name: 'Next page' }).disabled).toBe(false)

    rerender(<Pagination page={2} pages={2} pageSize={20} total={35} onPageChange={() => {}} />)
    expect(screen.getByRole<HTMLButtonElement>('button', { name: 'Previous page' }).disabled).toBe(false)
    expect(screen.getByRole<HTMLButtonElement>('button', { name: 'Next page' }).disabled).toBe(true)
  })

  it('asks for the neighbouring page', async () => {
    const onPageChange = vi.fn()
    render(<Pagination page={3} pages={5} pageSize={20} total={92} onPageChange={onPageChange} />)

    await userEvent.click(screen.getByRole('button', { name: 'Next page' }))
    await userEvent.click(screen.getByRole('button', { name: 'Previous page' }))

    expect(onPageChange.mock.calls).toEqual([[4], [2]])
  })

  it('renders nothing when there are no results', () => {
    const { container } = render(<Pagination page={1} pages={0} pageSize={20} total={0} onPageChange={() => {}} />)
    expect(container.innerHTML).toBe('')
  })
})
