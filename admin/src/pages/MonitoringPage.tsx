/**
 * MonitoringPage
 * Real-time monitoring dashboard for vehicle tracking and route progress
 */

import { useEffect, useCallback, useMemo } from 'react'
import { Box, Grid, Paper, Typography, Alert } from '@mui/material'
import { useDispatch, useSelector } from 'react-redux'
import { RootState } from '@/store'
import { useWebSocket, useWebSocketMessages } from '@/hooks/useWebSocket'
import {
  setConnectionStatus,
  setActiveRoutes,
  updateVehicleLocation,
  updateVisitETA,
  addDelayAlert,
  selectRoute,
  setLoading,
  setError,
  selectFilters
} from '@/store/monitoringSlice'
import { getActiveRoutes } from '@/services/trackingService'
import type { LocationUpdate, VisitStatusUpdate, ETAUpdate, DelayAlert } from '@/services/websocketService'

// Components
import LiveMap from '@/components/monitoring/LiveMap'
import ActiveRoutesPanel from '@/components/monitoring/ActiveRoutesPanel'
import StatusDashboard from '@/components/monitoring/StatusDashboard'
import MonitoringFilters from '@/components/monitoring/MonitoringFilters'
import ConnectionStatus from '@/components/monitoring/ConnectionStatus'

export const MonitoringPage: React.FC = () => {
  const dispatch = useDispatch()
  const filters = useSelector((state: RootState) => selectFilters(state))
  const activeRoutes = useSelector((state: RootState) => state.monitoring.activeRoutes)
  const selectedVehicleId = useSelector((state: RootState) => state.monitoring.selectedVehicleId)
  const selectedRouteId = useSelector((state: RootState) => state.monitoring.selectedRouteId)
  const loading = useSelector((state: RootState) => state.monitoring.loading)
  const error = useSelector((state: RootState) => state.monitoring.error)

  // WebSocket message handlers
  const {
    handleMessage
  } = useWebSocketMessages({
    onLocationUpdate: (vehicleId: number, location: LocationUpdate) => {
      console.log('[Monitoring] Location update:', vehicleId, location)
      dispatch(updateVehicleLocation({
        vehicleId,
        location: {
          vehicle_id: vehicleId,
          latitude: location.latitude,
          longitude: location.longitude,
          timestamp: location.timestamp,
          speed: location.speed,
          heading: location.heading,
          accuracy: location.accuracy
        }
      }))
    },
    onVisitStatusUpdate: (visitId: number, status: VisitStatusUpdate) => {
      console.log('[Monitoring] Visit status update:', visitId, status)
      // Refresh active routes to get updated visit status
      fetchActiveRoutes()
    },
    onETAUpdate: (visitId: number, eta: ETAUpdate) => {
      console.log('[Monitoring] ETA update:', visitId, eta)
      dispatch(updateVisitETA({
        visit_id: visitId,
        eta_minutes: eta.eta_minutes,
        arrival_time: eta.arrival_time,
        distance_km: 0, // Not provided in real-time update
        traffic_multiplier: eta.traffic_multiplier,
        calculated_at: new Date().toISOString()
      }))
    },
    onDelayAlert: (alert: DelayAlert) => {
      console.log('[Monitoring] Delay alert:', alert)
      dispatch(addDelayAlert(alert))
    }
  })

  // Initialize WebSocket connection
  const { connectionStatus, isConnected, subscribe } = useWebSocket(
    handleMessage,
    { autoConnect: true }
  )

  // Update connection status in Redux
  useEffect(() => {
    dispatch(setConnectionStatus(connectionStatus))
  }, [connectionStatus, dispatch])

  // Fetch active routes from API
  const fetchActiveRoutes = useCallback(async () => {
    try {
      dispatch(setLoading(true))
      const routes = await getActiveRoutes(filters.date)
      dispatch(setActiveRoutes(routes))

      // Subscribe to all active vehicles via WebSocket
      if (isConnected) {
        routes.forEach(route => {
          subscribe('vehicle', route.vehicle_id)
        })
      }
    } catch (err: any) {
      console.error('[Monitoring] Error fetching active routes:', err)
      dispatch(setError(err.message || 'Error al cargar las rutas activas'))
    }
  }, [dispatch, filters.date, isConnected, subscribe])

  // Fetch active routes on mount and when date filter changes
  useEffect(() => {
    fetchActiveRoutes()
  }, [fetchActiveRoutes])

  // Subscribe to active routes when WebSocket connects
  useEffect(() => {
    if (isConnected && activeRoutes.length > 0) {
      activeRoutes.forEach(route => {
        subscribe('vehicle', route.vehicle_id)
      })
    }
  }, [isConnected, activeRoutes, subscribe])

  // Handle route click
  const handleRouteClick = useCallback((routeId: number) => {
    dispatch(selectRoute(routeId))
  }, [dispatch])

  // Handle vehicle click on map
  const handleVehicleClick = useCallback((vehicleId: number) => {
    const route = activeRoutes.find(r => r.vehicle_id === vehicleId)
    if (route) {
      dispatch(selectRoute(route.route_id))
    }
  }, [activeRoutes, dispatch])

  // Available vehicles for filter
  const availableVehicles = useMemo(() => {
    return activeRoutes.map(route => ({
      id: route.vehicle_id,
      identifier: route.vehicle_identifier
    }))
  }, [activeRoutes])

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Monitoreo en Tiempo Real
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Seguimiento de vehículos y progreso de rutas en tiempo real
          </Typography>
        </Box>
        <ConnectionStatus showLabel />
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" onClose={() => dispatch(setError(null))} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Main Content */}
      <Grid container spacing={3}>
        {/* Left Panel - Filters, Dashboard, Routes */}
        <Grid item xs={12} md={4}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {/* Filters */}
            <MonitoringFilters availableVehicles={availableVehicles} />

            {/* Status Dashboard */}
            <StatusDashboard onRefresh={fetchActiveRoutes} loading={loading} />

            {/* Active Routes Panel */}
            <Paper sx={{ maxHeight: 600, overflow: 'hidden' }}>
              <ActiveRoutesPanel
                selectedRouteId={selectedRouteId}
                onRouteClick={handleRouteClick}
                maxHeight="600px"
              />
            </Paper>
          </Box>
        </Grid>

        {/* Right Panel - Map */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ height: '85vh', minHeight: 600, overflow: 'hidden' }}>
            <LiveMap
              selectedVehicleId={selectedVehicleId}
              onVehicleClick={handleVehicleClick}
              height="100%"
            />
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}

export default MonitoringPage
