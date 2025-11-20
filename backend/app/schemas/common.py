"""
Common Pydantic schemas used across the application
"""

from typing import Optional, List, Any, Generic, TypeVar
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

T = TypeVar('T')


class LocationSchema(BaseModel):
    """Schema for geographic location (WGS 84)"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude (-90 to 90)")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude (-180 to 180)")

    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v


class PaginationParams(BaseModel):
    """Pagination parameters"""
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records to return")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    total: int = Field(..., description="Total number of records")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")
    items: List[T] = Field(..., description="List of records")

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Simple message response"""
    message: str
