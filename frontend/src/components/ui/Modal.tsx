import { X } from 'lucide-react'
import { useEffect, useId, useRef, type MouseEvent, type ReactNode } from 'react'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: ReactNode
  /** Hides the close button and ignores backdrop clicks/Escape -- for use
   *  while an in-flight action (e.g. a delete) shouldn't be interrupted. */
  preventClose?: boolean
}

export function Modal({ isOpen, onClose, title, children, preventClose = false }: ModalProps) {
  const titleId = useId()
  const panelRef = useRef<HTMLDivElement>(null)
  const previouslyFocused = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (!isOpen) return

    previouslyFocused.current = document.activeElement as HTMLElement | null

    // A child (e.g. ConfirmDialog's Cancel button) may already have claimed
    // focus via `autoFocus`, which runs before this effect -- only fall back
    // to the panel itself if nothing inside did.
    if (!panelRef.current?.contains(document.activeElement)) {
      panelRef.current?.focus()
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !preventClose) {
        onClose()
      }
    }
    document.addEventListener('keydown', handleKeyDown)

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      previouslyFocused.current?.focus?.()
    }
  }, [isOpen, preventClose, onClose])

  if (!isOpen) return null

  const stopPropagation = (event: MouseEvent) => event.stopPropagation()
  const handleBackdropClick = () => {
    if (!preventClose) onClose()
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/45 p-4 animate-modal-fade max-sm:items-end max-sm:p-0"
      onClick={handleBackdropClick}
    >
      {/* max-h-[92dvh]: a viewport constraint (keep the panel scrollable on
          short screens), not a design value, so it isn't a token. */}
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className="max-h-[92dvh] w-full max-w-md overflow-y-auto rounded-sheet bg-sheet p-6 shadow-dialog animate-modal-in focus:outline-none max-sm:rounded-b-none sm:p-7"
        onClick={stopPropagation}
      >
        <div className="mb-5 flex items-center justify-between">
          <h2 id={titleId} className="text-xl font-bold tracking-tight text-ink">
            {title}
          </h2>
          {!preventClose && (
            <button
              type="button"
              onClick={onClose}
              className="-mr-1 -mt-1 rounded-control p-1.5 text-muted transition-colors hover:bg-ink/5 hover:text-ink focus:outline-none focus-visible:ring-2 focus-visible:ring-progress"
              aria-label="Close"
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          )}
        </div>
        {children}
      </div>
    </div>
  )
}
