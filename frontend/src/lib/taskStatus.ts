import type { TaskStatus } from '../types/task'

/** User-facing names for each status, shared by the badge and the filter. */
export const STATUS_LABELS: Record<TaskStatus, string> = {
  TODO: 'To do',
  IN_PROGRESS: 'In progress',
  COMPLETED: 'Done',
}
