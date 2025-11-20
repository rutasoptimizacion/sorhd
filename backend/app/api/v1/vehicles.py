"""
Vehicle API Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin_or_clinical
from app.models.user import User
from app.schemas.vehicle import (
    VehicleCreate,
    VehicleUpdate,
    VehicleResponse,
    VehicleListResponse,
    VehicleStatus
)
from app.schemas.common import MessageResponse
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    vehicle_in: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Create new vehicle

    Requires: Admin or Clinical Team role
    """
    service = VehicleService(db)
    vehicle = service.create_vehicle(vehicle_in, user_id=current_user.id)
    return VehicleResponse.from_orm_with_location(vehicle)


@router.get("", response_model=VehicleListResponse)
def get_vehicles(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    status: Optional[VehicleStatus] = Query(None, description="Filter by status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Get vehicles list with pagination and filters

    Requires: Admin or Clinical Team role
    """
    service = VehicleService(db)
    vehicles = service.get_vehicles(
        skip=skip,
        limit=limit,
        status=status,
        is_active=is_active
    )
    total = service.count_vehicles(status=status, is_active=is_active)

    # Convert ORM models to Pydantic schemas
    vehicle_responses = [VehicleResponse.from_orm_with_location(v) for v in vehicles]

    return VehicleListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=vehicle_responses
    )


@router.get("/available", response_model=List[VehicleResponse])
def get_available_vehicles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Get available vehicles (active and not in use)

    Requires: Admin or Clinical Team role
    """
    service = VehicleService(db)
    vehicles = service.get_available_vehicles(skip=skip, limit=limit)
    return [VehicleResponse.from_orm_with_location(v) for v in vehicles]


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Get vehicle by ID

    Requires: Admin or Clinical Team role
    """
    service = VehicleService(db)
    vehicle = service.get_vehicle(vehicle_id)
    return VehicleResponse.from_orm_with_location(vehicle)


@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: int,
    vehicle_in: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Update vehicle

    Requires: Admin or Clinical Team role
    """
    service = VehicleService(db)
    vehicle = service.update_vehicle(vehicle_id, vehicle_in, user_id=current_user.id)
    return VehicleResponse.from_orm_with_location(vehicle)


@router.delete("/{vehicle_id}", response_model=MessageResponse)
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Delete vehicle

    Requires: Admin or Clinical Team role

    Note: Cannot delete vehicle in active routes
    """
    service = VehicleService(db)
    service.delete_vehicle(vehicle_id, user_id=current_user.id)
    return MessageResponse(message=f"Vehicle {vehicle_id} deleted successfully")
