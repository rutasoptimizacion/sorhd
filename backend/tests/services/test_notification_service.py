"""
Unit Tests for Notification Service

Tests notification service functionality including:
- Push notification sending
- SMS fallback
- Notification templates
- Device token management
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.notification_service import (
    NotificationService,
    NotificationPayload,
    NotificationResult,
    NotificationChannel,
    NotificationTemplates,
    NotificationTriggers
)
from app.models.notification import Notification, NotificationStatus, NotificationType
from app.models.user import User, UserRole


@pytest.fixture
def mock_db():
    """Mock database session"""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_push_provider():
    """Mock push notification provider"""
    provider = AsyncMock()
    provider.send = AsyncMock()
    provider.send_batch = AsyncMock()
    return provider


@pytest.fixture
def mock_sms_provider():
    """Mock SMS provider"""
    provider = AsyncMock()
    provider.send = AsyncMock()
    return provider


@pytest.fixture
def notification_service(mock_db, mock_push_provider, mock_sms_provider):
    """Create notification service with mocked providers"""
    return NotificationService(
        db=mock_db,
        push_provider=mock_push_provider,
        sms_provider=mock_sms_provider
    )


@pytest.fixture
def mock_user():
    """Create mock user with device token"""
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        phone_number="+56912345678",
        device_token="test_device_token_123",
        role=UserRole.CLINICAL_TEAM
    )
    return user


class TestNotificationService:
    """Test notification service core functionality"""

    @pytest.mark.asyncio
    async def test_send_push_notification_success(
        self,
        notification_service,
        mock_db,
        mock_push_provider,
        mock_user
    ):
        """Test successful push notification sending"""
        # Arrange
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user
        mock_push_provider.send.return_value = NotificationResult(
            success=True,
            channel=NotificationChannel.PUSH,
            provider_id="fcm_message_id_123"
        )

        payload = NotificationPayload(
            title="Test Notification",
            body="This is a test",
            data={"key": "value"}
        )

        # Act
        result = await notification_service.send_notification(
            user_id=1,
            notification_type=NotificationType.ROUTE_ASSIGNED,
            payload=payload
        )

        # Assert
        assert result is not None
        assert result.status == NotificationStatus.SENT
        assert result.delivery_channel == NotificationChannel.PUSH.value
        assert result.provider_message_id == "fcm_message_id_123"
        mock_push_provider.send.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_to_sms_when_push_fails(
        self,
        notification_service,
        mock_db,
        mock_push_provider,
        mock_sms_provider,
        mock_user
    ):
        """Test SMS fallback when push notification fails"""
        # Arrange
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user
        mock_push_provider.send.return_value = NotificationResult(
            success=False,
            channel=NotificationChannel.PUSH,
            message="Device token invalid"
        )
        mock_sms_provider.send.return_value = NotificationResult(
            success=True,
            channel=NotificationChannel.SMS,
            provider_id="twilio_sid_123"
        )

        payload = NotificationPayload(
            title="Test Notification",
            body="This is a test"
        )

        # Act
        result = await notification_service.send_notification(
            user_id=1,
            notification_type=NotificationType.ROUTE_ASSIGNED,
            payload=payload,
            enable_fallback=True
        )

        # Assert
        assert result.status == NotificationStatus.SENT
        assert result.delivery_channel == NotificationChannel.SMS.value
        mock_push_provider.send.assert_called_once()
        mock_sms_provider.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_fallback_when_disabled(
        self,
        notification_service,
        mock_db,
        mock_push_provider,
        mock_sms_provider,
        mock_user
    ):
        """Test that SMS fallback doesn't happen when disabled"""
        # Arrange
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user
        mock_push_provider.send.return_value = NotificationResult(
            success=False,
            channel=NotificationChannel.PUSH,
            message="Device token invalid"
        )

        payload = NotificationPayload(
            title="Test Notification",
            body="This is a test"
        )

        # Act
        result = await notification_service.send_notification(
            user_id=1,
            notification_type=NotificationType.ROUTE_ASSIGNED,
            payload=payload,
            enable_fallback=False  # Disable fallback
        )

        # Assert
        assert result.status == NotificationStatus.FAILED
        mock_sms_provider.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_register_device_token(
        self,
        notification_service,
        mock_db,
        mock_user
    ):
        """Test device token registration"""
        # Arrange
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user
        new_token = "new_device_token_456"

        # Act
        result = await notification_service.register_device_token(
            user_id=1,
            device_token=new_token
        )

        # Assert
        assert result is True
        assert mock_user.device_token == new_token
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_notification_as_read(
        self,
        notification_service,
        mock_db
    ):
        """Test marking notification as read"""
        # Arrange
        notification = Notification(
            id=1,
            user_id=1,
            type=NotificationType.ROUTE_ASSIGNED,
            title="Test",
            message="Test message",
            status=NotificationStatus.SENT
        )
        mock_db.execute.return_value.scalar_one_or_none.return_value = notification

        # Act
        result = await notification_service.mark_as_read(
            notification_id=1,
            user_id=1
        )

        # Assert
        assert result is not None
        assert result.read_at is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_notifications(
        self,
        notification_service,
        mock_db
    ):
        """Test retrieving user notifications"""
        # Arrange
        notifications = [
            Notification(
                id=1,
                user_id=1,
                type=NotificationType.ROUTE_ASSIGNED,
                title="Notification 1",
                message="Message 1",
                status=NotificationStatus.SENT
            ),
            Notification(
                id=2,
                user_id=1,
                type=NotificationType.ETA_UPDATE,
                title="Notification 2",
                message="Message 2",
                status=NotificationStatus.SENT
            )
        ]
        mock_db.execute.return_value.scalars.return_value.all.return_value = notifications

        # Act
        result = await notification_service.get_user_notifications(
            user_id=1,
            limit=50,
            offset=0
        )

        # Assert
        assert len(result) == 2
        assert result[0].title == "Notification 1"
        assert result[1].title == "Notification 2"

    @pytest.mark.asyncio
    async def test_send_bulk_notification(
        self,
        notification_service,
        mock_db,
        mock_push_provider
    ):
        """Test sending notifications to multiple users"""
        # Arrange
        users = [
            User(id=1, username="user1", device_token="token1", role=UserRole.CLINICAL_TEAM),
            User(id=2, username="user2", device_token="token2", role=UserRole.CLINICAL_TEAM),
            User(id=3, username="user3", device_token="token3", role=UserRole.CLINICAL_TEAM)
        ]

        async def mock_get_user(user_id):
            return users[user_id - 1]

        notification_service._get_user = mock_get_user

        mock_push_provider.send.return_value = NotificationResult(
            success=True,
            channel=NotificationChannel.PUSH
        )

        payload = NotificationPayload(
            title="Bulk Notification",
            body="Sent to multiple users"
        )

        # Act
        results = await notification_service.send_bulk_notification(
            user_ids=[1, 2, 3],
            notification_type=NotificationType.ROUTE_ASSIGNED,
            payload=payload
        )

        # Assert
        assert len(results) == 3
        assert all(n.status == NotificationStatus.SENT for n in results)


class TestNotificationTemplates:
    """Test notification templates"""

    def test_route_assigned_template(self):
        """Test route assigned template formatting"""
        payload = NotificationTemplates.format_template(
            "ROUTE_ASSIGNED",
            visit_count=5,
            date="2025-11-15"
        )

        assert payload.title == "Ruta Asignada"
        assert "5" in payload.body
        assert "2025-11-15" in payload.body

    def test_vehicle_en_route_template(self):
        """Test vehicle en route template"""
        payload = NotificationTemplates.format_template(
            "VEHICLE_EN_ROUTE",
            eta=15
        )

        assert payload.title == "Equipo en Camino"
        assert "15" in payload.body

    def test_eta_update_template(self):
        """Test ETA update template"""
        payload = NotificationTemplates.format_template(
            "ETA_UPDATE",
            eta=20
        )

        assert payload.title == "Actualización de Llegada"
        assert "20" in payload.body

    def test_delay_alert_template(self):
        """Test delay alert template"""
        payload = NotificationTemplates.format_template(
            "DELAY_ALERT",
            eta=30
        )

        assert payload.title == "Retraso Detectado"
        assert "30" in payload.body

    def test_visit_completed_template(self):
        """Test visit completed template"""
        payload = NotificationTemplates.format_template(
            "VISIT_COMPLETED"
        )

        assert payload.title == "Visita Completada"
        assert "completada" in payload.body.lower()


class TestNotificationTriggers:
    """Test automatic notification triggers"""

    @pytest.mark.asyncio
    async def test_on_route_assigned_trigger(self, notification_service):
        """Test route assigned trigger"""
        notification_service.send_notification = AsyncMock()

        await NotificationTriggers.on_route_assigned(
            service=notification_service,
            user_id=1,
            visit_count=5,
            date="2025-11-15"
        )

        notification_service.send_notification.assert_called_once()
        call_args = notification_service.send_notification.call_args
        assert call_args.kwargs["user_id"] == 1
        assert call_args.kwargs["notification_type"] == NotificationType.ROUTE_ASSIGNED

    @pytest.mark.asyncio
    async def test_on_vehicle_en_route_trigger(self, notification_service):
        """Test vehicle en route trigger"""
        notification_service.send_notification = AsyncMock()

        await NotificationTriggers.on_vehicle_en_route(
            service=notification_service,
            user_id=1,
            eta_minutes=15
        )

        notification_service.send_notification.assert_called_once()
        call_args = notification_service.send_notification.call_args
        assert call_args.kwargs["notification_type"] == NotificationType.VEHICLE_EN_ROUTE

    @pytest.mark.asyncio
    async def test_on_delay_detected_trigger(self, notification_service):
        """Test delay detected trigger with SMS fallback"""
        notification_service.send_notification = AsyncMock()

        await NotificationTriggers.on_delay_detected(
            service=notification_service,
            user_id=1,
            eta_minutes=45
        )

        notification_service.send_notification.assert_called_once()
        call_args = notification_service.send_notification.call_args
        assert call_args.kwargs["enable_fallback"] is True  # Ensure SMS fallback is enabled

    @pytest.mark.asyncio
    async def test_eta_update_only_on_significant_change(self, notification_service):
        """Test that ETA update only triggers on significant change"""
        notification_service.send_notification = AsyncMock()

        # No significant change
        await NotificationTriggers.on_eta_update(
            service=notification_service,
            user_id=1,
            eta_minutes=15,
            significant_change=False
        )

        # Should not send notification
        notification_service.send_notification.assert_not_called()

        # Significant change
        await NotificationTriggers.on_eta_update(
            service=notification_service,
            user_id=1,
            eta_minutes=15,
            significant_change=True
        )

        # Should send notification
        notification_service.send_notification.assert_called_once()


class TestNotificationChannel:
    """Test notification channel enum"""

    def test_channel_values(self):
        """Test channel enum values"""
        assert NotificationChannel.PUSH.value == "push"
        assert NotificationChannel.SMS.value == "sms"
        assert NotificationChannel.EMAIL.value == "email"


@pytest.mark.asyncio
async def test_user_not_found_error(notification_service, mock_db):
    """Test error handling when user is not found"""
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    payload = NotificationPayload(
        title="Test",
        body="Test message"
    )

    with pytest.raises(ValueError, match="User .* not found"):
        await notification_service.send_notification(
            user_id=999,
            notification_type=NotificationType.ROUTE_ASSIGNED,
            payload=payload
        )
