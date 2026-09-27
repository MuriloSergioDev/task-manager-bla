import type { Meta, StoryObj } from '@storybook/react-vite'
import { Check, Pencil, Plus, Trash2 } from 'lucide-react'

import { Button } from './Button'

const meta = {
  title: 'Components/Button',
  component: Button,
  args: { children: 'New task', variant: 'primary', size: 'md', disabled: false },
  argTypes: {
    variant: { control: 'inline-radio', options: ['primary', 'secondary', 'danger', 'ghost'] },
    size: { control: 'inline-radio', options: ['md', 'sm', 'icon'] },
  },
} satisfies Meta<typeof Button>

export default meta
type Story = StoryObj<typeof meta>

/** Use the controls to try every variant and size. */
export const Playground: Story = {}

/** One primary action per view; secondary for the rest; danger only to
 *  confirm something destructive; ghost for low-emphasis actions in dense rows. */
export const Variants: Story = {
  render: (args) => (
    <div className="flex flex-wrap items-center gap-3">
      <Button {...args} variant="primary">
        <Plus className="h-4 w-4" aria-hidden="true" />
        New task
      </Button>
      <Button {...args} variant="secondary">
        Cancel
      </Button>
      <Button {...args} variant="danger">
        Delete task
      </Button>
      <Button {...args} variant="ghost">
        Clear filters
      </Button>
    </div>
  ),
}

export const Sizes: Story = {
  render: () => (
    <div className="flex items-center gap-3">
      <Button size="md">Create task</Button>
      <Button size="sm" variant="secondary">
        <Check className="h-4 w-4" aria-hidden="true" />
        Complete
      </Button>
      <Button size="icon" variant="ghost" aria-label="Edit task" title="Edit">
        <Pencil className="h-4 w-4" aria-hidden="true" />
      </Button>
      <Button size="icon" variant="ghost" aria-label="Delete task" title="Delete">
        <Trash2 className="h-4 w-4" aria-hidden="true" />
      </Button>
    </div>
  ),
}

export const Disabled: Story = {
  render: () => (
    <div className="flex items-center gap-3">
      <Button disabled>Saving…</Button>
      <Button disabled variant="secondary">
        Previous
      </Button>
      <Button disabled variant="danger">
        Delete task
      </Button>
    </div>
  ),
}
