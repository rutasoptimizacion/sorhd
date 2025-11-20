"""
User Model
"""
from sqlalchemy import Column, Integer, String, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    """User roles"""
    ADMIN = "admin"
    CLINICAL_TEAM = "clinical_team"
    PATIENT = "patient"


class User(BaseModel):
    """User model for authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]), nullable=False, default=UserRole.CLINICAL_TEAM)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Integer, default=1, nullable=False)  # Using Integer for boolean (1=True, 0=False)
    first_login = Column(Integer, default=1, nullable=False)  # 1=needs activation, 0=activated (for mobile app)
    phone_number = Column(String(20), nullable=True)  # E.164 format (+56912345678)
    device_token = Column(String(255), nullable=True)  # FCM/APNS device token

    # Relationships
    # notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
