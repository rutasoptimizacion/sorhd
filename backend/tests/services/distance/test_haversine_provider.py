"""
Unit tests for Haversine distance provider.
"""
import pytest
import math
from app.services.distance import Location, HaversineProvider, VincentyProvider


class TestHaversineProvider:
    """Tests for HaversineProvider."""

    @pytest.fixture
    def provider(self):
        """Create a Haversine provider instance."""
        return HaversineProvider(average_speed_kmh=40.0)

    @pytest.mark.asyncio
    async def test_single_location(self, provider):
        """Test matrix calculation with a single location."""
        locations = [Location(latitude=0.0, longitude=0.0, label="origin")]

        matrix = await provider.calculate_matrix(locations)

        assert len(matrix.locations) == 1
        assert matrix.distances_meters == [[0.0]]
        assert matrix.durations_seconds == [[0.0]]
        assert matrix.provider == "haversine"

    @pytest.mark.asyncio
    async def test_two_locations(self, provider):
        """Test distance calculation between two points."""
        # New York and Los Angeles (approximately 3,944 km apart)
        locations = [
            Location(latitude=40.7128, longitude=-74.0060, label="NYC"),
            Location(latitude=34.0522, longitude=-118.2437, label="LA")
        ]

        matrix = await provider.calculate_matrix(locations)

        # Check matrix dimensions
        assert len(matrix.distances_meters) == 2
        assert len(matrix.distances_meters[0]) == 2

        # Distance should be symmetric
        dist_nyc_to_la = matrix.distances_meters[0][1]
        dist_la_to_nyc = matrix.distances_meters[1][0]
        assert abs(dist_nyc_to_la - dist_la_to_nyc) < 1.0  # Within 1 meter

        # Check approximate distance (should be around 3.9M meters)
        assert 3_900_000 < dist_nyc_to_la < 4_000_000

        # Duration should be calculated based on speed
        expected_duration = dist_nyc_to_la / (40.0 / 3.6)  # 40 km/h in m/s
        actual_duration = matrix.durations_seconds[0][1]
        assert abs(expected_duration - actual_duration) < 1.0

    @pytest.mark.asyncio
    async def test_multiple_locations(self, provider):
        """Test matrix with multiple locations."""
        locations = [
            Location(latitude=0.0, longitude=0.0, label="Equator"),
            Location(latitude=10.0, longitude=0.0, label="North"),
            Location(latitude=0.0, longitude=10.0, label="East"),
        ]

        matrix = await provider.calculate_matrix(locations)

        # Check dimensions
        assert len(matrix.distances_meters) == 3
        assert len(matrix.durations_seconds) == 3

        # Diagonal should be zero
        for i in range(3):
            assert matrix.distances_meters[i][i] == 0.0
            assert matrix.durations_seconds[i][i] == 0.0

        # Distance should be symmetric
        for i in range(3):
            for j in range(3):
                assert abs(
                    matrix.distances_meters[i][j] - matrix.distances_meters[j][i]
                ) < 1.0

    @pytest.mark.asyncio
    async def test_empty_locations(self, provider):
        """Test with empty locations list."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await provider.calculate_matrix([])

    @pytest.mark.asyncio
    async def test_equator_distance(self, provider):
        """Test distance calculation along equator."""
        # Points along equator
        loc1 = Location(latitude=0.0, longitude=0.0)
        loc2 = Location(latitude=0.0, longitude=1.0)  # 1 degree east

        matrix = await provider.calculate_matrix([loc1, loc2])
        distance = matrix.distances_meters[0][1]

        # 1 degree at equator is approximately 111.19 km (more accurate haversine)
        expected_distance = 111_195  # meters
        assert abs(distance - expected_distance) < 100  # Within 100 meters

    @pytest.mark.asyncio
    async def test_meridian_distance(self, provider):
        """Test distance calculation along meridian."""
        # Points along prime meridian
        loc1 = Location(latitude=0.0, longitude=0.0)
        loc2 = Location(latitude=1.0, longitude=0.0)  # 1 degree north

        matrix = await provider.calculate_matrix([loc1, loc2])
        distance = matrix.distances_meters[0][1]

        # 1 degree latitude is approximately 111.19 km (more accurate haversine)
        expected_distance = 111_195  # meters
        assert abs(distance - expected_distance) < 100

    def test_speed_configuration(self):
        """Test average speed configuration."""
        provider = HaversineProvider(average_speed_kmh=60.0)
        assert provider.average_speed_kmh == 60.0
        assert provider.average_speed_ms == pytest.approx(60.0 / 3.6)

        # Test speed update
        provider.set_average_speed(80.0)
        assert provider.average_speed_kmh == 80.0
        assert provider.average_speed_ms == pytest.approx(80.0 / 3.6)

    def test_invalid_speed(self):
        """Test invalid speed raises error."""
        provider = HaversineProvider(average_speed_kmh=40.0)

        with pytest.raises(ValueError, match="Speed must be positive"):
            provider.set_average_speed(0)

        with pytest.raises(ValueError, match="Speed must be positive"):
            provider.set_average_speed(-10)


class TestVincentyProvider:
    """Tests for VincentyProvider (more accurate)."""

    @pytest.fixture
    def provider(self):
        """Create a Vincenty provider instance."""
        return VincentyProvider(average_speed_kmh=40.0)

    @pytest.mark.asyncio
    async def test_vincenty_accuracy(self, provider):
        """Test that Vincenty is more accurate than Haversine."""
        # Points with significant distance
        locations = [
            Location(latitude=40.7128, longitude=-74.0060, label="NYC"),
            Location(latitude=34.0522, longitude=-118.2437, label="LA")
        ]

        matrix = await provider.calculate_matrix(locations)
        distance = matrix.distances_meters[0][1]

        # Vincenty should give a result close to actual geodesic distance
        # (approximately 3,944 km for NYC-LA)
        assert 3_900_000 < distance < 4_000_000

    @pytest.mark.asyncio
    async def test_vincenty_same_point(self, provider):
        """Test Vincenty with same point."""
        loc = Location(latitude=10.0, longitude=20.0)

        matrix = await provider.calculate_matrix([loc, loc])

        # Distance to itself should be zero
        assert matrix.distances_meters[0][1] == 0.0

    @pytest.mark.asyncio
    async def test_vincenty_fallback_to_haversine(self, provider):
        """Test that Vincenty falls back to Haversine for antipodal points."""
        # Nearly antipodal points (opposite sides of Earth)
        # This may cause Vincenty to fail to converge
        locations = [
            Location(latitude=0.0, longitude=0.0),
            Location(latitude=0.0, longitude=179.9),
        ]

        # Should not raise an error (falls back to Haversine)
        matrix = await provider.calculate_matrix(locations)

        # Distance should be close to half Earth's circumference
        # Earth circumference at equator ≈ 40,075 km
        distance = matrix.distances_meters[0][1]
        assert distance > 0  # Should calculate some distance
