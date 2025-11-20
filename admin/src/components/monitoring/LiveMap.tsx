/**
 * LiveMap Component
 * Real-time map displaying vehicle locations and routes
 */

import { useEffect, useMemo } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import { LatLngExpression, Icon, LatLngBounds } from 'leaflet'
import { Box, Typography, Chip } from '@mui/material'
import { useSelector } from 'react-redux'
import { RootState } from '@/store'
import { selectActiveRoutes, selectVehicleLocations } from '@/store/monitoringSlice'
import type { ActiveRoute } from '@/services/trackingService'

// Default center (Bogotá, Colombia)
const DEFAULT_CENTER: LatLngExpression = [4.711, -74.0721]
const DEFAULT_ZOOM = 12

// Component to auto-fit map bounds
const AutoFitBounds = ({ bounds }: { bounds: LatLngBounds | null }) => {
  const map = useMap()

  useEffect(() => {
    if (bounds && bounds.isValid()) {
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 })
    }
  }, [bounds, map])

  return null
}

// Custom marker icons
const createVehicleIcon = (status: string) => {
  const colors: Record<string, string> = {
    en_route: '#4caf50', // Green
    at_visit: '#ff9800', // Orange
    delayed: '#f44336', // Red
    pending: '#9e9e9e', // Gray
    default: '#2196f3' // Blue
  }

  const color = colors[status] || colors.default

  return new Icon({
    iconUrl: `data:image/svg+xml;base64,${btoa(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="32" height="32">
        <circle cx="12" cy="12" r="11" fill="${color}" stroke="white" stroke-width="2"/>
        <path d="M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.5 16c-.83 0-1.5-.67-1.5-1.5S5.67 13 6.5 13s1.5.67 1.5 1.5S7.33 16 6.5 16zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z" fill="white"/>
      </svg>
    `)}`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16]
  })
}


interface LiveMapProps {
  selectedVehicleId?: number | null
  onVehicleClick?: (vehicleId: number) => void
  height?: string | number
}

export const LiveMap: React.FC<LiveMapProps> = ({
  onVehicleClick,
  height = '100%'
}) => {
  const activeRoutes = useSelector((state: RootState) => selectActiveRoutes(state))
  const vehicleLocations = useSelector((state: RootState) => selectVehicleLocations(state))

  // Calculate bounds to fit all markers
  const bounds = useMemo(() => {
    const positions: LatLngExpression[] = []

    // Add vehicle positions
    Object.values(vehicleLocations).forEach(location => {
      positions.push([location.latitude, location.longitude])
    })

    // Add route start locations
    activeRoutes.forEach(route => {
      if (route.current_location) {
        positions.push([route.current_location.latitude, route.current_location.longitude])
      }
    })

    if (positions.length === 0) return null

    return new LatLngBounds(positions)
  }, [vehicleLocations, activeRoutes])

  // Determine vehicle status based on route info
  const getVehicleStatus = (route: ActiveRoute): string => {
    if (route.in_progress_visits > 0) return 'at_visit'
    if (route.completed_visits > 0 && route.pending_visits > 0) return 'en_route'
    if (route.completed_visits === 0) return 'pending'
    return 'default'
  }

  // Format timestamp
  const formatTime = (timestamp?: string) => {
    if (!timestamp) return 'N/A'
    const date = new Date(timestamp)
    return date.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <Box sx={{ height, width: '100%', position: 'relative' }}>
      <MapContainer
        center={DEFAULT_CENTER}
        zoom={DEFAULT_ZOOM}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Auto-fit bounds */}
        <AutoFitBounds bounds={bounds} />

        {/* Vehicle markers */}
        {activeRoutes.map((route) => {
          const location = vehicleLocations[route.vehicle_id] || route.current_location

          if (!location) return null

          const position: LatLngExpression = [location.latitude, location.longitude]
          const status = getVehicleStatus(route)

          return (
            <Marker
              key={`vehicle-${route.vehicle_id}`}
              position={position}
              icon={createVehicleIcon(status)}
              eventHandlers={{
                click: () => onVehicleClick?.(route.vehicle_id)
              }}
            >
              <Popup>
                <Box sx={{ minWidth: 200 }}>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    {route.vehicle_identifier}
                  </Typography>

                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    <strong>Personal:</strong>
                  </Typography>
                  {route.personnel.map(p => (
                    <Typography key={p.personnel_id} variant="body2" sx={{ ml: 1 }}>
                      • {p.name}
                    </Typography>
                  ))}

                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    <strong>Progreso:</strong> {route.completed_visits}/{route.total_visits} visitas
                  </Typography>

                  <Chip
                    label={`${route.completion_percentage.toFixed(0)}% completado`}
                    size="small"
                    color={route.completion_percentage === 100 ? 'success' : 'primary'}
                    sx={{ mt: 1 }}
                  />

                  {'timestamp' in location && (
                    <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                      Última actualización: {formatTime(location.timestamp)}
                    </Typography>
                  )}
                </Box>
              </Popup>
            </Marker>
          )
        })}

        {/* No vehicles message */}
        {activeRoutes.length === 0 && (
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              zIndex: 1000,
              bgcolor: 'background.paper',
              p: 3,
              borderRadius: 2,
              boxShadow: 3
            }}
          >
            <Typography variant="h6" color="text.secondary">
              No hay rutas activas para mostrar
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Las rutas activas aparecerán aquí en tiempo real
            </Typography>
          </Box>
        )}
      </MapContainer>

      {/* Legend */}
      <Box
        sx={{
          position: 'absolute',
          bottom: 16,
          right: 16,
          bgcolor: 'background.paper',
          p: 2,
          borderRadius: 1,
          boxShadow: 2,
          zIndex: 1000
        }}
      >
        <Typography variant="caption" fontWeight="bold" display="block" gutterBottom>
          Leyenda
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
          <Box sx={{ width: 16, height: 16, borderRadius: '50%', bgcolor: '#4caf50' }} />
          <Typography variant="caption">En ruta</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
          <Box sx={{ width: 16, height: 16, borderRadius: '50%', bgcolor: '#ff9800' }} />
          <Typography variant="caption">En visita</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 16, height: 16, borderRadius: '50%', bgcolor: '#f44336' }} />
          <Typography variant="caption">Retrasado</Typography>
        </Box>
      </Box>
    </Box>
  )
}

export default LiveMap
