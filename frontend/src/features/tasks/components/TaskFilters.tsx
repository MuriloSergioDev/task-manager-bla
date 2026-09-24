import { Button } from '../../../components/ui/Button'
import { Input } from '../../../components/ui/Input'
import { Select } from '../../../components/ui/Select'
import type { TaskFilterValues, TaskStatus } from '../../../types/task'

const STATUS_OPTIONS: { value: TaskStatus; label: string }[] = [
  { value: 'TODO', label: 'To do' },
  { value: 'IN_PROGRESS', label: 'In progress' },
  { value: 'COMPLETED', label: 'Completed' },
]

interface TaskFiltersProps {
  filters: TaskFilterValues
  onChange: (partial: Partial<TaskFilterValues>) => void
}

export function TaskFilters({ filters, onChange }: TaskFiltersProps) {
  return (
    <div className="flex flex-wrap items-end gap-4 rounded-lg bg-white p-4 shadow-sm">
      <div className="w-40">
        <Select
          label="Status"
          name="status"
          value={filters.status ?? ''}
          onChange={(event) =>
            onChange({ status: (event.target.value || undefined) as TaskStatus | undefined })
          }
        >
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
      </div>
      <div className="w-40">
        <Input
          label="Due from"
          type="date"
          name="dueDateFrom"
          value={filters.dueDateFrom ?? ''}
          onChange={(event) => onChange({ dueDateFrom: event.target.value || undefined })}
        />
      </div>
      <div className="w-40">
        <Input
          label="Due to"
          type="date"
          name="dueDateTo"
          value={filters.dueDateTo ?? ''}
          onChange={(event) => onChange({ dueDateTo: event.target.value || undefined })}
        />
      </div>
      <Button
        variant="ghost"
        type="button"
        onClick={() => onChange({ status: undefined, dueDateFrom: undefined, dueDateTo: undefined })}
      >
        Clear filters
      </Button>
    </div>
  )
}
