"""
Case API Endpoints
"""

from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin_or_clinical
from app.models.user import User
from app.schemas.case import (
    CaseCreate,
    CaseUpdate,
    CaseResponse,
    CaseListResponse,
    CaseStatus,
    CasePriority
)
from app.schemas.common import MessageResponse
from app.services.case_service import CaseService

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    case_in: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Create new case

    Requires: Admin or Clinical Team role
    """
    service = CaseService(db)
    case = service.create_case(case_in, user_id=current_user.id)
    return CaseResponse.from_orm_with_location(case)


@router.get("", response_model=CaseListResponse)
def get_cases(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    scheduled_date: Optional[date] = Query(None, description="Filter by scheduled date"),
    status: Optional[CaseStatus] = Query(None, description="Filter by status"),
    patient_id: Optional[int] = Query(None, description="Filter by patient ID"),
    priority: Optional[CasePriority] = Query(None, description="Filter by priority"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Get cases list with pagination and filters

    Requires: Admin or Clinical Team role
    """
    service = CaseService(db)
    cases = service.get_cases(
        skip=skip,
        limit=limit,
        scheduled_date=scheduled_date,
        status=status,
        patient_id=patient_id,
        priority=priority
    )
    total = service.count_cases(scheduled_date=scheduled_date, status=status)

    # Convert ORM models to Pydantic schemas
    case_responses = [CaseResponse.from_orm_with_location(c) for c in cases]

    return CaseListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=case_responses
    )


@router.get("/pending/{scheduled_date}", response_model=CaseListResponse)
def get_pending_cases_by_date(
    scheduled_date: date,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Get pending cases for a specific date

    Useful for route planning

    Requires: Admin or Clinical Team role
    """
    service = CaseService(db)
    cases = service.get_pending_cases_by_date(scheduled_date, skip=skip, limit=limit)
    total = service.count_cases(scheduled_date=scheduled_date, status=CaseStatus.PENDING)

    # Convert ORM models to Pydantic schemas
    case_responses = [CaseResponse.from_orm_with_location(c) for c in cases]

    return CaseListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=case_responses
    )


@router.get("/my-cases", response_model=CaseListResponse)
def get_my_cases(
    status: Optional[CaseStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get cases for current patient.

    Returns all cases for the patient associated with the current user.
    This endpoint is used by the mobile app for patient profile.

    Args:
        status: Optional status filter
        skip: Number of records to skip
        limit: Maximum number of records
        db: Database session
        current_user: Current authenticated user

    Returns:
        CaseListResponse with cases for the current patient

    Raises:
        HTTPException 404: If user has no patient record
    """
    from fastapi import HTTPException
    from app.models.patient import Patient

    # Get patient record for current user
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No patient record found for current user"
        )

    # Get cases for this patient
    service = CaseService(db)
    cases = service.get_cases(
        skip=skip,
        limit=limit,
        patient_id=patient.id,
        status=status
    )
    total = service.count_cases(patient_id=patient.id, status=status)

    # Convert ORM models to Pydantic schemas
    case_responses = [CaseResponse.from_orm_with_location(c) for c in cases]

    return CaseListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=case_responses
    )


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Get case by ID

    Requires: Admin or Clinical Team role
    """
    service = CaseService(db)
    case = service.get_case(case_id)
    return CaseResponse.from_orm_with_location(case)


@router.put("/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: int,
    case_in: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Update case

    Requires: Admin or Clinical Team role
    """
    service = CaseService(db)
    case = service.update_case(case_id, case_in, user_id=current_user.id)
    return CaseResponse.from_orm_with_location(case)


@router.delete("/{case_id}", response_model=MessageResponse)
def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Delete case

    Requires: Admin or Clinical Team role

    Note: Cannot delete cases with status 'assigned' or 'completed'
    """
    service = CaseService(db)
    service.delete_case(case_id, user_id=current_user.id)
    return MessageResponse(message=f"Case {case_id} deleted successfully")
