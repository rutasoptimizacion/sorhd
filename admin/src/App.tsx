import React from 'react'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { Box, Typography } from '@mui/material'

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
})

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          flexDirection: 'column',
          gap: 2,
        }}
      >
        <Typography variant="h3" component="h1">
          SOR-HD Admin Panel
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Sistema de Optimización de Rutas para Hospitalización Domiciliaria
        </Typography>
      </Box>
    </ThemeProvider>
  )
}

export default App
