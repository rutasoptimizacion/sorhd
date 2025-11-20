"""
Audit Log Model
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.models.base import BaseModel


class AuditAction(str, enum.Enum):
    """Audit action types"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    OPTIMIZE = "optimize"
    STATUS_CHANGE = "status_change"


class AuditLog(BaseModel):
    """Audit log model - tracks all important actions"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(SQLEnum(AuditAction, values_callable=lambda x: [e.value for e in x]), nullable=False)
    entity_type = Column(String(100), nullable=False)  # e.g., "personnel", "route", "case"
    entity_id = Column(Integer, nullable=True)
    changes = Column(Text, nullable=True)  # JSON string with before/after values
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, entity={self.entity_type})>"
