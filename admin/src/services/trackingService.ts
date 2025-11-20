/**
 * Tracking Service - REST API calls for tracking and monitoring
 */

import { apiClient } from './api'

// Types
export interface VehicleLocation {
  vehicle_id: number
  latitude: number
  longitude: number
  timestamp: string
  speed?: number
  heading?: number
  accuracy?: number
}

export interface VisitInfo {
  visit_id: number
  case_id: number
  sequence: number
  status: string
  patient_name: string
  address: string
  latitude: number
  longitude: number
  estimated_arrival?: string
  estimated_departure?: string
  actual_arrival?: string
  actual_departure?: string
  time_window_start?: string
  time_window_end?: string
}

export interface RouteProgress {
  route_id: number
  total_visits: number
  completed_visits: number
  in_progress_visits: number
  pending_visits: number
  total_distance_km: number
  completion_percentage: number
  current_visit?: VisitInfo
  next_visit?: VisitInfo
}

export interface ActiveRoute {
  route_id: number
  vehicle_id: number
  vehicle_identifier: string
  date: string
  status: string
  total_visits: number
  completed_visits: number
  in_progress_visits: number
  pending_visits: number
  completion_percentage: number
  personnel: {
    personnel_id: number
    name: string
    role?: string
  }[]
  current_location?: {
    latitude: number
    longitude: number
    timestamp: string
  }
}

export interface ETAResponse {
  visit_id: number
  eta_minutes: number
  arrival_time: string
  distance_km: number
  traffic_multiplier: number
  calculated_at: string
}

export interface DelayAlert {
  visit_id: number
  route_id: number
  severity: 'minor' | 'moderate' | 'severe'
  delay_minutes: number
  time_window_start?: string
  time_window_end?: string
  estimated_arrival: string
  message: string
}

export interface LocationHistory {
  vehicle_id: number
  locations: VehicleLocation[]
}

/**
 * Get active routes for a given date
 */
export const getActiveRoutes = async (date?: string): Promise<ActiveRoute[]> => {
  const params = date ? { route_date: date } : {}
  const response = await apiClient.get('/tracking/routes/active', { params })
  return response.data
}

/**
 * Get current location for a vehicle
 */
export const getVehicleLocation = async (vehicleId: number): Promise<VehicleLocation> => {
  const response = await apiClient.get(`/tracking/vehicle/${vehicleId}`)
  return response.data
}

/**
 * Get location history for a vehicle
 */
export const getVehicleLocationHistory = async (
  vehicleId: number,
  startTime?: string,
  endTime?: string
): Promise<LocationHistory> => {
  const params: any = {}
  if (startTime) params.start_time = startTime
  if (endTime) params.end_time = endTime

  const response = await apiClient.get(`/tracking/vehicle/${vehicleId}/history`, { params })
  return response.data
}

/**
 * Get progress for a specific route
 */
export const getRouteProgress = async (routeId: number): Promise<RouteProgress> => {
  const response = await apiClient.get(`/tracking/routes/${routeId}/progress`)
  return response.data
}

/**
 * Get ETA for a specific visit
 */
export const getVisitETA = async (visitId: number): Promise<ETAResponse> => {
  const response = await apiClient.get(`/tracking/visits/${visitId}/eta`)
  return response.data
}

/**
 * Get delay alerts for a route
 */
export const getRouteDelays = async (routeId: number): Promise<DelayAlert[]> => {
  const response = await apiClient.get(`/tracking/routes/${routeId}/delays`)
  return response.data
}

/**
 * Upload GPS location (for testing purposes only - normally done by mobile app)
 */
export const uploadLocation = async (
  vehicleId: number,
  latitude: number,
  longitude: number,
  speed?: number,
  heading?: number,
  accuracy?: number
): Promise<void> => {
  await apiClient.post('/tracking/location', {
    vehicle_id: vehicleId,
    latitude,
    longitude,
    speed,
    heading,
    accuracy
  })
}

// Export all types and functions
export default {
  getActiveRoutes,
  getVehicleLocation,
  getVehicleLocationHistory,
  getRouteProgress,
  getVisitETA,
  getRouteDelays,
  uploadLocation
}
