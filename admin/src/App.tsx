import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Provider } from 'react-redux'
import { QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { store } from '@/store'
import { queryClient } from '@/lib/queryClient'
import Layout from '@/components/layout/Layout'
import PrivateRoute from '@/components/auth/PrivateRoute'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import NotFoundPage from '@/pages/NotFoundPage'
import UsersPage from '@/pages/UsersPage'
import SkillsPage from '@/pages/SkillsPage'
import CareTypesPage from '@/pages/CareTypesPage'
import PersonnelPage from '@/pages/PersonnelPage'
import VehiclesPage from '@/pages/VehiclesPage'
import PatientsPage from '@/pages/PatientsPage'
import CasesPage from '@/pages/CasesPage'
import RoutePlanningPage from '@/pages/RoutePlanningPage'
import RoutesPage from '@/pages/RoutesPage'
import MonitoringPage from '@/pages/MonitoringPage'

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
  },
})

function App() {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <BrowserRouter>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<LoginPage />} />

              {/* Protected routes */}
              <Route
                path="/"
                element={
                  <PrivateRoute>
                    <Layout>
                      <DashboardPage />
                    </Layout>
                  </PrivateRoute>
                }
              />

              {/* Resource Management Routes */}
              <Route
                path="/users"
                element={
                  <PrivateRoute>
                    <Layout>
                      <UsersPage />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/skills"
                element={
                  <PrivateRoute>
                    <Layout>
                      <SkillsPage />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/care-types"
                element={
                  <PrivateRoute>
                    <Layout>
                      <CareTypesPage />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/personnel"
                element={
                  <PrivateRoute>
                    <Layout>
                      <PersonnelPage />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/vehicles"
                element={
                  <PrivateRoute>
                    <Layout>
                      <VehiclesPage />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/patients"
                element={
                  <PrivateRoute>
                    <Layout>
                      <PatientsPage />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/cases"
                element={
                  <PrivateRoute>
                    <Layout>
                      <CasesPage />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/planning"
                element={
                  <PrivateRoute>
                    <Layout>
                      <RoutePlanningPage />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/routes"
                element={
                  <PrivateRoute>
                    <Layout>
                      <RoutesPage />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/monitoring"
                element={
                  <PrivateRoute>
                    <Layout>
                      <MonitoringPage />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/notifications"
                element={
                  <PrivateRoute>
                    <Layout>
                      <div>Notificaciones - En desarrollo</div>
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/reports"
                element={
                  <PrivateRoute>
                    <Layout>
                      <div>Reportes - En desarrollo</div>
                    </Layout>
                  </PrivateRoute>
                }
              />

              {/* 404 route */}
              <Route path="/404" element={<NotFoundPage />} />
              <Route path="*" element={<Navigate to="/404" replace />} />
            </Routes>
          </BrowserRouter>
        </ThemeProvider>
      </QueryClientProvider>
    </Provider>
  )
}

export default App
