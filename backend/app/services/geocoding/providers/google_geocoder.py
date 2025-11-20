"""
Google Maps Geocoding Provider

Uses Google Maps Geocoding API for address geocoding
"""

import logging
from typing import Optional
import httpx

from app.services.geocoding.base_geocoder import BaseGeocoder, GeocodingResult
from app.core.config import settings

logger = logging.getLogger(__name__)


class GoogleGeocoder(BaseGeocoder):
    """Google Maps geocoding provider"""

    GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Google geocoder

        Args:
            api_key: Google Maps API key (defaults to settings.GOOGLE_MAPS_API_KEY)
        """
        self.api_key = api_key or settings.GOOGLE_MAPS_API_KEY

        if not self.api_key:
            logger.warning("Google Maps API key not configured")

    @property
    def provider_name(self) -> str:
        """Get provider name"""
        return "Google Maps"

    async def geocode(
        self,
        address: str,
        country: str = "CL"
    ) -> Optional[GeocodingResult]:
        """
        Geocode address using Google Maps Geocoding API

        Args:
            address: Address string to geocode
            country: ISO 3166-1 alpha-2 country code (default: CL for Chile)

        Returns:
            GeocodingResult if successful, None if geocoding failed

        Raises:
            Exception: If API error occurs
        """
        if not self.api_key:
            logger.error("Cannot geocode: Google Maps API key not configured")
            raise Exception(
                "Geocodificación no disponible: Google Maps API key no está configurada. "
                "Por favor, configura GOOGLE_MAPS_API_KEY en el archivo .env o usa coordenadas explícitas."
            )

        if not address or not address.strip():
            logger.warning("Cannot geocode empty address")
            return None

        try:
            # Build request parameters
            params = {
                "address": address.strip(),
                "key": self.api_key,
                "region": country.lower(),  # Bias results to country
                "language": "es"  # Spanish results
            }

            # Make API request
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.GEOCODE_URL, params=params)
                response.raise_for_status()

                data = response.json()

            # Check API response status
            if data.get("status") != "OK":
                status = data.get("status")
                error_message = data.get("error_message", "Unknown error")

                if status == "ZERO_RESULTS":
                    logger.info(f"No results found for address: {address}")
                    return None
                elif status == "OVER_QUERY_LIMIT":
                    logger.error("Google Maps API quota exceeded")
                    raise Exception("API quota exceeded")
                elif status == "REQUEST_DENIED":
                    logger.error(f"Google Maps API request denied: {error_message}")
                    raise Exception(f"API request denied: {error_message}")
                elif status == "INVALID_REQUEST":
                    logger.warning(f"Invalid geocoding request for address: {address}")
                    return None
                else:
                    logger.error(f"Google Maps API error: {status} - {error_message}")
                    raise Exception(f"API error: {status}")

            # Extract results
            results = data.get("results", [])
            if not results:
                logger.info(f"No geocoding results for address: {address}")
                return None

            # Use first result (highest confidence)
            result = results[0]
            location = result.get("geometry", {}).get("location", {})

            # Validate location data
            if "lat" not in location or "lng" not in location:
                logger.error("Invalid location data in geocoding result")
                return None

            # Extract address components
            address_components = {}
            for component in result.get("address_components", []):
                types = component.get("types", [])
                if "street_number" in types:
                    address_components["street_number"] = component.get("long_name")
                elif "route" in types:
                    address_components["street"] = component.get("long_name")
                elif "locality" in types:
                    address_components["city"] = component.get("long_name")
                elif "administrative_area_level_1" in types:
                    address_components["region"] = component.get("long_name")
                elif "country" in types:
                    address_components["country"] = component.get("long_name")
                    address_components["country_code"] = component.get("short_name")
                elif "postal_code" in types:
                    address_components["postal_code"] = component.get("long_name")

            # Calculate confidence based on location type
            location_type = result.get("geometry", {}).get("location_type", "")
            confidence = self._calculate_confidence(location_type, result.get("types", []))

            # Create result
            geocoding_result = GeocodingResult(
                latitude=location["lat"],
                longitude=location["lng"],
                formatted_address=result.get("formatted_address", address),
                place_id=result.get("place_id"),
                address_components=address_components,
                confidence=confidence
            )

            logger.info(
                f"Geocoded address '{address}' to ({geocoding_result.latitude}, {geocoding_result.longitude}) "
                f"with confidence {confidence}"
            )

            return geocoding_result

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during geocoding: {e}")
            raise Exception(f"Geocoding request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error geocoding address '{address}': {e}")
            raise

    async def reverse_geocode(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[GeocodingResult]:
        """
        Reverse geocode coordinates to address using Google Maps API

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            GeocodingResult if successful, None if reverse geocoding failed

        Raises:
            Exception: If API error occurs
        """
        if not self.api_key:
            logger.error("Cannot reverse geocode: Google Maps API key not configured")
            return None

        # Validate coordinates
        if not (-90 <= latitude <= 90):
            logger.warning(f"Invalid latitude: {latitude}")
            return None

        if not (-180 <= longitude <= 180):
            logger.warning(f"Invalid longitude: {longitude}")
            return None

        try:
            # Build request parameters
            params = {
                "latlng": f"{latitude},{longitude}",
                "key": self.api_key,
                "language": "es"  # Spanish results
            }

            # Make API request
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.GEOCODE_URL, params=params)
                response.raise_for_status()

                data = response.json()

            # Check API response status
            if data.get("status") != "OK":
                status = data.get("status")
                if status == "ZERO_RESULTS":
                    logger.info(f"No address found for coordinates: ({latitude}, {longitude})")
                    return None
                else:
                    error_message = data.get("error_message", "Unknown error")
                    logger.error(f"Google Maps API error: {status} - {error_message}")
                    raise Exception(f"API error: {status}")

            # Extract results
            results = data.get("results", [])
            if not results:
                logger.info(f"No reverse geocoding results for coordinates: ({latitude}, {longitude})")
                return None

            # Use first result (most specific)
            result = results[0]

            # Create result
            geocoding_result = GeocodingResult(
                latitude=latitude,
                longitude=longitude,
                formatted_address=result.get("formatted_address", ""),
                place_id=result.get("place_id"),
                confidence=1.0  # Reverse geocoding typically has high confidence
            )

            logger.info(
                f"Reverse geocoded ({latitude}, {longitude}) to '{geocoding_result.formatted_address}'"
            )

            return geocoding_result

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during reverse geocoding: {e}")
            raise Exception(f"Reverse geocoding request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error reverse geocoding coordinates ({latitude}, {longitude}): {e}")
            raise

    def _calculate_confidence(self, location_type: str, place_types: list) -> float:
        """
        Calculate confidence score based on Google Maps location type

        Args:
            location_type: Google Maps location type (ROOFTOP, RANGE_INTERPOLATED, etc.)
            place_types: List of place types

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Location type confidence (primary factor)
        location_type_scores = {
            "ROOFTOP": 1.0,           # Precise location
            "RANGE_INTERPOLATED": 0.8, # Interpolated between points
            "GEOMETRIC_CENTER": 0.6,   # Center of location (e.g., street, neighborhood)
            "APPROXIMATE": 0.4         # Approximate location
        }

        base_confidence = location_type_scores.get(location_type, 0.5)

        # Adjust based on place type (secondary factor)
        if "street_address" in place_types:
            base_confidence = min(1.0, base_confidence + 0.1)
        elif "premise" in place_types:
            base_confidence = min(1.0, base_confidence + 0.05)
        elif "locality" in place_types or "administrative_area" in place_types:
            base_confidence = max(0.3, base_confidence - 0.1)

        return round(base_confidence, 2)
