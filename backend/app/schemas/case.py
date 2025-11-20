"""
Pydantic schemas for Case entity
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date, time
from enum import Enum

from app.schemas.common import LocationSchema


class CaseStatus(str, Enum):
    """Case status enum"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CasePriority(str, Enum):
    """Case priority enum"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class CaseBase(BaseModel):
    """Base case schema"""
    patient_id: int = Field(..., description="Patient ID")
    care_type_id: int = Field(..., description="Care type ID")
    scheduled_date: date = Field(..., description="Scheduled visit date")
    priority: CasePriority = Field(CasePriority.MEDIUM, description="Priority level")
    notes: Optional[str] = Field(None, description="Additional notes")


class CaseCreate(CaseBase):
    """Schema for creating a case"""
    location: Optional[LocationSchema] = Field(None, description="Visit location (defaults to patient's home)")
    time_window_start: Optional[time] = Field(None, description="Earliest acceptable visit time")
    time_window_end: Optional[time] = Field(None, description="Latest acceptable visit time")

    @field_validator('time_window_start', 'time_window_end', mode='before')
    @classmethod
    def empty_string_to_none(cls, v):
        """Convert empty strings to None"""
        if v == "" or v is None:
            return None
        return v

    @field_validator('time_window_end')
    @classmethod
    def validate_time_window(cls, v, info):
        """Validate that end time is after start time"""
        if v and info.data.get('time_window_start'):
            if v <= info.data['time_window_start']:
                raise ValueError('time_window_end must be after time_window_start')
        return v


class CaseUpdate(BaseModel):
    """Schema for updating a case"""
    patient_id: Optional[int] = None
    care_type_id: Optional[int] = None
    scheduled_date: Optional[date] = None
    priority: Optional[CasePriority] = None
    notes: Optional[str] = None
    location: Optional[LocationSchema] = None
    time_window_start: Optional[time] = None
    time_window_end: Optional[time] = None
    status: Optional[CaseStatus] = None

    @field_validator('time_window_start', 'time_window_end', mode='before')
    @classmethod
    def empty_string_to_none(cls, v):
        """Convert empty strings to None"""
        if v == "" or v is None:
            return None
        return v

    @field_validator('time_window_end')
    @classmethod
    def validate_time_window(cls, v, info):
        """Validate that end time is after start time"""
        if v and info.data.get('time_window_start'):
            if v <= info.data['time_window_start']:
                raise ValueError('time_window_end must be after time_window_start')
        return v


class CaseResponse(CaseBase):
    """Schema for case response"""
    id: int
    location: LocationSchema
    time_window_start: Optional[time]
    time_window_end: Optional[time]
    status: CaseStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_with_location(cls, case):
        """Create response from ORM model with location and datetime conversions"""
        from geoalchemy2.shape import to_shape

        # Convert PostGIS location to LocationSchema
        point = to_shape(case.location)
        location = LocationSchema(latitude=point.y, longitude=point.x)

        # Convert datetime fields to date and time
        scheduled_date_only = case.scheduled_date.date() if case.scheduled_date else None
        time_window_start_only = case.time_window_start.time() if case.time_window_start else None
        time_window_end_only = case.time_window_end.time() if case.time_window_end else None

        return cls(
            id=case.id,
            patient_id=case.patient_id,
            care_type_id=case.care_type_id,
            scheduled_date=scheduled_date_only,
            priority=case.priority,
            notes=case.notes,
            location=location,
            time_window_start=time_window_start_only,
            time_window_end=time_window_end_only,
            status=case.status,
            created_at=case.created_at,
            updated_at=case.updated_at
        )

    class Config:
        from_attributes = True


class CaseListResponse(BaseModel):
    """Schema for case list with pagination"""
    total: int
    skip: int
    limit: int
    items: List[CaseResponse]
