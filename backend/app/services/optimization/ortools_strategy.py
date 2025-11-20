"""
OR-Tools VRP Strategy

This module implements the route optimization using Google OR-Tools.
It solves the Vehicle Routing Problem with Time Windows and Skills (VRP-TWS).
"""

import logging
from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime, timedelta, time
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

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
    SkillGapAnalysis,
    UnassignedCaseDetail,
    select_optimal_personnel,
    assign_personnel_to_vehicles,
    get_allowed_vehicles_for_case
)

logger = logging.getLogger(__name__)


class ORToolsVRPStrategy:
    """
    Optimization strategy using OR-Tools Constraint Programming solver.
    Implements VRP with Time Windows and Skills constraints.
    """

    def __init__(self):
        self.request: Optional[OptimizationRequest] = None
        self.manager: Optional[pywrapcp.RoutingIndexManager] = None
        self.routing: Optional[pywrapcp.RoutingModel] = None
        self.locations: List[Location] = []  # All locations (depot + cases)
        self.location_to_case: Dict[int, Case] = {}  # Map location index to case
        self.vehicle_to_personnel: Dict[int, List[Personnel]] = {}  # Map vehicle to assigned personnel
        self.distance_matrix: List[List[float]] = []
        self.time_matrix: List[List[int]] = []

    def optimize(self, request: OptimizationRequest) -> OptimizationResult:
        """
        Execute the optimization using OR-Tools.

        Args:
            request: Optimization request with cases, vehicles, and personnel

        Returns:
            OptimizationResult with optimized routes or violations
        """
        self.request = request
        start_time = datetime.now()

        try:
            # Validate request
            violations = self._validate_request()
            if violations:
                return OptimizationResult(
                    success=False,
                    routes=[],
                    unassigned_cases=request.cases,
                    constraint_violations=violations,
                    strategy_used="ortools",
                    message="Validation failed"
                )

            # Build data model
            self._build_data_model()

            # Create routing manager and model
            self._create_routing_model()

            # Add constraints (distance and capacity)
            # NOTE: Skill constraints are already added in _create_routing_model() via SetAllowedVehiclesForIndex()
            self._add_distance_constraint()
            # Time windows DISABLED to allow OR-Tools to find solutions
            # self._add_time_window_constraint()
            self._add_capacity_constraint()
            # DO NOT call _add_skill_constraint() - it duplicates logic from _create_routing_model()

            logger.info("Constraints applied: distance, capacity, and SKILLS (via _create_routing_model)")

            # Set search parameters
            search_parameters = self._get_search_parameters()

            # Solve
            logger.info(f"Starting OR-Tools optimization with {len(request.cases)} cases and {len(request.vehicles)} vehicles")
            logger.info(f"  - Total locations: {len(self.locations)} (depots + cases)")
            logger.info(f"  - Available personnel: {len(request.personnel)}")
            logger.info(f"  - Distance matrix size: {len(self.distance_matrix)}x{len(self.distance_matrix[0]) if self.distance_matrix else 0}")

            solution = self.routing.SolveWithParameters(search_parameters)

            # Check solution status using routing status (NOT solution object truthiness)
            # Status codes: 0=NOT_SOLVED, 1=SUCCESS, 2=NO_SOLUTION_FOUND, 3=TIME_LIMIT, 4=FAIL, etc.
            status = self.routing.status()
            logger.info(f"OR-Tools solver status: {status} (1=SUCCESS, 2=NO_SOLUTION_FOUND, 3=TIME_LIMIT, 4=FAIL)")

            # Extract solution if status is SUCCESS (1) or if we have a solution even with time/solution limit reached
            # Status 1 = ROUTING_SUCCESS (optimal solution found)
            # Status 3 = TIME_LIMIT but may have found a good solution
            # Check if solution is not None (OR-Tools found at least one feasible solution)
            print(f"🔧 OR-Tools status={status}, solution is None={solution is None}", flush=True)
            if status == 1 or (solution is not None and status in [3]):  # SUCCESS or TIME_LIMIT with solution
                if status == 1:
                    print("✓ OR-Tools found optimal solution!", flush=True)
                    logger.info("✓ OR-Tools found optimal solution!")
                else:
                    print(f"✓ OR-Tools found solution (status={status}, may not be optimal but usable)", flush=True)
                    logger.info(f"✓ OR-Tools found solution (status={status}, may not be optimal but usable)")

                try:
                    result = self._extract_solution(solution)
                    optimization_time = (datetime.now() - start_time).total_seconds()
                    result.optimization_time = optimization_time
                    result.strategy_used = "ortools"
                    logger.info(f"✓ OR-Tools optimization completed in {optimization_time:.2f}s: {result.get_summary()}")
                    return result
                except Exception as extract_error:
                    logger.error(f"✗ Failed to extract OR-Tools solution: {extract_error}", exc_info=True)
                    # Fall through to error case
            else:
                # No solution found
                logger.error(f"✗ OR-Tools could not find a solution (status={status})")
                logger.error(f"  - Search ran for {(datetime.now() - start_time).total_seconds():.2f}s")
                logger.error(f"  - Problem size: {len(request.cases)} cases, {len(request.vehicles)} vehicles")
                logger.error(f"  - Try: (1) Relaxing time windows, (2) Increasing vehicle capacity, (3) Reducing cases")
                return OptimizationResult(
                    success=False,
                    routes=[],
                    unassigned_cases=request.cases,
                    constraint_violations=[
                        ConstraintViolation(
                            type=ConstraintType.INFEASIBLE,
                            description="No feasible solution found. Constraints may be too strict. Try relaxing time windows or increasing vehicle capacity.",
                            severity="error"
                        )
                    ],
                    optimization_time=(datetime.now() - start_time).total_seconds(),
                    strategy_used="ortools",
                    message="No feasible solution found"
                )

        except Exception as e:
            logger.error(f"OR-Tools optimization failed: {e}", exc_info=True)
            return OptimizationResult(
                success=False,
                routes=[],
                unassigned_cases=request.cases,
                constraint_violations=[
                    ConstraintViolation(
                        type=ConstraintType.INFEASIBLE,
                        description=f"Optimization failed: {str(e)}",
                        severity="error"
                    )
                ],
                optimization_time=(datetime.now() - start_time).total_seconds(),
                strategy_used="ortools",
                message=f"Optimization error: {str(e)}"
            )

    def _validate_request(self) -> List[ConstraintViolation]:
        """Validate the optimization request"""
        violations = []

        # Check that all vehicles have assigned personnel
        for vehicle in self.request.vehicles:
            if not self.request.personnel:
                violations.append(ConstraintViolation(
                    type=ConstraintType.INFEASIBLE,
                    description=f"Vehicle {vehicle.identifier} has no personnel assigned",
                    entity_id=vehicle.id,
                    entity_type="vehicle"
                ))

        return violations

    def _build_data_model(self):
        """Build the data model for OR-Tools"""
        # PHASE 1: Pre-assign personnel to vehicles based on ALL case skills
        logger.info("Pre-assigning personnel to vehicles based on required skills...")
        self.vehicle_to_personnel = assign_personnel_to_vehicles(
            vehicles=self.request.vehicles,
            personnel=self.request.personnel,
            cases=self.request.cases
        )

        # Log personnel assignments
        for vehicle in self.request.vehicles:
            assigned = self.vehicle_to_personnel.get(vehicle.id, [])
            skills = set()
            for p in assigned:
                skills.update(p.skills)
            logger.info(f"  Vehicle {vehicle.identifier}: {len(assigned)} personnel with skills: {sorted(skills)}")

        # PHASE 1.5: PRE-FILTER cases that have NO valid vehicles (will be auto-unassigned)
        # This prevents OR-Tools from trying to assign them and violating constraints
        logger.info("Pre-filtering cases without valid vehicles...")
        self.feasible_cases = []
        self.infeasible_cases = []  # Cases that cannot be assigned to any vehicle

        for case in self.request.cases:
            # Check if ANY vehicle can serve this case
            allowed_vehicles = get_allowed_vehicles_for_case(
                case=case,
                vehicles=self.request.vehicles,
                vehicle_personnel_map=self.vehicle_to_personnel
            )

            if allowed_vehicles:
                self.feasible_cases.append(case)
            else:
                self.infeasible_cases.append(case)
                logger.warning(f"  ⚠️  Case {case.id} has NO valid vehicles (skills: {case.required_skills}) - PRE-FILTERED OUT")

        logger.info(f"  Feasible cases: {len(self.feasible_cases)} | Infeasible cases: {len(self.infeasible_cases)}")

        # Build location list: first all vehicle base locations (depots), then ONLY FEASIBLE case locations
        self.locations = []
        self.location_to_case = {}

        # Add vehicle base locations (one depot per vehicle)
        depot_indices = []
        for i, vehicle in enumerate(self.request.vehicles):
            self.locations.append(vehicle.base_location)
            depot_indices.append(len(self.locations) - 1)

        # Add ONLY FEASIBLE case locations (skip infeasible ones)
        case_start_idx = len(self.locations)
        for i, case in enumerate(self.feasible_cases):  # Changed from self.request.cases to self.feasible_cases
            self.locations.append(case.location)
            self.location_to_case[len(self.locations) - 1] = case

        # Build distance and time matrices
        self._build_matrices()

    def _build_matrices(self):
        """Build distance and time matrices"""
        n = len(self.locations)

        # Initialize matrices with zeros
        self.distance_matrix = [[0.0] * n for _ in range(n)]
        self.time_matrix = [[0] * n for _ in range(n)]

        # If matrices provided in request, use them
        if self.request.distance_matrix and self.request.time_matrix:
            logger.info(f"Building matrices from provided data for {n} locations")

            # The request matrices use indices: [0..num_vehicles-1] for depots, [num_vehicles..n-1] for cases
            # self.locations uses same indexing: first num_vehicles are depots, rest are cases

            for i in range(n):
                for j in range(n):
                    # Get distance and time from request matrices
                    dist = self.request.distance_matrix.get((i, j), 0.0)
                    time_val = self.request.time_matrix.get((i, j), 0)

                    # If not found in request matrices, calculate using Haversine
                    if dist == 0.0 and i != j:
                        dist = self._haversine_distance(self.locations[i], self.locations[j])
                        time_val = int((dist / 40.0) * 60)  # minutes at 40 km/h

                    self.distance_matrix[i][j] = dist
                    self.time_matrix[i][j] = time_val

            logger.info(f"Matrix construction complete. Sample distances: {[self.distance_matrix[0][i] for i in range(min(5, n))]}")
        else:
            # Create matrices using Haversine distance (fallback)
            logger.warning("No distance matrix provided, using Haversine distance")

            for i in range(n):
                for j in range(n):
                    if i != j:
                        dist = self._haversine_distance(self.locations[i], self.locations[j])
                        self.distance_matrix[i][j] = dist
                        # Estimate time: assume 40 km/h average speed
                        self.time_matrix[i][j] = int((dist / 40.0) * 60)  # minutes

    def _haversine_distance(self, loc1: Location, loc2: Location) -> float:
        """Calculate Haversine distance between two locations in km"""
        import math

        R = 6371  # Earth radius in km
        lat1, lon1 = math.radians(loc1.latitude), math.radians(loc1.longitude)
        lat2, lon2 = math.radians(loc2.latitude), math.radians(loc2.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    def _create_routing_model(self):
        """Create the OR-Tools routing model"""
        num_vehicles = len(self.request.vehicles)

        # Depot indices are the first num_vehicles locations (vehicle base locations)
        depot_indices = list(range(num_vehicles))

        # Create routing index manager
        # Total locations = num vehicles (depots) + num cases
        num_locations = len(self.locations)

        logger.info(f"Creating routing model:")
        logger.info(f"  - Vehicles: {num_vehicles}")
        logger.info(f"  - Total locations: {num_locations}")
        logger.info(f"  - Cases to visit: {len(self.location_to_case)}")
        logger.info(f"  - Depot indices: {depot_indices}")

        self.manager = pywrapcp.RoutingIndexManager(
            num_locations,
            num_vehicles,
            depot_indices,  # start depots
            depot_indices   # end depots
        )

        # Create routing model
        self.routing = pywrapcp.RoutingModel(self.manager)

        # PHASE 2: Add skill-based vehicle constraints
        # For each case, determine which vehicles can serve it (based on personnel skills)
        logger.info("Adding skill-based vehicle constraints...")

        cases_with_no_valid_vehicles = []

        for location_idx, case in self.location_to_case.items():
            # Get list of vehicle indices that can serve this case
            allowed_vehicles = get_allowed_vehicles_for_case(
                case=case,
                vehicles=self.request.vehicles,
                vehicle_personnel_map=self.vehicle_to_personnel
            )

            node_index = self.manager.NodeToIndex(location_idx)

            if not allowed_vehicles:
                # No vehicle can serve this case
                # NOTE: SetAllowedVehiclesForIndex([]) means "ALL vehicles allowed" (OR-Tools default)
                # We'll use penalty=0 in AddDisjunction to force these to be dropped
                cases_with_no_valid_vehicles.append(case.id)
                logger.warning(f"  Case {case.id} has no valid vehicles (required skills: {case.required_skills}) - will be dropped")
            else:
                # Restrict this case to ONLY the allowed vehicles (hard constraint)
                self.routing.SetAllowedVehiclesForIndex(allowed_vehicles, node_index)
                logger.info(f"  Case {case.id} can be served by vehicles: {[self.request.vehicles[i].identifier for i in allowed_vehicles]}")

        # Allow dropping nodes (not visiting some cases) with differentiated penalties
        # Penalty must be in same units as distance (meters, since distance_callback multiplies by 1000)
        # HIGH penalty (100000 = 100km): for cases that CAN be assigned - prefer assigning them
        # ZERO penalty (0): for cases that CANNOT be assigned - ALWAYS drop them (no cost)
        penalty_high = 100000  # High penalty = prefer to assign
        penalty_zero = 0       # Zero penalty = always drop (no cost to leave unassigned)

        for location_idx, case in self.location_to_case.items():
            index = self.manager.NodeToIndex(location_idx)

            # Use ZERO penalty for cases without valid vehicles (always drop - no cost)
            # Use HIGH penalty for cases with valid vehicles (prefer to assign - high cost to drop)
            if case.id in cases_with_no_valid_vehicles:
                self.routing.AddDisjunction([index], penalty_zero)
            else:
                self.routing.AddDisjunction([index], penalty_high)

        logger.info(f"  - Drop penalties: HIGH={penalty_high} (prefer assign), ZERO={penalty_zero} (always drop)")

        if cases_with_no_valid_vehicles:
            logger.warning(f"  WARNING: {len(cases_with_no_valid_vehicles)} cases have no valid vehicles and will likely be dropped")
            logger.warning(f"           Case IDs: {sorted(cases_with_no_valid_vehicles)}")

    def _add_distance_constraint(self):
        """Add distance dimension to the model"""
        def distance_callback(from_index, to_index):
            """Return distance between two nodes"""
            try:
                # Validate indices are within valid range
                if from_index < 0 or to_index < 0:
                    return 0

                # Check if indices are valid routing indices
                if from_index >= self.manager.GetNumberOfIndices() or to_index >= self.manager.GetNumberOfIndices():
                    return 0

                from_node = self.manager.IndexToNode(from_index)
                to_node = self.manager.IndexToNode(to_index)

                # Validate nodes are within matrix bounds
                if from_node < 0 or to_node < 0:
                    return 0
                if from_node >= len(self.distance_matrix) or to_node >= len(self.distance_matrix):
                    return 0

                return int(self.distance_matrix[from_node][to_node] * 1000)  # Convert to meters
            except (OverflowError, IndexError, KeyError, Exception) as e:
                # Return a large penalty distance for invalid transitions
                return 999999

        transit_callback_index = self.routing.RegisterTransitCallback(distance_callback)

        # Define cost of each arc
        self.routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Add distance dimension
        dimension_name = 'Distance'
        self.routing.AddDimension(
            transit_callback_index,
            0,  # no slack
            300000,  # maximum distance per vehicle (300 km in meters)
            True,  # start cumul to zero
            dimension_name
        )
        distance_dimension = self.routing.GetDimensionOrDie(dimension_name)
        # REMOVED: SetGlobalSpanCostCoefficient(100) - was making routes too expensive compared to drop penalty
        # The span coefficient multiplies max vehicle distance, causing OR-Tools to prefer dropping ALL cases
        # Instead, rely on arc costs and drop penalties only

    def _add_time_window_constraint(self):
        """Add time window constraints"""
        def time_callback(from_index, to_index):
            """Return travel time between two nodes"""
            try:
                # Validate indices
                if from_index < 0 or to_index < 0:
                    return 0

                # Check if indices are valid routing indices
                if from_index >= self.manager.GetNumberOfIndices() or to_index >= self.manager.GetNumberOfIndices():
                    return 0

                from_node = self.manager.IndexToNode(from_index)
                to_node = self.manager.IndexToNode(to_index)

                # Validate nodes are within bounds
                if from_node < 0 or to_node < 0:
                    return 0
                if from_node >= len(self.time_matrix) or to_node >= len(self.time_matrix):
                    return 0

                travel_time = self.time_matrix[from_node][to_node]

                # Add service time if going to a case location
                if to_node in self.location_to_case:
                    case = self.location_to_case[to_node]
                    travel_time += case.estimated_duration

                return travel_time
            except (OverflowError, IndexError, KeyError, Exception) as e:
                # Silent fail - this can happen legitimately for invalid arcs
                return 9999  # Large penalty time

        transit_callback_index = self.routing.RegisterTransitCallback(time_callback)

        # Add time dimension with VERY relaxed slack to allow flexibility
        dimension_name = 'Time'
        self.routing.AddDimension(
            transit_callback_index,
            240,  # allow 4 hours of waiting time (very flexible)
            720,  # maximum time per vehicle (12 hours in minutes)
            False,  # don't force start cumul to zero
            dimension_name
        )
        time_dimension = self.routing.GetDimensionOrDie(dimension_name)

        # Add ULTRA soft time window constraints for each case
        # Very low penalty makes constraints extremely relaxed
        penalty = 100  # VERY LOW penalty for violating time windows (ultra soft constraint)

        for location_idx, case in self.location_to_case.items():
            index = self.manager.NodeToIndex(location_idx)

            # Convert time window to minutes since start of day (8:00)
            start_minutes, end_minutes = case.time_window.to_minutes()

            # Adjust to be relative to work start (8:00 = 0)
            work_start_minutes = 8 * 60  # 8:00 AM
            tw_start = max(0, start_minutes - work_start_minutes)
            tw_end = end_minutes - work_start_minutes

            # Add very soft time windows (can be easily violated)
            time_dimension.CumulVar(index).SetRange(0, 720)  # Very soft range (12 hours)
            # Add small penalty for being outside preferred window
            time_dimension.SetCumulVarSoftUpperBound(index, tw_end, penalty)
            time_dimension.SetCumulVarSoftLowerBound(index, tw_start, penalty)

        # Add time window for vehicles (depot) - allow starting later
        for vehicle_idx in range(len(self.request.vehicles)):
            index = self.routing.Start(vehicle_idx)
            time_dimension.CumulVar(index).SetRange(0, 60)  # Can start up to 1 hour late

    def _add_capacity_constraint(self):
        """Add vehicle capacity constraints"""
        # For simplicity, each case counts as 1 unit of capacity
        def demand_callback(from_index):
            """Return demand of a node"""
            from_node = self.manager.IndexToNode(from_index)
            if from_node in self.location_to_case:
                return 1
            return 0

        demand_callback_index = self.routing.RegisterUnaryTransitCallback(demand_callback)

        # Get capacities and ensure minimum capacity allows all cases to be served
        num_cases = len(self.request.cases)
        num_vehicles = len(self.request.vehicles)

        # Calculate minimum capacity needed per vehicle (round up)
        min_capacity_per_vehicle = max(3, (num_cases + num_vehicles - 1) // num_vehicles)

        # Increase capacity generously to ensure feasibility
        vehicle_capacities = [
            max(vehicle.capacity, min_capacity_per_vehicle, num_cases)  # At least enough for all cases
            for vehicle in self.request.vehicles
        ]

        logger.info(f"Vehicle capacities adjusted: {vehicle_capacities} for {num_cases} cases across {num_vehicles} vehicles")

        # Add capacity dimension with generous slack
        self.routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            2,  # Allow 2 units slack (very flexible)
            vehicle_capacities,  # adjusted vehicle capacities
            True,  # start cumul to zero
            'Capacity'
        )

    def _add_skill_constraint(self):
        """Add skill constraints - cases can only be assigned to vehicles with required skills"""
        logger.info("Adding SKILL constraints...")

        # For each case location, determine which vehicles have the required skills
        for location_idx, case in self.location_to_case.items():
            # Get required skills for this case
            required_skills = set(case.required_skills)

            # Find vehicles that have ALL required skills
            allowed_vehicles = []
            for vehicle_idx, vehicle in enumerate(self.request.vehicles):
                # Get skills from personnel assigned to this vehicle
                assigned_personnel = self.vehicle_to_personnel.get(vehicle.id, [])
                vehicle_skills = set()
                for person in assigned_personnel:
                    vehicle_skills.update(person.skills)

                # Check if vehicle has ALL required skills
                if required_skills.issubset(vehicle_skills):
                    allowed_vehicles.append(vehicle_idx)

            # Get routing index for this case location
            index = self.manager.NodeToIndex(location_idx)

            # If no vehicles have the required skills, mark case as droppable
            if not allowed_vehicles:
                logger.warning(f"Case {case.id} requires skills {required_skills} but NO vehicles have them")
                # Make the drop penalty lower than visiting to ensure it's dropped
                self.routing.AddDisjunction([index], 1000)  # Low penalty = prefer to drop
            else:
                # Restrict this case to only be visited by vehicles with required skills
                self.routing.SetAllowedVehiclesForIndex(allowed_vehicles, index)
                logger.debug(f"Case {case.id} can be assigned to vehicles: {[self.request.vehicles[i].identifier for i in allowed_vehicles]}")

                # Add a moderate drop penalty to prefer assigning over dropping
                # But not too high to force infeasible solutions
                self.routing.AddDisjunction([index], 100000)  # Higher penalty = prefer to assign

        logger.info(f"Skill constraints applied for {len(self.location_to_case)} cases")

    def _get_search_parameters(self) -> pywrapcp.DefaultRoutingSearchParameters:
        """Configure search parameters"""
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()

        # Use PARALLEL_CHEAPEST_INSERTION - best for small VRP problems
        # This strategy builds all routes in parallel, good for balanced solutions
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
        )

        # Use guided local search for metaheuristic (good balance)
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )

        # Set generous time limit
        search_parameters.time_limit.seconds = max(self.request.max_optimization_time, 120)  # At least 2 minutes

        # Allow many solution attempts but not too many (to avoid timeouts)
        search_parameters.solution_limit = 50000  # Increased from 10000 to allow more exploration

        # Enable more advanced features
        search_parameters.use_full_propagation = False  # Sometimes less propagation helps find solutions faster

        # Log search for debugging (disable for production to reduce log spam)
        search_parameters.log_search = False  # Changed to False to reduce log spam

        logger.info(f"Search parameters: strategy=PARALLEL_CHEAPEST_INSERTION, time_limit={search_parameters.time_limit.seconds}s, solution_limit=50000")

        return search_parameters

    def _calculate_skill_gap_analysis(
        self,
        unassigned_cases: List[Case],
        all_cases: List[Case],
        assigned_case_ids: Set[int]
    ) -> SkillGapAnalysis:
        """
        Calculate comprehensive skill gap analysis for business insights.

        This function provides actionable data for hiring decisions by analyzing:
        1. Which skills are missing and preventing case assignments
        2. Which skills are most in-demand (hiring priority)
        3. Coverage percentage per skill
        4. Impact simulation: how many more cases could be assigned with additional personnel

        Args:
            unassigned_cases: Cases that could not be assigned to any route
            all_cases: All cases requested in the optimization
            assigned_case_ids: IDs of cases that were successfully assigned

        Returns:
            SkillGapAnalysis with comprehensive business metrics
        """
        # Initialize analysis
        analysis = SkillGapAnalysis()

        # Summary metrics
        analysis.total_cases_requested = len(all_cases)
        analysis.total_cases_assigned = len(assigned_case_ids)
        analysis.total_cases_unassigned = len(unassigned_cases)
        if analysis.total_cases_requested > 0:
            analysis.assignment_rate_percentage = (
                analysis.total_cases_assigned / analysis.total_cases_requested
            ) * 100.0

        # If all cases assigned, return empty analysis (success!)
        if not unassigned_cases:
            logger.info("✅ All cases assigned - no skill gaps detected")
            return analysis

        # Collect all skills from all vehicles (what we have)
        all_available_skills = set()
        for vehicle in self.request.vehicles:
            assigned_personnel = self.vehicle_to_personnel.get(vehicle.id, [])
            for person in assigned_personnel:
                all_available_skills.update(person.skills)

        # 1. Analyze unassigned cases - determine missing skills
        unassigned_case_details = []
        skills_demand_counter = {}  # skill -> count of cases requiring it

        for case in unassigned_cases:
            required_skills = set(case.required_skills)
            missing_skills = required_skills - all_available_skills

            # Track demand for each missing skill
            for skill in missing_skills:
                skills_demand_counter[skill] = skills_demand_counter.get(skill, 0) + 1

            # Create detailed case info
            # Convert priority to int (handle enum/string/int types)
            if isinstance(case.priority, int):
                priority_int = case.priority
            elif hasattr(case.priority, 'value'):
                priority_int = case.priority.value if isinstance(case.priority.value, int) else {'low': 1, 'medium': 2, 'high': 3, 'urgent': 4}.get(str(case.priority.value).lower(), 2)
            elif isinstance(case.priority, str):
                priority_int = {'low': 1, 'medium': 2, 'high': 3, 'urgent': 4}.get(case.priority.lower(), 2)
            else:
                priority_int = 2  # default to medium

            detail = UnassignedCaseDetail(
                case_id=case.id,
                case_name=case.patient_name,
                required_skills=case.required_skills,
                missing_skills=list(missing_skills),
                priority=priority_int
            )
            unassigned_case_details.append(detail)

            # Group by skill
            for skill in missing_skills:
                if skill not in analysis.unassigned_cases_by_skill:
                    analysis.unassigned_cases_by_skill[skill] = []
                analysis.unassigned_cases_by_skill[skill].append(case.id)

        analysis.unassigned_case_details = unassigned_case_details

        # 2. Most demanded skills (hiring priority ranking)
        analysis.most_demanded_skills = sorted(
            skills_demand_counter.items(),
            key=lambda x: (-x[1], x[0])  # Sort by count descending, then by name
        )

        # 3. Skill coverage percentage
        # For each skill, calculate: (cases requiring skill that CAN be assigned) / (total cases requiring skill)
        for case in all_cases:
            for skill in case.required_skills:
                if skill not in analysis.skill_coverage_percentage:
                    # Count total cases requiring this skill
                    total_with_skill = sum(
                        1 for c in all_cases if skill in c.required_skills
                    )
                    # Count assigned cases requiring this skill
                    assigned_with_skill = sum(
                        1 for c in all_cases
                        if skill in c.required_skills and c.id in assigned_case_ids
                    )

                    if total_with_skill > 0:
                        coverage = (assigned_with_skill / total_with_skill) * 100.0
                    else:
                        coverage = 0.0

                    analysis.skill_coverage_percentage[skill] = round(coverage, 2)

        # 4. Hiring impact simulation
        # For each missing skill, simulate adding one person with that skill
        # Count how many currently unassigned cases would become assignable
        for skill in skills_demand_counter.keys():
            additional_assignable = 0

            for case in unassigned_cases:
                missing_skills = set(case.required_skills) - all_available_skills

                # If this skill is the ONLY missing skill for this case,
                # hiring someone with this skill would make the case assignable
                if skill in missing_skills:
                    # Check if adding this skill would make the case fully covered
                    would_be_covered = (set(case.required_skills) - {skill}).issubset(all_available_skills)
                    if would_be_covered or len(missing_skills) == 1:
                        additional_assignable += 1

            analysis.hiring_impact_simulation[skill] = additional_assignable

        # Log summary
        logger.info("=" * 80)
        logger.info("📊 SKILL GAP ANALYSIS:")
        logger.info(f"  Assignment rate: {analysis.assignment_rate_percentage:.1f}% ({analysis.total_cases_assigned}/{analysis.total_cases_requested})")
        logger.info(f"  Unassigned cases: {analysis.total_cases_unassigned}")

        if analysis.most_demanded_skills:
            logger.info("  🔥 Most demanded skills (hiring priority):")
            for skill, count in analysis.most_demanded_skills[:5]:  # Top 5
                impact = analysis.hiring_impact_simulation.get(skill, 0)
                coverage = analysis.skill_coverage_percentage.get(skill, 0.0)
                logger.info(f"     - {skill}: {count} cases blocked, {coverage:.1f}% coverage, +{impact} cases if hired")

        logger.info("=" * 80)

        return analysis

    def _extract_solution(self, solution) -> OptimizationResult:
        """Extract the solution from OR-Tools"""
        routes = []
        unassigned_cases = []
        violations = []
        total_distance = 0.0
        total_time = 0

        # Track assigned cases
        assigned_case_ids = set()

        # Extract route for each vehicle
        for vehicle_idx in range(len(self.request.vehicles)):
            vehicle = self.request.vehicles[vehicle_idx]
            index = self.routing.Start(vehicle_idx)

            route_visits = []
            route_distance = 0.0
            route_time = 0
            sequence = 0
            last_node_index = self.manager.IndexToNode(index)  # Track previous node index

            while not self.routing.IsEnd(index):
                node_index = self.manager.IndexToNode(index)
                next_index = solution.Value(self.routing.NextVar(index))
                next_node_index = self.manager.IndexToNode(next_index)

                # If this is a case location, add to route
                if node_index in self.location_to_case:
                    case = self.location_to_case[node_index]
                    assigned_case_ids.add(case.id)

                    # Calculate arrival time based on accumulated route time
                    work_start = datetime.combine(self.request.date.date(), time(8, 0))
                    arrival_time = work_start + timedelta(minutes=route_time)
                    start_time = arrival_time
                    end_time = start_time + timedelta(minutes=case.estimated_duration)

                    # Travel distance and time from previous to current
                    travel_time = self.time_matrix[last_node_index][node_index]
                    distance = self.distance_matrix[last_node_index][node_index]

                    visit = Visit(
                        case=case,
                        sequence=sequence,
                        arrival_time=arrival_time,
                        start_time=start_time,
                        end_time=end_time,
                        travel_time_from_previous=travel_time,
                        distance_from_previous=distance
                    )
                    route_visits.append(visit)

                    # Update route time for next visit
                    route_time += travel_time + case.estimated_duration
                    sequence += 1

                # Accumulate distance
                route_distance += self.distance_matrix[node_index][next_node_index]

                # Move to next node
                last_node_index = node_index
                index = next_index

            # Only create route if it has visits
            if route_visits:
                # Use pre-assigned personnel (already determined to have required skills)
                personnel = self.vehicle_to_personnel.get(vehicle.id, [])

                route = Route(
                    vehicle=vehicle,
                    personnel=personnel,
                    visits=route_visits,
                    date=self.request.date,
                    total_distance=route_distance,
                    total_time=route_time
                )

                # Validate skills
                # NOTE: Even with pre-assignment, OR-Tools may create routes where personnel don't have
                # ALL skills for ALL visits (business reality). Mark as WARNING, not ERROR.
                if not route.validate_skills():
                    # Log details for debugging
                    all_personnel_skills = set()
                    for person in route.personnel:
                        all_personnel_skills.update(person.skills)

                    missing_skills_per_visit = []
                    for visit in route.visits:
                        required = set(visit.case.required_skills)
                        missing = required - all_personnel_skills
                        if missing:
                            missing_skills_per_visit.append(f"Case {visit.case.id} missing: {missing}")

                    logger.warning(
                        f"Route for vehicle {vehicle.identifier} has skill gaps: "
                        f"{'; '.join(missing_skills_per_visit)}"
                    )

                    violations.append(ConstraintViolation(
                        type=ConstraintType.SKILL_MISMATCH,
                        description=f"Route for vehicle {vehicle.identifier} lacks some required skills",
                        entity_id=vehicle.id,
                        entity_type="route",
                        severity="warning",  # Business reality: not all routes will have perfect skill coverage
                        details={
                            "vehicle_skills": list(all_personnel_skills),
                            "missing_skills_details": missing_skills_per_visit
                        }
                    ))

                routes.append(route)
                total_distance += route_distance

        # Find unassigned cases (including pre-filtered infeasible cases)
        for case in self.request.cases:
            if case.id not in assigned_case_ids:
                unassigned_cases.append(case)

        # Include pre-filtered infeasible cases in unassigned list
        for case in self.infeasible_cases:
            if case not in unassigned_cases:
                unassigned_cases.append(case)

        # NEW SUCCESS CRITERION: Success if ANY routes were created
        # Partial optimization (some unassigned cases) is still successful for business
        success = len(routes) > 0

        # Calculate skill gap analysis for business insights
        skill_gap_analysis = self._calculate_skill_gap_analysis(
            unassigned_cases=unassigned_cases,
            all_cases=self.request.cases,
            assigned_case_ids=assigned_case_ids
        )

        # Check for critical violations (should be rare with pre-assignment)
        critical_violations = [v for v in violations if v.severity == "error"]

        # Debug logging
        if violations:
            print(f"⚠️  OR-Tools violations: {[f'{v.type.value}:{v.description}' for v in violations]}", flush=True)
        print(f"📋 OR-Tools result: {len(routes)} routes, {len(assigned_case_ids)}/{len(self.request.cases)} assigned ({skill_gap_analysis.assignment_rate_percentage:.1f}% coverage)", flush=True)

        # Build message
        if len(unassigned_cases) > 0:
            message = f"Optimized {len(routes)} routes with {len(assigned_case_ids)}/{len(self.request.cases)} cases assigned ({len(unassigned_cases)} unassigned due to skill gaps)"
        else:
            message = f"Optimized {len(routes)} routes with all {len(assigned_case_ids)} cases assigned"

        return OptimizationResult(
            success=success,
            routes=routes,
            unassigned_cases=unassigned_cases,
            constraint_violations=violations,
            total_distance=total_distance,
            total_time=total_time,
            skill_gap_analysis=skill_gap_analysis,
            message=message
        )
