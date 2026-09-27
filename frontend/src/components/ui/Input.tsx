import { forwardRef, type InputHTMLAttributes } from 'react'

import { FIELD_ERROR, FIELD_LABEL, fieldControl } from './fieldStyles'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  /** Visible label, linked to the control. */
  label: string
  /** Validation message; marks the field invalid and is announced. */
  error?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, error, id, className = '', ...props },
  ref,
) {
  const inputId = id ?? props.name
  const errorId = error ? `${inputId}-error` : undefined

  return (
    <div className="space-y-1.5">
      <label htmlFor={inputId} className={FIELD_LABEL}>
        {label}
      </label>
      <input
        ref={ref}
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={errorId}
        className={`${fieldControl(Boolean(error))} ${className}`}
        {...props}
      />
      {error && (
        <p id={errorId} className={FIELD_ERROR} role="alert">
          {error}
        </p>
      )}
    </div>
  )
})
