"""
Patient Model
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography

from app.models.base import BaseModel


class Patient(BaseModel):
    """Patient model"""
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, unique=True)
    name = Column(String(255), nullable=False)
    rut = Column(String(12), nullable=True, unique=True, index=True)  # Chilean national ID
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(String(500), nullable=True)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    cases = relationship("Case", back_populates="patient")

    def __repr__(self):
        return f"<Patient(id={self.id}, name={self.name})>"
