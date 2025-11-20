"""
Heuristic Optimization Strategy

This module implements a simple heuristic approach for route optimization.
Uses Nearest Neighbor construction followed by 2-opt local search.
This serves as a fast fallback when OR-Tools fails or times out.
"""

import logging
import math
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime, timedelta, time, date

from .models import (
    OptimizationRequest,
    OptimizationResult,
    Route,
    Visit,
    Case,
    Vehicle,
    Personnel,
    Location,
    ConstraintViolation,
    ConstraintType,
    select_optimal_personnel
)

logger = logging.getLogger(__name__)


class HeuristicStrategy:
    """
    Heuristic optimization strategy using Nearest Neighbor + 2-opt.
    Simpler and faster than OR-Tools but may produce suboptimal solutions.
    """

    def __init__(self):
        self.request: Optional[OptimizationRequest] = None
        self.distance_matrix: Dict[Tuple[int, int], float] = {}
        self.time_matrix: Dict[Tuple[int, int], int] = {}

    def _get_date(self) -> date:
        """
        Safely extract date from request.date whether it's a datetime or date object
        """
        if isinstance(self.request.date, datetime):
            return self.request.date.date()
        return self.request.date

    def optimize(self, request: OptimizationRequest) -> OptimizationResult:
        """
        Execute heuristic optimization.

        Args:
            request: Optimization request with cases, vehicles, and personnel

        Returns:
            OptimizationResult with optimized routes
        """
        self.request = request
        start_time = datetime.now()

        try:
            logger.info(f"Starting heuristic optimization with {len(request.cases)} cases and {len(request.vehicles)} vehicles")

            # Build distance and time matrices
            self._build_matrices()

            # Initialize routes
            routes = []
            assigned_case_ids = set()  # Track assigned case IDs
            violations = []

            # Assign cases to vehicles using nearest neighbor
            for vehicle in request.vehicles:
                # Get unassigned cases
                available_cases = [c for c in request.cases if c.id not in assigned_case_ids]
                if not available_cases:
                    break

                # Build route for this vehicle (personnel will be selected inside based on assigned cases)
                route = self._build_route_for_vehicle(
                    vehicle,
                    request.personnel,
                    available_cases
                )

                if route and route.visits:
                    # Mark cases as assigned
                    for visit in route.visits:
                        assigned_case_ids.add(visit.case.id)

                    # Apply 2-opt improvement
                    route = self._improve_route_2opt(route)

                    routes.append(route)

            # Calculate totals
            total_distance = sum(r.total_distance for r in routes)
            total_time = sum(r.total_time for r in routes)

            # Find unassigned cases
            unassigned_cases = [c for c in request.cases if c.id not in assigned_case_ids]

            # Validate routes
            for route in routes:
                if not route.validate_skills():
                    violations.append(ConstraintViolation(
                        type=ConstraintType.SKILL_MISMATCH,
                        description=f"Route for vehicle {route.vehicle.identifier} lacks some required skills",
                        entity_id=route.vehicle.id,
                        entity_type="route",
                        severity="warning"  # Business reality: not all routes will have perfect skill coverage
                    ))

            optimization_time = (datetime.now() - start_time).total_seconds()
            success = len(unassigned_cases) == 0 and len(violations) == 0

            result = OptimizationResult(
                success=success,
                routes=routes,
                unassigned_cases=list(unassigned_cases),
                constraint_violations=violations,
                total_distance=total_distance,
                total_time=total_time,
                optimization_time=optimization_time,
                strategy_used="heuristic",
                message=f"Heuristic: {len(routes)} routes, {len(unassigned_cases)} unassigned cases"
            )

            logger.info(f"Heuristic optimization completed in {optimization_time:.2f}s: {result.get_summary()}")
            return result

        except Exception as e:
            logger.error(f"Heuristic optimization failed: {e}", exc_info=True)
            return OptimizationResult(
                success=False,
                routes=[],
                unassigned_cases=request.cases,
                constraint_violations=[
                    ConstraintViolation(
                        type=ConstraintType.INFEASIBLE,
                        description=f"Heuristic optimization failed: {str(e)}",
                        severity="error"
                    )
                ],
                optimization_time=(datetime.now() - start_time).total_seconds(),
                strategy_used="heuristic",
                message=f"Optimization error: {str(e)}"
            )

    def _build_matrices(self):
        """Build distance and time matrices"""
        # Use provided matrices or create them
        if self.request.distance_matrix:
            self.distance_matrix = self.request.distance_matrix
        else:
            # Build using Haversine distance
            self.distance_matrix = {}
            all_locations = (
                [v.base_location for v in self.request.vehicles] +
                [c.location for c in self.request.cases]
            )
            for i, loc1 in enumerate(all_locations):
                for j, loc2 in enumerate(all_locations):
                    if i != j:
                        self.distance_matrix[(i, j)] = self._haversine_distance(loc1, loc2)

        if self.request.time_matrix:
            self.time_matrix = self.request.time_matrix
        else:
            # Estimate time from distance (assume 40 km/h average)
            self.time_matrix = {}
            for (i, j), dist in self.distance_matrix.items():
                self.time_matrix[(i, j)] = int((dist / 40.0) * 60)  # minutes

    def _haversine_distance(self, loc1: Location, loc2: Location) -> float:
        """Calculate Haversine distance between two locations in km"""
        R = 6371  # Earth radius in km
        lat1, lon1 = math.radians(loc1.latitude), math.radians(loc1.longitude)
        lat2, lon2 = math.radians(loc2.latitude), math.radians(loc2.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    def _build_route_for_vehicle(
        self,
        vehicle: Vehicle,
        personnel: List[Personnel],
        available_cases: List[Case]
    ) -> Optional[Route]:
        """
        Build a route for a vehicle using nearest neighbor heuristic.

        Args:
            vehicle: The vehicle to route
            personnel: Available personnel
            available_cases: Cases that haven't been assigned yet

        Returns:
            Route or None if no feasible route
        """
        if not available_cases:
            return None

        # Get collective skills from personnel
        available_skills = set()
        for person in personnel:
            available_skills.update(person.skills)

        # Filter cases that can be served by this personnel team
        feasible_cases = [
            c for c in available_cases
            if set(c.required_skills).issubset(available_skills)
        ]

        if not feasible_cases:
            return None

        # Start from vehicle base location
        current_location = vehicle.base_location
        current_time = datetime.combine(self._get_date(), time(8, 0))  # Start at 8:00 AM
        work_end_time = datetime.combine(self._get_date(), time(17, 0))  # End at 5:00 PM

        visits = []
        remaining_cases = feasible_cases.copy()
        sequence = 0
        total_distance = 0.0
        total_time = 0

        # Nearest neighbor construction
        while remaining_cases and len(visits) < vehicle.capacity:
            # Find nearest feasible case
            best_case = None
            best_distance = float('inf')
            best_arrival_time = None

            for case in remaining_cases:
                # Calculate travel time and distance
                distance = self._haversine_distance(current_location, case.location)
                travel_time_minutes = int((distance / 40.0) * 60)  # Assume 40 km/h

                # Calculate arrival time
                arrival_time = current_time + timedelta(minutes=travel_time_minutes)

                # Check time window feasibility
                tw_start = datetime.combine(self._get_date(), case.time_window.start)
                tw_end = datetime.combine(self._get_date(), case.time_window.end)

                # Adjust arrival to time window start if we arrive early
                if arrival_time < tw_start:
                    arrival_time = tw_start

                # Check if we can complete the visit before time window ends and work ends
                end_time = arrival_time + timedelta(minutes=case.estimated_duration)

                if arrival_time <= tw_end and end_time <= work_end_time:
                    # Feasible case
                    if distance < best_distance:
                        best_distance = distance
                        best_case = case
                        best_arrival_time = arrival_time

            if best_case is None:
                # No more feasible cases
                break

            # Add visit to route
            start_time = best_arrival_time
            end_time = start_time + timedelta(minutes=best_case.estimated_duration)

            visit = Visit(
                case=best_case,
                sequence=sequence,
                arrival_time=best_arrival_time,
                start_time=start_time,
                end_time=end_time,
                travel_time_from_previous=int((best_distance / 40.0) * 60) if sequence > 0 else 0,
                distance_from_previous=best_distance if sequence > 0 else 0.0
            )

            visits.append(visit)
            remaining_cases.remove(best_case)

            # Update current position and time
            current_location = best_case.location
            current_time = end_time
            total_distance += best_distance
            total_time += visit.travel_time_from_previous + best_case.estimated_duration
            sequence += 1

        if not visits:
            return None

        # Select optimal personnel based on the cases actually assigned to this route
        assigned_cases = [visit.case for visit in visits]
        selected_personnel = select_optimal_personnel(
            available_personnel=personnel,
            cases=assigned_cases,
            vehicle_capacity=vehicle.capacity
        )

        return Route(
            vehicle=vehicle,
            personnel=selected_personnel,
            visits=visits,
            date=self.request.date,
            total_distance=total_distance,
            total_time=total_time
        )

    def _improve_route_2opt(self, route: Route) -> Route:
        """
        Improve a route using 2-opt local search.

        The 2-opt algorithm removes two edges and reconnects the route
        in a different way, if it reduces total distance.

        Args:
            route: Route to improve

        Returns:
            Improved route
        """
        if len(route.visits) < 3:
            # 2-opt requires at least 3 visits
            return route

        improved = True
        best_route = route

        # Maximum iterations to prevent infinite loop
        max_iterations = 100
        iteration = 0

        while improved and iteration < max_iterations:
            improved = False
            iteration += 1

            for i in range(1, len(best_route.visits) - 1):
                for j in range(i + 1, len(best_route.visits)):
                    # Try reversing the segment between i and j
                    new_visits = (
                        best_route.visits[:i] +
                        list(reversed(best_route.visits[i:j+1])) +
                        best_route.visits[j+1:]
                    )

                    # Recalculate route with new visit order
                    # Pass available personnel so it can reselect optimal set
                    new_route = self._recalculate_route(
                        best_route.vehicle,
                        self.request.personnel,
                        new_visits
                    )

                    # Check if new route is better and feasible
                    if (new_route and
                        new_route.total_distance < best_route.total_distance and
                        self._is_route_feasible(new_route)):
                        best_route = new_route
                        improved = True

        return best_route

    def _recalculate_route(
        self,
        vehicle: Vehicle,
        personnel: List[Personnel],
        visits: List[Visit]
    ) -> Optional[Route]:
        """Recalculate route metrics with new visit order"""
        current_location = vehicle.base_location
        current_time = datetime.combine(self._get_date(), time(8, 0))
        total_distance = 0.0
        total_time = 0

        updated_visits = []

        for seq, visit in enumerate(visits):
            # Calculate travel distance and time
            distance = self._haversine_distance(current_location, visit.case.location)
            travel_time = int((distance / 40.0) * 60)

            # Calculate arrival time
            arrival_time = current_time + timedelta(minutes=travel_time)

            # Check time window
            tw_start = datetime.combine(self._get_date(), visit.case.time_window.start)
            tw_end = datetime.combine(self._get_date(), visit.case.time_window.end)

            if arrival_time < tw_start:
                arrival_time = tw_start

            if arrival_time > tw_end:
                # Time window violation
                return None

            start_time = arrival_time
            end_time = start_time + timedelta(minutes=visit.case.estimated_duration)

            updated_visit = Visit(
                case=visit.case,
                sequence=seq,
                arrival_time=arrival_time,
                start_time=start_time,
                end_time=end_time,
                travel_time_from_previous=travel_time if seq > 0 else 0,
                distance_from_previous=distance if seq > 0 else 0.0
            )

            updated_visits.append(updated_visit)

            # Update for next iteration
            current_location = visit.case.location
            current_time = end_time
            total_distance += distance
            total_time += travel_time + visit.case.estimated_duration

        # Select optimal personnel based on the cases in this route
        assigned_cases = [visit.case for visit in updated_visits]
        selected_personnel = select_optimal_personnel(
            available_personnel=personnel,
            cases=assigned_cases,
            vehicle_capacity=vehicle.capacity
        )

        return Route(
            vehicle=vehicle,
            personnel=selected_personnel,
            visits=updated_visits,
            date=self.request.date,
            total_distance=total_distance,
            total_time=total_time
        )

    def _is_route_feasible(self, route: Route) -> bool:
        """Check if a route is feasible (time windows, capacity, working hours)"""
        if len(route.visits) > route.vehicle.capacity:
            return False

        work_end = datetime.combine(self._get_date(), time(17, 0))
        for visit in route.visits:
            if visit.end_time and visit.end_time > work_end:
                return False

        return True
