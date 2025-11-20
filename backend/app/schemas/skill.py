"""
Pydantic schemas for Skill entity
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class SkillBase(BaseModel):
    """Base skill schema with common attributes"""
    name: str = Field(..., min_length=1, max_length=100, description="Skill name")
    description: Optional[str] = Field(None, max_length=500, description="Skill description")


class SkillCreate(SkillBase):
    """Schema for creating a new skill"""
    pass


class SkillUpdate(BaseModel):
    """Schema for updating a skill"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class SkillResponse(SkillBase):
    """Schema for skill response"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
