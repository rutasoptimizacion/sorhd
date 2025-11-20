/**
 * StatusDashboard Component
 * Displays summary cards and statistics for monitoring
 */

import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Alert,
  AlertTitle,
  Chip,
  IconButton,
  Tooltip,
  Stack
} from '@mui/material'
import DirectionsCarIcon from '@mui/icons-material/DirectionsCar'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import AccessTimeIcon from '@mui/icons-material/AccessTime'
import WarningIcon from '@mui/icons-material/Warning'
import RefreshIcon from '@mui/icons-material/Refresh'
import { useSelector } from 'react-redux'
import { RootState } from '@/store'
import { selectMonitoringStats, selectAllDelays } from '@/store/monitoringSlice'

interface StatusDashboardProps {
  onRefresh?: () => void
  loading?: boolean
}

export const StatusDashboard: React.FC<StatusDashboardProps> = ({
  onRefresh,
  loading = false
}) => {
  const stats = useSelector((state: RootState) => selectMonitoringStats(state))
  const delays = useSelector((state: RootState) => selectAllDelays(state))
  const lastUpdate = useSelector((state: RootState) => state.monitoring.lastUpdate)

  // Format timestamp
  const formatLastUpdate = () => {
    if (!lastUpdate) return 'Nunca'
    const date = new Date(lastUpdate)
    const now = new Date()
    const diffSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (diffSeconds < 60) return `Hace ${diffSeconds}s`
    if (diffSeconds < 3600) return `Hace ${Math.floor(diffSeconds / 60)}m`
    return date.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })
  }

  // Severity badge color
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'severe':
        return 'error'
      case 'moderate':
        return 'warning'
      case 'minor':
        return 'info'
      default:
        return 'default'
    }
  }

  return (
    <Box>
      {/* Header with refresh button */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          Dashboard
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Última actualización: {formatLastUpdate()}
          </Typography>
          <Tooltip title="Refrescar datos">
            <IconButton onClick={onRefresh} disabled={loading} size="small">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <DirectionsCarIcon sx={{ fontSize: 32, color: 'primary.main', mb: 1 }} />
              <Typography variant="h4" fontWeight="bold">
                {stats.totalRoutes}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Rutas Activas
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <CheckCircleIcon sx={{ fontSize: 32, color: 'success.main', mb: 1 }} />
              <Typography variant="h4" fontWeight="bold">
                {stats.completedVisits}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Completadas
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <AccessTimeIcon sx={{ fontSize: 32, color: 'warning.main', mb: 1 }} />
              <Typography variant="h4" fontWeight="bold">
                {stats.inProgressVisits}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                En Progreso
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <WarningIcon sx={{ fontSize: 32, color: 'error.main', mb: 1 }} />
              <Typography variant="h4" fontWeight="bold">
                {stats.delayedVisits}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Retrasadas
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Progress Overview */}
      {stats.totalVisits > 0 && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="subtitle2" gutterBottom>
              Progreso General
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h5" fontWeight="bold">
                {stats.averageCompletion.toFixed(0)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {stats.completedVisits} de {stats.totalVisits} visitas completadas
              </Typography>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Delay Alerts */}
      {delays.length > 0 && (
        <Box>
          <Typography variant="subtitle2" gutterBottom sx={{ px: 1 }}>
            Alertas de Retraso ({delays.length})
          </Typography>
          <Stack spacing={1} sx={{ maxHeight: 300, overflow: 'auto' }}>
            {delays.map((delay, index) => (
              <Alert
                key={`delay-${delay.visit_id}-${index}`}
                severity={
                  delay.severity === 'severe' ? 'error' :
                  delay.severity === 'moderate' ? 'warning' : 'info'
                }
                sx={{ py: 0.5 }}
              >
                <AlertTitle sx={{ mb: 0.5 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="subtitle2">
                      Visita #{delay.visit_id}
                    </Typography>
                    <Chip
                      label={`+${delay.delay_minutes} min`}
                      size="small"
                      color={getSeverityColor(delay.severity)}
                    />
                  </Box>
                </AlertTitle>
                <Typography variant="body2">
                  {delay.message}
                </Typography>
                {delay.time_window_end && (
                  <Typography variant="caption" color="text.secondary">
                    Ventana de tiempo: hasta {new Date(delay.time_window_end).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })}
                  </Typography>
                )}
              </Alert>
            ))}
          </Stack>
        </Box>
      )}

      {/* No delays message */}
      {delays.length === 0 && stats.totalRoutes > 0 && (
        <Alert severity="success" sx={{ mt: 2 }}>
          <AlertTitle>Sin retrasos</AlertTitle>
          Todas las rutas están en horario
        </Alert>
      )}
    </Box>
  )
}

export default StatusDashboard
