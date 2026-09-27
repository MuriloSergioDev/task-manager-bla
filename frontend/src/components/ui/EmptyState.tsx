import type { ReactNode } from 'react'

interface EmptyStateProps {
  title: string
  description?: string
  /** The next step, usually a Button: an empty screen should invite action. */
  action?: ReactNode
  /** `error` when the list couldn't load, rather than having nothing in it. */
  tone?: 'neutral' | 'error'
}

export function EmptyState({ title, description, action, tone = 'neutral' }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-start gap-4 px-5 py-14 sm:px-8">
      <div className="max-w-md">
        <p className={`text-lg font-bold tracking-tight ${tone === 'error' ? 'text-late' : 'text-ink'}`}>
          {title}
        </p>
        {description && <p className="mt-1 text-sm leading-relaxed text-muted">{description}</p>}
      </div>
      {action}
    </div>
  )
}
