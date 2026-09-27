import type { Task } from '../../types/task'

export type DueState = 'none' | 'overdue' | 'today' | 'upcoming' | 'done'

const MS_PER_DAY = 24 * 60 * 60 * 1000

/** Today as YYYY-MM-DD in the viewer's local time zone. `toISOString()`
 *  would give the UTC date, flagging tasks overdue (or not) up to a day
 *  early/late depending on where the viewer is. */
function localToday(): string {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${now.getFullYear()}-${month}-${day}`
}

// Date-only strings parsed at local midnight, so the calendar day is stable.
function parseDateOnly(date: string): Date {
  return new Date(`${date}T00:00:00`)
}

export function getDueState(task: Task): DueState {
  if (task.status === 'COMPLETED') return 'done'
  if (task.due_date === null) return 'none'
  const today = localToday()
  if (task.due_date < today) return 'overdue'
  if (task.due_date === today) return 'today'
  return 'upcoming'
}

export function isOverdue(task: Task): boolean {
  return getDueState(task) === 'overdue'
}

/** Whole calendar days a task is past its due date (0 if not overdue). */
export function daysOverdue(task: Task): number {
  if (!isOverdue(task) || task.due_date === null) return 0
  const elapsed = parseDateOnly(localToday()).getTime() - parseDateOnly(task.due_date).getTime()
  return Math.round(elapsed / MS_PER_DAY)
}

/** The pieces the date stub renders: month, day, and a year only when it
 *  isn't the current one (most due dates are this year; repeating it is noise). */
export function dueDateParts(dueDate: string): { month: string; day: string; year: string | null } {
  const date = parseDateOnly(dueDate)
  const year = date.getFullYear()
  return {
    month: date.toLocaleDateString('en-US', { month: 'short' }),
    day: String(date.getDate()),
    year: year === new Date().getFullYear() ? null : String(year),
  }
}

export function formatDueDate(dueDate: string | null): string {
  if (dueDate === null) return 'No due date'
  // Fixed locale rather than the browser/OS default: the format should be
  // the same for every viewer, not depend on where they happen to be.
  return parseDateOnly(dueDate).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

// completed_at is a full ISO datetime (not a plain date like due_date), so
// it's parsed directly rather than through formatDueDate's date-only path.
export function formatCompletedDate(completedAt: string): string {
  return new Date(completedAt).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}
