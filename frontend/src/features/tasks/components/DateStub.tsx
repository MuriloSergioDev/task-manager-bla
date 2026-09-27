import type { Task } from '../../../types/task'
import { dueDateParts, formatDueDate, getDueState, type DueState } from '../dueDateStatus'

type DatedState = Exclude<DueState, 'none'>

// band = the "binding" strip across the top of the leaf.
const STUB_STYLES: Record<DatedState, { stub: string; band: string }> = {
  overdue: { stub: 'border-late/40 bg-late-wash text-late', band: 'bg-late text-sheet' },
  today: { stub: 'border-ink bg-ink text-sheet', band: 'bg-ink-soft text-sheet' },
  upcoming: { stub: 'border-line-strong bg-sheet text-ink', band: 'bg-wash text-muted' },
  done: { stub: 'border-line text-muted', band: 'text-muted' },
}

const SR_PREFIX: Record<DatedState, string> = {
  overdue: 'Overdue, was due',
  today: 'Due today,',
  upcoming: 'Due',
  done: 'Was due',
}

/** A tear-off calendar leaf showing when a task is due. It leads each row
 *  because "when" is what people scan a work queue by. */
export function DateStub({ task }: { task: Task }) {
  const state = getDueState(task)

  if (task.due_date === null || state === 'none') {
    return (
      <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-control border border-dashed border-line-strong text-faint">
        <span aria-hidden="true">—</span>
        <span className="sr-only">No due date</span>
      </div>
    )
  }

  const { month, day, year } = dueDateParts(task.due_date)
  const styles = STUB_STYLES[state]

  return (
    <div
      className={`flex h-14 w-14 shrink-0 flex-col overflow-hidden rounded-control border text-center ${styles.stub}`}
    >
      <span className="sr-only">
        {SR_PREFIX[state]} {formatDueDate(task.due_date)}
      </span>
      <span aria-hidden="true" className={`py-0.5 text-micro font-bold ${styles.band}`}>
        {month}
        {year && ` ’${year.slice(2)}`}
      </span>
      <span
        aria-hidden="true"
        className="flex flex-1 items-center justify-center text-figure font-extrabold tracking-tight tabular-nums"
      >
        {day}
      </span>
    </div>
  )
}
