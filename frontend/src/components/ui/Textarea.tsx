import { forwardRef, type TextareaHTMLAttributes } from 'react'

import { FIELD_ERROR, FIELD_LABEL, fieldControl } from './fieldStyles'

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  /** Visible label, linked to the control. */
  label: string
  /** Validation message; marks the field invalid and is announced. */
  error?: string
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(function Textarea(
  { label, error, id, className = '', rows = 3, ...props },
  ref,
) {
  const textareaId = id ?? props.name

  return (
    <div className="space-y-1.5">
      <label htmlFor={textareaId} className={FIELD_LABEL}>
        {label}
      </label>
      <textarea
        ref={ref}
        id={textareaId}
        rows={rows}
        aria-invalid={error ? true : undefined}
        // fieldControl sets a single-line height; a textarea sizes by rows.
        className={`${fieldControl(Boolean(error))} h-auto resize-y py-2 leading-relaxed ${className}`}
        {...props}
      />
      {error && (
        <p className={FIELD_ERROR} role="alert">
          {error}
        </p>
      )}
    </div>
  )
})
