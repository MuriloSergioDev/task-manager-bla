import { X } from 'lucide-react'

import { Button, Input, StatusGlyph } from '../../../components/ui'
import { STATUS_LABELS } from '../../../lib/taskStatus'
import type { TaskFilterValues, TaskStatus } from '../../../types/task'

const STATUSES: TaskStatus[] = ['TODO', 'IN_PROGRESS', 'COMPLETED']

interface TaskFiltersProps {
  filters: TaskFilterValues
  onChange: (partial: Partial<TaskFilterValues>) => void
}

export function TaskFilters({ filters, onChange }: TaskFiltersProps) {
  const hasActiveFilters = Boolean(filters.status || filters.dueDateFrom || filters.dueDateTo)

  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <StatusSegments
        value={filters.status}
        onChange={(status) => onChange({ status })}
      />

      {/* Two equal columns on phones; fixed-width fields in a row from sm up. */}
      <div className="grid grid-cols-2 items-end gap-3 sm:flex sm:flex-wrap">
        <div className="sm:w-40">
          <Input
            label="Due from"
            type="date"
            name="dueDateFrom"
            value={filters.dueDateFrom ?? ''}
            max={filters.dueDateTo}
            onChange={(event) => onChange({ dueDateFrom: event.target.value || undefined })}
          />
        </div>
        <div className="sm:w-40">
          <Input
            label="Due to"
            type="date"
            name="dueDateTo"
            value={filters.dueDateTo ?? ''}
            min={filters.dueDateFrom}
            onChange={(event) => onChange({ dueDateTo: event.target.value || undefined })}
          />
        </div>
        {hasActiveFilters && (
          <Button
            variant="ghost"
            type="button"
            className="col-span-2 justify-self-start"
            onClick={() => onChange({ status: undefined, dueDateFrom: undefined, dueDateTo: undefined })}
          >
            <X className="h-4 w-4" aria-hidden="true" />
            Clear filters
          </Button>
        )}
      </div>
    </div>
  )
}

interface StatusSegmentsProps {
  value: TaskStatus | undefined
  onChange: (status: TaskStatus | undefined) => void
}

/** Status filter as one-click segments rather than a dropdown: there are
 *  only four choices, and seeing them all makes the current view obvious.
 *  Native radios underneath give arrow-key navigation for free. */
function StatusSegments({ value, onChange }: StatusSegmentsProps) {
  const options: { key: string; status: TaskStatus | undefined; label: string }[] = [
    { key: 'ALL', status: undefined, label: 'All' },
    ...STATUSES.map((status) => ({ key: status, status, label: STATUS_LABELS[status] })),
  ]

  return (
    <fieldset className="min-w-0">
      <legend className="sr-only">Status</legend>
      <div className="flex overflow-x-auto rounded-control border border-line-strong bg-sheet p-0.5">
        {options.map((option) => {
          const isSelected = value === option.status
          return (
            <label
              key={option.key}
              className={`flex h-9 shrink-0 cursor-pointer items-center gap-1.5 rounded-segment px-3 text-sm font-semibold whitespace-nowrap transition-colors has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-progress ${
                isSelected ? 'bg-ink text-sheet' : 'text-muted hover:bg-wash hover:text-ink'
              }`}
            >
              <input
                type="radio"
                name="status"
                className="sr-only"
                checked={isSelected}
                onChange={() => onChange(option.status)}
              />
              {option.status && <StatusGlyph status={option.status} />}
              {option.label}
            </label>
          )
        })}
      </div>
    </fieldset>
  )
}
