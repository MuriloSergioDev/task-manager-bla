import type { Meta, StoryObj } from '@storybook/react-vite'

import type { Task, TaskStatus } from '../../../types/task'
import { DateStub } from './DateStub'

// Local YYYY-MM-DD `offset` days from today. Relative, so "today" and
// "overdue" stay true whenever Storybook is opened.
function dayFromToday(offset: number): string {
  const date = new Date()
  date.setDate(date.getDate() + offset)
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day}`
}

function makeTask(dueDate: string | null, status: TaskStatus = 'TODO'): Task {
  return {
    id: 'story-task',
    title: 'Renew SSL certificate',
    description: null,
    status,
    due_date: dueDate,
    completed_at: status === 'COMPLETED' ? new Date().toISOString() : null,
    owner_id: 'owner',
    assigned_to: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
}

const meta = {
  title: 'Patterns/DateStub',
  component: DateStub,
  args: { task: makeTask(dayFromToday(5)) },
} satisfies Meta<typeof DateStub>

export default meta
type Story = StoryObj<typeof meta>

export const Upcoming: Story = {}

/** Brick, and the row adds "N days late" beside the status. */
export const Overdue: Story = { args: { task: makeTask(dayFromToday(-6)) } }

/** Inverted to ink: the most urgent state that isn't yet late. */
export const DueToday: Story = { args: { task: makeTask(dayFromToday(0)) } }

/** The year only appears when it isn't the current one. */
export const OtherYear: Story = { args: { task: makeTask(dayFromToday(400)) } }

export const NoDueDate: Story = { args: { task: makeTask(null) } }

/** Done tasks fade back even if they were due in the past. */
export const Done: Story = { args: { task: makeTask(dayFromToday(-3), 'COMPLETED') } }

/** Every state in a row, as they appear down the list. */
export const AllStates: Story = {
  render: () => (
    <div className="flex gap-3">
      <DateStub task={makeTask(dayFromToday(-6))} />
      <DateStub task={makeTask(dayFromToday(0))} />
      <DateStub task={makeTask(dayFromToday(5))} />
      <DateStub task={makeTask(dayFromToday(400))} />
      <DateStub task={makeTask(null)} />
      <DateStub task={makeTask(dayFromToday(-3), 'COMPLETED')} />
    </div>
  ),
}
