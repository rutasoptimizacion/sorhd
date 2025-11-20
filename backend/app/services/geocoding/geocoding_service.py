"""
Geocoding Service

Main service for geocoding addresses to coordinates
"""

import logging
from typing import Optional

from app.services.geocoding.base_geocoder import BaseGeocoder, GeocodingResult
from app.services.geocoding.providers.google_geocoder import GoogleGeocoder
from app.core.config import settings

logger = logging.getLogger(__name__)


class GeocodingService:
    """
    Service for geocoding addresses to coordinates

    Uses Google Maps as primary provider
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize geocoding service

        Args:
            api_key: Google Maps API key (optional, defaults to settings)
        """
        # Initialize Google Maps provider
        self.primary_provider: BaseGeocoder = GoogleGeocoder(api_key=api_key)

    async def geocode_address(
        self,
        address: str,
        country: str = "CL"
    ) -> Optional[GeocodingResult]:
        """
        Geocode Chilean address to coordinates

        Args:
            address: Address string to geocode
            country: Country code (default: CL for Chile)

        Returns:
            GeocodingResult if successful, None if geocoding failed

        Raises:
            Exception: If provider error occurs

        Examples:
            >>> service = GeocodingService()
            >>> result = await service.geocode_address("Avenida Libertador Bernardo O'Higgins 1234, Santiago")
            >>> print(result.latitude, result.longitude)
            -33.4569 -70.6483
        """
        if not address or not address.strip():
            logger.warning("Cannot geocode empty address")
            return None

        logger.info(f"Geocoding address: {address} (country: {country})")

        try:
            # Try primary provider (Google Maps)
            result = await self.primary_provider.geocode(address, country)

            if result:
                logger.info(
                    f"Successfully geocoded address using {self.primary_provider.provider_name}: "
                    f"({result.latitude}, {result.longitude})"
                )
                return result
            else:
                logger.warning(f"No results found for address: {address}")
                return None

        except Exception as e:
            logger.error(f"Error geocoding address '{address}': {e}")
            raise

    async def reverse_geocode(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[GeocodingResult]:
        """
        Reverse geocode coordinates to address

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            GeocodingResult if successful, None if reverse geocoding failed

        Raises:
            Exception: If provider error occurs

        Examples:
            >>> service = GeocodingService()
            >>> result = await service.reverse_geocode(-33.4569, -70.6483)
            >>> print(result.formatted_address)
            "Avenida Libertador Bernardo O'Higgins 1234, Santiago, Chile"
        """
        # Validate coordinates
        if not (-90 <= latitude <= 90):
            logger.warning(f"Invalid latitude: {latitude}")
            raise ValueError(f"Invalid latitude: {latitude}. Must be between -90 and 90")

        if not (-180 <= longitude <= 180):
            logger.warning(f"Invalid longitude: {longitude}")
            raise ValueError(f"Invalid longitude: {longitude}. Must be between -180 and 180")

        logger.info(f"Reverse geocoding coordinates: ({latitude}, {longitude})")

        try:
            # Try primary provider (Google Maps)
            result = await self.primary_provider.reverse_geocode(latitude, longitude)

            if result:
                logger.info(
                    f"Successfully reverse geocoded using {self.primary_provider.provider_name}: "
                    f"{result.formatted_address}"
                )
                return result
            else:
                logger.warning(f"No address found for coordinates: ({latitude}, {longitude})")
                return None

        except Exception as e:
            logger.error(f"Error reverse geocoding coordinates ({latitude}, {longitude}): {e}")
            raise

    async def validate_chilean_address(self, address: str) -> bool:
        """
        Validate if address can be geocoded (simple check)

        Args:
            address: Address string to validate

        Returns:
            True if address can be geocoded, False otherwise
        """
        try:
            result = await self.geocode_address(address, country="CL")
            return result is not None
        except Exception as e:
            logger.error(f"Error validating address: {e}")
            return False
