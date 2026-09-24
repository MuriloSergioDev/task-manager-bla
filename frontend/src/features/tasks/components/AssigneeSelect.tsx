import { Select } from '../../../components/ui/Select'
import { useUsers } from '../hooks/useUsers'

interface AssigneeSelectProps {
  value: string
  onChange: (value: string) => void
  label?: string
  error?: string
}

export function AssigneeSelect({ value, onChange, label = 'Assignee', error }: AssigneeSelectProps) {
  const { data: users, isLoading } = useUsers()

  return (
    <Select
      label={label}
      aria-label={label || 'Assignee'}
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
