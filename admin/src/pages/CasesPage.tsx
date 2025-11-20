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
  Checkbox,
  Paper,
  Grid,
} from '@mui/material'
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon, FilterList as FilterListIcon } from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm, Controller } from 'react-hook-form'
import { DataTable, LoadingSpinner, ErrorMessage, ConfirmDialog, LocationPicker } from '@/components/common'
import { caseService } from '@/services/caseService'
import { patientService } from '@/services/patientService'
import { careTypeService } from '@/services/careTypeService'
import type { Case, CaseCreate, CaseStatus, CasePriority } from '@/types'
import { CasePriority as CasePriorityEnum } from '@/types'
import type { Column } from '@/components/common/DataTable'
import { format } from 'date-fns'

export default function CasesPage() {
  const [openDialog, setOpenDialog] = useState(false)
  const [editingCase, setEditingCase] = useState<Case | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [caseToDelete, setCaseToDelete] = useState<Case | null>(null)
  const [usePatientLocation, setUsePatientLocation] = useState(true)

  // Filtros
  const [filterPatient, setFilterPatient] = useState<number | ''>('')
  const [filterCareType, setFilterCareType] = useState<number | ''>('')
  const [filterDateFrom, setFilterDateFrom] = useState('')
  const [filterDateTo, setFilterDateTo] = useState('')
  const [filterPriority, setFilterPriority] = useState<CasePriority | ''>('')
  const [filterStatus, setFilterStatus] = useState<CaseStatus | ''>('')

  const queryClient = useQueryClient()

  const { data: casesResponse, isLoading, error } = useQuery({
    queryKey: ['cases'],
    queryFn: () => caseService.getAll(),
  })

  const { data: patientsResponse } = useQuery({
    queryKey: ['patients'],
    queryFn: () => patientService.getAll(),
  })

  const { data: careTypesResponse } = useQuery({
    queryKey: ['careTypes'],
    queryFn: () => careTypeService.getAll(),
  })

  // Filtrado de casos
  const filteredCases = useMemo(() => {
    if (!casesResponse?.items) return []

    return casesResponse.items.filter((caseItem) => {
      // Filtro por paciente
      if (filterPatient && caseItem.patient_id !== filterPatient) {
        return false
      }

      // Filtro por tipo de atención
      if (filterCareType && caseItem.care_type_id !== filterCareType) {
        return false
      }

      // Filtro por fecha desde
      if (filterDateFrom && caseItem.scheduled_date < filterDateFrom) {
        return false
      }

      // Filtro por fecha hasta
      if (filterDateTo && caseItem.scheduled_date > filterDateTo) {
        return false
      }

      // Filtro por prioridad
      if (filterPriority && caseItem.priority !== filterPriority) {
        return false
      }

      // Filtro por estado
      if (filterStatus && caseItem.status !== filterStatus) {
        return false
      }

      return true
    })
  }, [casesResponse, filterPatient, filterCareType, filterDateFrom, filterDateTo, filterPriority, filterStatus])

  const createMutation = useMutation({
    mutationFn: (data: CaseCreate) => caseService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cases'] })
      setOpenDialog(false)
      reset()
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: CaseCreate }) => caseService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cases'] })
      setOpenDialog(false)
      setEditingCase(null)
      reset()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => caseService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cases'] })
      setDeleteDialogOpen(false)
      setCaseToDelete(null)
    },
  })

  const {
    register,
    handleSubmit,
    reset,
    control,
    watch,
    formState: { errors },
  } = useForm<CaseCreate>({
    defaultValues: {
      patient_id: 0,
      care_type_id: 0,
      scheduled_date: format(new Date(), 'yyyy-MM-dd'),
      priority: CasePriorityEnum.MEDIUM,
      notes: '',
      location: { latitude: -33.4489, longitude: -70.6693 },
      time_window_start: '',
      time_window_end: '',
    },
  })

  const selectedPatientId = watch('patient_id')

  const handleCreate = () => {
    setEditingCase(null)
    setUsePatientLocation(true)
    reset({
      patient_id: 0,
      care_type_id: 0,
      scheduled_date: format(new Date(), 'yyyy-MM-dd'),
      priority: CasePriorityEnum.MEDIUM,
      notes: '',
      location: { latitude: -33.4489, longitude: -70.6693 },
      time_window_start: '',
      time_window_end: '',
    })
    setOpenDialog(true)
  }

  const handleEdit = (caseItem: Case) => {
    setEditingCase(caseItem)
    setUsePatientLocation(false)
    reset({
      patient_id: caseItem.patient_id,
      care_type_id: caseItem.care_type_id,
      scheduled_date: caseItem.scheduled_date,
      priority: caseItem.priority,
      notes: caseItem.notes || '',
      location: caseItem.location,
      time_window_start: caseItem.time_window_start || '',
      time_window_end: caseItem.time_window_end || '',
    })
    setOpenDialog(true)
  }

  const handleDelete = (caseItem: Case) => {
    setCaseToDelete(caseItem)
    setDeleteDialogOpen(true)
  }

  const onSubmit = (data: CaseCreate) => {
    // If using patient location, get it from patient data
    if (usePatientLocation && selectedPatientId) {
      const patient = patientsResponse?.items.find((p) => p.id === selectedPatientId)
      if (patient) {
        data.location = patient.location
      }
    }

    if (editingCase) {
      updateMutation.mutate({ id: editingCase.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  const getPatientName = (patientId: number) => {
    return patientsResponse?.items.find((p) => p.id === patientId)?.name || `ID: ${patientId}`
  }

  const getCareTypeName = (careTypeId: number) => {
    return careTypesResponse?.items.find((ct) => ct.id === careTypeId)?.name || `ID: ${careTypeId}`
  }

  const getStatusLabel = (status: CaseStatus) => {
    const labels = {
      pending: 'Pendiente',
      assigned: 'Asignado',
      completed: 'Completado',
      cancelled: 'Cancelado',
    }
    return labels[status]
  }

  const getStatusColor = (status: CaseStatus) => {
    const colors: Record<CaseStatus, 'warning' | 'info' | 'success' | 'error'> = {
      pending: 'warning',
      assigned: 'info',
      completed: 'success',
      cancelled: 'error',
    }
    return colors[status]
  }

  const getPriorityLabel = (priority: CasePriority) => {
    const labels = {
      low: 'Baja',
      medium: 'Media',
      high: 'Alta',
      urgent: 'Urgente',
    }
    return labels[priority]
  }

  const getPriorityColor = (priority: CasePriority) => {
    const colors: Record<CasePriority, 'success' | 'info' | 'warning' | 'error'> = {
      low: 'success',
      medium: 'info',
      high: 'warning',
      urgent: 'error',
    }
    return colors[priority]
  }

  const columns: Column<Case>[] = [
    { id: 'id', label: 'ID', sortable: true, minWidth: 80 },
    {
      id: 'patient_id',
      label: 'Paciente',
      sortable: true,
      minWidth: 200,
      render: (row) => getPatientName(row.patient_id),
    },
    {
      id: 'care_type_id',
      label: 'Tipo de Atención',
      minWidth: 180,
      render: (row) => getCareTypeName(row.care_type_id),
    },
    {
      id: 'scheduled_date',
      label: 'Fecha',
      sortable: true,
      minWidth: 120,
      render: (row) => {
        // Parse date as local date to avoid timezone conversion
        const [year, month, day] = row.scheduled_date.split('-').map(Number)
        return format(new Date(year, month - 1, day), 'dd/MM/yyyy')
      },
    },
    {
      id: 'priority',
      label: 'Prioridad',
      minWidth: 100,
      render: (row) => (
        <Chip
          label={getPriorityLabel(row.priority)}
          color={getPriorityColor(row.priority)}
          size="small"
        />
      ),
    },
    {
      id: 'status',
      label: 'Estado',
      minWidth: 120,
      render: (row) => (
        <Chip label={getStatusLabel(row.status)} color={getStatusColor(row.status)} size="small" />
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
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Casos de Atención</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>
          Nuevo Caso
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
            <FormControl fullWidth size="small">
              <InputLabel>Paciente</InputLabel>
              <Select
                value={filterPatient}
                onChange={(e) => setFilterPatient(e.target.value as number | '')}
                label="Paciente"
              >
                <MenuItem value="">Todos</MenuItem>
                {patientsResponse?.items.map((patient) => (
                  <MenuItem key={patient.id} value={patient.id}>
                    {patient.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Tipo de Atención</InputLabel>
              <Select
                value={filterCareType}
                onChange={(e) => setFilterCareType(e.target.value as number | '')}
                label="Tipo de Atención"
              >
                <MenuItem value="">Todos</MenuItem>
                {careTypesResponse?.items.map((careType) => (
                  <MenuItem key={careType.id} value={careType.id}>
                    {careType.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Prioridad</InputLabel>
              <Select
                value={filterPriority}
                onChange={(e) => setFilterPriority(e.target.value as CasePriority | '')}
                label="Prioridad"
              >
                <MenuItem value="">Todas</MenuItem>
                <MenuItem value="low">Baja</MenuItem>
                <MenuItem value="medium">Media</MenuItem>
                <MenuItem value="high">Alta</MenuItem>
                <MenuItem value="urgent">Urgente</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Estado</InputLabel>
              <Select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value as CaseStatus | '')}
                label="Estado"
              >
                <MenuItem value="">Todos</MenuItem>
                <MenuItem value="pending">Pendiente</MenuItem>
                <MenuItem value="assigned">Asignado</MenuItem>
                <MenuItem value="completed">Completado</MenuItem>
                <MenuItem value="cancelled">Cancelado</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              label="Fecha Desde"
              type="date"
              value={filterDateFrom}
              onChange={(e) => setFilterDateFrom(e.target.value)}
              size="small"
              fullWidth
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              label="Fecha Hasta"
              type="date"
              value={filterDateTo}
              onChange={(e) => setFilterDateTo(e.target.value)}
              size="small"
              fullWidth
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
        </Grid>
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Mostrando {filteredCases.length} de {casesResponse?.items.length || 0} casos
          </Typography>
          {(filterPatient || filterCareType || filterDateFrom || filterDateTo || filterPriority || filterStatus) && (
            <Button
              size="small"
              onClick={() => {
                setFilterPatient('')
                setFilterCareType('')
                setFilterDateFrom('')
                setFilterDateTo('')
                setFilterPriority('')
                setFilterStatus('')
              }}
            >
              Limpiar filtros
            </Button>
          )}
        </Box>
      </Paper>

      <Box sx={{ flex: 1, minHeight: 0 }}>
        {isLoading ? (
          <LoadingSpinner />
        ) : (
          <DataTable
            columns={columns}
            data={filteredCases}
            loading={isLoading}
            emptyMessage={
              filterPatient || filterCareType || filterDateFrom || filterDateTo || filterPriority || filterStatus
                ? 'No se encontraron casos con los filtros aplicados'
                : 'No hay casos registrados'
            }
          />
        )}
      </Box>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogTitle>{editingCase ? 'Editar Caso' : 'Nuevo Caso'}</DialogTitle>
          <DialogContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
              <Controller
                name="patient_id"
                control={control}
                rules={{ required: 'El paciente es requerido', min: { value: 1, message: 'Seleccione un paciente' } }}
                render={({ field }) => (
                  <FormControl fullWidth error={!!errors.patient_id}>
                    <InputLabel>Paciente</InputLabel>
                    <Select {...field} label="Paciente">
                      <MenuItem value={0} disabled>
                        Seleccione un paciente
                      </MenuItem>
                      {patientsResponse?.items.map((patient) => (
                        <MenuItem key={patient.id} value={patient.id}>
                          {patient.name}
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.patient_id && (
                      <Typography variant="caption" color="error" sx={{ mt: 0.5, ml: 1.75 }}>
                        {errors.patient_id.message}
                      </Typography>
                    )}
                  </FormControl>
                )}
              />

              <Controller
                name="care_type_id"
                control={control}
                rules={{ required: 'El tipo de atención es requerido', min: { value: 1, message: 'Seleccione un tipo de atención' } }}
                render={({ field }) => (
                  <FormControl fullWidth error={!!errors.care_type_id}>
                    <InputLabel>Tipo de Atención</InputLabel>
                    <Select {...field} label="Tipo de Atención">
                      <MenuItem value={0} disabled>
                        Seleccione un tipo de atención
                      </MenuItem>
                      {careTypesResponse?.items.map((careType) => (
                        <MenuItem key={careType.id} value={careType.id}>
                          {careType.name} ({careType.estimated_duration} min)
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.care_type_id && (
                      <Typography variant="caption" color="error" sx={{ mt: 0.5, ml: 1.75 }}>
                        {errors.care_type_id.message}
                      </Typography>
                    )}
                  </FormControl>
                )}
              />

              <TextField
                label="Fecha Programada"
                type="date"
                {...register('scheduled_date', { required: 'La fecha es requerida' })}
                error={!!errors.scheduled_date}
                helperText={errors.scheduled_date?.message}
                fullWidth
                InputLabelProps={{ shrink: true }}
              />

              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  label="Ventana de Inicio (opcional)"
                  type="time"
                  {...register('time_window_start')}
                  fullWidth
                  InputLabelProps={{ shrink: true }}
                  helperText="Hora más temprana para la visita"
                />
                <TextField
                  label="Ventana de Fin (opcional)"
                  type="time"
                  {...register('time_window_end')}
                  fullWidth
                  InputLabelProps={{ shrink: true }}
                  helperText="Hora más tardía para la visita"
                />
              </Box>

              <Controller
                name="priority"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth>
                    <InputLabel>Prioridad</InputLabel>
                    <Select {...field} label="Prioridad">
                      <MenuItem value="low">Baja</MenuItem>
                      <MenuItem value="medium">Media</MenuItem>
                      <MenuItem value="high">Alta</MenuItem>
                      <MenuItem value="urgent">Urgente</MenuItem>
                    </Select>
                  </FormControl>
                )}
              />

              <TextField label="Notas" {...register('notes')} multiline rows={3} fullWidth />

              <FormControlLabel
                control={
                  <Checkbox
                    checked={usePatientLocation}
                    onChange={(e) => setUsePatientLocation(e.target.checked)}
                  />
                }
                label="Usar ubicación del paciente"
              />

              {!usePatientLocation && (
                <Controller
                  name="location"
                  control={control}
                  rules={{ required: !usePatientLocation ? 'La ubicación es requerida' : false }}
                  render={({ field }) => (
                    <LocationPicker
                      value={field.value}
                      onChange={field.onChange}
                      label="Ubicación de la Visita"
                      error={!!errors.location}
                      helperText={errors.location?.message}
                    />
                  )}
                />
              )}
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenDialog(false)}>Cancelar</Button>
            <Button
              type="submit"
              variant="contained"
              disabled={createMutation.isPending || updateMutation.isPending}
            >
              {editingCase ? 'Actualizar' : 'Crear'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      <ConfirmDialog
        open={deleteDialogOpen}
        title="Eliminar Caso"
        message={`¿Estás seguro de que deseas eliminar este caso? Esta acción no se puede deshacer.`}
        onConfirm={() => caseToDelete && deleteMutation.mutate(caseToDelete.id)}
        onCancel={() => {
          setDeleteDialogOpen(false)
          setCaseToDelete(null)
        }}
        confirmText="Eliminar"
        cancelText="Cancelar"
      />
    </Box>
  )
}
