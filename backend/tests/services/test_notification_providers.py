"""
Unit Tests for Notification Providers

Tests for FCM, APNS, and Twilio SMS providers.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock

from app.services.notification_service import (
    NotificationPayload,
    NotificationResult,
    NotificationChannel
)


class TestFCMProvider:
    """Test Firebase Cloud Messaging provider"""

    @pytest.mark.asyncio
    @patch('app.services.notification_providers.fcm_provider.firebase_admin')
    @patch('app.services.notification_providers.fcm_provider.messaging')
    async def test_fcm_send_success(self, mock_messaging, mock_firebase):
        """Test successful FCM notification"""
        from app.services.notification_providers.fcm_provider import FCMProvider

        # Mock Firebase initialization
        mock_firebase._apps = True

        # Mock messaging send
        mock_messaging.send.return_value = "fcm_message_id_123"

        provider = FCMProvider.__new__(FCMProvider)
        provider.initialized = True

        payload = NotificationPayload(
            title="Test Notification",
            body="Test body",
            data={"key": "value"}
        )

        result = await provider.send(
            device_token="test_device_token",
            payload=payload
        )

        assert result.success is True
        assert result.channel == NotificationChannel.PUSH
        assert result.provider_id == "fcm_message_id_123"

    @pytest.mark.asyncio
    @patch('app.services.notification_providers.fcm_provider.firebase_admin')
    @patch('app.services.notification_providers.fcm_provider.messaging')
    async def test_fcm_send_invalid_token(self, mock_messaging, mock_firebase):
        """Test FCM with invalid device token"""
        from app.services.notification_providers.fcm_provider import FCMProvider

        mock_firebase._apps = True

        # Mock UnregisteredError
        mock_messaging.UnregisteredError = Exception
        mock_messaging.send.side_effect = mock_messaging.UnregisteredError("Invalid token")

        provider = FCMProvider.__new__(FCMProvider)
        provider.initialized = True

        payload = NotificationPayload(
            title="Test",
            body="Test"
        )

        result = await provider.send(
            device_token="invalid_token",
            payload=payload
        )

        assert result.success is False
        assert "invalid" in result.message.lower() or "unregistered" in result.message.lower()

    @pytest.mark.asyncio
    @patch('app.services.notification_providers.fcm_provider.firebase_admin')
    @patch('app.services.notification_providers.fcm_provider.messaging')
    async def test_fcm_batch_send(self, mock_messaging, mock_firebase):
        """Test FCM batch sending"""
        from app.services.notification_providers.fcm_provider import FCMProvider

        mock_firebase._apps = True

        # Mock batch response
        batch_response = Mock()
        batch_response.success_count = 2
        batch_response.failure_count = 1
        batch_response.responses = [
            Mock(success=True, message_id="msg1"),
            Mock(success=True, message_id="msg2"),
            Mock(success=False, exception=Exception("Failed"))
        ]

        mock_messaging.send_multicast.return_value = batch_response

        provider = FCMProvider.__new__(FCMProvider)
        provider.initialized = True

        payload = NotificationPayload(
            title="Batch Test",
            body="Test body"
        )

        results = await provider.send_batch(
            device_tokens=["token1", "token2", "token3"],
            payload=payload
        )

        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is True
        assert results[2].success is False


class TestAPNSProvider:
    """Test Apple Push Notification Service provider"""

    @pytest.mark.asyncio
    @patch('app.services.notification_providers.apns_provider.APNs')
    async def test_apns_send_success(self, mock_apns_class):
        """Test successful APNS notification"""
        from app.services.notification_providers.apns_provider import APNSProvider

        # Mock APNs client
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.is_successful = True
        mock_response.notification_id = "apns_id_123"
        mock_client.send_notification.return_value = mock_response

        provider = APNSProvider.__new__(APNSProvider)
        provider.client = mock_client
        provider.team_id = "TEST_TEAM"
        provider.key_id = "TEST_KEY"
        provider.key_file = "test.p8"
        provider.bundle_id = "com.test.app"
        provider.use_sandbox = True

        payload = NotificationPayload(
            title="Test Notification",
            body="Test body"
        )

        result = await provider.send(
            device_token="test_device_token",
            payload=payload
        )

        assert result.success is True
        assert result.channel == NotificationChannel.PUSH
        assert result.provider_id == "apns_id_123"

    @pytest.mark.asyncio
    @patch('app.services.notification_providers.apns_provider.APNs')
    async def test_apns_send_failure(self, mock_apns_class):
        """Test APNS notification failure"""
        from app.services.notification_providers.apns_provider import APNSProvider

        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.is_successful = False
        mock_response.status = "400"
        mock_response.description = "BadDeviceToken"
        mock_client.send_notification.return_value = mock_response

        provider = APNSProvider.__new__(APNSProvider)
        provider.client = mock_client

        payload = NotificationPayload(
            title="Test",
            body="Test"
        )

        result = await provider.send(
            device_token="invalid_token",
            payload=payload
        )

        assert result.success is False
        assert "400" in result.message

    @pytest.mark.asyncio
    @patch('app.services.notification_providers.apns_provider.APNs')
    async def test_apns_batch_send(self, mock_apns_class):
        """Test APNS batch sending (concurrent)"""
        from app.services.notification_providers.apns_provider import APNSProvider

        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.is_successful = True
        mock_response.notification_id = "apns_batch_id"
        mock_client.send_notification.return_value = mock_response

        provider = APNSProvider.__new__(APNSProvider)
        provider.client = mock_client

        payload = NotificationPayload(
            title="Batch Test",
            body="Test body"
        )

        results = await provider.send_batch(
            device_tokens=["token1", "token2", "token3"],
            payload=payload
        )

        assert len(results) == 3
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    @patch('app.services.notification_providers.apns_provider.APNs')
    async def test_apns_silent_notification(self, mock_apns_class):
        """Test APNS silent (background) notification"""
        from app.services.notification_providers.apns_provider import APNSProvider

        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.is_successful = True
        mock_response.notification_id = "silent_id"
        mock_client.send_notification.return_value = mock_response

        provider = APNSProvider.__new__(APNSProvider)
        provider.client = mock_client

        result = await provider.send_silent(
            device_token="test_token",
            data={"background_task": "update_routes"}
        )

        assert result.success is True
        mock_client.send_notification.assert_called_once()


class TestTwilioSMSProvider:
    """Test Twilio SMS provider"""

    @pytest.mark.asyncio
    @patch('app.services.notification_providers.twilio_provider.Client')
    async def test_twilio_send_success(self, mock_client_class):
        """Test successful SMS sending"""
        from app.services.notification_providers.twilio_provider import TwilioSMSProvider

        # Mock Twilio client
        mock_client = Mock()
        mock_message = Mock()
        mock_message.sid = "twilio_sid_123"
        mock_message.status = "sent"
        mock_client.messages.create.return_value = mock_message
        mock_client_class.return_value = mock_client

        provider = TwilioSMSProvider(
            account_sid="test_sid",
            auth_token="test_token",
            from_phone="+56912345678"
        )
        provider.client = mock_client

        result = await provider.send(
            phone_number="+56987654321",
            message="Test SMS message"
        )

        assert result.success is True
        assert result.channel == NotificationChannel.SMS
        assert result.provider_id == "twilio_sid_123"

    @pytest.mark.asyncio
    @patch('app.services.notification_providers.twilio_provider.Client')
    async def test_twilio_send_invalid_phone(self, mock_client_class):
        """Test SMS with invalid phone number"""
        from app.services.notification_providers.twilio_provider import TwilioSMSProvider

        provider = TwilioSMSProvider(
            account_sid="test_sid",
            auth_token="test_token",
            from_phone="+56912345678"
        )

        # Invalid phone format (no country code, too short, etc.)
        result = await provider.send(
            phone_number="123",
            message="Test message"
        )

        assert result.success is False
        assert "invalid" in result.message.lower()

    def test_phone_number_validation(self):
        """Test phone number format validation"""
        from app.services.notification_providers.twilio_provider import TwilioSMSProvider

        # Valid E.164 format
        assert TwilioSMSProvider._validate_phone_format("+56912345678") is True
        assert TwilioSMSProvider._validate_phone_format("+12025551234") is True

        # Invalid formats
        assert TwilioSMSProvider._validate_phone_format("912345678") is False
        assert TwilioSMSProvider._validate_phone_format("+56 9 1234 5678") is False
        assert TwilioSMSProvider._validate_phone_format("56912345678") is False

    def test_phone_number_normalization(self):
        """Test phone number normalization"""
        from app.services.notification_providers.twilio_provider import TwilioSMSProvider

        # Already normalized
        assert TwilioSMSProvider.normalize_phone_number("+56912345678") == "+56912345678"

        # Without country code (Chile default)
        assert TwilioSMSProvider.normalize_phone_number("912345678") == "+56912345678"

        # With spaces
        result = TwilioSMSProvider.normalize_phone_number("+56 9 1234 5678")
        assert " " not in result

        # With country code but no +
        assert TwilioSMSProvider.normalize_phone_number("56912345678") == "+56912345678"

    @pytest.mark.asyncio
    @patch('app.services.notification_providers.twilio_provider.Client')
    async def test_twilio_message_truncation(self, mock_client_class):
        """Test that long messages are truncated"""
        from app.services.notification_providers.twilio_provider import TwilioSMSProvider

        mock_client = Mock()
        mock_message = Mock()
        mock_message.sid = "sid"
        mock_message.status = "sent"
        mock_client.messages.create.return_value = mock_message
        mock_client_class.return_value = mock_client

        provider = TwilioSMSProvider(
            account_sid="test_sid",
            auth_token="test_token",
            from_phone="+56912345678"
        )
        provider.client = mock_client

        # Message longer than 1600 chars
        long_message = "x" * 2000

        result = await provider.send(
            phone_number="+56987654321",
            message=long_message
        )

        # Check that message was truncated
        call_args = mock_client.messages.create.call_args
        sent_message = call_args.kwargs["body"]
        assert len(sent_message) <= 1600

    @pytest.mark.asyncio
    @patch('app.services.notification_providers.twilio_provider.Client')
    async def test_twilio_bulk_send(self, mock_client_class):
        """Test bulk SMS sending"""
        from app.services.notification_providers.twilio_provider import TwilioSMSProvider

        mock_client = Mock()
        mock_message = Mock()
        mock_message.sid = "sid"
        mock_message.status = "sent"
        mock_client.messages.create.return_value = mock_message
        mock_client_class.return_value = mock_client

        provider = TwilioSMSProvider(
            account_sid="test_sid",
            auth_token="test_token",
            from_phone="+56912345678"
        )
        provider.client = mock_client

        results = await provider.send_bulk(
            phone_numbers=["+56987654321", "+56987654322", "+56987654323"],
            message="Bulk SMS test"
        )

        assert len(results) == 3
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    @patch('app.services.notification_providers.twilio_provider.Client')
    async def test_twilio_get_message_status(self, mock_client_class):
        """Test fetching message delivery status"""
        from app.services.notification_providers.twilio_provider import TwilioSMSProvider
        from datetime import datetime

        mock_client = Mock()
        mock_message = Mock()
        mock_message.sid = "sid123"
        mock_message.status = "delivered"
        mock_message.error_code = None
        mock_message.error_message = None
        mock_message.date_sent = datetime(2025, 11, 15, 10, 30)
        mock_message.date_updated = datetime(2025, 11, 15, 10, 31)
        mock_message.price = "-0.0075"
        mock_message.price_unit = "USD"

        mock_client.messages.return_value.fetch.return_value = mock_message
        mock_client_class.return_value = mock_client

        provider = TwilioSMSProvider(
            account_sid="test_sid",
            auth_token="test_token",
            from_phone="+56912345678"
        )
        provider.client = mock_client

        status = await provider.get_message_status("sid123")

        assert status is not None
        assert status["sid"] == "sid123"
        assert status["status"] == "delivered"
        assert status["error_code"] is None
