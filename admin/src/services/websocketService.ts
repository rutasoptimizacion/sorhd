/**
 * WebSocket Service for Real-Time Tracking
 * Handles WebSocket connection, authentication, subscriptions, and message handling
 */

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

export type WebSocketMessageType =
  | 'connection_established'
  | 'subscription_confirmed'
  | 'location_update'
  | 'visit_status_update'
  | 'eta_update'
  | 'delay_alert'
  | 'ping'
  | 'error'

export interface WebSocketMessage {
  type: WebSocketMessageType
  timestamp?: string
  vehicle_id?: number
  visit_id?: number
  route_id?: number
  data?: any
  message?: string
}

export interface SubscriptionRequest {
  action: 'subscribe' | 'unsubscribe'
  type: 'vehicle' | 'route'
  id: number
}

export interface LocationUpdate {
  latitude: number
  longitude: number
  timestamp: string
  speed?: number
  heading?: number
  accuracy?: number
}

export interface VisitStatusUpdate {
  status: string
  timestamp: string
  notes?: string
}

export interface ETAUpdate {
  eta_minutes: number
  arrival_time: string
  traffic_multiplier: number
}

export interface DelayAlert {
  visit_id: number
  route_id: number
  severity: 'minor' | 'moderate' | 'severe'
  delay_minutes: number
  time_window_start?: string
  time_window_end?: string
  estimated_arrival: string
  message: string
}

type MessageHandler = (message: WebSocketMessage) => void
type StatusChangeHandler = (status: ConnectionStatus) => void

class WebSocketService {
  private socket: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000 // Start with 1 second
  private maxReconnectDelay = 30000 // Max 30 seconds
  private reconnectTimeout: NodeJS.Timeout | null = null
  private pingInterval: NodeJS.Timeout | null = null
  private connectionStatus: ConnectionStatus = 'disconnected'
  private messageHandlers: Set<MessageHandler> = new Set()
  private statusChangeHandlers: Set<StatusChangeHandler> = new Set()
  private subscriptions: Map<string, Set<number>> = new Map([
    ['vehicles', new Set()],
    ['routes', new Set()]
  ])

  /**
   * Get WebSocket URL from environment or default
   */
  private getWebSocketUrl(): string {
    const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
    // Convert http:// to ws:// and https:// to wss://
    const wsUrl = apiUrl.replace(/^http/, 'ws')
    return `${wsUrl}/tracking/live`
  }

  /**
   * Connect to WebSocket with JWT authentication
   */
  connect(token?: string): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Already connected')
      return
    }

    // Get token from localStorage if not provided
    const authToken = token || localStorage.getItem('access_token')
    if (!authToken) {
      console.error('[WebSocket] No authentication token available')
      this.setConnectionStatus('error')
      return
    }

    const url = `${this.getWebSocketUrl()}?token=${authToken}`

    console.log('[WebSocket] Connecting to:', this.getWebSocketUrl())
    this.setConnectionStatus('connecting')

    try {
      this.socket = new WebSocket(url)
      this.setupSocketHandlers()
    } catch (error) {
      console.error('[WebSocket] Connection error:', error)
      this.setConnectionStatus('error')
      this.scheduleReconnect()
    }
  }

  /**
   * Set up WebSocket event handlers
   */
  private setupSocketHandlers(): void {
    if (!this.socket) return

    this.socket.onopen = () => {
      console.log('[WebSocket] Connected successfully')
      this.setConnectionStatus('connected')
      this.reconnectAttempts = 0
      this.reconnectDelay = 1000
      this.startPingInterval()

      // Re-subscribe to previous subscriptions
      this.resubscribe()
    }

    this.socket.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        console.log('[WebSocket] Message received:', message.type)

        // Handle ping messages automatically
        if (message.type === 'ping') {
          this.sendPong()
          return
        }

        // Notify all message handlers
        this.messageHandlers.forEach(handler => {
          try {
            handler(message)
          } catch (error) {
            console.error('[WebSocket] Error in message handler:', error)
          }
        })
      } catch (error) {
        console.error('[WebSocket] Error parsing message:', error)
      }
    }

    this.socket.onerror = (error) => {
      console.error('[WebSocket] Error:', error)
      this.setConnectionStatus('error')
    }

    this.socket.onclose = (event) => {
      console.log('[WebSocket] Connection closed:', event.code, event.reason)
      this.setConnectionStatus('disconnected')
      this.stopPingInterval()

      // Attempt reconnection if not a normal closure
      if (event.code !== 1000) {
        this.scheduleReconnect()
      }
    }
  }

  /**
   * Send pong response to ping
   */
  private sendPong(): void {
    this.send({
      action: 'pong'
    })
  }

  /**
   * Start ping interval to keep connection alive (client-side)
   */
  private startPingInterval(): void {
    this.stopPingInterval()
    // Send ping every 25 seconds (backend pings every 30 seconds)
    this.pingInterval = setInterval(() => {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        // Server sends pings, we just respond with pong
        // This interval is just to check connection status
        console.log('[WebSocket] Connection check')
      }
    }, 25000)
  }

  /**
   * Stop ping interval
   */
  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnection attempts reached')
      this.setConnectionStatus('error')
      return
    }

    // Clear any existing reconnect timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
    }

    this.reconnectAttempts++
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    )

    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`)

    this.reconnectTimeout = setTimeout(() => {
      console.log('[WebSocket] Attempting reconnection...')
      this.connect()
    }, delay)
  }

  /**
   * Re-subscribe to previous subscriptions after reconnection
   */
  private resubscribe(): void {
    // Subscribe to vehicles
    this.subscriptions.get('vehicles')?.forEach(vehicleId => {
      this.subscribe('vehicle', vehicleId)
    })

    // Subscribe to routes
    this.subscriptions.get('routes')?.forEach(routeId => {
      this.subscribe('route', routeId)
    })
  }

  /**
   * Subscribe to vehicle or route updates
   */
  subscribe(type: 'vehicle' | 'route', id: number): void {
    const request: SubscriptionRequest = {
      action: 'subscribe',
      type,
      id
    }

    this.send(request)

    // Track subscription
    const key = `${type}s` as 'vehicles' | 'routes'
    this.subscriptions.get(key)?.add(id)

    console.log(`[WebSocket] Subscribed to ${type} ${id}`)
  }

  /**
   * Unsubscribe from vehicle or route updates
   */
  unsubscribe(type: 'vehicle' | 'route', id: number): void {
    const request: SubscriptionRequest = {
      action: 'unsubscribe',
      type,
      id
    }

    this.send(request)

    // Remove from tracked subscriptions
    const key = `${type}s` as 'vehicles' | 'routes'
    this.subscriptions.get(key)?.delete(id)

    console.log(`[WebSocket] Unsubscribed from ${type} ${id}`)
  }

  /**
   * Send message through WebSocket
   */
  private send(data: any): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data))
    } else {
      console.warn('[WebSocket] Cannot send message, not connected')
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    console.log('[WebSocket] Disconnecting...')

    // Clear reconnection timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }

    // Stop ping interval
    this.stopPingInterval()

    // Close socket
    if (this.socket) {
      this.socket.close(1000, 'Client disconnect')
      this.socket = null
    }

    this.setConnectionStatus('disconnected')
    this.reconnectAttempts = 0
  }

  /**
   * Add message handler
   */
  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler)

    // Return cleanup function
    return () => {
      this.messageHandlers.delete(handler)
    }
  }

  /**
   * Add status change handler
   */
  onStatusChange(handler: StatusChangeHandler): () => void {
    this.statusChangeHandlers.add(handler)

    // Return cleanup function
    return () => {
      this.statusChangeHandlers.delete(handler)
    }
  }

  /**
   * Set connection status and notify handlers
   */
  private setConnectionStatus(status: ConnectionStatus): void {
    if (this.connectionStatus !== status) {
      this.connectionStatus = status
      console.log('[WebSocket] Status changed to:', status)

      this.statusChangeHandlers.forEach(handler => {
        try {
          handler(status)
        } catch (error) {
          console.error('[WebSocket] Error in status change handler:', error)
        }
      })
    }
  }

  /**
   * Get current connection status
   */
  getConnectionStatus(): ConnectionStatus {
    return this.connectionStatus
  }

  /**
   * Check if currently connected
   */
  isConnected(): boolean {
    return this.connectionStatus === 'connected' &&
           this.socket !== null &&
           this.socket.readyState === WebSocket.OPEN
  }

  /**
   * Get current subscriptions
   */
  getSubscriptions(): { vehicles: number[], routes: number[] } {
    return {
      vehicles: Array.from(this.subscriptions.get('vehicles') || []),
      routes: Array.from(this.subscriptions.get('routes') || [])
    }
  }
}

// Export singleton instance
export const websocketService = new WebSocketService()

export default websocketService
