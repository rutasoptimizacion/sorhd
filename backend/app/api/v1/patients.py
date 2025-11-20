"""
Patient API Endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin_or_clinical
from app.models.user import User
from app.schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientListResponse,
    GeocodePreviewRequest,
    GeocodePreviewResponse
)
from app.schemas.common import MessageResponse
from app.services.patient_service import PatientService
from app.services.geocoding.geocoding_service import GeocodingService

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("/geocode-preview", response_model=GeocodePreviewResponse)
async def geocode_address_preview(
    request: GeocodePreviewRequest,
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Preview geocoding results for an address without saving

    This endpoint geocodes an address and returns the coordinates for
    operator confirmation before creating/updating a patient.

    Requires: Admin or Clinical Team role
    """
    geocoding_service = GeocodingService()

    try:
        result = await geocoding_service.geocode_address(
            address=request.address,
            country=request.country
        )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se pudo geocodificar la dirección. Verifique que sea una dirección válida en Chile."
            )

        return GeocodePreviewResponse(
            latitude=result.latitude,
            longitude=result.longitude,
            formatted_address=result.formatted_address,
            confidence=result.confidence,
            address_components=result.address_components
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al geocodificar dirección: {str(e)}"
        )


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_in: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Create new patient

    Supports two methods for specifying location:
    1. Explicit coordinates: Provide 'location' field with latitude/longitude
    2. Chilean address: Provide 'address' field (will be geocoded automatically)

    RUT field is optional but will be validated if provided.

    Requires: Admin or Clinical Team role
    """
    service = PatientService(db)
    patient = await service.create_patient(patient_in, user_id=current_user.id)
    return PatientResponse.from_orm_with_location(patient)


@router.get("", response_model=PatientListResponse)
def get_patients(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    search: Optional[str] = Query(None, description="Search by name, phone, or email"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Get patients list with pagination and search

    Requires: Admin or Clinical Team role
    """
    service = PatientService(db)

    if search:
        patients = service.search_patients(query=search, skip=skip, limit=limit)
        total = len(patients)  # Approximate for search results
    else:
        patients = service.get_patients(skip=skip, limit=limit)
        total = service.count_patients()

    # Convert ORM models to Pydantic schemas
    patient_responses = [PatientResponse.from_orm_with_location(p) for p in patients]

    return PatientListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=patient_responses
    )


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Get patient by ID

    Requires: Admin or Clinical Team role
    """
    service = PatientService(db)
    patient = service.get_patient(patient_id)
    return PatientResponse.from_orm_with_location(patient)


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    patient_in: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Update patient

    Supports updating location via:
    1. Explicit coordinates: Provide 'location' field with latitude/longitude
    2. Chilean address: Provide 'address' field (will be geocoded automatically)

    RUT field can be updated and will be validated if provided.

    Requires: Admin or Clinical Team role
    """
    service = PatientService(db)
    patient = await service.update_patient(patient_id, patient_in, user_id=current_user.id)
    return PatientResponse.from_orm_with_location(patient)


@router.delete("/{patient_id}", response_model=MessageResponse)
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_clinical)
):
    """
    Delete patient

    Requires: Admin or Clinical Team role
    """
    service = PatientService(db)
    service.delete_patient(patient_id, user_id=current_user.id)
    return MessageResponse(message=f"Patient {patient_id} deleted successfully")
