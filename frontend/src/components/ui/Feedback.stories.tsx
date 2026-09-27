import type { Meta, StoryObj } from '@storybook/react-vite'
import { Plus } from 'lucide-react'
import type { ReactNode } from 'react'

import { Alert } from './Alert'
import { Button } from './Button'
import { EmptyState } from './EmptyState'
import { Spinner } from './Spinner'

/** How the interface reports state: inline alerts for a form or action,
 *  empty states for a list with nothing to show, a spinner while loading. */
const meta = {
  title: 'Components/Feedback',
  component: Alert,
  args: { tone: 'error', children: 'Incorrect email or password.' },
} satisfies Meta<typeof Alert>

export default meta
type Story = StoryObj<typeof meta>

const narrow = (content: ReactNode) => <div className="w-96">{content}</div>
const sheet = (content: ReactNode) => (
  <div className="w-xl rounded-sheet border border-line bg-sheet">{content}</div>
)

export const ErrorAlert: Story = {
  render: (args) => narrow(<Alert {...args} />),
}

export const SuccessAlert: Story = {
  args: { tone: 'success', children: 'Account created. Sign in with your new password.' },
  render: (args) => narrow(<Alert {...args} />),
}

/** An empty screen is an invitation to act, so it carries the action. */
export const EmptyWithAction: Story = {
  render: () =>
    sheet(
      <EmptyState
        title="Your queue is empty"
        description="Create a task to get started. Tasks that teammates assign to you will show up here too."
        action={
          <Button>
            <Plus className="h-4 w-4" aria-hidden="true" />
            New task
          </Button>
        }
      />,
    ),
}

export const EmptyFiltered: Story = {
  render: () =>
    sheet(
      <EmptyState
        title="Nothing matches these filters"
        description="Widen the date range or pick a different status."
        action={<Button variant="secondary">Clear filters</Button>}
      />,
    ),
}

/** Errors say what happened and what to do next; they don't apologise. */
export const EmptyError: Story = {
  render: () =>
    sheet(
      <EmptyState
        tone="error"
        title="Tasks couldn't be loaded"
        description="Network Error. Check your connection and reload the page."
      />,
    ),
}

export const Loading: Story = {
  render: () => <Spinner className="h-7 w-7 text-faint" />,
}
