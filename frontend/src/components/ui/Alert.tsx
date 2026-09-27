import type { ReactNode } from 'react'

type AlertTone = 'error' | 'success'

const TONE_CLASSES: Record<AlertTone, string> = {
  error: 'bg-late-wash text-late',
  success: 'bg-done-wash text-done',
}

interface AlertProps {
  tone: AlertTone
  children: ReactNode
  /** Spacing only (e.g. `mt-4`); the alert's look comes from `tone`. */
  className?: string
}

/** An inline message about a whole form or action, as opposed to a field
 *  error. Errors are announced immediately (`alert`); confirmations
 *  politely (`status`). */
export function Alert({ tone, children, className = '' }: AlertProps) {
  return (
    <p
      role={tone === 'error' ? 'alert' : 'status'}
      className={`rounded-control px-3 py-2.5 text-sm font-medium ${TONE_CLASSES[tone]} ${className}`}
    >
      {children}
    </p>
  )
}
