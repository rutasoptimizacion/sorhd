/**
 * ConnectionStatus Component
 * Displays WebSocket connection status indicator
 */

import { Box, Chip, Tooltip, CircularProgress } from '@mui/material'
import WifiIcon from '@mui/icons-material/Wifi'
import WifiOffIcon from '@mui/icons-material/WifiOff'
import ErrorIcon from '@mui/icons-material/Error'
import { useSelector } from 'react-redux'
import { RootState } from '@/store'
import { selectConnectionStatus } from '@/store/monitoringSlice'
import type { ConnectionStatus as ConnectionStatusType } from '@/services/websocketService'

interface ConnectionStatusProps {
  size?: 'small' | 'medium'
  showLabel?: boolean
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  size = 'small',
  showLabel = true
}) => {
  const connectionStatus = useSelector((state: RootState) => selectConnectionStatus(state))

  const getStatusConfig = (status: ConnectionStatusType) => {
    switch (status) {
      case 'connected':
        return {
          color: 'success' as const,
          icon: <WifiIcon fontSize={size} />,
          label: 'Conectado',
          tooltip: 'Conexión en tiempo real activa'
        }
      case 'connecting':
        return {
          color: 'warning' as const,
          icon: <CircularProgress size={size === 'small' ? 16 : 20} />,
          label: 'Conectando',
          tooltip: 'Estableciendo conexión...'
        }
      case 'disconnected':
        return {
          color: 'default' as const,
          icon: <WifiOffIcon fontSize={size} />,
          label: 'Desconectado',
          tooltip: 'Sin conexión en tiempo real'
        }
      case 'error':
        return {
          color: 'error' as const,
          icon: <ErrorIcon fontSize={size} />,
          label: 'Error',
          tooltip: 'Error de conexión. Reintentando...'
        }
      default:
        return {
          color: 'default' as const,
          icon: <WifiOffIcon fontSize={size} />,
          label: 'Desconocido',
          tooltip: 'Estado desconocido'
        }
    }
  }

  const config = getStatusConfig(connectionStatus)

  return (
    <Tooltip title={config.tooltip} arrow>
      <Box sx={{ display: 'inline-flex', alignItems: 'center' }}>
        <Chip
          icon={config.icon}
          label={showLabel ? config.label : undefined}
          color={config.color}
          size={size}
          variant={connectionStatus === 'connected' ? 'filled' : 'outlined'}
          sx={{
            fontWeight: connectionStatus === 'connected' ? 'bold' : 'normal',
            animation: connectionStatus === 'connecting' ? 'pulse 2s infinite' : 'none',
            '@keyframes pulse': {
              '0%, 100%': {
                opacity: 1
              },
              '50%': {
                opacity: 0.5
              }
            }
          }}
        />
      </Box>
    </Tooltip>
  )
}

export default ConnectionStatus
