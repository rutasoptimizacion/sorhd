"""
Distance Cache Model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, ARRAY, Float, DateTime
from sqlalchemy.dialects.postgresql import JSONB

from .base import BaseModel


class DistanceCache(BaseModel):
    """
    Cache table for storing calculated distance matrices.
    Reduces API calls to external distance providers.
    """
    __tablename__ = "distance_cache"

    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(64), unique=True, nullable=False, index=True)

    # Store matrices as 2D arrays (PostgreSQL ARRAY type)
    distances_meters = Column(JSONB, nullable=False)  # Using JSONB for 2D array
    durations_seconds = Column(JSONB, nullable=False)  # Using JSONB for 2D array

    # Metadata
    provider = Column(String(50), nullable=False)  # google_maps, osrm, haversine
    expires_at = Column(DateTime, nullable=False, index=True)

    def __repr__(self):
        return f"<DistanceCache(cache_key={self.cache_key}, provider={self.provider})>"

    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.utcnow() > self.expires_at
