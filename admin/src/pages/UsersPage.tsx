import { useState } from 'react'
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
  InputAdornment,
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility,
  VisibilityOff,
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm, Controller } from 'react-hook-form'
import { DataTable, LoadingSpinner, ErrorMessage, ConfirmDialog } from '@/components/common'
import { userService } from '@/services/userService'
import { User, UserCreate, UserRole } from '@/types'
import type { Column } from '@/components/common/DataTable'

export default function UsersPage() {
  const [openDialog, setOpenDialog] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [userToDelete, setUserToDelete] = useState<User | null>(null)
  const [showPassword, setShowPassword] = useState(false)

  const queryClient = useQueryClient()

  // Fetch users
  const { data: usersResponse, isLoading, error } = useQuery({
    queryKey: ['users'],
    queryFn: () => userService.getAll(),
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: UserCreate) => userService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setOpenDialog(false)
      reset()
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<UserCreate> }) =>
      userService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setOpenDialog(false)
      setEditingUser(null)
      reset()
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => userService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setDeleteDialogOpen(false)
      setUserToDelete(null)
    },
  })

  // Form
  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm<UserCreate>({
    defaultValues: {
      username: '',
      password: '',
      full_name: '',
      role: UserRole.CLINICAL_TEAM,
      is_active: true,
    },
  })

  const handleCreate = () => {
    setEditingUser(null)
    reset({
      username: '',
      password: '',
      full_name: '',
      role: UserRole.CLINICAL_TEAM,
      is_active: true,
    })
    setOpenDialog(true)
  }

  const handleEdit = (user: User) => {
    setEditingUser(user)
    reset({
      username: user.username,
      password: '', // Don't populate password on edit
      full_name: user.full_name,
      role: user.role,
      is_active: user.is_active,
    })
    setOpenDialog(true)
  }

  const handleDelete = (user: User) => {
    setUserToDelete(user)
    setDeleteDialogOpen(true)
  }

  const onSubmit = (data: UserCreate) => {
    if (editingUser) {
      // Don't send password if empty (user doesn't want to change it)
      const updateData: Partial<UserCreate> = { ...data }
      if (!data.password) {
        delete updateData.password
      }
      updateMutation.mutate({ id: editingUser.id, data: updateData })
    } else {
      createMutation.mutate(data)
    }
  }

  const getRoleLabel = (role: UserRole) => {
    switch (role) {
      case UserRole.ADMIN:
        return 'Administrador'
      case UserRole.CLINICAL_TEAM:
        return 'Equipo Clínico'
      case UserRole.PATIENT:
        return 'Paciente'
      default:
        return role
    }
  }

  const getRoleColor = (role: UserRole): 'primary' | 'success' | 'warning' => {
    switch (role) {
      case UserRole.ADMIN:
        return 'primary'
      case UserRole.CLINICAL_TEAM:
        return 'success'
      case UserRole.PATIENT:
        return 'warning'
      default:
        return 'primary'
    }
  }

  const columns: Column<User>[] = [
    { id: 'id', label: 'ID', sortable: true, minWidth: 80 },
    { id: 'username', label: 'Usuario', sortable: true, minWidth: 150 },
    { id: 'full_name', label: 'Nombre Completo', sortable: true, minWidth: 200 },
    {
      id: 'role',
      label: 'Rol',
      minWidth: 150,
      render: (row) => (
        <Chip label={getRoleLabel(row.role)} color={getRoleColor(row.role)} size="small" />
      ),
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
      id: 'created_at',
      label: 'Fecha de Creación',
      minWidth: 180,
      render: (row) => new Date(row.created_at).toLocaleString('es-CL'),
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
        <Typography variant="h4">Gestión de Usuarios</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>
          Nuevo Usuario
        </Button>
      </Box>

      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <DataTable
          columns={columns}
          data={usersResponse?.items || []}
          loading={isLoading}
          emptyMessage="No hay usuarios registrados"
        />
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogTitle>{editingUser ? 'Editar Usuario' : 'Nuevo Usuario'}</DialogTitle>
          <DialogContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
              <TextField
                label="Usuario"
                {...register('username', { required: 'El usuario es requerido' })}
                error={!!errors.username}
                helperText={errors.username?.message}
                fullWidth
                autoFocus
              />

              <TextField
                label="Nombre Completo"
                {...register('full_name', { required: 'El nombre completo es requerido' })}
                error={!!errors.full_name}
                helperText={errors.full_name?.message}
                fullWidth
              />

              <TextField
                label={editingUser ? 'Nueva Contraseña (dejar vacío para no cambiar)' : 'Contraseña'}
                type={showPassword ? 'text' : 'password'}
                {...register('password', {
                  required: editingUser ? false : 'La contraseña es requerida',
                  minLength: {
                    value: 6,
                    message: 'La contraseña debe tener al menos 6 caracteres',
                  },
                })}
                error={!!errors.password}
                helperText={errors.password?.message}
                fullWidth
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />

              <Controller
                name="role"
                control={control}
                rules={{ required: 'El rol es requerido' }}
                render={({ field }) => (
                  <FormControl fullWidth error={!!errors.role}>
                    <InputLabel>Rol</InputLabel>
                    <Select {...field} label="Rol">
                      <MenuItem value={UserRole.ADMIN}>Administrador</MenuItem>
                      <MenuItem value={UserRole.CLINICAL_TEAM}>Equipo Clínico</MenuItem>
                      <MenuItem value={UserRole.PATIENT}>Paciente</MenuItem>
                    </Select>
                    {errors.role && (
                      <Typography variant="caption" color="error" sx={{ mt: 0.5, ml: 1.75 }}>
                        {errors.role.message}
                      </Typography>
                    )}
                  </FormControl>
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
              {editingUser ? 'Actualizar' : 'Crear'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteDialogOpen}
        title="Eliminar Usuario"
        message={`¿Estás seguro de que deseas eliminar al usuario "${userToDelete?.username}"? Esta acción no se puede deshacer.`}
        onConfirm={() => userToDelete && deleteMutation.mutate(userToDelete.id)}
        onCancel={() => {
          setDeleteDialogOpen(false)
          setUserToDelete(null)
        }}
        confirmText="Eliminar"
        cancelText="Cancelar"
      />
    </Box>
  )
}
