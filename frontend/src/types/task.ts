export type TaskStatus = 'TODO' | 'IN_PROGRESS' | 'COMPLETED'

export interface Task {
  id: string
  title: string
  description: string | null
  status: TaskStatus
  due_date: string | null
  completed_at: string | null
  owner_id: string
  assigned_to: string | null
  created_at: string
  updated_at: string
}

export interface TaskListResponse {
  items: Task[]
  page: number
  page_size: number
  total: number
  pages: number
}

export interface TaskCreateInput {
  title: string
  description?: string | null
  due_date?: string | null
  assigned_to?: string | null
}

export interface TaskUpdateInput {
  title?: string
  description?: string | null
  due_date?: string | null
  status?: TaskStatus
  assigned_to?: string | null
}

export interface TaskFilterValues {
  status?: TaskStatus
  dueDateFrom?: string
  dueDateTo?: string
}
