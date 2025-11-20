"""
API v1 Router
"""
from fastapi import APIRouter
from app.api.v1 import (
    auth,
    users,
    personnel,
    vehicles,
    patients,
    cases,
    skills,
    care_types,
    routes,
    tracking,
    visits,
    notifications
)

api_router = APIRouter()

# Include authentication routes
api_router.include_router(auth.router)

# Include user management routes
api_router.include_router(users.router)

# Include resource management routes
api_router.include_router(skills.router)
api_router.include_router(care_types.router)
api_router.include_router(personnel.router)
api_router.include_router(vehicles.router)
api_router.include_router(patients.router)
api_router.include_router(cases.router)

# Include route optimization
api_router.include_router(routes.router)

# Include tracking and visits
api_router.include_router(tracking.router)
api_router.include_router(visits.router)

# Include notifications
api_router.include_router(notifications.router)
