"""
Pydantic schemas for Patient entity
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime, date

from app.schemas.common import LocationSchema
from app.utils.rut_validator import validate_rut, normalize_rut


class PatientBase(BaseModel):
    """Base patient schema"""
    name: str = Field(..., min_length=1, max_length=200, description="Patient full name")
    rut: Optional[str] = Field(None, max_length=12, description="Chilean RUT (Rol Único Tributario)")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    email: Optional[str] = Field(None, max_length=100, description="Contact email")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    medical_notes: Optional[str] = Field(None, description="Medical notes or special instructions")

    @field_validator("rut")
    @classmethod
    def validate_rut_field(cls, value: Optional[str]) -> Optional[str]:
        """Validate and normalize RUT"""
        if value is None or value.strip() == "":
            return None

        # Validate RUT format and check digit
        is_valid, error_message = validate_rut(value)
        if not is_valid:
            raise ValueError(error_message)

        # Return normalized RUT (cleaned format without dots/hyphens)
        from app.utils.rut_validator import clean_rut
        return clean_rut(value)


class PatientCreate(PatientBase):
    """
    Schema for creating a patient

    Two options for specifying location:
    1. Explicit coordinates via 'location' field (existing behavior)
    2. Chilean address via 'address' field (will be geocoded automatically)

    At least one of 'location' or 'address' must be provided.
    If both are provided, 'location' takes precedence.
    """
    user_id: Optional[int] = Field(None, description="Optional link to User account for mobile app access")
    location: Optional[LocationSchema] = Field(None, description="Patient home location (explicit coordinates)")
    address: Optional[str] = Field(None, min_length=5, max_length=500, description="Patient home address (will be geocoded)")

    @model_validator(mode='after')
    def validate_location_or_address(self):
        """Ensure at least location or address is provided"""
        if self.location is None and (self.address is None or self.address.strip() == ""):
            raise ValueError("Debe proporcionar 'location' (coordenadas) o 'address' (dirección)")
        return self


class PatientUpdate(BaseModel):
    """Schema for updating a patient"""
    user_id: Optional[int] = Field(None, description="Optional link to User account for mobile app access")
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    rut: Optional[str] = Field(None, max_length=12, description="Chilean RUT (Rol Único Tributario)")
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    medical_notes: Optional[str] = None
    location: Optional[LocationSchema] = None
    address: Optional[str] = Field(None, min_length=5, max_length=500, description="Patient home address (will be geocoded)")

    @field_validator("rut")
    @classmethod
    def validate_rut_field(cls, value: Optional[str]) -> Optional[str]:
        """Validate and normalize RUT"""
        if value is None or value.strip() == "":
            return None

        # Validate RUT format and check digit
        is_valid, error_message = validate_rut(value)
        if not is_valid:
            raise ValueError(error_message)

        # Return normalized RUT (cleaned format without dots/hyphens)
        from app.utils.rut_validator import clean_rut
        return clean_rut(value)


class PatientResponse(PatientBase):
    """Schema for patient response"""
    id: int
    user_id: Optional[int] = None
    location: LocationSchema
    address: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_with_location(cls, patient):
        """Create response from ORM model with location conversion"""
        from geoalchemy2.shape import to_shape

        # Convert PostGIS location to LocationSchema
        point = to_shape(patient.location)
        location = LocationSchema(latitude=point.y, longitude=point.x)

        return cls(
            id=patient.id,
            user_id=patient.user_id,  # Include user_id field
            name=patient.name,
            rut=patient.rut,  # Include RUT field
            phone=patient.phone,
            email=patient.email,
            date_of_birth=None,  # Model doesn't have this field
            medical_notes=patient.notes,  # Map from model field
            location=location,
            address=patient.address,  # Include address field
            created_at=patient.created_at,
            updated_at=patient.updated_at
        )

    class Config:
        from_attributes = True


class PatientListResponse(BaseModel):
    """Schema for patient list with pagination"""
    total: int
    skip: int
    limit: int
    items: List[PatientResponse]


class GeocodePreviewRequest(BaseModel):
    """Schema for geocoding preview request"""
    address: str = Field(..., min_length=5, max_length=500, description="Address to geocode")
    country: str = Field("CL", max_length=2, description="Country code (default: Chile)")


class GeocodePreviewResponse(BaseModel):
    """Schema for geocoding preview response"""
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    formatted_address: str = Field(..., description="Formatted address returned by geocoding service")
    confidence: Optional[float] = Field(None, description="Confidence score (0.0-1.0)")
    address_components: Optional[dict] = Field(None, description="Detailed address components")
