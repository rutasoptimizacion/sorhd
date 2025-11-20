"""
Route and Visit Models
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum, Date, DateTime, Float, Text
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class RouteStatus(str, enum.Enum):
    """Route status"""
    DRAFT = "draft"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VisitStatus(str, enum.Enum):
    """Visit status"""
    PENDING = "pending"
    EN_ROUTE = "en_route"
    ARRIVED = "arrived"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class Route(BaseModel):
    """Route model - represents optimized daily routes"""
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    route_date = Column(Date, nullable=False)
    status = Column(SQLEnum(RouteStatus, values_callable=lambda x: [e.value for e in x]), default=RouteStatus.DRAFT, nullable=False)
    total_distance_km = Column(Float, nullable=True)
    total_duration_minutes = Column(Float, nullable=True)
    optimization_metadata = Column(Text, nullable=True)  # JSON string with optimization details

    # Relationships
    vehicle = relationship("Vehicle", back_populates="routes")
    assigned_personnel = relationship("Personnel", secondary="route_personnel", back_populates="routes")
    visits = relationship("Visit", back_populates="route", order_by="Visit.sequence_number")
    optimization_metrics = relationship("OptimizationMetrics", back_populates="route", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Route(id={self.id}, vehicle_id={self.vehicle_id}, date={self.route_date}, status={self.status})>"


class RoutePersonnel(BaseModel):
    """Many-to-many relationship between Route and Personnel"""
    __tablename__ = "route_personnel"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    personnel_id = Column(Integer, ForeignKey("personnel.id", ondelete="CASCADE"), nullable=False)

    def __repr__(self):
        return f"<RoutePersonnel(route_id={self.route_id}, personnel_id={self.personnel_id})>"


class Visit(BaseModel):
    """Visit model - individual visit in a route"""
    __tablename__ = "visits"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    estimated_arrival_time = Column(DateTime, nullable=True)
    estimated_departure_time = Column(DateTime, nullable=True)
    actual_arrival_time = Column(DateTime, nullable=True)
    actual_departure_time = Column(DateTime, nullable=True)
    status = Column(SQLEnum(VisitStatus, values_callable=lambda x: [e.value for e in x]), default=VisitStatus.PENDING, nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    route = relationship("Route", back_populates="visits")
    case = relationship("Case", back_populates="visits")

    def __repr__(self):
        return f"<Visit(id={self.id}, route_id={self.route_id}, sequence={self.sequence_number}, status={self.status})>"
