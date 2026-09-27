import type { ButtonHTMLAttributes } from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost'
type ButtonSize = 'md' | 'sm' | 'icon'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** `primary`: the one main action in a view. `secondary`: everything else.
   *  `danger`: confirming something destructive. `ghost`: low-emphasis
   *  actions in dense rows and toolbars. */
  variant?: ButtonVariant
  /** `md` for forms and page actions, `sm` inside rows, `icon` for icon-only
   *  buttons (which must have an `aria-label`). */
  size?: ButtonSize
}

const variantClasses: Record<ButtonVariant, string> = {
  primary: 'bg-ink text-sheet hover:bg-ink-soft disabled:bg-faint',
  secondary:
    'bg-sheet text-ink ring-1 ring-inset ring-line-strong hover:bg-wash disabled:text-faint',
  danger: 'bg-late text-sheet hover:bg-late/90 disabled:bg-late/50',
  ghost: 'bg-transparent text-muted hover:bg-ink/5 hover:text-ink',
}

const sizeClasses: Record<ButtonSize, string> = {
  md: 'h-10 px-4 text-sm',
  sm: 'h-8 px-3 text-label',
  // Square, for icon-only buttons (which must carry an aria-label).
  icon: 'h-8 w-8 shrink-0',
}

export function Button({
  variant = 'primary',
  size = 'md',
  className = '',
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-1.5 rounded-control font-semibold whitespace-nowrap transition-colors duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-progress focus-visible:ring-offset-2 focus-visible:ring-offset-sheet disabled:cursor-not-allowed ${sizeClasses[size]} ${variantClasses[variant]} ${className}`}
      {...props}
    />
  )
}
