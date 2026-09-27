// Shared by Input and Select so the two controls are visually identical.
export const FIELD_LABEL = 'block text-label font-semibold text-ink-soft'

export function fieldControl(hasError: boolean, compact = false): string {
  const size = compact ? 'h-8 px-2 text-label' : 'h-10 px-3 text-sm'
  return `block ${size} w-full rounded-control border bg-sheet text-ink placeholder:text-muted transition-colors focus:outline-none focus:border-progress focus:ring-2 focus:ring-progress/25 disabled:bg-wash disabled:text-faint ${
    hasError ? 'border-late' : 'border-line-strong hover:border-muted'
  }`
}

export const FIELD_ERROR = 'text-label font-medium text-late'
