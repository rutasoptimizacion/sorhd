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
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Chip,
  Paper,
  Grid,
} from '@mui/material'
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon, Person as PersonIcon, FilterList as FilterListIcon } from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm, Controller } from 'react-hook-form'
import { DataTable, LoadingSpinner, ErrorMessage, ConfirmDialog, LocationPicker } from '@/components/common'
import { patientService } from '@/services/patientService'
import { userService } from '@/services/userService'
import type { Patient, PatientCreate, UserRole } from '@/types'
import type { Column } from '@/components/common/DataTable'
import { format } from 'date-fns'
import { validateRut, formatRut } from '@/lib/rutValidator'

export default function PatientsPage() {
  const [openDialog, setOpenDialog] = useState(false)
  const [editingPatient, setEditingPatient] = useState<Patient | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [patientToDelete, setPatientToDelete] = useState<Patient | null>(null)

  // Filtros
  const [filterName, setFilterName] = useState('')
  const [filterRut, setFilterRut] = useState('')
  const [filterPhone, setFilterPhone] = useState('')
  const [filterEmail, setFilterEmail] = useState('')
  const [filterAddress, setFilterAddress] = useState('')

  const queryClient = useQueryClient()

  const { data: patientsResponse, isLoading, error } = useQuery({
    queryKey: ['patients'],
    queryFn: () => patientService.getAll(),
  })

  // Fetch users with patient role for selector
  const { data: usersResponse } = useQuery({
    queryKey: ['users', 'patient'],
    queryFn: () => userService.getAll(),
  })

  // Filter users: only show patient role users that are not already assigned
  const assignedUserIds = patientsResponse?.items.map((p) => p.user_id).filter((id) => id !== undefined) || []
  const availableUsers = usersResponse?.items.filter(
    (u) => u.role === 'patient' && (!assignedUserIds.includes(u.id) || u.id === editingPatient?.user_id)
  ) || []

  // Filtrado de pacientes
  const filteredPatients = useMemo(() => {
    if (!patientsResponse?.items) return []

    return patientsResponse.items.filter((patient) => {
      // Filtro por nombre
      if (filterName && !patient.name.toLowerCase().includes(filterName.toLowerCase())) {
        return false
      }

      // Filtro por RUT
      if (filterRut && patient.rut) {
        const cleanFilterRut = filterRut.replace(/[.-]/g, '').toLowerCase()
        const cleanPatientRut = patient.rut.replace(/[.-]/g, '').toLowerCase()
        if (!cleanPatientRut.includes(cleanFilterRut)) {
          return false
        }
      }

      // Filtro por teléfono
      if (filterPhone && patient.phone && !patient.phone.includes(filterPhone)) {
        return false
      }

      // Filtro por email
      if (filterEmail && patient.email && !patient.email.toLowerCase().includes(filterEmail.toLowerCase())) {
        return false
      }

      // Filtro por dirección
      if (filterAddress && patient.address && !patient.address.toLowerCase().includes(filterAddress.toLowerCase())) {
        return false
      }

      return true
    })
  }, [patientsResponse, filterName, filterRut, filterPhone, filterEmail, filterAddress])

  const createMutation = useMutation({
    mutationFn: (data: PatientCreate) => patientService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patients'] })
      setOpenDialog(false)
      reset()
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: PatientCreate }) =>
      patientService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patients'] })
      setOpenDialog(false)
      setEditingPatient(null)
      reset()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => patientService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patients'] })
      setDeleteDialogOpen(false)
      setPatientToDelete(null)
    },
  })

  const {
    register,
    handleSubmit,
    reset,
    control,
    setValue,
    watch,
    formState: { errors },
  } = useForm<PatientCreate>({
    defaultValues: {
      user_id: undefined,
      name: '',
      rut: '',
      phone: '',
      email: '',
      date_of_birth: '',
      medical_notes: '',
      address: '',
      location: undefined,
    },
  })

  const addressValue = watch('address')
  const locationValue = watch('location')

  const handleCreate = () => {
    setEditingPatient(null)
    reset({
      user_id: undefined,
      name: '',
      rut: '',
      phone: '',
      email: '',
      date_of_birth: '',
      medical_notes: '',
      address: '',
      location: undefined,
    })
    setOpenDialog(true)
  }

  const handleEdit = (patient: Patient) => {
    setEditingPatient(patient)
    reset({
      user_id: patient.user_id,
      name: patient.name,
      rut: patient.rut ? formatRut(patient.rut) : '',
      phone: patient.phone || '',
      email: patient.email || '',
      date_of_birth: patient.date_of_birth || '',
      medical_notes: patient.medical_notes || '',
      address: patient.address || '',
      location: patient.location,
    })
    setOpenDialog(true)
  }

  const handleDelete = (patient: Patient) => {
    setPatientToDelete(patient)
    setDeleteDialogOpen(true)
  }

  const onSubmit = (data: PatientCreate) => {
    if (editingPatient) {
      updateMutation.mutate({ id: editingPatient.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  const columns: Column<Patient>[] = [
    { id: 'id', label: 'ID', sortable: true, minWidth: 80 },
    { id: 'name', label: 'Nombre', sortable: true, minWidth: 200 },
    {
      id: 'rut',
      label: 'RUT',
      minWidth: 130,
      render: (row) => row.rut ? formatRut(row.rut) : '-',
    },
    { id: 'phone', label: 'Teléfono', minWidth: 130 },
    { id: 'email', label: 'Email', minWidth: 200 },
    {
      id: 'address',
      label: 'Dirección',
      minWidth: 250,
      render: (row) => {
        if (row.address) {
          const truncated = row.address.length > 50 ? row.address.substring(0, 50) + '...' : row.address
          return <span title={row.address}>{truncated}</span>
        }
        return <span title={`Lat: ${row.location.latitude}, Lng: ${row.location.longitude}`}>
          {`${row.location.latitude.toFixed(4)}, ${row.location.longitude.toFixed(4)}`}
        </span>
      },
    },
    {
      id: 'user_id',
      label: 'Acceso App',
      align: 'center',
      minWidth: 120,
      render: (row) => {
        const user = usersResponse?.items.find((u) => u.id === row.user_id)
        return row.user_id ? (
          <Chip
            icon={<PersonIcon />}
            label={user?.username || 'Usuario'}
            color="success"
            size="small"
            title={user?.full_name || ''}
          />
        ) : (
          <Chip label="Sin acceso" size="small" variant="outlined" />
        )
      },
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
        <Typography variant="h4">Pacientes</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>
          Nuevo Paciente
        </Button>
      </Box>

      {/* Filtros */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <FilterListIcon sx={{ mr: 1, color: 'text.secondary' }} />
          <Typography variant="h6">Filtros</Typography>
        </Box>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={2.4}>
            <TextField
              label="Nombre"
              value={filterName}
              onChange={(e) => setFilterName(e.target.value)}
              size="small"
              fullWidth
              placeholder="Buscar por nombre..."
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <TextField
              label="RUT"
              value={filterRut}
              onChange={(e) => setFilterRut(e.target.value)}
              size="small"
              fullWidth
              placeholder="12345678-9"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <TextField
              label="Teléfono"
              value={filterPhone}
              onChange={(e) => setFilterPhone(e.target.value)}
              size="small"
              fullWidth
              placeholder="+56912345678"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <TextField
              label="Email"
              value={filterEmail}
              onChange={(e) => setFilterEmail(e.target.value)}
              size="small"
              fullWidth
              placeholder="correo@ejemplo.com"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <TextField
              label="Dirección/Comuna"
              value={filterAddress}
              onChange={(e) => setFilterAddress(e.target.value)}
              size="small"
              fullWidth
              placeholder="Viña del Mar..."
            />
          </Grid>
        </Grid>
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Mostrando {filteredPatients.length} de {patientsResponse?.items.length || 0} pacientes
          </Typography>
          {(filterName || filterRut || filterPhone || filterEmail || filterAddress) && (
            <Button
              size="small"
              onClick={() => {
                setFilterName('')
                setFilterRut('')
                setFilterPhone('')
                setFilterEmail('')
                setFilterAddress('')
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
            data={filteredPatients}
            loading={isLoading}
            emptyMessage={
              filterName || filterRut || filterPhone || filterEmail || filterAddress
                ? 'No se encontraron pacientes con los filtros aplicados'
                : 'No hay pacientes registrados'
            }
          />
        )}
      </Box>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogTitle>{editingPatient ? 'Editar Paciente' : 'Nuevo Paciente'}</DialogTitle>
          <DialogContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
              <TextField
                label="Nombre Completo"
                {...register('name', { required: 'El nombre es requerido' })}
                error={!!errors.name}
                helperText={errors.name?.message}
                fullWidth
                autoFocus
              />

              <Controller
                name="user_id"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth>
                    <InputLabel>Usuario para App Móvil (Opcional)</InputLabel>
                    <Select
                      {...field}
                      value={field.value || ''}
                      onChange={(e) => field.onChange(e.target.value === '' ? undefined : Number(e.target.value))}
                      label="Usuario para App Móvil (Opcional)"
                    >
                      <MenuItem value="">
                        <em>Sin usuario asignado</em>
                      </MenuItem>
                      {availableUsers.map((user) => (
                        <MenuItem key={user.id} value={user.id}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <PersonIcon fontSize="small" />
                            <span>{user.full_name} ({user.username})</span>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                    <Typography variant="caption" sx={{ mt: 0.5, ml: 1.75, color: 'text.secondary' }}>
                      Asigna un usuario para que el paciente pueda usar la aplicación móvil
                    </Typography>
                  </FormControl>
                )}
              />

              <TextField
                label="RUT"
                placeholder="12.345.678-5"
                {...register('rut', {
                  validate: (value) => {
                    if (!value || value.trim() === '') return true // Optional field
                    const { valid, error } = validateRut(value)
                    return valid || error
                  },
                  onChange: (e) => {
                    const value = e.target.value
                    if (value && value.trim()) {
                      // Auto-format as user types
                      const formatted = formatRut(value)
                      if (formatted !== value) {
                        setValue('rut', formatted)
                      }
                    }
                  },
                })}
                error={!!errors.rut}
                helperText={errors.rut?.message || 'Opcional. Formato: 12.345.678-5'}
                fullWidth
              />
              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField label="Teléfono" {...register('phone')} fullWidth />
                <TextField label="Email" type="email" {...register('email')} fullWidth />
              </Box>
              <TextField
                label="Fecha de Nacimiento"
                type="date"
                {...register('date_of_birth')}
                fullWidth
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                label="Notas Médicas"
                {...register('medical_notes')}
                multiline
                rows={3}
                fullWidth
              />
              <Box>
                <Controller
                  name="location"
                  control={control}
                  rules={{
                    validate: () => {
                      // Either address or location must be provided
                      if (!addressValue && !locationValue) {
                        return 'Debe proporcionar una dirección o coordenadas'
                      }
                      return true
                    },
                  }}
                  render={({ field }) => (
                    <Controller
                      name="address"
                      control={control}
                      render={({ field: addressField }) => (
                        <LocationPicker
                          value={field.value}
                          address={addressField.value}
                          onChange={field.onChange}
                          onAddressChange={addressField.onChange}
                          label="Ubicación del Domicilio"
                          error={!!errors.location}
                          helperText={errors.location?.message}
                          allowAddressInput={true}
                        />
                      )}
                    />
                  )}
                />
              </Box>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenDialog(false)}>Cancelar</Button>
            <Button
              type="submit"
              variant="contained"
              disabled={createMutation.isPending || updateMutation.isPending}
            >
              {editingPatient ? 'Actualizar' : 'Crear'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      <ConfirmDialog
        open={deleteDialogOpen}
        title="Eliminar Paciente"
        message={`¿Estás seguro de que deseas eliminar al paciente "${patientToDelete?.name}"? Esta acción no se puede deshacer.`}
        onConfirm={() => patientToDelete && deleteMutation.mutate(patientToDelete.id)}
        onCancel={() => {
          setDeleteDialogOpen(false)
          setPatientToDelete(null)
        }}
        confirmText="Eliminar"
        cancelText="Cancelar"
      />
    </Box>
  )
}
