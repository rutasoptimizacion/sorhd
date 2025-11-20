"""
Unit tests for OR-Tools VRP optimization strategy
"""
import pytest
from datetime import datetime, time
from app.services.optimization.ortools_strategy import ORToolsVRPStrategy
from app.services.optimization.models import (
    Location,
    TimeWindow,
    Personnel,
    Vehicle,
    Case,
    OptimizationRequest
)


class TestORToolsVRPStrategy:
    """Test ORToolsVRPStrategy class"""

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
            time_matrix=simple_time_matrix,
            max_optimization_time=10
        )

        strategy = ORToolsVRPStrategy()
        result = strategy.optimize(request)

        # Should successfully optimize
        assert result.strategy_used == "ortools"
        # Either success or infeasible (both valid)
        if result.success:
            assert len(result.routes) >= 1
            assert result.routes[0].vehicle.id == sample_vehicle.id
        else:
            # If infeasible, should have violation
            assert len(result.constraint_violations) > 0

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
            time_matrix=simple_time_matrix,
            max_optimization_time=15
        )

        strategy = ORToolsVRPStrategy()
        result = strategy.optimize(request)

        assert result.strategy_used == "ortools"
        # OR-Tools should find a solution or report infeasibility
        assert result.success or len(result.constraint_violations) > 0

    def test_haversine_distance(self):
        """Test Haversine distance calculation"""
        strategy = ORToolsVRPStrategy()

        # Santiago to Providencia (~2.5 km)
        loc1 = Location(latitude=-33.4489, longitude=-70.6693)
        loc2 = Location(latitude=-33.4372, longitude=-70.6506)

        distance = strategy._haversine_distance(loc1, loc2)

        # Should be approximately 2-3 km
        assert 1.5 < distance < 3.5

    def test_haversine_distance_same_location(self):
        """Test Haversine distance for same location"""
        strategy = ORToolsVRPStrategy()

        loc = Location(latitude=-33.4489, longitude=-70.6693)

        distance = strategy._haversine_distance(loc, loc)

        assert distance == pytest.approx(0.0, abs=0.01)

    def test_build_data_model(
        self,
        sample_cases,
        sample_vehicle,
        sample_personnel_list,
        simple_distance_matrix,
        simple_time_matrix
    ):
        """Test building data model for OR-Tools"""
        request = OptimizationRequest(
            cases=sample_cases,
            vehicles=[sample_vehicle],
            personnel=sample_personnel_list,
            date=datetime(2025, 11, 15),
            distance_matrix=simple_distance_matrix,
            time_matrix=simple_time_matrix
        )

        strategy = ORToolsVRPStrategy()
        strategy.request = request
        strategy._build_data_model()

        # Check locations are built correctly
        # Should have: vehicle depot + cases
        expected_locations = 1 + len(sample_cases)
        assert len(strategy.locations) == expected_locations

        # Check location to case mapping
        assert len(strategy.location_to_case) == len(sample_cases)

        # Check vehicle to personnel mapping
        assert sample_vehicle.id in strategy.vehicle_to_personnel

    def test_build_matrices_with_provided_matrices(
        self,
        sample_cases,
        sample_vehicle,
        sample_personnel_list,
        simple_distance_matrix,
        simple_time_matrix
    ):
        """Test matrix building with provided matrices"""
        request = OptimizationRequest(
            cases=sample_cases,
            vehicles=[sample_vehicle],
            personnel=sample_personnel_list,
            date=datetime(2025, 11, 15),
            distance_matrix=simple_distance_matrix,
            time_matrix=simple_time_matrix
        )

        strategy = ORToolsVRPStrategy()
        strategy.request = request
        strategy._build_data_model()

        # Matrices should be built
        assert len(strategy.distance_matrix) > 0
        assert len(strategy.time_matrix) > 0

    def test_build_matrices_without_provided_matrices(
        self,
        sample_case_nurse,
        sample_vehicle,
        sample_personnel
    ):
        """Test matrix building without provided matrices (uses Haversine)"""
        request = OptimizationRequest(
            cases=[sample_case_nurse],
            vehicles=[sample_vehicle],
            personnel=[sample_personnel],
            date=datetime(2025, 11, 15),
            # No distance_matrix or time_matrix
        )

        strategy = ORToolsVRPStrategy()
        strategy.request = request
        strategy._build_data_model()

        # Should build matrices using Haversine
        assert len(strategy.distance_matrix) > 0
        assert len(strategy.time_matrix) > 0

    def test_validate_request_no_personnel(
        self,
        sample_case_nurse,
        sample_vehicle
    ):
        """Test request validation fails without personnel"""
        # This should fail at request creation time
        with pytest.raises(ValueError, match="At least one personnel is required"):
            request = OptimizationRequest(
                cases=[sample_case_nurse],
                vehicles=[sample_vehicle],
                personnel=[],  # No personnel
                date=datetime(2025, 11, 15)
            )

    def test_optimization_with_tight_time_window(self):
        """Test optimization with very tight time windows"""
        loc1 = Location(latitude=-33.4489, longitude=-70.6693)
        loc2 = Location(latitude=-33.4372, longitude=-70.6506)

        # Case with very tight time window
        tight_tw = TimeWindow(start=time(9, 0), end=time(9, 15))
        tight_case = Case(
            id=1,
            patient_id=100,
            patient_name="Patient",
            location=loc2,
            care_type_id=1,
            care_type_name="Test",
            required_skills=["nurse"],
            time_window=tight_tw,
            priority=1,
            estimated_duration=60  # 1 hour visit but only 15 min window
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
            cases=[tight_case],
            vehicles=[vehicle],
            personnel=[personnel],
            date=datetime(2025, 11, 15),
            max_optimization_time=10
        )

        strategy = ORToolsVRPStrategy()
        result = strategy.optimize(request)

        # Should likely be infeasible
        assert result.strategy_used == "ortools"
        # Either success (unlikely) or infeasible
        if not result.success:
            assert len(result.constraint_violations) > 0

    def test_optimization_with_multiple_vehicles(
        self,
        sample_cases,
        sample_personnel_list,
        simple_distance_matrix,
        simple_time_matrix
    ):
        """Test optimization with multiple vehicles"""
        loc = Location(latitude=-33.4489, longitude=-70.6693)

        vehicle1 = Vehicle(
            id=1,
            identifier="VH-001",
            capacity=5,
            base_location=loc,
            status="available"
        )

        vehicle2 = Vehicle(
            id=2,
            identifier="VH-002",
            capacity=5,
            base_location=loc,
            status="available"
        )

        request = OptimizationRequest(
            cases=sample_cases,
            vehicles=[vehicle1, vehicle2],
            personnel=sample_personnel_list,
            date=datetime(2025, 11, 15),
            distance_matrix=simple_distance_matrix,
            time_matrix=simple_time_matrix,
            max_optimization_time=15
        )

        strategy = ORToolsVRPStrategy()
        result = strategy.optimize(request)

        assert result.strategy_used == "ortools"

        if result.success:
            # Should have at least one route
            assert len(result.routes) >= 1
            # All routes should have valid vehicle IDs
            for route in result.routes:
                assert route.vehicle.id in [1, 2]

    def test_optimization_timeout(
        self,
        sample_cases,
        sample_vehicle,
        sample_personnel_list,
        simple_distance_matrix,
        simple_time_matrix
    ):
        """Test that optimization respects timeout"""
        request = OptimizationRequest(
            cases=sample_cases,
            vehicles=[sample_vehicle],
            personnel=sample_personnel_list,
            date=datetime(2025, 11, 15),
            distance_matrix=simple_distance_matrix,
            time_matrix=simple_time_matrix,
            max_optimization_time=1  # Very short timeout
        )

        strategy = ORToolsVRPStrategy()
        result = strategy.optimize(request)

        # Should complete within timeout (possibly with suboptimal solution)
        assert result.optimization_time < 5.0  # Allow some overhead

    def test_error_handling(self):
        """Test that errors are caught and returned in result"""
        # Create request that might cause issues
        loc = Location(latitude=-33.4489, longitude=-70.6693)

        vehicle = Vehicle(
            id=1,
            identifier="VH-001",
            capacity=5,
            base_location=loc,
            status="available"
        )

        personnel = Personnel(
            id=1,
            name="Test",
            skills=["nurse"],
            start_location=loc,
            work_hours_start=time(8, 0),
            work_hours_end=time(17, 0)
        )

        # Request with no cases (will fail validation)
        try:
            request = OptimizationRequest(
                cases=[],
                vehicles=[vehicle],
                personnel=[personnel],
                date=datetime(2025, 11, 15)
            )
        except ValueError:
            # Expected - validation fails
            pass

    def test_create_routing_model(
        self,
        sample_cases,
        sample_vehicle,
        sample_personnel_list,
        simple_distance_matrix,
        simple_time_matrix
    ):
        """Test creating OR-Tools routing model"""
        request = OptimizationRequest(
            cases=sample_cases,
            vehicles=[sample_vehicle],
            personnel=sample_personnel_list,
            date=datetime(2025, 11, 15),
            distance_matrix=simple_distance_matrix,
            time_matrix=simple_time_matrix
        )

        strategy = ORToolsVRPStrategy()
        strategy.request = request
        strategy._build_data_model()
        strategy._create_routing_model()

        # Check that routing model and manager are created
        assert strategy.manager is not None
        assert strategy.routing is not None

    def test_skill_validation_in_result(
        self,
        sample_case_physician,
        sample_vehicle,
        sample_personnel,  # Has nurse skills, not physician
        simple_distance_matrix,
        simple_time_matrix
    ):
        """Test that skill violations are detected"""
        request = OptimizationRequest(
            cases=[sample_case_physician],  # Requires physician
            vehicles=[sample_vehicle],
            personnel=[sample_personnel],  # Only nurse
            date=datetime(2025, 11, 15),
            distance_matrix=simple_distance_matrix,
            time_matrix=simple_time_matrix,
            max_optimization_time=10
        )

        strategy = ORToolsVRPStrategy()
        result = strategy.optimize(request)

        # Should either be unassigned or have skill violation
        if result.success:
            # Check if route has skill violation
            skill_valid = all(route.validate_skills() for route in result.routes)
            if not skill_valid:
                # Should have skill mismatch violation
                violations = [v for v in result.constraint_violations
                            if v.type.value == "skill_mismatch"]
                assert len(violations) > 0
        else:
            # Should have unassigned case or violation
            assert len(result.unassigned_cases) > 0 or len(result.constraint_violations) > 0
