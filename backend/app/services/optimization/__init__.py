"""
Optimization Engine Package

This package contains the route optimization engine including:
- Domain models for optimization
- OR-Tools VRP strategy
- Heuristic fallback strategy
- Optimization service
"""

from .models import (
    OptimizationRequest,
    OptimizationResult,
    Route,
    Visit,
    Case,
    Vehicle,
    Personnel,
    Location,
    TimeWindow,
    ConstraintViolation,
    ConstraintType
)

__all__ = [
    "OptimizationRequest",
    "OptimizationResult",
    "Route",
    "Visit",
    "Case",
    "Vehicle",
    "Personnel",
    "Location",
    "TimeWindow",
    "ConstraintViolation",
    "ConstraintType"
]
