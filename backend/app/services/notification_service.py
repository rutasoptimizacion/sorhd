"""
Notification Service

Handles push notifications and SMS for the application.
Supports multiple providers with fallback mechanisms.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.notification import Notification, NotificationStatus, NotificationType
from app.models.user import User

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Notification delivery channels"""
    PUSH = "push"
    SMS = "sms"
    EMAIL = "email"


@dataclass
class NotificationPayload:
    """Data structure for notification content"""
    title: str
    body: str
    data: Optional[Dict[str, Any]] = None


@dataclass
class NotificationResult:
    """Result of notification delivery attempt"""
    success: bool
    channel: NotificationChannel
    message: Optional[str] = None
    provider_id: Optional[str] = None  # External ID from FCM/APNS/Twilio


# Abstract Provider Interfaces

class PushNotificationProvider(ABC):
    """Abstract interface for push notification providers (FCM, APNS)"""

    @abstractmethod
    async def send(
        self,
        device_token: str,
        payload: NotificationPayload
    ) -> NotificationResult:
        """Send push notification to a device"""
        pass

    @abstractmethod
    async def send_batch(
        self,
        device_tokens: List[str],
        payload: NotificationPayload
    ) -> List[NotificationResult]:
        """Send push notification to multiple devices"""
        pass


class SMSProvider(ABC):
    """Abstract interface for SMS providers"""

    @abstractmethod
    async def send(
        self,
        phone_number: str,
        message: str
    ) -> NotificationResult:
        """Send SMS to a phone number"""
        pass


# Notification Templates

class NotificationTemplates:
    """Spanish language templates for notifications"""

    ROUTE_ASSIGNED = {
        "title": "Ruta Asignada",
        "body": "Se te ha asignado una nueva ruta con {visit_count} visitas para el {date}."
    }

    VEHICLE_EN_ROUTE = {
        "title": "Equipo en Camino",
        "body": "El equipo médico está en camino a tu domicilio. Tiempo estimado de llegada: {eta} minutos."
    }

    ETA_UPDATE = {
        "title": "Actualización de Llegada",
        "body": "Tiempo estimado de llegada actualizado: {eta} minutos."
    }

    VISIT_COMPLETED = {
        "title": "Visita Completada",
        "body": "La visita ha sido completada exitosamente."
    }

    DELAY_ALERT = {
        "title": "Retraso Detectado",
        "body": "El equipo médico se encuentra retrasado. Nuevo tiempo estimado: {eta} minutos."
    }

    VISIT_CANCELLED = {
        "title": "Visita Cancelada",
        "body": "Tu visita programada para {date} a las {time} ha sido cancelada. Razón: {reason}"
    }

    @classmethod
    def format_template(cls, template_name: str, **kwargs) -> NotificationPayload:
        """Format a template with given parameters"""
        template = getattr(cls, template_name)
        return NotificationPayload(
            title=template["title"],
            body=template["body"].format(**kwargs),
            data=kwargs
        )


# Main Notification Service

class NotificationService:
    """
    Main notification service with multi-channel support and fallback.

    Priority order: PUSH → SMS → EMAIL
    """

    def __init__(
        self,
        db: AsyncSession,
        push_provider: Optional[PushNotificationProvider] = None,
        sms_provider: Optional[SMSProvider] = None
    ):
        self.db = db
        self.push_provider = push_provider
        self.sms_provider = sms_provider

    async def send_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        payload: NotificationPayload,
        priority_channel: NotificationChannel = NotificationChannel.PUSH,
        enable_fallback: bool = True
    ) -> Notification:
        """
        Send notification to a user through available channels.

        Args:
            user_id: Target user ID
            notification_type: Type of notification
            payload: Notification content
            priority_channel: Preferred channel (PUSH or SMS)
            enable_fallback: Enable fallback to SMS if push fails

        Returns:
            Notification record
        """
        # Get user details
        user = await self._get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Create notification record
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=payload.title,
            message=payload.body,
            data=payload.data or {},
            status=NotificationStatus.PENDING
        )
        self.db.add(notification)
        await self.db.flush()  # Get notification ID

        result = None

        # Try push notification first if requested and device token exists
        if priority_channel == NotificationChannel.PUSH and user.device_token:
            result = await self._send_push(user.device_token, payload)

            if result and result.success:
                notification.status = NotificationStatus.SENT
                notification.delivery_channel = NotificationChannel.PUSH.value
                notification.provider_message_id = result.provider_id
                notification.sent_at = datetime.utcnow()
                logger.info(f"Push notification sent to user {user_id}")
            else:
                notification.status = NotificationStatus.FAILED
                notification.error_message = result.message if result else "Push provider not available"
                logger.warning(f"Push notification failed for user {user_id}: {notification.error_message}")

        # Fallback to SMS if push failed and SMS is available
        if (enable_fallback and
            (not result or not result.success) and
            user.phone_number and
            self.sms_provider):

            sms_message = f"{payload.title}: {payload.body}"
            result = await self._send_sms(user.phone_number, sms_message)

            if result and result.success:
                notification.status = NotificationStatus.SENT
                notification.delivery_channel = NotificationChannel.SMS.value
                notification.provider_message_id = result.provider_id
                notification.sent_at = datetime.utcnow()
                logger.info(f"SMS notification sent to user {user_id}")
            else:
                notification.status = NotificationStatus.FAILED
                notification.error_message = result.message if result else "SMS provider not available"
                logger.error(f"SMS notification failed for user {user_id}: {notification.error_message}")

        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def send_bulk_notification(
        self,
        user_ids: List[int],
        notification_type: NotificationType,
        payload: NotificationPayload
    ) -> List[Notification]:
        """Send notification to multiple users"""
        notifications = []
        for user_id in user_ids:
            try:
                notification = await self.send_notification(
                    user_id=user_id,
                    notification_type=notification_type,
                    payload=payload
                )
                notifications.append(notification)
            except Exception as e:
                logger.error(f"Failed to send notification to user {user_id}: {str(e)}")

        return notifications

    async def mark_as_read(self, notification_id: int, user_id: int) -> Optional[Notification]:
        """Mark notification as read"""
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        )
        notification = result.scalar_one_or_none()

        if notification:
            notification.read_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(notification)

        return notification

    async def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """Get notifications for a user"""
        query = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            query = query.where(Notification.read_at.is_(None))

        query = query.order_by(Notification.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def register_device_token(self, user_id: int, device_token: str) -> bool:
        """Register or update device token for push notifications"""
        user = await self._get_user(user_id)
        if not user:
            return False

        user.device_token = device_token
        await self.db.commit()
        logger.info(f"Device token registered for user {user_id}")
        return True

    async def _send_push(
        self,
        device_token: str,
        payload: NotificationPayload
    ) -> Optional[NotificationResult]:
        """Send push notification through provider"""
        if not self.push_provider:
            return None

        try:
            return await self.push_provider.send(device_token, payload)
        except Exception as e:
            logger.error(f"Push notification error: {str(e)}")
            return NotificationResult(
                success=False,
                channel=NotificationChannel.PUSH,
                message=str(e)
            )

    async def _send_sms(
        self,
        phone_number: str,
        message: str
    ) -> Optional[NotificationResult]:
        """Send SMS through provider"""
        if not self.sms_provider:
            return None

        try:
            return await self.sms_provider.send(phone_number, message)
        except Exception as e:
            logger.error(f"SMS error: {str(e)}")
            return NotificationResult(
                success=False,
                channel=NotificationChannel.SMS,
                message=str(e)
            )

    async def _get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()


# Automatic Notification Triggers

class NotificationTriggers:
    """Helper class for triggering automatic notifications"""

    @staticmethod
    async def on_route_assigned(
        service: NotificationService,
        user_id: int,
        visit_count: int,
        date: str
    ):
        """Trigger when route is assigned to personnel"""
        payload = NotificationTemplates.format_template(
            "ROUTE_ASSIGNED",
            visit_count=visit_count,
            date=date
        )

        await service.send_notification(
            user_id=user_id,
            notification_type=NotificationType.ROUTE_ASSIGNED,
            payload=payload
        )

    @staticmethod
    async def on_vehicle_en_route(
        service: NotificationService,
        user_id: int,
        eta_minutes: int
    ):
        """Trigger when vehicle starts heading to patient"""
        payload = NotificationTemplates.format_template(
            "VEHICLE_EN_ROUTE",
            eta=eta_minutes
        )

        await service.send_notification(
            user_id=user_id,
            notification_type=NotificationType.VEHICLE_EN_ROUTE,
            payload=payload
        )

    @staticmethod
    async def on_eta_update(
        service: NotificationService,
        user_id: int,
        eta_minutes: int,
        significant_change: bool = False
    ):
        """Trigger when ETA is updated (only if significant change)"""
        if not significant_change:
            return

        payload = NotificationTemplates.format_template(
            "ETA_UPDATE",
            eta=eta_minutes
        )

        await service.send_notification(
            user_id=user_id,
            notification_type=NotificationType.ETA_UPDATE,
            payload=payload
        )

    @staticmethod
    async def on_delay_detected(
        service: NotificationService,
        user_id: int,
        eta_minutes: int
    ):
        """Trigger when significant delay is detected"""
        payload = NotificationTemplates.format_template(
            "DELAY_ALERT",
            eta=eta_minutes
        )

        await service.send_notification(
            user_id=user_id,
            notification_type=NotificationType.DELAY_ALERT,
            payload=payload,
            enable_fallback=True  # Always enable SMS fallback for delays
        )

    @staticmethod
    async def on_visit_completed(
        service: NotificationService,
        user_id: int
    ):
        """Trigger when visit is completed"""
        payload = NotificationTemplates.format_template("VISIT_COMPLETED")

        await service.send_notification(
            user_id=user_id,
            notification_type=NotificationType.VISIT_COMPLETED,
            payload=payload
        )
