"""
Models Package - exports all database models
"""
from app.models.base import BaseModel, TimestampMixin
from app.models.user import User, UserRole
from app.models.personnel import Personnel, Skill, PersonnelSkill
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.patient import Patient
from app.models.case import Case, CareType, CareTypeSkill, CaseStatus, CasePriority, TimeWindowType
from app.models.route import Route, RoutePersonnel, Visit, RouteStatus, VisitStatus
from app.models.tracking import LocationLog
from app.models.notification import Notification, NotificationType, NotificationChannel, NotificationStatus
from app.models.audit import AuditLog, AuditAction
from app.models.distance_cache import DistanceCache
from app.models.optimization_metrics import OptimizationMetrics

__all__ = [
    # Base
    "BaseModel",
    "TimestampMixin",
    # User
    "User",
    "UserRole",
    # Personnel & Skills
    "Personnel",
    "Skill",
    "PersonnelSkill",
    # Vehicle
    "Vehicle",
    "VehicleStatus",
    # Patient
    "Patient",
    # Case & CareType
    "Case",
    "CareType",
    "CareTypeSkill",
    "CaseStatus",
    "CasePriority",
    "TimeWindowType",
    # Route & Visit
    "Route",
    "RoutePersonnel",
    "Visit",
    "RouteStatus",
    "VisitStatus",
    # Tracking
    "LocationLog",
    # Notification
    "Notification",
    "NotificationType",
    "NotificationChannel",
    "NotificationStatus",
    # Audit
    "AuditLog",
    "AuditAction",
    # Distance Cache
    "DistanceCache",
    # Optimization Metrics
    "OptimizationMetrics",
]
