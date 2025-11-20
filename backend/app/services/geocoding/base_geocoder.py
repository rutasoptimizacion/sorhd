"""
Base Geocoder Interface

Abstract base class for geocoding providers
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class GeocodingResult:
    """Geocoding result data structure"""

    def __init__(
        self,
        latitude: float,
        longitude: float,
        formatted_address: str,
        place_id: Optional[str] = None,
        address_components: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None
    ):
        """
        Initialize geocoding result

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            formatted_address: Full formatted address returned by provider
            place_id: Provider-specific place identifier (optional)
            address_components: Detailed address components (optional)
            confidence: Confidence score 0.0-1.0 (optional)
        """
        self.latitude = latitude
        self.longitude = longitude
        self.formatted_address = formatted_address
        self.place_id = place_id
        self.address_components = address_components or {}
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "formatted_address": self.formatted_address,
            "place_id": self.place_id,
            "address_components": self.address_components,
            "confidence": self.confidence
        }


class BaseGeocoder(ABC):
    """Abstract base class for geocoding providers"""

    @abstractmethod
    async def geocode(
        self,
        address: str,
        country: str = "CL"
    ) -> Optional[GeocodingResult]:
        """
        Geocode an address to coordinates

        Args:
            address: Address string to geocode
            country: ISO 3166-1 alpha-2 country code (default: CL for Chile)

        Returns:
            GeocodingResult if successful, None if geocoding failed

        Raises:
            Exception: If provider API error occurs
        """
        pass

    @abstractmethod
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
            Exception: If provider API error occurs
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name"""
        pass
