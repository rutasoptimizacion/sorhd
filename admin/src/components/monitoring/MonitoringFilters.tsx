/**
 * MonitoringFilters Component
 * Provides filters for monitoring data (date, status, vehicles, auto-refresh)
 */

import {
  Box,
  Card,
  CardContent,
  TextField,
  MenuItem,
  FormControl,
  FormControlLabel,
  Switch,
  Typography,
  Button,
  Chip,
  Stack
} from '@mui/material'
import FilterListIcon from '@mui/icons-material/FilterList'
import ClearIcon from '@mui/icons-material/Clear'
import { useSelector, useDispatch } from 'react-redux'
import { RootState } from '@/store'
import {
  setDateFilter,
  setStatusFilter,
  setVehicleFilter,
  setAutoRefresh,
  resetFilters,
  selectFilters
} from '@/store/monitoringSlice'

interface MonitoringFiltersProps {
  availableVehicles?: { id: number; identifier: string }[]
}

export const MonitoringFilters: React.FC<MonitoringFiltersProps> = ({
  availableVehicles = []
}) => {
  const dispatch = useDispatch()
  const filters = useSelector((state: RootState) => selectFilters(state))
  const autoRefresh = useSelector((state: RootState) => state.monitoring.autoRefresh)

  const statusOptions = [
    { value: 'all', label: 'Todos' },
    { value: 'en_route', label: 'En ruta' },
    { value: 'at_visit', label: 'En visita' },
    { value: 'delayed', label: 'Retrasadas' }
  ]

  const handleDateChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    dispatch(setDateFilter(event.target.value))
  }

  const handleStatusChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    dispatch(setStatusFilter(event.target.value as any))
  }

  const handleVehicleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value
    // Parse comma-separated vehicle IDs
    const ids = value ? value.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id)) : []
    dispatch(setVehicleFilter(ids))
  }

  const handleAutoRefreshToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
    dispatch(setAutoRefresh(event.target.checked))
  }

  const handleResetFilters = () => {
    dispatch(resetFilters())
  }

  const hasActiveFilters = filters.status !== 'all' || filters.vehicleIds.length > 0

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FilterListIcon color="action" />
            <Typography variant="subtitle1" fontWeight="bold">
              Filtros
            </Typography>
          </Box>
          {hasActiveFilters && (
            <Button
              size="small"
              startIcon={<ClearIcon />}
              onClick={handleResetFilters}
            >
              Limpiar
            </Button>
          )}
        </Box>

        <Stack spacing={2}>
          {/* Date Filter */}
          <TextField
            label="Fecha"
            type="date"
            value={filters.date}
            onChange={handleDateChange}
            fullWidth
            size="small"
            InputLabelProps={{
              shrink: true,
            }}
          />

          {/* Status Filter */}
          <TextField
            label="Estado"
            select
            value={filters.status}
            onChange={handleStatusChange}
            fullWidth
            size="small"
          >
            {statusOptions.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </TextField>

          {/* Vehicle Filter */}
          {availableVehicles.length > 0 && (
            <TextField
              label="Vehículos"
              select
              value={filters.vehicleIds.join(',')}
              onChange={handleVehicleChange}
              fullWidth
              size="small"
              SelectProps={{
                multiple: true,
                renderValue: (selected) => {
                  const ids = typeof selected === 'string' ? selected.split(',').filter(Boolean) : []
                  if (ids.length === 0) return 'Todos los vehículos'
                  return (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {ids.map((id) => {
                        const vehicle = availableVehicles.find(v => v.id === parseInt(id))
                        return (
                          <Chip
                            key={id}
                            label={vehicle?.identifier || `#${id}`}
                            size="small"
                          />
                        )
                      })}
                    </Box>
                  )
                }
              }}
            >
              {availableVehicles.map((vehicle) => (
                <MenuItem key={vehicle.id} value={vehicle.id}>
                  {vehicle.identifier}
                </MenuItem>
              ))}
            </TextField>
          )}

          {/* Auto-refresh Toggle */}
          <FormControl>
            <FormControlLabel
              control={
                <Switch
                  checked={autoRefresh}
                  onChange={handleAutoRefreshToggle}
                  color="primary"
                />
              }
              label={
                <Box>
                  <Typography variant="body2">
                    Actualización automática
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {autoRefresh ? 'Datos se actualizan en tiempo real' : 'Actualización manual'}
                  </Typography>
                </Box>
              }
            />
          </FormControl>

          {/* Active filters summary */}
          {hasActiveFilters && (
            <Box sx={{ pt: 1 }}>
              <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                Filtros activos:
              </Typography>
              <Stack direction="row" spacing={0.5} flexWrap="wrap">
                {filters.status !== 'all' && (
                  <Chip
                    label={statusOptions.find(o => o.value === filters.status)?.label}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                )}
                {filters.vehicleIds.length > 0 && (
                  <Chip
                    label={`${filters.vehicleIds.length} vehículo(s)`}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                )}
              </Stack>
            </Box>
          )}
        </Stack>
      </CardContent>
    </Card>
  )
}

export default MonitoringFilters
