import { ChevronLeft, ChevronRight } from 'lucide-react'

import { Button } from './Button'

interface PaginationProps {
  page: number
  pages: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
}

export function Pagination({ page, pages, pageSize, total, onPageChange }: PaginationProps) {
  if (total === 0) {
    return null
  }

  // "21–35 of 35" says both where you are and how much is left, which a bare
  // "page 2 of 2" doesn't.
  const first = (page - 1) * pageSize + 1
  const last = Math.min(page * pageSize, total)

  return (
    <nav
      aria-label="Pagination"
      className="flex items-center justify-between gap-4 border-t border-line px-5 py-3 sm:px-6"
    >
      <p className="text-sm text-muted tabular-nums">
        <span className="font-semibold text-ink">
          {first}–{last}
        </span>{' '}
        of {total}
      </p>
      <div className="flex gap-2">
        <Button
          variant="secondary"
          size="sm"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          aria-label="Previous page"
        >
          <ChevronLeft className="h-4 w-4" aria-hidden="true" />
          <span className="max-sm:hidden">Previous</span>
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= pages}
          aria-label="Next page"
        >
          <span className="max-sm:hidden">Next</span>
          <ChevronRight className="h-4 w-4" aria-hidden="true" />
        </Button>
      </div>
    </nav>
  )
}
