"""
Skill Service
Business logic for skill management
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.repositories.personnel_repository import SkillRepository
from app.schemas.skill import SkillCreate, SkillUpdate
from app.models.personnel import Skill
from app.core.exceptions import NotFoundException, ConflictException
from app.services.audit_service import AuditService


class SkillService:
    """Service for Skill business logic"""

    def __init__(self, db: Session):
        self.db = db
        self.skill_repo = SkillRepository(db)
        self.audit_service = AuditService(db)

    def create_skill(
        self,
        skill_in: SkillCreate,
        user_id: Optional[int] = None
    ) -> Skill:
        """
        Create a new skill

        Args:
            skill_in: Skill creation data
            user_id: ID of user creating the skill

        Returns:
            Created skill

        Raises:
            ConflictException: If skill name already exists
        """
        # Check for duplicate name
        existing = self.skill_repo.get_by_name(skill_in.name)
        if existing:
            raise ConflictException(f"Skill with name '{skill_in.name}' already exists")

        # Create skill
        skill_dict = skill_in.model_dump()
        skill = self.skill_repo.create(skill_dict)

        # Log audit
        self.audit_service.log_create("skill", skill.id, user_id)

        return skill

    def get_skill(self, skill_id: int) -> Skill:
        """
        Get skill by ID

        Args:
            skill_id: Skill ID

        Returns:
            Skill instance

        Raises:
            NotFoundException: If skill not found
        """
        skill = self.skill_repo.get_by_id(skill_id)
        if not skill:
            raise NotFoundException(f"Skill with ID {skill_id} not found")
        return skill

    def get_skills(self, skip: int = 0, limit: int = 100) -> List[Skill]:
        """
        Get all skills with pagination

        Args:
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of skills
        """
        return self.skill_repo.get_multi(skip=skip, limit=limit)

    def get_skills_by_ids(self, skill_ids: List[int]) -> List[Skill]:
        """
        Get skills by list of IDs

        Args:
            skill_ids: List of skill IDs

        Returns:
            List of skills
        """
        return self.skill_repo.get_by_ids(skill_ids)

    def update_skill(
        self,
        skill_id: int,
        skill_in: SkillUpdate,
        user_id: Optional[int] = None
    ) -> Skill:
        """
        Update a skill

        Args:
            skill_id: Skill ID
            skill_in: Update data
            user_id: ID of user updating the skill

        Returns:
            Updated skill

        Raises:
            NotFoundException: If skill not found
            ConflictException: If new name conflicts with existing skill
        """
        # Check if skill exists
        skill = self.get_skill(skill_id)

        # Check for name conflict if name is being updated
        if skill_in.name and skill_in.name != skill.name:
            existing = self.skill_repo.get_by_name(skill_in.name)
            if existing:
                raise ConflictException(f"Skill with name '{skill_in.name}' already exists")

        # Update skill
        update_dict = skill_in.model_dump(exclude_unset=True)
        updated_skill = self.skill_repo.update(skill_id, update_dict)

        # Log audit
        self.audit_service.log_update("skill", skill_id, user_id, update_dict)

        return updated_skill

    def delete_skill(
        self,
        skill_id: int,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Delete a skill

        Args:
            skill_id: Skill ID
            user_id: ID of user deleting the skill

        Returns:
            True if deleted

        Raises:
            NotFoundException: If skill not found
        """
        # Check if skill exists
        self.get_skill(skill_id)

        # Delete skill
        result = self.skill_repo.delete(skill_id)

        # Log audit
        if result:
            self.audit_service.log_delete("skill", skill_id, user_id)

        return result

    def count_skills(self) -> int:
        """
        Count total number of skills

        Returns:
            Number of skills
        """
        return self.skill_repo.count()
