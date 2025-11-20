"""
Notification Model
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.models.base import BaseModel


class NotificationType(str, enum.Enum):
    """Notification type"""
    ROUTE_ASSIGNED = "route_assigned"
    VEHICLE_EN_ROUTE = "vehicle_en_route"
    ETA_UPDATE = "eta_update"
    VISIT_COMPLETED = "visit_completed"
    DELAY_ALERT = "delay_alert"
    VISIT_CANCELLED = "visit_cancelled"
    GENERAL = "general"


class NotificationChannel(str, enum.Enum):
    """Notification delivery channel"""
    PUSH = "push"
    SMS = "sms"
    EMAIL = "email"


class NotificationStatus(str, enum.Enum):
    """Notification delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class Notification(BaseModel):
    """
    Notification model for push notifications and SMS.

    Stores notification history, delivery status, and provides
    tracking for multi-channel notifications.
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Notification content
    type = Column(
        SQLEnum(NotificationType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSONB, nullable=True, default={})  # Additional data payload

    # Delivery tracking
    status = Column(
        SQLEnum(NotificationStatus, values_callable=lambda x: [e.value for e in x]),
        default=NotificationStatus.PENDING,
        nullable=False,
        index=True
    )
    delivery_channel = Column(String(50), nullable=True)  # push, sms, email
    provider_message_id = Column(String(255), nullable=True)  # FCM/APNS/Twilio ID
    error_message = Column(Text, nullable=True)

    # Timestamps
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True, index=True)

    # Relationships (Phase 6 - back_populates commented out for now)
    user = relationship("User")  # back_populates="notifications" removed temporarily

    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type}, status={self.status})>"

    @property
    def is_read(self) -> bool:
        """Check if notification has been read"""
        return self.read_at is not None

    def mark_as_read(self):
        """Mark notification as read"""
        if self.read_at is None:
            self.read_at = datetime.utcnow()
