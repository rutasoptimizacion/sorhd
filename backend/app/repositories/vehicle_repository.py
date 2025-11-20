"""
Vehicle Repository
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.repositories.base import BaseRepository
from app.models.vehicle import Vehicle, VehicleStatus


class VehicleRepository(BaseRepository[Vehicle]):
    """Repository for Vehicle entity"""

    def __init__(self, db: Session):
        super().__init__(Vehicle, db)

    def get_by_identifier(self, identifier: str) -> Optional[Vehicle]:
        """
        Get vehicle by identifier (license plate/code)

        Args:
            identifier: Vehicle identifier

        Returns:
            Vehicle instance or None
        """
        stmt = select(Vehicle).where(Vehicle.identifier == identifier)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_multi_by_status(
        self,
        status: Optional[VehicleStatus] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Vehicle]:
        """
        Get vehicles filtered by status and active flag

        Args:
            status: Filter by vehicle status
            is_active: Filter by active flag
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of vehicles
        """
        stmt = select(Vehicle)

        if status is not None:
            stmt = stmt.where(Vehicle.status == status)

        if is_active is not None:
            stmt = stmt.where(Vehicle.is_active == is_active)

        stmt = stmt.offset(skip).limit(limit)
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def get_available_vehicles(self, skip: int = 0, limit: int = 100) -> List[Vehicle]:
        """
        Get available vehicles (active and not in use)

        Args:
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of available vehicles
        """
        return self.get_multi_by_status(
            status=VehicleStatus.AVAILABLE,
            is_active=True,
            skip=skip,
            limit=limit
        )

    def update_status(self, id: int, status: VehicleStatus) -> Optional[Vehicle]:
        """
        Update vehicle status

        Args:
            id: Vehicle ID
            status: New status

        Returns:
            Updated vehicle or None
        """
        return self.update(id, {"status": status})
