import { useEffect, useMemo } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet'
import L from 'leaflet'
import { Box, Paper, Typography, Chip, Alert } from '@mui/material'
import type { RouteWithDetails, Case } from '@/types'
import 'leaflet/dist/leaflet.css'

// Fix for default marker icons in React-Leaflet
import icon from 'leaflet/dist/images/marker-icon.png'
import iconShadow from 'leaflet/dist/images/marker-shadow.png'
import iconRetina from 'leaflet/dist/images/marker-icon-2x.png'

const DefaultIcon = L.icon({
  iconUrl: icon,
  iconRetinaUrl: iconRetina,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

L.Marker.prototype.options.icon = DefaultIcon

interface RouteMapProps {
  routes: RouteWithDetails[]
  cases?: Case[]
  height?: string | number
}

// Component to fit map bounds to show all routes
const MapBounds = ({ routes, cases }: { routes: RouteWithDetails[]; cases?: Case[] }) => {
  const map = useMap()

  useEffect(() => {
    const bounds: [number, number][] = []

    // Add vehicle base locations
    routes.forEach((route) => {
      if (route.vehicle?.base_location) {
        bounds.push([
          route.vehicle.base_location.latitude,
          route.vehicle.base_location.longitude,
        ])
      }
    })

    // Add case locations
    if (cases) {
      cases.forEach((c) => {
        bounds.push([c.location.latitude, c.location.longitude])
      })
    }

    // Add visit locations
    routes.forEach((route) => {
      route.visits?.forEach((visit) => {
        if (visit.case?.location) {
          bounds.push([
            visit.case.location.latitude,
            visit.case.location.longitude,
          ])
        }
      })
    })

    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [50, 50] })
    }
  }, [routes, cases, map])

  return null
}

export const RouteMap = ({ routes, cases, height = 600 }: RouteMapProps) => {
  // Generate distinct colors for each route
  const routeColors = useMemo(() => {
    const colors = [
      '#1976d2', // blue
      '#d32f2f', // red
      '#388e3c', // green
      '#f57c00', // orange
      '#7b1fa2', // purple
      '#0097a7', // cyan
      '#c2185b', // pink
      '#5d4037', // brown
      '#455a64', // blue grey
      '#689f38', // light green
    ]
    return routes.map((_, index) => colors[index % colors.length])
  }, [routes])

  // Calculate center of map
  const center: [number, number] = useMemo(() => {
    if (routes.length > 0 && routes[0].vehicle?.base_location) {
      return [
        routes[0].vehicle.base_location.latitude,
        routes[0].vehicle.base_location.longitude,
      ]
    }
    if (cases && cases.length > 0) {
      return [cases[0].location.latitude, cases[0].location.longitude]
    }
    // Default to Santiago, Chile
    return [-33.4489, -70.6693]
  }, [routes, cases])

  // Create custom icons for vehicles
  const createVehicleIcon = (color: string) => {
    return L.divIcon({
      className: 'custom-vehicle-icon',
      html: `<div style="
        background-color: ${color};
        width: 30px;
        height: 30px;
        border-radius: 50%;
        border: 3px solid white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
      ">🚗</div>`,
      iconSize: [30, 30],
      iconAnchor: [15, 15],
      popupAnchor: [0, -15],
    })
  }

  // Create custom icons for cases/visits
  const createCaseIcon = (index: number) => {
    return L.divIcon({
      className: 'custom-case-icon',
      html: `<div style="
        background-color: white;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        border: 2px solid #1976d2;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 12px;
        color: #1976d2;
      ">${index}</div>`,
      iconSize: [28, 28],
      iconAnchor: [14, 14],
      popupAnchor: [0, -14],
    })
  }

  if (routes.length === 0 && (!cases || cases.length === 0)) {
    return (
      <Paper sx={{ p: 3, height }}>
        <Alert severity="info">
          No hay rutas para visualizar. Complete la optimización para ver las
          rutas en el mapa.
        </Alert>
      </Paper>
    )
  }

  return (
    <Paper sx={{ p: 2, height }}>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Visualización de Rutas
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {routes.map((route, index) => (
            <Chip
              key={route.id}
              label={`Ruta ${index + 1}: ${route.vehicle?.identifier || route.vehicle_id} (${route.visit_count} visitas)`}
              size="small"
              sx={{
                backgroundColor: routeColors[index],
                color: 'white',
              }}
            />
          ))}
        </Box>
      </Box>

      <Box sx={{ height: 'calc(100% - 80px)', borderRadius: 1, overflow: 'hidden' }}>
        <MapContainer
          center={center}
          zoom={12}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <MapBounds routes={routes} cases={cases} />

          {/* Render unassigned cases */}
          {cases &&
            cases.map((caseItem) => (
              <Marker
                key={`case-${caseItem.id}`}
                position={[caseItem.location.latitude, caseItem.location.longitude]}
              >
                <Popup>
                  <div>
                    <strong>Caso #{caseItem.id}</strong>
                    <br />
                    Paciente ID: {caseItem.patient_id}
                    <br />
                    Prioridad: {caseItem.priority}
                    <br />
                    Estado: {caseItem.status}
                  </div>
                </Popup>
              </Marker>
            ))}

          {/* Render each route */}
          {routes.map((route, routeIndex) => {
            const color = routeColors[routeIndex]
            const sortedVisits = [...(route.visits || [])].sort(
              (a, b) => a.sequence_number - b.sequence_number
            )

            // Build polyline coordinates
            const polylineCoords: [number, number][] = []

            // Start from vehicle base location
            if (route.vehicle?.base_location) {
              polylineCoords.push([
                route.vehicle.base_location.latitude,
                route.vehicle.base_location.longitude,
              ])
            }

            // Add each visit location
            sortedVisits.forEach((visit) => {
              if (visit.case?.location) {
                polylineCoords.push([
                  visit.case.location.latitude,
                  visit.case.location.longitude,
                ])
              }
            })

            // Return to base
            if (route.vehicle?.base_location) {
              polylineCoords.push([
                route.vehicle.base_location.latitude,
                route.vehicle.base_location.longitude,
              ])
            }

            return (
              <div key={route.id}>
                {/* Vehicle base marker */}
                {route.vehicle?.base_location && (
                  <Marker
                    position={[
                      route.vehicle.base_location.latitude,
                      route.vehicle.base_location.longitude,
                    ]}
                    icon={createVehicleIcon(color)}
                  >
                    <Popup>
                      <div>
                        <strong>Vehículo: {route.vehicle.identifier}</strong>
                        <br />
                        Capacidad: {route.vehicle.capacity}
                        <br />
                        Estado: {route.vehicle.status}
                        <br />
                        Visitas: {route.visit_count}
                        {route.total_distance_km && (
                          <>
                            <br />
                            Distancia: {route.total_distance_km.toFixed(1)} km
                          </>
                        )}
                      </div>
                    </Popup>
                  </Marker>
                )}

                {/* Visit markers */}
                {sortedVisits.map((visit, visitIndex) => {
                  if (!visit.case?.location) return null

                  return (
                    <Marker
                      key={`visit-${visit.id}`}
                      position={[
                        visit.case.location.latitude,
                        visit.case.location.longitude,
                      ]}
                      icon={createCaseIcon(visitIndex + 1)}
                    >
                      <Popup>
                        <div>
                          <strong>Visita #{visitIndex + 1}</strong>
                          <br />
                          Caso ID: {visit.case_id}
                          <br />
                          {visit.patient && (
                            <>
                              Paciente: {visit.patient.name}
                              <br />
                            </>
                          )}
                          {visit.care_type && (
                            <>
                              Atención: {visit.care_type.name}
                              <br />
                            </>
                          )}
                          {visit.estimated_arrival_time && (
                            <>
                              Llegada estimada:{' '}
                              {new Date(visit.estimated_arrival_time).toLocaleTimeString(
                                'es-ES',
                                { hour: '2-digit', minute: '2-digit' }
                              )}
                            </>
                          )}
                        </div>
                      </Popup>
                    </Marker>
                  )
                })}

                {/* Route polyline */}
                {polylineCoords.length > 1 && (
                  <Polyline
                    positions={polylineCoords}
                    color={color}
                    weight={4}
                    opacity={0.7}
                  />
                )}
              </div>
            )
          })}
        </MapContainer>
      </Box>
    </Paper>
  )
}
