"""
Personnel Repository
"""

from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from app.repositories.base import BaseRepository
from app.models.personnel import Personnel, Skill, PersonnelSkill


class PersonnelRepository(BaseRepository[Personnel]):
    """Repository for Personnel entity"""

    def __init__(self, db: Session):
        super().__init__(Personnel, db)

    def get_by_id_with_skills(self, id: int) -> Optional[Personnel]:
        """
        Get personnel by ID with skills loaded

        Args:
            id: Personnel ID

        Returns:
            Personnel instance with skills or None
        """
        stmt = select(Personnel).options(joinedload(Personnel.skills)).where(Personnel.id == id)
        result = self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    def get_by_user_id_with_skills(self, user_id: int) -> Optional[Personnel]:
        """
        Get personnel by user_id with skills loaded

        Args:
            user_id: User ID

        Returns:
            Personnel instance with skills or None
        """
        stmt = select(Personnel).options(joinedload(Personnel.skills)).where(Personnel.user_id == user_id)
        result = self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    def get_multi_with_skills(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        skill_id: Optional[int] = None
    ) -> List[Personnel]:
        """
        Get multiple personnel with skills loaded

        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            is_active: Filter by active status
            skill_id: Filter by skill ID

        Returns:
            List of personnel with skills
        """
        stmt = select(Personnel).options(joinedload(Personnel.skills))

        # Filter by active status
        if is_active is not None:
            stmt = stmt.where(Personnel.is_active == is_active)

        # Filter by skill
        if skill_id is not None:
            stmt = stmt.join(PersonnelSkill).where(PersonnelSkill.skill_id == skill_id)

        stmt = stmt.offset(skip).limit(limit)
        result = self.db.execute(stmt)
        return list(result.scalars().unique().all())

    def add_skill(self, personnel_id: int, skill_id: int) -> bool:
        """
        Add a skill to personnel

        Args:
            personnel_id: Personnel ID
            skill_id: Skill ID

        Returns:
            True if added, False if already exists
        """
        # Check if association already exists
        existing = self.db.execute(
            select(PersonnelSkill).where(
                PersonnelSkill.personnel_id == personnel_id,
                PersonnelSkill.skill_id == skill_id
            )
        ).scalar_one_or_none()

        if existing:
            return False

        personnel_skill = PersonnelSkill(personnel_id=personnel_id, skill_id=skill_id)
        self.db.add(personnel_skill)
        self.db.commit()
        return True

    def remove_skill(self, personnel_id: int, skill_id: int) -> bool:
        """
        Remove a skill from personnel

        Args:
            personnel_id: Personnel ID
            skill_id: Skill ID

        Returns:
            True if removed, False if not found
        """
        result = self.db.execute(
            select(PersonnelSkill).where(
                PersonnelSkill.personnel_id == personnel_id,
                PersonnelSkill.skill_id == skill_id
            )
        )
        personnel_skill = result.scalar_one_or_none()

        if not personnel_skill:
            return False

        self.db.delete(personnel_skill)
        self.db.commit()
        return True

    def update_skills(self, personnel_id: int, skill_ids: List[int]) -> None:
        """
        Update personnel skills (replace all)

        Args:
            personnel_id: Personnel ID
            skill_ids: List of skill IDs
        """
        # Delete existing skills
        self.db.execute(
            select(PersonnelSkill).where(PersonnelSkill.personnel_id == personnel_id)
        )
        self.db.query(PersonnelSkill).filter(PersonnelSkill.personnel_id == personnel_id).delete()

        # Add new skills
        for skill_id in skill_ids:
            personnel_skill = PersonnelSkill(personnel_id=personnel_id, skill_id=skill_id)
            self.db.add(personnel_skill)

        self.db.commit()


class SkillRepository(BaseRepository[Skill]):
    """Repository for Skill entity"""

    def __init__(self, db: Session):
        super().__init__(Skill, db)

    def get_by_name(self, name: str) -> Optional[Skill]:
        """
        Get skill by name

        Args:
            name: Skill name

        Returns:
            Skill instance or None
        """
        stmt = select(Skill).where(Skill.name == name)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_ids(self, skill_ids: List[int]) -> List[Skill]:
        """
        Get skills by list of IDs

        Args:
            skill_ids: List of skill IDs

        Returns:
            List of skills
        """
        stmt = select(Skill).where(Skill.id.in_(skill_ids))
        result = self.db.execute(stmt)
        return list(result.scalars().all())
