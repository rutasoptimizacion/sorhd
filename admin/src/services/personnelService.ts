import apiClient from './api'
import type {
  Personnel,
  PersonnelCreate,
  PersonnelUpdate,
  PaginatedResponse,
  PaginationParams,
} from '@/types'

export const personnelService = {
  // Get all personnel with pagination
  getAll: async (params?: PaginationParams & { is_active?: boolean }): Promise<PaginatedResponse<Personnel>> => {
    const response = await apiClient.get<PaginatedResponse<Personnel>>('/personnel', {
      params: {
        skip: params?.skip || 0,
        limit: params?.limit || 100,
        is_active: params?.is_active,
      },
    })
    return response.data
  },

  // Get personnel by ID
  getById: async (id: number): Promise<Personnel> => {
    const response = await apiClient.get<Personnel>(`/personnel/${id}`)
    return response.data
  },

  // Create personnel
  create: async (data: PersonnelCreate): Promise<Personnel> => {
    const response = await apiClient.post<Personnel>('/personnel', data)
    return response.data
  },

  // Update personnel
  update: async (id: number, data: PersonnelUpdate): Promise<Personnel> => {
    const response = await apiClient.put<Personnel>(`/personnel/${id}`, data)
    return response.data
  },

  // Delete personnel
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/personnel/${id}`)
  },
}
