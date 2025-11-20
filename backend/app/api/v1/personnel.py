"""
Personnel API Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin_or_clinical
from app.models.user import User
from app.schemas.personnel import (
    PersonnelCreate,
    PersonnelUpdate,
    PersonnelResponse,
    PersonnelListResponse
)
from app.schemas.common import MessageResponse
from app.services.personnel_service import PersonnelService

router = APIRouter(prefix="/personnel", tags=["personnel"])


@router.post("", response_model=PersonnelResponse, status_code=status.HTTP_201_CREATED)
def create_personnel(
    personnel_in: PersonnelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Create new personnel

    Requires: Admin or Clinical Team role
    """
    service = PersonnelService(db)
    personnel = service.create_personnel(personnel_in, user_id=current_user.id)
    return PersonnelResponse.from_orm_with_skills(personnel)


@router.get("/me", response_model=PersonnelResponse)
def get_my_personnel_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Get personnel record for current authenticated user

    Requires: Admin or Clinical Team role

    Returns personnel profile with skills for the current user.
    Used by mobile app to get own personnel information.
    """
    service = PersonnelService(db)
    personnel = service.get_personnel_by_user_id(current_user.id)
    return PersonnelResponse.from_orm_with_skills(personnel)


@router.get("", response_model=PersonnelListResponse)
def get_personnel_list(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skill_id: Optional[int] = Query(None, description="Filter by skill ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Get personnel list with pagination and filters

    Requires: Admin or Clinical Team role
    """
    service = PersonnelService(db)
    personnel_list = service.get_personnel_list(
        skip=skip,
        limit=limit,
        is_active=is_active,
        skill_id=skill_id
    )
    total = service.count_personnel(is_active=is_active)

    # Convert ORM models to Pydantic schemas
    personnel_responses = [PersonnelResponse.from_orm_with_skills(p) for p in personnel_list]

    return PersonnelListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=personnel_responses
    )


@router.get("/{personnel_id}", response_model=PersonnelResponse)
def get_personnel(
    personnel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Get personnel by ID

    Requires: Admin or Clinical Team role
    """
    service = PersonnelService(db)
    personnel = service.get_personnel(personnel_id)
    return PersonnelResponse.from_orm_with_skills(personnel)


@router.put("/{personnel_id}", response_model=PersonnelResponse)
def update_personnel(
    personnel_id: int,
    personnel_in: PersonnelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Update personnel

    Requires: Admin or Clinical Team role
    """
    service = PersonnelService(db)
    personnel = service.update_personnel(personnel_id, personnel_in, user_id=current_user.id)
    return PersonnelResponse.from_orm_with_skills(personnel)


@router.delete("/{personnel_id}", response_model=MessageResponse)
def delete_personnel(
    personnel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Delete personnel

    Requires: Admin or Clinical Team role

    Note: Cannot delete personnel in active routes
    """
    service = PersonnelService(db)
    service.delete_personnel(personnel_id, user_id=current_user.id)
    return MessageResponse(message=f"Personnel {personnel_id} deleted successfully")
