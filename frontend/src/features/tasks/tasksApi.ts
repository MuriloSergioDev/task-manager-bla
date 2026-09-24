import { apiClient } from '../../lib/apiClient'
import type { Task, TaskCreateInput, TaskListResponse, TaskUpdateInput } from '../../types/task'
import type { TaskQueryParams } from './taskFilterState'

export async function fetchTasks(params: TaskQueryParams): Promise<TaskListResponse> {
  const { data } = await apiClient.get<TaskListResponse>('/api/v1/tasks', { params })
  return data
}

export async function createTask(input: TaskCreateInput): Promise<Task> {
  const { data } = await apiClient.post<Task>('/api/v1/tasks', input)
  return data
}

export async function updateTask(taskId: string, input: TaskUpdateInput): Promise<Task> {
  const { data } = await apiClient.patch<Task>(`/api/v1/tasks/${taskId}`, input)
  return data
}

export async function deleteTask(taskId: string): Promise<void> {
  await apiClient.delete(`/api/v1/tasks/${taskId}`)
}

export async function completeTask(taskId: string): Promise<Task> {
  const { data } = await apiClient.post<Task>(`/api/v1/tasks/${taskId}/complete`)
  return data
}

export async function assignTask(taskId: string, assignedTo: string | null): Promise<Task> {
  const { data } = await apiClient.post<Task>(`/api/v1/tasks/${taskId}/assign`, {
    assigned_to: assignedTo,
  })
  return data
}
