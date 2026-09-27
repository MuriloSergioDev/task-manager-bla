import { Select } from '../../../components/ui'
import { useUsers } from '../hooks/useUsers'

interface AssigneeSelectProps {
  value: string
  onChange: (value: string) => void
  label?: string
  error?: string
  /** Needed when several selects render on one page (one per list row) --
   *  otherwise they'd all fall back to the same `name`-derived DOM id. */
  id?: string
  ariaLabel?: string
  compact?: boolean
}

export function AssigneeSelect({
  value,
  onChange,
  label = 'Assignee',
  error,
  id,
  ariaLabel,
  compact = false,
}: AssigneeSelectProps) {
  const { data: users, isLoading } = useUsers()

  return (
    <Select
      label={label}
      aria-label={ariaLabel ?? (label || 'Assignee')}
      id={id}
      compact={compact}
      name="assigned_to"
      value={value}
      onChange={(event) => onChange(event.target.value)}
      error={error}
      disabled={isLoading}
    >
      <option value="">Unassigned</option>
      {users?.map((user) => (
        <option key={user.id} value={user.id}>
          {user.email}
        </option>
      ))}
    </Select>
  )
}
