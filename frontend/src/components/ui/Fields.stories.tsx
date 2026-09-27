import type { Meta, StoryObj } from '@storybook/react-vite'

import { Input } from './Input'
import { Select } from './Select'
import { Textarea } from './Textarea'

/** Input, Select and Textarea share one style source (`fieldStyles.ts`), so
 *  they're shown together: they should always look like one family. */
const meta = {
  title: 'Components/Fields',
  component: Input,
  args: { label: 'Title', name: 'title', placeholder: '' },
  decorators: [(Story) => <div className="w-80">{Story()}</div>],
} satisfies Meta<typeof Input>

export default meta
type Story = StoryObj<typeof meta>

export const TextInput: Story = {}

export const WithError: Story = {
  args: { error: 'Title is required' },
}

export const Disabled: Story = {
  args: { disabled: true, defaultValue: 'Renew SSL certificate' },
}

export const DateInput: Story = {
  args: { label: 'Due date', name: 'due_date', type: 'date' },
}

export const SelectField: Story = {
  render: () => (
    <Select label="Assignee" name="assignee">
      <option value="">Unassigned</option>
      <option value="bob">bob@example.com</option>
    </Select>
  ),
}

/** For controls inside dense rows (the task list's assignee picker). */
export const CompactSelect: Story = {
  render: () => (
    <Select label="" aria-label="Assignee" name="assignee-compact" compact>
      <option value="">Unassigned</option>
      <option value="bob">bob@example.com</option>
    </Select>
  ),
}

export const TextareaField: Story = {
  render: () => <Textarea label="Description" name="description" placeholder="Optional details" />,
}

/** All three side by side, to check they line up. */
export const Family: Story = {
  decorators: [(Story) => <div className="w-xl">{Story()}</div>],
  render: () => (
    <div className="grid grid-cols-3 items-start gap-4">
      <Input label="Title" name="family-title" />
      <Select label="Status" name="family-status">
        <option>To do</option>
      </Select>
      <Textarea label="Notes" name="family-notes" rows={1} />
    </div>
  ),
}
