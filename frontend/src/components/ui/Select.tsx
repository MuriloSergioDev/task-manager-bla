import { forwardRef, type ReactNode, type SelectHTMLAttributes } from 'react'

import { FIELD_ERROR, FIELD_LABEL, fieldControl } from './fieldStyles'

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  /** Visible label. Pass `""` inside rows and give an `aria-label` instead. */
  label: string
  /** Validation message; marks the field invalid and is announced. */
  error?: string
  /** Smaller control for use inside dense rows rather than forms. */
  compact?: boolean
  children: ReactNode
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { label, error, compact = false, id, className = '', children, ...props },
  ref,
) {
  const selectId = id ?? props.name

  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={selectId} className={FIELD_LABEL}>
          {label}
        </label>
      )}
      <select
        ref={ref}
        id={selectId}
        aria-invalid={error ? true : undefined}
        className={`${fieldControl(Boolean(error), compact)} pr-8 ${className}`}
        {...props}
      >
        {children}
      </select>
      {error && (
        <p className={FIELD_ERROR} role="alert">
          {error}
        </p>
      )}
    </div>
  )
})
