import {
  Box,
  Paper,
  Typography,
  Checkbox,
  Card,
  CardContent,
  Chip,
  Alert,
  Stack,
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { vehicleService } from '@/services/vehicleService'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import ErrorMessage from '@/components/common/ErrorMessage'
import LocalShippingIcon from '@mui/icons-material/LocalShipping'
import InfoIcon from '@mui/icons-material/Info'

interface VehicleSelectorProps {
  selectedVehicleIds: number[]
  onSelectionChange: (vehicleIds: number[]) => void
}

export const VehicleSelector = ({
  selectedVehicleIds,
  onSelectionChange,
}: VehicleSelectorProps) => {
  // Fetch available vehicles
  const {
    data: vehiclesData,
    isLoading: vehiclesLoading,
    error: vehiclesError,
  } = useQuery({
    queryKey: ['vehicles', 'active'],
    queryFn: () =>
      vehicleService.getAll({
        limit: 100,
      }),
  })

  const vehicles = vehiclesData?.items?.filter((v) => v.is_active && v.status === 'available') || []

  const handleVehicleToggle = (vehicleId: number, checked: boolean) => {
    if (checked) {
      // Add vehicle to selection
      onSelectionChange([...selectedVehicleIds, vehicleId])
    } else {
      // Remove vehicle from selection
      onSelectionChange(selectedVehicleIds.filter((id) => id !== vehicleId))
    }
  }

  const isVehicleSelected = (vehicleId: number) => {
    return selectedVehicleIds.includes(vehicleId)
  }

  if (vehiclesLoading) {
    return (
      <Paper sx={{ p: 3 }}>
        <LoadingSpinner />
      </Paper>
    )
  }

  if (vehiclesError) {
    return (
      <Paper sx={{ p: 3 }}>
        <ErrorMessage message="Error al cargar vehículos" />
      </Paper>
    )
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Selección de Vehículos
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Seleccione los vehículos que desea utilizar para las rutas del día.
        </Typography>

        <Alert severity="info" icon={<InfoIcon />} sx={{ mt: 2 }}>
          <strong>Asignación automática de personal:</strong> El sistema asignará
          automáticamente el personal médico más adecuado a cada vehículo según las
          habilidades requeridas por los casos asignados.
        </Alert>

        <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
          <Chip
            label={`${vehicles.length} vehículos disponibles`}
            color="default"
            size="small"
          />
          <Chip
            label={`${selectedVehicleIds.length} seleccionados`}
            color="primary"
            size="small"
          />
        </Box>
      </Box>

      {vehicles.length === 0 && (
        <Alert severity="warning">
          No hay vehículos disponibles. Por favor, asegúrese de que existen
          vehículos activos y disponibles.
        </Alert>
      )}

      <Stack spacing={2}>
        {vehicles.map((vehicle) => {
          const selected = isVehicleSelected(vehicle.id)

          return (
            <Card
              key={vehicle.id}
              variant="outlined"
              sx={{
                borderColor: selected ? 'primary.main' : 'divider',
                borderWidth: selected ? 2 : 1,
                transition: 'all 0.2s',
                '&:hover': {
                  boxShadow: 2,
                },
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <Checkbox
                    checked={selected}
                    onChange={(e) =>
                      handleVehicleToggle(vehicle.id, e.target.checked)
                    }
                  />
                  <Box sx={{ flexGrow: 1 }}>
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1,
                        mb: 1,
                      }}
                    >
                      <LocalShippingIcon color="action" />
                      <Typography variant="h6">{vehicle.identifier}</Typography>
                      <Chip
                        label={`Capacidad: ${vehicle.capacity} personas`}
                        size="small"
                        color="default"
                      />
                    </Box>

                    <Typography variant="body2" color="text.secondary">
                      <strong>Ubicación base:</strong> {vehicle.base_location.latitude.toFixed(4)},{' '}
                      {vehicle.base_location.longitude.toFixed(4)}
                    </Typography>

                    {vehicle.resources && vehicle.resources.length > 0 && (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          <strong>Recursos:</strong> {vehicle.resources.join(', ')}
                        </Typography>
                      </Box>
                    )}

                    {selected && (
                      <Box sx={{ mt: 2 }}>
                        <Chip
                          label="Vehículo seleccionado - Personal asignado automáticamente"
                          color="success"
                          size="small"
                          variant="outlined"
                        />
                      </Box>
                    )}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          )
        })}
      </Stack>
    </Paper>
  )
}
