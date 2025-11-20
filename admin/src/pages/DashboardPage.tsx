import { Box, Card, CardContent, Grid, Typography } from '@mui/material'
import {
  People,
  DirectionsCar,
  PersonPin,
  MedicalServices,
} from '@mui/icons-material'

interface StatCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  color: string
}

function StatCard({ title, value, icon, color }: StatCardProps) {
  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography color="text.secondary" variant="overline">
              {title}
            </Typography>
            <Typography variant="h4" component="div">
              {value}
            </Typography>
          </Box>
          <Box
            sx={{
              backgroundColor: color,
              borderRadius: 2,
              p: 1.5,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  )
}

export default function DashboardPage() {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Panel Principal
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Bienvenido al Sistema de Optimización de Rutas para Hospitalización Domiciliaria
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Personal Activo"
            value="0"
            icon={<People sx={{ color: 'white' }} />}
            color="#1976d2"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Vehículos"
            value="0"
            icon={<DirectionsCar sx={{ color: 'white' }} />}
            color="#2e7d32"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Pacientes"
            value="0"
            icon={<PersonPin sx={{ color: 'white' }} />}
            color="#ed6c02"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Casos Pendientes"
            value="0"
            icon={<MedicalServices sx={{ color: 'white' }} />}
            color="#d32f2f"
          />
        </Grid>
      </Grid>

      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Acciones Rápidas
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Utiliza el menú lateral para navegar a las diferentes secciones del sistema.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
