"""
Care Type Repository
"""

from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from app.repositories.base import BaseRepository
from app.models.case import CareType, CareTypeSkill


class CareTypeRepository(BaseRepository[CareType]):
    """Repository for CareType entity"""

    def __init__(self, db: Session):
        super().__init__(CareType, db)

    def get_by_id_with_skills(self, id: int) -> Optional[CareType]:
        """
        Get care type by ID with required skills loaded

        Args:
            id: CareType ID

        Returns:
            CareType instance with skills or None
        """
        stmt = (
            select(CareType)
            .options(joinedload(CareType.required_skills))
            .where(CareType.id == id)
        )
        result = self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    def get_multi_with_skills(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[CareType]:
        """
        Get care types with skills loaded

        Args:
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of care types with skills
        """
        stmt = (
            select(CareType)
            .options(joinedload(CareType.required_skills))
            .offset(skip)
            .limit(limit)
        )
        result = self.db.execute(stmt)
        return list(result.scalars().unique().all())

    def get_by_name(self, name: str) -> Optional[CareType]:
        """
        Get care type by name

        Args:
            name: Care type name

        Returns:
            CareType instance or None
        """
        stmt = select(CareType).where(CareType.name == name)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def update_required_skills(self, care_type_id: int, skill_ids: List[int]) -> None:
        """
        Update care type required skills (replace all)

        Args:
            care_type_id: CareType ID
            skill_ids: List of skill IDs
        """
        # Delete existing skills
        self.db.query(CareTypeSkill).filter(
            CareTypeSkill.care_type_id == care_type_id
        ).delete()

        # Add new skills
        for skill_id in skill_ids:
            care_type_skill = CareTypeSkill(care_type_id=care_type_id, skill_id=skill_id)
            self.db.add(care_type_skill)

        self.db.commit()
