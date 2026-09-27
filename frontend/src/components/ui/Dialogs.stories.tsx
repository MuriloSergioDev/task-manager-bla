import type { Meta, StoryObj } from '@storybook/react-vite'
import { useState, type ReactNode } from 'react'

import { Button } from './Button'
import { ConfirmDialog } from './ConfirmDialog'
import { Input } from './Input'
import { Modal } from './Modal'
import { StatusBadge } from './StatusBadge'

// Stories open the dialog straight away but keep it closable and re-openable,
// so Escape, backdrop click and focus return can be tried by hand.
function Opener({
  label,
  children,
}: {
  label: string
  children: (close: () => void, isOpen: boolean) => ReactNode
}) {
  const [isOpen, setIsOpen] = useState(true)
  return (
    <div className="p-6">
      <Button variant="secondary" onClick={() => setIsOpen(true)}>
        {label}
      </Button>
      {children(() => setIsOpen(false), isOpen)}
    </div>
  )
}

const meta = {
  title: 'Components/Dialogs',
  component: Modal,
  // Dialogs cover the viewport, so on the docs page each story renders in
  // its own frame rather than inline over the page.
  parameters: { layout: 'fullscreen', docs: { story: { inline: false, height: '460px' } } },
  args: { isOpen: true, title: 'New task', onClose: () => {}, children: null },
} satisfies Meta<typeof Modal>

export default meta
type Story = StoryObj<typeof meta>

export const FormDialog: Story = {
  render: () => (
    <Opener label="Open dialog">
      {(close, isOpen) => (
        <Modal isOpen={isOpen} onClose={close} title="New task">
          <div className="space-y-5">
            <Input label="Title" name="story-title" />
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={close}>
                Cancel
              </Button>
              <Button onClick={close}>Create task</Button>
            </div>
          </div>
        </Modal>
      )}
    </Opener>
  ),
}

/** While an action is in flight the dialog can't be dismissed. */
export const PreventClose: Story = {
  render: () => (
    <Modal isOpen onClose={() => {}} title="Deleting…" preventClose>
      <p className="text-sm text-muted">The close button, Escape and backdrop click are all disabled.</p>
    </Modal>
  ),
}

const taskPreview = (
  <div className="flex items-center gap-3 rounded-control border border-line bg-wash px-3 py-2.5">
    <p className="min-w-0 flex-1 truncate text-sm font-semibold text-ink">Renew SSL certificate</p>
    <StatusBadge status="TODO" />
  </div>
)

const DELETE_COPY = {
  title: 'Delete this task?',
  description: "It's removed for you and for anyone it's assigned to. This can't be undone.",
  confirmLabel: 'Delete task',
}

/** Destructive confirm: Cancel takes initial focus so a stray Enter is safe. */
export const ConfirmDanger: Story = {
  render: () => (
    <Opener label="Delete task">
      {(close, isOpen) => (
        <ConfirmDialog isOpen={isOpen} {...DELETE_COPY} onCancel={close} onConfirm={close}>
          {taskPreview}
        </ConfirmDialog>
      )}
    </Opener>
  ),
}

export const ConfirmPrimary: Story = {
  render: () => (
    <ConfirmDialog
      isOpen
      variant="primary"
      title="Reopen this task?"
      description="It moves back to To do and its completion date is cleared."
      confirmLabel="Reopen task"
      onCancel={() => {}}
      onConfirm={() => {}}
    />
  ),
}

export const ConfirmWithError: Story = {
  render: () => (
    <ConfirmDialog
      isOpen
      {...DELETE_COPY}
      errorMessage="The task couldn't be deleted. Check your connection and try again."
      onCancel={() => {}}
      onConfirm={() => {}}
    >
      {taskPreview}
    </ConfirmDialog>
  ),
}

export const ConfirmInProgress: Story = {
  render: () => (
    <ConfirmDialog isOpen isConfirming {...DELETE_COPY} onCancel={() => {}} onConfirm={() => {}}>
      {taskPreview}
    </ConfirmDialog>
  ),
}
