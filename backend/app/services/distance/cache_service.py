"""
Cache service for distance matrices.
Supports both Redis (if available) and database fallback.
"""
import hashlib
import json
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from ...models.distance_cache import DistanceCache
from .models import Location, DistanceMatrix


class CacheService:
    """
    Service for caching distance matrices.
    Uses Redis if available, falls back to database.
    """

    DEFAULT_TTL_HOURS = 24

    def __init__(self, db: AsyncSession, redis_client=None):
        """
        Initialize cache service.

        Args:
            db: Database session
            redis_client: Optional Redis client (not implemented yet)
        """
        self.db = db
        self.redis_client = redis_client
        self.ttl_hours = self.DEFAULT_TTL_HOURS

    @staticmethod
    def generate_cache_key(locations: List[Location]) -> str:
        """
        Generate a deterministic cache key for a list of locations.

        Args:
            locations: List of Location objects

        Returns:
            SHA-256 hash of sorted coordinates
        """
        # Sort locations by coordinates to ensure deterministic key
        sorted_coords = sorted([(loc.latitude, loc.longitude) for loc in locations])

        # Create string representation
        coords_str = json.dumps(sorted_coords, sort_keys=True)

        # Generate hash
        cache_key = hashlib.sha256(coords_str.encode()).hexdigest()
        return cache_key

    async def get(self, locations: List[Location]) -> Optional[DistanceMatrix]:
        """
        Retrieve distance matrix from cache.

        Args:
            locations: List of Location objects

        Returns:
            DistanceMatrix if found and not expired, None otherwise
        """
        cache_key = self.generate_cache_key(locations)

        # Try Redis first (if available)
        if self.redis_client:
            try:
                cached_data = await self._get_from_redis(cache_key)
                if cached_data:
                    return DistanceMatrix.from_dict(json.loads(cached_data))
            except Exception as e:
                # Redis error, fall back to database
                print(f"Redis error: {e}")

        # Fall back to database
        return await self._get_from_database(cache_key, locations)

    async def set(self, matrix: DistanceMatrix, ttl_hours: Optional[int] = None):
        """
        Store distance matrix in cache.

        Args:
            matrix: DistanceMatrix to cache
            ttl_hours: Time to live in hours (default: 24)
        """
        cache_key = self.generate_cache_key(matrix.locations)
        ttl = ttl_hours or self.ttl_hours
        expires_at = datetime.utcnow() + timedelta(hours=ttl)

        # Try Redis first (if available)
        if self.redis_client:
            try:
                await self._set_in_redis(cache_key, matrix, ttl)
            except Exception as e:
                print(f"Redis error: {e}")

        # Always store in database as fallback
        await self._set_in_database(cache_key, matrix, expires_at)

    async def _get_from_redis(self, cache_key: str) -> Optional[str]:
        """Get cached data from Redis."""
        # Redis implementation placeholder
        # return await self.redis_client.get(f"distance_matrix:{cache_key}")
        return None

    async def _set_in_redis(self, cache_key: str, matrix: DistanceMatrix, ttl_hours: int):
        """Store data in Redis with expiration."""
        # Redis implementation placeholder
        # data = json.dumps(matrix.to_dict())
        # await self.redis_client.setex(
        #     f"distance_matrix:{cache_key}",
        #     ttl_hours * 3600,
        #     data
        # )
        pass

    async def _get_from_database(self, cache_key: str, locations: List[Location]) -> Optional[DistanceMatrix]:
        """Retrieve cached distance matrix from database."""
        stmt = select(DistanceCache).where(
            DistanceCache.cache_key == cache_key,
            DistanceCache.expires_at > datetime.utcnow()
        )

        result = await self.db.execute(stmt)
        cache_entry = result.scalar_one_or_none()

        if cache_entry:
            # Reconstruct DistanceMatrix from cached data
            return DistanceMatrix(
                locations=locations,
                distances_meters=cache_entry.distances_meters,
                durations_seconds=cache_entry.durations_seconds,
                provider=cache_entry.provider
            )

        return None

    async def _set_in_database(self, cache_key: str, matrix: DistanceMatrix, expires_at: datetime):
        """Store distance matrix in database."""
        # Check if entry already exists
        stmt = select(DistanceCache).where(DistanceCache.cache_key == cache_key)
        result = await self.db.execute(stmt)
        existing_entry = result.scalar_one_or_none()

        if existing_entry:
            # Update existing entry
            existing_entry.distances_meters = matrix.distances_meters
            existing_entry.durations_seconds = matrix.durations_seconds
            existing_entry.provider = matrix.provider
            existing_entry.expires_at = expires_at
            existing_entry.updated_at = datetime.utcnow()
        else:
            # Create new entry
            cache_entry = DistanceCache(
                cache_key=cache_key,
                distances_meters=matrix.distances_meters,
                durations_seconds=matrix.durations_seconds,
                provider=matrix.provider,
                expires_at=expires_at
            )
            self.db.add(cache_entry)

        await self.db.commit()

    async def invalidate(self, locations: List[Location]):
        """
        Invalidate cached distance matrix for given locations.

        Args:
            locations: List of Location objects
        """
        cache_key = self.generate_cache_key(locations)

        # Invalidate in Redis
        if self.redis_client:
            try:
                # await self.redis_client.delete(f"distance_matrix:{cache_key}")
                pass
            except Exception as e:
                print(f"Redis error: {e}")

        # Invalidate in database
        stmt = delete(DistanceCache).where(DistanceCache.cache_key == cache_key)
        await self.db.execute(stmt)
        await self.db.commit()

    async def clear_expired(self):
        """Remove expired cache entries from database."""
        stmt = delete(DistanceCache).where(DistanceCache.expires_at <= datetime.utcnow())
        await self.db.execute(stmt)
        await self.db.commit()

    async def get_statistics(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        stmt = select(DistanceCache)
        result = await self.db.execute(stmt)
        all_entries = result.scalars().all()

        now = datetime.utcnow()
        valid_entries = [e for e in all_entries if e.expires_at > now]
        expired_entries = [e for e in all_entries if e.expires_at <= now]

        return {
            "total_entries": len(all_entries),
            "valid_entries": len(valid_entries),
            "expired_entries": len(expired_entries),
            "cache_hit_potential": len(valid_entries) / max(len(all_entries), 1)
        }
