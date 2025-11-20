"""
Skill API Endpoints
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin_or_clinical
from app.models.user import User
from typing import List
from app.schemas.skill import SkillCreate, SkillUpdate, SkillResponse
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services.skill_service import SkillService

router = APIRouter(prefix="/skills", tags=["skills"])


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
def create_skill(
    skill_in: SkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Create new skill

    Requires: Admin or Clinical Team role
    """
    service = SkillService(db)
    skill = service.create_skill(skill_in, user_id=current_user.id)
    return SkillResponse.model_validate(skill)


@router.get("", response_model=PaginatedResponse[SkillResponse])
def get_skills(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get skills list with pagination

    Requires: Any authenticated user
    """
    service = SkillService(db)
    skills = service.get_skills(skip=skip, limit=limit)
    total = service.count_skills()

    # Convert SQLAlchemy models to Pydantic schemas
    skill_responses = [SkillResponse.model_validate(skill) for skill in skills]

    return PaginatedResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=skill_responses
    )


@router.get("/{skill_id}", response_model=SkillResponse)
def get_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get skill by ID

    Requires: Any authenticated user
    """
    service = SkillService(db)
    skill = service.get_skill(skill_id)
    return SkillResponse.model_validate(skill)


@router.put("/{skill_id}", response_model=SkillResponse)
def update_skill(
    skill_id: int,
    skill_in: SkillUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Update skill

    Requires: Admin or Clinical Team role
    """
    service = SkillService(db)
    skill = service.update_skill(skill_id, skill_in, user_id=current_user.id)
    return SkillResponse.model_validate(skill)


@router.delete("/{skill_id}", response_model=MessageResponse)
def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Delete skill

    Requires: Admin or Clinical Team role
    """
    service = SkillService(db)
    service.delete_skill(skill_id, user_id=current_user.id)
    return MessageResponse(message=f"Skill {skill_id} deleted successfully")
