"""
Notification System Configuration

Centralizes notification provider initialization and configuration.
"""
import os
import logging
from typing import Optional

from app.services.notification_service import NotificationService
from app.services.notification_providers import FCMProvider, APNSProvider, TwilioSMSProvider
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class NotificationConfig:
    """
    Notification system configuration and provider initialization.

    Handles lazy initialization of notification providers based on
    available credentials in environment variables.
    """

    _fcm_provider: Optional[FCMProvider] = None
    _apns_provider: Optional[APNSProvider] = None
    _twilio_provider: Optional[TwilioSMSProvider] = None

    @classmethod
    def get_fcm_provider(cls) -> Optional[FCMProvider]:
        """
        Get or create FCM provider instance.

        Requires GOOGLE_APPLICATION_CREDENTIALS environment variable.
        """
        if cls._fcm_provider is not None:
            return cls._fcm_provider

        try:
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if not credentials_path:
                logger.warning(
                    "GOOGLE_APPLICATION_CREDENTIALS not set. "
                    "FCM notifications will not be available."
                )
                return None

            cls._fcm_provider = FCMProvider(credentials_path=credentials_path)
            logger.info("FCM provider initialized successfully")
            return cls._fcm_provider

        except Exception as e:
            logger.error(f"Failed to initialize FCM provider: {e}")
            return None

    @classmethod
    def get_apns_provider(cls) -> Optional[APNSProvider]:
        """
        Get or create APNS provider instance.

        Requires:
        - APNS_TEAM_ID
        - APNS_KEY_ID
        - APNS_KEY_FILE
        - APNS_BUNDLE_ID
        - APNS_USE_SANDBOX (optional, default: false)
        """
        if cls._apns_provider is not None:
            return cls._apns_provider

        try:
            team_id = os.getenv("APNS_TEAM_ID")
            key_id = os.getenv("APNS_KEY_ID")
            key_file = os.getenv("APNS_KEY_FILE")
            bundle_id = os.getenv("APNS_BUNDLE_ID")
            use_sandbox = os.getenv("APNS_USE_SANDBOX", "false").lower() == "true"

            if not all([team_id, key_id, key_file, bundle_id]):
                logger.warning(
                    "APNS credentials not complete. "
                    "APNS notifications will not be available. "
                    "Required: APNS_TEAM_ID, APNS_KEY_ID, APNS_KEY_FILE, APNS_BUNDLE_ID"
                )
                return None

            cls._apns_provider = APNSProvider(
                team_id=team_id,
                key_id=key_id,
                key_file=key_file,
                bundle_id=bundle_id,
                use_sandbox=use_sandbox
            )
            logger.info(
                f"APNS provider initialized successfully "
                f"(sandbox={use_sandbox})"
            )
            return cls._apns_provider

        except Exception as e:
            logger.error(f"Failed to initialize APNS provider: {e}")
            return None

    @classmethod
    def get_twilio_provider(cls) -> Optional[TwilioSMSProvider]:
        """
        Get or create Twilio SMS provider instance.

        Requires:
        - TWILIO_ACCOUNT_SID
        - TWILIO_AUTH_TOKEN
        - TWILIO_FROM_PHONE
        """
        if cls._twilio_provider is not None:
            return cls._twilio_provider

        try:
            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            from_phone = os.getenv("TWILIO_FROM_PHONE")

            if not all([account_sid, auth_token, from_phone]):
                logger.warning(
                    "Twilio credentials not complete. "
                    "SMS notifications will not be available. "
                    "Required: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_PHONE"
                )
                return None

            cls._twilio_provider = TwilioSMSProvider(
                account_sid=account_sid,
                auth_token=auth_token,
                from_phone=from_phone
            )
            logger.info("Twilio SMS provider initialized successfully")
            return cls._twilio_provider

        except Exception as e:
            logger.error(f"Failed to initialize Twilio provider: {e}")
            return None

    @classmethod
    def get_notification_service(cls, db: AsyncSession) -> NotificationService:
        """
        Create NotificationService instance with all available providers.

        Automatically initializes providers based on available credentials.

        Args:
            db: Database session

        Returns:
            NotificationService with configured providers
        """
        # Initialize providers (lazy loading)
        fcm_provider = cls.get_fcm_provider()
        apns_provider = cls.get_apns_provider()
        twilio_provider = cls.get_twilio_provider()

        # Determine which push provider to use
        # Priority: FCM (Android) > APNS (iOS)
        # In production, you might want to select based on user's device OS
        push_provider = fcm_provider or apns_provider

        if push_provider is None:
            logger.warning(
                "No push notification provider available. "
                "Only SMS notifications will work (if Twilio is configured)."
            )

        if twilio_provider is None:
            logger.warning(
                "SMS provider not available. "
                "SMS fallback will not work."
            )

        return NotificationService(
            db=db,
            push_provider=push_provider,
            sms_provider=twilio_provider
        )

    @classmethod
    def reset_providers(cls):
        """
        Reset all provider instances.

        Useful for testing or when credentials change.
        """
        cls._fcm_provider = None
        cls._apns_provider = None
        cls._twilio_provider = None
        logger.info("All notification providers reset")


# Convenience function for dependency injection
def get_notification_service(db: AsyncSession = None) -> NotificationService:
    """
    Dependency injection helper for FastAPI endpoints.

    Usage in endpoint:
    ```python
    @router.post("/send")
    async def send_notification(
        service: NotificationService = Depends(get_notification_service)
    ):
        ...
    ```
    """
    if db is None:
        from app.core.database import get_db
        db = next(get_db())

    return NotificationConfig.get_notification_service(db)
