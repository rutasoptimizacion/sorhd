/**
 * Monitoring Redux Slice
 * Manages real-time monitoring state for vehicle tracking and route progress
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import type { ConnectionStatus } from '@/services/websocketService'
import type {
  ActiveRoute,
  VehicleLocation,
  DelayAlert,
  ETAResponse
} from '@/services/trackingService'

// State interface
export interface MonitoringState {
  // Connection status
  connectionStatus: ConnectionStatus

  // Active routes
  activeRoutes: ActiveRoute[]
  selectedRouteId: number | null
  selectedVehicleId: number | null

  // Vehicle locations (keyed by vehicle_id)
  vehicleLocations: Record<number, VehicleLocation>

  // Visit ETAs (keyed by visit_id)
  visitETAs: Record<number, ETAResponse>

  // Delay alerts (keyed by route_id)
  routeDelays: Record<number, DelayAlert[]>

  // Filters
  filters: {
    date: string // ISO date string
    status: 'all' | 'en_route' | 'at_visit' | 'delayed'
    vehicleIds: number[]
  }

  // UI state
  autoRefresh: boolean
  lastUpdate: string | null
  loading: boolean
  error: string | null
}

// Initial state
const today = new Date().toISOString().split('T')[0]

const initialState: MonitoringState = {
  connectionStatus: 'disconnected',
  activeRoutes: [],
  selectedRouteId: null,
  selectedVehicleId: null,
  vehicleLocations: {},
  visitETAs: {},
  routeDelays: {},
  filters: {
    date: today,
    status: 'all',
    vehicleIds: []
  },
  autoRefresh: true,
  lastUpdate: null,
  loading: false,
  error: null
}

// Slice
const monitoringSlice = createSlice({
  name: 'monitoring',
  initialState,
  reducers: {
    // Connection status
    setConnectionStatus: (state, action: PayloadAction<ConnectionStatus>) => {
      state.connectionStatus = action.payload
    },

    // Active routes
    setActiveRoutes: (state, action: PayloadAction<ActiveRoute[]>) => {
      state.activeRoutes = action.payload
      state.lastUpdate = new Date().toISOString()
      state.loading = false
      state.error = null
    },

    updateActiveRoute: (state, action: PayloadAction<ActiveRoute>) => {
      const index = state.activeRoutes.findIndex(r => r.route_id === action.payload.route_id)
      if (index !== -1) {
        state.activeRoutes[index] = action.payload
      } else {
        state.activeRoutes.push(action.payload)
      }
      state.lastUpdate = new Date().toISOString()
    },

    removeActiveRoute: (state, action: PayloadAction<number>) => {
      state.activeRoutes = state.activeRoutes.filter(r => r.route_id !== action.payload)
    },

    // Vehicle location updates
    updateVehicleLocation: (state, action: PayloadAction<{ vehicleId: number, location: VehicleLocation }>) => {
      const { vehicleId, location } = action.payload
      state.vehicleLocations[vehicleId] = location

      // Also update location in active routes
      const route = state.activeRoutes.find(r => r.vehicle_id === vehicleId)
      if (route) {
        route.current_location = {
          latitude: location.latitude,
          longitude: location.longitude,
          timestamp: location.timestamp
        }
      }

      state.lastUpdate = new Date().toISOString()
    },

    // Visit ETA updates
    updateVisitETA: (state, action: PayloadAction<ETAResponse>) => {
      state.visitETAs[action.payload.visit_id] = action.payload
      state.lastUpdate = new Date().toISOString()
    },

    // Delay alerts
    setRouteDelays: (state, action: PayloadAction<{ routeId: number, delays: DelayAlert[] }>) => {
      state.routeDelays[action.payload.routeId] = action.payload.delays
    },

    addDelayAlert: (state, action: PayloadAction<DelayAlert>) => {
      const routeId = action.payload.route_id
      if (!state.routeDelays[routeId]) {
        state.routeDelays[routeId] = []
      }

      // Check if alert already exists
      const existingIndex = state.routeDelays[routeId].findIndex(
        d => d.visit_id === action.payload.visit_id
      )

      if (existingIndex !== -1) {
        // Update existing alert
        state.routeDelays[routeId][existingIndex] = action.payload
      } else {
        // Add new alert
        state.routeDelays[routeId].push(action.payload)
      }

      state.lastUpdate = new Date().toISOString()
    },

    // Selection
    selectRoute: (state, action: PayloadAction<number | null>) => {
      state.selectedRouteId = action.payload
      if (action.payload) {
        const route = state.activeRoutes.find(r => r.route_id === action.payload)
        if (route) {
          state.selectedVehicleId = route.vehicle_id
        }
      }
    },

    selectVehicle: (state, action: PayloadAction<number | null>) => {
      state.selectedVehicleId = action.payload
    },

    // Filters
    setDateFilter: (state, action: PayloadAction<string>) => {
      state.filters.date = action.payload
    },

    setStatusFilter: (state, action: PayloadAction<'all' | 'en_route' | 'at_visit' | 'delayed'>) => {
      state.filters.status = action.payload
    },

    setVehicleFilter: (state, action: PayloadAction<number[]>) => {
      state.filters.vehicleIds = action.payload
    },

    resetFilters: (state) => {
      state.filters = {
        date: today,
        status: 'all',
        vehicleIds: []
      }
    },

    // Auto-refresh toggle
    setAutoRefresh: (state, action: PayloadAction<boolean>) => {
      state.autoRefresh = action.payload
    },

    // Loading and error states
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },

    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
      state.loading = false
    },

    // Clear all data
    clearMonitoringData: (state) => {
      state.activeRoutes = []
      state.vehicleLocations = {}
      state.visitETAs = {}
      state.routeDelays = {}
      state.selectedRouteId = null
      state.selectedVehicleId = null
      state.lastUpdate = null
    },

    // Reset state
    resetMonitoringState: () => initialState
  }
})

// Export actions
export const {
  setConnectionStatus,
  setActiveRoutes,
  updateActiveRoute,
  removeActiveRoute,
  updateVehicleLocation,
  updateVisitETA,
  setRouteDelays,
  addDelayAlert,
  selectRoute,
  selectVehicle,
  setDateFilter,
  setStatusFilter,
  setVehicleFilter,
  resetFilters,
  setAutoRefresh,
  setLoading,
  setError,
  clearMonitoringData,
  resetMonitoringState
} = monitoringSlice.actions

// Selectors
export const selectConnectionStatus = (state: { monitoring: MonitoringState }) =>
  state.monitoring.connectionStatus

export const selectActiveRoutes = (state: { monitoring: MonitoringState }) =>
  state.monitoring.activeRoutes

export const selectFilteredActiveRoutes = (state: { monitoring: MonitoringState }) => {
  const { activeRoutes, filters } = state.monitoring

  return activeRoutes.filter(route => {
    // Date filter (routes are already filtered by date from API)
    // Status filter
    if (filters.status !== 'all') {
      // Determine route status based on various factors
      const hasDelays = state.monitoring.routeDelays[route.route_id]?.length > 0
      const isInProgress = route.in_progress_visits > 0

      if (filters.status === 'delayed' && !hasDelays) return false
      if (filters.status === 'at_visit' && !isInProgress) return false
      if (filters.status === 'en_route' && (isInProgress || hasDelays)) return false
    }

    // Vehicle filter
    if (filters.vehicleIds.length > 0 && !filters.vehicleIds.includes(route.vehicle_id)) {
      return false
    }

    return true
  })
}

export const selectVehicleLocations = (state: { monitoring: MonitoringState }) =>
  state.monitoring.vehicleLocations

export const selectVehicleLocation = (state: { monitoring: MonitoringState }, vehicleId: number) =>
  state.monitoring.vehicleLocations[vehicleId]

export const selectSelectedRoute = (state: { monitoring: MonitoringState }) => {
  if (!state.monitoring.selectedRouteId) return null
  return state.monitoring.activeRoutes.find(r => r.route_id === state.monitoring.selectedRouteId)
}

export const selectRouteDelays = (state: { monitoring: MonitoringState }, routeId: number) =>
  state.monitoring.routeDelays[routeId] || []

export const selectAllDelays = (state: { monitoring: MonitoringState }) => {
  return Object.values(state.monitoring.routeDelays).flat()
}

export const selectFilters = (state: { monitoring: MonitoringState }) =>
  state.monitoring.filters

export const selectMonitoringStats = (state: { monitoring: MonitoringState }) => {
  const routes = state.monitoring.activeRoutes
  const delays = Object.values(state.monitoring.routeDelays).flat()

  return {
    totalRoutes: routes.length,
    totalVisits: routes.reduce((sum, r) => sum + r.total_visits, 0),
    completedVisits: routes.reduce((sum, r) => sum + r.completed_visits, 0),
    inProgressVisits: routes.reduce((sum, r) => sum + r.in_progress_visits, 0),
    delayedVisits: delays.length,
    averageCompletion: routes.length > 0
      ? routes.reduce((sum, r) => sum + r.completion_percentage, 0) / routes.length
      : 0
  }
}

// Export reducer
export default monitoringSlice.reducer
