"""
Pydantic schemas for CareType entity
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_serializer
from datetime import datetime


class CareTypeBase(BaseModel):
    """Base care type schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Care type name")
    description: Optional[str] = Field(None, max_length=500, description="Description")
    estimated_duration: int = Field(..., gt=0, description="Estimated duration in minutes")


class CareTypeCreate(CareTypeBase):
    """Schema for creating a care type"""
    required_skill_ids: List[int] = Field(default_factory=list, description="List of required skill IDs")


class CareTypeUpdate(BaseModel):
    """Schema for updating a care type"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    estimated_duration: Optional[int] = Field(None, gt=0)
    required_skill_ids: Optional[List[int]] = None


class CareTypeResponse(BaseModel):
    """Schema for care type response"""
    id: int
    name: str
    description: Optional[str] = None
    estimated_duration: int = Field(alias="estimated_duration_minutes", serialization_alias="estimated_duration")
    required_skill_ids: List[int] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_with_skills(cls, care_type):
        """Create response from ORM model with skills"""
        # Extract skill IDs from related skills
        skill_ids = [skill.id for skill in care_type.required_skills] if care_type.required_skills else []

        return cls(
            id=care_type.id,
            name=care_type.name,
            description=care_type.description,
            estimated_duration=care_type.estimated_duration_minutes,
            required_skill_ids=skill_ids,
            created_at=care_type.created_at,
            updated_at=care_type.updated_at
        )

    class Config:
        from_attributes = True
        populate_by_name = True
