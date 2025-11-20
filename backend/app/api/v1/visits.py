"""
Visit Management API Endpoints
Handles visit status updates and visit-related operations
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.route import Visit, VisitStatus
from app.schemas.tracking import (
    VisitStatusUpdate,
    VisitStatusResponse,
    MyVisitResponse,
    VisitInMyVisit,
    CaseInVisit,
    CareTypeInVisit,
    PatientInVisit,
    RouteInVisit,
    VehicleInVisit,
    PersonnelInVisit,
    LocationInVisit
)
from app.services.tracking import RouteTrackerService, connection_manager, ETACalculator
from app.core.exceptions import NotFoundError, ValidationError


router = APIRouter(prefix="/visits", tags=["visits"])


@router.patch("/{visit_id}/status", response_model=VisitStatusResponse)
async def update_visit_status(
    visit_id: int,
    status_update: VisitStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update the status of a visit.

    **Valid status transitions:**
    - pending → en_route, cancelled
    - en_route → arrived, cancelled
    - arrived → in_progress, cancelled
    - in_progress → completed, failed
    - completed → (terminal state)
    - cancelled → (terminal state)
    - failed → (terminal state)

    **Permissions:** Clinical Team members only

    **Side effects:**
    - Updates associated case status
    - Checks if route should be marked as completed
    - Broadcasts status update via WebSocket
    - May trigger notification to patient
    """
    # Only clinical team can update visit status
    if current_user.role != UserRole.CLINICAL_TEAM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clinical team members can update visit status"
        )

    # Parse status enum
    try:
        new_status = VisitStatus(status_update.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {status_update.status}"
        )

    # Update status using route tracker
    route_tracker = RouteTrackerService(db)

    try:
        updated_visit = route_tracker.update_visit_status(
            visit_id=visit_id,
            new_status=new_status,
            notes=status_update.notes
        )

        # Prepare response
        response = VisitStatusResponse(
            id=updated_visit.id,
            route_id=updated_visit.route_id,
            case_id=updated_visit.case_id,
            sequence_number=updated_visit.sequence_number,
            status=updated_visit.status.value,
            estimated_arrival_time=updated_visit.estimated_arrival_time,
            estimated_departure_time=updated_visit.estimated_departure_time,
            actual_arrival_time=updated_visit.actual_arrival_time,
            actual_departure_time=updated_visit.actual_departure_time,
            notes=updated_visit.notes
        )

        # Broadcast status update via WebSocket
        await connection_manager.broadcast_visit_status_update(
            route_id=updated_visit.route_id,
            visit_id=visit_id,
            status_data={
                "status": updated_visit.status.value,
                "notes": updated_visit.notes,
                "actual_arrival_time": updated_visit.actual_arrival_time.isoformat() if updated_visit.actual_arrival_time else None,
                "actual_departure_time": updated_visit.actual_departure_time.isoformat() if updated_visit.actual_departure_time else None
            }
        )

        # TODO: Trigger notification to patient when status changes
        # This will be implemented in Phase 6 when notification service is ready

        return response

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/my-visit", response_model=MyVisitResponse)
async def get_my_upcoming_visit(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the upcoming or in-progress visit for the current patient.

    Returns the next visit (pending, en_route, arrived, or in_progress) for the
    patient associated with the current user. Used by the mobile app patient profile.

    **Permissions:** Patient role only

    **Returns:** Visit data with full case, route, vehicle, personnel details, and ETA
    """
    from app.models.patient import Patient
    from app.models.case import Case, CareType
    from app.models.route import Route
    from app.models.vehicle import Vehicle
    from app.models.personnel import Personnel
    from sqlalchemy.orm import joinedload
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"Getting visit for user_id={current_user.id}, username={current_user.username}, role={current_user.role}")

    # Get patient record for current user
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        logger.warning(f"No patient record found for user_id={current_user.id}")
        return MyVisitResponse(visit=None, route=None, eta_minutes=None)

    logger.info(f"Found patient_id={patient.id} for user_id={current_user.id}")

    # Find upcoming visit for this patient with all relationships eagerly loaded
    visit = (
        db.query(Visit)
        .join(Case, Visit.case_id == Case.id)
        .options(
            joinedload(Visit.case).joinedload(Case.patient),
            joinedload(Visit.case).joinedload(Case.care_type)
        )
        .filter(Case.patient_id == patient.id)
        .filter(Visit.status.in_([
            VisitStatus.PENDING,
            VisitStatus.EN_ROUTE,
            VisitStatus.ARRIVED,
            VisitStatus.IN_PROGRESS
        ]))
        .order_by(Visit.estimated_arrival_time)
        .first()
    )

    if not visit:
        logger.info(f"No upcoming visits found for patient_id={patient.id}")
        return MyVisitResponse(visit=None, route=None, eta_minutes=None)

    logger.info(f"Found visit_id={visit.id} for patient_id={patient.id}")

    # Load route with vehicle and personnel
    route = (
        db.query(Route)
        .options(
            joinedload(Route.vehicle),
            joinedload(Route.assigned_personnel)
        )
        .filter(Route.id == visit.route_id)
        .first()
    )

    # Calculate ETA if visit is en_route
    eta_minutes = None
    if visit.status == VisitStatus.EN_ROUTE and route:
        try:
            eta_calculator = ETACalculator(db)
            eta_data = await eta_calculator.calculate_eta(route.vehicle_id, visit.id)
            eta_minutes = eta_data.get("eta_minutes")
        except Exception as e:
            logger.warning(f"Failed to calculate ETA for visit {visit.id}: {e}")

    # Build response
    visit_data = VisitInMyVisit(
        id=visit.id,
        route_id=visit.route_id,
        case_id=visit.case_id,
        sequence_number=visit.sequence_number,
        status=visit.status.value,
        estimated_arrival_time=visit.estimated_arrival_time.isoformat() if visit.estimated_arrival_time else None,
        actual_arrival_time=visit.actual_arrival_time.isoformat() if visit.actual_arrival_time else None,
        actual_start_time=None,  # This field doesn't exist in the model
        actual_end_time=visit.actual_departure_time.isoformat() if visit.actual_departure_time else None,
        notes=visit.notes,
        created_at=visit.created_at.isoformat(),
        updated_at=visit.updated_at.isoformat(),
        case=CaseInVisit(
            id=visit.case.id,
            patient_id=visit.case.patient_id,
            care_type_id=visit.case.care_type_id,
            priority=visit.case.priority.value,
            status=visit.case.status.value,
            scheduled_date=visit.case.scheduled_date.isoformat() if visit.case.scheduled_date else None,
            time_window_start=visit.case.time_window_start.strftime("%H:%M") if visit.case.time_window_start else None,
            time_window_end=visit.case.time_window_end.strftime("%H:%M") if visit.case.time_window_end else None,
            special_notes=visit.case.notes,
            patient=PatientInVisit(
                id=visit.case.patient.id,
                name=visit.case.patient.name,
                phone=visit.case.patient.phone
            ),
            care_type=CareTypeInVisit(
                id=visit.case.care_type.id,
                name=visit.case.care_type.name,
                duration_minutes=visit.case.care_type.estimated_duration_minutes
            )
        )
    )

    route_data = None
    if route:
        route_data = RouteInVisit(
            id=route.id,
            vehicle=VehicleInVisit(
                id=route.vehicle.id,
                identifier=route.vehicle.identifier
            ),
            personnel=[
                PersonnelInVisit(
                    id=p.id,
                    name=p.name,
                    skills=[skill.name for skill in p.skills]
                )
                for p in route.assigned_personnel
            ]
        )

    return MyVisitResponse(
        visit=visit_data,
        route=route_data,
        eta_minutes=eta_minutes
    )


@router.get("/{visit_id}", response_model=VisitInMyVisit)
async def get_visit(
    visit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get visit details with full case, patient, and care type information.

    **Permissions:** All authenticated users
    """
    from sqlalchemy.orm import joinedload
    from app.models.case import Case, CareType
    from app.models.patient import Patient

    # Load visit with all related data
    visit = (
        db.query(Visit)
        .options(
            joinedload(Visit.case).joinedload(Case.patient),
            joinedload(Visit.case).joinedload(Case.care_type)
        )
        .filter(Visit.id == visit_id)
        .first()
    )

    if not visit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")

    # Build the response
    # Convert PostGIS location to lat/lon
    from geoalchemy2.shape import to_shape
    location = None
    if visit.case.location:
        point = to_shape(visit.case.location)
        location = LocationInVisit(latitude=point.y, longitude=point.x)

    case_data = CaseInVisit(
        id=visit.case.id,
        patient_id=visit.case.patient_id,
        care_type_id=visit.case.care_type_id,
        priority=visit.case.priority.value if hasattr(visit.case.priority, 'value') else str(visit.case.priority),
        status=visit.case.status.value if hasattr(visit.case.status, 'value') else str(visit.case.status),
        scheduled_date=visit.case.scheduled_date.isoformat() if visit.case.scheduled_date else None,
        time_window_start=visit.case.time_window_start.strftime("%H:%M") if visit.case.time_window_start else None,
        time_window_end=visit.case.time_window_end.strftime("%H:%M") if visit.case.time_window_end else None,
        special_notes=visit.case.notes,
        location=location,
        patient=PatientInVisit(
            id=visit.case.patient.id,
            name=visit.case.patient.name,
            phone=visit.case.patient.phone
        ),
        care_type=CareTypeInVisit(
            id=visit.case.care_type.id,
            name=visit.case.care_type.name,
            duration_minutes=visit.case.care_type.estimated_duration_minutes
        )
    )

    return VisitInMyVisit(
        id=visit.id,
        route_id=visit.route_id,
        case_id=visit.case_id,
        sequence_number=visit.sequence_number,
        status=visit.status.value if hasattr(visit.status, 'value') else str(visit.status),
        estimated_arrival_time=visit.estimated_arrival_time.isoformat() if visit.estimated_arrival_time else None,
        actual_arrival_time=visit.actual_arrival_time.isoformat() if visit.actual_arrival_time else None,
        actual_start_time=None,  # Not tracked in current model
        actual_end_time=visit.actual_departure_time.isoformat() if visit.actual_departure_time else None,
        notes=visit.notes,
        created_at=visit.created_at.isoformat(),
        updated_at=visit.updated_at.isoformat(),
        case=case_data
    )


@router.get("/route/{route_id}/visits", response_model=List[VisitStatusResponse])
async def get_route_visits(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all visits for a route.

    **Permissions:** All authenticated users
    """
    route_tracker = RouteTrackerService(db)

    try:
        route = route_tracker.get_route_by_id(route_id)
        visits = route.visits

        return [
            VisitStatusResponse(
                id=visit.id,
                route_id=visit.route_id,
                case_id=visit.case_id,
                sequence_number=visit.sequence_number,
                status=visit.status.value,
                estimated_arrival_time=visit.estimated_arrival_time,
                estimated_departure_time=visit.estimated_departure_time,
                actual_arrival_time=visit.actual_arrival_time,
                actual_departure_time=visit.actual_departure_time,
                notes=visit.notes
            )
            for visit in visits
        ]
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/route/{route_id}/current", response_model=VisitStatusResponse)
async def get_current_visit(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the currently active visit for a route (EN_ROUTE, ARRIVED, or IN_PROGRESS).

    **Permissions:** All authenticated users
    """
    route_tracker = RouteTrackerService(db)
    current_visit = route_tracker.get_current_visit(route_id)

    if not current_visit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active visit found for this route"
        )

    return VisitStatusResponse(
        id=current_visit.id,
        route_id=current_visit.route_id,
        case_id=current_visit.case_id,
        sequence_number=current_visit.sequence_number,
        status=current_visit.status.value,
        estimated_arrival_time=current_visit.estimated_arrival_time,
        estimated_departure_time=current_visit.estimated_departure_time,
        actual_arrival_time=current_visit.actual_arrival_time,
        actual_departure_time=current_visit.actual_departure_time,
        notes=current_visit.notes
    )


@router.get("/route/{route_id}/next", response_model=VisitStatusResponse)
async def get_next_visit(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the next pending visit for a route.

    **Permissions:** All authenticated users
    """
    route_tracker = RouteTrackerService(db)
    next_visit = route_tracker.get_next_pending_visit(route_id)

    if not next_visit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending visits for this route"
        )

    return VisitStatusResponse(
        id=next_visit.id,
        route_id=next_visit.route_id,
        case_id=next_visit.case_id,
        sequence_number=next_visit.sequence_number,
        status=next_visit.status.value,
        estimated_arrival_time=next_visit.estimated_arrival_time,
        estimated_departure_time=next_visit.estimated_departure_time,
        actual_arrival_time=next_visit.actual_arrival_time,
        actual_departure_time=next_visit.actual_departure_time,
        notes=next_visit.notes
    )


@router.get("/{visit_id}/team")
async def get_visit_team(
    visit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get clinical team information for a visit.

    Returns details about the vehicle and personnel assigned to the route
    containing this visit. Used by patient mobile app to show "who is coming".

    **Permissions:** All authenticated users

    **Returns:** Vehicle and personnel information for the visit's route
    """
    from app.models.route import Route
    from app.models.vehicle import Vehicle

    # Get visit
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visit not found"
        )

    # Get route with vehicle and personnel
    route = (
        db.query(Route)
        .filter(Route.id == visit.route_id)
        .first()
    )

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found for this visit"
        )

    # Build team response
    team_members = []
    for person in route.assigned_personnel:
        team_members.append({
            "id": person.id,
            "name": person.name,
            "phone": person.phone,
            "skills": [skill.name for skill in person.skills]
        })

    vehicle_info = None
    if route.vehicle:
        vehicle_info = {
            "id": route.vehicle.id,
            "identifier": route.vehicle.identifier,
            "type": route.vehicle.vehicle_type
        }

    return {
        "visit_id": visit_id,
        "route_id": route.id,
        "route_date": route.route_date.isoformat(),
        "vehicle": vehicle_info,
        "team_members": team_members
    }
