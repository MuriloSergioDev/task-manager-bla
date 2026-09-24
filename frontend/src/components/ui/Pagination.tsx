import { Button } from './Button'

interface PaginationProps {
  page: number
  pages: number
  total: number
  onPageChange: (page: number) => void
}

export function Pagination({ page, pages, total, onPageChange }: PaginationProps) {
  if (total === 0) {
    return null
  }

  return (
    <div className="flex items-center justify-between border-t border-gray-200 px-2 py-3">
      <p className="text-sm text-gray-600">
        Page {page} of {pages} &middot; {total} task{total === 1 ? '' : 's'}
      </p>
      <div className="flex gap-2">
        <Button
          variant="secondary"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
        >
          Previous
        </Button>
        <Button
          variant="secondary"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= pages}
        >
          Next
        </Button>
      </div>
    </div>
  )
}
