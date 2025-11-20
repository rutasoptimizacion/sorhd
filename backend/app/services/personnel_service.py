"""
Personnel Service
Business logic for personnel management
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement

from app.repositories.personnel_repository import PersonnelRepository
from app.schemas.personnel import PersonnelCreate, PersonnelUpdate
from app.schemas.common import LocationSchema
from app.models.personnel import Personnel
from app.core.exceptions import NotFoundException, ValidationException
from app.services.audit_service import AuditService
from app.services.skill_service import SkillService


class PersonnelService:
    """Service for Personnel business logic"""

    def __init__(self, db: Session):
        self.db = db
        self.personnel_repo = PersonnelRepository(db)
        self.skill_service = SkillService(db)
        self.audit_service = AuditService(db)

    def _location_to_wkt(self, location: LocationSchema) -> str:
        """
        Convert LocationSchema to WKT Point

        Args:
            location: Location schema

        Returns:
            WKT string
        """
        return f"POINT({location.longitude} {location.latitude})"

    def _wkt_to_location(self, wkt: str) -> LocationSchema:
        """
        Convert WKT Point to LocationSchema

        Args:
            wkt: WKT string

        Returns:
            Location schema
        """
        # Parse WKT: "POINT(lon lat)"
        coords = wkt.replace("POINT(", "").replace(")", "").split()
        return LocationSchema(longitude=float(coords[0]), latitude=float(coords[1]))

    def create_personnel(
        self,
        personnel_in: PersonnelCreate,
        user_id: Optional[int] = None
    ) -> Personnel:
        """
        Create new personnel

        Args:
            personnel_in: Personnel creation data
            user_id: ID of user creating personnel

        Returns:
            Created personnel

        Raises:
            ValidationException: If skill IDs are invalid
        """
        # Validate skill IDs
        if personnel_in.skill_ids:
            skills = self.skill_service.get_skills_by_ids(personnel_in.skill_ids)
            if len(skills) != len(personnel_in.skill_ids):
                raise ValidationException("One or more skill IDs are invalid")

        # Create personnel (exclude skill_ids, start_location, and email from dict)
        personnel_dict = personnel_in.model_dump(exclude={"skill_ids", "start_location", "email"})

        # Convert location to WKT if provided
        if personnel_in.start_location is not None:
            personnel_dict["start_location"] = self._location_to_wkt(personnel_in.start_location)
        else:
            personnel_dict["start_location"] = None

        # Map field names from schema to model
        if "work_hours_start" in personnel_dict:
            personnel_dict["work_start_time"] = personnel_dict.pop("work_hours_start")
        if "work_hours_end" in personnel_dict:
            personnel_dict["work_end_time"] = personnel_dict.pop("work_hours_end")

        personnel = self.personnel_repo.create(personnel_dict)

        # Add skills
        if personnel_in.skill_ids:
            self.personnel_repo.update_skills(personnel.id, personnel_in.skill_ids)

        # Log audit
        self.audit_service.log_create("personnel", personnel.id, user_id)

        # Reload with skills
        return self.personnel_repo.get_by_id_with_skills(personnel.id)

    def get_personnel(self, personnel_id: int) -> Personnel:
        """
        Get personnel by ID with skills

        Args:
            personnel_id: Personnel ID

        Returns:
            Personnel instance

        Raises:
            NotFoundException: If personnel not found
        """
        personnel = self.personnel_repo.get_by_id_with_skills(personnel_id)
        if not personnel:
            raise NotFoundException(f"Personnel with ID {personnel_id} not found")
        return personnel

    def get_personnel_by_user_id(self, user_id: int) -> Personnel:
        """
        Get personnel by user_id with skills

        Args:
            user_id: User ID

        Returns:
            Personnel instance

        Raises:
            NotFoundException: If personnel not found for this user
        """
        personnel = self.personnel_repo.get_by_user_id_with_skills(user_id)
        if not personnel:
            raise NotFoundException(f"No personnel record found for user ID {user_id}")
        return personnel

    def get_personnel_list(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        skill_id: Optional[int] = None
    ) -> List[Personnel]:
        """
        Get personnel list with filters

        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            is_active: Filter by active status
            skill_id: Filter by skill ID

        Returns:
            List of personnel with skills
        """
        return self.personnel_repo.get_multi_with_skills(
            skip=skip,
            limit=limit,
            is_active=is_active,
            skill_id=skill_id
        )

    def update_personnel(
        self,
        personnel_id: int,
        personnel_in: PersonnelUpdate,
        user_id: Optional[int] = None
    ) -> Personnel:
        """
        Update personnel

        Args:
            personnel_id: Personnel ID
            personnel_in: Update data
            user_id: ID of user updating personnel

        Returns:
            Updated personnel

        Raises:
            NotFoundException: If personnel not found
            ValidationException: If skill IDs are invalid or personnel is in active route
        """
        # Check if personnel exists
        personnel = self.get_personnel(personnel_id)

        # Validate skill IDs if provided
        if personnel_in.skill_ids is not None:
            skills = self.skill_service.get_skills_by_ids(personnel_in.skill_ids)
            if len(skills) != len(personnel_in.skill_ids):
                raise ValidationException("One or more skill IDs are invalid")

        # Update personnel (exclude skill_ids, start_location, and email)
        update_dict = personnel_in.model_dump(exclude_unset=True, exclude={"skill_ids", "start_location", "email"})

        # Convert location if provided
        if personnel_in.start_location:
            update_dict["start_location"] = self._location_to_wkt(personnel_in.start_location)

        # Map field names from schema to model
        if "work_hours_start" in update_dict:
            update_dict["work_start_time"] = update_dict.pop("work_hours_start")
        if "work_hours_end" in update_dict:
            update_dict["work_end_time"] = update_dict.pop("work_hours_end")

        if update_dict:
            self.personnel_repo.update(personnel_id, update_dict)

        # Update skills if provided
        if personnel_in.skill_ids is not None:
            self.personnel_repo.update_skills(personnel_id, personnel_in.skill_ids)

        # Log audit
        self.audit_service.log_update("personnel", personnel_id, user_id, personnel_in.model_dump(exclude_unset=True))

        # Reload with skills
        return self.personnel_repo.get_by_id_with_skills(personnel_id)

    def delete_personnel(
        self,
        personnel_id: int,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Delete personnel

        Args:
            personnel_id: Personnel ID
            user_id: ID of user deleting personnel

        Returns:
            True if deleted

        Raises:
            NotFoundException: If personnel not found
            ValidationException: If personnel is in active route
        """
        # Check if personnel exists
        personnel = self.get_personnel(personnel_id)

        # TODO: Check if personnel is in active routes (Phase 4)
        # This will require checking the routes table for active routes with this personnel

        # Delete personnel
        result = self.personnel_repo.delete(personnel_id)

        # Log audit
        if result:
            self.audit_service.log_delete("personnel", personnel_id, user_id)

        return result

    def count_personnel(self, is_active: Optional[bool] = None) -> int:
        """
        Count personnel

        Args:
            is_active: Filter by active status

        Returns:
            Number of personnel
        """
        filters = {"is_active": is_active} if is_active is not None else None
        return self.personnel_repo.count(filters=filters)
