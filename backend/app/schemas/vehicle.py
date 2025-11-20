"""
Pydantic schemas for Vehicle entity
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from app.schemas.common import LocationSchema


class VehicleStatus(str, Enum):
    """Vehicle status enum"""
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    UNAVAILABLE = "unavailable"


class VehicleBase(BaseModel):
    """Base vehicle schema"""
    identifier: str = Field(..., min_length=1, max_length=50, description="Vehicle identifier (license plate or code)")
    capacity: int = Field(..., gt=0, description="Maximum capacity (number of personnel)")
    is_active: bool = Field(True, description="Whether vehicle is active")


class VehicleCreate(VehicleBase):
    """Schema for creating a vehicle"""
    base_location: LocationSchema = Field(..., description="Vehicle base location")
    status: VehicleStatus = Field(VehicleStatus.AVAILABLE, description="Current status")
    resources: Optional[List[str]] = Field(default_factory=list, description="Available resources/equipment")


class VehicleUpdate(BaseModel):
    """Schema for updating a vehicle"""
    identifier: Optional[str] = Field(None, min_length=1, max_length=50)
    capacity: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None
    base_location: Optional[LocationSchema] = None
    status: Optional[VehicleStatus] = None
    resources: Optional[List[str]] = None


class VehicleResponse(VehicleBase):
    """Schema for vehicle response"""
    id: int
    base_location: LocationSchema
    status: VehicleStatus
    resources: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_with_location(cls, vehicle):
        """Create response from ORM model with location conversion"""
        from geoalchemy2.shape import to_shape

        # Convert PostGIS location to LocationSchema
        point = to_shape(vehicle.base_location)
        location = LocationSchema(latitude=point.y, longitude=point.x)

        return cls(
            id=vehicle.id,
            identifier=vehicle.identifier,
            capacity=vehicle.capacity_personnel,  # Map from model field
            is_active=vehicle.is_active,
            base_location=location,
            status=vehicle.status,
            resources=vehicle.resources or [],
            created_at=vehicle.created_at,
            updated_at=vehicle.updated_at
        )

    class Config:
        from_attributes = True


class VehicleListResponse(BaseModel):
    """Schema for vehicle list with pagination"""
    total: int
    skip: int
    limit: int
    items: List[VehicleResponse]
