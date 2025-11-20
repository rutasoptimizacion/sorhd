import apiClient from './api'
import type {
  Case,
  CaseCreate,
  CaseUpdate,
  CaseStatus,
  CasePriority,
  PaginatedResponse,
  PaginationParams,
} from '@/types'

export const caseService = {
  // Get all cases with pagination
  getAll: async (
    params?: PaginationParams & {
      status?: CaseStatus
      priority?: CasePriority
      scheduled_date?: string
    }
  ): Promise<PaginatedResponse<Case>> => {
    const response = await apiClient.get<PaginatedResponse<Case>>('/cases', {
      params: {
        skip: params?.skip || 0,
        limit: params?.limit || 100,
        status: params?.status,
        priority: params?.priority,
        scheduled_date: params?.scheduled_date,
      },
    })
    return response.data
  },

  // Get case by ID
  getById: async (id: number): Promise<Case> => {
    const response = await apiClient.get<Case>(`/cases/${id}`)
    return response.data
  },

  // Create case
  create: async (data: CaseCreate): Promise<Case> => {
    const response = await apiClient.post<Case>('/cases', data)
    return response.data
  },

  // Update case
  update: async (id: number, data: CaseUpdate): Promise<Case> => {
    const response = await apiClient.put<Case>(`/cases/${id}`, data)
    return response.data
  },

  // Delete case
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/cases/${id}`)
  },
}
