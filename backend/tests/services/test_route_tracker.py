"""
Tests for Route Tracker Service
"""
import pytest
from datetime import datetime, date
from sqlalchemy.orm import Session

from app.services.tracking.route_tracker import RouteTrackerService
from app.models.route import Route, Visit, RouteStatus, VisitStatus
from app.models.case import CaseStatus
from app.core.exceptions import NotFoundError, ValidationError


def test_get_active_routes(db: Session, test_active_route: Route):
    """Test getting active routes"""
    tracker = RouteTrackerService(db)

    active_routes = tracker.get_active_routes()

    assert len(active_routes) >= 1
    route_ids = [r.id for r in active_routes]
    assert test_active_route.id in route_ids


def test_get_active_routes_by_date(db: Session, test_active_route: Route):
    """Test filtering active routes by date"""
    tracker = RouteTrackerService(db)

    routes = tracker.get_active_routes(route_date=test_active_route.route_date)

    assert len(routes) >= 1
    assert all(r.route_date == test_active_route.route_date for r in routes)


def test_get_active_routes_by_vehicle(db: Session, test_active_route: Route):
    """Test filtering active routes by vehicle"""
    tracker = RouteTrackerService(db)

    routes = tracker.get_active_routes(vehicle_id=test_active_route.vehicle_id)

    assert len(routes) >= 1
    assert all(r.vehicle_id == test_active_route.vehicle_id for r in routes)


def test_get_route_by_id(db: Session, test_active_route: Route):
    """Test getting route by ID"""
    tracker = RouteTrackerService(db)

    route = tracker.get_route_by_id(test_active_route.id)

    assert route.id == test_active_route.id


def test_get_route_by_id_not_found(db: Session):
    """Test getting non-existent route"""
    tracker = RouteTrackerService(db)

    with pytest.raises(NotFoundError):
        tracker.get_route_by_id(99999)


def test_get_active_route_for_vehicle(db: Session, test_active_route: Route):
    """Test getting active route for specific vehicle"""
    tracker = RouteTrackerService(db)

    route = tracker.get_active_route_for_vehicle(test_active_route.vehicle_id)

    assert route is not None
    assert route.id == test_active_route.id


def test_update_visit_status_to_en_route(db: Session, test_visit: Visit):
    """Test updating visit status to EN_ROUTE"""
    tracker = RouteTrackerService(db)

    # Ensure visit is pending
    test_visit.status = VisitStatus.PENDING
    db.commit()

    # Update to EN_ROUTE
    updated = tracker.update_visit_status(
        test_visit.id,
        VisitStatus.EN_ROUTE,
        notes="En camino al paciente"
    )

    assert updated.status == VisitStatus.EN_ROUTE
    assert updated.notes == "En camino al paciente"


def test_update_visit_status_to_arrived(db: Session, test_visit: Visit):
    """Test updating visit status to ARRIVED"""
    tracker = RouteTrackerService(db)

    # Set to EN_ROUTE first
    test_visit.status = VisitStatus.EN_ROUTE
    db.commit()

    # Update to ARRIVED
    updated = tracker.update_visit_status(
        test_visit.id,
        VisitStatus.ARRIVED
    )

    assert updated.status == VisitStatus.ARRIVED
    assert updated.actual_arrival_time is not None


def test_update_visit_status_to_completed(db: Session, test_visit: Visit):
    """Test updating visit status to COMPLETED"""
    tracker = RouteTrackerService(db)

    # Set to IN_PROGRESS first
    test_visit.status = VisitStatus.IN_PROGRESS
    db.commit()

    # Update to COMPLETED
    updated = tracker.update_visit_status(
        test_visit.id,
        VisitStatus.COMPLETED
    )

    assert updated.status == VisitStatus.COMPLETED
    assert updated.actual_departure_time is not None

    # Case should also be completed
    db.refresh(test_visit.case)
    assert test_visit.case.status == CaseStatus.COMPLETED


def test_update_visit_status_invalid_transition(db: Session, test_visit: Visit):
    """Test invalid status transition"""
    tracker = RouteTrackerService(db)

    # Try to go from PENDING to COMPLETED (invalid)
    test_visit.status = VisitStatus.PENDING
    db.commit()

    with pytest.raises(ValidationError):
        tracker.update_visit_status(
            test_visit.id,
            VisitStatus.COMPLETED
        )


def test_update_visit_status_not_found(db: Session):
    """Test updating non-existent visit"""
    tracker = RouteTrackerService(db)

    with pytest.raises(NotFoundError):
        tracker.update_visit_status(99999, VisitStatus.COMPLETED)


def test_get_next_pending_visit(db: Session, test_active_route: Route):
    """Test getting next pending visit"""
    tracker = RouteTrackerService(db)

    # Ensure route has pending visits
    if test_active_route.visits:
        test_active_route.visits[0].status = VisitStatus.PENDING
        db.commit()

    next_visit = tracker.get_next_pending_visit(test_active_route.id)

    if test_active_route.visits:
        assert next_visit is not None
        assert next_visit.status == VisitStatus.PENDING


def test_get_current_visit(db: Session, test_active_route: Route):
    """Test getting current active visit"""
    tracker = RouteTrackerService(db)

    # Set first visit to EN_ROUTE
    if test_active_route.visits:
        test_active_route.visits[0].status = VisitStatus.EN_ROUTE
        db.commit()

        current = tracker.get_current_visit(test_active_route.id)

        assert current is not None
        assert current.status in [VisitStatus.EN_ROUTE, VisitStatus.ARRIVED, VisitStatus.IN_PROGRESS]


def test_get_route_progress(db: Session, test_active_route: Route):
    """Test getting route progress statistics"""
    tracker = RouteTrackerService(db)

    progress = tracker.get_route_progress(test_active_route.id)

    assert "route_id" in progress
    assert "total_visits" in progress
    assert "completed" in progress
    assert "pending" in progress
    assert "completion_percentage" in progress
    assert progress["route_id"] == test_active_route.id


def test_route_completion_detection(db: Session, test_active_route: Route):
    """Test automatic route completion when all visits complete"""
    tracker = RouteTrackerService(db)

    # Mark route as IN_PROGRESS
    test_active_route.status = RouteStatus.IN_PROGRESS
    db.commit()

    # Complete all visits
    for visit in test_active_route.visits:
        visit.status = VisitStatus.IN_PROGRESS
        db.commit()

        tracker.update_visit_status(visit.id, VisitStatus.COMPLETED)

    # Route should now be completed
    db.refresh(test_active_route)
    assert test_active_route.status == RouteStatus.COMPLETED


def test_cancel_route(db: Session, test_active_route: Route):
    """Test cancelling a route"""
    tracker = RouteTrackerService(db)

    cancelled = tracker.cancel_route(
        test_active_route.id,
        reason="Vehículo averiado"
    )

    assert cancelled.status == RouteStatus.CANCELLED

    # All non-terminal visits should be cancelled
    for visit in cancelled.visits:
        if visit.status not in [VisitStatus.COMPLETED, VisitStatus.FAILED]:
            assert visit.status == VisitStatus.CANCELLED
            assert "Vehículo averiado" in (visit.notes or "")


def test_cancel_completed_route(db: Session, test_active_route: Route):
    """Test that completed routes cannot be cancelled"""
    tracker = RouteTrackerService(db)

    # Mark route as completed
    test_active_route.status = RouteStatus.COMPLETED
    db.commit()

    with pytest.raises(ValidationError):
        tracker.cancel_route(test_active_route.id)


def test_route_status_updates_to_in_progress(db: Session, test_active_route: Route):
    """Test route automatically updates to IN_PROGRESS when first visit starts"""
    tracker = RouteTrackerService(db)

    # Ensure route is ACTIVE
    test_active_route.status = RouteStatus.ACTIVE
    db.commit()

    # Start first visit
    if test_active_route.visits:
        test_active_route.visits[0].status = VisitStatus.PENDING
        db.commit()

        tracker.update_visit_status(
            test_active_route.visits[0].id,
            VisitStatus.EN_ROUTE
        )

        # Route should now be IN_PROGRESS
        db.refresh(test_active_route)
        assert test_active_route.status == RouteStatus.IN_PROGRESS
