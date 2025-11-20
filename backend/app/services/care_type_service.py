"""
Care Type Service
Business logic for care type management
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.repositories.care_type_repository import CareTypeRepository
from app.schemas.care_type import CareTypeCreate, CareTypeUpdate
from app.models.case import CareType
from app.core.exceptions import NotFoundException, ConflictException, ValidationException
from app.services.audit_service import AuditService
from app.services.skill_service import SkillService


class CareTypeService:
    """Service for CareType business logic"""

    def __init__(self, db: Session):
        self.db = db
        self.care_type_repo = CareTypeRepository(db)
        self.skill_service = SkillService(db)
        self.audit_service = AuditService(db)

    def create_care_type(
        self,
        care_type_in: CareTypeCreate,
        user_id: Optional[int] = None
    ) -> CareType:
        """
        Create a new care type

        Args:
            care_type_in: Care type creation data
            user_id: ID of user creating the care type

        Returns:
            Created care type

        Raises:
            ConflictException: If care type name already exists
            ValidationException: If skill IDs are invalid
        """
        # Check for duplicate name
        existing = self.care_type_repo.get_by_name(care_type_in.name)
        if existing:
            raise ConflictException(f"Care type with name '{care_type_in.name}' already exists")

        # Validate skill IDs
        if care_type_in.required_skill_ids:
            skills = self.skill_service.get_skills_by_ids(care_type_in.required_skill_ids)
            if len(skills) != len(care_type_in.required_skill_ids):
                raise ValidationException("One or more skill IDs are invalid")

        # Create care type (exclude skill_ids from dict and map field name)
        care_type_dict = care_type_in.model_dump(exclude={"required_skill_ids"})
        # Map estimated_duration to estimated_duration_minutes for the database model
        if "estimated_duration" in care_type_dict:
            care_type_dict["estimated_duration_minutes"] = care_type_dict.pop("estimated_duration")
        care_type = self.care_type_repo.create(care_type_dict)

        # Add required skills
        if care_type_in.required_skill_ids:
            self.care_type_repo.update_required_skills(care_type.id, care_type_in.required_skill_ids)

        # Log audit
        self.audit_service.log_create("care_type", care_type.id, user_id)

        # Reload with skills
        return self.care_type_repo.get_by_id_with_skills(care_type.id)

    def get_care_type(self, care_type_id: int) -> CareType:
        """
        Get care type by ID with skills

        Args:
            care_type_id: Care type ID

        Returns:
            Care type instance

        Raises:
            NotFoundException: If care type not found
        """
        care_type = self.care_type_repo.get_by_id_with_skills(care_type_id)
        if not care_type:
            raise NotFoundException(f"Care type with ID {care_type_id} not found")
        return care_type

    def get_care_types(self, skip: int = 0, limit: int = 100) -> List[CareType]:
        """
        Get all care types with pagination

        Args:
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of care types with skills
        """
        return self.care_type_repo.get_multi_with_skills(skip=skip, limit=limit)

    def update_care_type(
        self,
        care_type_id: int,
        care_type_in: CareTypeUpdate,
        user_id: Optional[int] = None
    ) -> CareType:
        """
        Update a care type

        Args:
            care_type_id: Care type ID
            care_type_in: Update data
            user_id: ID of user updating the care type

        Returns:
            Updated care type

        Raises:
            NotFoundException: If care type not found
            ConflictException: If new name conflicts
            ValidationException: If skill IDs are invalid
        """
        # Check if care type exists
        care_type = self.get_care_type(care_type_id)

        # Check for name conflict
        if care_type_in.name and care_type_in.name != care_type.name:
            existing = self.care_type_repo.get_by_name(care_type_in.name)
            if existing:
                raise ConflictException(f"Care type with name '{care_type_in.name}' already exists")

        # Validate skill IDs if provided
        if care_type_in.required_skill_ids is not None:
            skills = self.skill_service.get_skills_by_ids(care_type_in.required_skill_ids)
            if len(skills) != len(care_type_in.required_skill_ids):
                raise ValidationException("One or more skill IDs are invalid")

        # Update care type
        update_dict = care_type_in.model_dump(exclude_unset=True, exclude={"required_skill_ids"})
        # Map estimated_duration to estimated_duration_minutes for the database model
        if "estimated_duration" in update_dict:
            update_dict["estimated_duration_minutes"] = update_dict.pop("estimated_duration")
        if update_dict:
            self.care_type_repo.update(care_type_id, update_dict)

        # Update skills if provided
        if care_type_in.required_skill_ids is not None:
            self.care_type_repo.update_required_skills(care_type_id, care_type_in.required_skill_ids)

        # Log audit
        self.audit_service.log_update("care_type", care_type_id, user_id, care_type_in.model_dump(exclude_unset=True))

        # Reload with skills
        return self.care_type_repo.get_by_id_with_skills(care_type_id)

    def delete_care_type(
        self,
        care_type_id: int,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Delete a care type

        Args:
            care_type_id: Care type ID
            user_id: ID of user deleting the care type

        Returns:
            True if deleted

        Raises:
            NotFoundException: If care type not found
        """
        # Check if care type exists
        self.get_care_type(care_type_id)

        # Delete care type
        result = self.care_type_repo.delete(care_type_id)

        # Log audit
        if result:
            self.audit_service.log_delete("care_type", care_type_id, user_id)

        return result

    def count_care_types(self) -> int:
        """
        Count total number of care types

        Returns:
            Number of care types
        """
        return self.care_type_repo.count()
