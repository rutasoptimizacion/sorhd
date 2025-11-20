import apiClient from './api'
import type {
  Route,
  RouteCreate,
  RouteUpdate,
  RouteListParams,
  RouteListResponse,
  OptimizationRequest,
  OptimizationResponse,
  Visit,
  VisitUpdate,
  RouteWithDetails,
} from '@/types'

export const routeService = {
  // Optimize routes - main operation for route planning
  optimize: async (data: OptimizationRequest): Promise<OptimizationResponse> => {
    const response = await apiClient.post<OptimizationResponse>('/routes/optimize', data)
    return response.data
  },

  // Get all routes with pagination and filters
  getAll: async (params?: RouteListParams): Promise<RouteListResponse> => {
    const response = await apiClient.get<RouteListResponse>('/routes', {
      params: {
        page: params?.page || 1,
        page_size: params?.page_size || 20,
        date: params?.date,
        status: params?.status,
        vehicle_id: params?.vehicle_id,
      },
    })
    return response.data
  },

  // Get route by ID
  getById: async (id: number): Promise<Route> => {
    const response = await apiClient.get<Route>(`/routes/${id}`)
    return response.data
  },

  // Get route with full details (including visits, vehicle, personnel)
  getByIdWithDetails: async (id: number): Promise<RouteWithDetails> => {
    const response = await apiClient.get<RouteWithDetails>(`/routes/${id}`)
    return response.data
  },

  // Get active routes
  getActive: async (): Promise<Route[]> => {
    const response = await apiClient.get<Route[]>('/routes/active')
    return response.data
  },

  // Create route (manual creation, not through optimization)
  create: async (data: RouteCreate): Promise<Route> => {
    const response = await apiClient.post<Route>('/routes', data)
    return response.data
  },

  // Update route status
  updateStatus: async (id: number, data: RouteUpdate): Promise<Route> => {
    const response = await apiClient.patch<Route>(`/routes/${id}/status`, data)
    return response.data
  },

  // Delete/cancel route
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/routes/${id}`)
  },

  // Get visits for a route
  getVisits: async (routeId: number): Promise<Visit[]> => {
    const response = await apiClient.get<Visit[]>(`/routes/${routeId}/visits`)
    return response.data
  },

  // Update visit status
  updateVisit: async (routeId: number, visitId: number, data: VisitUpdate): Promise<Visit> => {
    const response = await apiClient.patch<Visit>(`/routes/${routeId}/visits/${visitId}`, data)
    return response.data
  },
}
