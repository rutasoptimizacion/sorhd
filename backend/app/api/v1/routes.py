"""
Route API Endpoints
"""
import logging
from typing import List, Optional
from datetime import date as DateType
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.dependencies import get_db, get_current_user
from app.core.exceptions import NotFoundException, ValidationException
from app.models.user import User
from app.models.route import Route, RouteStatus, Visit
from app.models.personnel import Personnel
from app.models.case import Case
from app.schemas.route import (
    OptimizationRequest,
    OptimizationResponse,
    RouteResponse,
    RouteUpdate,
    RouteListResponse,
    VisitResponse,
    RouteWithDetailsResponse
)
from app.services.optimization.service import OptimizationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routes", tags=["routes"])


@router.post("/optimize", response_model=OptimizationResponse, status_code=status.HTTP_200_OK)
async def optimize_routes(
    request: OptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger route optimization.

    This endpoint creates optimized routes for the given cases and vehicles.
    Requires admin role.

    Args:
        request: Optimization request with case IDs, vehicle IDs, and date
        db: Database session
        current_user: Current authenticated user

    Returns:
        OptimizationResponse with routes and optimization details

    Raises:
        HTTPException: If optimization fails or user lacks permissions
    """
    # Check admin permission
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can optimize routes"
        )

    try:
        print(f"⭐ API ENDPOINT CALLED: user={current_user.username}, cases={len(request.case_ids)}, use_heuristic={request.use_heuristic}", flush=True)
        logger.info(f"User {current_user.username} requested route optimization for {len(request.case_ids)} cases")

        # Create optimization service
        optimization_service = OptimizationService(db)

        # Execute optimization
        # Convert date to datetime (at midnight)
        from datetime import datetime, time
        route_datetime = datetime.combine(request.date, time(0, 0))

        result = await optimization_service.optimize_routes(
            case_ids=request.case_ids,
            vehicle_ids=request.vehicle_ids,
            date=route_datetime,
            use_heuristic=request.use_heuristic,
            max_time=request.max_optimization_time
        )

        # Collect route IDs from database
        route_ids = []
        for route in result.routes:
            # Fetch route ID from database
            route_db = db.query(Route).filter(
                Route.vehicle_id == route.vehicle.id,
                Route.route_date == request.date
            ).first()

            if route_db:
                route_ids.append(route_db.id)

        # Collect unassigned case IDs
        unassigned_case_ids = [case.id for case in result.unassigned_cases]

        # Convert constraint violations
        violations = [
            {
                "type": v.type.value,
                "description": v.description,
                "entity_id": v.entity_id,
                "entity_type": v.entity_type,
                "severity": v.severity,
                "details": v.details
            }
            for v in result.constraint_violations
        ]

        logger.info(f"Optimization completed successfully. Created {len(route_ids)} routes: {route_ids}")

        # Convert skill_gap_analysis to schema format
        skill_gap_analysis_schema = None
        if result.skill_gap_analysis:
            from app.schemas.route import SkillGapAnalysisSchema, UnassignedCaseDetailSchema
            skill_gap_analysis_schema = SkillGapAnalysisSchema(
                unassigned_cases_by_skill=result.skill_gap_analysis.unassigned_cases_by_skill,
                unassigned_case_details=[
                    UnassignedCaseDetailSchema(
                        case_id=detail.case_id,
                        case_name=detail.case_name,
                        required_skills=detail.required_skills,
                        missing_skills=detail.missing_skills,
                        priority=detail.priority
                    )
                    for detail in result.skill_gap_analysis.unassigned_case_details
                ],
                most_demanded_skills=[
                    {"skill": skill, "demand_count": count}
                    for skill, count in result.skill_gap_analysis.most_demanded_skills
                ],
                skill_coverage_percentage=result.skill_gap_analysis.skill_coverage_percentage,
                hiring_impact_simulation=result.skill_gap_analysis.hiring_impact_simulation,
                summary={
                    "total_cases_requested": result.skill_gap_analysis.total_cases_requested,
                    "total_cases_assigned": result.skill_gap_analysis.total_cases_assigned,
                    "total_cases_unassigned": result.skill_gap_analysis.total_cases_unassigned,
                    "assignment_rate_percentage": result.skill_gap_analysis.assignment_rate_percentage
                }
            )

        return OptimizationResponse(
            success=result.success,
            message=result.message,
            route_ids=route_ids,
            unassigned_case_ids=unassigned_case_ids,
            constraint_violations=violations,
            optimization_time_seconds=result.optimization_time,
            strategy_used=result.strategy_used,
            total_distance_km=result.total_distance,
            total_time_minutes=result.total_time,
            skill_gap_analysis=skill_gap_analysis_schema
        )

    except Exception as e:
        logger.error(f"Route optimization failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization failed: {str(e)}"
        )


@router.get("", response_model=RouteListResponse)
def list_routes(
    date: Optional[DateType] = Query(None, description="Filter by route date"),
    status_filter: Optional[RouteStatus] = Query(None, alias="status", description="Filter by status"),
    vehicle_id: Optional[int] = Query(None, description="Filter by vehicle ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List routes with pagination and filtering.

    Args:
        date: Optional date filter
        status_filter: Optional status filter
        vehicle_id: Optional vehicle ID filter
        page: Page number (1-indexed)
        page_size: Number of items per page
        db: Database session
        current_user: Current authenticated user

    Returns:
        RouteListResponse with paginated routes
    """
    # Build query
    query = db.query(Route)

    # Apply filters
    if date:
        query = query.filter(Route.route_date == date)
    if status_filter:
        query = query.filter(Route.status == status_filter)
    if vehicle_id:
        query = query.filter(Route.vehicle_id == vehicle_id)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    routes = query.offset(offset).limit(page_size).all()

    # Calculate total pages
    pages = (total + page_size - 1) // page_size

    return RouteListResponse(
        items=[RouteResponse.model_validate(route) for route in routes],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )



@router.get("/my-routes", response_model=List[RouteWithDetailsResponse])
def get_my_routes(
    date: Optional[DateType] = Query(None, description="Filter by route date"),
    status_filter: Optional[RouteStatus] = Query(None, alias="status", description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get routes assigned to current personnel member.

    Returns routes where the current user's personnel record is assigned.
    This endpoint is used by the mobile app for clinical team members.

    Args:
        date: Optional date filter (format: YYYY-MM-DD)
        status_filter: Optional status filter
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of routes with full details (vehicle, personnel, visits)

    Raises:
        HTTPException 404: If user has no personnel record
    """
    # Get personnel record for current user
    from app.models.route import RoutePersonnel
    from sqlalchemy.orm import joinedload

    personnel = db.query(Personnel).filter(Personnel.user_id == current_user.id).first()
    if not personnel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No personnel record found for current user"
        )

    # Build query: get routes where this personnel is assigned
    # Load all relationships eagerly to avoid lazy loading issues
    from app.models.case import Case as CaseModel
    from app.models.patient import Patient

    query = (
        db.query(Route)
        .join(RoutePersonnel, Route.id == RoutePersonnel.route_id)
        .filter(RoutePersonnel.personnel_id == personnel.id)
        .options(
            joinedload(Route.vehicle),
            joinedload(Route.assigned_personnel).joinedload(Personnel.skills),
            joinedload(Route.visits).joinedload(Visit.case).joinedload(CaseModel.patient),
            joinedload(Route.visits).joinedload(Visit.case).joinedload(CaseModel.care_type)
        )
    )

    # Apply filters
    if date:
        query = query.filter(Route.route_date == date)
    if status_filter:
        query = query.filter(Route.status == status_filter)

    # Order by date descending (most recent first)
    query = query.order_by(Route.route_date.desc())

    routes = query.all()

    # Return routes with full details
    return [RouteWithDetailsResponse.from_orm_with_relationships(route) for route in routes]


@router.get("/active", response_model=List[RouteResponse])
def get_active_routes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all active routes.

    Returns routes with status ACTIVE or IN_PROGRESS.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of active routes
    """
    routes = db.query(Route).filter(
        Route.status.in_([RouteStatus.ACTIVE, RouteStatus.IN_PROGRESS])
    ).all()

    return [RouteResponse.model_validate(route) for route in routes]

@router.get("/{route_id}", response_model=RouteWithDetailsResponse)
def get_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get route details by ID with all nested relationships.

    Args:
        route_id: Route ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        RouteWithDetailsResponse with complete route details including vehicle, personnel, visits, etc.

    Raises:
        HTTPException: If route not found
    """
    from sqlalchemy.orm import joinedload
    from geoalchemy2.shape import to_shape

    # Eager load all relationships
    route = db.query(Route).options(
        joinedload(Route.vehicle),
        joinedload(Route.assigned_personnel).joinedload(Personnel.skills),
        joinedload(Route.visits).joinedload(Visit.case).joinedload(Case.patient),
        joinedload(Route.visits).joinedload(Visit.case).joinedload(Case.care_type)
    ).filter(Route.id == route_id).first()

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route {route_id} not found"
        )

    # Build response manually to handle PostGIS conversion
    from app.schemas.route import (
        RouteWithDetailsResponse, VehicleSimple, PersonnelSimple,
        VisitDetailed, CaseSimple, PatientSimple, CareTypeSimple, LocationResponse
    )

    # Convert vehicle
    vehicle_data = None
    if route.vehicle:
        base_location = None
        if route.vehicle.base_location:
            point = to_shape(route.vehicle.base_location)
            base_location = LocationResponse(latitude=point.y, longitude=point.x)

        vehicle_data = VehicleSimple(
            id=route.vehicle.id,
            identifier=route.vehicle.identifier,
            capacity=route.vehicle.capacity_personnel,
            status=route.vehicle.status,
            resources=route.vehicle.resources or [],
            base_location=base_location
        )

    # Convert personnel
    personnel_data = []
    for person in route.assigned_personnel:
        personnel_data.append(PersonnelSimple(
            id=person.id,
            name=person.name,
            skills=[skill.name for skill in person.skills]
        ))

    # Convert visits with nested case, patient, care_type
    visits_data = []
    for visit in route.visits:
        # Convert case location
        case_location = None
        if visit.case and visit.case.location:
            point = to_shape(visit.case.location)
            case_location = LocationResponse(latitude=point.y, longitude=point.x)

        # Build case data
        case_data = None
        if visit.case:
            patient_data = None
            if visit.case.patient:
                patient_data = PatientSimple(
                    id=visit.case.patient.id,
                    name=visit.case.patient.name,
                    phone=visit.case.patient.phone
                )

            care_type_data = None
            if visit.case.care_type:
                care_type_data = CareTypeSimple(
                    id=visit.case.care_type.id,
                    name=visit.case.care_type.name,
                    estimated_duration_minutes=visit.case.care_type.estimated_duration_minutes
                )

            case_data = CaseSimple(
                id=visit.case.id,
                patient_id=visit.case.patient_id,
                care_type_id=visit.case.care_type_id,
                location=case_location,
                priority=visit.case.priority.value if hasattr(visit.case.priority, 'value') else str(visit.case.priority),
                status=visit.case.status.value if hasattr(visit.case.status, 'value') else str(visit.case.status),
                patient=patient_data,
                care_type=care_type_data
            )

        visit_data = VisitDetailed(
            id=visit.id,
            route_id=visit.route_id,
            case_id=visit.case_id,
            sequence_number=visit.sequence_number,
            estimated_arrival_time=visit.estimated_arrival_time,
            estimated_departure_time=visit.estimated_departure_time,
            actual_arrival_time=visit.actual_arrival_time,
            actual_departure_time=visit.actual_departure_time,
            status=visit.status,
            notes=visit.notes,
            created_at=visit.created_at,
            updated_at=visit.updated_at,
            case=case_data,
            patient=case_data.patient if case_data else None,
            care_type=case_data.care_type if case_data else None
        )
        visits_data.append(visit_data)

    # Build final response
    response = RouteWithDetailsResponse(
        id=route.id,
        vehicle_id=route.vehicle_id,
        route_date=route.route_date,
        status=route.status,
        total_distance_km=route.total_distance_km,
        total_duration_minutes=route.total_duration_minutes,
        optimization_metadata=route.optimization_metadata,
        visit_count=len(route.visits),
        created_at=route.created_at,
        updated_at=route.updated_at,
        vehicle=vehicle_data,
        personnel=personnel_data,
        visits=visits_data
    )

    return response


@router.patch("/{route_id}/status", response_model=RouteResponse)
def update_route_status(
    route_id: int,
    update: RouteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update route status.

    Args:
        route_id: Route ID
        update: Route update with new status
        db: Database session
        current_user: Current authenticated user

    Returns:
        RouteResponse with updated route

    Raises:
        HTTPException: If route not found or user lacks permissions
    """
    # Check admin permission
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update route status"
        )

    route = db.query(Route).filter(Route.id == route_id).first()

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route {route_id} not found"
        )

    # Update status
    if update.status:
        route.status = update.status

    db.commit()
    db.refresh(route)

    logger.info(f"Route {route_id} status updated to {route.status} by {current_user.username}")

    return RouteResponse.model_validate(route)


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel/delete a route.

    Only routes in DRAFT or PLANNED status can be deleted.
    Active or completed routes cannot be deleted.

    Args:
        route_id: Route ID
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: If route not found, cannot be deleted, or user lacks permissions
    """
    # Check admin permission
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete routes"
        )

    route = db.query(Route).filter(Route.id == route_id).first()

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route {route_id} not found"
        )

    # Check if route can be deleted
    if route.status in [RouteStatus.ACTIVE, RouteStatus.IN_PROGRESS, RouteStatus.COMPLETED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete route in {route.status} status. Cancel it first."
        )

    # Mark as cancelled instead of deleting
    route.status = RouteStatus.CANCELLED
    db.commit()

    logger.info(f"Route {route_id} cancelled by {current_user.username}")


