"""
Tracking Schemas
Pydantic models for GPS tracking and real-time updates
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
from enum import Enum


class LocationUpload(BaseModel):
    """Schema for uploading GPS location"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    speed_kmh: Optional[float] = Field(None, ge=0, description="Vehicle speed in km/h")
    heading_degrees: Optional[float] = Field(None, ge=0, le=360, description="Vehicle heading in degrees")
    accuracy_meters: Optional[float] = Field(None, ge=0, description="GPS accuracy in meters")
    timestamp: Optional[datetime] = Field(None, description="Location timestamp (defaults to server time)")

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": -33.4489,
                "longitude": -70.6693,
                "speed_kmh": 45.5,
                "heading_degrees": 180.0,
                "accuracy_meters": 10.0
            }
        }


class LocationResponse(BaseModel):
    """Schema for location response"""
    id: int
    vehicle_id: int
    latitude: float
    longitude: float
    speed_kmh: Optional[float]
    heading_degrees: Optional[float]
    accuracy_meters: Optional[float]
    timestamp: str

    class Config:
        from_attributes = True


class VehicleLocationResponse(BaseModel):
    """Schema for vehicle location with additional info"""
    vehicle_id: int
    vehicle_identifier: str
    current_location: Optional[LocationResponse]
    last_update: Optional[str]
    is_active: bool


class VisitStatusUpdate(BaseModel):
    """Schema for updating visit status"""
    status: str = Field(..., description="New visit status")
    notes: Optional[str] = Field(None, max_length=500, description="Status update notes")

    @validator("status")
    def validate_status(cls, v):
        valid_statuses = ["pending", "en_route", "arrived", "in_progress", "completed", "cancelled", "failed"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "status": "arrived",
                "notes": "Llegamos a la dirección del paciente"
            }
        }


class VisitStatusResponse(BaseModel):
    """Schema for visit status response"""
    id: int
    route_id: int
    case_id: int
    sequence_number: int
    status: str
    estimated_arrival_time: Optional[datetime]
    estimated_departure_time: Optional[datetime]
    actual_arrival_time: Optional[datetime]
    actual_departure_time: Optional[datetime]
    notes: Optional[str]

    class Config:
        from_attributes = True


class ETAResponse(BaseModel):
    """Schema for ETA calculation response"""
    visit_id: int
    vehicle_id: int
    current_location: dict
    destination: dict
    distance_km: float
    base_duration_minutes: float
    traffic_multiplier: float
    traffic_period: str
    buffered_duration_minutes: float
    eta: str
    estimated_arrival_time: Optional[str]
    delay_minutes: Optional[float]
    is_delayed: bool


class DelayAlertResponse(BaseModel):
    """Schema for delay alert response"""
    visit_id: int
    route_id: int
    vehicle_id: int
    case_id: int
    severity: str
    delay_minutes: float
    estimated_arrival: Optional[str]
    current_eta: Optional[str]
    message: str
    detected_at: str


class RouteProgressResponse(BaseModel):
    """Schema for route progress"""
    route_id: int
    total_visits: int
    completed: int
    in_progress: int
    failed: int
    cancelled: int
    pending: int
    completion_percentage: float


class WebSocketMessage(BaseModel):
    """Schema for WebSocket message"""
    type: str
    data: dict
    timestamp: str


class SubscribeRequest(BaseModel):
    """Schema for subscription request"""
    subscription_type: str = Field(..., description="Type: 'vehicle' or 'route'")
    id: int = Field(..., description="Vehicle ID or Route ID")

    @validator("subscription_type")
    def validate_subscription_type(cls, v):
        if v not in ["vehicle", "route"]:
            raise ValueError("subscription_type must be 'vehicle' or 'route'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "subscription_type": "vehicle",
                "id": 1
            }
        }


# Schemas for My Visit endpoint (Patient mobile app)
class CareTypeInVisit(BaseModel):
    """Care type schema for visit response"""
    id: int
    name: str
    duration_minutes: int

    class Config:
        from_attributes = True


class PatientInVisit(BaseModel):
    """Patient schema for visit response"""
    id: int
    name: str
    phone: str

    class Config:
        from_attributes = True


class LocationInVisit(BaseModel):
    """Location schema for visit response"""
    latitude: float
    longitude: float


class CaseInVisit(BaseModel):
    """Case schema for visit response"""
    id: int
    patient_id: int
    care_type_id: int
    priority: str
    status: str
    scheduled_date: Optional[str]  # YYYY-MM-DD
    time_window_start: Optional[str]  # HH:MM
    time_window_end: Optional[str]  # HH:MM
    special_notes: Optional[str]
    location: Optional[LocationInVisit] = None
    patient: PatientInVisit
    care_type: CareTypeInVisit

    class Config:
        from_attributes = True


class PersonnelInVisit(BaseModel):
    """Personnel schema for visit response"""
    id: int
    name: str
    skills: List[str]

    class Config:
        from_attributes = True


class VehicleInVisit(BaseModel):
    """Vehicle schema for visit response"""
    id: int
    identifier: str

    class Config:
        from_attributes = True


class RouteInVisit(BaseModel):
    """Route schema for visit response"""
    id: int
    vehicle: VehicleInVisit
    personnel: List[PersonnelInVisit]

    class Config:
        from_attributes = True


class VisitInMyVisit(BaseModel):
    """Visit schema for my visit response"""
    id: int
    route_id: int
    case_id: int
    sequence_number: int
    status: str
    estimated_arrival_time: Optional[str]
    actual_arrival_time: Optional[str]
    actual_start_time: Optional[str]
    actual_end_time: Optional[str]
    notes: Optional[str]
    created_at: str
    updated_at: str
    case: CaseInVisit

    class Config:
        from_attributes = True


class MyVisitResponse(BaseModel):
    """Response schema for /visits/my-visit endpoint"""
    visit: Optional[VisitInMyVisit]
    route: Optional[RouteInVisit]
    eta_minutes: Optional[int]

    class Config:
        from_attributes = True
