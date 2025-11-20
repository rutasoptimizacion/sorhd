import apiClient from './api'
import type {
  Vehicle,
  VehicleCreate,
  VehicleUpdate,
  VehicleStatus,
  PaginatedResponse,
  PaginationParams,
} from '@/types'

export const vehicleService = {
  // Get all vehicles with pagination
  getAll: async (
    params?: PaginationParams & { is_active?: boolean; status?: VehicleStatus }
  ): Promise<PaginatedResponse<Vehicle>> => {
    const response = await apiClient.get<PaginatedResponse<Vehicle>>('/vehicles', {
      params: {
        skip: params?.skip || 0,
        limit: params?.limit || 100,
        is_active: params?.is_active,
        status: params?.status,
      },
    })
    return response.data
  },

  // Get vehicle by ID
  getById: async (id: number): Promise<Vehicle> => {
    const response = await apiClient.get<Vehicle>(`/vehicles/${id}`)
    return response.data
  },

  // Create vehicle
  create: async (data: VehicleCreate): Promise<Vehicle> => {
    const response = await apiClient.post<Vehicle>('/vehicles', data)
    return response.data
  },

  // Update vehicle
  update: async (id: number, data: VehicleUpdate): Promise<Vehicle> => {
    const response = await apiClient.put<Vehicle>(`/vehicles/${id}`, data)
    return response.data
  },

  // Delete vehicle
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/vehicles/${id}`)
  },
}
