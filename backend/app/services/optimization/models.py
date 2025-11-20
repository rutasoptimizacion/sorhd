"""
Optimization Domain Models

This module defines the domain models used throughout the optimization engine.
These models are separate from database models and represent the optimization
problem space.
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum


class ConstraintType(str, Enum):
    """Types of constraint violations"""
    SKILL_MISMATCH = "skill_mismatch"
    CAPACITY_EXCEEDED = "capacity_exceeded"
    TIME_WINDOW_VIOLATION = "time_window_violation"
    WORKING_HOURS_VIOLATION = "working_hours_violation"
    INFEASIBLE = "infeasible"


@dataclass
class Location:
    """Geographic location"""
    latitude: float
    longitude: float

    def to_tuple(self) -> Tuple[float, float]:
        """Convert to (lat, lon) tuple"""
        return (self.latitude, self.longitude)

    def __post_init__(self):
        """Validate coordinates"""
        if not -90 <= self.latitude <= 90:
            raise ValueError(f"Invalid latitude: {self.latitude}")
        if not -180 <= self.longitude <= 180:
            raise ValueError(f"Invalid longitude: {self.longitude}")


@dataclass
class TimeWindow:
    """Time window constraint for a visit"""
    start: time
    end: time

    def __post_init__(self):
        """Validate time window"""
        if self.start >= self.end:
            raise ValueError(f"Invalid time window: {self.start} >= {self.end}")

    def to_minutes(self) -> Tuple[int, int]:
        """Convert to minutes since midnight"""
        start_minutes = self.start.hour * 60 + self.start.minute
        end_minutes = self.end.hour * 60 + self.end.minute
        return (start_minutes, end_minutes)


@dataclass
class Personnel:
    """Personnel information for optimization"""
    id: int
    name: str
    skills: List[str]
    start_location: Location
    work_hours_start: time
    work_hours_end: time
    is_active: bool = True


@dataclass
class Vehicle:
    """Vehicle information for optimization"""
    id: int
    identifier: str
    capacity: int
    base_location: Location
    status: str
    is_active: bool = True
    resources: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Case:
    """Case (visit request) information for optimization"""
    id: int
    patient_id: int
    patient_name: str
    location: Location
    care_type_id: int
    care_type_name: str
    required_skills: List[str]
    time_window: TimeWindow
    priority: int
    estimated_duration: int  # minutes
    special_instructions: Optional[str] = None


@dataclass
class Visit:
    """A visit in an optimized route"""
    case: Case
    sequence: int  # 0-based sequence in route
    arrival_time: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    travel_time_from_previous: Optional[int] = None  # minutes
    distance_from_previous: Optional[float] = None  # km


@dataclass
class Route:
    """An optimized route for a vehicle and personnel"""
    vehicle: Vehicle
    personnel: List[Personnel]
    visits: List[Visit]
    date: datetime
    total_distance: float = 0.0  # km
    total_time: int = 0  # minutes

    def validate_skills(self) -> bool:
        """Validate that personnel have all required skills for all visits"""
        all_personnel_skills = set()
        for person in self.personnel:
            all_personnel_skills.update(person.skills)

        for visit in self.visits:
            required_skills = set(visit.case.required_skills)
            if not required_skills.issubset(all_personnel_skills):
                return False

        return True


@dataclass
class ConstraintViolation:
    """A constraint violation found during optimization or validation"""
    type: ConstraintType
    description: str
    entity_id: Optional[int] = None
    entity_type: Optional[str] = None  # "case", "vehicle", "personnel", "route"
    severity: str = "error"  # "error", "warning"
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UnassignedCaseDetail:
    """Details about why a case could not be assigned"""
    case_id: int
    case_name: str
    required_skills: List[str]
    missing_skills: List[str]  # Skills required but not available in any selected vehicle
    priority: int


@dataclass
class SkillGapAnalysis:
    """
    Analysis of skill gaps and their business impact.
    Provides actionable insights for hiring decisions.
    """
    # Unassigned cases grouped by missing skills
    unassigned_cases_by_skill: Dict[str, List[int]] = field(default_factory=dict)  # skill -> [case_ids]

    # Detailed information about unassigned cases
    unassigned_case_details: List[UnassignedCaseDetail] = field(default_factory=list)

    # Skills ranked by frequency in unassigned cases (hiring priority)
    most_demanded_skills: List[Tuple[str, int]] = field(default_factory=list)  # [(skill, count)]

    # Coverage percentage per skill: cases requiring skill vs available personnel
    skill_coverage_percentage: Dict[str, float] = field(default_factory=dict)  # skill -> percentage (0-100)

    # Simulation: additional cases that could be assigned if one person with each skill is hired
    hiring_impact_simulation: Dict[str, int] = field(default_factory=dict)  # skill -> additional_cases

    # Summary metrics
    total_cases_requested: int = 0
    total_cases_assigned: int = 0
    total_cases_unassigned: int = 0
    assignment_rate_percentage: float = 0.0  # percentage (0-100)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "unassigned_cases_by_skill": self.unassigned_cases_by_skill,
            "unassigned_case_details": [
                {
                    "case_id": detail.case_id,
                    "case_name": detail.case_name,
                    "required_skills": detail.required_skills,
                    "missing_skills": detail.missing_skills,
                    "priority": detail.priority
                }
                for detail in self.unassigned_case_details
            ],
            "most_demanded_skills": [
                {"skill": skill, "demand_count": count}
                for skill, count in self.most_demanded_skills
            ],
            "skill_coverage_percentage": self.skill_coverage_percentage,
            "hiring_impact_simulation": self.hiring_impact_simulation,
            "summary": {
                "total_cases_requested": self.total_cases_requested,
                "total_cases_assigned": self.total_cases_assigned,
                "total_cases_unassigned": self.total_cases_unassigned,
                "assignment_rate_percentage": self.assignment_rate_percentage
            }
        }


@dataclass
class OptimizationRequest:
    """Request for route optimization"""
    cases: List[Case]
    vehicles: List[Vehicle]
    personnel: List[Personnel]
    date: datetime
    distance_matrix: Optional[Dict[Tuple[int, int], float]] = None  # (from_idx, to_idx) -> distance in km
    time_matrix: Optional[Dict[Tuple[int, int], int]] = None  # (from_idx, to_idx) -> time in minutes

    # Optimization parameters
    max_optimization_time: int = 60  # seconds
    use_heuristic_fallback: bool = True

    def __post_init__(self):
        """Validate request"""
        if not self.cases:
            raise ValueError("At least one case is required")
        if not self.vehicles:
            raise ValueError("At least one vehicle is required")
        if not self.personnel:
            raise ValueError("At least one personnel is required")


@dataclass
class OptimizationResult:
    """Result of route optimization"""
    success: bool
    routes: List[Route]
    unassigned_cases: List[Case]
    constraint_violations: List[ConstraintViolation]

    # Metrics
    total_distance: float = 0.0  # km
    total_time: int = 0  # minutes
    optimization_time: float = 0.0  # seconds
    strategy_used: str = "unknown"  # "ortools", "heuristic"

    # Skill gap analysis for business insights
    skill_gap_analysis: Optional[SkillGapAnalysis] = None

    # Details
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the optimization result"""
        return {
            "success": self.success,
            "strategy_used": self.strategy_used,
            "num_routes": len(self.routes),
            "num_assigned_cases": sum(len(route.visits) for route in self.routes),
            "num_unassigned_cases": len(self.unassigned_cases),
            "num_violations": len(self.constraint_violations),
            "total_distance_km": round(self.total_distance, 2),
            "total_time_minutes": self.total_time,
            "optimization_time_seconds": round(self.optimization_time, 2),
            "message": self.message
        }


# Helper functions

def select_optimal_personnel(
    available_personnel: List[Personnel],
    cases: List[Case],
    vehicle_capacity: int
) -> List[Personnel]:
    """
    Select the optimal (minimal) set of personnel to cover all required skills.

    Uses a greedy set cover algorithm to minimize the number of personnel
    while ensuring all required skills are covered.

    Args:
        available_personnel: List of available personnel
        cases: List of cases that need to be covered
        vehicle_capacity: Maximum number of personnel that can be assigned

    Returns:
        List of selected personnel (minimal set that covers all skills)
    """
    if not cases:
        return []

    # Collect all required skills from all cases
    required_skills = set()
    for case in cases:
        required_skills.update(case.required_skills)

    if not required_skills:
        return []

    # Greedy set cover: select personnel that covers most uncovered skills
    selected_personnel = []
    uncovered_skills = required_skills.copy()

    while uncovered_skills and len(selected_personnel) < vehicle_capacity:
        # Find personnel that covers the most uncovered skills
        best_person = None
        best_coverage = 0

        for person in available_personnel:
            if person in selected_personnel:
                continue

            # Count how many uncovered skills this person has
            person_skills = set(person.skills)
            coverage = len(uncovered_skills & person_skills)

            if coverage > best_coverage:
                best_coverage = coverage
                best_person = person

        # If no person covers any remaining skills, we can't cover all skills
        if best_person is None or best_coverage == 0:
            break

        # Add the best person to the selection
        selected_personnel.append(best_person)

        # Remove covered skills
        uncovered_skills -= set(best_person.skills)

    return selected_personnel


def assign_personnel_to_vehicles(
    vehicles: List['Vehicle'],
    personnel: List[Personnel],
    cases: List[Case]
) -> Dict[int, List[Personnel]]:
    """
    Pre-assign personnel to vehicles BEFORE route optimization.

    IMPROVED STRATEGY (Balanced Round-Robin with Skill Diversity Priority):
    1. Sort personnel by skill diversity (multi-skilled personnel first)
    2. Distribute personnel evenly across vehicles using balanced round-robin
    3. Track capacity dynamically to prevent clustering
    4. Maximize skill coverage per vehicle

    This ensures rare/unique skills are distributed evenly across vehicles,
    not concentrated in one vehicle (which was the previous algorithm's flaw).

    Args:
        vehicles: List of available vehicles
        personnel: List of available personnel
        cases: List of cases to be optimized

    Returns:
        Dictionary mapping vehicle.id -> List[Personnel]
    """
    import logging
    logger = logging.getLogger(__name__)

    # Initialize assignments
    vehicle_assignments = {vehicle.id: [] for vehicle in vehicles}
    assigned_personnel_ids = set()

    # Sort personnel by skill diversity (multi-skilled personnel provide more value)
    # Tie-break by ID for consistency
    personnel_by_diversity = sorted(
        personnel,
        key=lambda p: (-len(p.skills), p.id)
    )

    # Sort vehicles by ID for consistent, balanced assignment (NOT by capacity)
    sorted_vehicles = sorted(vehicles, key=lambda v: v.id)

    # Balanced round-robin assignment
    vehicle_idx = 0
    for person in personnel_by_diversity:
        if person.id in assigned_personnel_ids:
            continue

        # Find next vehicle with available capacity
        attempts = 0
        while attempts < len(sorted_vehicles):
            current_vehicle = sorted_vehicles[vehicle_idx % len(sorted_vehicles)]

            if len(vehicle_assignments[current_vehicle.id]) < current_vehicle.capacity:
                # Assign to this vehicle
                vehicle_assignments[current_vehicle.id].append(person)
                assigned_personnel_ids.add(person.id)

                # Move to next vehicle for balanced distribution
                vehicle_idx += 1
                break

            # This vehicle is full, try next
            vehicle_idx += 1
            attempts += 1

        # If all vehicles are full, person remains unassigned
        if attempts >= len(sorted_vehicles):
            logger.warning(
                f"⚠️  Personnel {person.name} (ID {person.id}) could not be assigned - all vehicles at capacity"
            )

    # Collect all required skills for coverage analysis
    all_required_skills = set()
    for case in cases:
        all_required_skills.update(case.required_skills)

    # Log final assignments and skill coverage
    logger.info("=" * 80)
    logger.info("📋 PERSONNEL ASSIGNMENTS:")
    for vehicle in sorted_vehicles:
        assigned = vehicle_assignments[vehicle.id]
        team_skills = set()
        for p in assigned:
            team_skills.update(p.skills)

        person_names = [f"{p.name} ({', '.join(p.skills)})" for p in assigned]
        logger.info(
            f"  🚗 {vehicle.identifier}: {len(assigned)}/{vehicle.capacity} personnel, "
            f"{len(team_skills)} unique skills: {sorted(team_skills)}"
        )
        for person_info in person_names:
            logger.info(f"     - {person_info}")

    # Check skill coverage
    uncovered_skills = all_required_skills.copy()
    for vehicle in sorted_vehicles:
        assigned = vehicle_assignments[vehicle.id]
        for person in assigned:
            uncovered_skills -= set(person.skills)

    if uncovered_skills:
        logger.warning(f"⚠️  UNCOVERED SKILLS across ALL vehicles: {sorted(uncovered_skills)}")
        logger.warning(f"    Cases requiring these skills cannot be assigned to any vehicle")
    else:
        logger.info("✅ ALL required skills covered by at least one vehicle")

    logger.info("=" * 80)

    return vehicle_assignments


def get_allowed_vehicles_for_case(
    case: Case,
    vehicles: List['Vehicle'],
    vehicle_personnel_map: Dict[int, List[Personnel]]
) -> List[int]:
    """
    Determine which vehicles can serve a case based on personnel skills.

    Args:
        case: The case to check
        vehicles: List of all vehicles
        vehicle_personnel_map: Mapping of vehicle.id -> assigned personnel

    Returns:
        List of vehicle indices that can serve this case
    """
    allowed_vehicle_indices = []

    required_skills = set(case.required_skills)

    for i, vehicle in enumerate(vehicles):
        # Get personnel assigned to this vehicle
        assigned_personnel = vehicle_personnel_map.get(vehicle.id, [])

        # Get collective skills of this team
        team_skills = set()
        for person in assigned_personnel:
            team_skills.update(person.skills)

        # Check if team has all required skills
        if required_skills.issubset(team_skills):
            allowed_vehicle_indices.append(i)

    return allowed_vehicle_indices
