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
  Paper,
  Grid,
} from '@mui/material'
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon, FilterList as FilterListIcon } from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { DataTable, LoadingSpinner, ErrorMessage, ConfirmDialog } from '@/components/common'
import { skillService } from '@/services/skillService'
import type { Skill, SkillCreate } from '@/types'
import type { Column } from '@/components/common/DataTable'

export default function SkillsPage() {
  const [openDialog, setOpenDialog] = useState(false)
  const [editingSkill, setEditingSkill] = useState<Skill | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [skillToDelete, setSkillToDelete] = useState<Skill | null>(null)

  // Filtros
  const [filterName, setFilterName] = useState('')
  const [filterDescription, setFilterDescription] = useState('')

  const queryClient = useQueryClient()

  // Fetch skills
  const { data: skills, isLoading, error } = useQuery({
    queryKey: ['skills'],
    queryFn: () => skillService.getAll(),
  })

  // Filtrado de habilidades
  const filteredSkills = useMemo(() => {
    if (!skills) return []

    return skills.filter((skill) => {
      // Filtro por nombre
      if (filterName && !skill.name.toLowerCase().includes(filterName.toLowerCase())) {
        return false
      }

      // Filtro por descripción
      if (filterDescription && skill.description && !skill.description.toLowerCase().includes(filterDescription.toLowerCase())) {
        return false
      }

      return true
    })
  }, [skills, filterName, filterDescription])

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: SkillCreate) => skillService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] })
      setOpenDialog(false)
      reset()
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: SkillCreate }) => skillService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] })
      setOpenDialog(false)
      setEditingSkill(null)
      reset()
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => skillService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] })
      setDeleteDialogOpen(false)
      setSkillToDelete(null)
    },
  })

  // Form
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<SkillCreate>({
    defaultValues: {
      name: '',
      description: '',
    },
  })

  const handleCreate = () => {
    setEditingSkill(null)
    reset({ name: '', description: '' })
    setOpenDialog(true)
  }

  const handleEdit = (skill: Skill) => {
    setEditingSkill(skill)
    reset({ name: skill.name, description: skill.description || '' })
    setOpenDialog(true)
  }

  const handleDelete = (skill: Skill) => {
    setSkillToDelete(skill)
    setDeleteDialogOpen(true)
  }

  const onSubmit = (data: SkillCreate) => {
    if (editingSkill) {
      updateMutation.mutate({ id: editingSkill.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  const columns: Column<Skill>[] = [
    { id: 'id', label: 'ID', sortable: true, minWidth: 80 },
    { id: 'name', label: 'Nombre', sortable: true, minWidth: 200 },
    { id: 'description', label: 'Descripción', minWidth: 300 },
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
        <Typography variant="h4">Habilidades</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>
          Nueva Habilidad
        </Button>
      </Box>

      {/* Filtros */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <FilterListIcon sx={{ mr: 1, color: 'text.secondary' }} />
          <Typography variant="h6">Filtros</Typography>
        </Box>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <TextField
              label="Nombre"
              value={filterName}
              onChange={(e) => setFilterName(e.target.value)}
              size="small"
              fullWidth
              placeholder="Buscar por nombre..."
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              label="Descripción"
              value={filterDescription}
              onChange={(e) => setFilterDescription(e.target.value)}
              size="small"
              fullWidth
              placeholder="Buscar en descripción..."
            />
          </Grid>
        </Grid>
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Mostrando {filteredSkills.length} de {skills?.length || 0} habilidades
          </Typography>
          {(filterName || filterDescription) && (
            <Button
              size="small"
              onClick={() => {
                setFilterName('')
                setFilterDescription('')
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
          data={filteredSkills}
          loading={isLoading}
          emptyMessage={
            filterName || filterDescription
              ? 'No se encontraron habilidades con los filtros aplicados'
              : 'No hay habilidades registradas'
          }
        />
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogTitle>{editingSkill ? 'Editar Habilidad' : 'Nueva Habilidad'}</DialogTitle>
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
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenDialog(false)}>Cancelar</Button>
            <Button type="submit" variant="contained" disabled={createMutation.isPending || updateMutation.isPending}>
              {editingSkill ? 'Actualizar' : 'Crear'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteDialogOpen}
        title="Eliminar Habilidad"
        message={`¿Estás seguro de que deseas eliminar la habilidad "${skillToDelete?.name}"? Esta acción no se puede deshacer.`}
        onConfirm={() => skillToDelete && deleteMutation.mutate(skillToDelete.id)}
        onCancel={() => {
          setDeleteDialogOpen(false)
          setSkillToDelete(null)
        }}
        confirmText="Eliminar"
        cancelText="Cancelar"
      />
    </Box>
  )
}
