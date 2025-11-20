"""
Unit tests for DistanceService.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.distance import (
    DistanceService,
    Location,
    DistanceMatrix,
    HaversineProvider
)


class TestDistanceService:
    """Tests for DistanceService with mocked database."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.fixture
    def service_with_haversine_only(self, mock_db):
        """Create a service with only Haversine provider."""
        # Don't provide API keys so only Haversine is available
        service = DistanceService(
            db=mock_db,
            google_maps_api_key=None,
            osrm_base_url=None,
            use_cache=False
        )
        return service

    @pytest.mark.asyncio
    async def test_service_initialization(self, mock_db):
        """Test service initializes with fallback provider."""
        service = DistanceService(
            db=mock_db,
            use_cache=False
        )

        # Should have at least the Haversine fallback
        assert len(service.providers) >= 1
        assert isinstance(service.providers[-1], HaversineProvider)

    @pytest.mark.asyncio
    async def test_calculate_matrix(self, service_with_haversine_only):
        """Test calculating distance matrix."""
        locations = [
            Location(latitude=0.0, longitude=0.0, label="Origin"),
            Location(latitude=1.0, longitude=1.0, label="Destination")
        ]

        matrix = await service_with_haversine_only.calculate_matrix(locations)

        assert isinstance(matrix, DistanceMatrix)
        assert len(matrix.locations) == 2
        assert matrix.distances_meters[0][0] == 0.0  # Same point
        assert matrix.distances_meters[0][1] > 0  # Different point

    @pytest.mark.asyncio
    async def test_calculate_distance(self, service_with_haversine_only):
        """Test calculating distance between two points."""
        origin = Location(latitude=0.0, longitude=0.0)
        destination = Location(latitude=1.0, longitude=1.0)

        travel_time = await service_with_haversine_only.calculate_distance(
            origin, destination
        )

        assert travel_time.distance_meters > 0
        assert travel_time.duration_seconds > 0
        assert travel_time.origin == origin
        assert travel_time.destination == destination

    @pytest.mark.asyncio
    async def test_empty_locations(self, service_with_haversine_only):
        """Test with empty locations list."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await service_with_haversine_only.calculate_matrix([])

    @pytest.mark.asyncio
    async def test_get_primary_provider(self, service_with_haversine_only):
        """Test getting primary provider."""
        primary = service_with_haversine_only.get_primary_provider()
        assert primary is not None
        assert isinstance(primary, HaversineProvider)

    @pytest.mark.asyncio
    async def test_get_fallback_provider(self, service_with_haversine_only):
        """Test getting fallback provider."""
        fallback = service_with_haversine_only.get_fallback_provider()
        assert fallback is not None
        assert isinstance(fallback, HaversineProvider)

    @pytest.mark.asyncio
    async def test_force_specific_provider(self, service_with_haversine_only):
        """Test forcing a specific provider."""
        locations = [
            Location(latitude=0.0, longitude=0.0),
            Location(latitude=1.0, longitude=1.0)
        ]

        matrix = await service_with_haversine_only.calculate_matrix(
            locations,
            force_provider="haversine"
        )

        assert matrix.provider == "haversine"

    @pytest.mark.asyncio
    async def test_force_unavailable_provider(self, service_with_haversine_only):
        """Test forcing an unavailable provider."""
        locations = [
            Location(latitude=0.0, longitude=0.0),
            Location(latitude=1.0, longitude=1.0)
        ]

        with pytest.raises(ValueError, match="not available"):
            await service_with_haversine_only.calculate_matrix(
                locations,
                force_provider="google_maps"
            )

    @pytest.mark.asyncio
    async def test_cache_disabled(self, mock_db):
        """Test service with caching disabled."""
        service = DistanceService(
            db=mock_db,
            use_cache=False
        )

        assert service.cache_service is None

        locations = [
            Location(latitude=0.0, longitude=0.0),
            Location(latitude=1.0, longitude=1.0)
        ]

        # Should work without caching
        matrix = await service.calculate_matrix(locations)
        assert matrix is not None

    @pytest.mark.asyncio
    async def test_get_cache_statistics_disabled(self, mock_db):
        """Test cache statistics when caching is disabled."""
        service = DistanceService(
            db=mock_db,
            use_cache=False
        )

        stats = await service.get_cache_statistics()
        assert stats == {"cache_enabled": False}
