/**
 * useWebSocket Hook
 * React hook for WebSocket connection management
 */

import { useEffect, useState, useCallback } from 'react'
import { useSelector } from 'react-redux'
import { RootState } from '@/store'
import websocketService, {
  ConnectionStatus,
  WebSocketMessage,
  LocationUpdate,
  VisitStatusUpdate,
  ETAUpdate,
  DelayAlert
} from '@/services/websocketService'

export interface UseWebSocketOptions {
  autoConnect?: boolean
  subscribeToVehicles?: number[]
  subscribeToRoutes?: number[]
}

export interface UseWebSocketReturn {
  connectionStatus: ConnectionStatus
  isConnected: boolean
  connect: () => void
  disconnect: () => void
  subscribe: (type: 'vehicle' | 'route', id: number) => void
  unsubscribe: (type: 'vehicle' | 'route', id: number) => void
  subscriptions: { vehicles: number[], routes: number[] }
}

/**
 * Hook for managing WebSocket connection and subscriptions
 */
export const useWebSocket = (
  onMessage?: (message: WebSocketMessage) => void,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn => {
  const {
    autoConnect = false,
    subscribeToVehicles = [],
    subscribeToRoutes = []
  } = options

  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>(
    websocketService.getConnectionStatus()
  )
  const [subscriptions, setSubscriptions] = useState<{ vehicles: number[], routes: number[] }>({
    vehicles: [],
    routes: []
  })

  // Get auth token from Redux
  const token = useSelector((state: RootState) => state.auth.accessToken)

  // Connect function
  const connect = useCallback(() => {
    if (token) {
      websocketService.connect(token)
    } else {
      console.warn('[useWebSocket] Cannot connect: no auth token available')
    }
  }, [token])

  // Disconnect function
  const disconnect = useCallback(() => {
    websocketService.disconnect()
  }, [])

  // Subscribe function
  const subscribe = useCallback((type: 'vehicle' | 'route', id: number) => {
    websocketService.subscribe(type, id)
    setSubscriptions(websocketService.getSubscriptions())
  }, [])

  // Unsubscribe function
  const unsubscribe = useCallback((type: 'vehicle' | 'route', id: number) => {
    websocketService.unsubscribe(type, id)
    setSubscriptions(websocketService.getSubscriptions())
  }, [])

  // Set up message handler
  useEffect(() => {
    if (!onMessage) return

    const cleanup = websocketService.onMessage(onMessage)
    return cleanup
  }, [onMessage])

  // Set up status change handler
  useEffect(() => {
    const cleanup = websocketService.onStatusChange((status) => {
      setConnectionStatus(status)
      // Update subscriptions when connected
      if (status === 'connected') {
        setSubscriptions(websocketService.getSubscriptions())
      }
    })

    // Initialize status
    setConnectionStatus(websocketService.getConnectionStatus())

    return cleanup
  }, [])

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect && token && !websocketService.isConnected()) {
      connect()
    }
  }, [autoConnect, token, connect])

  // Subscribe to initial vehicles and routes
  useEffect(() => {
    if (websocketService.isConnected()) {
      subscribeToVehicles.forEach(id => subscribe('vehicle', id))
      subscribeToRoutes.forEach(id => subscribe('route', id))
    }
  }, [subscribeToVehicles, subscribeToRoutes, subscribe])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (autoConnect) {
        disconnect()
      }
    }
  }, [autoConnect, disconnect])

  return {
    connectionStatus,
    isConnected: connectionStatus === 'connected',
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    subscriptions
  }
}

/**
 * Hook for handling specific message types with type-safe callbacks
 */
export const useWebSocketMessages = (handlers: {
  onLocationUpdate?: (vehicleId: number, location: LocationUpdate) => void
  onVisitStatusUpdate?: (visitId: number, status: VisitStatusUpdate) => void
  onETAUpdate?: (visitId: number, eta: ETAUpdate) => void
  onDelayAlert?: (alert: DelayAlert) => void
}) => {
  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'location_update':
        if (handlers.onLocationUpdate && message.vehicle_id && message.data) {
          handlers.onLocationUpdate(message.vehicle_id, message.data)
        }
        break

      case 'visit_status_update':
        if (handlers.onVisitStatusUpdate && message.visit_id && message.data) {
          handlers.onVisitStatusUpdate(message.visit_id, message.data)
        }
        break

      case 'eta_update':
        if (handlers.onETAUpdate && message.visit_id && message.data) {
          handlers.onETAUpdate(message.visit_id, message.data)
        }
        break

      case 'delay_alert':
        if (handlers.onDelayAlert && message.data) {
          handlers.onDelayAlert(message.data)
        }
        break

      case 'connection_established':
        console.log('[WebSocket] Connection established')
        break

      case 'subscription_confirmed':
        console.log('[WebSocket] Subscription confirmed')
        break

      case 'error':
        console.error('[WebSocket] Error:', message.message)
        break

      default:
        console.log('[WebSocket] Unknown message type:', message.type)
    }
  }, [handlers])

  return { handleMessage }
}

export default useWebSocket
