import { useState } from 'react'
import {
  Container,
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Stepper,
  Step,
  StepLabel,
  Alert,
  CircularProgress,
} from '@mui/material'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { routeService } from '@/services/routeService'
import { CaseSelector } from '@/components/planning/CaseSelector'
import { VehicleSelector } from '@/components/planning/VehicleSelector'
import { OptimizationResults } from '@/components/planning/OptimizationResults'
import { RouteMap } from '@/components/planning/RouteMap'
import type {
  OptimizationRequest,
  OptimizationResponse,
  RouteWithDetails,
  RouteStatus,
} from '@/types'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import { format } from 'date-fns'

const steps = [
  'Seleccionar Fecha',
  'Seleccionar Casos',
  'Seleccionar Vehículos',
  'Optimizar Rutas',
]

export default function RoutePlanningPage() {
  const queryClient = useQueryClient()

  // Step management
  const [activeStep, setActiveStep] = useState(0)

  // Form state
  const [selectedDate, setSelectedDate] = useState(format(new Date(), 'yyyy-MM-dd'))
  const [selectedCaseIds, setSelectedCaseIds] = useState<number[]>([])
  const [selectedVehicleIds, setSelectedVehicleIds] = useState<number[]>([])

  // Optimization results
  const [optimizationResult, setOptimizationResult] =
    useState<OptimizationResponse | null>(null)
  const [optimizedRoutes, setOptimizedRoutes] = useState<RouteWithDetails[]>([])

  // Optimization mutation
  const optimizeMutation = useMutation({
    mutationFn: (request: OptimizationRequest) => routeService.optimize(request),
    onSuccess: async (response) => {
      setOptimizationResult(response)

      // Fetch detailed route information
      const routeDetailsPromises = response.route_ids.map((routeId) =>
        routeService.getByIdWithDetails(routeId)
      )
      const routes = await Promise.all(routeDetailsPromises)
      setOptimizedRoutes(routes)

      // Move to results step
      setActiveStep(3)
    },
    onError: (error: any) => {
      console.error('Optimization error:', error)
    },
  })

  // Approve routes mutation
  const approveRoutesMutation = useMutation({
    mutationFn: async (routeIds: number[]) => {
      // Update each route status to 'active'
      return Promise.all(
        routeIds.map((routeId) =>
          routeService.updateStatus(routeId, { status: 'active' as RouteStatus })
        )
      )
    },
    onSuccess: () => {
      // Invalidate routes cache
      queryClient.invalidateQueries({ queryKey: ['routes'] })

      // Reset form
      handleReset()

      alert('Rutas aprobadas y activadas exitosamente!')
    },
    onError: (error: any) => {
      console.error('Approve routes error:', error)
      alert('Error al aprobar las rutas. Por favor intente nuevamente.')
    },
  })

  const handleNext = () => {
    // Validate each step before proceeding
    if (activeStep === 0 && !selectedDate) {
      alert('Por favor seleccione una fecha')
      return
    }

    if (activeStep === 1 && selectedCaseIds.length === 0) {
      alert('Por favor seleccione al menos un caso')
      return
    }

    if (activeStep === 2) {
      // Validate vehicle selection
      if (selectedVehicleIds.length === 0) {
        alert('Por favor seleccione al menos un vehículo')
        return
      }

      // Trigger optimization
      handleOptimize()
      return
    }

    setActiveStep((prev) => prev + 1)
  }

  const handleBack = () => {
    setActiveStep((prev) => prev - 1)
  }

  const handleOptimize = () => {
    const request: OptimizationRequest = {
      case_ids: selectedCaseIds,
      vehicle_ids: selectedVehicleIds,
      date: selectedDate,
    }

    optimizeMutation.mutate(request)
  }

  const handleReoptimize = () => {
    setOptimizationResult(null)
    setOptimizedRoutes([])
    setActiveStep(2)
  }

  const handleApproveRoutes = () => {
    if (!optimizationResult) return

    if (
      window.confirm(
        `¿Está seguro de que desea aprobar y activar ${optimizationResult.route_ids.length} rutas?`
      )
    ) {
      approveRoutesMutation.mutate(optimizationResult.route_ids)
    }
  }

  const handleReset = () => {
    setActiveStep(0)
    setSelectedDate(format(new Date(), 'yyyy-MM-dd'))
    setSelectedCaseIds([])
    setSelectedVehicleIds([])
    setOptimizationResult(null)
    setOptimizedRoutes([])
  }

  const canProceed = () => {
    switch (activeStep) {
      case 0:
        return !!selectedDate
      case 1:
        return selectedCaseIds.length > 0
      case 2:
        return selectedVehicleIds.length > 0
      default:
        return false
    }
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4, height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <Box sx={{ mb: 4, flexShrink: 0 }}>
        <Typography variant="h4" gutterBottom>
          Planificación de Rutas
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Optimice las rutas diarias para los equipos de hospitalización
          domiciliaria
        </Typography>
      </Box>

      {/* Stepper */}
      <Paper sx={{ p: 3, mb: 3, flexShrink: 0 }}>
        <Stepper activeStep={activeStep}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
          <Button disabled={activeStep === 0} onClick={handleBack}>
            Atrás
          </Button>
          <Box sx={{ display: 'flex', gap: 2 }}>
            {activeStep < 3 && (
              <Button
                variant="contained"
                onClick={handleNext}
                disabled={!canProceed() || optimizeMutation.isPending}
              >
                {activeStep === 2 ? (
                  optimizeMutation.isPending ? (
                    <>
                      <CircularProgress size={20} sx={{ mr: 1 }} />
                      Optimizando...
                    </>
                  ) : (
                    <>
                      <PlayArrowIcon sx={{ mr: 1 }} />
                      Optimizar Rutas
                    </>
                  )
                ) : (
                  'Siguiente'
                )}
              </Button>
            )}
            <Button variant="outlined" onClick={handleReset}>
              Reiniciar
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* Step Content */}
      <Box sx={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
        {/* Step 0: Date Selection */}
        {activeStep === 0 && (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Seleccione la Fecha de Planificación
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Elija la fecha para la cual desea optimizar las rutas de visitas
              domiciliarias.
            </Typography>
            <TextField
              label="Fecha"
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              fullWidth
              sx={{ mt: 2, maxWidth: 300 }}
              InputLabelProps={{ shrink: true }}
            />
          </Paper>
        )}

        {/* Step 1: Case Selection */}
        {activeStep === 1 && (
          <CaseSelector
            selectedDate={selectedDate}
            selectedCaseIds={selectedCaseIds}
            onSelectionChange={setSelectedCaseIds}
          />
        )}

        {/* Step 2: Vehicle Selection */}
        {activeStep === 2 && (
          <VehicleSelector
            selectedVehicleIds={selectedVehicleIds}
            onSelectionChange={setSelectedVehicleIds}
          />
        )}

        {/* Step 3: Optimization Results */}
        {activeStep === 3 && optimizationResult && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <OptimizationResults
              result={optimizationResult}
              routes={optimizedRoutes}
              onApproveRoutes={handleApproveRoutes}
              onReoptimize={handleReoptimize}
              isApproving={approveRoutesMutation.isPending}
            />
            <RouteMap routes={optimizedRoutes} height={600} />
          </Box>
        )}

        {/* Optimization Error */}
        {optimizeMutation.isError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            <strong>Error en la optimización:</strong>{' '}
            {optimizeMutation.error?.message || 'Error desconocido'}
          </Alert>
        )}
      </Box>
    </Container>
  )
}
