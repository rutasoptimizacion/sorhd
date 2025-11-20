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
  OutlinedInput,
  FormControlLabel,
  Switch,
  Alert,
  Paper,
  Grid,
} from '@mui/material'
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon, Person as PersonIcon, FilterList as FilterListIcon } from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm, Controller } from 'react-hook-form'
import { DataTable, LoadingSpinner, ErrorMessage, ConfirmDialog, LocationPicker } from '@/components/common'
import { personnelService } from '@/services/personnelService'
import { skillService } from '@/services/skillService'
import { userService } from '@/services/userService'
import type { Personnel, PersonnelCreate } from '@/types'
import type { Column } from '@/components/common/DataTable'

export default function PersonnelPage() {
  const [openDialog, setOpenDialog] = useState(false)
  const [editingPersonnel, setEditingPersonnel] = useState<Personnel | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [personnelToDelete, setPersonnelToDelete] = useState<Personnel | null>(null)

  // Filtros
  const [filterName, setFilterName] = useState('')
  const [filterPhone, setFilterPhone] = useState('')
  const [filterEmail, setFilterEmail] = useState('')
  const [filterSkill, setFilterSkill] = useState<number | ''>('')
  const [filterActive, setFilterActive] = useState<'all' | 'active' | 'inactive'>('all')

  const queryClient = useQueryClient()

  // Fetch personnel and skills
  const { data: personnelResponse, isLoading, error } = useQuery({
    queryKey: ['personnel'],
    queryFn: () => personnelService.getAll(),
  })

  const { data: skills } = useQuery({
    queryKey: ['skills'],
    queryFn: () => skillService.getAll(),
  })

  // Fetch users with clinical_team role for selector
  const { data: usersResponse } = useQuery({
    queryKey: ['users', 'clinical_team'],
    queryFn: () => userService.getAll(),
  })

  // Filter users: only show clinical_team role users that are not already assigned
  const assignedUserIds = personnelResponse?.items.map((p) => p.user_id).filter((id) => id !== undefined) || []
  const availableUsers = usersResponse?.items.filter(
    (u) => u.role === 'clinical_team' && (!assignedUserIds.includes(u.id) || u.id === editingPersonnel?.user_id)
  ) || []

  // Filtrado de personal
  const filteredPersonnel = useMemo(() => {
    if (!personnelResponse?.items) return []

    return personnelResponse.items.filter((person) => {
      // Filtro por nombre
      if (filterName && !person.name.toLowerCase().includes(filterName.toLowerCase())) {
        return false
      }

      // Filtro por teléfono
      if (filterPhone && person.phone && !person.phone.includes(filterPhone)) {
        return false
      }

      // Filtro por email
      if (filterEmail && person.email && !person.email.toLowerCase().includes(filterEmail.toLowerCase())) {
        return false
      }

      // Filtro por habilidad
      if (filterSkill && !person.skill_ids.includes(filterSkill as number)) {
        return false
      }

      // Filtro por activo/inactivo
      if (filterActive === 'active' && !person.is_active) {
        return false
      }
      if (filterActive === 'inactive' && person.is_active) {
        return false
      }

      return true
    })
  }, [personnelResponse, filterName, filterPhone, filterEmail, filterSkill, filterActive])

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: PersonnelCreate) => personnelService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['personnel'] })
      setOpenDialog(false)
      reset()
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: PersonnelCreate }) =>
      personnelService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['personnel'] })
      setOpenDialog(false)
      setEditingPersonnel(null)
      reset()
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => personnelService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['personnel'] })
      setDeleteDialogOpen(false)
      setPersonnelToDelete(null)
    },
  })

  // Form
  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm<PersonnelCreate>({
    defaultValues: {
      user_id: undefined,
      name: '',
      phone: '',
      email: '',
      is_active: true,
      start_location: undefined, // Optional field
      work_hours_start: '08:00',
      work_hours_end: '17:00',
      skill_ids: [],
    },
  })

  const handleCreate = () => {
    setEditingPersonnel(null)
    reset({
      user_id: undefined,
      name: '',
      phone: '',
      email: '',
      is_active: true,
      start_location: undefined, // Optional field
      work_hours_start: '08:00',
      work_hours_end: '17:00',
      skill_ids: [],
    })
    setOpenDialog(true)
  }

  const handleEdit = (personnel: Personnel) => {
    setEditingPersonnel(personnel)
    reset({
      user_id: personnel.user_id,
      name: personnel.name,
      phone: personnel.phone || '',
      email: personnel.email || '',
      is_active: personnel.is_active,
      start_location: personnel.start_location,
      work_hours_start: personnel.work_hours_start,
      work_hours_end: personnel.work_hours_end,
      skill_ids: personnel.skill_ids,
    })
    setOpenDialog(true)
  }

  const handleDelete = (personnel: Personnel) => {
    setPersonnelToDelete(personnel)
    setDeleteDialogOpen(true)
  }

  const onSubmit = (data: PersonnelCreate) => {
    if (editingPersonnel) {
      updateMutation.mutate({ id: editingPersonnel.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  const getSkillNames = (skillIds: number[]) => {
    if (!skills) return ''
    return skills
      .filter((s) => skillIds.includes(s.id))
      .map((s) => s.name)
      .join(', ')
  }

  const columns: Column<Personnel>[] = [
    { id: 'id', label: 'ID', sortable: true, minWidth: 80 },
    { id: 'name', label: 'Nombre', sortable: true, minWidth: 200 },
    { id: 'phone', label: 'Teléfono', minWidth: 130 },
    { id: 'email', label: 'Email', minWidth: 200 },
    {
      id: 'work_hours_start',
      label: 'Horario',
      minWidth: 120,
      render: (row) => `${row.work_hours_start} - ${row.work_hours_end}`,
    },
    {
      id: 'skill_ids',
      label: 'Habilidades',
      minWidth: 200,
      render: (row) => getSkillNames(row.skill_ids),
    },
    {
      id: 'is_active',
      label: 'Estado',
      minWidth: 100,
      align: 'center',
      render: (row) => (
        <Chip label={row.is_active ? 'Activo' : 'Inactivo'} color={row.is_active ? 'success' : 'default'} size="small" />
      ),
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
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Personal Clínico</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>
          Nuevo Personal
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
            <FormControl fullWidth size="small">
              <InputLabel>Habilidad</InputLabel>
              <Select
                value={filterSkill}
                onChange={(e) => setFilterSkill(e.target.value as number | '')}
                label="Habilidad"
              >
                <MenuItem value="">Todas</MenuItem>
                {skills?.map((skill) => (
                  <MenuItem key={skill.id} value={skill.id}>
                    {skill.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <FormControl fullWidth size="small">
              <InputLabel>Estado</InputLabel>
              <Select
                value={filterActive}
                onChange={(e) => setFilterActive(e.target.value as 'all' | 'active' | 'inactive')}
                label="Estado"
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
            Mostrando {filteredPersonnel.length} de {personnelResponse?.items.length || 0} personal
          </Typography>
          {(filterName || filterPhone || filterEmail || filterSkill || filterActive !== 'all') && (
            <Button
              size="small"
              onClick={() => {
                setFilterName('')
                setFilterPhone('')
                setFilterEmail('')
                setFilterSkill('')
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
          data={filteredPersonnel}
          loading={isLoading}
          emptyMessage={
            filterName || filterPhone || filterEmail || filterSkill || filterActive !== 'all'
              ? 'No se encontró personal con los filtros aplicados'
              : 'No hay personal registrado'
          }
        />
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogTitle>{editingPersonnel ? 'Editar Personal' : 'Nuevo Personal'}</DialogTitle>
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
                      Asigna un usuario para que el personal pueda usar la aplicación móvil
                    </Typography>
                  </FormControl>
                )}
              />

              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField label="Teléfono" {...register('phone')} fullWidth />
                <TextField label="Email" type="email" {...register('email')} fullWidth />
              </Box>

              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  label="Hora de Inicio"
                  type="time"
                  {...register('work_hours_start', { required: 'La hora de inicio es requerida' })}
                  error={!!errors.work_hours_start}
                  helperText={errors.work_hours_start?.message}
                  fullWidth
                  InputLabelProps={{ shrink: true }}
                />
                <TextField
                  label="Hora de Fin"
                  type="time"
                  {...register('work_hours_end', { required: 'La hora de fin es requerida' })}
                  error={!!errors.work_hours_end}
                  helperText={errors.work_hours_end?.message}
                  fullWidth
                  InputLabelProps={{ shrink: true }}
                />
              </Box>

              <Controller
                name="skill_ids"
                control={control}
                rules={{ required: 'Debe seleccionar al menos una habilidad' }}
                render={({ field }) => (
                  <FormControl fullWidth error={!!errors.skill_ids}>
                    <InputLabel>Habilidades</InputLabel>
                    <Select
                      {...field}
                      multiple
                      input={<OutlinedInput label="Habilidades" />}
                      renderValue={(selected) => (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {(selected as number[]).map((value) => {
                            const skill = skills?.find((s) => s.id === value)
                            return <Chip key={value} label={skill?.name || value} size="small" />
                          })}
                        </Box>
                      )}
                    >
                      {skills?.map((skill) => (
                        <MenuItem key={skill.id} value={skill.id}>
                          {skill.name}
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.skill_ids && (
                      <Typography variant="caption" color="error" sx={{ mt: 0.5, ml: 1.75 }}>
                        {errors.skill_ids.message}
                      </Typography>
                    )}
                  </FormControl>
                )}
              />

              <Alert severity="info" sx={{ mb: 1 }}>
                <Typography variant="body2">
                  <strong>Ubicación de Inicio (Opcional):</strong> Este campo se utilizará
                  cuando se habilite el modo "Pickup" en futuras versiones del sistema.
                  El modo Pickup optimizará rutas considerando la ubicación inicial del personal.
                </Typography>
              </Alert>

              <Controller
                name="start_location"
                control={control}
                render={({ field }) => (
                  <LocationPicker
                    value={field.value}
                    onChange={field.onChange}
                    label="Ubicación de Inicio (Casa/Base) - Opcional"
                    helperText="Requerido solo cuando el modo 'Pickup' esté habilitado"
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
              {editingPersonnel ? 'Actualizar' : 'Crear'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteDialogOpen}
        title="Eliminar Personal"
        message={`¿Estás seguro de que deseas eliminar a "${personnelToDelete?.name}"? Esta acción no se puede deshacer.`}
        onConfirm={() => personnelToDelete && deleteMutation.mutate(personnelToDelete.id)}
        onCancel={() => {
          setDeleteDialogOpen(false)
          setPersonnelToDelete(null)
        }}
        confirmText="Eliminar"
        cancelText="Cancelar"
      />
    </Box>
  )
}
