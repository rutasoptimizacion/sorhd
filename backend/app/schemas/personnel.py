"""
Pydantic schemas for Personnel entity
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import time, datetime

from app.schemas.common import LocationSchema
from app.schemas.skill import SkillResponse


class PersonnelBase(BaseModel):
    """Base personnel schema"""
    name: str = Field(..., min_length=1, max_length=200, description="Personnel full name")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    email: Optional[str] = Field(None, max_length=100, description="Contact email")
    is_active: bool = Field(True, description="Whether personnel is currently active")


class PersonnelCreate(PersonnelBase):
    """Schema for creating personnel"""
    user_id: Optional[int] = Field(None, description="Optional link to User account for mobile app access")
    start_location: Optional[LocationSchema] = Field(None, description="Start location (home/base). Optional - required only when 'Pickup Mode' is enabled (future feature)")
    work_hours_start: time = Field(default=time(8, 0), description="Work start time (default 08:00)")
    work_hours_end: time = Field(default=time(17, 0), description="Work end time (default 17:00)")
    skill_ids: List[int] = Field(default_factory=list, description="List of skill IDs")


class PersonnelUpdate(BaseModel):
    """Schema for updating personnel"""
    user_id: Optional[int] = Field(None, description="Optional link to User account for mobile app access")
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    start_location: Optional[LocationSchema] = None
    work_hours_start: Optional[time] = None
    work_hours_end: Optional[time] = None
    skill_ids: Optional[List[int]] = None


class PersonnelResponse(PersonnelBase):
    """Schema for personnel response (without nested skills - use /personnel/{id}/skills)"""
    id: int
    user_id: Optional[int] = None
    start_location: Optional[LocationSchema] = None
    work_hours_start: time
    work_hours_end: time
    skill_ids: List[int] = []  # List of skill IDs (fetch details via /skills)
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_with_skills(cls, personnel):
        """Create response from ORM model with skills and location conversion"""
        from geoalchemy2.shape import to_shape

        # Extract skill IDs from related skills
        skill_ids = [skill.id for skill in personnel.skills] if personnel.skills else []

        # Convert PostGIS location to LocationSchema (if present)
        location = None
        if personnel.start_location is not None:
            point = to_shape(personnel.start_location)
            location = LocationSchema(latitude=point.y, longitude=point.x)

        return cls(
            id=personnel.id,
            user_id=personnel.user_id,  # Include user_id field
            name=personnel.name,
            phone=personnel.phone,
            email=None,  # Model doesn't have email field
            is_active=personnel.is_active,
            start_location=location,
            work_hours_start=personnel.work_start_time,
            work_hours_end=personnel.work_end_time,
            skill_ids=skill_ids,
            created_at=personnel.created_at,
            updated_at=personnel.updated_at
        )

    class Config:
        from_attributes = True


class PersonnelListResponse(BaseModel):
    """Schema for personnel list with pagination"""
    total: int
    skip: int
    limit: int
    items: List[PersonnelResponse]
