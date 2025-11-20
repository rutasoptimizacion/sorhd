import apiClient from './api'
import type { CareType, CareTypeCreate, CareTypeUpdate, PaginatedResponse, PaginationParams } from '@/types'

export const careTypeService = {
  // Get all care types with pagination
  getAll: async (params?: PaginationParams): Promise<PaginatedResponse<CareType>> => {
    const response = await apiClient.get<PaginatedResponse<CareType>>('/care-types', {
      params: {
        skip: params?.skip || 0,
        limit: params?.limit || 100,
      },
    })
    return response.data
  },

  // Get care type by ID
  getById: async (id: number): Promise<CareType> => {
    const response = await apiClient.get<CareType>(`/care-types/${id}`)
    return response.data
  },

  // Create care type
  create: async (data: CareTypeCreate): Promise<CareType> => {
    const response = await apiClient.post<CareType>('/care-types', data)
    return response.data
  },

  // Update care type
  update: async (id: number, data: CareTypeUpdate): Promise<CareType> => {
    const response = await apiClient.put<CareType>(`/care-types/${id}`, data)
    return response.data
  },

  // Delete care type
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/care-types/${id}`)
  },
}
