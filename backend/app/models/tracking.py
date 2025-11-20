"""
GPS Tracking Model
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float, Index
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from datetime import datetime

from app.models.base import BaseModel


class LocationLog(BaseModel):
    """Location log model - GPS tracking"""
    __tablename__ = "location_logs"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    speed_kmh = Column(Float, nullable=True)
    heading_degrees = Column(Float, nullable=True)
    accuracy_meters = Column(Float, nullable=True)

    # Relationships
    vehicle = relationship("Vehicle")

    # Index for efficient geospatial queries
    __table_args__ = (
        Index('idx_location_logs_vehicle_timestamp', 'vehicle_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<LocationLog(id={self.id}, vehicle_id={self.vehicle_id}, timestamp={self.timestamp})>"
