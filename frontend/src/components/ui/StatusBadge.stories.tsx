import type { Meta, StoryObj } from '@storybook/react-vite'

import { StatusBadge, StatusGlyph } from './StatusBadge'

const meta = {
  title: 'Components/StatusBadge',
  component: StatusBadge,
  args: { status: 'IN_PROGRESS' },
  argTypes: { status: { control: 'inline-radio', options: ['TODO', 'IN_PROGRESS', 'COMPLETED'] } },
} satisfies Meta<typeof StatusBadge>

export default meta
type Story = StoryObj<typeof meta>

export const Playground: Story = {}

/** The ring fills as work advances, so status reads as progress rather than
 *  as three arbitrary colours. */
export const AllStatuses: Story = {
  render: () => (
    <div className="flex items-center gap-6">
      <StatusBadge status="TODO" />
      <StatusBadge status="IN_PROGRESS" />
      <StatusBadge status="COMPLETED" />
    </div>
  ),
}

/** The done check is cut out of the disc with a mask rather than painted in
 *  a fixed colour, so it stays visible on the selected (ink) filter segment. */
export const GlyphOnInk: Story = {
  render: () => (
    <div className="flex items-center gap-4 rounded-control bg-ink px-4 py-3 text-sheet">
      <StatusGlyph status="TODO" className="h-5 w-5" />
      <StatusGlyph status="IN_PROGRESS" className="h-5 w-5" />
      <StatusGlyph status="COMPLETED" className="h-5 w-5" />
    </div>
  ),
}
