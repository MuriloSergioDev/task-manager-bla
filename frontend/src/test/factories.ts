import type { Task } from '../types/task'
import type { User } from '../types/user'

export function makeTask(overrides: Partial<Task> = {}): Task {
  return {
    id: 'task-1',
    title: 'Renew SSL certificate',
    description: null,
    status: 'TODO',
    due_date: null,
    completed_at: null,
    owner_id: 'owner-1',
    assigned_to: null,
    created_at: '2026-09-01T12:00:00Z',
    updated_at: '2026-09-01T12:00:00Z',
    ...overrides,
  }
}

export function makeUser(overrides: Partial<User> = {}): User {
  return { id: 'owner-1', email: 'alice@example.com', ...overrides }
}
