import { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  Checkbox,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { caseService } from '@/services/caseService'
import { careTypeService } from '@/services/careTypeService'
import { skillService } from '@/services/skillService'
import DataTable, { Column } from '@/components/common/DataTable'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import ErrorMessage from '@/components/common/ErrorMessage'
import type { Case, CaseStatus, CasePriority } from '@/types'

interface CaseSelectorProps {
  selectedDate: string
  selectedCaseIds: number[]
  onSelectionChange: (caseIds: number[]) => void
}

export const CaseSelector = ({
  selectedDate,
  selectedCaseIds,
  onSelectionChange,
}: CaseSelectorProps) => {
  const [statusFilter, setStatusFilter] = useState<CaseStatus | ''>('')
  const [priorityFilter, setPriorityFilter] = useState<CasePriority | ''>('')

  // Fetch cases for the selected date
  const { data, isLoading, error } = useQuery({
    queryKey: ['cases', selectedDate, statusFilter, priorityFilter],
    queryFn: () =>
      caseService.getAll({
        scheduled_date: selectedDate,
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
        limit: 1000, // Get all cases for the date
      }),
    enabled: !!selectedDate,
  })

  // Fetch care types to get required skills
  const { data: careTypesData } = useQuery({
    queryKey: ['careTypes'],
    queryFn: () => careTypeService.getAll(),
  })

  // Fetch skills to display skill names
  const { data: skillsData } = useQuery({
    queryKey: ['skills'],
    queryFn: () => skillService.getAll(),
  })

  const cases = data?.items || []
  const careTypes = careTypesData?.items || []
  const skills = skillsData || []

  // Reset selection when date changes
  useEffect(() => {
    onSelectionChange([])
  }, [selectedDate])

  const handleSelectCase = (caseId: number, checked: boolean) => {
    if (checked) {
      onSelectionChange([...selectedCaseIds, caseId])
    } else {
      onSelectionChange(selectedCaseIds.filter((id) => id !== caseId))
    }
  }

  const getPriorityColor = (priority: CasePriority) => {
    switch (priority) {
      case 'urgent':
        return 'error'
      case 'high':
        return 'warning'
      case 'medium':
        return 'info'
      case 'low':
        return 'default'
      default:
        return 'default'
    }
  }

  const getStatusColor = (status: CaseStatus) => {
    switch (status) {
      case 'pending':
        return 'warning'
      case 'assigned':
        return 'info'
      case 'completed':
        return 'success'
      case 'cancelled':
        return 'error'
      default:
        return 'default'
    }
  }

  // Get required skills for a case
  const getRequiredSkills = (caseItem: Case) => {
    const careType = careTypes.find((ct) => ct.id === caseItem.care_type_id)
    if (!careType) return []

    return careType.required_skill_ids
      .map((skillId) => skills.find((s) => s.id === skillId))
      .filter((skill) => skill !== undefined)
  }

  // Get care type name
  const getCareTypeName = (careTypeId: number) => {
    return careTypes.find((ct) => ct.id === careTypeId)?.name || `ID: ${careTypeId}`
  }

  const columns: Column<Case>[] = [
    {
      id: 'select',
      label: 'Seleccionar',
      render: (row) => (
        <Checkbox
          checked={selectedCaseIds.includes(row.id)}
          onChange={(e) => handleSelectCase(row.id, e.target.checked)}
          disabled={row.status !== 'pending'}
        />
      ),
    },
    {
      id: 'id',
      label: 'ID',
      sortable: true,
    },
    {
      id: 'priority',
      label: 'Prioridad',
      render: (row) => (
        <Chip
          label={row.priority.toUpperCase()}
          color={getPriorityColor(row.priority)}
          size="small"
        />
      ),
      sortable: true,
    },
    {
      id: 'status',
      label: 'Estado',
      render: (row) => (
        <Chip
          label={row.status.replace('_', ' ').toUpperCase()}
          color={getStatusColor(row.status)}
          size="small"
        />
      ),
      sortable: true,
    },
    {
      id: 'patient_id',
      label: 'Paciente ID',
      sortable: true,
    },
    {
      id: 'care_type_id',
      label: 'Tipo Atención',
      sortable: true,
      render: (row) => getCareTypeName(row.care_type_id),
      minWidth: 150,
    },
    {
      id: 'required_skills',
      label: 'Habilidades Requeridas',
      minWidth: 250,
      render: (row) => {
        const requiredSkills = getRequiredSkills(row)
        if (requiredSkills.length === 0) {
          return <Typography variant="caption" color="text.secondary">Sin habilidades</Typography>
        }
        return (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {requiredSkills.map((skill) => (
              <Chip
                key={skill.id}
                label={skill.name}
                size="small"
                color="primary"
                variant="outlined"
              />
            ))}
          </Box>
        )
      },
    },
    {
      id: 'time_window',
      label: 'Ventana Horaria',
      minWidth: 150,
      render: (row) => {
        if (row.time_window_start && row.time_window_end) {
          return `${row.time_window_start} - ${row.time_window_end}`
        }
        return 'Sin restricción'
      },
    },
    {
      id: 'location',
      label: 'Ubicación',
      minWidth: 180,
      render: (row) =>
        `${row.location.latitude.toFixed(4)}, ${row.location.longitude.toFixed(4)}`,
    },
  ]

  if (!selectedDate) {
    return (
      <Paper sx={{ p: 3 }}>
        <Alert severity="info">
          Por favor seleccione una fecha para ver los casos disponibles.
        </Alert>
      </Paper>
    )
  }

  if (isLoading) {
    return (
      <Paper sx={{ p: 3 }}>
        <LoadingSpinner />
      </Paper>
    )
  }

  if (error) {
    return (
      <Paper sx={{ p: 3 }}>
        <ErrorMessage message="Error al cargar los casos" />
      </Paper>
    )
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Selección de Casos
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Seleccione los casos pendientes para incluir en la optimización de
          rutas.
        </Typography>

        {/* Filters */}
        <Box sx={{ display: 'flex', gap: 2, mt: 2, mb: 2 }}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Estado</InputLabel>
            <Select
              value={statusFilter}
              label="Estado"
              onChange={(e) => setStatusFilter(e.target.value as CaseStatus | '')}
            >
              <MenuItem value="">Todos</MenuItem>
              <MenuItem value="pending">Pendiente</MenuItem>
              <MenuItem value="assigned">Asignado</MenuItem>
              <MenuItem value="completed">Completado</MenuItem>
              <MenuItem value="cancelled">Cancelado</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Prioridad</InputLabel>
            <Select
              value={priorityFilter}
              label="Prioridad"
              onChange={(e) =>
                setPriorityFilter(e.target.value as CasePriority | '')
              }
            >
              <MenuItem value="">Todas</MenuItem>
              <MenuItem value="urgent">Urgente</MenuItem>
              <MenuItem value="high">Alta</MenuItem>
              <MenuItem value="medium">Media</MenuItem>
              <MenuItem value="low">Baja</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {/* Selection summary */}
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Chip
            label={`${cases.length} casos totales`}
            color="default"
            size="small"
          />
          <Chip
            label={`${cases.filter((c) => c.status === 'pending').length} pendientes`}
            color="warning"
            size="small"
          />
          <Chip
            label={`${selectedCaseIds.length} seleccionados`}
            color="primary"
            size="small"
          />
        </Box>
      </Box>

      {/* Cases table */}
      <DataTable
        columns={columns}
        data={cases}
        pagination={true}
        emptyMessage="No hay casos para la fecha seleccionada"
      />
    </Paper>
  )
}
