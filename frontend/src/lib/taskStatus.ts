import type { TaskStatus } from '../types/task'

/** User-facing names for each status, shared by the badge and the filter. */
export const STATUS_LABELS: Record<TaskStatus, string> = {
  TODO: 'To do',
  IN_PROGRESS: 'In progress',
  COMPLETED: 'Done',
}

/** Narrows untrusted input (e.g. a URL parameter) to a known status.
 *  `Object.hasOwn`, not `in`: `in` would also accept inherited keys such as
 *  "toString". */
export function isTaskStatus(value: string | null): value is TaskStatus {
  return value !== null && Object.hasOwn(STATUS_LABELS, value)
}
