"""
Route Tracker Service
Handles active route tracking, visit status updates, and completion detection
"""
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.route import Route, Visit, RouteStatus, VisitStatus
from app.models.case import Case, CaseStatus
from app.core.exceptions import NotFoundError, ValidationError


class RouteTrackerService:
    """Service for tracking route execution and visit status"""

    # Valid status transitions for visits
    VALID_VISIT_TRANSITIONS = {
        VisitStatus.PENDING: [VisitStatus.EN_ROUTE, VisitStatus.CANCELLED],
        VisitStatus.EN_ROUTE: [VisitStatus.ARRIVED, VisitStatus.CANCELLED],
        VisitStatus.ARRIVED: [VisitStatus.IN_PROGRESS, VisitStatus.CANCELLED],
        VisitStatus.IN_PROGRESS: [VisitStatus.COMPLETED, VisitStatus.FAILED],
        VisitStatus.COMPLETED: [],  # Terminal state
        VisitStatus.CANCELLED: [],  # Terminal state
        VisitStatus.FAILED: [],     # Terminal state
    }

    def __init__(self, db: Session):
        self.db = db

    def get_active_routes(
        self,
        route_date: Optional[date] = None,
        vehicle_id: Optional[int] = None
    ) -> List[Route]:
        """
        Get all active routes (ACTIVE or IN_PROGRESS status)

        Args:
            route_date: Filter by specific date (optional)
            vehicle_id: Filter by vehicle ID (optional)

        Returns:
            List of active Route instances
        """
        query = self.db.query(Route).filter(
            Route.status.in_([RouteStatus.ACTIVE, RouteStatus.IN_PROGRESS])
        )

        if route_date:
            query = query.filter(Route.route_date == route_date)

        if vehicle_id:
            query = query.filter(Route.vehicle_id == vehicle_id)

        return query.all()

    def get_route_by_id(self, route_id: int) -> Route:
        """
        Get route by ID

        Args:
            route_id: Route ID

        Returns:
            Route instance

        Raises:
            NotFoundError: If route not found
        """
        route = self.db.query(Route).filter(Route.id == route_id).first()
        if not route:
            raise NotFoundError(f"Route with id {route_id} not found")
        return route

    def get_active_route_for_vehicle(self, vehicle_id: int) -> Optional[Route]:
        """
        Get the current active route for a vehicle

        Args:
            vehicle_id: Vehicle ID

        Returns:
            Active Route instance or None
        """
        return (
            self.db.query(Route)
            .filter(
                and_(
                    Route.vehicle_id == vehicle_id,
                    Route.status.in_([RouteStatus.ACTIVE, RouteStatus.IN_PROGRESS])
                )
            )
            .first()
        )

    def update_visit_status(
        self,
        visit_id: int,
        new_status: VisitStatus,
        notes: Optional[str] = None
    ) -> Visit:
        """
        Update visit status with validation

        Args:
            visit_id: Visit ID
            new_status: New status to set
            notes: Optional notes about the status change

        Returns:
            Updated Visit instance

        Raises:
            NotFoundError: If visit not found
            ValidationError: If status transition is invalid
        """
        # Get visit
        visit = self.db.query(Visit).filter(Visit.id == visit_id).first()
        if not visit:
            raise NotFoundError(f"Visit with id {visit_id} not found")

        # Validate status transition
        current_status = visit.status
        if not self._is_valid_transition(current_status, new_status):
            raise ValidationError(
                f"Invalid status transition from {current_status.value} to {new_status.value}"
            )

        # Update status and timestamps
        visit.status = new_status

        if notes:
            visit.notes = notes

        # Update timestamps based on status
        now = datetime.utcnow()

        if new_status == VisitStatus.ARRIVED:
            visit.actual_arrival_time = now
        elif new_status == VisitStatus.COMPLETED:
            if not visit.actual_departure_time:
                visit.actual_departure_time = now

        self.db.commit()
        self.db.refresh(visit)

        # Update associated case status
        self._update_case_status_from_visit(visit)

        # Check if route should be updated
        self._check_route_completion(visit.route_id)

        # Mark route as in_progress if first visit started
        if new_status == VisitStatus.EN_ROUTE:
            route = visit.route
            if route.status == RouteStatus.ACTIVE:
                route.status = RouteStatus.IN_PROGRESS
                self.db.commit()

        return visit

    def get_next_pending_visit(self, route_id: int) -> Optional[Visit]:
        """
        Get the next pending visit in a route

        Args:
            route_id: Route ID

        Returns:
            Next pending Visit or None
        """
        return (
            self.db.query(Visit)
            .filter(
                and_(
                    Visit.route_id == route_id,
                    Visit.status == VisitStatus.PENDING
                )
            )
            .order_by(Visit.sequence_number)
            .first()
        )

    def get_current_visit(self, route_id: int) -> Optional[Visit]:
        """
        Get the currently active visit (EN_ROUTE, ARRIVED, or IN_PROGRESS)

        Args:
            route_id: Route ID

        Returns:
            Current Visit or None
        """
        return (
            self.db.query(Visit)
            .filter(
                and_(
                    Visit.route_id == route_id,
                    Visit.status.in_([
                        VisitStatus.EN_ROUTE,
                        VisitStatus.ARRIVED,
                        VisitStatus.IN_PROGRESS
                    ])
                )
            )
            .order_by(Visit.sequence_number)
            .first()
        )

    def get_route_progress(self, route_id: int) -> dict:
        """
        Get route progress statistics

        Args:
            route_id: Route ID

        Returns:
            Dictionary with progress statistics
        """
        route = self.get_route_by_id(route_id)
        visits = route.visits

        total_visits = len(visits)
        completed = sum(1 for v in visits if v.status == VisitStatus.COMPLETED)
        in_progress = sum(1 for v in visits if v.status == VisitStatus.IN_PROGRESS)
        failed = sum(1 for v in visits if v.status == VisitStatus.FAILED)
        cancelled = sum(1 for v in visits if v.status == VisitStatus.CANCELLED)

        return {
            "route_id": route_id,
            "total_visits": total_visits,
            "completed": completed,
            "in_progress": in_progress,
            "failed": failed,
            "cancelled": cancelled,
            "pending": total_visits - completed - in_progress - failed - cancelled,
            "completion_percentage": round((completed / total_visits * 100), 2) if total_visits > 0 else 0
        }

    def _is_valid_transition(
        self,
        current_status: VisitStatus,
        new_status: VisitStatus
    ) -> bool:
        """
        Check if status transition is valid

        Args:
            current_status: Current visit status
            new_status: Desired new status

        Returns:
            True if transition is valid
        """
        if current_status == new_status:
            return True

        allowed_transitions = self.VALID_VISIT_TRANSITIONS.get(current_status, [])
        return new_status in allowed_transitions

    def _update_case_status_from_visit(self, visit: Visit):
        """
        Update case status based on visit status

        Args:
            visit: Visit instance
        """
        case = visit.case

        if visit.status == VisitStatus.COMPLETED:
            case.status = CaseStatus.COMPLETED
        elif visit.status == VisitStatus.FAILED:
            case.status = CaseStatus.FAILED
        elif visit.status == VisitStatus.CANCELLED:
            case.status = CaseStatus.CANCELLED
        elif visit.status in [VisitStatus.EN_ROUTE, VisitStatus.ARRIVED, VisitStatus.IN_PROGRESS]:
            case.status = CaseStatus.IN_PROGRESS

        self.db.commit()

    def _check_route_completion(self, route_id: int):
        """
        Check if all visits in route are complete and update route status

        Args:
            route_id: Route ID
        """
        route = self.get_route_by_id(route_id)

        # Check if all visits are in terminal state
        all_complete = all(
            visit.status in [
                VisitStatus.COMPLETED,
                VisitStatus.FAILED,
                VisitStatus.CANCELLED
            ]
            for visit in route.visits
        )

        if all_complete and route.status == RouteStatus.IN_PROGRESS:
            route.status = RouteStatus.COMPLETED
            self.db.commit()

    def cancel_route(self, route_id: int, reason: Optional[str] = None) -> Route:
        """
        Cancel a route and all pending visits

        Args:
            route_id: Route ID
            reason: Cancellation reason

        Returns:
            Updated Route instance

        Raises:
            NotFoundError: If route not found
            ValidationError: If route cannot be cancelled
        """
        route = self.get_route_by_id(route_id)

        if route.status == RouteStatus.COMPLETED:
            raise ValidationError("Cannot cancel a completed route")

        # Cancel all non-terminal visits
        for visit in route.visits:
            if visit.status not in [VisitStatus.COMPLETED, VisitStatus.FAILED, VisitStatus.CANCELLED]:
                visit.status = VisitStatus.CANCELLED
                if reason:
                    visit.notes = f"Route cancelled: {reason}"

        route.status = RouteStatus.CANCELLED
        self.db.commit()
        self.db.refresh(route)

        return route
