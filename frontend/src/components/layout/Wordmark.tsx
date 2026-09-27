/** The date-stub mark (a calendar leaf with a check) plus the product name --
 *  the same motif the task list uses for due dates, and the favicon. */
export function Wordmark({ size = 'md' }: { size?: 'md' | 'lg' }) {
  const mark = size === 'lg' ? 'h-9 w-9' : 'h-7 w-7'
  const text = size === 'lg' ? 'text-2xl' : 'text-brand'

  return (
    <span className="inline-flex items-center gap-2.5">
      <svg viewBox="0 0 32 32" className={`shrink-0 ${mark}`} aria-hidden="true">
        <rect x="3" y="3" width="26" height="26" rx="5" fill="var(--color-ink)" />
        <path d="M3 8a5 5 0 0 1 5-5h16a5 5 0 0 1 5 5v3H3z" fill="var(--color-late)" />
        <path
          d="M10 19.5l4 4 8-9"
          fill="none"
          stroke="var(--color-sheet)"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span className={`font-extrabold tracking-heading text-ink ${text}`}>Task Manager</span>
    </span>
  )
}
