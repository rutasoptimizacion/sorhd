"""
Firebase Cloud Messaging (FCM) Provider

Handles push notifications for Android devices.
"""
import logging
from typing import List, Optional
import asyncio

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FCM_AVAILABLE = True
except ImportError:
    FCM_AVAILABLE = False
    logging.warning("firebase-admin not installed. FCM notifications will not work.")

from app.services.notification_service import (
    PushNotificationProvider,
    NotificationPayload,
    NotificationResult,
    NotificationChannel
)

logger = logging.getLogger(__name__)


class FCMProvider(PushNotificationProvider):
    """
    Firebase Cloud Messaging provider for Android push notifications.

    Requires firebase-admin SDK and a service account JSON file.
    """

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize FCM provider.

        Args:
            credentials_path: Path to Firebase service account JSON file.
                            If None, will use GOOGLE_APPLICATION_CREDENTIALS env var.
        """
        if not FCM_AVAILABLE:
            raise ImportError(
                "firebase-admin is required for FCM. "
                "Install with: pip install firebase-admin"
            )

        self.initialized = False
        self._initialize(credentials_path)

    def _initialize(self, credentials_path: Optional[str] = None):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if already initialized
            if firebase_admin._apps:
                self.initialized = True
                logger.info("FCM already initialized")
                return

            # Initialize with credentials
            if credentials_path:
                cred = credentials.Certificate(credentials_path)
                firebase_admin.initialize_app(cred)
            else:
                # Will use GOOGLE_APPLICATION_CREDENTIALS env var
                firebase_admin.initialize_app()

            self.initialized = True
            logger.info("FCM initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize FCM: {str(e)}")
            raise

    async def send(
        self,
        device_token: str,
        payload: NotificationPayload
    ) -> NotificationResult:
        """
        Send push notification to a single device.

        Args:
            device_token: FCM device registration token
            payload: Notification content

        Returns:
            NotificationResult with success status
        """
        if not self.initialized:
            return NotificationResult(
                success=False,
                channel=NotificationChannel.PUSH,
                message="FCM not initialized"
            )

        try:
            # Build FCM message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=payload.title,
                    body=payload.body
                ),
                data=payload.data or {},
                token=device_token,
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        sound="default",
                        channel_id="default"
                    )
                )
            )

            # Send message (blocking call, run in executor)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                messaging.send,
                message
            )

            logger.info(f"FCM notification sent successfully: {response}")

            return NotificationResult(
                success=True,
                channel=NotificationChannel.PUSH,
                provider_id=response,
                message="FCM notification sent"
            )

        except messaging.UnregisteredError:
            logger.warning(f"Device token is invalid or unregistered: {device_token}")
            return NotificationResult(
                success=False,
                channel=NotificationChannel.PUSH,
                message="Device token invalid or unregistered"
            )

        except messaging.SenderIdMismatchError:
            logger.error(f"Sender ID mismatch for device token: {device_token}")
            return NotificationResult(
                success=False,
                channel=NotificationChannel.PUSH,
                message="Sender ID mismatch"
            )

        except Exception as e:
            logger.error(f"FCM send error: {str(e)}")
            return NotificationResult(
                success=False,
                channel=NotificationChannel.PUSH,
                message=str(e)
            )

    async def send_batch(
        self,
        device_tokens: List[str],
        payload: NotificationPayload
    ) -> List[NotificationResult]:
        """
        Send push notification to multiple devices (batch).

        FCM supports up to 500 tokens per batch.

        Args:
            device_tokens: List of FCM device registration tokens
            payload: Notification content

        Returns:
            List of NotificationResult for each token
        """
        if not self.initialized:
            return [
                NotificationResult(
                    success=False,
                    channel=NotificationChannel.PUSH,
                    message="FCM not initialized"
                )
                for _ in device_tokens
            ]

        results = []
        batch_size = 500  # FCM limit

        # Process in batches
        for i in range(0, len(device_tokens), batch_size):
            batch_tokens = device_tokens[i:i + batch_size]
            batch_results = await self._send_batch_internal(batch_tokens, payload)
            results.extend(batch_results)

        return results

    async def _send_batch_internal(
        self,
        device_tokens: List[str],
        payload: NotificationPayload
    ) -> List[NotificationResult]:
        """Send a single batch (up to 500 tokens)"""
        try:
            # Build multicast message
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=payload.title,
                    body=payload.body
                ),
                data=payload.data or {},
                tokens=device_tokens,
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        sound="default",
                        channel_id="default"
                    )
                )
            )

            # Send batch (blocking call, run in executor)
            loop = asyncio.get_event_loop()
            batch_response = await loop.run_in_executor(
                None,
                messaging.send_multicast,
                message
            )

            logger.info(
                f"FCM batch sent: {batch_response.success_count} success, "
                f"{batch_response.failure_count} failures"
            )

            # Build results from responses
            results = []
            for idx, response in enumerate(batch_response.responses):
                if response.success:
                    results.append(NotificationResult(
                        success=True,
                        channel=NotificationChannel.PUSH,
                        provider_id=response.message_id,
                        message="FCM notification sent"
                    ))
                else:
                    error_msg = str(response.exception) if response.exception else "Unknown error"
                    results.append(NotificationResult(
                        success=False,
                        channel=NotificationChannel.PUSH,
                        message=error_msg
                    ))

            return results

        except Exception as e:
            logger.error(f"FCM batch send error: {str(e)}")
            # Return failure for all tokens
            return [
                NotificationResult(
                    success=False,
                    channel=NotificationChannel.PUSH,
                    message=str(e)
                )
                for _ in device_tokens
            ]

    async def send_to_topic(
        self,
        topic: str,
        payload: NotificationPayload
    ) -> NotificationResult:
        """
        Send notification to a topic (for broadcast messages).

        Args:
            topic: Topic name (e.g., "all_users", "clinical_team")
            payload: Notification content

        Returns:
            NotificationResult
        """
        if not self.initialized:
            return NotificationResult(
                success=False,
                channel=NotificationChannel.PUSH,
                message="FCM not initialized"
            )

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=payload.title,
                    body=payload.body
                ),
                data=payload.data or {},
                topic=topic,
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        sound="default",
                        channel_id="default"
                    )
                )
            )

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                messaging.send,
                message
            )

            logger.info(f"FCM topic notification sent to '{topic}': {response}")

            return NotificationResult(
                success=True,
                channel=NotificationChannel.PUSH,
                provider_id=response,
                message=f"FCM notification sent to topic '{topic}'"
            )

        except Exception as e:
            logger.error(f"FCM topic send error: {str(e)}")
            return NotificationResult(
                success=False,
                channel=NotificationChannel.PUSH,
                message=str(e)
            )
