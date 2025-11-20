"""
Unit tests for optimization domain models
"""
import pytest
from datetime import datetime, time, timedelta
from app.services.optimization.models import (
    Location,
    TimeWindow,
    Personnel,
    Vehicle,
    Case,
    Visit,
    Route,
    OptimizationRequest,
    OptimizationResult,
    ConstraintViolation,
    ConstraintType
)


class TestLocation:
    """Test Location model"""

    def test_valid_location(self):
        """Test creating a valid location"""
        loc = Location(latitude=-33.4489, longitude=-70.6693)  # Santiago, Chile
        assert loc.latitude == -33.4489
        assert loc.longitude == -70.6693

    def test_location_to_tuple(self):
        """Test conversion to tuple"""
        loc = Location(latitude=-33.4489, longitude=-70.6693)
        assert loc.to_tuple() == (-33.4489, -70.6693)

    def test_invalid_latitude(self):
        """Test invalid latitude raises error"""
        with pytest.raises(ValueError, match="Invalid latitude"):
            Location(latitude=91.0, longitude=-70.0)

        with pytest.raises(ValueError, match="Invalid latitude"):
            Location(latitude=-91.0, longitude=-70.0)

    def test_invalid_longitude(self):
        """Test invalid longitude raises error"""
        with pytest.raises(ValueError, match="Invalid longitude"):
            Location(latitude=-33.0, longitude=181.0)

        with pytest.raises(ValueError, match="Invalid longitude"):
            Location(latitude=-33.0, longitude=-181.0)


class TestTimeWindow:
    """Test TimeWindow model"""

    def test_valid_time_window(self):
        """Test creating a valid time window"""
        tw = TimeWindow(start=time(8, 0), end=time(12, 0))
        assert tw.start == time(8, 0)
        assert tw.end == time(12, 0)

    def test_to_minutes(self):
        """Test conversion to minutes since midnight"""
        tw = TimeWindow(start=time(8, 0), end=time(12, 0))
        start_min, end_min = tw.to_minutes()
        assert start_min == 480  # 8 * 60
        assert end_min == 720  # 12 * 60

    def test_invalid_time_window(self):
        """Test that start >= end raises error"""
        with pytest.raises(ValueError, match="Invalid time window"):
            TimeWindow(start=time(12, 0), end=time(8, 0))

        with pytest.raises(ValueError, match="Invalid time window"):
            TimeWindow(start=time(12, 0), end=time(12, 0))


class TestPersonnel:
    """Test Personnel model"""

    def test_create_personnel(self):
        """Test creating personnel"""
        loc = Location(latitude=-33.4489, longitude=-70.6693)
        personnel = Personnel(
            id=1,
            name="Dr. Maria Silva",
            skills=["physician", "emergency"],
            start_location=loc,
            work_hours_start=time(8, 0),
            work_hours_end=time(17, 0),
            is_active=True
        )

        assert personnel.id == 1
        assert personnel.name == "Dr. Maria Silva"
        assert "physician" in personnel.skills
        assert personnel.is_active is True


class TestVehicle:
    """Test Vehicle model"""

    def test_create_vehicle(self):
        """Test creating vehicle"""
        loc = Location(latitude=-33.4489, longitude=-70.6693)
        vehicle = Vehicle(
            id=1,
            identifier="VH-001",
            capacity=5,
            base_location=loc,
            status="available",
            is_active=True,
            resources={"oxygen": True, "wheelchair": True}
        )

        assert vehicle.id == 1
        assert vehicle.identifier == "VH-001"
        assert vehicle.capacity == 5
        assert vehicle.resources["oxygen"] is True


class TestCase:
    """Test Case model"""

    def test_create_case(self):
        """Test creating a case"""
        loc = Location(latitude=-33.4489, longitude=-70.6693)
        tw = TimeWindow(start=time(8, 0), end=time(12, 0))

        case = Case(
            id=1,
            patient_id=100,
            patient_name="Juan Pérez",
            location=loc,
            care_type_id=1,
            care_type_name="Wound Care",
            required_skills=["nurse", "wound_care"],
            time_window=tw,
            priority=2,
            estimated_duration=30,
            special_instructions="Ring doorbell twice"
        )

        assert case.id == 1
        assert case.patient_name == "Juan Pérez"
        assert len(case.required_skills) == 2
        assert case.estimated_duration == 30


class TestVisit:
    """Test Visit model"""

    def test_create_visit(self):
        """Test creating a visit"""
        loc = Location(latitude=-33.4489, longitude=-70.6693)
        tw = TimeWindow(start=time(8, 0), end=time(12, 0))
        case = Case(
            id=1,
            patient_id=100,
            patient_name="Juan Pérez",
            location=loc,
            care_type_id=1,
            care_type_name="Wound Care",
            required_skills=["nurse"],
            time_window=tw,
            priority=2,
            estimated_duration=30
        )

        visit = Visit(
            case=case,
            sequence=0,
            arrival_time=datetime(2025, 11, 15, 9, 0),
            start_time=datetime(2025, 11, 15, 9, 0),
            end_time=datetime(2025, 11, 15, 9, 30),
            travel_time_from_previous=0,
            distance_from_previous=0.0
        )

        assert visit.sequence == 0
        assert visit.case.patient_name == "Juan Pérez"
        assert visit.travel_time_from_previous == 0


class TestRoute:
    """Test Route model"""

    def test_create_route(self):
        """Test creating a route"""
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
            name="Dr. Maria Silva",
            skills=["nurse", "wound_care"],
            start_location=loc,
            work_hours_start=time(8, 0),
            work_hours_end=time(17, 0)
        )

        route = Route(
            vehicle=vehicle,
            personnel=[personnel],
            visits=[],
            date=datetime(2025, 11, 15),
            total_distance=10.5,
            total_time=120
        )

        assert route.vehicle.identifier == "VH-001"
        assert len(route.personnel) == 1
        assert route.total_distance == 10.5

    def test_route_validate_skills_success(self):
        """Test skill validation succeeds when personnel have required skills"""
        loc = Location(latitude=-33.4489, longitude=-70.6693)
        tw = TimeWindow(start=time(8, 0), end=time(12, 0))

        vehicle = Vehicle(
            id=1,
            identifier="VH-001",
            capacity=5,
            base_location=loc,
            status="available"
        )

        personnel = Personnel(
            id=1,
            name="Dr. Maria Silva",
            skills=["nurse", "wound_care", "physician"],
            start_location=loc,
            work_hours_start=time(8, 0),
            work_hours_end=time(17, 0)
        )

        case = Case(
            id=1,
            patient_id=100,
            patient_name="Juan Pérez",
            location=loc,
            care_type_id=1,
            care_type_name="Wound Care",
            required_skills=["nurse", "wound_care"],
            time_window=tw,
            priority=2,
            estimated_duration=30
        )

        visit = Visit(
            case=case,
            sequence=0,
            arrival_time=datetime(2025, 11, 15, 9, 0),
            start_time=datetime(2025, 11, 15, 9, 0),
            end_time=datetime(2025, 11, 15, 9, 30)
        )

        route = Route(
            vehicle=vehicle,
            personnel=[personnel],
            visits=[visit],
            date=datetime(2025, 11, 15)
        )

        assert route.validate_skills() is True

    def test_route_validate_skills_failure(self):
        """Test skill validation fails when personnel lack required skills"""
        loc = Location(latitude=-33.4489, longitude=-70.6693)
        tw = TimeWindow(start=time(8, 0), end=time(12, 0))

        vehicle = Vehicle(
            id=1,
            identifier="VH-001",
            capacity=5,
            base_location=loc,
            status="available"
        )

        personnel = Personnel(
            id=1,
            name="Dr. Maria Silva",
            skills=["nurse"],  # Missing "wound_care" skill
            start_location=loc,
            work_hours_start=time(8, 0),
            work_hours_end=time(17, 0)
        )

        case = Case(
            id=1,
            patient_id=100,
            patient_name="Juan Pérez",
            location=loc,
            care_type_id=1,
            care_type_name="Wound Care",
            required_skills=["nurse", "wound_care"],
            time_window=tw,
            priority=2,
            estimated_duration=30
        )

        visit = Visit(
            case=case,
            sequence=0
        )

        route = Route(
            vehicle=vehicle,
            personnel=[personnel],
            visits=[visit],
            date=datetime(2025, 11, 15)
        )

        assert route.validate_skills() is False


class TestConstraintViolation:
    """Test ConstraintViolation model"""

    def test_create_violation(self):
        """Test creating a constraint violation"""
        violation = ConstraintViolation(
            type=ConstraintType.SKILL_MISMATCH,
            description="Personnel lack required skills",
            entity_id=1,
            entity_type="route",
            severity="error",
            details={"missing_skills": ["wound_care"]}
        )

        assert violation.type == ConstraintType.SKILL_MISMATCH
        assert violation.severity == "error"
        assert "missing_skills" in violation.details


class TestOptimizationRequest:
    """Test OptimizationRequest model"""

    def test_create_request(self):
        """Test creating an optimization request"""
        loc = Location(latitude=-33.4489, longitude=-70.6693)
        tw = TimeWindow(start=time(8, 0), end=time(12, 0))

        vehicle = Vehicle(
            id=1,
            identifier="VH-001",
            capacity=5,
            base_location=loc,
            status="available"
        )

        personnel = Personnel(
            id=1,
            name="Dr. Maria Silva",
            skills=["nurse"],
            start_location=loc,
            work_hours_start=time(8, 0),
            work_hours_end=time(17, 0)
        )

        case = Case(
            id=1,
            patient_id=100,
            patient_name="Juan Pérez",
            location=loc,
            care_type_id=1,
            care_type_name="Wound Care",
            required_skills=["nurse"],
            time_window=tw,
            priority=2,
            estimated_duration=30
        )

        request = OptimizationRequest(
            cases=[case],
            vehicles=[vehicle],
            personnel=[personnel],
            date=datetime(2025, 11, 15),
            max_optimization_time=60
        )

        assert len(request.cases) == 1
        assert len(request.vehicles) == 1
        assert request.max_optimization_time == 60

    def test_request_validation_no_cases(self):
        """Test that request with no cases raises error"""
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
            name="Dr. Maria Silva",
            skills=["nurse"],
            start_location=loc,
            work_hours_start=time(8, 0),
            work_hours_end=time(17, 0)
        )

        with pytest.raises(ValueError, match="At least one case is required"):
            OptimizationRequest(
                cases=[],
                vehicles=[vehicle],
                personnel=[personnel],
                date=datetime(2025, 11, 15)
            )

    def test_request_validation_no_vehicles(self):
        """Test that request with no vehicles raises error"""
        loc = Location(latitude=-33.4489, longitude=-70.6693)
        tw = TimeWindow(start=time(8, 0), end=time(12, 0))

        personnel = Personnel(
            id=1,
            name="Dr. Maria Silva",
            skills=["nurse"],
            start_location=loc,
            work_hours_start=time(8, 0),
            work_hours_end=time(17, 0)
        )

        case = Case(
            id=1,
            patient_id=100,
            patient_name="Juan Pérez",
            location=loc,
            care_type_id=1,
            care_type_name="Wound Care",
            required_skills=["nurse"],
            time_window=tw,
            priority=2,
            estimated_duration=30
        )

        with pytest.raises(ValueError, match="At least one vehicle is required"):
            OptimizationRequest(
                cases=[case],
                vehicles=[],
                personnel=[personnel],
                date=datetime(2025, 11, 15)
            )


class TestOptimizationResult:
    """Test OptimizationResult model"""

    def test_create_result(self):
        """Test creating an optimization result"""
        result = OptimizationResult(
            success=True,
            routes=[],
            unassigned_cases=[],
            constraint_violations=[],
            total_distance=15.5,
            total_time=180,
            optimization_time=5.2,
            strategy_used="ortools",
            message="Optimization completed successfully"
        )

        assert result.success is True
        assert result.total_distance == 15.5
        assert result.strategy_used == "ortools"

    def test_get_summary(self):
        """Test getting result summary"""
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
            name="Dr. Maria Silva",
            skills=["nurse"],
            start_location=loc,
            work_hours_start=time(8, 0),
            work_hours_end=time(17, 0)
        )

        route = Route(
            vehicle=vehicle,
            personnel=[personnel],
            visits=[],
            date=datetime(2025, 11, 15),
            total_distance=10.0,
            total_time=120
        )

        result = OptimizationResult(
            success=True,
            routes=[route],
            unassigned_cases=[],
            constraint_violations=[],
            total_distance=10.0,
            total_time=120,
            optimization_time=3.5,
            strategy_used="ortools",
            message="Success"
        )

        summary = result.get_summary()

        assert summary["success"] is True
        assert summary["num_routes"] == 1
        assert summary["num_assigned_cases"] == 0
        assert summary["num_unassigned_cases"] == 0
        assert summary["total_distance_km"] == 10.0
        assert summary["optimization_time_seconds"] == 3.5
        assert summary["strategy_used"] == "ortools"
