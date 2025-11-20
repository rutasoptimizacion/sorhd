"""
Apple Push Notification Service (APNS) Provider

Handles push notifications for iOS devices.
"""
import logging
from typing import List, Optional
import asyncio
import json

try:
    from aioapns import APNs, NotificationRequest, PushType
    APNS_AVAILABLE = True
except ImportError:
    APNS_AVAILABLE = False
    logging.warning("aioapns not installed. APNS notifications will not work.")

from app.services.notification_service import (
    PushNotificationProvider,
    NotificationPayload,
    NotificationResult,
    NotificationChannel
)

logger = logging.getLogger(__name__)


class APNSProvider(PushNotificationProvider):
    """
    Apple Push Notification Service provider for iOS push notifications.

    Uses token-based authentication (recommended by Apple).
    Requires:
    - Team ID
    - Key ID (from Apple Developer portal)
    - Private key file (.p8)
    """

    def __init__(
        self,
        team_id: str,
        key_id: str,
        key_file: str,
        bundle_id: str,
        use_sandbox: bool = False
    ):
        """
        Initialize APNS provider.

        Args:
            team_id: Apple Developer Team ID
            key_id: APNs Key ID
            key_file: Path to .p8 private key file
            bundle_id: iOS app bundle identifier
            use_sandbox: Use sandbox environment (for development)
        """
        if not APNS_AVAILABLE:
            raise ImportError(
                "aioapns is required for APNS. "
                "Install with: pip install aioapns"
            )

        self.team_id = team_id
        self.key_id = key_id
        self.key_file = key_file
        self.bundle_id = bundle_id
        self.use_sandbox = use_sandbox
        self.client: Optional[APNs] = None

    async def _get_client(self) -> APNs:
        """Get or create APNS client"""
        if self.client is None:
            try:
                self.client = APNs(
                    key=self.key_file,
                    key_id=self.key_id,
                    team_id=self.team_id,
                    topic=self.bundle_id,
                    use_sandbox=self.use_sandbox
                )
                logger.info(f"APNS client initialized (sandbox={self.use_sandbox})")
            except Exception as e:
                logger.error(f"Failed to initialize APNS client: {str(e)}")
                raise

        return self.client

    async def send(
        self,
        device_token: str,
        payload: NotificationPayload
    ) -> NotificationResult:
        """
        Send push notification to a single iOS device.

        Args:
            device_token: APNS device token (hex string)
            payload: Notification content

        Returns:
            NotificationResult with success status
        """
        try:
            client = await self._get_client()

            # Build APNS payload
            # Reference: https://developer.apple.com/documentation/usernotifications
            apns_payload = {
                "aps": {
                    "alert": {
                        "title": payload.title,
                        "body": payload.body
                    },
                    "sound": "default",
                    "badge": 1  # Could be made dynamic
                }
            }

            # Add custom data
            if payload.data:
                apns_payload.update(payload.data)

            # Create notification request
            request = NotificationRequest(
                device_token=device_token,
                message=apns_payload,
                push_type=PushType.ALERT,
                priority=10  # High priority
            )

            # Send notification
            response = await client.send_notification(request)

            if response.is_successful:
                logger.info(f"APNS notification sent successfully to {device_token[:10]}...")
                return NotificationResult(
                    success=True,
                    channel=NotificationChannel.PUSH,
                    provider_id=response.notification_id,
                    message="APNS notification sent"
                )
            else:
                logger.warning(
                    f"APNS notification failed: {response.status} - {response.description}"
                )
                return NotificationResult(
                    success=False,
                    channel=NotificationChannel.PUSH,
                    message=f"APNS error: {response.status} - {response.description}"
                )

        except Exception as e:
            logger.error(f"APNS send error: {str(e)}")
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
        Send push notification to multiple iOS devices.

        Args:
            device_tokens: List of APNS device tokens
            payload: Notification content

        Returns:
            List of NotificationResult for each token
        """
        # APNS doesn't have a native batch API, send concurrently
        tasks = [self.send(token, payload) for token in device_tokens]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(NotificationResult(
                    success=False,
                    channel=NotificationChannel.PUSH,
                    message=str(result)
                ))
            else:
                processed_results.append(result)

        success_count = sum(1 for r in processed_results if r.success)
        logger.info(
            f"APNS batch sent: {success_count}/{len(device_tokens)} successful"
        )

        return processed_results

    async def send_silent(
        self,
        device_token: str,
        data: dict
    ) -> NotificationResult:
        """
        Send silent push notification (background update).

        Silent notifications don't show an alert but can wake up the app
        to perform background tasks.

        Args:
            device_token: APNS device token
            data: Custom data payload

        Returns:
            NotificationResult
        """
        try:
            client = await self._get_client()

            # Build silent notification payload
            apns_payload = {
                "aps": {
                    "content-available": 1  # Required for silent notifications
                }
            }
            apns_payload.update(data)

            request = NotificationRequest(
                device_token=device_token,
                message=apns_payload,
                push_type=PushType.BACKGROUND,
                priority=5  # Lower priority for background
            )

            response = await client.send_notification(request)

            if response.is_successful:
                logger.info(f"APNS silent notification sent to {device_token[:10]}...")
                return NotificationResult(
                    success=True,
                    channel=NotificationChannel.PUSH,
                    provider_id=response.notification_id,
                    message="APNS silent notification sent"
                )
            else:
                return NotificationResult(
                    success=False,
                    channel=NotificationChannel.PUSH,
                    message=f"APNS error: {response.status} - {response.description}"
                )

        except Exception as e:
            logger.error(f"APNS silent notification error: {str(e)}")
            return NotificationResult(
                success=False,
                channel=NotificationChannel.PUSH,
                message=str(e)
            )

    async def close(self):
        """Close APNS connection"""
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("APNS client closed")
