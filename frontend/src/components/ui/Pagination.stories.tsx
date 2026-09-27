import type { Meta, StoryObj } from '@storybook/react-vite'
import { useState } from 'react'

import { Pagination } from './Pagination'

const meta = {
  title: 'Components/Pagination',
  component: Pagination,
  args: { page: 1, pages: 2, pageSize: 20, total: 35, onPageChange: () => {} },
  decorators: [
    (Story) => <div className="w-xl rounded-sheet border border-line bg-sheet">{Story()}</div>,
  ],
} satisfies Meta<typeof Pagination>

export default meta
type Story = StoryObj<typeof meta>

export const FirstPage: Story = {}

export const MiddlePage: Story = { args: { page: 3, pages: 5, total: 92 } }

export const LastPage: Story = { args: { page: 2 } }

function InteractivePagination() {
  const [page, setPage] = useState(1)
  return <Pagination page={page} pages={5} pageSize={20} total={92} onPageChange={setPage} />
}

/** Clickable: Previous/Next update the range and disable at the ends. */
export const Interactive: Story = {
  render: () => <InteractivePagination />,
}
