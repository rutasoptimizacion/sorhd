"""
Location Tracking Service
Handles GPS location storage, retrieval, and history management
"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from geoalchemy2.functions import ST_AsGeoJSON, ST_GeogFromText, ST_Distance
from geoalchemy2.elements import WKTElement
import json

from app.models.tracking import LocationLog
from app.models.vehicle import Vehicle
from app.core.exceptions import NotFoundError, ValidationError


class LocationTracker:
    """Service for tracking vehicle locations"""

    # Data retention period (90 days)
    RETENTION_DAYS = 90

    def __init__(self, db: Session):
        self.db = db

    def record_location(
        self,
        vehicle_id: int,
        latitude: float,
        longitude: float,
        speed_kmh: Optional[float] = None,
        heading_degrees: Optional[float] = None,
        accuracy_meters: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ) -> LocationLog:
        """
        Record a new GPS location for a vehicle

        Args:
            vehicle_id: ID of the vehicle
            latitude: Latitude coordinate (-90 to 90)
            longitude: Longitude coordinate (-180 to 180)
            speed_kmh: Vehicle speed in km/h (optional)
            heading_degrees: Vehicle heading in degrees (0-360, optional)
            accuracy_meters: GPS accuracy in meters (optional)
            timestamp: Location timestamp (defaults to now)

        Returns:
            Created LocationLog instance

        Raises:
            NotFoundError: If vehicle doesn't exist
            ValidationError: If coordinates are invalid
        """
        # Validate vehicle exists
        vehicle = self.db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            raise NotFoundError(f"Vehicle with id {vehicle_id} not found")

        # Validate coordinates
        self._validate_coordinates(latitude, longitude)

        # Validate optional parameters
        if speed_kmh is not None and speed_kmh < 0:
            raise ValidationError("Speed cannot be negative")

        if heading_degrees is not None and not (0 <= heading_degrees <= 360):
            raise ValidationError("Heading must be between 0 and 360 degrees")

        if accuracy_meters is not None and accuracy_meters < 0:
            raise ValidationError("Accuracy cannot be negative")

        # Create WKT Point for PostGIS
        point_wkt = f"POINT({longitude} {latitude})"

        # Create location log
        location_log = LocationLog(
            vehicle_id=vehicle_id,
            location=point_wkt,
            speed_kmh=speed_kmh,
            heading_degrees=heading_degrees,
            accuracy_meters=accuracy_meters,
            timestamp=timestamp or datetime.utcnow()
        )

        self.db.add(location_log)
        self.db.commit()
        self.db.refresh(location_log)

        return location_log

    def get_current_location(self, vehicle_id: int) -> Optional[LocationLog]:
        """
        Get the most recent location for a vehicle

        Args:
            vehicle_id: ID of the vehicle

        Returns:
            Most recent LocationLog or None if no locations recorded
        """
        return (
            self.db.query(LocationLog)
            .filter(LocationLog.vehicle_id == vehicle_id)
            .order_by(desc(LocationLog.timestamp))
            .first()
        )

    def get_location_history(
        self,
        vehicle_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[LocationLog]:
        """
        Get location history for a vehicle

        Args:
            vehicle_id: ID of the vehicle
            start_time: Start of time range (optional)
            end_time: End of time range (optional)
            limit: Maximum number of records to return

        Returns:
            List of LocationLog instances, ordered by timestamp descending
        """
        query = self.db.query(LocationLog).filter(LocationLog.vehicle_id == vehicle_id)

        if start_time:
            query = query.filter(LocationLog.timestamp >= start_time)

        if end_time:
            query = query.filter(LocationLog.timestamp <= end_time)

        return query.order_by(desc(LocationLog.timestamp)).limit(limit).all()

    def get_location_as_dict(self, location_log: LocationLog) -> dict:
        """
        Convert LocationLog to dictionary with extracted coordinates

        Args:
            location_log: LocationLog instance

        Returns:
            Dictionary with location data including lat/lng
        """
        # Extract coordinates from PostGIS Geography type
        geojson = self.db.scalar(ST_AsGeoJSON(location_log.location))
        coords = json.loads(geojson)["coordinates"]

        return {
            "id": location_log.id,
            "vehicle_id": location_log.vehicle_id,
            "latitude": coords[1],
            "longitude": coords[0],
            "speed_kmh": location_log.speed_kmh,
            "heading_degrees": location_log.heading_degrees,
            "accuracy_meters": location_log.accuracy_meters,
            "timestamp": location_log.timestamp.isoformat() if location_log.timestamp else None
        }

    def get_nearby_vehicles(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float = 5000,
        max_age_minutes: int = 10
    ) -> List[dict]:
        """
        Find vehicles near a location

        Args:
            latitude: Center point latitude
            longitude: Center point longitude
            radius_meters: Search radius in meters
            max_age_minutes: Maximum age of location data in minutes

        Returns:
            List of dictionaries with vehicle IDs and their distances
        """
        self._validate_coordinates(latitude, longitude)

        # Create point for query
        point_wkt = f"POINT({longitude} {latitude})"
        point = ST_GeogFromText(point_wkt)

        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)

        # Subquery to get most recent location per vehicle
        from sqlalchemy import func
        subquery = (
            self.db.query(
                LocationLog.vehicle_id,
                func.max(LocationLog.timestamp).label("max_timestamp")
            )
            .filter(LocationLog.timestamp >= cutoff_time)
            .group_by(LocationLog.vehicle_id)
            .subquery()
        )

        # Query for nearby vehicles
        results = (
            self.db.query(
                LocationLog,
                ST_Distance(LocationLog.location, point).label("distance")
            )
            .join(
                subquery,
                and_(
                    LocationLog.vehicle_id == subquery.c.vehicle_id,
                    LocationLog.timestamp == subquery.c.max_timestamp
                )
            )
            .filter(ST_Distance(LocationLog.location, point) <= radius_meters)
            .all()
        )

        nearby_vehicles = []
        for location_log, distance in results:
            location_dict = self.get_location_as_dict(location_log)
            location_dict["distance_meters"] = round(distance, 2)
            nearby_vehicles.append(location_dict)

        return nearby_vehicles

    def cleanup_old_locations(self, days: Optional[int] = None) -> int:
        """
        Delete location logs older than retention period

        Args:
            days: Number of days to retain (defaults to RETENTION_DAYS)

        Returns:
            Number of records deleted
        """
        retention_days = days or self.RETENTION_DAYS
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        deleted = (
            self.db.query(LocationLog)
            .filter(LocationLog.timestamp < cutoff_date)
            .delete()
        )

        self.db.commit()
        return deleted

    def _validate_coordinates(self, latitude: float, longitude: float):
        """
        Validate coordinate ranges

        Args:
            latitude: Latitude to validate
            longitude: Longitude to validate

        Raises:
            ValidationError: If coordinates are out of valid range
        """
        if not (-90 <= latitude <= 90):
            raise ValidationError(f"Latitude must be between -90 and 90, got {latitude}")

        if not (-180 <= longitude <= 180):
            raise ValidationError(f"Longitude must be between -180 and 180, got {longitude}")
