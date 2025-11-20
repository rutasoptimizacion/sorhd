import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
  Stack,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import WarningIcon from '@mui/icons-material/Warning'
import ErrorIcon from '@mui/icons-material/Error'
import DirectionsCarIcon from '@mui/icons-material/DirectionsCar'
import AccessTimeIcon from '@mui/icons-material/AccessTime'
import RouteIcon from '@mui/icons-material/Route'
import type {
  OptimizationResponse,
  RouteWithDetails,
} from '@/types'

interface OptimizationResultsProps {
  result: OptimizationResponse
  routes: RouteWithDetails[]
  onApproveRoutes: () => void
  onReoptimize: () => void
  isApproving?: boolean
}

export const OptimizationResults = ({
  result,
  routes,
  onApproveRoutes,
  onReoptimize,
  isApproving = false,
}: OptimizationResultsProps) => {
  const hasWarnings = result.constraint_violations.some(
    (v) => v.severity === 'warning'
  )
  const hasErrors = result.constraint_violations.some((v) => v.severity === 'error')
  const hasUnassigned = result.unassigned_case_ids.length > 0

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error':
        return 'error'
      case 'warning':
        return 'warning'
      default:
        return 'default'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error':
        return <ErrorIcon />
      case 'warning':
        return <WarningIcon />
      default:
        return <CheckCircleIcon />
    }
  }

  return (
    <Paper sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Resultados de Optimización
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Estrategia utilizada: <strong>{result.strategy_used}</strong> | Tiempo
          de optimización: <strong>{result.optimization_time_seconds.toFixed(2)}s</strong>
        </Typography>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <DirectionsCarIcon color="primary" />
                <Typography variant="h4">{result.route_ids.length}</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Rutas Generadas
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <RouteIcon color="success" />
                <Typography variant="h4">
                  {result.total_distance_km.toFixed(1)}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Distancia Total (km)
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <AccessTimeIcon color="info" />
                <Typography variant="h4">
                  {Math.round(result.total_time_minutes)}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Tiempo Total (min)
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <CheckCircleIcon
                  color={hasUnassigned ? 'warning' : 'success'}
                />
                <Typography variant="h4">
                  {result.unassigned_case_ids.length}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Casos Sin Asignar
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alerts */}
      {result.success && !hasErrors && !hasWarnings && !hasUnassigned && (
        <Alert severity="success" sx={{ mb: 2 }} icon={<CheckCircleIcon />}>
          <strong>Optimización exitosa:</strong> {result.message}
        </Alert>
      )}

      {hasUnassigned && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <strong>Casos sin asignar:</strong> {result.unassigned_case_ids.length}{' '}
          casos no pudieron ser asignados a ninguna ruta. IDs:{' '}
          {result.unassigned_case_ids.join(', ')}
        </Alert>
      )}

      {hasErrors && (
        <Alert severity="error" sx={{ mb: 2 }}>
          <strong>Errores encontrados:</strong> Hay problemas críticos que deben
          resolverse antes de aprobar las rutas.
        </Alert>
      )}

      {/* Skill Gap Analysis */}
      {result.skill_gap_analysis && (
        <Accordion sx={{ mb: 2 }} defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <WarningIcon color="info" />
              <Typography>
                Análisis de Competencias (Skill Gaps)
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Stack spacing={3}>
              {/* Summary */}
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Resumen de Asignación
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={3}>
                    <Card variant="outlined">
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" color="text.secondary">
                          {result.skill_gap_analysis.summary.total_cases_requested}
                        </Typography>
                        <Typography variant="caption">Casos Solicitados</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={3}>
                    <Card variant="outlined">
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" color="success.main">
                          {result.skill_gap_analysis.summary.total_cases_assigned}
                        </Typography>
                        <Typography variant="caption">Casos Asignados</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={3}>
                    <Card variant="outlined">
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" color="warning.main">
                          {result.skill_gap_analysis.summary.total_cases_unassigned}
                        </Typography>
                        <Typography variant="caption">Casos Sin Asignar</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={3}>
                    <Card variant="outlined">
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" color="info.main">
                          {result.skill_gap_analysis.summary.assignment_rate_percentage.toFixed(1)}%
                        </Typography>
                        <Typography variant="caption">Tasa de Asignación</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </Box>

              {/* Most Demanded Skills */}
              {result.skill_gap_analysis.most_demanded_skills.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Skills Más Demandadas (Prioridad de Contratación)
                  </Typography>
                  <Alert severity="info" sx={{ mb: 1 }}>
                    Estas son las competencias que más faltan y que al contratar personal con estas skills, más casos podrían asignarse.
                  </Alert>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell><strong>Skill</strong></TableCell>
                          <TableCell align="right"><strong>Casos Bloqueados</strong></TableCell>
                          <TableCell align="right"><strong>Casos Recuperables</strong></TableCell>
                          <TableCell align="right"><strong>Cobertura Actual</strong></TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {result.skill_gap_analysis.most_demanded_skills.map((skill) => (
                          <TableRow key={skill.skill}>
                            <TableCell>
                              <Chip label={skill.skill} color="primary" size="small" />
                            </TableCell>
                            <TableCell align="right">
                              <Typography color="error" variant="body2">
                                {skill.demand_count}
                              </Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Typography color="success" variant="body2">
                                +{result.skill_gap_analysis?.hiring_impact_simulation[skill.skill] || 0}
                              </Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Typography variant="body2">
                                {(result.skill_gap_analysis?.skill_coverage_percentage[skill.skill] || 0).toFixed(0)}%
                              </Typography>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              )}

              {/* Unassigned Cases Details */}
              {result.skill_gap_analysis.unassigned_case_details.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Detalle de Casos No Asignados
                  </Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell><strong>Caso ID</strong></TableCell>
                          <TableCell><strong>Nombre</strong></TableCell>
                          <TableCell><strong>Prioridad</strong></TableCell>
                          <TableCell><strong>Skills Requeridas</strong></TableCell>
                          <TableCell><strong>Skills Faltantes</strong></TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {result.skill_gap_analysis.unassigned_case_details.map((caseDetail) => (
                          <TableRow key={caseDetail.case_id}>
                            <TableCell>{caseDetail.case_id}</TableCell>
                            <TableCell>{caseDetail.case_name}</TableCell>
                            <TableCell>
                              <Chip
                                label={caseDetail.priority}
                                size="small"
                                color={caseDetail.priority >= 3 ? 'error' : 'default'}
                              />
                            </TableCell>
                            <TableCell>
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                {caseDetail.required_skills.map((skill) => (
                                  <Chip key={skill} label={skill} size="small" variant="outlined" />
                                ))}
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                {caseDetail.missing_skills.map((skill) => (
                                  <Chip key={skill} label={skill} size="small" color="error" />
                                ))}
                              </Box>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              )}
            </Stack>
          </AccordionDetails>
        </Accordion>
      )}

      {/* Constraint Violations */}
      {result.constraint_violations.length > 0 && (
        <Accordion sx={{ mb: 2 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <WarningIcon color={hasErrors ? 'error' : 'warning'} />
              <Typography>
                Violaciones de Restricciones ({result.constraint_violations.length})
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Severidad</TableCell>
                    <TableCell>Tipo</TableCell>
                    <TableCell>Entidad</TableCell>
                    <TableCell>Descripción</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {result.constraint_violations.map((violation, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <Chip
                          icon={getSeverityIcon(violation.severity)}
                          label={violation.severity.toUpperCase()}
                          color={getSeverityColor(violation.severity)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={violation.type.replace('_', ' ').toUpperCase()}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        {violation.entity_type && violation.entity_id
                          ? `${violation.entity_type} #${violation.entity_id}`
                          : '-'}
                      </TableCell>
                      <TableCell>{violation.description}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </AccordionDetails>
        </Accordion>
      )}

      {/* Routes Table */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Rutas Detalladas
        </Typography>
        <Stack spacing={2}>
          {routes.map((route, index) => (
            <Accordion key={route.id}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 2,
                    width: '100%',
                  }}
                >
                  <DirectionsCarIcon color="primary" />
                  <Typography>
                    Ruta #{index + 1} - Vehículo: {route.vehicle?.identifier || route.vehicle_id}
                  </Typography>
                  <Chip
                    label={`${route.visit_count} visitas`}
                    size="small"
                    color="primary"
                  />
                  {route.total_distance_km && (
                    <Chip
                      label={`${route.total_distance_km.toFixed(1)} km`}
                      size="small"
                    />
                  )}
                  {route.total_duration_minutes && (
                    <Chip
                      label={`${Math.round(route.total_duration_minutes)} min`}
                      size="small"
                    />
                  )}
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                {/* Personnel assigned */}
                {route.personnel && route.personnel.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" gutterBottom>
                      <strong>Personal asignado:</strong>
                    </Typography>
                    <Stack spacing={1}>
                      {route.personnel.map((p) => (
                        <Box key={p.id}>
                          <Typography variant="body2" sx={{ fontWeight: 'medium', mb: 0.5 }}>
                            {p.name}
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, ml: 2 }}>
                            {p.skills && p.skills.length > 0 ? (
                              p.skills.map((skill) => (
                                <Chip
                                  key={skill}
                                  label={skill}
                                  size="small"
                                  color="primary"
                                  variant="outlined"
                                />
                              ))
                            ) : (
                              <Typography variant="caption" color="text.secondary">
                                Sin habilidades registradas
                              </Typography>
                            )}
                          </Box>
                        </Box>
                      ))}
                    </Stack>
                  </Box>
                )}

                {/* Visits table */}
                {route.visits && route.visits.length > 0 ? (
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>#</TableCell>
                          <TableCell>Caso ID</TableCell>
                          <TableCell>Paciente</TableCell>
                          <TableCell>Tipo de Atención</TableCell>
                          <TableCell>Hora Estimada Llegada</TableCell>
                          <TableCell>Hora Estimada Salida</TableCell>
                          <TableCell>Estado</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {route.visits
                          .sort((a, b) => a.sequence_number - b.sequence_number)
                          .map((visit) => (
                            <TableRow key={visit.id}>
                              <TableCell>{visit.sequence_number + 1}</TableCell>
                              <TableCell>{visit.case_id}</TableCell>
                              <TableCell>
                                {visit.patient?.name || `Paciente #${visit.case?.patient_id || 'N/A'}`}
                              </TableCell>
                              <TableCell>
                                {visit.care_type?.name || `Tipo #${visit.case?.care_type_id || 'N/A'}`}
                              </TableCell>
                              <TableCell>
                                {visit.estimated_arrival_time
                                  ? new Date(visit.estimated_arrival_time).toLocaleTimeString('es-ES', {
                                      hour: '2-digit',
                                      minute: '2-digit',
                                    })
                                  : '-'}
                              </TableCell>
                              <TableCell>
                                {visit.estimated_departure_time
                                  ? new Date(visit.estimated_departure_time).toLocaleTimeString('es-ES', {
                                      hour: '2-digit',
                                      minute: '2-digit',
                                    })
                                  : '-'}
                              </TableCell>
                              <TableCell>
                                <Chip
                                  label={visit.status.toUpperCase()}
                                  size="small"
                                  color="default"
                                />
                              </TableCell>
                            </TableRow>
                          ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Alert severity="info">No hay visitas en esta ruta.</Alert>
                )}
              </AccordionDetails>
            </Accordion>
          ))}
        </Stack>
      </Box>

      {/* Action Buttons */}
      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
        <Button variant="outlined" onClick={onReoptimize}>
          Re-optimizar
        </Button>
        <Button
          variant="contained"
          color="success"
          onClick={onApproveRoutes}
          disabled={hasErrors || isApproving}
          startIcon={<CheckCircleIcon />}
        >
          {isApproving ? 'Aprobando...' : 'Aprobar y Activar Rutas'}
        </Button>
      </Box>
    </Paper>
  )
}
