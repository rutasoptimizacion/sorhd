"""
Care Type API Endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin_or_clinical
from app.models.user import User
from app.schemas.care_type import CareTypeCreate, CareTypeUpdate, CareTypeResponse
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services.care_type_service import CareTypeService

router = APIRouter(prefix="/care-types", tags=["care-types"])


@router.post("", response_model=CareTypeResponse, status_code=status.HTTP_201_CREATED)
def create_care_type(
    care_type_in: CareTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Create new care type

    Requires: Admin or Clinical Team role
    """
    service = CareTypeService(db)
    care_type = service.create_care_type(care_type_in, user_id=current_user.id)
    return CareTypeResponse.from_orm_with_skills(care_type)


@router.get("", response_model=PaginatedResponse[CareTypeResponse])
def get_care_types(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get care types list with pagination

    Requires: Any authenticated user
    """
    service = CareTypeService(db)
    care_types = service.get_care_types(skip=skip, limit=limit)
    total = service.count_care_types()

    # Convert SQLAlchemy models to Pydantic schemas with skills
    care_type_responses = [CareTypeResponse.from_orm_with_skills(ct) for ct in care_types]

    return PaginatedResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=care_type_responses
    )


@router.get("/{care_type_id}", response_model=CareTypeResponse)
def get_care_type(
    care_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get care type by ID

    Requires: Any authenticated user
    """
    service = CareTypeService(db)
    care_type = service.get_care_type(care_type_id)
    return CareTypeResponse.from_orm_with_skills(care_type)


@router.put("/{care_type_id}", response_model=CareTypeResponse)
def update_care_type(
    care_type_id: int,
    care_type_in: CareTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Update care type

    Requires: Admin or Clinical Team role
    """
    service = CareTypeService(db)
    care_type = service.update_care_type(care_type_id, care_type_in, user_id=current_user.id)
    return CareTypeResponse.from_orm_with_skills(care_type)


@router.delete("/{care_type_id}", response_model=MessageResponse)
def delete_care_type(
    care_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Delete care type

    Requires: Admin or Clinical Team role
    """
    service = CareTypeService(db)
    service.delete_care_type(care_type_id, user_id=current_user.id)
    return MessageResponse(message=f"Care type {care_type_id} deleted successfully")
