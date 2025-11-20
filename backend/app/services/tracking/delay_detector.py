"""
Delay Detection Service
Detects delays by comparing actual vs estimated times and generates alerts
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from dataclasses import dataclass
from enum import Enum

from app.models.route import Route, Visit, VisitStatus
from app.services.tracking.eta_calculator import ETACalculator
from app.core.exceptions import NotFoundError


class DelaySeverity(str, Enum):
    """Delay severity levels"""
    MINOR = "minor"          # 5-15 minutes
    MODERATE = "moderate"    # 15-30 minutes
    SEVERE = "severe"        # 30+ minutes


@dataclass
class DelayAlert:
    """Represents a delay alert"""
    visit_id: int
    route_id: int
    vehicle_id: int
    case_id: int
    severity: DelaySeverity
    delay_minutes: float
    estimated_arrival: Optional[datetime]
    current_eta: Optional[datetime]
    message: str
    detected_at: datetime


class DelayDetector:
    """Service for detecting and managing delays"""

    # Delay thresholds in minutes
    MINOR_THRESHOLD = 5
    MODERATE_THRESHOLD = 15
    SEVERE_THRESHOLD = 30

    # Check interval to avoid spam (5 minutes)
    CHECK_INTERVAL_MINUTES = 5

    def __init__(self, db: Session):
        self.db = db
        self.eta_calculator = ETACalculator(db)
        self._last_check = {}  # visit_id -> last_check_time

    def detect_delays_for_route(self, route_id: int) -> List[DelayAlert]:
        """
        Detect delays for all visits in a route

        Args:
            route_id: Route ID

        Returns:
            List of DelayAlert instances
        """
        route = self.db.query(Route).filter(Route.id == route_id).first()
        if not route:
            raise NotFoundError(f"Route with id {route_id} not found")

        alerts = []
        for visit in route.visits:
            # Only check active visits
            if visit.status in [VisitStatus.PENDING, VisitStatus.EN_ROUTE, VisitStatus.ARRIVED]:
                alert = self.check_visit_delay(visit.id, route.vehicle_id)
                if alert:
                    alerts.append(alert)

        return alerts

    def check_visit_delay(
        self,
        visit_id: int,
        vehicle_id: int,
        force: bool = False
    ) -> Optional[DelayAlert]:
        """
        Check if a specific visit is delayed

        Args:
            visit_id: Visit ID
            vehicle_id: Vehicle ID
            force: Force check even if recently checked

        Returns:
            DelayAlert if delayed, None otherwise
        """
        # Check if we recently checked this visit
        if not force and visit_id in self._last_check:
            last_check = self._last_check[visit_id]
            if (datetime.utcnow() - last_check).total_seconds() < (self.CHECK_INTERVAL_MINUTES * 60):
                return None

        # Get visit
        visit = self.db.query(Visit).filter(Visit.id == visit_id).first()
        if not visit:
            raise NotFoundError(f"Visit with id {visit_id} not found")

        # Can't detect delay without estimated arrival time
        if not visit.estimated_arrival_time:
            return None

        # Get current ETA
        eta_details = self.eta_calculator.calculate_eta_with_details(visit_id, vehicle_id)
        if not eta_details:
            return None

        delay_minutes = eta_details.get("delay_minutes")
        if delay_minutes is None or delay_minutes < self.MINOR_THRESHOLD:
            # Update last check time
            self._last_check[visit_id] = datetime.utcnow()
            return None

        # Determine severity
        severity = self._calculate_severity(delay_minutes)

        # Create alert
        alert = DelayAlert(
            visit_id=visit_id,
            route_id=visit.route_id,
            vehicle_id=vehicle_id,
            case_id=visit.case_id,
            severity=severity,
            delay_minutes=delay_minutes,
            estimated_arrival=visit.estimated_arrival_time,
            current_eta=datetime.fromisoformat(eta_details["eta"]),
            message=self._generate_delay_message(delay_minutes, severity),
            detected_at=datetime.utcnow()
        )

        # Update last check time
        self._last_check[visit_id] = datetime.utcnow()

        return alert

    def get_delay_statistics(self, route_id: int) -> Dict:
        """
        Get delay statistics for a route

        Args:
            route_id: Route ID

        Returns:
            Dictionary with delay statistics
        """
        route = self.db.query(Route).filter(Route.id == route_id).first()
        if not route:
            raise NotFoundError(f"Route with id {route_id} not found")

        stats = {
            "route_id": route_id,
            "total_visits": len(route.visits),
            "on_time": 0,
            "minor_delays": 0,
            "moderate_delays": 0,
            "severe_delays": 0,
            "average_delay_minutes": 0,
            "max_delay_minutes": 0
        }

        delays = []
        for visit in route.visits:
            if visit.status in [VisitStatus.COMPLETED]:
                # Check completed visits for historical delay
                delay = self._calculate_historical_delay(visit)
                if delay is not None:
                    delays.append(delay)

                    if delay < self.MINOR_THRESHOLD:
                        stats["on_time"] += 1
                    elif delay < self.MODERATE_THRESHOLD:
                        stats["minor_delays"] += 1
                    elif delay < self.SEVERE_THRESHOLD:
                        stats["moderate_delays"] += 1
                    else:
                        stats["severe_delays"] += 1

            elif visit.status in [VisitStatus.PENDING, VisitStatus.EN_ROUTE, VisitStatus.ARRIVED]:
                # Check current visits for predicted delay
                alert = self.check_visit_delay(visit.id, route.vehicle_id)
                if alert:
                    delays.append(alert.delay_minutes)

                    if alert.severity == DelaySeverity.MINOR:
                        stats["minor_delays"] += 1
                    elif alert.severity == DelaySeverity.MODERATE:
                        stats["moderate_delays"] += 1
                    else:
                        stats["severe_delays"] += 1
                else:
                    stats["on_time"] += 1

        # Calculate averages
        if delays:
            stats["average_delay_minutes"] = round(sum(delays) / len(delays), 1)
            stats["max_delay_minutes"] = round(max(delays), 1)

        return stats

    def check_time_window_violations(self, route_id: int) -> List[Dict]:
        """
        Check if any visits will violate their time windows

        Args:
            route_id: Route ID

        Returns:
            List of dictionaries with violation details
        """
        route = self.db.query(Route).filter(Route.id == route_id).first()
        if not route:
            raise NotFoundError(f"Route with id {route_id} not found")

        violations = []

        for visit in route.visits:
            if visit.status not in [VisitStatus.PENDING, VisitStatus.EN_ROUTE, VisitStatus.ARRIVED]:
                continue

            case = visit.case
            if not case.time_window_end or not visit.estimated_arrival_time:
                continue

            # Calculate current ETA
            eta_details = self.eta_calculator.calculate_eta_with_details(visit.id, route.vehicle_id)
            if not eta_details:
                continue

            current_eta = datetime.fromisoformat(eta_details["eta"])

            # Compare with time window end
            time_window_end = datetime.combine(
                route.route_date,
                case.time_window_end
            )

            if current_eta > time_window_end:
                minutes_over = (current_eta - time_window_end).total_seconds() / 60
                violations.append({
                    "visit_id": visit.id,
                    "case_id": case.id,
                    "patient_name": case.patient.name,
                    "time_window_end": time_window_end.isoformat(),
                    "current_eta": current_eta.isoformat(),
                    "minutes_over_window": round(minutes_over, 1),
                    "severity": "critical" if minutes_over > 30 else "warning"
                })

        return violations

    def _calculate_severity(self, delay_minutes: float) -> DelaySeverity:
        """
        Calculate delay severity based on minutes

        Args:
            delay_minutes: Delay in minutes

        Returns:
            DelaySeverity enum value
        """
        if delay_minutes >= self.SEVERE_THRESHOLD:
            return DelaySeverity.SEVERE
        elif delay_minutes >= self.MODERATE_THRESHOLD:
            return DelaySeverity.MODERATE
        else:
            return DelaySeverity.MINOR

    def _generate_delay_message(self, delay_minutes: float, severity: DelaySeverity) -> str:
        """
        Generate human-readable delay message in Spanish

        Args:
            delay_minutes: Delay in minutes
            severity: Delay severity

        Returns:
            Delay message string
        """
        rounded_delay = round(delay_minutes)

        if severity == DelaySeverity.SEVERE:
            return f"Retraso grave: {rounded_delay} minutos de demora. Se requiere acción inmediata."
        elif severity == DelaySeverity.MODERATE:
            return f"Retraso moderado: {rounded_delay} minutos de demora. Considere ajustar la ruta."
        else:
            return f"Retraso leve: {rounded_delay} minutos de demora."

    def _calculate_historical_delay(self, visit: Visit) -> Optional[float]:
        """
        Calculate delay for a completed visit

        Args:
            visit: Completed visit

        Returns:
            Delay in minutes or None
        """
        if not visit.actual_arrival_time or not visit.estimated_arrival_time:
            return None

        delay_seconds = (visit.actual_arrival_time - visit.estimated_arrival_time).total_seconds()
        return delay_seconds / 60

    def clear_check_cache(self):
        """Clear the last check cache"""
        self._last_check.clear()
