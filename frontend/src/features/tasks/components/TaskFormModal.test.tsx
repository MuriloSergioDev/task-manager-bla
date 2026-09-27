import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { makeTask, makeUser } from '../../../test/factories'
import { renderWithProviders } from '../../../test/render'
import * as tasksApi from '../tasksApi'
import * as usersApi from '../usersApi'
import { TaskFormModal } from './TaskFormModal'

const bob = makeUser({ id: 'bob-1', email: 'bob@example.com' })

beforeEach(() => {
  vi.spyOn(usersApi, 'fetchUsers').mockResolvedValue([makeUser(), bob])
})

describe('TaskFormModal: creating', () => {
  it('requires a title and sends nothing without one', async () => {
    const createTask = vi.spyOn(tasksApi, 'createTask')
    renderWithProviders(<TaskFormModal isOpen onClose={() => {}} />)

    await userEvent.click(screen.getByRole('button', { name: 'Create task' }))

    expect(await screen.findByText('Title is required')).toBeTruthy()
    expect(createTask).not.toHaveBeenCalled()
  })

  it('rejects a title over 200 characters', async () => {
    renderWithProviders(<TaskFormModal isOpen onClose={() => {}} />)

    // paste() rather than type(): 201 simulated keystrokes are slow and add nothing.
    await userEvent.click(screen.getByLabelText('Title'))
    await userEvent.paste('x'.repeat(201))
    await userEvent.click(screen.getByRole('button', { name: 'Create task' }))

    expect(await screen.findByText('Title must be 200 characters or fewer')).toBeTruthy()
  })

  it('sends empty optional fields as null and the chosen assignee, then closes', async () => {
    const createTask = vi.spyOn(tasksApi, 'createTask').mockResolvedValue(makeTask())
    const onClose = vi.fn()
    renderWithProviders(<TaskFormModal isOpen onClose={onClose} />)

    await userEvent.type(screen.getByLabelText('Title'), 'Write release notes')
    await screen.findByRole('option', { name: 'bob@example.com' })
    await userEvent.selectOptions(screen.getByLabelText('Assignee'), 'bob-1')
    await userEvent.click(screen.getByRole('button', { name: 'Create task' }))

    await vi.waitFor(() => expect(onClose).toHaveBeenCalled())
    expect(createTask.mock.calls[0][0]).toEqual({
      title: 'Write release notes',
      description: null,
      due_date: null,
      assigned_to: 'bob-1',
    })
  })

  it('keeps the dialog open and shows the API error when saving fails', async () => {
    vi.spyOn(tasksApi, 'createTask').mockRejectedValue({ status: 422, message: 'Assignee does not exist' })
    const onClose = vi.fn()
    renderWithProviders(<TaskFormModal isOpen onClose={onClose} />)

    await userEvent.type(screen.getByLabelText('Title'), 'Write release notes')
    await userEvent.click(screen.getByRole('button', { name: 'Create task' }))

    expect((await screen.findByRole('alert')).textContent).toBe('Assignee does not exist')
    expect(onClose).not.toHaveBeenCalled()
  })
})

describe('TaskFormModal: editing', () => {
  const existing = makeTask({
    id: 'task-9',
    title: 'Renew SSL certificate',
    description: 'Before the old one expires',
    due_date: '2026-10-01',
    status: 'IN_PROGRESS',
    assigned_to: 'bob-1',
  })

  it('starts from the task\'s current values', () => {
    renderWithProviders(<TaskFormModal isOpen onClose={() => {}} task={existing} />)

    expect(screen.getByLabelText<HTMLInputElement>('Title').value).toBe('Renew SSL certificate')
    expect(screen.getByLabelText<HTMLTextAreaElement>('Description').value).toBe('Before the old one expires')
    expect(screen.getByLabelText<HTMLInputElement>('Due date').value).toBe('2026-10-01')
    expect(screen.getByLabelText<HTMLSelectElement>('Status').value).toBe('IN_PROGRESS')
  })

  // Status is only sent when it changed, and reassignment is a separate
  // action (POST /assign), so an edit never touches assigned_to.
  it('sends the edited fields without status or assignee when those are unchanged', async () => {
    const updateTask = vi.spyOn(tasksApi, 'updateTask').mockResolvedValue(existing)
    renderWithProviders(<TaskFormModal isOpen onClose={() => {}} task={existing} />)

    await userEvent.clear(screen.getByLabelText('Description'))
    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }))

    await vi.waitFor(() => expect(updateTask).toHaveBeenCalledTimes(1))
    expect(updateTask.mock.calls[0]).toEqual([
      'task-9',
      { title: 'Renew SSL certificate', description: null, due_date: '2026-10-01' },
    ])
  })

  it('sends the status when it changed', async () => {
    const updateTask = vi.spyOn(tasksApi, 'updateTask').mockResolvedValue(existing)
    renderWithProviders(<TaskFormModal isOpen onClose={() => {}} task={existing} />)

    await userEvent.selectOptions(screen.getByLabelText('Status'), 'TODO')
    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }))

    await vi.waitFor(() => expect(updateTask).toHaveBeenCalledTimes(1))
    expect(updateTask.mock.calls[0][1]).toMatchObject({ status: 'TODO' })
  })

  // Completing goes through POST /complete (it stamps completed_at and queues
  // the activity job), so "Done" is only offered to keep a done task as is.
  it('offers "Done" only for a task that is already done', () => {
    const { unmount } = renderWithProviders(<TaskFormModal isOpen onClose={() => {}} task={existing} />)
    const optionsFor = () =>
      Array.from(screen.getByLabelText<HTMLSelectElement>('Status').options).map((option) => option.value)
    expect(optionsFor()).toEqual(['TODO', 'IN_PROGRESS'])
    unmount()

    renderWithProviders(<TaskFormModal isOpen onClose={() => {}} task={{ ...existing, status: 'COMPLETED' }} />)
    expect(optionsFor()).toEqual(['COMPLETED', 'TODO', 'IN_PROGRESS'])
  })
})
