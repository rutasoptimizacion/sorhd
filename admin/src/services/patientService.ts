import apiClient from './api'
import type { Patient, PatientCreate, PatientUpdate, PaginatedResponse, PaginationParams, Location } from '@/types'

export interface GeocodePreviewRequest {
  address: string
  country?: string
}

export interface GeocodePreviewResponse {
  latitude: number
  longitude: number
  formatted_address: string
  confidence?: number
  address_components?: Record<string, any>
}

export const patientService = {
  // Get all patients with pagination
  getAll: async (params?: PaginationParams): Promise<PaginatedResponse<Patient>> => {
    const response = await apiClient.get<PaginatedResponse<Patient>>('/patients', {
      params: {
        skip: params?.skip || 0,
        limit: params?.limit || 100,
      },
    })
    return response.data
  },

  // Get patient by ID
  getById: async (id: number): Promise<Patient> => {
    const response = await apiClient.get<Patient>(`/patients/${id}`)
    return response.data
  },

  // Create patient
  create: async (data: PatientCreate): Promise<Patient> => {
    const response = await apiClient.post<Patient>('/patients', data)
    return response.data
  },

  // Update patient
  update: async (id: number, data: PatientUpdate): Promise<Patient> => {
    const response = await apiClient.put<Patient>(`/patients/${id}`, data)
    return response.data
  },

  // Delete patient
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/patients/${id}`)
  },

  // Geocode address preview (without saving)
  geocodePreview: async (address: string, country: string = 'CL'): Promise<GeocodePreviewResponse> => {
    const response = await apiClient.post<GeocodePreviewResponse>('/patients/geocode-preview', {
      address,
      country,
    })
    return response.data
  },
}
