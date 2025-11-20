"""
Optimization Service

Main service for route optimization. Orchestrates the optimization process,
manages strategy selection, and persists results to the database.
"""

import logging
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.case import Case as CaseModel
from app.models.vehicle import Vehicle as VehicleModel
from app.models.personnel import Personnel as PersonnelModel
from app.models.route import Route as RouteModel, RouteStatus
from app.models.route import RoutePersonnel, Visit as VisitModel, VisitStatus
from app.models.optimization_metrics import OptimizationMetrics
from app.services.distance.providers import HaversineProvider

from .models import (
    OptimizationRequest,
    OptimizationResult,
    Case,
    Vehicle,
    Personnel,
    Location,
    TimeWindow,
    ConstraintViolation,
    ConstraintType
)
from .ortools_strategy import ORToolsVRPStrategy
from .heuristic_strategy import HeuristicStrategy

logger = logging.getLogger(__name__)


class OptimizationService:
    """
    Service for route optimization.
    Handles optimization request preparation, strategy selection, and result persistence.
    """

    def __init__(self, db: Session):
        self.db = db
        # Initialize distance providers
        self._init_distance_providers()
        self.ortools_strategy = ORToolsVRPStrategy()
        self.heuristic_strategy = HeuristicStrategy()

    def _init_distance_providers(self):
        """Initialize distance providers with Google Maps (traffic support) as primary"""
        import os
        from app.services.distance.providers import GoogleMapsProvider

        self.use_traffic = False
        self.google_maps_provider = None

        # Try to initialize Google Maps with traffic support
        google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if google_api_key:
            try:
                self.google_maps_provider = GoogleMapsProvider(google_api_key)
                self.use_traffic = True
                logger.info("Google Maps provider initialized with traffic support")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Maps: {e}")

        # Fallback to Haversine
        self.distance_provider = HaversineProvider(average_speed_kmh=40.0)
        if not self.use_traffic:
            logger.info("Using Haversine provider (no traffic data)")

    async def optimize_routes(
        self,
        case_ids: List[int],
        vehicle_ids: List[int],
        date: datetime,
        use_heuristic: bool = False,
        max_time: int = 60
    ) -> OptimizationResult:
        """
        Optimize routes for given cases and vehicles.

        Args:
            case_ids: List of case IDs to include in optimization
            vehicle_ids: List of vehicle IDs to use
            date: Date for the routes
            use_heuristic: Force use of heuristic strategy
            max_time: Maximum optimization time in seconds

        Returns:
            OptimizationResult with optimized routes
        """
        print(f"🚀 OPTIMIZATION START: cases={len(case_ids)}, vehicles={len(vehicle_ids)}, use_heuristic={use_heuristic}", flush=True)
        logger.info(f"🚀 OPTIMIZATION START: cases={len(case_ids)}, vehicles={len(vehicle_ids)}, use_heuristic={use_heuristic}")
        try:
            logger.info(f"Starting route optimization for {len(case_ids)} cases and {len(vehicle_ids)} vehicles")

            # Fetch cases from database (allow pending or assigned cases for re-optimization)
            cases_db = self.db.query(CaseModel).filter(
                CaseModel.id.in_(case_ids),
                CaseModel.status.in_(["pending", "assigned"])
            ).all()

            if len(cases_db) != len(case_ids):
                missing_count = len(case_ids) - len(cases_db)
                return OptimizationResult(
                    success=False,
                    routes=[],
                    unassigned_cases=[],
                    constraint_violations=[
                        ConstraintViolation(
                            type=ConstraintType.INFEASIBLE,
                            description=f"Some cases not found or have invalid status. Found {len(cases_db)} of {len(case_ids)} cases. Make sure cases are in 'pending' or 'assigned' status.",
                            severity="error"
                        )
                    ],
                    message="Invalid cases"
                )

            # Fetch vehicles from database
            vehicles_db = self.db.query(VehicleModel).filter(
                VehicleModel.id.in_(vehicle_ids),
                VehicleModel.is_active == True
            ).all()

            if len(vehicles_db) != len(vehicle_ids):
                return OptimizationResult(
                    success=False,
                    routes=[],
                    unassigned_cases=[],
                    constraint_violations=[
                        ConstraintViolation(
                            type=ConstraintType.INFEASIBLE,
                            description="Some vehicles not found or not active",
                            severity="error"
                        )
                    ],
                    message="Invalid vehicles"
                )

            # Fetch all active personnel
            personnel_db = self.db.query(PersonnelModel).filter(
                PersonnelModel.is_active == True
            ).all()

            if not personnel_db:
                return OptimizationResult(
                    success=False,
                    routes=[],
                    unassigned_cases=[],
                    constraint_violations=[
                        ConstraintViolation(
                            type=ConstraintType.INFEASIBLE,
                            description="No active personnel available",
                            severity="error"
                        )
                    ],
                    message="No personnel available"
                )

            # Convert to optimization domain models
            cases = self._convert_cases(cases_db)
            vehicles = self._convert_vehicles(vehicles_db)
            personnel = self._convert_personnel(personnel_db)

            # Get distance and time matrices
            distance_matrix, time_matrix = await self._get_distance_matrices(
                cases,
                vehicles
            )

            # Create optimization request
            request = OptimizationRequest(
                cases=cases,
                vehicles=vehicles,
                personnel=personnel,
                date=date,
                distance_matrix=distance_matrix,
                time_matrix=time_matrix,
                max_optimization_time=max_time,
                use_heuristic_fallback=not use_heuristic
            )

            # Execute optimization
            # ALWAYS use OR-Tools strategy (no fallback to heuristic)
            # Partial optimization (some unassigned cases) is acceptable for business
            print(f"🔍 Strategy: OR-Tools only (use_heuristic parameter ignored, fallback disabled)", flush=True)
            logger.info(f"🔍 Using OR-Tools strategy exclusively (no heuristic fallback)")

            print("✅ Using OR-Tools strategy", flush=True)
            logger.info("Using OR-Tools strategy")
            result = self.ortools_strategy.optimize(request)

            print(f"📊 OR-Tools result: success={result.success}, routes={len(result.routes)}, unassigned={len(result.unassigned_cases)}", flush=True)
            logger.info(f"OR-Tools result: success={result.success}, routes={len(result.routes)}, unassigned={len(result.unassigned_cases)}, violations={len(result.constraint_violations)}")

            # NO FALLBACK TO HEURISTIC
            # Business requirement: Always use OR-Tools for best optimization
            # Partial assignment is acceptable - skill gap analysis will provide insights

            # Persist results to database if successful
            if result.success:
                await self._persist_routes(result, cases_db, vehicles_db, personnel_db)

            logger.info(f"Optimization completed: {result.get_summary()}")
            return result

        except Exception as e:
            logger.error(f"Optimization service error: {e}", exc_info=True)
            return OptimizationResult(
                success=False,
                routes=[],
                unassigned_cases=[],
                constraint_violations=[
                    ConstraintViolation(
                        type=ConstraintType.INFEASIBLE,
                        description=f"Service error: {str(e)}",
                        severity="error"
                    )
                ],
                message=f"Optimization failed: {str(e)}"
            )

    def _convert_cases(self, cases_db: List[CaseModel]) -> List[Case]:
        """Convert database Case models to optimization Case models"""
        from geoalchemy2.shape import to_shape

        cases = []
        for case_db in cases_db:
            # Extract coordinates from PostGIS Point
            point = to_shape(case_db.location)
            location = Location(latitude=point.y, longitude=point.x)

            # Get required skills from care type
            required_skills = [skill.name for skill in case_db.care_type.required_skills]

            # Parse time window - extract time part from datetime
            from datetime import time as time_type
            tw_start = case_db.time_window_start.time() if isinstance(case_db.time_window_start, datetime) else case_db.time_window_start
            tw_end = case_db.time_window_end.time() if isinstance(case_db.time_window_end, datetime) else case_db.time_window_end

            time_window = TimeWindow(
                start=tw_start,
                end=tw_end
            )

            case = Case(
                id=case_db.id,
                patient_id=case_db.patient_id,
                patient_name=case_db.patient.name,
                location=location,
                care_type_id=case_db.care_type_id,
                care_type_name=case_db.care_type.name,
                required_skills=required_skills,
                time_window=time_window,
                priority=case_db.priority,
                estimated_duration=case_db.estimated_duration_minutes or case_db.care_type.estimated_duration_minutes or 30,
                special_instructions=case_db.notes or ""
            )
            cases.append(case)

        return cases

    def _convert_vehicles(self, vehicles_db: List[VehicleModel]) -> List[Vehicle]:
        """Convert database Vehicle models to optimization Vehicle models"""
        from geoalchemy2.shape import to_shape

        vehicles = []
        for vehicle_db in vehicles_db:
            # Extract coordinates from PostGIS Point
            point = to_shape(vehicle_db.base_location)
            location = Location(latitude=point.y, longitude=point.x)

            vehicle = Vehicle(
                id=vehicle_db.id,
                identifier=vehicle_db.identifier,
                capacity=vehicle_db.capacity_personnel,
                base_location=location,
                status=vehicle_db.status,
                is_active=vehicle_db.is_active,
                resources=vehicle_db.resources or []
            )
            vehicles.append(vehicle)

        return vehicles

    def _convert_personnel(self, personnel_db: List[PersonnelModel]) -> List[Personnel]:
        """Convert database Personnel models to optimization Personnel models"""
        from geoalchemy2.shape import to_shape

        personnel_list = []
        for person_db in personnel_db:
            # Extract coordinates from PostGIS Point (if present)
            # Note: start_location is optional and not used in current optimization
            if person_db.start_location is not None:
                point = to_shape(person_db.start_location)
                location = Location(latitude=point.y, longitude=point.x)
            else:
                # Default location (not used in optimization, but required by domain model)
                location = Location(latitude=0.0, longitude=0.0)

            # Get skills
            skills = [skill.name for skill in person_db.skills]

            personnel = Personnel(
                id=person_db.id,
                name=person_db.name,
                skills=skills,
                start_location=location,
                work_hours_start=person_db.work_start_time,
                work_hours_end=person_db.work_end_time,
                is_active=person_db.is_active
            )
            personnel_list.append(personnel)

        return personnel_list

    async def _get_distance_matrices(
        self,
        cases: List[Case],
        vehicles: List[Vehicle]
    ) -> Tuple[Dict[Tuple[int, int], float], Dict[Tuple[int, int], int]]:
        """
        Get distance and time matrices for all locations with TRAFFIC consideration.

        Returns:
            Tuple of (distance_matrix, time_matrix with traffic)
        """
        from app.services.distance.models import Location as DistLocation
        from datetime import time as time_type
        import time

        # Collect all locations and convert to distance service format
        opt_locations = [v.base_location for v in vehicles] + [c.location for c in cases]
        dist_locations = [
            DistLocation(latitude=loc.latitude, longitude=loc.longitude)
            for loc in opt_locations
        ]

        # Try to use Google Maps with traffic
        if self.use_traffic and self.google_maps_provider:
            try:
                # Calculate departure time (default to 8 AM tomorrow for rush hour simulation)
                from datetime import datetime, timedelta
                tomorrow_8am = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=1)
                departure_timestamp = int(time.mktime(tomorrow_8am.timetuple()))

                logger.info(f"Calculating distance matrix with TRAFFIC data (departure: {tomorrow_8am.strftime('%Y-%m-%d %H:%M')})")
                matrix = await self.google_maps_provider.calculate_with_traffic(
                    dist_locations,
                    departure_time=departure_timestamp
                )
                logger.info("Successfully obtained traffic-aware distance matrix from Google Maps")
            except Exception as e:
                logger.warning(f"Failed to get traffic data from Google Maps: {e}, falling back to Haversine")
                matrix = await self.distance_provider.calculate_matrix(dist_locations)
        else:
            # Fallback: Use Haversine and simulate traffic with time-based multipliers
            logger.info("Simulating traffic with time-based multipliers (no Google Maps API)")
            matrix = await self.distance_provider.calculate_matrix(dist_locations)
            matrix = self._apply_traffic_simulation(matrix)

        # Build dictionary matrices
        distance_matrix = {}
        time_matrix = {}

        n = len(dist_locations)
        for i in range(n):
            for j in range(n):
                travel_time = matrix.get_travel_time(i, j)
                distance_matrix[(i, j)] = travel_time.distance_km
                time_matrix[(i, j)] = travel_time.duration_minutes

        return distance_matrix, time_matrix

    def _apply_traffic_simulation(self, matrix):
        """
        Apply traffic simulation to matrix based on typical urban traffic patterns.
        Increases travel times during rush hours.
        """
        from datetime import datetime

        # Get current hour (or use 8 AM for morning rush simulation)
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:
            current_hour = 8  # Default to morning rush

        # Traffic multipliers by hour (1.0 = no traffic, 1.5 = 50% slower)
        traffic_multipliers = {
            7: 1.3,   # Morning build-up
            8: 1.5,   # Morning rush hour
            9: 1.4,   # Morning rush hour
            12: 1.2,  # Lunch hour
            13: 1.2,  # Lunch hour
            17: 1.4,  # Evening rush start
            18: 1.5,  # Evening rush hour
            19: 1.4,  # Evening rush hour
        }

        multiplier = traffic_multipliers.get(current_hour, 1.1)  # Default slight traffic
        logger.info(f"Applying traffic simulation: {multiplier}x multiplier for hour {current_hour}")

        # Apply multiplier to duration matrix
        n = len(matrix.durations_seconds)
        for i in range(n):
            for j in range(n):
                if i != j:
                    matrix.durations_seconds[i][j] *= multiplier

        return matrix

    async def _persist_routes(
        self,
        result: OptimizationResult,
        cases_db: List[CaseModel],
        vehicles_db: List[VehicleModel],
        personnel_db: List[PersonnelModel]
    ):
        """Persist optimization results to database"""
        import json

        try:
            # Create maps for easy lookup
            case_map = {c.id: c for c in cases_db}
            vehicle_map = {v.id: v for v in vehicles_db}
            personnel_map = {p.id: p for p in personnel_db}

            # Create routes
            for route in result.routes:
                # Create route record
                # Handle both datetime and date objects
                route_date = route.date.date() if isinstance(route.date, datetime) else route.date

                # Convert metadata dict to JSON string
                metadata_str = json.dumps(result.get_summary())

                route_db = RouteModel(
                    vehicle_id=route.vehicle.id,
                    route_date=route_date,
                    status=RouteStatus.DRAFT,
                    total_distance_km=route.total_distance,
                    total_duration_minutes=route.total_time,
                    optimization_metadata=metadata_str
                )
                self.db.add(route_db)
                self.db.flush()  # Get route ID

                # Associate personnel with route
                for person in route.personnel:
                    route_personnel = RoutePersonnel(
                        route_id=route_db.id,
                        personnel_id=person.id
                    )
                    self.db.add(route_personnel)

                # Create visits
                for visit in route.visits:
                    visit_db = VisitModel(
                        route_id=route_db.id,
                        case_id=visit.case.id,
                        sequence_number=visit.sequence,
                        estimated_arrival_time=visit.arrival_time,
                        estimated_departure_time=visit.end_time,
                        status=VisitStatus.PENDING
                    )
                    self.db.add(visit_db)

                    # Update case status to assigned
                    case_db = case_map.get(visit.case.id)
                    if case_db:
                        case_db.status = "assigned"

                # Save optimization metrics for this route
                if result.skill_gap_analysis:
                    # Create optimization metrics record linked to this route
                    metrics_record = OptimizationMetrics(
                        route_id=route_db.id,
                        optimization_date=route_date,
                        optimization_timestamp=datetime.utcnow(),
                        strategy_used=result.strategy_used,
                        total_cases_requested=result.skill_gap_analysis.total_cases_requested,
                        total_cases_assigned=result.skill_gap_analysis.total_cases_assigned,
                        total_cases_unassigned=result.skill_gap_analysis.total_cases_unassigned,
                        assignment_rate_percentage=result.skill_gap_analysis.assignment_rate_percentage,
                        optimization_time_seconds=result.optimization_time,
                        total_distance_km=result.total_distance,
                        total_time_minutes=result.total_time,
                        skill_gaps=result.skill_gap_analysis.to_dict()
                    )
                    self.db.add(metrics_record)

            # Also save overall optimization metrics (not linked to specific route)
            # This captures optimization runs even if they fail completely
            if result.skill_gap_analysis:
                overall_metrics = OptimizationMetrics(
                    route_id=None,  # Not linked to any specific route (overall metrics)
                    optimization_date=result.routes[0].date.date() if result.routes else datetime.utcnow().date(),
                    optimization_timestamp=datetime.utcnow(),
                    strategy_used=result.strategy_used,
                    total_cases_requested=result.skill_gap_analysis.total_cases_requested,
                    total_cases_assigned=result.skill_gap_analysis.total_cases_assigned,
                    total_cases_unassigned=result.skill_gap_analysis.total_cases_unassigned,
                    assignment_rate_percentage=result.skill_gap_analysis.assignment_rate_percentage,
                    optimization_time_seconds=result.optimization_time,
                    total_distance_km=result.total_distance,
                    total_time_minutes=result.total_time,
                    skill_gaps=result.skill_gap_analysis.to_dict()
                )
                self.db.add(overall_metrics)

            self.db.commit()
            logger.info(f"Persisted {len(result.routes)} routes and optimization metrics to database")

        except Exception as e:
            logger.error(f"Failed to persist routes: {e}", exc_info=True)
            self.db.rollback()
            raise
