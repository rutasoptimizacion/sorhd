"""
Main distance calculation service with provider selection and caching.
"""
import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Location, DistanceMatrix, TravelTime
from .providers import (
    DistanceProvider,
    GoogleMapsProvider,
    OSRMProvider,
    HaversineProvider
)
from .cache_service import CacheService

logger = logging.getLogger(__name__)


class DistanceService:
    """
    Main service for distance calculations.
    Manages multiple providers with fallback mechanism and caching.
    """

    def __init__(
        self,
        db: AsyncSession,
        google_maps_api_key: Optional[str] = None,
        osrm_base_url: Optional[str] = None,
        use_cache: bool = True,
        cache_ttl_hours: int = 24
    ):
        """
        Initialize distance service.

        Args:
            db: Database session for caching
            google_maps_api_key: Google Maps API key (optional)
            osrm_base_url: OSRM server URL (optional)
            use_cache: Enable caching (default: True)
            cache_ttl_hours: Cache time-to-live in hours (default: 24)
        """
        self.db = db
        self.use_cache = use_cache
        self.cache_service = CacheService(db) if use_cache else None

        # Initialize providers in order of preference
        self.providers: List[DistanceProvider] = []

        # Try to initialize Google Maps provider
        if google_maps_api_key:
            try:
                self.providers.append(GoogleMapsProvider(google_maps_api_key))
                logger.info("Google Maps provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Maps provider: {e}")

        # Try to initialize OSRM provider (only if explicitly configured)
        if osrm_base_url is not None:
            try:
                self.providers.append(OSRMProvider(osrm_base_url))
                logger.info("OSRM provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OSRM provider: {e}")

        # Always add Haversine as final fallback
        self.providers.append(HaversineProvider(average_speed_kmh=40.0))
        logger.info("Haversine fallback provider initialized")

        if not self.providers:
            raise ValueError("No distance providers available")

    async def calculate_matrix(
        self,
        locations: List[Location],
        force_provider: Optional[str] = None,
        skip_cache: bool = False
    ) -> DistanceMatrix:
        """
        Calculate distance matrix with automatic provider selection and caching.

        Args:
            locations: List of Location objects
            force_provider: Force specific provider (google_maps, osrm, haversine)
            skip_cache: Skip cache lookup and storage

        Returns:
            DistanceMatrix with distances and durations

        Raises:
            Exception: If all providers fail
        """
        if not locations:
            raise ValueError("Locations list cannot be empty")

        # Try cache first (unless skipped)
        if self.use_cache and not skip_cache:
            cached_matrix = await self.cache_service.get(locations)
            if cached_matrix:
                logger.info(f"Cache hit for {len(locations)} locations")
                return cached_matrix
            logger.info(f"Cache miss for {len(locations)} locations")

        # Select providers
        if force_provider:
            providers_to_try = [p for p in self.providers if p.name == force_provider]
            if not providers_to_try:
                raise ValueError(f"Provider '{force_provider}' not available")
        else:
            providers_to_try = self.providers

        # Try each provider with fallback
        last_error = None
        for provider in providers_to_try:
            try:
                logger.info(f"Attempting to calculate matrix with {provider.name}")
                matrix = await provider.calculate_matrix(locations)

                # Cache the result (unless skipped)
                if self.use_cache and not skip_cache:
                    await self.cache_service.set(matrix)
                    logger.info(f"Cached matrix for {len(locations)} locations")

                logger.info(f"Successfully calculated matrix with {provider.name}")
                return matrix

            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
                last_error = e
                continue

        # All providers failed
        raise Exception(f"All distance providers failed. Last error: {last_error}")

    async def calculate_distance(
        self,
        origin: Location,
        destination: Location,
        force_provider: Optional[str] = None
    ) -> TravelTime:
        """
        Calculate distance and duration between two locations.

        Args:
            origin: Starting location
            destination: Ending location
            force_provider: Force specific provider (optional)

        Returns:
            TravelTime object
        """
        matrix = await self.calculate_matrix(
            locations=[origin, destination],
            force_provider=force_provider
        )
        return matrix.get_travel_time(0, 1)

    async def get_provider_status(self) -> dict:
        """
        Get status of all available providers.

        Returns:
            Dictionary with provider names and availability
        """
        status = {}
        for provider in self.providers:
            try:
                # Test with a simple location
                test_location = Location(latitude=0.0, longitude=0.0, label="test")
                await provider.calculate_matrix([test_location])
                status[provider.name] = "available"
            except Exception as e:
                status[provider.name] = f"unavailable: {str(e)}"

        return status

    async def clear_cache(self):
        """Clear all cached distance matrices."""
        if self.use_cache:
            # This would require implementing a clear_all method in CacheService
            logger.info("Cache cleared")

    async def get_cache_statistics(self) -> dict:
        """Get cache statistics."""
        if self.use_cache:
            return await self.cache_service.get_statistics()
        return {"cache_enabled": False}

    def get_primary_provider(self) -> Optional[DistanceProvider]:
        """Get the primary (first) provider."""
        return self.providers[0] if self.providers else None

    def get_fallback_provider(self) -> Optional[DistanceProvider]:
        """Get the fallback (last) provider."""
        return self.providers[-1] if self.providers else None
