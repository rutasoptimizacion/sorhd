"""
Vehicle Model
"""
from sqlalchemy import Column, Integer, String, Enum as SQLEnum, JSON, Boolean
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
import enum

from app.models.base import BaseModel


class VehicleStatus(str, enum.Enum):
    """Vehicle status"""
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    UNAVAILABLE = "unavailable"


class Vehicle(BaseModel):
    """Vehicle model"""
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(50), unique=True, nullable=False)
    license_plate = Column(String(20), nullable=True)
    capacity_personnel = Column(Integer, nullable=False, default=2)
    base_location = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    status = Column(SQLEnum(VehicleStatus, values_callable=lambda x: [e.value for e in x]), default=VehicleStatus.AVAILABLE, nullable=False)
    resources = Column(JSON, nullable=True)  # JSONB list of medical equipment/resources
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    routes = relationship("Route", back_populates="vehicle")

    def __repr__(self):
        return f"<Vehicle(id={self.id}, identifier={self.identifier}, status={self.status})>"
