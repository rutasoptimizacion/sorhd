import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Box,
  Button,
  Card,
  CardContent,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  Container,
} from '@mui/material'
import { LoginOutlined } from '@mui/icons-material'
import { useAppDispatch } from '@/hooks'
import { loginSuccess, setError, setLoading } from '@/store/authSlice'
import { authService } from '@/services/authService'

// Validation schema
const loginSchema = z.object({
  username: z.string().min(1, 'El nombre de usuario es requerido'),
  password: z.string().min(1, 'La contraseña es requerida'),
})

type LoginFormData = z.infer<typeof loginSchema>

export default function LoginPage() {
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true)
    setErrorMessage(null)
    dispatch(setLoading(true))

    try {
      const response = await authService.login(data)

      dispatch(
        loginSuccess({
          accessToken: response.access_token,
          refreshToken: response.refresh_token,
          user: response.user,
        })
      )

      // Redirect to dashboard
      navigate('/')
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Error al iniciar sesión'
      setErrorMessage(message)
      dispatch(setError(message))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f5f5f5',
      }}
    >
      <Container maxWidth="sm">
        <Card elevation={3}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              <Typography variant="h4" component="h1" gutterBottom fontWeight="bold">
                SOR-HD
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Sistema de Optimización de Rutas
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Hospitalización Domiciliaria
              </Typography>
            </Box>

            {errorMessage && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {errorMessage}
              </Alert>
            )}

            <form onSubmit={handleSubmit(onSubmit)}>
              <TextField
                fullWidth
                label="Usuario"
                margin="normal"
                autoComplete="username"
                autoFocus
                error={!!errors.username}
                helperText={errors.username?.message}
                {...register('username')}
              />

              <TextField
                fullWidth
                label="Contraseña"
                type="password"
                margin="normal"
                autoComplete="current-password"
                error={!!errors.password}
                helperText={errors.password?.message}
                {...register('password')}
              />

              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                startIcon={isLoading ? <CircularProgress size={20} /> : <LoginOutlined />}
                disabled={isLoading}
                sx={{ mt: 3, mb: 2 }}
              >
                {isLoading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
              </Button>
            </form>

            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2, textAlign: 'center' }}>
              Panel de Administración v1.0
            </Typography>
          </CardContent>
        </Card>
      </Container>
    </Box>
  )
}
