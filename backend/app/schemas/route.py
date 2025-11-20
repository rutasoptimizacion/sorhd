"""
Route Schemas
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from datetime import date as DateType  # Renamed to avoid shadowing
from datetime import time as TimeType  # Renamed for consistency
from enum import Enum


class RouteStatus(str, Enum):
    """Route status enum"""
    DRAFT = "draft"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VisitStatus(str, Enum):
    """Visit status enum"""
    PENDING = "pending"
    EN_ROUTE = "en_route"
    ARRIVED = "arrived"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class OptimizationRequest(BaseModel):
    """Request schema for route optimization"""
    case_ids: List[int] = Field(..., min_length=1, description="List of case IDs to optimize")
    vehicle_ids: List[int] = Field(..., min_length=1, description="List of vehicle IDs to use")
    date: DateType = Field(..., description="Date for the routes")
    use_heuristic: bool = Field(False, description="Force use of heuristic algorithm")
    max_optimization_time: int = Field(60, ge=10, le=300, description="Maximum optimization time in seconds")

    model_config = ConfigDict(from_attributes=True)


class VisitBase(BaseModel):
    """Base visit schema"""
    case_id: int
    sequence_number: int
    estimated_arrival_time: Optional[datetime] = None
    estimated_departure_time: Optional[datetime] = None
    status: VisitStatus = VisitStatus.PENDING

    model_config = ConfigDict(from_attributes=True)


class VisitCreate(VisitBase):
    """Create visit schema"""
    route_id: int


class VisitUpdate(BaseModel):
    """Update visit schema"""
    status: Optional[VisitStatus] = None
    actual_arrival_time: Optional[datetime] = None
    actual_departure_time: Optional[datetime] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class VisitResponse(VisitBase):
    """Visit response schema"""
    id: int
    route_id: int
    actual_arrival_time: Optional[datetime] = None
    actual_departure_time: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RouteBase(BaseModel):
    """Base route schema"""
    vehicle_id: int
    route_date: DateType
    status: RouteStatus = RouteStatus.DRAFT

    model_config = ConfigDict(from_attributes=True)


class RouteCreate(RouteBase):
    """Create route schema"""
    personnel_ids: List[int] = Field(default_factory=list)


class RouteUpdate(BaseModel):
    """Update route schema"""
    status: Optional[RouteStatus] = None

    model_config = ConfigDict(from_attributes=True)


class RouteResponse(RouteBase):
    """Route response schema (without nested visits - use /routes/{id}/visits)"""
    id: int
    total_distance_km: Optional[float] = None
    total_duration_minutes: Optional[float] = None
    optimization_metadata: Optional[str] = None
    visit_count: int = 0  # Number of visits in this route
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UnassignedCaseDetailSchema(BaseModel):
    """Schema for unassigned case details"""
    case_id: int
    case_name: str
    required_skills: List[str]
    missing_skills: List[str]
    priority: int

    model_config = ConfigDict(from_attributes=True)


class SkillGapAnalysisSchema(BaseModel):
    """Schema for skill gap analysis - business insights"""
    unassigned_cases_by_skill: Dict[str, List[int]] = Field(
        default_factory=dict,
        description="Map of skill -> list of case IDs blocked by that skill"
    )
    unassigned_case_details: List[UnassignedCaseDetailSchema] = Field(
        default_factory=list,
        description="Detailed information about each unassigned case"
    )
    most_demanded_skills: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Skills ranked by demand (hiring priority). Format: [{skill: str, demand_count: int}]"
    )
    skill_coverage_percentage: Dict[str, float] = Field(
        default_factory=dict,
        description="Coverage percentage per skill (0-100)"
    )
    hiring_impact_simulation: Dict[str, int] = Field(
        default_factory=dict,
        description="Simulated impact: additional assignable cases if hiring 1 person with each skill"
    )
    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Summary metrics: total_cases_requested, total_cases_assigned, total_cases_unassigned, assignment_rate_percentage"
    )

    model_config = ConfigDict(from_attributes=True)


class OptimizationResponse(BaseModel):
    """Response schema for optimization"""
    success: bool
    message: str
    route_ids: List[int] = []  # IDs of created routes (fetch details via /routes/{id})
    unassigned_case_ids: List[int] = []
    constraint_violations: List[Dict[str, Any]] = []
    optimization_time_seconds: float
    strategy_used: str
    total_distance_km: float = 0.0
    total_time_minutes: int = 0

    # Business insights - skill gap analysis
    skill_gap_analysis: Optional[SkillGapAnalysisSchema] = Field(
        None,
        description="Comprehensive skill gap analysis for hiring decisions and business insights"
    )

    model_config = ConfigDict(from_attributes=True)


class RouteListResponse(BaseModel):
    """Route list response with pagination"""
    items: List[RouteResponse]
    total: int
    page: int
    page_size: int
    pages: int

    model_config = ConfigDict(from_attributes=True)


# Detailed schemas with nested relationships
class LocationResponse(BaseModel):
    """Location response"""
    latitude: float
    longitude: float

    model_config = ConfigDict(from_attributes=True)


class PersonnelSimple(BaseModel):
    """Simplified personnel schema for nested responses"""
    id: int
    name: str
    skills: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class VehicleSimple(BaseModel):
    """Simplified vehicle schema for nested responses"""
    id: int
    identifier: str
    capacity: int
    status: str
    resources: List[str] = []
    base_location: Optional[LocationResponse] = None

    model_config = ConfigDict(from_attributes=True)


class PatientSimple(BaseModel):
    """Simplified patient schema for nested responses"""
    id: int
    name: str
    phone: str

    model_config = ConfigDict(from_attributes=True)


class CareTypeSimple(BaseModel):
    """Simplified care type schema for nested responses"""
    id: int
    name: str
    estimated_duration_minutes: int

    model_config = ConfigDict(from_attributes=True)


class CaseSimple(BaseModel):
    """Simplified case schema for nested responses"""
    id: int
    patient_id: int
    care_type_id: int
    location: Optional[LocationResponse] = None
    priority: str  # Enum value as string (e.g., "urgent", "high", "medium", "low")
    status: str
    patient: Optional[PatientSimple] = None
    care_type: Optional[CareTypeSimple] = None

    model_config = ConfigDict(from_attributes=True)


class VisitDetailed(VisitBase):
    """Detailed visit schema with nested relationships"""
    id: int
    route_id: int
    actual_arrival_time: Optional[datetime] = None
    actual_departure_time: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    case: Optional[CaseSimple] = None
    patient: Optional[PatientSimple] = None
    care_type: Optional[CareTypeSimple] = None

    model_config = ConfigDict(from_attributes=True)


class RouteWithDetailsResponse(RouteBase):
    """Complete route response with all nested relationships"""
    id: int
    total_distance_km: Optional[float] = None
    total_duration_minutes: Optional[float] = None
    optimization_metadata: Optional[str] = None
    visit_count: int = 0
    created_at: datetime
    updated_at: datetime
    vehicle: Optional[VehicleSimple] = None
    personnel: List[PersonnelSimple] = []
    visits: List[VisitDetailed] = []

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_relationships(cls, route):
        """
        Create RouteWithDetailsResponse from ORM Route object.
        Maps assigned_personnel to personnel and loads all relationships.
        """
        from geoalchemy2.shape import to_shape

        # Build visits with nested relationships
        visits = []
        if route.visits:
            for visit in route.visits:
                visit_data = {
                    "id": visit.id,
                    "route_id": visit.route_id,
                    "case_id": visit.case_id,
                    "sequence_number": visit.sequence_number,
                    "estimated_arrival_time": visit.estimated_arrival_time,
                    "estimated_departure_time": visit.estimated_departure_time,
                    "actual_arrival_time": visit.actual_arrival_time,
                    "actual_departure_time": visit.actual_departure_time,
                    "status": visit.status,
                    "notes": visit.notes,
                    "created_at": visit.created_at,
                    "updated_at": visit.updated_at,
                }

                # Add case with nested patient and care_type
                if visit.case:
                    # Convert PostGIS location to LocationResponse
                    location = None
                    if visit.case.location:
                        point = to_shape(visit.case.location)
                        location = LocationResponse(latitude=point.y, longitude=point.x)

                    visit_data["case"] = CaseSimple(
                        id=visit.case.id,
                        patient_id=visit.case.patient_id,
                        care_type_id=visit.case.care_type_id,
                        location=location,
                        priority=visit.case.priority.value if hasattr(visit.case.priority, 'value') else str(visit.case.priority),
                        status=visit.case.status.value if hasattr(visit.case.status, 'value') else str(visit.case.status)
                    )
                    visit_data["patient"] = PatientSimple.model_validate(visit.case.patient) if visit.case.patient else None
                    visit_data["care_type"] = CareTypeSimple.model_validate(visit.case.care_type) if visit.case.care_type else None

                visits.append(VisitDetailed(**visit_data))

        # Convert vehicle with PostGIS location
        vehicle = None
        if route.vehicle:
            base_location = None
            if route.vehicle.base_location:
                point = to_shape(route.vehicle.base_location)
                base_location = LocationResponse(latitude=point.y, longitude=point.x)

            # Convert resources from JSON to list of strings if needed
            resources = route.vehicle.resources if isinstance(route.vehicle.resources, list) else []

            vehicle = VehicleSimple(
                id=route.vehicle.id,
                identifier=route.vehicle.identifier,
                capacity=route.vehicle.capacity_personnel,
                status=route.vehicle.status.value if hasattr(route.vehicle.status, 'value') else str(route.vehicle.status),
                resources=resources,
                base_location=base_location
            )

        # Convert personnel with skills
        personnel = []
        if route.assigned_personnel:
            for p in route.assigned_personnel:
                personnel.append(PersonnelSimple(
                    id=p.id,
                    name=p.name,
                    skills=[skill.name for skill in p.skills] if p.skills else []
                ))

        return cls(
            id=route.id,
            vehicle_id=route.vehicle_id,
            route_date=route.route_date,
            status=route.status,
            total_distance_km=route.total_distance_km,
            total_duration_minutes=route.total_duration_minutes,
            optimization_metadata=route.optimization_metadata,
            visit_count=len(route.visits) if route.visits else 0,
            created_at=route.created_at,
            updated_at=route.updated_at,
            vehicle=vehicle,
            personnel=personnel,
            visits=visits
        )
