import type { Meta, StoryObj } from '@storybook/react-vite'

import { Wordmark } from './Wordmark'

/** The mark is the date stub again (a calendar leaf with a check), so the
 *  logo, the favicon and the task list share one motif. */
const meta = {
  title: 'Patterns/Wordmark',
  component: Wordmark,
  args: { size: 'md' },
  argTypes: { size: { control: 'inline-radio', options: ['md', 'lg'] } },
} satisfies Meta<typeof Wordmark>

export default meta
type Story = StoryObj<typeof meta>

/** Header. */
export const Medium: Story = {}

/** Sign-in and registration screens. */
export const Large: Story = { args: { size: 'lg' } }
