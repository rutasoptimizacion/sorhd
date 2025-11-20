"""
Case and CareType Models
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum, DateTime, Text, Float
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
import enum

from app.models.base import BaseModel


class CaseStatus(str, enum.Enum):
    """Case status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CasePriority(str, enum.Enum):
    """Case priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TimeWindowType(str, enum.Enum):
    """Time window type"""
    AM = "am"  # 08:00-12:00
    PM = "pm"  # 12:00-17:00
    SPECIFIC = "specific"  # Specific time range
    ANYTIME = "anytime"  # Flexible


class CareType(BaseModel):
    """Care type model - defines types of care"""
    __tablename__ = "care_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500), nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=False, default=60)

    # Relationships
    required_skills = relationship("Skill", secondary="care_type_skills", back_populates="care_types")
    cases = relationship("Case", back_populates="care_type")

    def __repr__(self):
        return f"<CareType(id={self.id}, name={self.name})>"


class CareTypeSkill(BaseModel):
    """Many-to-many relationship between CareType and Skills"""
    __tablename__ = "care_type_skills"

    id = Column(Integer, primary_key=True, index=True)
    care_type_id = Column(Integer, ForeignKey("care_types.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)

    def __repr__(self):
        return f"<CareTypeSkill(care_type_id={self.care_type_id}, skill_id={self.skill_id})>"


class Case(BaseModel):
    """Case model - represents a visit request"""
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    care_type_id = Column(Integer, ForeignKey("care_types.id"), nullable=False)
    scheduled_date = Column(DateTime, nullable=False)
    time_window_type = Column(SQLEnum(TimeWindowType, values_callable=lambda x: [e.value for e in x]), default=TimeWindowType.ANYTIME, nullable=False)
    time_window_start = Column(DateTime, nullable=True)
    time_window_end = Column(DateTime, nullable=True)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    priority = Column(SQLEnum(CasePriority, values_callable=lambda x: [e.value for e in x]), default=CasePriority.MEDIUM, nullable=False)
    status = Column(SQLEnum(CaseStatus, values_callable=lambda x: [e.value for e in x]), default=CaseStatus.PENDING, nullable=False)
    notes = Column(Text, nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="cases")
    care_type = relationship("CareType", back_populates="cases")
    visits = relationship("Visit", back_populates="case")

    def __repr__(self):
        return f"<Case(id={self.id}, patient_id={self.patient_id}, status={self.status})>"
