"""
Vehicle Service
Business logic for vehicle management
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleStatus
from app.schemas.common import LocationSchema
from app.models.vehicle import Vehicle
from app.core.exceptions import NotFoundException, ConflictException, ValidationException
from app.services.audit_service import AuditService


class VehicleService:
    """Service for Vehicle business logic"""

    def __init__(self, db: Session):
        self.db = db
        self.vehicle_repo = VehicleRepository(db)
        self.audit_service = AuditService(db)

    def _location_to_wkt(self, location: LocationSchema) -> str:
        """Convert LocationSchema to WKT Point"""
        return f"POINT({location.longitude} {location.latitude})"

    def _wkt_to_location(self, wkt: str) -> LocationSchema:
        """Convert WKT Point to LocationSchema"""
        coords = wkt.replace("POINT(", "").replace(")", "").split()
        return LocationSchema(longitude=float(coords[0]), latitude=float(coords[1]))

    def create_vehicle(
        self,
        vehicle_in: VehicleCreate,
        user_id: Optional[int] = None
    ) -> Vehicle:
        """
        Create new vehicle

        Args:
            vehicle_in: Vehicle creation data
            user_id: ID of user creating vehicle

        Returns:
            Created vehicle

        Raises:
            ConflictException: If vehicle identifier already exists
        """
        # Check for duplicate identifier
        existing = self.vehicle_repo.get_by_identifier(vehicle_in.identifier)
        if existing:
            raise ConflictException(f"Vehicle with identifier '{vehicle_in.identifier}' already exists")

        # Convert location to WKT
        location_wkt = self._location_to_wkt(vehicle_in.base_location)

        # Create vehicle
        vehicle_dict = vehicle_in.model_dump(exclude={"base_location"})
        vehicle_dict["base_location"] = location_wkt

        # Map field names from schema to model
        if "capacity" in vehicle_dict:
            vehicle_dict["capacity_personnel"] = vehicle_dict.pop("capacity")

        vehicle = self.vehicle_repo.create(vehicle_dict)

        # Log audit
        self.audit_service.log_create("vehicle", vehicle.id, user_id)

        return vehicle

    def get_vehicle(self, vehicle_id: int) -> Vehicle:
        """
        Get vehicle by ID

        Args:
            vehicle_id: Vehicle ID

        Returns:
            Vehicle instance

        Raises:
            NotFoundException: If vehicle not found
        """
        vehicle = self.vehicle_repo.get_by_id(vehicle_id)
        if not vehicle:
            raise NotFoundException(f"Vehicle with ID {vehicle_id} not found")
        return vehicle

    def get_vehicles(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[VehicleStatus] = None,
        is_active: Optional[bool] = None
    ) -> List[Vehicle]:
        """
        Get vehicles with filters

        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            status: Filter by status
            is_active: Filter by active status

        Returns:
            List of vehicles
        """
        return self.vehicle_repo.get_multi_by_status(
            status=status,
            is_active=is_active,
            skip=skip,
            limit=limit
        )

    def get_available_vehicles(self, skip: int = 0, limit: int = 100) -> List[Vehicle]:
        """
        Get available vehicles

        Args:
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of available vehicles
        """
        return self.vehicle_repo.get_available_vehicles(skip=skip, limit=limit)

    def update_vehicle(
        self,
        vehicle_id: int,
        vehicle_in: VehicleUpdate,
        user_id: Optional[int] = None
    ) -> Vehicle:
        """
        Update vehicle

        Args:
            vehicle_id: Vehicle ID
            vehicle_in: Update data
            user_id: ID of user updating vehicle

        Returns:
            Updated vehicle

        Raises:
            NotFoundException: If vehicle not found
            ConflictException: If new identifier conflicts
        """
        # Check if vehicle exists
        vehicle = self.get_vehicle(vehicle_id)

        # Check for identifier conflict
        if vehicle_in.identifier and vehicle_in.identifier != vehicle.identifier:
            existing = self.vehicle_repo.get_by_identifier(vehicle_in.identifier)
            if existing:
                raise ConflictException(f"Vehicle with identifier '{vehicle_in.identifier}' already exists")

        # Update vehicle
        update_dict = vehicle_in.model_dump(exclude_unset=True, exclude={"base_location"})

        # Convert location if provided
        if vehicle_in.base_location:
            update_dict["base_location"] = self._location_to_wkt(vehicle_in.base_location)

        # Map field names from schema to model
        if "capacity" in update_dict:
            update_dict["capacity_personnel"] = update_dict.pop("capacity")

        updated_vehicle = self.vehicle_repo.update(vehicle_id, update_dict)

        # Log audit
        self.audit_service.log_update("vehicle", vehicle_id, user_id, vehicle_in.model_dump(exclude_unset=True))

        return updated_vehicle

    def update_vehicle_status(
        self,
        vehicle_id: int,
        status: VehicleStatus,
        user_id: Optional[int] = None
    ) -> Vehicle:
        """
        Update vehicle status

        Args:
            vehicle_id: Vehicle ID
            status: New status
            user_id: ID of user updating status

        Returns:
            Updated vehicle
        """
        vehicle = self.vehicle_repo.update_status(vehicle_id, status)
        if not vehicle:
            raise NotFoundException(f"Vehicle with ID {vehicle_id} not found")

        # Log audit
        self.audit_service.log_update("vehicle", vehicle_id, user_id, {"status": status})

        return vehicle

    def delete_vehicle(
        self,
        vehicle_id: int,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Delete vehicle

        Args:
            vehicle_id: Vehicle ID
            user_id: ID of user deleting vehicle

        Returns:
            True if deleted

        Raises:
            NotFoundException: If vehicle not found
            ValidationException: If vehicle is in active route
        """
        # Check if vehicle exists
        vehicle = self.get_vehicle(vehicle_id)

        # TODO: Check if vehicle is in active routes (Phase 4)

        # Delete vehicle
        result = self.vehicle_repo.delete(vehicle_id)

        # Log audit
        if result:
            self.audit_service.log_delete("vehicle", vehicle_id, user_id)

        return result

    def count_vehicles(
        self,
        status: Optional[VehicleStatus] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """
        Count vehicles

        Args:
            status: Filter by status
            is_active: Filter by active status

        Returns:
            Number of vehicles
        """
        filters = {}
        if status is not None:
            filters["status"] = status
        if is_active is not None:
            filters["is_active"] = is_active

        return self.vehicle_repo.count(filters=filters if filters else None)
