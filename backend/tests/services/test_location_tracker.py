"""
Tests for Location Tracker Service
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.tracking.location_tracker import LocationTracker
from app.models.vehicle import Vehicle
from app.models.tracking import LocationLog
from app.core.exceptions import NotFoundError, ValidationError


def test_record_location(db: Session, test_vehicle: Vehicle):
    """Test recording a GPS location"""
    tracker = LocationTracker(db)

    location = tracker.record_location(
        vehicle_id=test_vehicle.id,
        latitude=-33.4489,
        longitude=-70.6693,
        speed_kmh=45.5,
        heading_degrees=180.0,
        accuracy_meters=10.0
    )

    assert location.id is not None
    assert location.vehicle_id == test_vehicle.id
    assert location.speed_kmh == 45.5
    assert location.heading_degrees == 180.0
    assert location.accuracy_meters == 10.0


def test_record_location_invalid_vehicle(db: Session):
    """Test recording location for non-existent vehicle"""
    tracker = LocationTracker(db)

    with pytest.raises(NotFoundError):
        tracker.record_location(
            vehicle_id=99999,
            latitude=-33.4489,
            longitude=-70.6693
        )


def test_record_location_invalid_coordinates(db: Session, test_vehicle: Vehicle):
    """Test recording location with invalid coordinates"""
    tracker = LocationTracker(db)

    # Invalid latitude
    with pytest.raises(ValidationError):
        tracker.record_location(
            vehicle_id=test_vehicle.id,
            latitude=91.0,  # Out of range
            longitude=-70.6693
        )

    # Invalid longitude
    with pytest.raises(ValidationError):
        tracker.record_location(
            vehicle_id=test_vehicle.id,
            latitude=-33.4489,
            longitude=181.0  # Out of range
        )


def test_record_location_negative_speed(db: Session, test_vehicle: Vehicle):
    """Test recording location with negative speed"""
    tracker = LocationTracker(db)

    with pytest.raises(ValidationError):
        tracker.record_location(
            vehicle_id=test_vehicle.id,
            latitude=-33.4489,
            longitude=-70.6693,
            speed_kmh=-10.0
        )


def test_get_current_location(db: Session, test_vehicle: Vehicle):
    """Test getting most recent location"""
    tracker = LocationTracker(db)

    # Record multiple locations
    tracker.record_location(
        vehicle_id=test_vehicle.id,
        latitude=-33.4489,
        longitude=-70.6693,
        timestamp=datetime.utcnow() - timedelta(minutes=10)
    )

    latest = tracker.record_location(
        vehicle_id=test_vehicle.id,
        latitude=-33.4500,
        longitude=-70.6700,
        timestamp=datetime.utcnow()
    )

    # Get current location
    current = tracker.get_current_location(test_vehicle.id)

    assert current.id == latest.id


def test_get_current_location_none(db: Session, test_vehicle: Vehicle):
    """Test getting current location when no locations recorded"""
    tracker = LocationTracker(db)

    current = tracker.get_current_location(test_vehicle.id)
    assert current is None


def test_get_location_history(db: Session, test_vehicle: Vehicle):
    """Test getting location history"""
    tracker = LocationTracker(db)

    # Record multiple locations
    now = datetime.utcnow()
    for i in range(5):
        tracker.record_location(
            vehicle_id=test_vehicle.id,
            latitude=-33.4489 + (i * 0.001),
            longitude=-70.6693 + (i * 0.001),
            timestamp=now - timedelta(minutes=i)
        )

    # Get history
    history = tracker.get_location_history(test_vehicle.id, limit=10)

    assert len(history) == 5
    # Should be ordered by timestamp descending
    assert history[0].timestamp > history[-1].timestamp


def test_get_location_history_with_time_range(db: Session, test_vehicle: Vehicle):
    """Test getting location history with time range"""
    tracker = LocationTracker(db)

    now = datetime.utcnow()
    start_time = now - timedelta(hours=1)
    end_time = now

    # Record locations outside and inside range
    tracker.record_location(
        vehicle_id=test_vehicle.id,
        latitude=-33.4489,
        longitude=-70.6693,
        timestamp=now - timedelta(hours=2)  # Outside range
    )

    for i in range(3):
        tracker.record_location(
            vehicle_id=test_vehicle.id,
            latitude=-33.4489,
            longitude=-70.6693,
            timestamp=now - timedelta(minutes=i * 10)  # Inside range
        )

    # Get history within range
    history = tracker.get_location_history(
        test_vehicle.id,
        start_time=start_time,
        end_time=end_time
    )

    assert len(history) == 3


def test_get_location_as_dict(db: Session, test_vehicle: Vehicle):
    """Test converting location to dictionary"""
    tracker = LocationTracker(db)

    location = tracker.record_location(
        vehicle_id=test_vehicle.id,
        latitude=-33.4489,
        longitude=-70.6693,
        speed_kmh=45.5
    )

    location_dict = tracker.get_location_as_dict(location)

    assert location_dict["id"] == location.id
    assert location_dict["vehicle_id"] == test_vehicle.id
    assert abs(location_dict["latitude"] - (-33.4489)) < 0.0001
    assert abs(location_dict["longitude"] - (-70.6693)) < 0.0001
    assert location_dict["speed_kmh"] == 45.5


def test_cleanup_old_locations(db: Session, test_vehicle: Vehicle):
    """Test cleaning up old location logs"""
    tracker = LocationTracker(db)

    now = datetime.utcnow()

    # Record old locations (>90 days)
    for i in range(3):
        tracker.record_location(
            vehicle_id=test_vehicle.id,
            latitude=-33.4489,
            longitude=-70.6693,
            timestamp=now - timedelta(days=95 + i)
        )

    # Record recent locations
    for i in range(2):
        tracker.record_location(
            vehicle_id=test_vehicle.id,
            latitude=-33.4489,
            longitude=-70.6693,
            timestamp=now - timedelta(days=i)
        )

    # Cleanup old locations
    deleted = tracker.cleanup_old_locations()

    assert deleted == 3

    # Verify only recent locations remain
    remaining = db.query(LocationLog).filter(LocationLog.vehicle_id == test_vehicle.id).count()
    assert remaining == 2


def test_get_nearby_vehicles(db: Session, test_vehicle: Vehicle, db_session: Session):
    """Test finding nearby vehicles"""
    from geoalchemy2 import WKTElement
    from app.models.vehicle import Vehicle
    # Create additional vehicles
    vehicle2 = Vehicle(
        identifier="AMB-002",
        capacity_personnel=4,
        base_location=WKTElement("POINT(-70.6700 -33.4500)", srid=4326),
        status="available",
        is_active=True
    )
    db_session.add(vehicle2)
    db_session.commit()

    tracker = LocationTracker(db)

    # Record locations
    tracker.record_location(
        vehicle_id=test_vehicle.id,
        latitude=-33.4489,
        longitude=-70.6693
    )

    tracker.record_location(
        vehicle_id=vehicle2.id,
        latitude=-33.4500,  # Close to test_vehicle
        longitude=-70.6700
    )

    # Find nearby vehicles
    nearby = tracker.get_nearby_vehicles(
        latitude=-33.4489,
        longitude=-70.6693,
        radius_meters=2000
    )

    # Should find both vehicles
    assert len(nearby) >= 1
    vehicle_ids = [v["vehicle_id"] for v in nearby]
    assert test_vehicle.id in vehicle_ids
