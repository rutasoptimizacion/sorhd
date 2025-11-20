"""
ETA Calculator Service
Calculates estimated time of arrival based on current location and traffic conditions
"""
from datetime import datetime, timedelta, time
from typing import Optional, Tuple
from sqlalchemy.orm import Session
import json

from app.services.distance.models import Location, TravelTime
from app.services.distance.distance_service import DistanceService
from app.services.tracking.location_tracker import LocationTracker
from app.models.route import Visit
from app.models.case import Case
from app.core.exceptions import NotFoundError, ValidationError


class ETACalculator:
    """Service for calculating ETA with traffic buffers"""

    # Traffic buffer multipliers by time of day
    TRAFFIC_BUFFERS = {
        "rush_hour_morning": 1.3,    # 7:00-9:00
        "rush_hour_evening": 1.4,    # 17:00-19:00
        "peak_hours": 1.15,          # 12:00-14:00
        "normal": 1.05,              # All other times
        "late_night": 1.0            # 22:00-6:00
    }

    # ETA cache TTL (5 minutes)
    CACHE_TTL_SECONDS = 300

    # Significant change threshold (minutes)
    SIGNIFICANT_CHANGE_MINUTES = 10

    def __init__(self, db: Session):
        self.db = db
        self.location_tracker = LocationTracker(db)
        self.distance_service = DistanceService(db)
        self._eta_cache = {}  # Simple in-memory cache: visit_id -> (eta, timestamp)

    def calculate_eta(
        self,
        visit_id: int,
        vehicle_id: int,
        use_cache: bool = True
    ) -> Optional[datetime]:
        """
        Calculate ETA for a visit based on current vehicle location

        Args:
            visit_id: Visit ID
            vehicle_id: Vehicle ID
            use_cache: Whether to use cached ETA (default: True)

        Returns:
            Estimated arrival datetime or None if cannot calculate

        Raises:
            NotFoundError: If visit or vehicle not found
        """
        # Check cache
        if use_cache and visit_id in self._eta_cache:
            cached_eta, cached_time = self._eta_cache[visit_id]
            if (datetime.utcnow() - cached_time).seconds < self.CACHE_TTL_SECONDS:
                return cached_eta

        # Get visit
        visit = self.db.query(Visit).filter(Visit.id == visit_id).first()
        if not visit:
            raise NotFoundError(f"Visit with id {visit_id} not found")

        # Get current vehicle location
        current_location = self.location_tracker.get_current_location(vehicle_id)
        if not current_location:
            return None  # No location data available

        # Extract vehicle coordinates
        location_dict = self.location_tracker.get_location_as_dict(current_location)
        vehicle_lat = location_dict["latitude"]
        vehicle_lng = location_dict["longitude"]

        # Get destination from case
        case = visit.case
        destination_coords = self._extract_coordinates_from_case(case)
        if not destination_coords:
            return None

        dest_lat, dest_lng = destination_coords

        # Calculate travel time using distance service
        origin = Location(latitude=vehicle_lat, longitude=vehicle_lng)
        destination = Location(latitude=dest_lat, longitude=dest_lng)

        try:
            travel_time = self.distance_service.get_travel_time(origin, destination)
        except Exception:
            # If distance service fails, return None
            return None

        # Apply traffic buffer
        buffered_duration = self._apply_traffic_buffer(
            travel_time.duration_seconds,
            current_location.timestamp or datetime.utcnow()
        )

        # Calculate ETA
        eta = (current_location.timestamp or datetime.utcnow()) + timedelta(seconds=buffered_duration)

        # Cache the result
        self._eta_cache[visit_id] = (eta, datetime.utcnow())

        return eta

    def calculate_eta_with_details(
        self,
        visit_id: int,
        vehicle_id: int
    ) -> Optional[dict]:
        """
        Calculate ETA with detailed information

        Args:
            visit_id: Visit ID
            vehicle_id: Vehicle ID

        Returns:
            Dictionary with ETA details or None
        """
        # Get visit
        visit = self.db.query(Visit).filter(Visit.id == visit_id).first()
        if not visit:
            raise NotFoundError(f"Visit with id {visit_id} not found")

        # Get current vehicle location
        current_location = self.location_tracker.get_current_location(vehicle_id)
        if not current_location:
            return None

        # Extract coordinates
        location_dict = self.location_tracker.get_location_as_dict(current_location)
        vehicle_lat = location_dict["latitude"]
        vehicle_lng = location_dict["longitude"]

        case = visit.case
        destination_coords = self._extract_coordinates_from_case(case)
        if not destination_coords:
            return None

        dest_lat, dest_lng = destination_coords

        # Calculate travel time
        origin = Location(latitude=vehicle_lat, longitude=vehicle_lng)
        destination = Location(latitude=dest_lat, longitude=dest_lng)

        try:
            travel_time = self.distance_service.get_travel_time(origin, destination)
        except Exception:
            return None

        # Get traffic buffer info
        traffic_multiplier, traffic_period = self._get_traffic_buffer()
        buffered_duration = travel_time.duration_seconds * traffic_multiplier

        # Calculate ETA
        current_time = current_location.timestamp or datetime.utcnow()
        eta = current_time + timedelta(seconds=buffered_duration)

        # Check for significant delay vs estimated time
        delay_minutes = None
        if visit.estimated_arrival_time:
            delay_minutes = (eta - visit.estimated_arrival_time).total_seconds() / 60

        return {
            "visit_id": visit_id,
            "vehicle_id": vehicle_id,
            "current_location": {
                "latitude": vehicle_lat,
                "longitude": vehicle_lng,
                "timestamp": current_time.isoformat()
            },
            "destination": {
                "latitude": dest_lat,
                "longitude": dest_lng
            },
            "distance_km": round(travel_time.distance_km, 2),
            "base_duration_minutes": round(travel_time.duration_minutes, 1),
            "traffic_multiplier": traffic_multiplier,
            "traffic_period": traffic_period,
            "buffered_duration_minutes": round(buffered_duration / 60, 1),
            "eta": eta.isoformat(),
            "estimated_arrival_time": visit.estimated_arrival_time.isoformat() if visit.estimated_arrival_time else None,
            "delay_minutes": round(delay_minutes, 1) if delay_minutes is not None else None,
            "is_delayed": delay_minutes > 5 if delay_minutes is not None else False
        }

    def check_significant_eta_change(
        self,
        visit_id: int,
        vehicle_id: int
    ) -> Tuple[bool, Optional[float]]:
        """
        Check if ETA has changed significantly from cached value

        Args:
            visit_id: Visit ID
            vehicle_id: Vehicle ID

        Returns:
            Tuple of (has_changed, change_in_minutes)
        """
        # Get cached ETA
        if visit_id not in self._eta_cache:
            # No cached value, calculate new one
            new_eta = self.calculate_eta(visit_id, vehicle_id, use_cache=False)
            return (True, None) if new_eta else (False, None)

        cached_eta, _ = self._eta_cache[visit_id]

        # Calculate new ETA without cache
        new_eta = self.calculate_eta(visit_id, vehicle_id, use_cache=False)

        if not new_eta:
            return (False, None)

        # Calculate difference
        change_minutes = (new_eta - cached_eta).total_seconds() / 60

        # Check if significant
        is_significant = abs(change_minutes) >= self.SIGNIFICANT_CHANGE_MINUTES

        return (is_significant, change_minutes)

    def invalidate_cache(self, visit_id: Optional[int] = None):
        """
        Invalidate ETA cache

        Args:
            visit_id: Specific visit ID to invalidate, or None for all
        """
        if visit_id:
            self._eta_cache.pop(visit_id, None)
        else:
            self._eta_cache.clear()

    def _apply_traffic_buffer(
        self,
        base_duration_seconds: float,
        current_time: datetime
    ) -> float:
        """
        Apply traffic buffer based on time of day

        Args:
            base_duration_seconds: Base travel duration
            current_time: Current datetime

        Returns:
            Buffered duration in seconds
        """
        multiplier, _ = self._get_traffic_buffer(current_time)
        return base_duration_seconds * multiplier

    def _get_traffic_buffer(
        self,
        current_time: Optional[datetime] = None
    ) -> Tuple[float, str]:
        """
        Get traffic buffer multiplier for current time

        Args:
            current_time: Datetime to check (defaults to now)

        Returns:
            Tuple of (multiplier, period_name)
        """
        if not current_time:
            current_time = datetime.utcnow()

        current_hour = current_time.hour
        current_minute = current_time.minute
        current_time_minutes = current_hour * 60 + current_minute

        # Late night (22:00-6:00)
        if current_hour >= 22 or current_hour < 6:
            return (self.TRAFFIC_BUFFERS["late_night"], "late_night")

        # Morning rush hour (7:00-9:00)
        if 7 * 60 <= current_time_minutes < 9 * 60:
            return (self.TRAFFIC_BUFFERS["rush_hour_morning"], "rush_hour_morning")

        # Evening rush hour (17:00-19:00)
        if 17 * 60 <= current_time_minutes < 19 * 60:
            return (self.TRAFFIC_BUFFERS["rush_hour_evening"], "rush_hour_evening")

        # Peak hours (12:00-14:00)
        if 12 * 60 <= current_time_minutes < 14 * 60:
            return (self.TRAFFIC_BUFFERS["peak_hours"], "peak_hours")

        # Normal hours
        return (self.TRAFFIC_BUFFERS["normal"], "normal")

    def _extract_coordinates_from_case(self, case: Case) -> Optional[Tuple[float, float]]:
        """
        Extract latitude and longitude from case location

        Args:
            case: Case instance

        Returns:
            Tuple of (latitude, longitude) or None
        """
        if not case.location:
            return None

        try:
            # Case location is stored as PostGIS Geography
            from geoalchemy2.functions import ST_AsGeoJSON
            geojson = self.db.scalar(ST_AsGeoJSON(case.location))
            coords = json.loads(geojson)["coordinates"]
            return (coords[1], coords[0])  # (lat, lng)
        except Exception:
            return None
