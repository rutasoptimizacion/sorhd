"""
Geospatial utilities for coordinate validation and PostGIS operations.
"""
import math
from typing import Tuple, List, Optional
from geoalchemy2.shape import to_shape
from geoalchemy2 import WKTElement
from shapely.geometry import Point
from shapely import wkt


def validate_coordinates(latitude: float, longitude: float) -> bool:
    """
    Validate geographic coordinates.

    Args:
        latitude: Latitude value
        longitude: Longitude value

    Returns:
        True if coordinates are valid

    Raises:
        ValueError: If coordinates are invalid
    """
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        raise ValueError("Latitude and longitude must be numeric")

    if not -90 <= latitude <= 90:
        raise ValueError(f"Invalid latitude: {latitude}. Must be between -90 and 90.")

    if not -180 <= longitude <= 180:
        raise ValueError(f"Invalid longitude: {longitude}. Must be between -180 and 180.")

    return True


def create_point(latitude: float, longitude: float, srid: int = 4326) -> WKTElement:
    """
    Create a PostGIS Point geometry from coordinates.

    Args:
        latitude: Latitude value
        longitude: Longitude value
        srid: Spatial Reference System Identifier (default: 4326 for WGS 84)

    Returns:
        WKTElement representing the point in PostGIS format

    Note:
        PostGIS uses (longitude, latitude) order, not (latitude, longitude)!
    """
    validate_coordinates(latitude, longitude)

    # PostGIS uses POINT(longitude latitude) order
    point_wkt = f'POINT({longitude} {latitude})'
    return WKTElement(point_wkt, srid=srid)


def extract_coordinates(geom) -> Tuple[float, float]:
    """
    Extract latitude and longitude from a PostGIS geometry.

    Args:
        geom: PostGIS geometry object

    Returns:
        Tuple of (latitude, longitude)
    """
    if geom is None:
        raise ValueError("Geometry is None")

    # Convert to Shapely geometry
    shape = to_shape(geom)

    if not isinstance(shape, Point):
        raise ValueError(f"Expected Point geometry, got {type(shape)}")

    # PostGIS stores as (longitude, latitude)
    longitude = shape.x
    latitude = shape.y

    return (latitude, longitude)


def calculate_bounding_box(
    center_lat: float,
    center_lon: float,
    radius_meters: float
) -> Tuple[float, float, float, float]:
    """
    Calculate a bounding box around a center point.

    Args:
        center_lat: Center latitude
        center_lon: Center longitude
        radius_meters: Radius in meters

    Returns:
        Tuple of (min_lat, min_lon, max_lat, max_lon)
    """
    validate_coordinates(center_lat, center_lon)

    # Earth's radius in meters
    earth_radius = 6371000.0

    # Calculate angular distance
    angular_distance = radius_meters / earth_radius

    # Convert to radians
    lat_rad = math.radians(center_lat)
    lon_rad = math.radians(center_lon)

    # Calculate bounding box
    min_lat = math.degrees(lat_rad - angular_distance)
    max_lat = math.degrees(lat_rad + angular_distance)

    # Adjust for longitude (depends on latitude)
    delta_lon = math.degrees(angular_distance / math.cos(lat_rad))
    min_lon = center_lon - delta_lon
    max_lon = center_lon + delta_lon

    # Clamp to valid ranges
    min_lat = max(min_lat, -90.0)
    max_lat = min(max_lat, 90.0)
    min_lon = max(min_lon, -180.0)
    max_lon = min(max_lon, 180.0)

    return (min_lat, min_lon, max_lat, max_lon)


def create_circle(
    center_lat: float,
    center_lon: float,
    radius_meters: float,
    srid: int = 4326
) -> str:
    """
    Create a WKT string for a circular buffer around a point.

    Args:
        center_lat: Center latitude
        center_lon: Center longitude
        radius_meters: Radius in meters
        srid: Spatial Reference System Identifier

    Returns:
        WKT string for use in PostGIS ST_Buffer queries
    """
    validate_coordinates(center_lat, center_lon)

    # Create point
    point = Point(center_lon, center_lat)

    # For accurate buffering, need to use geography type in PostGIS
    # This is just the point WKT - buffering should be done in SQL
    return point.wkt


def is_point_in_polygon(point_lat: float, point_lon: float, polygon_wkt: str) -> bool:
    """
    Check if a point is inside a polygon.

    Args:
        point_lat: Point latitude
        point_lon: Point longitude
        polygon_wkt: Polygon in WKT format

    Returns:
        True if point is inside polygon
    """
    validate_coordinates(point_lat, point_lon)

    point = Point(point_lon, point_lat)
    polygon = wkt.loads(polygon_wkt)

    return point.within(polygon)


def format_coordinates_for_display(latitude: float, longitude: float) -> str:
    """
    Format coordinates for human-readable display.

    Args:
        latitude: Latitude value
        longitude: Longitude value

    Returns:
        Formatted string (e.g., "12.3456°N, 78.9012°W")
    """
    validate_coordinates(latitude, longitude)

    lat_dir = "N" if latitude >= 0 else "S"
    lon_dir = "E" if longitude >= 0 else "W"

    return f"{abs(latitude):.4f}°{lat_dir}, {abs(longitude):.4f}°{lon_dir}"


def parse_coordinates(coord_string: str) -> Tuple[float, float]:
    """
    Parse coordinate string in various formats.

    Supported formats:
    - "lat,lon" (e.g., "12.3456,78.9012")
    - "lat, lon" (with space)
    - "12.3456°N, 78.9012°W"

    Args:
        coord_string: String containing coordinates

    Returns:
        Tuple of (latitude, longitude)

    Raises:
        ValueError: If string cannot be parsed
    """
    coord_string = coord_string.strip()

    # Remove degree symbols and cardinal directions
    coord_string = coord_string.replace("°", "")

    # Handle N/S/E/W suffixes
    lat_multiplier = 1
    lon_multiplier = 1

    if "S" in coord_string.upper():
        lat_multiplier = -1
        coord_string = coord_string.upper().replace("S", "")

    if "N" in coord_string.upper():
        coord_string = coord_string.upper().replace("N", "")

    if "W" in coord_string.upper():
        lon_multiplier = -1
        coord_string = coord_string.upper().replace("W", "")

    if "E" in coord_string.upper():
        coord_string = coord_string.upper().replace("E", "")

    # Split by comma
    parts = coord_string.split(",")
    if len(parts) != 2:
        raise ValueError(f"Invalid coordinate string: {coord_string}. Expected 'lat,lon' format.")

    try:
        latitude = float(parts[0].strip()) * lat_multiplier
        longitude = float(parts[1].strip()) * lon_multiplier
    except ValueError:
        raise ValueError(f"Invalid coordinate values: {coord_string}")

    validate_coordinates(latitude, longitude)
    return (latitude, longitude)


def calculate_distance_haversine(
    lat1: float, lon1: float,
    lat2: float, lon2: float
) -> float:
    """
    Calculate great-circle distance using Haversine formula.

    Args:
        lat1: First point latitude
        lon1: First point longitude
        lat2: Second point latitude
        lon2: Second point longitude

    Returns:
        Distance in meters
    """
    validate_coordinates(lat1, lon1)
    validate_coordinates(lat2, lon2)

    # Earth's radius in meters
    R = 6371000.0

    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)

    # Haversine formula
    a = (
        math.sin(dLat / 2) ** 2 +
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dLon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def get_postgis_distance_query(
    point1_column: str,
    point2_column: str,
    use_geography: bool = True
) -> str:
    """
    Generate PostGIS distance query SQL fragment.

    Args:
        point1_column: Name of first point column
        point2_column: Name of second point column
        use_geography: Use geography type for accurate distances (default: True)

    Returns:
        SQL fragment for distance calculation

    Example:
        ST_Distance(location1::geography, location2::geography)
    """
    if use_geography:
        return f"ST_Distance({point1_column}::geography, {point2_column}::geography)"
    else:
        return f"ST_Distance({point1_column}, {point2_column})"


def normalize_longitude(longitude: float) -> float:
    """
    Normalize longitude to [-180, 180] range.

    Args:
        longitude: Longitude value

    Returns:
        Normalized longitude
    """
    while longitude > 180:
        longitude -= 360
    while longitude < -180:
        longitude += 360
    return longitude


def normalize_latitude(latitude: float) -> float:
    """
    Clamp latitude to [-90, 90] range.

    Args:
        latitude: Latitude value

    Returns:
        Clamped latitude
    """
    return max(-90.0, min(90.0, latitude))
