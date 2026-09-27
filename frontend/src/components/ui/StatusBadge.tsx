import { useId } from 'react'

import { STATUS_LABELS } from '../../lib/taskStatus'
import type { TaskStatus } from '../../types/task'

const STATUS_TEXT: Record<TaskStatus, string> = {
  TODO: 'text-muted',
  IN_PROGRESS: 'text-progress',
  COMPLETED: 'text-done',
}

/** A ring that fills as work advances -- empty, half, checked -- so status
 *  reads as progress at a glance rather than as three arbitrary colours. */
export function StatusGlyph({ status, className = 'h-3.5 w-3.5' }: { status: TaskStatus; className?: string }) {
  // The check is cut out of the disc (a mask, not a painted stroke) so the
  // glyph reads on any background, including the selected filter segment.
  const maskId = useId()

  return (
    <svg viewBox="0 0 16 16" className={`shrink-0 ${className}`} aria-hidden="true">
      {status === 'COMPLETED' ? (
        <>
          <mask id={maskId}>
            <rect width="16" height="16" fill="white" />
            <path d="M4.8 8.3l2.1 2.1 4.3-4.6" fill="none" stroke="black" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          </mask>
          <circle cx="8" cy="8" r="7" fill="currentColor" mask={`url(#${maskId})`} />
        </>
      ) : (
        <>
          <circle cx="8" cy="8" r="6.25" fill="none" stroke="currentColor" strokeWidth="1.5" />
          {status === 'IN_PROGRESS' && <path d="M8 3.5a4.5 4.5 0 0 1 0 9z" fill="currentColor" />}
        </>
      )}
    </svg>
  )
}

export function StatusBadge({ status }: { status: TaskStatus }) {
  return (
    <span
      className={`inline-flex shrink-0 items-center gap-1.5 whitespace-nowrap text-label font-semibold ${STATUS_TEXT[status]}`}
    >
      <StatusGlyph status={status} />
      {STATUS_LABELS[status]}
    </span>
  )
}
