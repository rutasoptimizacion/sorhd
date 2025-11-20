/**
 * ActiveRoutesPanel Component
 * Displays list of active routes with progress and status
 */

import {
  Box,
  Typography,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Divider,
  Avatar,
  Stack,
  Tooltip
} from '@mui/material'
import DirectionsCarIcon from '@mui/icons-material/DirectionsCar'
import PersonIcon from '@mui/icons-material/Person'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import AccessTimeIcon from '@mui/icons-material/AccessTime'
import WarningIcon from '@mui/icons-material/Warning'
import { useSelector } from 'react-redux'
import { RootState } from '@/store'
import { selectFilteredActiveRoutes, selectRouteDelays } from '@/store/monitoringSlice'
import type { ActiveRoute } from '@/services/trackingService'

interface ActiveRoutesPanelProps {
  selectedRouteId?: number | null
  onRouteClick?: (routeId: number) => void
  maxHeight?: string | number
}

export const ActiveRoutesPanel: React.FC<ActiveRoutesPanelProps> = ({
  selectedRouteId,
  onRouteClick,
  maxHeight = '600px'
}) => {
  const activeRoutes = useSelector((state: RootState) => selectFilteredActiveRoutes(state))

  // Format time
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })
  }

  // Get status color
  const getStatusColor = (route: ActiveRoute) => {
    if (route.completion_percentage === 100) return 'success'
    if (route.in_progress_visits > 0) return 'warning'
    if (route.completed_visits > 0) return 'info'
    return 'default'
  }

  // Get status label
  const getStatusLabel = (route: ActiveRoute) => {
    if (route.completion_percentage === 100) return 'Completado'
    if (route.in_progress_visits > 0) return 'En visita'
    if (route.completed_visits > 0) return 'En ruta'
    return 'Pendiente'
  }

  // Get status icon
  const getStatusIcon = (route: ActiveRoute) => {
    if (route.completion_percentage === 100) return <CheckCircleIcon fontSize="small" />
    if (route.in_progress_visits > 0) return <AccessTimeIcon fontSize="small" />
    return null
  }

  // Check if route has delays
  const hasDelays = (routeId: number) => {
    return useSelector((state: RootState) => selectRouteDelays(state, routeId)).length > 0
  }

  return (
    <Box sx={{ height: '100%' }}>
      <Typography variant="h6" gutterBottom sx={{ px: 2, pt: 2 }}>
        Rutas Activas ({activeRoutes.length})
      </Typography>

      {activeRoutes.length === 0 ? (
        <Box sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            No hay rutas activas para mostrar
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Las rutas aparecerán aquí cuando estén activas
          </Typography>
        </Box>
      ) : (
        <List
          sx={{
            maxHeight,
            overflow: 'auto',
            '&::-webkit-scrollbar': {
              width: '8px'
            },
            '&::-webkit-scrollbar-thumb': {
              backgroundColor: 'rgba(0,0,0,0.2)',
              borderRadius: '4px'
            }
          }}
        >
          {activeRoutes.map((route, index) => (
            <Box key={route.route_id}>
              {index > 0 && <Divider />}
              <ListItem disablePadding>
                <ListItemButton
                  selected={selectedRouteId === route.route_id}
                  onClick={() => onRouteClick?.(route.route_id)}
                  sx={{ py: 2 }}
                >
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
                          <DirectionsCarIcon fontSize="small" />
                        </Avatar>
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="subtitle2" fontWeight="bold">
                            {route.vehicle_identifier}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {route.date}
                          </Typography>
                        </Box>
                        <Stack direction="row" spacing={0.5}>
                          <Chip
                            label={getStatusLabel(route)}
                            color={getStatusColor(route)}
                            size="small"
                            icon={getStatusIcon(route) || undefined}
                          />
                          {hasDelays(route.route_id) && (
                            <Tooltip title="Ruta con retrasos">
                              <Chip
                                label="Retraso"
                                color="error"
                                size="small"
                                icon={<WarningIcon fontSize="small" />}
                              />
                            </Tooltip>
                          )}
                        </Stack>
                      </Box>
                    }
                    secondary={
                      <Box>
                        {/* Personnel */}
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
                          <PersonIcon fontSize="small" color="action" />
                          <Typography variant="body2" color="text.secondary">
                            {route.personnel.map(p => p.name).join(', ')}
                          </Typography>
                        </Box>

                        {/* Progress */}
                        <Box sx={{ mb: 1 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                            <Typography variant="caption" color="text.secondary">
                              Progreso
                            </Typography>
                            <Typography variant="caption" fontWeight="bold">
                              {route.completed_visits}/{route.total_visits} visitas
                            </Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={route.completion_percentage}
                            sx={{
                              height: 6,
                              borderRadius: 1,
                              bgcolor: 'action.hover',
                              '& .MuiLinearProgress-bar': {
                                borderRadius: 1
                              }
                            }}
                          />
                          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                            {route.completion_percentage.toFixed(0)}% completado
                          </Typography>
                        </Box>

                        {/* Visit status breakdown */}
                        <Box sx={{ display: 'flex', gap: 2 }}>
                          <Typography variant="caption" color="success.main">
                            ✓ {route.completed_visits} completadas
                          </Typography>
                          {route.in_progress_visits > 0 && (
                            <Typography variant="caption" color="warning.main">
                              ⏱ {route.in_progress_visits} en progreso
                            </Typography>
                          )}
                          {route.pending_visits > 0 && (
                            <Typography variant="caption" color="text.secondary">
                              ○ {route.pending_visits} pendientes
                            </Typography>
                          )}
                        </Box>

                        {/* Last update */}
                        {route.current_location && (
                          <Typography variant="caption" color="text.disabled" sx={{ mt: 1, display: 'block' }}>
                            Última actualización: {formatTime(route.current_location.timestamp)}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItemButton>
              </ListItem>
            </Box>
          ))}
        </List>
      )}
    </Box>
  )
}

export default ActiveRoutesPanel
