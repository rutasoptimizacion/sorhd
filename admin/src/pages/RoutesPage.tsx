import { useState } from 'react'
import {
  Box,
  Button,
  Typography,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Card,
  CardContent,
  Divider,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
} from '@mui/material'
import {
  Visibility as VisibilityIcon,
  Cancel as CancelIcon,
  PlayArrow as ActivateIcon,
  DirectionsCar,
  People,
  Route as RouteIcon,
  Schedule,
  Timeline,
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { DataTable, LoadingSpinner, ErrorMessage, ConfirmDialog } from '@/components/common'
import { RouteMap } from '@/components/planning/RouteMap'
import { routeService } from '@/services/routeService'
import type { Route, RouteStatus, RouteListParams, RouteWithDetails } from '@/types'
import type { Column } from '@/components/common/DataTable'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

export default function RoutesPage() {
  const [filters, setFilters] = useState<RouteListParams>({
    page: 1,
    page_size: 20,
  })
  const [selectedRoute, setSelectedRoute] = useState<RouteWithDetails | null>(null)
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false)
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false)
  const [routeToCancel, setRouteToCancel] = useState<Route | null>(null)
  const [loadingDetails, setLoadingDetails] = useState(false)

  const queryClient = useQueryClient()

  const { data: routesResponse, isLoading, error } = useQuery({
    queryKey: ['routes', filters],
    queryFn: () => routeService.getAll(filters),
  })

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: RouteStatus }) =>
      routeService.updateStatus(id, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['routes'] })
    },
  })

  const cancelMutation = useMutation({
    mutationFn: (id: number) => routeService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['routes'] })
      setCancelDialogOpen(false)
      setRouteToCancel(null)
    },
  })

  const handleViewDetails = async (route: Route) => {
    setDetailsDialogOpen(true)
    setLoadingDetails(true)
    try {
      // Fetch full route details with visits, vehicle, personnel, etc.
      const routeDetails = await routeService.getByIdWithDetails(route.id)
      setSelectedRoute(routeDetails)
    } catch (error) {
      console.error('Error loading route details:', error)
      alert('Error al cargar los detalles de la ruta')
      setDetailsDialogOpen(false)
    } finally {
      setLoadingDetails(false)
    }
  }

  const handleActivate = (route: Route) => {
    if (window.confirm(`¿Activar la ruta para el vehículo ${route.vehicle?.identifier || route.vehicle_id}?`)) {
      updateStatusMutation.mutate({ id: route.id, status: 'active' })
    }
  }

  const handleCancel = (route: Route) => {
    setRouteToCancel(route)
    setCancelDialogOpen(true)
  }

  const getStatusLabel = (status: RouteStatus) => {
    const labels: Record<RouteStatus, string> = {
      draft: 'Borrador',
      planned: 'Planificada',
      active: 'Activa',
      in_progress: 'En Progreso',
      completed: 'Completada',
      cancelled: 'Cancelada',
    }
    return labels[status]
  }

  const getStatusColor = (status: RouteStatus) => {
    const colors: Record<RouteStatus, 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info'> = {
      draft: 'default',
      planned: 'info',
      active: 'primary',
      in_progress: 'warning',
      completed: 'success',
      cancelled: 'error',
    }
    return colors[status]
  }

  const columns: Column<Route>[] = [
    { id: 'id', label: 'ID', sortable: true, minWidth: 80 },
    {
      id: 'route_date',
      label: 'Fecha',
      sortable: true,
      minWidth: 120,
      render: (row) => format(new Date(row.route_date), 'dd/MM/yyyy', { locale: es }),
    },
    {
      id: 'vehicle_id',
      label: 'Vehículo',
      minWidth: 120,
      render: (row) => row.vehicle?.identifier || `ID ${row.vehicle_id}`,
    },
    {
      id: 'status',
      label: 'Estado',
      minWidth: 130,
      render: (row) => (
        <Chip label={getStatusLabel(row.status)} color={getStatusColor(row.status)} size="small" />
      ),
    },
    {
      id: 'total_distance_km',
      label: 'Distancia',
      align: 'right',
      minWidth: 110,
      render: (row) => `${row.total_distance_km?.toFixed(1) || '0.0'} km`,
    },
    {
      id: 'total_duration_minutes',
      label: 'Duración',
      align: 'right',
      minWidth: 110,
      render: (row) => {
        const hours = Math.floor((row.total_duration_minutes || 0) / 60)
        const minutes = (row.total_duration_minutes || 0) % 60
        return `${hours}h ${minutes}m`
      },
    },
    {
      id: 'visits_count',
      label: 'Visitas',
      align: 'center',
      minWidth: 100,
      render: (row) => row.visits?.length || 0,
    },
    {
      id: 'personnel_count',
      label: 'Personal',
      align: 'center',
      minWidth: 100,
      render: (row) => row.personnel?.length || 0,
    },
    {
      id: 'actions',
      label: 'Acciones',
      align: 'right',
      minWidth: 150,
      render: (row) => (
        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
          <IconButton size="small" color="primary" onClick={() => handleViewDetails(row)}>
            <VisibilityIcon fontSize="small" />
          </IconButton>
          {row.status === 'draft' && (
            <IconButton size="small" color="success" onClick={() => handleActivate(row)}>
              <ActivateIcon fontSize="small" />
            </IconButton>
          )}
          {['draft', 'planned'].includes(row.status) && (
            <IconButton size="small" color="error" onClick={() => handleCancel(row)}>
              <CancelIcon fontSize="small" />
            </IconButton>
          )}
        </Box>
      ),
    },
  ]

  if (error) {
    return <ErrorMessage message={error.message} />
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Rutas</Typography>
        <Button variant="contained" href="/planning">
          Nueva Planificación
        </Button>
      </Box>

      {/* Filters */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <TextField
          label="Fecha"
          type="date"
          value={filters.date || ''}
          onChange={(e) => setFilters({ ...filters, date: e.target.value })}
          InputLabelProps={{ shrink: true }}
          sx={{ minWidth: 180 }}
        />
        <FormControl sx={{ minWidth: 180 }}>
          <InputLabel>Estado</InputLabel>
          <Select
            value={filters.status || ''}
            onChange={(e) => setFilters({ ...filters, status: e.target.value as RouteStatus })}
            label="Estado"
          >
            <MenuItem value="">Todos</MenuItem>
            <MenuItem value="draft">Borrador</MenuItem>
            <MenuItem value="planned">Planificada</MenuItem>
            <MenuItem value="active">Activa</MenuItem>
            <MenuItem value="in_progress">En Progreso</MenuItem>
            <MenuItem value="completed">Completada</MenuItem>
            <MenuItem value="cancelled">Cancelada</MenuItem>
          </Select>
        </FormControl>
        <Button variant="outlined" onClick={() => setFilters({ page: 1, page_size: 20 })}>
          Limpiar Filtros
        </Button>
      </Box>

      {/* Table */}
      <Box sx={{ flex: 1, minHeight: 0 }}>
        {isLoading ? (
          <LoadingSpinner />
        ) : (
          <DataTable
            columns={columns}
            data={routesResponse?.items || []}
            loading={isLoading}
            emptyMessage="No hay rutas registradas"
          />
        )}
      </Box>

      {/* Details Dialog */}
      <Dialog
        open={detailsDialogOpen}
        onClose={() => setDetailsDialogOpen(false)}
        maxWidth="xl"
        fullWidth
        PaperProps={{
          sx: { height: '90vh' }
        }}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <RouteIcon />
            <Box>
              <Typography variant="h6">
                Ruta #{selectedRoute?.id}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {selectedRoute && format(new Date(selectedRoute.route_date), "dd 'de' MMMM, yyyy", { locale: es })}
              </Typography>
            </Box>
            {selectedRoute && (
              <Chip
                label={getStatusLabel(selectedRoute.status)}
                color={getStatusColor(selectedRoute.status)}
                size="small"
                sx={{ ml: 'auto' }}
              />
            )}
          </Box>
        </DialogTitle>
        <DialogContent sx={{ p: 3 }}>
          {loadingDetails ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
              <CircularProgress />
            </Box>
          ) : selectedRoute ? (
            <Grid container spacing={3}>
              {/* Left Column - Information */}
              <Grid item xs={12} md={5}>
                {/* Vehicle Card */}
                <Card sx={{ mb: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <DirectionsCar color="primary" />
                      <Typography variant="h6">Vehículo</Typography>
                    </Box>
                    <Typography variant="body1" gutterBottom>
                      <strong>{selectedRoute.vehicle?.identifier || `ID ${selectedRoute.vehicle_id}`}</strong>
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Capacidad: {selectedRoute.vehicle?.capacity || 'N/A'} personas
                    </Typography>
                    {selectedRoute.vehicle?.resources && selectedRoute.vehicle.resources.length > 0 && (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          Recursos:
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
                          {selectedRoute.vehicle.resources.map((resource, index) => (
                            <Chip key={index} label={resource} size="small" variant="outlined" />
                          ))}
                        </Box>
                      </Box>
                    )}
                  </CardContent>
                </Card>

                {/* Personnel Card */}
                <Card sx={{ mb: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <People color="primary" />
                      <Typography variant="h6">Personal Asignado</Typography>
                    </Box>
                    {selectedRoute.personnel && selectedRoute.personnel.length > 0 ? (
                      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        {selectedRoute.personnel.map((person) => (
                          <Chip key={person.id} label={person.name} variant="outlined" />
                        ))}
                      </Box>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        Sin personal asignado
                      </Typography>
                    )}
                  </CardContent>
                </Card>

                {/* Metrics Card */}
                <Card sx={{ mb: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <Timeline color="primary" />
                      <Typography variant="h6">Métricas</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">
                          Distancia Total:
                        </Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {selectedRoute.total_distance_km?.toFixed(1) || '0.0'} km
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">
                          Duración Estimada:
                        </Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {Math.floor((selectedRoute.total_duration_minutes || 0) / 60)}h{' '}
                          {(selectedRoute.total_duration_minutes || 0) % 60}m
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">
                          Total de Visitas:
                        </Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {selectedRoute.visits?.length || 0}
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>

                {/* Visits Card */}
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <Schedule color="primary" />
                      <Typography variant="h6">
                        Visitas ({selectedRoute.visits?.length || 0})
                      </Typography>
                    </Box>
                    <List sx={{ maxHeight: '300px', overflowY: 'auto' }}>
                      {selectedRoute.visits && selectedRoute.visits.length > 0 ? (
                        [...selectedRoute.visits]
                          .sort((a, b) => a.sequence_number - b.sequence_number)
                          .map((visit, index) => (
                            <Box key={visit.id}>
                              {index > 0 && <Divider />}
                              <ListItem>
                                <ListItemText
                                  primary={
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                      <Chip
                                        label={visit.sequence_number + 1}
                                        size="small"
                                        color="primary"
                                      />
                                      <Typography variant="body2">
                                        {visit.patient?.name || `Paciente ${visit.case?.patient_id}`}
                                      </Typography>
                                    </Box>
                                  }
                                  secondary={
                                    <Box sx={{ mt: 0.5 }}>
                                      <Typography variant="caption" display="block">
                                        {visit.care_type?.name || `Caso #${visit.case_id}`}
                                      </Typography>
                                      {visit.estimated_arrival_time && (
                                        <Typography variant="caption" color="primary">
                                          🕒 {format(new Date(visit.estimated_arrival_time), 'HH:mm')} -{' '}
                                          {visit.estimated_departure_time &&
                                            format(new Date(visit.estimated_departure_time), 'HH:mm')}
                                        </Typography>
                                      )}
                                      {visit.case?.location && (
                                        <Typography variant="caption" display="block" color="text.secondary">
                                          📍 {visit.case.location.latitude.toFixed(4)}, {visit.case.location.longitude.toFixed(4)}
                                        </Typography>
                                      )}
                                      <Chip
                                        label={visit.status || 'pending'}
                                        size="small"
                                        sx={{ mt: 0.5 }}
                                      />
                                    </Box>
                                  }
                                />
                              </ListItem>
                            </Box>
                          ))
                      ) : (
                        <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
                          Sin visitas programadas
                        </Typography>
                      )}
                    </List>
                  </CardContent>
                </Card>
              </Grid>

              {/* Right Column - Map */}
              <Grid item xs={12} md={7}>
                <Box sx={{ height: '100%', minHeight: '600px' }}>
                  <RouteMap routes={[selectedRoute]} height="100%" />
                </Box>
              </Grid>
            </Grid>
          ) : (
            <Typography>No se pudo cargar la información de la ruta</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsDialogOpen(false)}>Cerrar</Button>
        </DialogActions>
      </Dialog>

      {/* Cancel Confirmation Dialog */}
      <ConfirmDialog
        open={cancelDialogOpen}
        title="Cancelar Ruta"
        message={`¿Estás seguro de que deseas cancelar la ruta #${routeToCancel?.id}? Esta acción no se puede deshacer.`}
        onConfirm={() => routeToCancel && cancelMutation.mutate(routeToCancel.id)}
        onCancel={() => {
          setCancelDialogOpen(false)
          setRouteToCancel(null)
        }}
        confirmText="Cancelar Ruta"
        cancelText="Volver"
      />
    </Box>
  )
}
