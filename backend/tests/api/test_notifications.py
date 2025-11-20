"""
Integration Tests for Notification API Endpoints

Tests for notification API endpoints including:
- Device token registration
- Getting user notifications
- Marking notifications as read
- Admin sending notifications
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.models.user import User, UserRole
from app.models.notification import Notification, NotificationStatus, NotificationType


class TestNotificationEndpoints:
    """Test notification API endpoints"""

    @pytest.mark.asyncio
    async def test_register_device_token(
        self,
        client: AsyncClient,
        test_user: User,
        test_token: str
    ):
        """Test device token registration endpoint"""
        response = await client.post(
            "/api/v1/notifications/device-token",
            json={"device_token": "test_fcm_token_123"},
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "registered" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_register_device_token_unauthorized(self, client: AsyncClient):
        """Test device token registration without authentication"""
        response = await client.post(
            "/api/v1/notifications/device-token",
            json={"device_token": "test_token"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_notifications(
        self,
        client: AsyncClient,
        test_user: User,
        test_token: str,
        db_session
    ):
        """Test getting user notifications"""
        # Create test notifications
        notification1 = Notification(
            user_id=test_user.id,
            type=NotificationType.ROUTE_ASSIGNED,
            title="Ruta Asignada",
            message="Se te ha asignado una ruta",
            status=NotificationStatus.SENT
        )
        notification2 = Notification(
            user_id=test_user.id,
            type=NotificationType.ETA_UPDATE,
            title="ETA Actualizado",
            message="Tiempo estimado actualizado",
            status=NotificationStatus.SENT
        )

        db_session.add(notification1)
        db_session.add(notification2)
        await db_session.commit()

        response = await client.get(
            "/api/v1/notifications/",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 2

    @pytest.mark.asyncio
    async def test_get_unread_notifications_only(
        self,
        client: AsyncClient,
        test_user: User,
        test_token: str,
        db_session
    ):
        """Test filtering unread notifications"""
        # Create read and unread notifications
        read_notif = Notification(
            user_id=test_user.id,
            type=NotificationType.ROUTE_ASSIGNED,
            title="Read",
            message="Already read",
            status=NotificationStatus.SENT,
            read_at=datetime.utcnow()
        )
        unread_notif = Notification(
            user_id=test_user.id,
            type=NotificationType.ETA_UPDATE,
            title="Unread",
            message="Not read yet",
            status=NotificationStatus.SENT
        )

        db_session.add(read_notif)
        db_session.add(unread_notif)
        await db_session.commit()

        response = await client.get(
            "/api/v1/notifications/?unread_only=true",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # Should only include unread notifications
        assert all(item["read_at"] is None for item in data["items"])

    @pytest.mark.asyncio
    async def test_mark_notification_read(
        self,
        client: AsyncClient,
        test_user: User,
        test_token: str,
        db_session
    ):
        """Test marking notification as read"""
        notification = Notification(
            user_id=test_user.id,
            type=NotificationType.ROUTE_ASSIGNED,
            title="Test",
            message="Test message",
            status=NotificationStatus.SENT
        )
        db_session.add(notification)
        await db_session.commit()
        await db_session.refresh(notification)

        response = await client.patch(
            f"/api/v1/notifications/{notification.id}/read",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["read_at"] is not None

    @pytest.mark.asyncio
    async def test_mark_notification_read_not_found(
        self,
        client: AsyncClient,
        test_token: str
    ):
        """Test marking non-existent notification as read"""
        response = await client.patch(
            "/api/v1/notifications/99999/read",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_mark_other_user_notification(
        self,
        client: AsyncClient,
        test_user: User,
        test_token: str,
        db_session
    ):
        """Test that user cannot mark another user's notification"""
        # Create notification for different user
        other_user = User(
            username="otheruser",
            email="other@example.com",
            role=UserRole.CLINICAL_TEAM
        )
        db_session.add(other_user)
        await db_session.commit()

        notification = Notification(
            user_id=other_user.id,
            type=NotificationType.ROUTE_ASSIGNED,
            title="Test",
            message="Test message",
            status=NotificationStatus.SENT
        )
        db_session.add(notification)
        await db_session.commit()
        await db_session.refresh(notification)

        response = await client.patch(
            f"/api/v1/notifications/{notification.id}/read",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # Should not find notification (filtered by user_id)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_mark_notifications_batch(
        self,
        client: AsyncClient,
        test_user: User,
        test_token: str,
        db_session
    ):
        """Test marking multiple notifications as read"""
        notifications = []
        for i in range(3):
            notif = Notification(
                user_id=test_user.id,
                type=NotificationType.ROUTE_ASSIGNED,
                title=f"Test {i}",
                message=f"Message {i}",
                status=NotificationStatus.SENT
            )
            db_session.add(notif)
            notifications.append(notif)

        await db_session.commit()
        for notif in notifications:
            await db_session.refresh(notif)

        notification_ids = [n.id for n in notifications]

        response = await client.post(
            "/api/v1/notifications/mark-read-batch",
            json={"notification_ids": notification_ids},
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["marked_count"] == 3

    @pytest.mark.asyncio
    async def test_get_unread_count(
        self,
        client: AsyncClient,
        test_user: User,
        test_token: str,
        db_session
    ):
        """Test getting unread notification count"""
        # Create some unread notifications
        for i in range(5):
            notif = Notification(
                user_id=test_user.id,
                type=NotificationType.ROUTE_ASSIGNED,
                title=f"Test {i}",
                message=f"Message {i}",
                status=NotificationStatus.SENT
            )
            db_session.add(notif)

        await db_session.commit()

        response = await client.get(
            "/api/v1/notifications/unread-count",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["unread_count"] >= 5

    @pytest.mark.asyncio
    async def test_admin_send_notification(
        self,
        client: AsyncClient,
        admin_user: User,
        admin_token: str,
        test_user: User
    ):
        """Test admin sending notification to users"""
        with patch('app.services.notification_service.NotificationService.send_bulk_notification') as mock_send:
            # Mock the service response
            mock_notification = Notification(
                id=1,
                user_id=test_user.id,
                type=NotificationType.ROUTE_ASSIGNED,
                title="Admin Notification",
                message="Test from admin",
                status=NotificationStatus.SENT
            )
            mock_send.return_value = [mock_notification]

            response = await client.post(
                "/api/v1/notifications/send",
                json={
                    "user_ids": [test_user.id],
                    "type": "route_assigned",
                    "title": "Admin Notification",
                    "body": "Test from admin",
                    "data": {"key": "value"}
                },
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_non_admin_cannot_send_notification(
        self,
        client: AsyncClient,
        test_user: User,
        test_token: str
    ):
        """Test that non-admin users cannot send notifications"""
        response = await client.post(
            "/api/v1/notifications/send",
            json={
                "user_ids": [1],
                "type": "route_assigned",
                "title": "Test",
                "body": "Test"
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )

        # Should be forbidden (403) or unauthorized
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_admin_delete_notification(
        self,
        client: AsyncClient,
        admin_user: User,
        admin_token: str,
        db_session
    ):
        """Test admin deleting notification"""
        notification = Notification(
            user_id=admin_user.id,
            type=NotificationType.ROUTE_ASSIGNED,
            title="Test",
            message="To be deleted",
            status=NotificationStatus.SENT
        )
        db_session.add(notification)
        await db_session.commit()
        await db_session.refresh(notification)

        response = await client.delete(
            f"/api/v1/notifications/{notification.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_pagination(
        self,
        client: AsyncClient,
        test_user: User,
        test_token: str,
        db_session
    ):
        """Test notification pagination"""
        # Create 25 notifications
        for i in range(25):
            notif = Notification(
                user_id=test_user.id,
                type=NotificationType.ROUTE_ASSIGNED,
                title=f"Test {i}",
                message=f"Message {i}",
                status=NotificationStatus.SENT
            )
            db_session.add(notif)

        await db_session.commit()

        # Get first page
        response = await client.get(
            "/api/v1/notifications/?limit=10&offset=0",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["limit"] == 10
        assert data["offset"] == 0

        # Get second page
        response = await client.get(
            "/api/v1/notifications/?limit=10&offset=10",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["offset"] == 10


# Fixtures

@pytest.fixture
async def test_user(db_session):
    """Create test user"""
    from datetime import datetime

    user = User(
        username="testuser",
        email="test@example.com",
        role=UserRole.CLINICAL_TEAM,
        hashed_password="hashed_password",
        device_token=None
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(db_session):
    """Create admin user"""
    user = User(
        username="admin",
        email="admin@example.com",
        role=UserRole.ADMIN,
        hashed_password="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def test_token(test_user):
    """Generate test JWT token"""
    from app.core.security import create_access_token

    return create_access_token({"sub": str(test_user.id)})


@pytest.fixture
def admin_token(admin_user):
    """Generate admin JWT token"""
    from app.core.security import create_access_token

    return create_access_token({"sub": str(admin_user.id)})
