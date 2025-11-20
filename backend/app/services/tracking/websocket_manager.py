"""
WebSocket Manager for Real-Time Tracking
Handles WebSocket connections, authentication, subscriptions, and broadcasts
"""
from typing import Dict, Set, Optional, List
from fastapi import WebSocket, WebSocketDisconnect, status
from datetime import datetime
import json
import asyncio
from collections import defaultdict

from app.core.security import verify_access_token
from app.core.exceptions import AuthenticationError


class ConnectionManager:
    """Manages WebSocket connections for real-time tracking"""

    def __init__(self):
        # Active connections: connection_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}

        # User subscriptions: connection_id -> user_id
        self.connection_users: Dict[str, int] = {}

        # Vehicle subscriptions: vehicle_id -> Set[connection_id]
        self.vehicle_subscriptions: Dict[int, Set[str]] = defaultdict(set)

        # Route subscriptions: route_id -> Set[connection_id]
        self.route_subscriptions: Dict[int, Set[str]] = defaultdict(set)

        # All subscriptions: connection_id -> {'vehicles': Set[int], 'routes': Set[int]}
        self.subscriptions: Dict[str, Dict[str, Set[int]]] = defaultdict(
            lambda: {"vehicles": set(), "routes": set()}
        )

    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        token: Optional[str] = None
    ) -> bool:
        """
        Accept WebSocket connection with authentication

        Args:
            websocket: WebSocket instance
            connection_id: Unique connection identifier
            token: JWT authentication token (optional)

        Returns:
            True if connection successful

        Raises:
            AuthenticationError: If authentication fails
        """
        await websocket.accept()

        # Authenticate if token provided
        if token:
            try:
                payload = verify_access_token(token)
                if payload:
                    user_id = payload.get("sub")
                    if user_id:
                        self.connection_users[connection_id] = int(user_id)
                else:
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    raise AuthenticationError("Invalid authentication token")
            except Exception:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                raise AuthenticationError("Invalid authentication token")

        # Store connection
        self.active_connections[connection_id] = websocket

        # Send connection confirmation
        await self._send_message(
            websocket,
            {
                "type": "connection_established",
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        return True

    def disconnect(self, connection_id: str):
        """
        Remove connection and clean up subscriptions

        Args:
            connection_id: Connection identifier
        """
        # Remove from active connections
        self.active_connections.pop(connection_id, None)
        self.connection_users.pop(connection_id, None)

        # Remove from vehicle subscriptions
        if connection_id in self.subscriptions:
            for vehicle_id in self.subscriptions[connection_id]["vehicles"]:
                self.vehicle_subscriptions[vehicle_id].discard(connection_id)

            # Remove from route subscriptions
            for route_id in self.subscriptions[connection_id]["routes"]:
                self.route_subscriptions[route_id].discard(connection_id)

            # Remove subscription record
            del self.subscriptions[connection_id]

    async def subscribe_to_vehicle(self, connection_id: str, vehicle_id: int):
        """
        Subscribe connection to vehicle updates

        Args:
            connection_id: Connection identifier
            vehicle_id: Vehicle ID to subscribe to
        """
        self.vehicle_subscriptions[vehicle_id].add(connection_id)
        self.subscriptions[connection_id]["vehicles"].add(vehicle_id)

        # Send confirmation
        websocket = self.active_connections.get(connection_id)
        if websocket:
            await self._send_message(
                websocket,
                {
                    "type": "subscription_confirmed",
                    "subscription_type": "vehicle",
                    "vehicle_id": vehicle_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

    async def subscribe_to_route(self, connection_id: str, route_id: int):
        """
        Subscribe connection to route updates

        Args:
            connection_id: Connection identifier
            route_id: Route ID to subscribe to
        """
        self.route_subscriptions[route_id].add(connection_id)
        self.subscriptions[connection_id]["routes"].add(route_id)

        # Send confirmation
        websocket = self.active_connections.get(connection_id)
        if websocket:
            await self._send_message(
                websocket,
                {
                    "type": "subscription_confirmed",
                    "subscription_type": "route",
                    "route_id": route_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

    async def unsubscribe_from_vehicle(self, connection_id: str, vehicle_id: int):
        """
        Unsubscribe connection from vehicle updates

        Args:
            connection_id: Connection identifier
            vehicle_id: Vehicle ID to unsubscribe from
        """
        self.vehicle_subscriptions[vehicle_id].discard(connection_id)
        self.subscriptions[connection_id]["vehicles"].discard(vehicle_id)

        # Send confirmation
        websocket = self.active_connections.get(connection_id)
        if websocket:
            await self._send_message(
                websocket,
                {
                    "type": "unsubscribed",
                    "subscription_type": "vehicle",
                    "vehicle_id": vehicle_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

    async def broadcast_location_update(
        self,
        vehicle_id: int,
        location_data: dict
    ):
        """
        Broadcast location update to all subscribers

        Args:
            vehicle_id: Vehicle ID
            location_data: Location data dictionary
        """
        subscribers = self.vehicle_subscriptions.get(vehicle_id, set())

        message = {
            "type": "location_update",
            "vehicle_id": vehicle_id,
            "data": location_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Send to all subscribers
        disconnected = []
        for connection_id in subscribers:
            websocket = self.active_connections.get(connection_id)
            if websocket:
                try:
                    await self._send_message(websocket, message)
                except Exception:
                    disconnected.append(connection_id)
            else:
                disconnected.append(connection_id)

        # Clean up disconnected clients
        for connection_id in disconnected:
            self.disconnect(connection_id)

    async def broadcast_visit_status_update(
        self,
        route_id: int,
        visit_id: int,
        status_data: dict
    ):
        """
        Broadcast visit status update to route subscribers

        Args:
            route_id: Route ID
            visit_id: Visit ID
            status_data: Status data dictionary
        """
        subscribers = self.route_subscriptions.get(route_id, set())

        message = {
            "type": "visit_status_update",
            "route_id": route_id,
            "visit_id": visit_id,
            "data": status_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Send to all subscribers
        disconnected = []
        for connection_id in subscribers:
            websocket = self.active_connections.get(connection_id)
            if websocket:
                try:
                    await self._send_message(websocket, message)
                except Exception:
                    disconnected.append(connection_id)
            else:
                disconnected.append(connection_id)

        # Clean up disconnected clients
        for connection_id in disconnected:
            self.disconnect(connection_id)

    async def broadcast_eta_update(
        self,
        route_id: int,
        visit_id: int,
        eta_data: dict
    ):
        """
        Broadcast ETA update to route subscribers

        Args:
            route_id: Route ID
            visit_id: Visit ID
            eta_data: ETA data dictionary
        """
        subscribers = self.route_subscriptions.get(route_id, set())

        message = {
            "type": "eta_update",
            "route_id": route_id,
            "visit_id": visit_id,
            "data": eta_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Send to all subscribers
        disconnected = []
        for connection_id in subscribers:
            websocket = self.active_connections.get(connection_id)
            if websocket:
                try:
                    await self._send_message(websocket, message)
                except Exception:
                    disconnected.append(connection_id)
            else:
                disconnected.append(connection_id)

        # Clean up disconnected clients
        for connection_id in disconnected:
            self.disconnect(connection_id)

    async def broadcast_delay_alert(
        self,
        route_id: int,
        alert_data: dict
    ):
        """
        Broadcast delay alert to route subscribers

        Args:
            route_id: Route ID
            alert_data: Alert data dictionary
        """
        subscribers = self.route_subscriptions.get(route_id, set())

        message = {
            "type": "delay_alert",
            "route_id": route_id,
            "data": alert_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Send to all subscribers
        disconnected = []
        for connection_id in subscribers:
            websocket = self.active_connections.get(connection_id)
            if websocket:
                try:
                    await self._send_message(websocket, message)
                except Exception:
                    disconnected.append(connection_id)
            else:
                disconnected.append(connection_id)

        # Clean up disconnected clients
        for connection_id in disconnected:
            self.disconnect(connection_id)

    async def send_personal_message(self, connection_id: str, message: dict):
        """
        Send message to specific connection

        Args:
            connection_id: Connection identifier
            message: Message dictionary
        """
        websocket = self.active_connections.get(connection_id)
        if websocket:
            await self._send_message(websocket, message)

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)

    def get_vehicle_subscriber_count(self, vehicle_id: int) -> int:
        """Get number of subscribers for a vehicle"""
        return len(self.vehicle_subscriptions.get(vehicle_id, set()))

    def get_route_subscriber_count(self, route_id: int) -> int:
        """Get number of subscribers for a route"""
        return len(self.route_subscriptions.get(route_id, set()))

    async def _send_message(self, websocket: WebSocket, message: dict):
        """
        Send JSON message to WebSocket

        Args:
            websocket: WebSocket instance
            message: Message dictionary
        """
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            # Connection may be closed
            raise e

    async def ping_all(self):
        """Send ping to all connections to keep them alive"""
        message = {
            "type": "ping",
            "timestamp": datetime.utcnow().isoformat()
        }

        disconnected = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await self._send_message(websocket, message)
            except Exception:
                disconnected.append(connection_id)

        # Clean up disconnected clients
        for connection_id in disconnected:
            self.disconnect(connection_id)


# Global connection manager instance
connection_manager = ConnectionManager()


async def keep_alive_task():
    """Background task to keep connections alive with periodic pings"""
    while True:
        await asyncio.sleep(30)  # Ping every 30 seconds
        await connection_manager.ping_all()
