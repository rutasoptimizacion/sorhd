"""
Unit tests for geospatial utilities.
"""
import pytest
from app.utils.geospatial import (
    validate_coordinates,
    create_point,
    calculate_bounding_box,
    format_coordinates_for_display,
    parse_coordinates,
    calculate_distance_haversine,
    normalize_longitude,
    normalize_latitude
)


class TestCoordinateValidation:
    """Tests for coordinate validation."""

    def test_valid_coordinates(self):
        """Test validation of valid coordinates."""
        assert validate_coordinates(0.0, 0.0) is True
        assert validate_coordinates(45.0, -122.0) is True
        assert validate_coordinates(90.0, 180.0) is True
        assert validate_coordinates(-90.0, -180.0) is True

    def test_invalid_latitude(self):
        """Test validation rejects invalid latitude."""
        with pytest.raises(ValueError, match="Invalid latitude"):
            validate_coordinates(91.0, 0.0)

        with pytest.raises(ValueError, match="Invalid latitude"):
            validate_coordinates(-91.0, 0.0)

        with pytest.raises(ValueError, match="Invalid latitude"):
            validate_coordinates(100.0, 0.0)

    def test_invalid_longitude(self):
        """Test validation rejects invalid longitude."""
        with pytest.raises(ValueError, match="Invalid longitude"):
            validate_coordinates(0.0, 181.0)

        with pytest.raises(ValueError, match="Invalid longitude"):
            validate_coordinates(0.0, -181.0)

        with pytest.raises(ValueError, match="Invalid longitude"):
            validate_coordinates(0.0, 200.0)

    def test_non_numeric_coordinates(self):
        """Test validation rejects non-numeric values."""
        with pytest.raises(ValueError, match="must be numeric"):
            validate_coordinates("45.0", 0.0)

        with pytest.raises(ValueError, match="must be numeric"):
            validate_coordinates(0.0, "invalid")


class TestCreatePoint:
    """Tests for creating PostGIS points."""

    def test_create_point_valid(self):
        """Test creating a valid point."""
        point = create_point(45.0, -122.0)
        assert point is not None
        # Point should be in WKT format with longitude first
        assert "POINT(-122" in str(point)
        assert "45" in str(point)

    def test_create_point_invalid(self):
        """Test creating a point with invalid coordinates."""
        with pytest.raises(ValueError):
            create_point(100.0, 0.0)

        with pytest.raises(ValueError):
            create_point(0.0, 200.0)

    def test_create_point_srid(self):
        """Test creating a point with custom SRID."""
        point = create_point(45.0, -122.0, srid=3857)
        assert point is not None
        assert point.srid == 3857


class TestBoundingBox:
    """Tests for bounding box calculation."""

    def test_bounding_box_at_equator(self):
        """Test bounding box calculation at equator."""
        min_lat, min_lon, max_lat, max_lon = calculate_bounding_box(
            center_lat=0.0,
            center_lon=0.0,
            radius_meters=111_320  # ~1 degree at equator
        )

        # Should be roughly 1 degree in each direction
        assert -1.1 < min_lat < -0.9
        assert -1.1 < min_lon < -0.9
        assert 0.9 < max_lat < 1.1
        assert 0.9 < max_lon < 1.1

    def test_bounding_box_clamping(self):
        """Test that bounding box is clamped to valid ranges."""
        # Large radius that would exceed bounds
        min_lat, min_lon, max_lat, max_lon = calculate_bounding_box(
            center_lat=85.0,
            center_lon=175.0,
            radius_meters=1_000_000  # 1000 km
        )

        # Should be clamped to valid ranges
        assert -90 <= min_lat <= 90
        assert -180 <= min_lon <= 180
        assert -90 <= max_lat <= 90
        assert -180 <= max_lon <= 180

    def test_bounding_box_invalid_center(self):
        """Test bounding box with invalid center."""
        with pytest.raises(ValueError):
            calculate_bounding_box(
                center_lat=100.0,
                center_lon=0.0,
                radius_meters=1000
            )


class TestCoordinateFormatting:
    """Tests for coordinate formatting and parsing."""

    def test_format_coordinates_north_east(self):
        """Test formatting coordinates in NE quadrant."""
        formatted = format_coordinates_for_display(45.5, 122.3)
        assert "45.5" in formatted
        assert "122.3" in formatted
        assert "N" in formatted
        assert "E" in formatted

    def test_format_coordinates_south_west(self):
        """Test formatting coordinates in SW quadrant."""
        formatted = format_coordinates_for_display(-33.9, -70.6)
        assert "33.9" in formatted
        assert "70.6" in formatted
        assert "S" in formatted
        assert "W" in formatted

    def test_parse_coordinates_simple(self):
        """Test parsing simple lat,lon format."""
        lat, lon = parse_coordinates("45.5, -122.3")
        assert lat == pytest.approx(45.5)
        assert lon == pytest.approx(-122.3)

    def test_parse_coordinates_no_space(self):
        """Test parsing without space."""
        lat, lon = parse_coordinates("45.5,-122.3")
        assert lat == pytest.approx(45.5)
        assert lon == pytest.approx(-122.3)

    def test_parse_coordinates_with_cardinal(self):
        """Test parsing with cardinal directions."""
        lat, lon = parse_coordinates("45.5°N, 122.3°W")
        assert lat == pytest.approx(45.5)
        assert lon == pytest.approx(-122.3)

        lat, lon = parse_coordinates("33.9°S, 70.6°W")
        assert lat == pytest.approx(-33.9)
        assert lon == pytest.approx(-70.6)

    def test_parse_coordinates_invalid(self):
        """Test parsing invalid coordinate strings."""
        with pytest.raises(ValueError):
            parse_coordinates("invalid")

        with pytest.raises(ValueError):
            parse_coordinates("45.5")  # Missing longitude

        with pytest.raises(ValueError):
            parse_coordinates("45.5,abc")  # Non-numeric


class TestHaversineDistance:
    """Tests for Haversine distance calculation."""

    def test_distance_same_point(self):
        """Test distance between same point is zero."""
        distance = calculate_distance_haversine(0.0, 0.0, 0.0, 0.0)
        assert distance == pytest.approx(0.0)

    def test_distance_along_equator(self):
        """Test distance along equator."""
        # 1 degree at equator ≈ 111.32 km
        distance = calculate_distance_haversine(0.0, 0.0, 0.0, 1.0)
        assert 111_000 < distance < 112_000

    def test_distance_along_meridian(self):
        """Test distance along meridian."""
        # 1 degree latitude ≈ 111.32 km
        distance = calculate_distance_haversine(0.0, 0.0, 1.0, 0.0)
        assert 111_000 < distance < 112_000

    def test_distance_nyc_to_la(self):
        """Test known distance (NYC to LA)."""
        distance = calculate_distance_haversine(
            40.7128, -74.0060,  # NYC
            34.0522, -118.2437  # LA
        )
        # Approximately 3,944 km
        assert 3_900_000 < distance < 4_000_000


class TestNormalization:
    """Tests for coordinate normalization."""

    def test_normalize_longitude(self):
        """Test longitude normalization."""
        assert normalize_longitude(0.0) == pytest.approx(0.0)
        assert normalize_longitude(180.0) == pytest.approx(180.0)
        assert normalize_longitude(-180.0) == pytest.approx(-180.0)
        assert normalize_longitude(200.0) == pytest.approx(-160.0)
        assert normalize_longitude(-200.0) == pytest.approx(160.0)
        assert normalize_longitude(540.0) == pytest.approx(180.0)

    def test_normalize_latitude(self):
        """Test latitude normalization (clamping)."""
        assert normalize_latitude(0.0) == pytest.approx(0.0)
        assert normalize_latitude(45.0) == pytest.approx(45.0)
        assert normalize_latitude(-45.0) == pytest.approx(-45.0)
        assert normalize_latitude(100.0) == pytest.approx(90.0)
        assert normalize_latitude(-100.0) == pytest.approx(-90.0)
