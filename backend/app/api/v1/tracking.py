"""
GPS Tracking API Endpoints
Handles location uploads, WebSocket subscriptions, and real-time updates
"""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle
from app.models.route import Route, VisitStatus
from app.schemas.tracking import (
    LocationUpload,
    LocationResponse,
    VehicleLocationResponse,
    ETAResponse,
    DelayAlertResponse,
    RouteProgressResponse,
    SubscribeRequest
)
from app.services.tracking import (
    LocationTracker,
    RouteTrackerService,
    ETACalculator,
    DelayDetector,
    connection_manager
)
from app.core.exceptions import NotFoundError, ValidationError


router = APIRouter(prefix="/tracking", tags=["tracking"])


@router.post("/location", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def upload_location(
    location: LocationUpload,
    vehicle_id: int = Query(..., description="Vehicle ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload GPS location for a vehicle.

    **Rate limit:** 120 requests per minute per vehicle

    **Permissions:** Clinical Team members only
    """
    # Only clinical team can upload locations
    if current_user.role != UserRole.CLINICAL_TEAM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clinical team members can upload locations"
        )

    # Create location tracker
    tracker = LocationTracker(db)

    try:
        # Record location
        location_log = tracker.record_location(
            vehicle_id=vehicle_id,
            latitude=location.latitude,
            longitude=location.longitude,
            speed_kmh=location.speed_kmh,
            heading_degrees=location.heading_degrees,
            accuracy_meters=location.accuracy_meters,
            timestamp=location.timestamp
        )

        # Convert to response format
        location_dict = tracker.get_location_as_dict(location_log)

        # Broadcast to WebSocket subscribers
        await connection_manager.broadcast_location_update(
            vehicle_id=vehicle_id,
            location_data=location_dict
        )

        return LocationResponse(**location_dict)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/vehicle/{vehicle_id}", response_model=VehicleLocationResponse)
async def get_vehicle_location(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current location of a vehicle.

    **Permissions:** All authenticated users
    """
    # Get vehicle
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    # Get current location
    tracker = LocationTracker(db)
    current_location = tracker.get_current_location(vehicle_id)

    response = VehicleLocationResponse(
        vehicle_id=vehicle_id,
        vehicle_identifier=vehicle.identifier,
        current_location=None,
        last_update=None,
        is_active=vehicle.is_active
    )

    if current_location:
        location_dict = tracker.get_location_as_dict(current_location)
        response.current_location = LocationResponse(**location_dict)
        response.last_update = location_dict["timestamp"]

    return response


@router.get("/vehicle/{vehicle_id}/history", response_model=List[LocationResponse])
async def get_vehicle_location_history(
    vehicle_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get location history for a vehicle.

    **Permissions:** Admin only
    """
    # Only admins can view history
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view location history"
        )

    tracker = LocationTracker(db)
    history = tracker.get_location_history(
        vehicle_id=vehicle_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )

    return [
        LocationResponse(**tracker.get_location_as_dict(log))
        for log in history
    ]


@router.get("/routes/active", response_model=List[dict])
async def get_active_routes(
    route_date: Optional[date] = None,
    vehicle_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all active routes.

    **Permissions:** All authenticated users
    """
    route_tracker = RouteTrackerService(db)
    routes = route_tracker.get_active_routes(
        route_date=route_date,
        vehicle_id=vehicle_id
    )

    result = []
    for route in routes:
        result.append({
            "id": route.id,
            "vehicle_id": route.vehicle_id,
            "vehicle_identifier": route.vehicle.identifier,
            "route_date": route.route_date.isoformat(),
            "status": route.status.value,
            "total_distance_km": route.total_distance_km,
            "total_duration_minutes": route.total_duration_minutes,
            "total_visits": len(route.visits),
            "completed_visits": sum(1 for v in route.visits if v.status == VisitStatus.COMPLETED)
        })

    return result


@router.get("/routes/{route_id}/progress", response_model=RouteProgressResponse)
async def get_route_progress(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get progress statistics for a route.

    **Permissions:** All authenticated users
    """
    route_tracker = RouteTrackerService(db)

    try:
        progress = route_tracker.get_route_progress(route_id)
        return RouteProgressResponse(**progress)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/visits/{visit_id}/eta", response_model=ETAResponse)
async def get_visit_eta(
    visit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get estimated time of arrival for a visit.

    **Permissions:** All authenticated users
    """
    from app.models.route import Visit

    # Get visit to find vehicle
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")

    vehicle_id = visit.route.vehicle_id

    # Calculate ETA
    eta_calculator = ETACalculator(db)
    eta_details = eta_calculator.calculate_eta_with_details(visit_id, vehicle_id)

    if not eta_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cannot calculate ETA: no location data available"
        )

    return ETAResponse(**eta_details)


@router.get("/routes/{route_id}/delays", response_model=List[DelayAlertResponse])
async def get_route_delays(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get delay alerts for a route.

    **Permissions:** All authenticated users
    """
    delay_detector = DelayDetector(db)

    try:
        alerts = delay_detector.detect_delays_for_route(route_id)

        return [
            DelayAlertResponse(
                visit_id=alert.visit_id,
                route_id=alert.route_id,
                vehicle_id=alert.vehicle_id,
                case_id=alert.case_id,
                severity=alert.severity.value,
                delay_minutes=alert.delay_minutes,
                estimated_arrival=alert.estimated_arrival.isoformat() if alert.estimated_arrival else None,
                current_eta=alert.current_eta.isoformat() if alert.current_eta else None,
                message=alert.message,
                detected_at=alert.detected_at.isoformat()
            )
            for alert in alerts
        ]
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.websocket("/live")
async def websocket_tracking(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time tracking updates.

    **Usage:**
    1. Connect to websocket: ws://host/api/v1/tracking/live?token=<jwt_token>
    2. Send subscription messages: {"action": "subscribe", "type": "vehicle", "id": 1}
    3. Receive real-time updates

    **Message Types:**
    - connection_established: Connection successful
    - subscription_confirmed: Subscription successful
    - location_update: Vehicle location updated
    - visit_status_update: Visit status changed
    - eta_update: ETA changed significantly
    - delay_alert: Delay detected
    - ping: Keep-alive ping
    """
    connection_id = str(uuid.uuid4())

    try:
        # Connect and authenticate
        await connection_manager.connect(websocket, connection_id, token)

        # Listen for messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()

                action = data.get("action")

                if action == "subscribe":
                    subscription_type = data.get("type")
                    entity_id = data.get("id")

                    if subscription_type == "vehicle":
                        await connection_manager.subscribe_to_vehicle(connection_id, entity_id)
                    elif subscription_type == "route":
                        await connection_manager.subscribe_to_route(connection_id, entity_id)
                    else:
                        await connection_manager.send_personal_message(
                            connection_id,
                            {"type": "error", "message": "Invalid subscription type"}
                        )

                elif action == "unsubscribe":
                    subscription_type = data.get("type")
                    entity_id = data.get("id")

                    if subscription_type == "vehicle":
                        await connection_manager.unsubscribe_from_vehicle(connection_id, entity_id)

                elif action == "pong":
                    # Client responding to ping
                    pass

                else:
                    await connection_manager.send_personal_message(
                        connection_id,
                        {"type": "error", "message": f"Unknown action: {action}"}
                    )

            except WebSocketDisconnect:
                break
            except Exception as e:
                # Send error message
                await connection_manager.send_personal_message(
                    connection_id,
                    {"type": "error", "message": str(e)}
                )

    except Exception:
        pass
    finally:
        # Clean up connection
        connection_manager.disconnect(connection_id)
