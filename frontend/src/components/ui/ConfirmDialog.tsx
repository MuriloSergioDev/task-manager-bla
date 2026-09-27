import type { ReactNode } from 'react'

import { Alert } from './Alert'
import { Button } from './Button'
import { Modal } from './Modal'
import { Spinner } from './Spinner'

interface ConfirmDialogProps {
  isOpen: boolean
  title: string
  description: string
  /** Optional context about exactly what's being acted on -- e.g. a small
   *  preview of the specific record -- rendered between the description
   *  and the error message/actions. */
  children?: ReactNode
  confirmLabel?: string
  cancelLabel?: string
  /** `danger` gives Cancel the initial focus, so a stray Enter can't confirm. */
  variant?: 'danger' | 'primary'
  /** While true, shows a spinner and blocks closing until the action settles. */
  isConfirming?: boolean
  errorMessage?: string
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmDialog({
  isOpen,
  title,
  description,
  children,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'danger',
  isConfirming = false,
  errorMessage,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <Modal isOpen={isOpen} onClose={onCancel} title={title} preventClose={isConfirming}>
      <p className="text-sm leading-relaxed text-muted">{description}</p>
      {children && <div className="mt-4">{children}</div>}
      {errorMessage && (
        <Alert tone="error" className="mt-4">{errorMessage}</Alert>
      )}

      <div className="mt-6 flex justify-end gap-2">
        {/* Cancel gets the initial focus for a destructive confirm -- a stray
            Enter keypress should never delete something. */}
        <Button
          type="button"
          variant="secondary"
          onClick={onCancel}
          disabled={isConfirming}
          autoFocus={variant === 'danger'}
        >
          {cancelLabel}
        </Button>
        <Button
          type="button"
          variant={variant}
          onClick={onConfirm}
          disabled={isConfirming}
          autoFocus={variant !== 'danger'}
        >
          {isConfirming && <Spinner className="h-4 w-4" />}
          {confirmLabel}
        </Button>
      </div>
    </Modal>
  )
}
