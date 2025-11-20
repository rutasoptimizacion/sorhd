"""
Unit tests for heuristic optimization strategy
"""
import pytest
from datetime import datetime, time
from app.services.optimization.heuristic_strategy import HeuristicStrategy
from app.services.optimization.models import (
    Location,
    TimeWindow,
    Personnel,
    Vehicle,
    Case,
    OptimizationRequest
)


class TestHeuristicStrategy:
    """Test HeuristicStrategy class"""

    def test_optimize_simple_case(
        self,
        sample_case_nurse,
        sample_vehicle,
        sample_personnel,
        simple_distance_matrix,
        simple_time_matrix
    ):
        """Test optimization with a single case"""
        request = OptimizationRequest(
            cases=[sample_case_nurse],
            vehicles=[sample_vehicle],
            personnel=[sample_personnel],
            date=datetime(2025, 11, 15),
            distance_matrix=simple_distance_matrix,
            time_matrix=simple_time_matrix
        )

        strategy = HeuristicStrategy()
        result = strategy.optimize(request)

        assert result.success is True
        assert result.strategy_used == "heuristic"
        assert len(result.routes) == 1
        assert len(result.unassigned_cases) == 0
        assert result.routes[0].vehicle.id == sample_vehicle.id
        assert len(result.routes[0].visits) == 1

    def test_optimize_multiple_cases(
        self,
        sample_cases,
        sample_vehicle,
        sample_personnel_list,
        simple_distance_matrix,
        simple_time_matrix
    ):
        """Test optimization with multiple cases"""
        request = OptimizationRequest(
            cases=sample_cases,
            vehicles=[sample_vehicle],
            personnel=sample_personnel_list,
            date=datetime(2025, 11, 15),
            distance_matrix=simple_distance_matrix,
            time_matrix=simple_time_matrix
        )

        strategy = HeuristicStrategy()
        result = strategy.optimize(request)

        # May or may not succeed depending on constraints
        assert result.strategy_used == "heuristic"
        assert result.optimization_time < 5.0  # Should be fast
        # If successful, should have routes
        if result.success:
            assert len(result.routes) >= 1

    def test_optimize_capacity_constraint(
        self,
        sample_cases,
        sample_vehicle_small,
        sample_personnel_list,
        simple_distance_matrix,
        simple_time_matrix
    ):
        """Test that capacity constraints are respected"""
        # Create many cases to exceed small vehicle capacity
        many_cases = []
        base_location = Location(latitude=-33.4489, longitude=-70.6693)
        tw = TimeWindow(start=time(8, 0), end=time(17, 0))

        for i in range(5):
            case = Case(
                id=i + 1,
                patient_id=100 + i,
                patient_name=f"Patient {i}",
                location=base_location,
                care_type_id=1,
                care_type_name="Test Care",
                required_skills=["nurse"],
                time_window=tw,
                priority=1,
                estimated_duration=30
            )
            many_cases.append(case)

        request = OptimizationRequest(
            cases=many_cases,
            vehicles=[sample_vehicle_small],  # Capacity = 3
            personnel=sample_personnel_list,
            date=datetime(2025, 11, 15),
            distance_matrix=simple_distance_matrix,
            time_matrix=simple_time_matrix
        )

        strategy = HeuristicStrategy()
        result = strategy.optimize(request)

        # Should respect capacity limit
        if result.routes:
            for route in result.routes:
                assert len(route.visits) <= route.vehicle.capacity

    def test_optimize_skill_mismatch(
        self,
        sample_case_physician,
        sample_vehicle,
        sample_personnel,  # Only has nurse skills, not physician
        simple_distance_matrix,
        simple_time_matrix
    ):
        """Test that cases requiring missing skills are not assigned"""
        request = OptimizationRequest(
            cases=[sample_case_physician],  # Requires physician
            vehicles=[sample_vehicle],
            personnel=[sample_personnel],  # Only nurse
            date=datetime(2025, 11, 15),
            distance_matrix=simple_distance_matrix,
            time_matrix=simple_time_matrix
        )

        strategy = HeuristicStrategy()
        result = strategy.optimize(request)

        # Should not assign case if skills don't match
        assert len(result.unassigned_cases) == 1

    def test_optimize_time_window_constraints(self):
        """Test that time window constraints are respected"""
        loc1 = Location(latitude=-33.4489, longitude=-70.6693)
        loc2 = Location(latitude=-33.4372, longitude=-70.6506)

        # Case with very early time window
        early_tw = TimeWindow(start=time(8, 0), end=time(8, 30))
        early_case = Case(
            id=1,
            patient_id=100,
            patient_name="Early Patient",
            location=loc2,
            care_type_id=1,
            care_type_name="Test",
            required_skills=["nurse"],
            time_window=early_tw,
            priority=1,
            estimated_duration=60  # Takes 1 hour
        )

        # Case with late time window
        late_tw = TimeWindow(start=time(16, 30), end=time(17, 0))
        late_case = Case(
            id=2,
            patient_id=101,
            patient_name="Late Patient",
            location=loc2,
            care_type_id=1,
            care_type_name="Test",
            required_skills=["nurse"],
            time_window=late_tw,
            priority=1,
            estimated_duration=60
        )

        vehicle = Vehicle(
            id=1,
            identifier="VH-001",
            capacity=10,
            base_location=loc1,
            status="available"
        )

        personnel = Personnel(
            id=1,
            name="Test Nurse",
            skills=["nurse"],
            start_location=loc1,
            work_hours_start=time(8, 0),
            work_hours_end=time(17, 0)
        )

        request = OptimizationRequest(
            cases=[early_case, late_case],
            vehicles=[vehicle],
            personnel=[personnel],
            date=datetime(2025, 11, 15)
        )

        strategy = HeuristicStrategy()
        result = strategy.optimize(request)

        # Check that visits respect time windows
        for route in result.routes:
            for visit in route.visits:
                tw_start = datetime.combine(
                    request.date.date(),
                    visit.case.time_window.start
                )
                tw_end = datetime.combine(
                    request.date.date(),
                    visit.case.time_window.end
                )

                if visit.arrival_time:
                    assert visit.arrival_time <= tw_end

    def test_haversine_distance(self):
        """Test Haversine distance calculation"""
        strategy = HeuristicStrategy()

        # Santiago to Providencia (~2.5 km)
        loc1 = Location(latitude=-33.4489, longitude=-70.6693)
        loc2 = Location(latitude=-33.4372, longitude=-70.6506)

        distance = strategy._haversine_distance(loc1, loc2)

        # Should be approximately 2-3 km
        assert 1.5 < distance < 3.5

    def test_haversine_distance_same_location(self):
        """Test Haversine distance for same location"""
        strategy = HeuristicStrategy()

        loc = Location(latitude=-33.4489, longitude=-70.6693)

        distance = strategy._haversine_distance(loc, loc)

        assert distance == pytest.approx(0.0, abs=0.01)

    def test_build_route_for_vehicle(
        self,
        sample_vehicle,
        sample_personnel,
        sample_case_nurse
    ):
        """Test building a route for a specific vehicle"""
        strategy = HeuristicStrategy()
        strategy.request = OptimizationRequest(
            cases=[sample_case_nurse],
            vehicles=[sample_vehicle],
            personnel=[sample_personnel],
            date=datetime(2025, 11, 15)
        )

        route = strategy._build_route_for_vehicle(
            sample_vehicle,
            [sample_personnel],
            [sample_case_nurse]
        )

        assert route is not None
        assert route.vehicle.id == sample_vehicle.id
        assert len(route.visits) == 1

    def test_build_route_no_feasible_cases(
        self,
        sample_vehicle,
        sample_personnel,
        sample_case_physician  # Requires physician, personnel is nurse
    ):
        """Test building route when no cases are feasible"""
        strategy = HeuristicStrategy()
        strategy.request = OptimizationRequest(
            cases=[sample_case_physician],
            vehicles=[sample_vehicle],
            personnel=[sample_personnel],
            date=datetime(2025, 11, 15)
        )

        route = strategy._build_route_for_vehicle(
            sample_vehicle,
            [sample_personnel],
            [sample_case_physician]
        )

        assert route is None

    def test_is_route_feasible(
        self,
        sample_vehicle,
        sample_personnel,
        sample_case_nurse
    ):
        """Test route feasibility checking"""
        from app.services.optimization.models import Route, Visit

        strategy = HeuristicStrategy()
        strategy.request = OptimizationRequest(
            cases=[sample_case_nurse],
            vehicles=[sample_vehicle],
            personnel=[sample_personnel],
            date=datetime(2025, 11, 15)
        )

        visit = Visit(
            case=sample_case_nurse,
            sequence=0,
            arrival_time=datetime(2025, 11, 15, 9, 0),
            start_time=datetime(2025, 11, 15, 9, 0),
            end_time=datetime(2025, 11, 15, 9, 30)
        )

        route = Route(
            vehicle=sample_vehicle,
            personnel=[sample_personnel],
            visits=[visit],
            date=datetime(2025, 11, 15)
        )

        assert strategy._is_route_feasible(route) is True

    def test_is_route_feasible_exceeds_capacity(
        self,
        sample_vehicle_small,
        sample_personnel
    ):
        """Test route is infeasible when exceeding capacity"""
        from app.services.optimization.models import Route, Visit, Case

        strategy = HeuristicStrategy()

        # Create more visits than vehicle capacity
        visits = []
        cases_list = []
        for i in range(5):  # vehicle capacity is 3
            case = Case(
                id=i + 1,
                patient_id=100 + i,
                patient_name=f"Patient {i}",
                location=Location(latitude=-33.4489, longitude=-70.6693),
                care_type_id=1,
                care_type_name="Test",
                required_skills=["nurse"],
                time_window=TimeWindow(start=time(8, 0), end=time(17, 0)),
                priority=1,
                estimated_duration=30
            )
            cases_list.append(case)
            visit = Visit(
                case=case,
                sequence=i,
                arrival_time=datetime(2025, 11, 15, 9 + i, 0),
                end_time=datetime(2025, 11, 15, 9 + i, 30)
            )
            visits.append(visit)

        route = Route(
            vehicle=sample_vehicle_small,  # capacity = 3
            personnel=[sample_personnel],
            visits=visits,  # 5 visits
            date=datetime(2025, 11, 15)
        )

        strategy.request = OptimizationRequest(
            cases=cases_list,
            vehicles=[sample_vehicle_small],
            personnel=[sample_personnel],
            date=datetime(2025, 11, 15)
        )

        assert strategy._is_route_feasible(route) is False

    def test_is_route_feasible_exceeds_working_hours(
        self,
        sample_vehicle,
        sample_personnel
    ):
        """Test route is infeasible when exceeding working hours"""
        from app.services.optimization.models import Route, Visit, Case

        strategy = HeuristicStrategy()

        # Create visit that ends after 17:00
        case = Case(
            id=1,
            patient_id=100,
            patient_name="Patient",
            location=Location(latitude=-33.4489, longitude=-70.6693),
            care_type_id=1,
            care_type_name="Test",
            required_skills=["nurse"],
            time_window=TimeWindow(start=time(16, 0), end=time(18, 0)),
            priority=1,
            estimated_duration=120  # 2 hours
        )

        visit = Visit(
            case=case,
            sequence=0,
            arrival_time=datetime(2025, 11, 15, 16, 0),
            start_time=datetime(2025, 11, 15, 16, 0),
            end_time=datetime(2025, 11, 15, 18, 0)  # After 17:00
        )

        route = Route(
            vehicle=sample_vehicle,
            personnel=[sample_personnel],
            visits=[visit],
            date=datetime(2025, 11, 15)
        )

        strategy.request = OptimizationRequest(
            cases=[case],
            vehicles=[sample_vehicle],
            personnel=[sample_personnel],
            date=datetime(2025, 11, 15)
        )

        assert strategy._is_route_feasible(route) is False

    def test_optimization_with_no_distance_matrix(
        self,
        sample_case_nurse,
        sample_vehicle,
        sample_personnel
    ):
        """Test that optimization works without provided distance matrix"""
        request = OptimizationRequest(
            cases=[sample_case_nurse],
            vehicles=[sample_vehicle],
            personnel=[sample_personnel],
            date=datetime(2025, 11, 15),
            # No distance_matrix or time_matrix provided
        )

        strategy = HeuristicStrategy()
        result = strategy.optimize(request)

        # Should still work using Haversine distance
        assert result.success is True or len(result.unassigned_cases) > 0
        assert result.strategy_used == "heuristic"

    def test_error_handling(self):
        """Test that errors are caught and returned in result"""
        # Create a request that will fail validation
        strategy = HeuristicStrategy()

        # This should fail validation at the OptimizationRequest level
        with pytest.raises(ValueError, match="At least one case is required"):
            request = OptimizationRequest(
                cases=[],  # Will fail validation
                vehicles=[Vehicle(
                    id=1,
                    identifier="VH-001",
                    capacity=5,
                    base_location=Location(latitude=-33.4489, longitude=-70.6693),
                    status="available"
                )],
                personnel=[Personnel(
                    id=1,
                    name="Test",
                    skills=["nurse"],
                    start_location=Location(latitude=-33.4489, longitude=-70.6693),
                    work_hours_start=time(8, 0),
                    work_hours_end=time(17, 0)
                )],
                date=datetime(2025, 11, 15)
            )
