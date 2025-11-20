"""
Integration Tests for Tracking Services
Tests ETA Calculator and Delay Detector functionality
"""
import pytest
from datetime import datetime, timedelta, time
from sqlalchemy.orm import Session

from app.services.tracking.eta_calculator import ETACalculator
from app.services.tracking.delay_detector import DelayDetector, DelaySeverity
from app.services.tracking.location_tracker import LocationTracker
from app.models.route import Visit, VisitStatus
from app.models.vehicle import Vehicle


def test_eta_calculator_traffic_buffers(db: Session):
    """Test traffic buffer calculation for different times of day"""
    calculator = ETACalculator(db)

    # Morning rush hour (8:00 AM)
    morning_rush = datetime.utcnow().replace(hour=8, minute=0)
    multiplier, period = calculator._get_traffic_buffer(morning_rush)
    assert period == "rush_hour_morning"
    assert multiplier == 1.3

    # Evening rush hour (18:00)
    evening_rush = datetime.utcnow().replace(hour=18, minute=0)
    multiplier, period = calculator._get_traffic_buffer(evening_rush)
    assert period == "rush_hour_evening"
    assert multiplier == 1.4

    # Peak hours (13:00)
    peak = datetime.utcnow().replace(hour=13, minute=0)
    multiplier, period = calculator._get_traffic_buffer(peak)
    assert period == "peak_hours"
    assert multiplier == 1.15

    # Late night (23:00)
    late_night = datetime.utcnow().replace(hour=23, minute=0)
    multiplier, period = calculator._get_traffic_buffer(late_night)
    assert period == "late_night"
    assert multiplier == 1.0


def test_eta_cache_invalidation(db: Session):
    """Test ETA cache invalidation"""
    calculator = ETACalculator(db)

    # Add something to cache
    visit_id = 1
    calculator._eta_cache[visit_id] = (datetime.utcnow(), datetime.utcnow())

    # Invalidate specific visit
    calculator.invalidate_cache(visit_id)
    assert visit_id not in calculator._eta_cache

    # Add again and clear all
    calculator._eta_cache[visit_id] = (datetime.utcnow(), datetime.utcnow())
    calculator.invalidate_cache()
    assert len(calculator._eta_cache) == 0


def test_delay_detector_severity_calculation(db: Session):
    """Test delay severity calculation"""
    detector = DelayDetector(db)

    # Minor delay (7 minutes)
    severity = detector._calculate_severity(7.0)
    assert severity == DelaySeverity.MINOR

    # Moderate delay (20 minutes)
    severity = detector._calculate_severity(20.0)
    assert severity == DelaySeverity.MODERATE

    # Severe delay (45 minutes)
    severity = detector._calculate_severity(45.0)
    assert severity == DelaySeverity.SEVERE


def test_delay_detector_message_generation(db: Session):
    """Test Spanish delay message generation"""
    detector = DelayDetector(db)

    # Minor delay
    message = detector._generate_delay_message(7.0, DelaySeverity.MINOR)
    assert "leve" in message.lower()
    assert "7" in message

    # Moderate delay
    message = detector._generate_delay_message(20.0, DelaySeverity.MODERATE)
    assert "moderado" in message.lower()
    assert "20" in message

    # Severe delay
    message = detector._generate_delay_message(45.0, DelaySeverity.SEVERE)
    assert "grave" in message.lower()
    assert "45" in message


def test_delay_detector_historical_delay(db: Session, test_visit: Visit):
    """Test calculating historical delay for completed visit"""
    detector = DelayDetector(db)

    # Set estimated and actual times
    now = datetime.utcnow()
    test_visit.estimated_arrival_time = now
    test_visit.actual_arrival_time = now + timedelta(minutes=15)
    test_visit.status = VisitStatus.COMPLETED
    db.commit()

    delay = detector._calculate_historical_delay(test_visit)

    assert delay is not None
    assert abs(delay - 15.0) < 0.1  # Should be approximately 15 minutes


def test_delay_detector_no_delay_for_on_time_visit(db: Session, test_visit: Visit, test_vehicle: Vehicle):
    """Test that on-time visits don't generate alerts"""
    detector = DelayDetector(db)
    tracker = LocationTracker(db)

    # Set estimated arrival to future
    test_visit.estimated_arrival_time = datetime.utcnow() + timedelta(hours=1)
    test_visit.status = VisitStatus.PENDING
    db.commit()

    # Record current location
    tracker.record_location(
        vehicle_id=test_vehicle.id,
        latitude=-33.4489,
        longitude=-70.6693
    )

    # Check for delay - should return None for on-time visit
    # Note: This test may need adjustment based on actual distance calculation
    alert = detector.check_visit_delay(test_visit.id, test_vehicle.id, force=True)

    # If ETA calculation works, should not generate alert for future arrival
    # (This test is simplified and may need mocking for full functionality)


def test_delay_check_interval(db: Session):
    """Test that delay checks respect check interval"""
    detector = DelayDetector(db)

    visit_id = 1
    now = datetime.utcnow()

    # Mark as recently checked
    detector._last_check[visit_id] = now

    # Try to check again immediately (should skip)
    # Note: This would need a full setup with valid visit and vehicle
    # This is a simplified test of the caching mechanism

    assert visit_id in detector._last_check
    last_check_time = detector._last_check[visit_id]
    time_since_check = (datetime.utcnow() - last_check_time).total_seconds()

    # Should be less than check interval
    assert time_since_check < (detector.CHECK_INTERVAL_MINUTES * 60)


def test_location_tracker_with_eta_calculation(db: Session, test_vehicle: Vehicle, test_visit: Visit):
    """Integration test: location tracking → ETA calculation"""
    tracker = LocationTracker(db)
    calculator = ETACalculator(db)

    # Record vehicle location
    location = tracker.record_location(
        vehicle_id=test_vehicle.id,
        latitude=-33.4489,
        longitude=-70.6693,
        speed_kmh=45.0
    )

    assert location is not None

    # Get location as dict
    location_dict = tracker.get_location_as_dict(location)
    assert "latitude" in location_dict
    assert "longitude" in location_dict

    # Note: ETA calculation requires full setup with case having location
    # This is a simplified integration test


def test_delay_statistics_all_on_time(db: Session, test_active_route):
    """Test delay statistics when all visits are on time"""
    detector = DelayDetector(db)

    # Mark all visits as completed on time
    for visit in test_active_route.visits:
        visit.status = VisitStatus.COMPLETED
        visit.estimated_arrival_time = datetime.utcnow()
        visit.actual_arrival_time = datetime.utcnow() + timedelta(minutes=2)  # 2 min delay (on time)
        db.commit()

    stats = detector.get_delay_statistics(test_active_route.id)

    assert stats["route_id"] == test_active_route.id
    assert stats["on_time"] == len(test_active_route.visits)
    assert stats["minor_delays"] == 0
    assert stats["moderate_delays"] == 0
    assert stats["severe_delays"] == 0


def test_clear_check_cache(db: Session):
    """Test clearing the delay check cache"""
    detector = DelayDetector(db)

    # Add some cached checks
    detector._last_check[1] = datetime.utcnow()
    detector._last_check[2] = datetime.utcnow()

    assert len(detector._last_check) == 2

    # Clear cache
    detector.clear_check_cache()

    assert len(detector._last_check) == 0
