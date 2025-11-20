import { useState, useMemo } from 'react'
import {
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Typography,
  Chip,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  FormControlLabel,
  Switch,
  Paper,
  Grid,
} from '@mui/material'
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon, FilterList as FilterListIcon } from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm, Controller } from 'react-hook-form'
import { DataTable, LoadingSpinner, ErrorMessage, ConfirmDialog, LocationPicker } from '@/components/common'
import { vehicleService } from '@/services/vehicleService'
import type { Vehicle, VehicleCreate, VehicleStatus } from '@/types'
import { VehicleStatus as VehicleStatusEnum } from '@/types'
import type { Column } from '@/components/common/DataTable'

export default function VehiclesPage() {
  const [openDialog, setOpenDialog] = useState(false)
  const [editingVehicle, setEditingVehicle] = useState<Vehicle | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [vehicleToDelete, setVehicleToDelete] = useState<Vehicle | null>(null)

  // Filtros
  const [filterIdentifier, setFilterIdentifier] = useState('')
  const [filterStatus, setFilterStatus] = useState<VehicleStatus | ''>('')
  const [filterCapacity, setFilterCapacity] = useState('')
  const [filterActive, setFilterActive] = useState<'all' | 'active' | 'inactive'>('all')

  const queryClient = useQueryClient()

  const { data: vehiclesResponse, isLoading, error } = useQuery({
    queryKey: ['vehicles'],
    queryFn: () => vehicleService.getAll(),
  })

  // Filtrado de vehículos
  const filteredVehicles = useMemo(() => {
    if (!vehiclesResponse?.items) return []

    return vehiclesResponse.items.filter((vehicle) => {
      // Filtro por identificador
      if (filterIdentifier && !vehicle.identifier.toLowerCase().includes(filterIdentifier.toLowerCase())) {
        return false
      }

      // Filtro por estado
      if (filterStatus && vehicle.status !== filterStatus) {
        return false
      }

      // Filtro por capacidad
      if (filterCapacity && vehicle.capacity.toString() !== filterCapacity) {
        return false
      }

      // Filtro por activo/inactivo
      if (filterActive === 'active' && !vehicle.is_active) {
        return false
      }
      if (filterActive === 'inactive' && vehicle.is_active) {
        return false
      }

      return true
    })
  }, [vehiclesResponse, filterIdentifier, filterStatus, filterCapacity, filterActive])

  const createMutation = useMutation({
    mutationFn: (data: VehicleCreate) => vehicleService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vehicles'] })
      setOpenDialog(false)
      reset()
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: VehicleCreate }) =>
      vehicleService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vehicles'] })
      setOpenDialog(false)
      setEditingVehicle(null)
      reset()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => vehicleService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vehicles'] })
      setDeleteDialogOpen(false)
      setVehicleToDelete(null)
    },
  })

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm<VehicleCreate>({
    defaultValues: {
      identifier: '',
      capacity: 2,
      is_active: true,
      base_location: { latitude: -33.4489, longitude: -70.6693 },
      status: VehicleStatusEnum.AVAILABLE,
      resources: [],
    },
  })

  const handleCreate = () => {
    setEditingVehicle(null)
    reset({
      identifier: '',
      capacity: 2,
      is_active: true,
      base_location: { latitude: -33.4489, longitude: -70.6693 },
      status: VehicleStatusEnum.AVAILABLE,
      resources: [],
    })
    setOpenDialog(true)
  }

  const handleEdit = (vehicle: Vehicle) => {
    setEditingVehicle(vehicle)
    reset({
      identifier: vehicle.identifier,
      capacity: vehicle.capacity,
      is_active: vehicle.is_active,
      base_location: vehicle.base_location,
      status: vehicle.status,
      resources: vehicle.resources,
    })
    setOpenDialog(true)
  }

  const handleDelete = (vehicle: Vehicle) => {
    setVehicleToDelete(vehicle)
    setDeleteDialogOpen(true)
  }

  const onSubmit = (data: VehicleCreate) => {
    if (editingVehicle) {
      updateMutation.mutate({ id: editingVehicle.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  const getStatusLabel = (status: VehicleStatus) => {
    const labels = {
      available: 'Disponible',
      in_use: 'En Uso',
      maintenance: 'Mantenimiento',
      unavailable: 'No Disponible',
    }
    return labels[status]
  }

  const getStatusColor = (status: VehicleStatus) => {
    const colors: Record<VehicleStatus, 'success' | 'warning' | 'error' | 'default'> = {
      available: 'success',
      in_use: 'warning',
      maintenance: 'default',
      unavailable: 'error',
    }
    return colors[status]
  }

  const columns: Column<Vehicle>[] = [
    { id: 'id', label: 'ID', sortable: true, minWidth: 80 },
    { id: 'identifier', label: 'Identificador', sortable: true, minWidth: 150 },
    { id: 'capacity', label: 'Capacidad', sortable: true, minWidth: 100, align: 'center' },
    {
      id: 'status',
      label: 'Estado',
      minWidth: 130,
      render: (row) => (
        <Chip label={getStatusLabel(row.status)} color={getStatusColor(row.status)} size="small" />
      ),
    },
    {
      id: 'resources',
      label: 'Recursos',
      minWidth: 200,
      render: (row) => (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
          {row.resources && row.resources.length > 0 ? (
            row.resources.map((resource, index) => (
              <Chip key={index} label={resource} size="small" variant="outlined" />
            ))
          ) : (
            <Typography variant="caption" color="text.secondary">
              Sin recursos
            </Typography>
          )}
        </Box>
      ),
    },
    {
      id: 'is_active',
      label: 'Activo',
      minWidth: 100,
      align: 'center',
      render: (row) => (
        <Chip label={row.is_active ? 'Sí' : 'No'} color={row.is_active ? 'success' : 'default'} size="small" />
      ),
    },
    {
      id: 'actions',
      label: 'Acciones',
      align: 'right',
      minWidth: 120,
      render: (row) => (
        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
          <IconButton size="small" color="primary" onClick={() => handleEdit(row)}>
            <EditIcon fontSize="small" />
          </IconButton>
          <IconButton size="small" color="error" onClick={() => handleDelete(row)}>
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Box>
      ),
    },
  ]

  if (error) {
    return <ErrorMessage message={error.message} />
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Vehículos</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>
          Nuevo Vehículo
        </Button>
      </Box>

      {/* Filtros */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <FilterListIcon sx={{ mr: 1, color: 'text.secondary' }} />
          <Typography variant="h6">Filtros</Typography>
        </Box>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              label="Identificador/Patente"
              value={filterIdentifier}
              onChange={(e) => setFilterIdentifier(e.target.value)}
              size="small"
              fullWidth
              placeholder="VEH-001..."
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Estado</InputLabel>
              <Select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value as VehicleStatus | '')}
                label="Estado"
              >
                <MenuItem value="">Todos</MenuItem>
                <MenuItem value="available">Disponible</MenuItem>
                <MenuItem value="in_use">En Uso</MenuItem>
                <MenuItem value="maintenance">Mantenimiento</MenuItem>
                <MenuItem value="unavailable">No Disponible</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              label="Capacidad"
              value={filterCapacity}
              onChange={(e) => setFilterCapacity(e.target.value)}
              size="small"
              fullWidth
              type="number"
              placeholder="2, 3, 4..."
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Activo</InputLabel>
              <Select
                value={filterActive}
                onChange={(e) => setFilterActive(e.target.value as 'all' | 'active' | 'inactive')}
                label="Activo"
              >
                <MenuItem value="all">Todos</MenuItem>
                <MenuItem value="active">Activos</MenuItem>
                <MenuItem value="inactive">Inactivos</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Mostrando {filteredVehicles.length} de {vehiclesResponse?.items.length || 0} vehículos
          </Typography>
          {(filterIdentifier || filterStatus || filterCapacity || filterActive !== 'all') && (
            <Button
              size="small"
              onClick={() => {
                setFilterIdentifier('')
                setFilterStatus('')
                setFilterCapacity('')
                setFilterActive('all')
              }}
            >
              Limpiar filtros
            </Button>
          )}
        </Box>
      </Paper>

      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <DataTable
          columns={columns}
          data={filteredVehicles}
          loading={isLoading}
          emptyMessage={
            filterIdentifier || filterStatus || filterCapacity || filterActive !== 'all'
              ? 'No se encontraron vehículos con los filtros aplicados'
              : 'No hay vehículos registrados'
          }
        />
      )}

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogTitle>{editingVehicle ? 'Editar Vehículo' : 'Nuevo Vehículo'}</DialogTitle>
          <DialogContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
              <TextField
                label="Identificador (Patente/Código)"
                {...register('identifier', { required: 'El identificador es requerido' })}
                error={!!errors.identifier}
                helperText={errors.identifier?.message}
                fullWidth
                autoFocus
              />
              <TextField
                label="Capacidad (Personas)"
                type="number"
                {...register('capacity', {
                  required: 'La capacidad es requerida',
                  min: { value: 1, message: 'Debe ser al menos 1' },
                })}
                error={!!errors.capacity}
                helperText={errors.capacity?.message}
                fullWidth
              />
              <Controller
                name="status"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth>
                    <InputLabel>Estado</InputLabel>
                    <Select {...field} label="Estado">
                      <MenuItem value="available">Disponible</MenuItem>
                      <MenuItem value="in_use">En Uso</MenuItem>
                      <MenuItem value="maintenance">Mantenimiento</MenuItem>
                      <MenuItem value="unavailable">No Disponible</MenuItem>
                    </Select>
                  </FormControl>
                )}
              />
              <Controller
                name="base_location"
                control={control}
                rules={{ required: 'La ubicación base es requerida' }}
                render={({ field }) => (
                  <LocationPicker
                    value={field.value}
                    onChange={field.onChange}
                    label="Ubicación Base"
                    error={!!errors.base_location}
                    helperText={errors.base_location?.message}
                  />
                )}
              />
              <Controller
                name="is_active"
                control={control}
                render={({ field }) => (
                  <FormControlLabel
                    control={<Switch checked={field.value} onChange={field.onChange} />}
                    label="Activo"
                  />
                )}
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenDialog(false)}>Cancelar</Button>
            <Button
              type="submit"
              variant="contained"
              disabled={createMutation.isPending || updateMutation.isPending}
            >
              {editingVehicle ? 'Actualizar' : 'Crear'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      <ConfirmDialog
        open={deleteDialogOpen}
        title="Eliminar Vehículo"
        message={`¿Estás seguro de que deseas eliminar el vehículo "${vehicleToDelete?.identifier}"? Esta acción no se puede deshacer.`}
        onConfirm={() => vehicleToDelete && deleteMutation.mutate(vehicleToDelete.id)}
        onCancel={() => {
          setDeleteDialogOpen(false)
          setVehicleToDelete(null)
        }}
        confirmText="Eliminar"
        cancelText="Cancelar"
      />
    </Box>
  )
}
