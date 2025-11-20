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
  OutlinedInput,
  FormHelperText,
} from '@mui/material'
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm, Controller } from 'react-hook-form'
import { DataTable, LoadingSpinner, ErrorMessage, ConfirmDialog } from '@/components/common'
import { careTypeService } from '@/services/careTypeService'
import { skillService } from '@/services/skillService'
import type { CareType, CareTypeCreate } from '@/types'
import type { Column } from '@/components/common/DataTable'

export default function CareTypesPage() {
  const [openDialog, setOpenDialog] = useState(false)
  const [editingCareType, setEditingCareType] = useState<CareType | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [careTypeToDelete, setCareTypeToDelete] = useState<CareType | null>(null)

  const queryClient = useQueryClient()

  // Fetch care types and skills
  const { data: careTypesResponse, isLoading, error } = useQuery({
    queryKey: ['careTypes'],
    queryFn: () => careTypeService.getAll(),
  })

  const { data: skills } = useQuery({
    queryKey: ['skills'],
    queryFn: () => skillService.getAll(),
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: CareTypeCreate) => careTypeService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['careTypes'] })
      setOpenDialog(false)
      reset()
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: CareTypeCreate }) =>
      careTypeService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['careTypes'] })
      setOpenDialog(false)
      setEditingCareType(null)
      reset()
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => careTypeService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['careTypes'] })
      setDeleteDialogOpen(false)
      setCareTypeToDelete(null)
    },
  })

  // Form
  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm<CareTypeCreate>({
    defaultValues: {
      name: '',
      description: '',
      estimated_duration: 60,
      required_skill_ids: [],
    },
  })

  const handleCreate = () => {
    setEditingCareType(null)
    reset({ name: '', description: '', estimated_duration: 60, required_skill_ids: [] })
    setOpenDialog(true)
  }

  const handleEdit = (careType: CareType) => {
    setEditingCareType(careType)
    reset({
      name: careType.name,
      description: careType.description || '',
      estimated_duration: careType.estimated_duration,
      required_skill_ids: careType.required_skill_ids,
    })
    setOpenDialog(true)
  }

  const handleDelete = (careType: CareType) => {
    setCareTypeToDelete(careType)
    setDeleteDialogOpen(true)
  }

  const onSubmit = (data: CareTypeCreate) => {
    if (editingCareType) {
      updateMutation.mutate({ id: editingCareType.id, data })
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

  const columns: Column<CareType>[] = [
    { id: 'id', label: 'ID', sortable: true, minWidth: 80 },
    { id: 'name', label: 'Nombre', sortable: true, minWidth: 200 },
    { id: 'description', label: 'Descripción', minWidth: 250 },
    {
      id: 'estimated_duration',
      label: 'Duración (min)',
      sortable: true,
      minWidth: 120,
      align: 'center',
    },
    {
      id: 'required_skill_ids',
      label: 'Habilidades Requeridas',
      minWidth: 250,
      render: (row) => getSkillNames(row.required_skill_ids),
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
        <Typography variant="h4">Tipos de Atención</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>
          Nuevo Tipo de Atención
        </Button>
      </Box>

      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <DataTable
          columns={columns}
          data={careTypesResponse?.items || []}
          loading={isLoading}
          emptyMessage="No hay tipos de atención registrados"
        />
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogTitle>
            {editingCareType ? 'Editar Tipo de Atención' : 'Nuevo Tipo de Atención'}
          </DialogTitle>
          <DialogContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
              <TextField
                label="Nombre"
                {...register('name', { required: 'El nombre es requerido' })}
                error={!!errors.name}
                helperText={errors.name?.message}
                fullWidth
                autoFocus
              />
              <TextField
                label="Descripción"
                {...register('description')}
                multiline
                rows={3}
                fullWidth
              />
              <TextField
                label="Duración Estimada (minutos)"
                type="number"
                {...register('estimated_duration', {
                  required: 'La duración es requerida',
                  min: { value: 1, message: 'Debe ser al menos 1 minuto' },
                })}
                error={!!errors.estimated_duration}
                helperText={errors.estimated_duration?.message}
                fullWidth
              />
              <Controller
                name="required_skill_ids"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth>
                    <InputLabel>Habilidades Requeridas</InputLabel>
                    <Select
                      {...field}
                      multiple
                      input={<OutlinedInput label="Habilidades Requeridas" />}
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
                    <FormHelperText>
                      Selecciona las habilidades necesarias para este tipo de atención
                    </FormHelperText>
                  </FormControl>
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
              {editingCareType ? 'Actualizar' : 'Crear'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteDialogOpen}
        title="Eliminar Tipo de Atención"
        message={`¿Estás seguro de que deseas eliminar el tipo de atención "${careTypeToDelete?.name}"? Esta acción no se puede deshacer.`}
        onConfirm={() => careTypeToDelete && deleteMutation.mutate(careTypeToDelete.id)}
        onCancel={() => {
          setDeleteDialogOpen(false)
          setCareTypeToDelete(null)
        }}
        confirmText="Eliminar"
        cancelText="Cancelar"
      />
    </Box>
  )
}
