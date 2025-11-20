"""
Personnel and Skill Models
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Time, Boolean
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography

from app.models.base import BaseModel


class Skill(BaseModel):
    """Skill model - defines healthcare skills"""
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500), nullable=True)

    # Relationships
    personnel = relationship("Personnel", secondary="personnel_skills", back_populates="skills")
    care_types = relationship("CareType", secondary="care_type_skills", back_populates="required_skills")

    def __repr__(self):
        return f"<Skill(id={self.id}, name={self.name})>"


class Personnel(BaseModel):
    """Personnel model - healthcare workers"""
    __tablename__ = "personnel"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, unique=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    start_location = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    work_start_time = Column(Time, nullable=False, default="08:00:00")
    work_end_time = Column(Time, nullable=False, default="17:00:00")
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    skills = relationship("Skill", secondary="personnel_skills", back_populates="personnel")
    routes = relationship("Route", secondary="route_personnel", back_populates="assigned_personnel")

    def __repr__(self):
        return f"<Personnel(id={self.id}, name={self.name})>"


class PersonnelSkill(BaseModel):
    """Many-to-many relationship between Personnel and Skills"""
    __tablename__ = "personnel_skills"

    id = Column(Integer, primary_key=True, index=True)
    personnel_id = Column(Integer, ForeignKey("personnel.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)

    def __repr__(self):
        return f"<PersonnelSkill(personnel_id={self.personnel_id}, skill_id={self.skill_id})>"
