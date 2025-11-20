"""
Twilio SMS Provider

Handles SMS notifications via Twilio API.
"""
import logging
from typing import Optional
import re
import asyncio

try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logging.warning("twilio not installed. SMS notifications will not work.")

from app.services.notification_service import (
    SMSProvider,
    NotificationResult,
    NotificationChannel
)

logger = logging.getLogger(__name__)


class TwilioSMSProvider(SMSProvider):
    """
    Twilio SMS provider for sending text messages.

    Requires Twilio account SID, auth token, and a phone number.
    """

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_phone: str
    ):
        """
        Initialize Twilio SMS provider.

        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            from_phone: Twilio phone number (E.164 format: +56912345678)
        """
        if not TWILIO_AVAILABLE:
            raise ImportError(
                "twilio is required for SMS. "
                "Install with: pip install twilio"
            )

        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_phone = from_phone
        self.client: Optional[Client] = None

        # Validate phone number format
        if not self._validate_phone_format(from_phone):
            raise ValueError(
                f"Invalid from_phone format: {from_phone}. "
                "Must be in E.164 format (e.g., +56912345678)"
            )

    def _get_client(self) -> Client:
        """Get or create Twilio client"""
        if self.client is None:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {str(e)}")
                raise

        return self.client

    @staticmethod
    def _validate_phone_format(phone: str) -> bool:
        """
        Validate phone number is in E.164 format.

        E.164 format: +[country code][number]
        Example: +56912345678 (Chile)
        """
        # E.164 regex: + followed by 1-15 digits
        pattern = r'^\+[1-9]\d{1,14}$'
        return bool(re.match(pattern, phone))

    @staticmethod
    def normalize_phone_number(phone: str, default_country_code: str = "+56") -> str:
        """
        Normalize phone number to E.164 format.

        Args:
            phone: Phone number (various formats accepted)
            default_country_code: Default country code if not provided (Chile: +56)

        Returns:
            Normalized phone number in E.164 format

        Examples:
            "912345678" -> "+56912345678" (Chile)
            "+56 9 1234 5678" -> "+56912345678"
            "56912345678" -> "+56912345678"
        """
        # Remove spaces, dashes, parentheses
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)

        # If already has +, validate and return
        if cleaned.startswith('+'):
            return cleaned

        # If starts with country code without +, add it
        if cleaned.startswith(default_country_code.replace('+', '')):
            return '+' + cleaned

        # Otherwise, prepend default country code
        return default_country_code + cleaned

    async def send(
        self,
        phone_number: str,
        message: str
    ) -> NotificationResult:
        """
        Send SMS to a phone number.

        Args:
            phone_number: Destination phone number (E.164 format)
            message: SMS message text (max 1600 characters)

        Returns:
            NotificationResult with success status
        """
        try:
            # Validate and normalize phone number
            if not self._validate_phone_format(phone_number):
                # Try to normalize
                phone_number = self.normalize_phone_number(phone_number)

                if not self._validate_phone_format(phone_number):
                    logger.warning(f"Invalid phone number format: {phone_number}")
                    return NotificationResult(
                        success=False,
                        channel=NotificationChannel.SMS,
                        message=f"Invalid phone number format: {phone_number}"
                    )

            # Truncate message if too long (Twilio limit is 1600 chars)
            if len(message) > 1600:
                logger.warning(f"SMS message truncated from {len(message)} to 1600 chars")
                message = message[:1597] + "..."

            # Get Twilio client
            client = self._get_client()

            # Send SMS (blocking call, run in executor)
            loop = asyncio.get_event_loop()
            twilio_message = await loop.run_in_executor(
                None,
                lambda: client.messages.create(
                    body=message,
                    from_=self.from_phone,
                    to=phone_number
                )
            )

            logger.info(
                f"SMS sent successfully to {phone_number}: "
                f"SID={twilio_message.sid}, Status={twilio_message.status}"
            )

            return NotificationResult(
                success=True,
                channel=NotificationChannel.SMS,
                provider_id=twilio_message.sid,
                message=f"SMS sent (status: {twilio_message.status})"
            )

        except TwilioRestException as e:
            logger.error(f"Twilio API error: {e.code} - {e.msg}")
            return NotificationResult(
                success=False,
                channel=NotificationChannel.SMS,
                message=f"Twilio error {e.code}: {e.msg}"
            )

        except Exception as e:
            logger.error(f"SMS send error: {str(e)}")
            return NotificationResult(
                success=False,
                channel=NotificationChannel.SMS,
                message=str(e)
            )

    async def send_bulk(
        self,
        phone_numbers: list[str],
        message: str
    ) -> list[NotificationResult]:
        """
        Send SMS to multiple phone numbers.

        Args:
            phone_numbers: List of phone numbers
            message: SMS message text

        Returns:
            List of NotificationResult for each number
        """
        # Send concurrently
        tasks = [self.send(phone, message) for phone in phone_numbers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(NotificationResult(
                    success=False,
                    channel=NotificationChannel.SMS,
                    message=str(result)
                ))
            else:
                processed_results.append(result)

        success_count = sum(1 for r in processed_results if r.success)
        logger.info(
            f"SMS batch sent: {success_count}/{len(phone_numbers)} successful"
        )

        return processed_results

    async def get_message_status(self, message_sid: str) -> Optional[dict]:
        """
        Get the delivery status of a sent message.

        Args:
            message_sid: Twilio message SID

        Returns:
            Dictionary with message status information, or None if not found
        """
        try:
            client = self._get_client()

            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None,
                lambda: client.messages(message_sid).fetch()
            )

            return {
                "sid": message.sid,
                "status": message.status,
                "error_code": message.error_code,
                "error_message": message.error_message,
                "date_sent": message.date_sent,
                "date_updated": message.date_updated,
                "price": message.price,
                "price_unit": message.price_unit
            }

        except TwilioRestException as e:
            logger.error(f"Failed to fetch message status: {e.code} - {e.msg}")
            return None

        except Exception as e:
            logger.error(f"Error fetching message status: {str(e)}")
            return None
